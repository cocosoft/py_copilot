import re
import logging
import asyncio
from typing import List, Dict, Any, Tuple, Optional, Set
from sqlalchemy.orm import Session
from app.services.knowledge.extraction.llm_extractor import LLMEntityExtractor, LLMEntityDisambiguator
from app.services.knowledge.llm_text_processor import LLMTextProcessor
from app.services.knowledge.entity_config_manager import EntityConfigManager

logger = logging.getLogger(__name__)


class AdvancedTextProcessor:
    """高级文本处理模块，提供智能分块、实体识别等功能

    使用混合策略（规则+词典+LLM）进行实体识别、关系抽取、文本分块、关键词提取等，
    支持高质量的知识图谱构建和可配置的提取策略
    """

    def __init__(self, db: Session = None, knowledge_base_id: int = None):
        """初始化高级文本处理器

        Args:
            db: 数据库会话，用于LLM实体提取器和文本处理器
            knowledge_base_id: 知识库ID，用于加载知识库级配置
        """
        self.db = db
        self.knowledge_base_id = knowledge_base_id

        # 初始化配置管理器（支持知识库级配置）
        self.config_manager = EntityConfigManager(knowledge_base_id)

        # 初始化LLM实体提取器（传入知识库ID）
        self.llm_extractor = LLMEntityExtractor(db, knowledge_base_id)
        self.llm_disambiguator = LLMEntityDisambiguator(db)

        # 初始化LLM文本处理器
        self.llm_text_processor = LLMTextProcessor(db)

        # 加载提取规则
        self.extraction_rules = self._load_extraction_rules()

        # 加载词典
        self.dictionaries = self._load_dictionaries()

        logger.info(f"高级文本处理器初始化成功，知识库ID: {knowledge_base_id}，使用混合策略进行文本处理")
    
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

    def _load_extraction_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载提取规则

        从配置管理器加载启用的提取规则

        Returns:
            按实体类型分组的提取规则
        """
        try:
            # 直接从配置获取规则字典
            all_rules = self.config_manager.config.get('extraction_rules', {})
            # 过滤禁用的规则
            filtered_rules = {}
            for entity_type, rules in all_rules.items():
                enabled_rules = [r for r in rules if r.get('enabled', True)]
                if enabled_rules:
                    filtered_rules[entity_type] = enabled_rules
            logger.info(f"加载了 {len(filtered_rules)} 个实体类型的提取规则")
            return filtered_rules
        except Exception as e:
            logger.warning(f"加载提取规则失败: {e}，使用空规则")
            return {}

    def _load_dictionaries(self) -> Dict[str, Set[str]]:
        """加载词典

        从配置管理器加载词典数据

        Returns:
            按实体类型分组的词典术语集合
        """
        try:
            dictionaries = self.config_manager.get_dictionaries()
            # 转换为集合以提高查找效率
            dict_sets = {}
            for entity_type, terms in dictionaries.items():
                dict_sets[entity_type] = set(terms)
            logger.info(f"加载了 {len(dict_sets)} 个词典")
            return dict_sets
        except Exception as e:
            logger.warning(f"加载词典失败: {e}，使用空词典")
            return {}

    def _extract_with_rules(self, text: str) -> List[Dict[str, Any]]:
        """使用规则引擎提取实体

        根据配置的规则提取实体

        Args:
            text: 输入文本

        Returns:
            提取的实体列表
        """
        entities = []

        if not self.extraction_rules:
            return entities

        for entity_type, rules in self.extraction_rules.items():
            # 检查实体类型是否启用
            entity_types = self.config_manager.get_entity_types()
            if entity_type in entity_types and not entity_types[entity_type].get('enabled', True):
                continue

            for rule in rules:
                if not rule.get('enabled', True):
                    continue

                pattern = rule.get('pattern', '')
                if not pattern:
                    continue

                try:
                    # 使用正则表达式匹配
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        entity_text = match.group(1) if match.groups() else match.group(0)
                        start_pos = match.start()
                        end_pos = match.end()

                        entity = {
                            'text': entity_text,
                            'type': entity_type,
                            'start_pos': start_pos,
                            'end_pos': end_pos,
                            'confidence': 0.8,  # 规则匹配的置信度
                            'source': 'rule',
                            'rule_name': rule.get('name', '')
                        }
                        entities.append(entity)
                except re.error as e:
                    logger.warning(f"规则 '{rule.get('name', '')}' 的正则表达式错误: {e}")
                    continue

        logger.info(f"规则引擎提取了 {len(entities)} 个实体")
        return entities

    def _extract_with_dictionary(self, text: str) -> List[Dict[str, Any]]:
        """使用词典匹配提取实体

        根据配置的词典提取实体

        Args:
            text: 输入文本

        Returns:
            提取的实体列表
        """
        entities = []

        if not self.dictionaries:
            return entities

        for entity_type, terms in self.dictionaries.items():
            # 检查实体类型是否启用
            entity_types = self.config_manager.get_entity_types()
            if entity_type in entity_types and not entity_types[entity_type].get('enabled', True):
                continue

            for term in terms:
                if not term:
                    continue

                # 在文本中查找词典术语
                start_pos = 0
                while True:
                    pos = text.find(term, start_pos)
                    if pos == -1:
                        break

                    entity = {
                        'text': term,
                        'type': entity_type,
                        'start_pos': pos,
                        'end_pos': pos + len(term),
                        'confidence': 0.9,  # 词典匹配的置信度较高
                        'source': 'dictionary'
                    }
                    entities.append(entity)
                    start_pos = pos + 1

        logger.info(f"词典匹配提取了 {len(entities)} 个实体")
        return entities

    def _merge_entities(self, *entity_lists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并多个实体列表，去重并保留最高置信度

        Args:
            *entity_lists: 多个实体列表

        Returns:
            合并后的实体列表
        """
        # 使用字典去重，键为 (text, type, start_pos)
        entity_map = {}

        for entities in entity_lists:
            for entity in entities:
                key = (entity.get('text', ''), entity.get('type', ''), entity.get('start_pos', 0))

                # 如果已存在，保留置信度更高的
                if key in entity_map:
                    if entity.get('confidence', 0) > entity_map[key].get('confidence', 0):
                        entity_map[key] = entity
                else:
                    entity_map[key] = entity

        # 按起始位置排序
        merged = sorted(entity_map.values(), key=lambda x: x.get('start_pos', 0))

        logger.info(f"合并后得到 {len(merged)} 个唯一实体")
        return merged

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
    
    async def extract_entities_relationships(self, text: str,
                                               use_rules: bool = True,
                                               use_dictionary: bool = True,
                                               use_llm: bool = True) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """提取实体和关系

        使用混合策略（规则+词典+LLM）进行实体识别和关系抽取，并进行实体消歧，
        提供高质量的知识图谱构建能力

        Args:
            text: 输入文本
            use_rules: 是否使用规则引擎
            use_dictionary: 是否使用词典匹配
            use_llm: 是否使用LLM提取

        Returns:
            (实体列表, 关系列表)
        """
        logger.info(f"[TextProcessor] 开始提取实体和关系, 文本长度={len(text)}, "
                   f"knowledge_base_id={self.knowledge_base_id}, "
                   f"use_rules={use_rules}, use_dictionary={use_dictionary}, use_llm={use_llm}")
        logger.info(f"[TextProcessor] 提取规则数量={len(self.extraction_rules)}, 词典数量={len(self.dictionaries)}")

        all_entities = []
        all_relationships = []

        try:
            # 1. 规则引擎提取
            if use_rules and self.extraction_rules:
                logger.info("[TextProcessor] 使用规则引擎提取实体")
                rule_entities = self._extract_with_rules(text)
                logger.info(f"[TextProcessor] 规则引擎提取到 {len(rule_entities)} 个实体")
                all_entities.extend(rule_entities)

            # 2. 词典匹配提取
            if use_dictionary and self.dictionaries:
                logger.info("[TextProcessor] 使用词典匹配提取实体")
                dict_entities = self._extract_with_dictionary(text)
                logger.info(f"[TextProcessor] 词典匹配提取到 {len(dict_entities)} 个实体")
                all_entities.extend(dict_entities)

            # 3. LLM提取
            if use_llm:
                logger.info("[TextProcessor] 使用LLM提取实体和关系")
                try:
                    llm_entities, llm_relationships = await self.llm_extractor.extract_entities_and_relationships(text)
                    logger.info(f"[TextProcessor] LLM提取到 {len(llm_entities)} 个实体, {len(llm_relationships)} 个关系")
                    all_entities.extend(llm_entities)
                    all_relationships.extend(llm_relationships)
                except Exception as e:
                    logger.error(f"[TextProcessor] LLM提取失败: {e}", exc_info=True)

            # 4. 合并去重
            if len(all_entities) > 0:
                logger.info(f"[TextProcessor] 合并前共有 {len(all_entities)} 个实体")
                merged_entities = self._merge_entities(all_entities)
                logger.info(f"[TextProcessor] 合并后得到 {len(merged_entities)} 个唯一实体")
            else:
                logger.warning("[TextProcessor] 没有提取到任何实体!")
                merged_entities = []

            # 5. 实体消歧
            if merged_entities and len(merged_entities) > 1:
                logger.info(f"[TextProcessor] 开始实体消歧，共 {len(merged_entities)} 个实体")
                entity_groups = await self.llm_disambiguator.disambiguate_entities(merged_entities, text)
                logger.info(f"[TextProcessor] 实体消歧完成，生成 {len(entity_groups)} 个实体组")

                # 将实体组转换为标准实体格式
                merged_entities = self._convert_entity_groups_to_entities(entity_groups, text)
                logger.info(f"[TextProcessor] 转换后得到 {len(merged_entities)} 个标准实体")

            # 6. 指代消解
            if merged_entities:
                logger.info(f"[TextProcessor] 开始指代消解")
                merged_entities = await self.llm_disambiguator.resolve_coreference(text, merged_entities)
                logger.info(f"[TextProcessor] 指代消解完成")

            logger.info(f"[TextProcessor] 最终提取结果: {len(merged_entities)} 个实体, {len(all_relationships)} 个关系")
            return merged_entities, all_relationships

        except Exception as e:
            logger.error(f"[TextProcessor] 实体提取异常: {e}", exc_info=True)
            return [], []
    
    def _convert_entity_groups_to_entities(self, entity_groups: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """将实体组转换为标准实体格式
        
        消歧后的实体组格式为：
        {
            "entity_id": "...",
            "canonical_name": "...",
            "mentions": ["...", "..."],
            "entity_type": "...",
            "confidence": 0.95
        }
        
        需要转换为标准格式：
        {
            "text": "...",
            "type": "...",
            "start_pos": 0,
            "end_pos": 10,
            "confidence": 0.95
        }
        
        Args:
            entity_groups: 实体组列表
            text: 原始文本
            
        Returns:
            标准格式的实体列表
        """
        entities = []
        
        for group in entity_groups:
            canonical_name = group.get('canonical_name', '')
            entity_type = group.get('entity_type', 'UNKNOWN')
            confidence = group.get('confidence', 0.7)
            
            # 在文本中查找标准化名称的位置
            start_pos = text.find(canonical_name)
            if start_pos == -1:
                # 如果找不到，使用第一个提及
                mentions = group.get('mentions', [])
                if mentions:
                    canonical_name = mentions[0]
                    start_pos = text.find(canonical_name)
                
                # 如果还是找不到，跳过这个实体
                if start_pos == -1:
                    logger.warning(f"无法在文本中找到实体: {canonical_name}")
                    continue
            
            end_pos = start_pos + len(canonical_name)
            
            entity = {
                'text': canonical_name,
                'type': entity_type,
                'start_pos': start_pos,
                'end_pos': end_pos,
                'confidence': confidence,
                'entity_id': group.get('entity_id', ''),
                'mentions': group.get('mentions', [])
            }
            entities.append(entity)
        
        return entities
    
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
        logger.info(f"[TextProcessor] 同步提取实体和关系, 文本长度={len(text)}, knowledge_base_id={self.knowledge_base_id}")

        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在异步环境中，创建新任务
                import nest_asyncio
                nest_asyncio.apply()
                result = loop.run_until_complete(self.extract_entities_relationships(text))
            else:
                # 如果没有运行的事件循环，使用run_until_complete
                result = loop.run_until_complete(self.extract_entities_relationships(text))

            entities, relationships = result
            logger.info(f"[TextProcessor] 同步提取完成: {len(entities)} 个实体, {len(relationships)} 个关系")
            return result

        except RuntimeError:
            # 没有事件循环，创建新的
            logger.info("[TextProcessor] 创建新的事件循环进行提取")
            result = asyncio.run(self.extract_entities_relationships(text))
            entities, relationships = result
            logger.info(f"[TextProcessor] 同步提取完成(新循环): {len(entities)} 个实体, {len(relationships)} 个关系")
            return result

        except Exception as e:
            logger.error(f"[TextProcessor] 同步实体提取失败: {e}", exc_info=True)
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
