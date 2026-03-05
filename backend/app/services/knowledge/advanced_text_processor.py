import re
import logging
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from .llm_extractor import LLMEntityExtractor, LLMEntityDisambiguator
from .llm_text_processor import LLMTextProcessor

logger = logging.getLogger(__name__)


class AdvancedTextProcessor:
    """高级文本处理模块，提供智能分块、实体识别等功能
    
    使用LLM进行实体识别、关系抽取、文本分块、关键词提取等，支持高质量的知识图谱构建
    """
    
    def __init__(self, db=None):
        """初始化高级文本处理器
        
        Args:
            db: 数据库会话，用于LLM实体提取器和文本处理器
        """
        # 初始化LLM实体提取器
        self.llm_extractor = LLMEntityExtractor(db)
        self.llm_disambiguator = LLMEntityDisambiguator(db)
        
        # 初始化LLM文本处理器
        self.llm_text_processor = LLMTextProcessor(db)
        
        logger.info("高级文本处理器初始化成功，使用LLM进行文本处理")
    
    def clean_text(self, text: str) -> str:
        """清理文本，移除多余空格和特殊字符"""
        # 处理None值
        if text is None:
            return ""
        
        # 移除多余的空格和换行
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符，保留中文、英文、数字和基本标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}]', '', text)
        return text.strip()
    
    async def semantic_chunking(self, text: str, max_chunk_size: int = 1000, 
                         min_chunk_size: int = 200, overlap: int = 100,
                         semantic_threshold: float = 0.7) -> List[str]:
        """智能语义分块，基于句子边界和语义单元
        
        使用LLM进行智能语义分块
        
        Args:
            text: 输入文本
            max_chunk_size: 最大块大小
            min_chunk_size: 最小块大小
            overlap: 重叠窗口大小
            semantic_threshold: 语义相似度阈值
        
        Returns:
            分块后的文本列表
        """
        return await self.llm_text_processor.semantic_chunking(text, max_chunk_size, min_chunk_size, overlap)
    
    async def extract_entities_relationships(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """提取实体和关系

        使用LLM进行实体识别和关系抽取，并进行实体消歧，提供高质量的知识图谱构建能力

        Args:
            text: 输入文本

        Returns:
            (实体列表, 关系列表)
        """
        # 使用LLM实体提取器
        try:
            entities, relationships = await self.llm_extractor.extract_entities_and_relationships(text)

            # 实体消歧
            if entities and len(entities) > 1:
                logger.info(f"开始实体消歧，共 {len(entities)} 个实体")
                entities = await self.llm_disambiguator.disambiguate_entities(entities, text)
                logger.info(f"实体消歧完成")

            # 指代消解
            if entities:
                logger.info(f"开始指代消解")
                entities = await self.llm_disambiguator.resolve_coreference(text, entities)
                logger.info(f"指代消解完成")

            return entities, relationships

        except Exception as e:
            logger.error(f"LLM实体提取异常: {e}")
            return [], []
    
    async def extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """提取关键词
        
        使用LLM进行关键词提取，返回关键词及其权重
        
        Args:
            text: 输入文本
            top_n: 返回的关键词数量
            
        Returns:
            关键词列表，包含词和权重
        """
        return await self.llm_text_processor.extract_keywords(text, top_n)
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度
        
        使用LLM计算两段文本的语义相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            相似度分数（0-1）
        """
        return await self.llm_text_processor.calculate_similarity(text1, text2)
    
    def _extract_overlap_text(self, text: str, overlap_size: int) -> str:
        """从文本末尾提取重叠部分
        
        Args:
            text: 输入文本
            overlap_size: 重叠窗口大小
            
        Returns:
            重叠部分的文本
        """
        if len(text) <= overlap_size:
            return text
        
        # 尝试按句子边界分割
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            # 如果没有句子边界，直接截取末尾overlap_size个字符
            return text[-overlap_size:]
        
        # 从后向前累加句子，直到达到重叠大小
        overlap_text = ""
        for i in range(len(sentences) - 1, -1, -1):
            sentence = sentences[i]
            if len(overlap_text) + len(sentence) <= overlap_size:
                overlap_text = sentence + " " + overlap_text if overlap_text else sentence
            else:
                break
        
        return overlap_text.strip()
    
    async def adaptive_chunking(self, text: str, target_chunk_size: int = 800, 
                         min_chunk_size: int = 200, max_chunk_size: int = 1200,
                         semantic_threshold: float = 0.6) -> List[str]:
        """自适应分块，根据内容语义动态调整块大小
        
        使用LLM进行智能自适应分块，根据内容语义动态调整块大小
        
        Args:
            text: 输入文本
            target_chunk_size: 目标块大小
            min_chunk_size: 最小块大小
            max_chunk_size: 最大块大小
            semantic_threshold: 语义相似度阈值
            
        Returns:
            分块后的文本列表
        """
        # 使用LLM进行智能语义分块（自适应分块使用相同的LLM方法）
        return await self.llm_text_processor.semantic_chunking(text, max_chunk_size, min_chunk_size, 100)
    
    def analyze_chunk_quality(self, chunks: List[str]) -> Dict[str, Any]:
        """分析分块质量
        
        Args:
            chunks: 分块列表
            
        Returns:
            分块质量分析结果
        """
        if not chunks:
            return {"error": "没有分块数据"}
        
        chunk_sizes = [len(chunk) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunks)
        max_size = max(chunk_sizes)
        min_size = min(chunk_sizes)
        
        # 计算语义连贯性（相邻块的相似度）
        semantic_coherence = []
        for i in range(len(chunks) - 1):
            similarity = self.calculate_similarity(chunks[i], chunks[i + 1])
            semantic_coherence.append(similarity)
        
        avg_coherence = sum(semantic_coherence) / len(semantic_coherence) if semantic_coherence else 0
        
        return {
            "total_chunks": len(chunks),
            "average_chunk_size": round(avg_size, 2),
            "max_chunk_size": max_size,
            "min_chunk_size": min_size,
            "average_semantic_coherence": round(avg_coherence, 3),
            "chunk_size_distribution": {
                "small": len([s for s in chunk_sizes if s < 200]),
                "medium": len([s for s in chunk_sizes if 200 <= s <= 800]),
                "large": len([s for s in chunk_sizes if s > 800])
            }
        }
    
    def get_entity_extraction_info(self) -> Dict[str, Any]:
        """获取实体识别模块信息
        
        Returns:
            实体识别模块的状态信息
        """
        return {
            "llm_extractor_available": True,
            "llm_disambiguator_available": True,
            "llm_text_processor_available": True,
            "primary_method": "llm"
        }
    
    def analyze_entity_quality(self, entities: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        """分析实体识别质量
        
        Args:
            entities: 实体列表
            text: 原始文本
            
        Returns:
            实体质量分析结果
        """
        if not entities:
            return {"error": "没有实体数据"}
        
        # 统计实体类型分布
        type_distribution = {}
        
        for entity in entities:
            entity_type = entity.get('type', 'UNKNOWN')
            type_distribution[entity_type] = type_distribution.get(entity_type, 0) + 1
        
        # 计算实体覆盖率（实体文本占总文本比例）
        total_entity_length = sum(ent.get('end_pos', 0) - ent.get('start_pos', 0) for ent in entities)
        coverage = total_entity_length / len(text) if text else 0
        
        return {
            "total_entities": len(entities),
            "type_distribution": type_distribution,
            "entity_coverage": round(coverage, 3),
            "average_entity_length": round(total_entity_length / len(entities), 2) if entities else 0
        }
    
    async def disambiguate_entities(self, entity_mentions: List[Dict[str, Any]], context: str = None) -> List[Dict[str, Any]]:
        """对实体提及进行消歧
        
        Args:
            entity_mentions: 实体提及列表
            context: 上下文文本
            
        Returns:
            消歧后的实体组列表
        """
        return await self.llm_disambiguator.disambiguate_entities(entity_mentions, context)
    
    async def resolve_coreference(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """指代消解
        
        Args:
            text: 原始文本
            entities: 已提取的实体列表
            
        Returns:
            包含指代信息的实体列表
        """
        return await self.llm_disambiguator.resolve_coreference(text, entities)

    def extract_entities_relationships_sync(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """同步版本的实体和关系提取
        
        为同步环境提供的包装方法，内部使用asyncio运行异步方法
        
        Args:
            text: 输入文本
            
        Returns:
            (实体列表, 关系列表)
        """
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在异步环境中，创建新任务
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.extract_entities_relationships(text))
            else:
                # 如果没有运行的事件循环，使用run_until_complete
                return loop.run_until_complete(self.extract_entities_relationships(text))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self.extract_entities_relationships(text))
        except Exception as e:
            logger.error(f"同步实体提取失败: {e}")
            return [], []

    def semantic_chunking_sync(self, text: str, max_chunk_size: int = 1000,
                               min_chunk_size: int = 200, overlap: int = 100) -> List[str]:
        """同步版本的语义分块
        
        Args:
            text: 输入文本
            max_chunk_size: 最大块大小
            min_chunk_size: 最小块大小
            overlap: 重叠窗口大小
            
        Returns:
            分块后的文本列表
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.semantic_chunking(text, max_chunk_size, min_chunk_size, overlap))
            else:
                return loop.run_until_complete(self.semantic_chunking(text, max_chunk_size, min_chunk_size, overlap))
        except RuntimeError:
            return asyncio.run(self.semantic_chunking(text, max_chunk_size, min_chunk_size, overlap))
        except Exception as e:
            logger.error(f"同步语义分块失败: {e}")
            return [text] if text else []

    def extract_keywords_sync(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """同步版本的关键词提取
        
        Args:
            text: 输入文本
            top_n: 返回的关键词数量
            
        Returns:
            关键词列表
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.extract_keywords(text, top_n))
            else:
                return loop.run_until_complete(self.extract_keywords(text, top_n))
        except RuntimeError:
            return asyncio.run(self.extract_keywords(text, top_n))
        except Exception as e:
            logger.error(f"同步关键词提取失败: {e}")
            return []

    def calculate_similarity_sync(self, text1: str, text2: str) -> float:
        """同步版本的相似度计算
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            相似度分数
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.calculate_similarity(text1, text2))
            else:
                return loop.run_until_complete(self.calculate_similarity(text1, text2))
        except RuntimeError:
            return asyncio.run(self.calculate_similarity(text1, text2))
        except Exception as e:
            logger.error(f"同步相似度计算失败: {e}")
            return 0.0
