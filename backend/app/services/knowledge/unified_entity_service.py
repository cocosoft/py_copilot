"""
统一实体识别服务模块

整合多种实体识别方法，包括：
1. 基于规则的实体识别
2. 基于LLM的实体提取
3. 基于传统NLP的实体识别

提供统一的接口和服务管理功能
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from sqlalchemy.orm import Session

from app.services.knowledge.extraction.llm_extractor import LLMEntityExtractor
from app.services.knowledge.entity_config_manager import EntityConfigManager
from app.utils.entity_recognizer import EntityRecognizer

logger = logging.getLogger(__name__)


class UnifiedEntityService:
    """统一实体识别服务，整合多种实体识别方法"""

    def __init__(self, knowledge_base_id: int = None):
        """
        初始化统一实体识别服务

        Args:
            knowledge_base_id: 知识库ID，用于加载知识库级配置
        """
        self.knowledge_base_id = knowledge_base_id
        
        # 初始化各实体识别组件
        self.entity_config_manager = EntityConfigManager(knowledge_base_id)
        self.llm_extractor = LLMEntityExtractor()
        self.entity_recognizer = EntityRecognizer()
        
        # 服务配置
        self.config = {
            "enabled_methods": {
                "rule_based": True,
                "llm_based": True,
                "nlp_based": False  # 传统NLP方法暂时禁用
            },
            "confidence_threshold": 0.7,
            "merge_entities": True
        }

    def recognize_entities(self, text: str, entity_types: List[str] = None, 
                         method: str = "auto") -> List[Dict[str, Union[str, float, int]]]:
        """
        识别文本中的实体

        Args:
            text: 要分析的文本
            entity_types: 要识别的实体类型列表（可选）
            method: 识别方法："auto"（自动选择）、"rule_based"（基于规则）、"llm_based"（基于LLM）

        Returns:
            实体信息列表，每个实体包含：
            - text: 实体文本
            - type: 实体类型
            - start: 开始位置
            - end: 结束位置
            - confidence: 置信度
            - method: 识别方法
        """
        try:
            logger.info(f"[UnifiedEntityService.recognize_entities] 开始识别实体，文本长度: {len(text)}, 方法: {method}")
            
            if method == "auto":
                # 自动选择方法：短文本使用基于规则，长文本使用LLM
                if len(text) < 1000:
                    method = "rule_based"
                else:
                    method = "llm_based"
            
            entities = []
            
            if method == "rule_based" and self.config["enabled_methods"]["rule_based"]:
                entities = self._recognize_with_rules(text, entity_types)
            elif method == "llm_based" and self.config["enabled_methods"]["llm_based"]:
                entities = self._recognize_with_llm(text, entity_types)
            
            # 过滤低置信度实体
            entities = [e for e in entities if e.get("confidence", 1.0) >= self.config["confidence_threshold"]]
            
            # 合并重叠实体
            if self.config["merge_entities"]:
                entities = self._merge_overlapping_entities(entities)
            
            logger.info(f"[UnifiedEntityService.recognize_entities] 识别完成，找到 {len(entities)} 个实体")
            return entities
            
        except Exception as e:
            logger.error(f"[UnifiedEntityService.recognize_entities] 实体识别失败: {e}")
            return []

    def batch_recognize_entities(self, texts: List[str], entity_types: List[str] = None, 
                                method: str = "auto") -> List[List[Dict[str, Union[str, float, int]]]]:
        """
        批量识别文本中的实体

        Args:
            texts: 要分析的文本列表
            entity_types: 要识别的实体类型列表（可选）
            method: 识别方法

        Returns:
            实体信息列表的列表
        """
        try:
            logger.info(f"[UnifiedEntityService.batch_recognize_entities] 开始批量识别，文本数量: {len(texts)}")
            
            results = []
            for text in texts:
                entities = self.recognize_entities(text, entity_types, method)
                results.append(entities)
            
            logger.info(f"[UnifiedEntityService.batch_recognize_entities] 批量识别完成")
            return results
            
        except Exception as e:
            logger.error(f"[UnifiedEntityService.batch_recognize_entities] 批量实体识别失败: {e}")
            return [[] for _ in texts]

    def get_entities_by_type(self, text: str, entity_types: List[str] = None, 
                            method: str = "auto") -> Dict[str, List[Dict[str, Union[str, float, int]]]]:
        """
        按类型分组的实体识别结果

        Args:
            text: 要分析的文本
            entity_types: 要识别的实体类型列表（可选）
            method: 识别方法

        Returns:
            按实体类型分组的字典
        """
        try:
            entities = self.recognize_entities(text, entity_types, method)
            
            # 按类型分组
            entities_by_type = {}
            for entity in entities:
                entity_type = entity.get("type")
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity)
            
            return entities_by_type
            
        except Exception as e:
            logger.error(f"[UnifiedEntityService.get_entities_by_type] 获取实体类型分组失败: {e}")
            return {}

    def get_entity_summary(self, text: str, entity_types: List[str] = None, 
                         method: str = "auto") -> Dict[str, Any]:
        """
        获取实体识别汇总信息

        Args:
            text: 要分析的文本
            entity_types: 要识别的实体类型列表（可选）
            method: 识别方法

        Returns:
            实体汇总信息，包含：
            - total_entities: 实体总数
            - entity_types: 实体类型列表
            - entity_names: 实体名称列表
            - entity_counts_by_type: 按类型统计的实体数量
        """
        try:
            entities = self.recognize_entities(text, entity_types, method)
            
            # 统计信息
            entity_types_set = set()
            entity_names = []
            entity_counts_by_type = {}
            
            for entity in entities:
                entity_type = entity.get("type")
                entity_text = entity.get("text")
                
                entity_types_set.add(entity_type)
                entity_names.append(entity_text)
                
                if entity_type not in entity_counts_by_type:
                    entity_counts_by_type[entity_type] = 0
                entity_counts_by_type[entity_type] += 1
            
            summary = {
                "total_entities": len(entities),
                "entity_types": list(entity_types_set),
                "entity_names": entity_names,
                "entity_counts_by_type": entity_counts_by_type
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"[UnifiedEntityService.get_entity_summary] 获取实体汇总信息失败: {e}")
            return {
                "total_entities": 0,
                "entity_types": [],
                "entity_names": [],
                "entity_counts_by_type": {}
            }

    def _recognize_with_rules(self, text: str, entity_types: List[str] = None) -> List[Dict[str, Union[str, float, int]]]:
        """
        使用基于规则的方法识别实体

        Args:
            text: 要分析的文本
            entity_types: 要识别的实体类型列表（可选）

        Returns:
            实体信息列表
        """
        try:
            entities = []
            
            # 从配置中获取实体类型和规则
            config = self.entity_config_manager.get_config()
            entity_types_config = config.get("entity_types", {})
            extraction_rules = config.get("extraction_rules", {})
            
            # 确定要处理的实体类型
            target_types = entity_types if entity_types else list(entity_types_config.keys())
            
            # 应用规则进行实体识别
            for entity_type in target_types:
                if not entity_types_config.get(entity_type, {}).get("enabled", True):
                    continue
                
                rules = extraction_rules.get(entity_type, [])
                for rule in rules:
                    if not rule.get("enabled", True):
                        continue
                    
                    # 这里可以实现基于规则的实体识别
                    # 由于当前系统中规则识别功能有限，这里暂时返回空结果
                    # 实际项目中应该实现规则匹配逻辑
                    pass
            
            return entities
            
        except Exception as e:
            logger.error(f"[UnifiedEntityService._recognize_with_rules] 基于规则的实体识别失败: {e}")
            return []

    def _recognize_with_llm(self, text: str, entity_types: List[str] = None) -> List[Dict[str, Union[str, float, int]]]:
        """
        使用基于LLM的方法识别实体

        Args:
            text: 要分析的文本
            entity_types: 要识别的实体类型列表（可选）

        Returns:
            实体信息列表
        """
        try:
            # 使用LLM提取器识别实体
            entities = self.llm_extractor.extract_entities(text)
            
            # 过滤指定类型的实体
            if entity_types:
                entities = [e for e in entities if e.get("type") in entity_types]
            
            # 添加识别方法标记
            for entity in entities:
                entity["method"] = "llm_based"
            
            return entities
            
        except Exception as e:
            logger.error(f"[UnifiedEntityService._recognize_with_llm] 基于LLM的实体识别失败: {e}")
            return []

    def _merge_overlapping_entities(self, entities: List[Dict[str, Union[str, float, int]]]) -> List[Dict[str, Union[str, float, int]]]:
        """
        合并重叠的实体

        Args:
            entities: 实体信息列表

        Returns:
            合并后的实体信息列表
        """
        if not entities:
            return entities
        
        # 按开始位置排序
        sorted_entities = sorted(entities, key=lambda x: x.get("start", 0))
        
        merged = []
        current = sorted_entities[0]
        
        for entity in sorted_entities[1:]:
            current_end = current.get("end", 0)
            entity_start = entity.get("start", 0)
            
            if entity_start < current_end:
                # 重叠，选择置信度高的
                if entity.get("confidence", 0) > current.get("confidence", 0):
                    current = entity
            else:
                merged.append(current)
                current = entity
        
        merged.append(current)
        return merged

    def update_config(self, config: Dict[str, Any]):
        """
        更新服务配置

        Args:
            config: 配置字典
        """
        self.config.update(config)
        logger.info(f"[UnifiedEntityService.update_config] 服务配置已更新: {config}")

    def get_config(self) -> Dict[str, Any]:
        """
        获取服务配置

        Returns:
            配置字典
        """
        return self.config


# 创建全局统一实体服务实例
unified_entity_service = UnifiedEntityService()
