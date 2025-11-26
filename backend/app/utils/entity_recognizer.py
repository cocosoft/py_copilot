"""命名实体识别工具模块"""
from typing import Dict, List, Optional, Set, Tuple, Union

from transformers import pipeline


class EntityRecognizer:
    """命名实体识别器类，用于识别文本中的命名实体"""

    def __init__(self, model_name: str = "dbmdz/bert-large-cased-finetuned-conll03-english"):
        """
        初始化命名实体识别器

        Args:
            model_name: 实体识别模型名称
        """
        self.model_name = model_name
        self.ner_pipeline = pipeline("ner", model=model_name, grouped_entities=True)

    def recognize_entities(self, text: str) -> List[Dict[str, Union[str, float, int]]]:
        """
        识别文本中的命名实体

        Args:
            text: 要分析的文本

        Returns:
            包含实体信息的字典列表
        """
        results = self.ner_pipeline(text)
        return results

    def batch_recognize_entities(self, texts: List[str]) -> List[List[Dict[str, Union[str, float, int]]]]:
        """
        批量识别文本中的命名实体

        Args:
            texts: 要分析的文本列表

        Returns:
            实体识别结果列表
        """
        return [self.recognize_entities(text) for text in texts]

    def get_entities_by_type(self, text: str) -> Dict[str, List[Dict[str, Union[str, float, int]]]]:
        """
        按实体类型分组获取识别结果

        Args:
            text: 要分析的文本

        Returns:
            按实体类型分组的字典
        """
        entities = self.recognize_entities(text)
        entities_by_type = {}
        
        for entity in entities:
            entity_type = entity.get("entity_group", "")
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        return entities_by_type

    def get_entity_summary(self, text: str) -> Dict[str, Union[int, List[str], Set[str], Dict[str, int]]]:
        """
        获取实体识别的汇总信息

        Args:
            text: 要分析的文本

        Returns:
            实体汇总信息
        """
        entities = self.recognize_entities(text)
        
        # 提取实体类型和实体名称
        entity_types = set()
        entity_names = []
        entity_counts = {}
        
        for entity in entities:
            entity_type = entity.get("entity_group", "")
            entity_text = entity.get("word", "")
            
            entity_types.add(entity_type)
            entity_names.append(entity_text)
            
            if entity_type not in entity_counts:
                entity_counts[entity_type] = 0
            entity_counts[entity_type] += 1
        
        return {
            "total_entities": len(entities),
            "entity_types": list(entity_types),
            "entity_names": entity_names,
            "entity_counts_by_type": entity_counts
        }

    def filter_entities_by_type(self, text: str, entity_types: List[str]) -> List[Dict[str, Union[str, float, int]]]:
        """
        按指定类型过滤实体

        Args:
            text: 要分析的文本
            entity_types: 要过滤的实体类型列表

        Returns:
            过滤后的实体列表
        """
        entities = self.recognize_entities(text)
        return [entity for entity in entities if entity.get("entity_group") in entity_types]


# 创建全局实体识别器实例
entity_recognizer = EntityRecognizer()