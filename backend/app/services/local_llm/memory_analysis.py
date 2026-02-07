from typing import Dict, Any, List, Optional
from app.services.llm_service import LLMService
from app.services.model_query_service import ModelQueryService
from app.core.database import get_db
from sqlalchemy.orm import Session
import logging
import time

logger = logging.getLogger(__name__)


class LocalMemoryAnalysisService:
    """本地记忆分析服务"""
    
    def __init__(self):
        """初始化本地记忆分析服务"""
        self.llm_service = LLMService()
        self.model_query_service = ModelQueryService()
        self.local_model = "deepseek-r1:1.5b"
        # 缓存字典
        self._cache = {}
        self._cache_expiry = {}
        self._cache_ttl = 3600  # 缓存过期时间（秒）
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [method]
        for k, v in sorted(kwargs.items()):
            if isinstance(v, str):
                key_parts.append(f"{k}:{v[:100]}")
            else:
                key_parts.append(f"{k}:{str(v)}")
        return ":".join(key_parts)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache:
            return False
        if cache_key not in self._cache_expiry:
            return False
        return time.time() < self._cache_expiry[cache_key]
    
    def _set_cache(self, cache_key: str, value: Any) -> None:
        """设置缓存"""
        self._cache[cache_key] = value
        self._cache_expiry[cache_key] = time.time() + self._cache_ttl
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """获取缓存"""
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        return None
    
    def _clear_cache(self, cache_key: str) -> None:
        """清除缓存"""
        if cache_key in self._cache:
            del self._cache[cache_key]
        if cache_key in self._cache_expiry:
            del self._cache_expiry[cache_key]
        
    async def analyze_memory_content(
        self,
        db: Session,
        memory_content: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """分析记忆内容
        
        Args:
            db: 数据库会话
            memory_content: 记忆内容
            user_id: 用户ID
            
        Returns:
            分析结果，包含主题、情感、关键词等
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("analyze_memory_content", memory_content=memory_content, user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 构建分析Prompt
            prompt = f"""
            请分析以下记忆内容，提取相关信息：
            
            记忆内容：{memory_content}
            
            请从以下几个方面进行分析：
            1. 主题：记忆的主要主题
            2. 情感：记忆的情感倾向（积极、消极、中性）
            3. 关键词：提取3-5个关键概念或实体
            4. 重要性：记忆的重要程度（1-5，5最高）
            5. 分类：记忆的类型（工作、生活、学习等）
            
            请以JSON格式返回分析结果，包含以下字段：
            - topic: 主题
            - sentiment: 情感倾向
            - keywords: 关键词列表
            - importance: 重要性评分
            - category: 记忆类型
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的记忆分析专家，擅长分析文本内容并提取关键信息。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=self.local_model,
                max_tokens=500,
                temperature=0.2,
                db=db
            )
            
            # 解析结果
            analysis_result = self._parse_analysis_result(result["generated_text"])
            
            # 设置缓存
            self._set_cache(cache_key, analysis_result)
            
            return analysis_result
        except Exception as e:
            logger.error(f"记忆内容分析失败: {e}")
            return {
                "topic": "未知",
                "sentiment": "中性",
                "keywords": [],
                "importance": 3,
                "category": "其他"
            }
    
    async def enhance_query_understanding(
        self,
        db: Session,
        query: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """增强查询理解
        
        Args:
            db: 数据库会话
            query: 用户查询
            user_id: 用户ID
            
        Returns:
            增强后的查询理解，包含意图、实体、上下文等
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("enhance_query_understanding", query=query, user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 构建理解Prompt
            prompt = f"""
            请分析以下用户查询，增强对其的理解：
            
            用户查询：{query}
            
            请从以下几个方面进行分析：
            1. 意图：用户的主要意图
            2. 实体：查询中包含的关键实体
            3. 上下文需求：理解查询所需的上下文信息
            4. 相关主题：与查询相关的主题
            5. 预期结果：用户可能期望的结果类型
            
            请以JSON格式返回分析结果，包含以下字段：
            - intent: 意图
            - entities: 实体列表
            - context_needs: 上下文需求
            - related_topics: 相关主题列表
            - expected_result_type: 预期结果类型
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的查询理解专家，擅长分析用户查询并提取关键信息。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=self.local_model,
                max_tokens=500,
                temperature=0.2,
                db=db
            )
            
            # 解析结果
            enhanced_understanding = self._parse_analysis_result(result["generated_text"])
            
            # 设置缓存
            self._set_cache(cache_key, enhanced_understanding)
            
            return enhanced_understanding
        except Exception as e:
            logger.error(f"查询理解增强失败: {e}")
            return {
                "intent": "未知",
                "entities": [],
                "context_needs": [],
                "related_topics": [],
                "expected_result_type": "未知"
            }
    
    async def generate_memory_metadata(
        self,
        db: Session,
        memory_content: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """自动生成记忆元数据
        
        Args:
            db: 数据库会话
            memory_content: 记忆内容
            user_id: 用户ID
            
        Returns:
            生成的元数据，包含标签、摘要等
        """
        try:
            # 生成缓存键
            cache_key = self._get_cache_key("generate_memory_metadata", memory_content=memory_content, user_id=user_id)
            
            # 检查缓存
            cached_result = self._get_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 构建生成Prompt
            prompt = f"""
            请为以下记忆内容生成元数据：
            
            记忆内容：{memory_content}
            
            请生成以下元数据：
            1. 标签：3-5个相关标签
            2. 摘要：一句话摘要
            3. 关联主题：可能关联的主题
            4. 存储建议：存储策略建议
            5. 检索关键词：用于检索的关键词
            
            请以JSON格式返回生成结果，包含以下字段：
            - tags: 标签列表
            - summary: 摘要
            - related_topics: 关联主题列表
            - storage_suggestion: 存储建议
            - retrieval_keywords: 检索关键词列表
            """
            
            # 调用本地LLM
            result = self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的元数据生成专家，擅长为内容生成结构化的元数据。"},
                    {"role": "user", "content": prompt}
                ],
                model_name=self.local_model,
                max_tokens=500,
                temperature=0.2,
                db=db
            )
            
            # 解析结果
            metadata = self._parse_analysis_result(result["generated_text"])
            
            # 设置缓存
            self._set_cache(cache_key, metadata)
            
            return metadata
        except Exception as e:
            logger.error(f"元数据生成失败: {e}")
            return {
                "tags": [],
                "summary": "",
                "related_topics": [],
                "storage_suggestion": "常规存储",
                "retrieval_keywords": []
            }
    
    def _parse_analysis_result(self, llm_output: str) -> Dict[str, Any]:
        """解析LLM分析结果
        
        Args:
            llm_output: LLM输出
            
        Returns:
            解析后的结果字典
        """
        import json
        import re
        
        try:
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', llm_output)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # 尝试直接解析
                return json.loads(llm_output)
        except Exception as e:
            logger.error(f"解析分析结果失败: {e}")
            return {}
    
    async def batch_analyze_memory_content(
        self,
        db: Session,
        memory_contents: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        批量分析记忆内容
        
        Args:
            db: 数据库会话
            memory_contents: 记忆内容列表
            user_id: 用户ID
            
        Returns:
            分析结果列表
        """
        results = []
        
        # 处理每个记忆内容
        for memory_content in memory_contents:
            try:
                # 检查缓存
                cache_key = self._get_cache_key("analyze_memory_content", memory_content=memory_content, user_id=user_id)
                cached_result = self._get_cache(cache_key)
                
                if cached_result:
                    results.append(cached_result)
                else:
                    # 调用单个分析方法
                    result = await self.analyze_memory_content(db, memory_content, user_id)
                    results.append(result)
            except Exception as e:
                logger.error(f"批量分析记忆内容失败: {e}")
                results.append({
                    "topic": "未知",
                    "sentiment": "中性",
                    "keywords": [],
                    "importance": 3,
                    "category": "其他"
                })
        
        return results
    
    async def batch_generate_memory_metadata(
        self,
        db: Session,
        memory_contents: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        批量生成记忆元数据
        
        Args:
            db: 数据库会话
            memory_contents: 记忆内容列表
            user_id: 用户ID
            
        Returns:
            元数据列表
        """
        results = []
        
        # 处理每个记忆内容
        for memory_content in memory_contents:
            try:
                # 检查缓存
                cache_key = self._get_cache_key("generate_memory_metadata", memory_content=memory_content, user_id=user_id)
                cached_result = self._get_cache(cache_key)
                
                if cached_result:
                    results.append(cached_result)
                else:
                    # 调用单个生成方法
                    result = await self.generate_memory_metadata(db, memory_content, user_id)
                    results.append(result)
            except Exception as e:
                logger.error(f"批量生成记忆元数据失败: {e}")
                results.append({
                    "tags": [],
                    "summary": "",
                    "related_topics": [],
                    "storage_suggestion": "常规存储",
                    "retrieval_keywords": []
                })
        
        return results
