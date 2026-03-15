"""
LLM文本处理器模块

基于大语言模型(LLM)的文本处理功能，提供智能分块、关键词提取、相似度计算等功能。
"""

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService
from app.services.default_model_cache_service import DefaultModelCacheService

logger = logging.getLogger(__name__)


class LLMTextProcessor:
    """
    LLM文本处理器
    
    基于大语言模型进行文本处理，包括智能分块、关键词提取、相似度计算等。
    集成默认模型管理系统，自动获取知识库场景配置的模型。
    """
    
    def __init__(self, db: Session = None):
        """
        初始化LLM文本处理器
        
        Args:
            db: 数据库会话，用于获取模型配置
        """
        self.db = db
        self.llm_service = LLMService()
        self.scene = "knowledge"
        self.fallback_scene = "chat"
        
        logger.info("LLM文本处理器初始化成功")
    
    def _get_model_for_processing(self) -> Optional[str]:
        """
        获取用于文本处理的模型
        
        按照以下优先级获取模型：
        1. 知识库场景(knowledge)的默认模型
        2. 聊天场景(chat)的默认模型
        3. 全局默认模型
        
        Returns:
            模型ID或None
        """
        if not self.db:
            return None
        
        try:
            # 1. 优先使用知识库场景模型
            model_id = self._get_scene_model_from_cache_or_db(self.scene)
            if model_id:
                logger.debug(f"使用知识库场景模型: {model_id}")
                return model_id
            
            # 2. 如果知识库场景未配置，使用聊天场景模型
            logger.info(f"知识库场景未配置模型，尝试使用聊天场景")
            model_id = self._get_scene_model_from_cache_or_db(self.fallback_scene)
            if model_id:
                logger.info(f"使用聊天场景默认模型作为备选: {model_id}")
                return model_id
            
            # 3. 如果聊天场景也未配置，使用全局默认模型
            global_models = DefaultModelCacheService.get_cached_global_default_models()
            if global_models and len(global_models) > 0:
                model_id = global_models[0].get('model_id')
                logger.info(f"使用全局默认模型: {model_id}")
                return model_id
            
            # 4. 如果都没有配置，返回None
            logger.warning("未配置默认模型")
            return None
            
        except Exception as e:
            logger.warning(f"获取默认模型失败: {e}")
            return None
    
    def _get_scene_model_from_cache_or_db(self, scene: str) -> Optional[str]:
        """
        从缓存或数据库获取场景默认模型
        
        Args:
            scene: 场景名称
            
        Returns:
            模型ID或None
        """
        # 1. 先尝试从缓存获取
        scene_models = DefaultModelCacheService.get_cached_scene_default_models(scene)
        if scene_models and len(scene_models) > 0:
            return scene_models[0].get('model_id')
        
        # 2. 缓存未命中，从数据库获取
        if self.db:
            try:
                from app.models.default_model import DefaultModel
                config = self.db.query(DefaultModel).filter(
                    DefaultModel.scope == "scene",
                    DefaultModel.scene == scene,
                    DefaultModel.is_active == True
                ).order_by(DefaultModel.priority.asc()).first()
                
                if config:
                    logger.info(f"从数据库获取到{scene}场景模型: {config.model_id}")
                    return config.model_id
            except Exception as e:
                logger.error(f"从数据库获取{scene}场景模型失败: {e}")
        
        return None
    
    async def semantic_chunking(self, text: str, max_chunk_size: int = 1000,
                                min_chunk_size: int = 200, overlap: int = 30) -> List[str]:
        """
        智能语义分块

        使用LLM进行智能分块，根据语义边界将文本分割成合适的块。

        Args:
            text: 输入文本
            max_chunk_size: 最大块大小（字符数）
            min_chunk_size: 最小块大小（字符数）
            overlap: 块之间的重叠大小（字符数），默认30以保证上下文连贯同时减少重复

        Returns:
            分块后的文本列表
        """
        if not text or len(text) <= max_chunk_size:
            return [text] if text else []
        
        try:
            model_id = self._get_model_for_processing()
            
            prompt = f"""请将以下文本按照语义边界智能分块，要求：
1. 每个块的大小在 {min_chunk_size} 到 {max_chunk_size} 字符之间
2. 优先在段落、句子边界处分割
3. 相邻块之间需要有 {overlap} 字符的重叠，以保证上下文连贯
4. 返回JSON格式：{{"chunks": ["块1内容", "块2内容", ...]}}

文本内容：
{text[:5000]}  # 限制输入长度避免超出模型上下文

请只返回JSON格式的分块结果，不要包含其他说明。"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model_name=model_id,
                temperature=0.3
            )
            
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                # 提取JSON部分
                json_match = self._extract_json(content)
                if json_match:
                    result = json.loads(json_match)
                    chunks = result.get("chunks", [])
                    if chunks:
                        logger.info(f"LLM智能分块成功，生成 {len(chunks)} 个块")
                        return chunks
            
            # 如果LLM分块失败，使用基于句子边界的简单分块
            logger.warning("LLM分块失败，使用句子边界分块")
            return self._sentence_based_chunking(text, max_chunk_size, min_chunk_size, overlap)
            
        except Exception as e:
            logger.error(f"LLM语义分块异常: {e}")
            return self._sentence_based_chunking(text, max_chunk_size, min_chunk_size, overlap)
    
    def _sentence_based_chunking(self, text: str, max_chunk_size: int,
                                  min_chunk_size: int, overlap: int) -> List[str]:
        """
        基于句子边界的分块（LLM失败时的备选方案）
        
        Args:
            text: 输入文本
            max_chunk_size: 最大块大小
            min_chunk_size: 最小块大小
            overlap: 重叠大小
            
        Returns:
            分块后的文本列表
        """
        import re
        
        # 使用句子边界分割
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return [text] if text else []
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_size = len(sentence)
            
            if current_size + sentence_size <= max_chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size += sentence_size
                i += 1
            else:
                if current_chunk and current_size >= min_chunk_size:
                    chunks.append(current_chunk.strip())
                    
                    # 应用重叠
                    if overlap > 0 and len(current_chunk) > overlap:
                        current_chunk = current_chunk[-overlap:]
                        current_size = len(current_chunk)
                    else:
                        current_chunk = ""
                        current_size = 0
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
                    current_size += sentence_size
                    i += 1
        
        if current_chunk and current_size >= min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        使用LLM提取关键词
        
        Args:
            text: 输入文本
            top_n: 返回的关键词数量
            
        Returns:
            关键词列表，包含词和权重
        """
        if not text:
            return []
        
        try:
            model_id = self._get_model_for_processing()
            
            prompt = f"""请从以下文本中提取 {top_n} 个最重要的关键词。
要求：
1. 关键词应该能代表文本的核心主题
2. 包括重要的实体名称、概念、术语
3. 返回JSON格式：{{"keywords": [{{"word": "关键词1", "weight": 0.95}}, ...]}}
4. weight取值范围0-1，表示重要性

文本内容：
{text[:3000]}

请只返回JSON格式的关键词列表，不要包含其他说明。"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model_name=model_id,
                temperature=0.3
            )
            
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                json_match = self._extract_json(content)
                if json_match:
                    result = json.loads(json_match)
                    keywords = result.get("keywords", [])
                    if keywords:
                        logger.info(f"LLM关键词提取成功，提取 {len(keywords)} 个关键词")
                        return keywords
            
            # 如果LLM提取失败，使用简单统计方法
            logger.warning("LLM关键词提取失败，使用统计方法")
            return self._statistical_keyword_extraction(text, top_n)
            
        except Exception as e:
            logger.error(f"LLM关键词提取异常: {e}")
            return self._statistical_keyword_extraction(text, top_n)
    
    def _statistical_keyword_extraction(self, text: str, top_n: int) -> List[Dict[str, Any]]:
        """
        基于统计的关键词提取（LLM失败时的备选方案）
        
        Args:
            text: 输入文本
            top_n: 返回的关键词数量
            
        Returns:
            关键词列表
        """
        import re
        from collections import Counter
        
        # 简单的分词：按非字母数字字符分割
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{2,}', text)
        
        # 停用词
        stop_words = {'的', '是', '在', '和', '与', '或', '了', '着', '过', '地', '得', 
                      '啊', '呢', '吧', '吗', '我', '你', '他', '她', '它', '我们', '你们',
                      '他们', '这个', '那个', '这里', '那里', '这样', '那样'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        word_freq = Counter(filtered_words)
        total_words = sum(word_freq.values())
        
        # 计算权重（归一化词频）
        keywords = []
        for word, freq in word_freq.most_common(top_n):
            weight = freq / total_words if total_words > 0 else 0
            keywords.append({"word": word, "weight": round(weight, 4)})
        
        return keywords
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        使用LLM计算文本相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            相似度分数（0-1）
        """
        if not text1 or not text2:
            return 0.0
        
        try:
            model_id = self._get_model_for_processing()
            
            prompt = f"""请判断以下两段文本的语义相似度。

文本1：
{text1[:1500]}

文本2：
{text2[:1500]}

请只返回一个0-1之间的数字表示相似度，1表示完全相同，0表示完全不同。
例如：0.85"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model_name=model_id,
                temperature=0.1
            )
            
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"].strip()
                # 提取数字
                import re
                numbers = re.findall(r'0?\.\d+|1\.0|0|1', content)
                if numbers:
                    similarity = float(numbers[0])
                    logger.debug(f"LLM相似度计算: {similarity}")
                    return min(1.0, max(0.0, similarity))
            
            # 如果LLM计算失败，使用Jaccard相似度
            logger.warning("LLM相似度计算失败，使用Jaccard相似度")
            return self._jaccard_similarity(text1, text2)
            
        except Exception as e:
            logger.error(f"LLM相似度计算异常: {e}")
            return self._jaccard_similarity(text1, text2)
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        Jaccard相似度计算（LLM失败时的备选方案）
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            相似度分数
        """
        import re
        
        # 简单的字符集相似度
        words1 = set(re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+', text1.lower()))
        words2 = set(re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_json(self, text: str) -> Optional[str]:
        """
        从文本中提取JSON部分
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            JSON字符串或None
        """
        import re
        
        # 尝试匹配JSON对象
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group()
        
        # 尝试匹配JSON数组
        json_array_match = re.search(r'\[[\s\S]*\]', text)
        if json_array_match:
            return json_array_match.group()
        
        return None


# 同步包装函数，用于兼容现有接口
def create_llm_text_processor(db: Session = None) -> LLMTextProcessor:
    """
    创建LLM文本处理器实例
    
    Args:
        db: 数据库会话
        
    Returns:
        LLMTextProcessor实例
    """
    return LLMTextProcessor(db)
