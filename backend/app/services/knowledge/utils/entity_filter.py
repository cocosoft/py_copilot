"""
实体过滤模块

用于过滤低质量、无意义的实体
"""

import re
from typing import List, Dict, Any


class EntityFilter:
    """实体过滤器"""
    
    # 停用词 - 无意义的单字
    STOP_WORDS = {
        '的', '是', '在', '和', '与', '或', '了', '着', '过', '地', '得',
        '啊', '呢', '吧', '吗', '哦', '嗯', '唉', '哎', '哼',
        '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
        '两', '几', '多', '少', '千', '万', '亿',
    }
    
    # 需要过滤的实体类型
    LOW_QUALITY_TYPES = {
        'CARDINAL',  # 基数词 - 纯数字
    }
    
    @classmethod
    def is_valid_entity(cls, entity_text: str, entity_type: str) -> bool:
        """
        检查实体是否有效
        
        Args:
            entity_text: 实体文本
            entity_type: 实体类型
            
        Returns:
            是否有效
        """
        if not entity_text or not entity_text.strip():
            return False
        
        text = entity_text.strip()
        
        # 1. 长度检查 - 至少2个字符
        if len(text) < 2:
            return False
        
        # 2. 纯数字过滤
        if re.match(r'^[0-9]+$', text):
            return False
        
        # 3. 纯数字+标点过滤
        if re.match(r'^[0-9.]+$', text):
            return False
        
        # 4. 停用词过滤
        if text in cls.STOP_WORDS:
            return False
        
        # 5. 序号模式过滤 (如"第1", "第2")
        if re.match(r'^第[0-9一二三四五六七八九十]+$', text) and len(text) <= 4:
            return False
        
        # 6. 特殊类型过滤
        if entity_type in cls.LOW_QUALITY_TYPES:
            # CARDINAL类型需要额外检查
            # 如果主要是数字，则过滤
            digit_ratio = sum(1 for c in text if c.isdigit()) / len(text)
            if digit_ratio > 0.5:  # 数字占比超过50%
                return False
        
        # 7. 日期类型特殊处理 - 过滤纯数字日期
        if entity_type == 'DATE':
            if re.match(r'^[0-9]{1,2}$', text):  # 纯数字且1-2位
                return False
        
        # 8. ORDINAL类型特殊处理 - 过滤过短的
        if entity_type == 'ORDINAL' and len(text) <= 3:
            return False
        
        return True
    
    @classmethod
    def filter_entities(cls, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤实体列表
        
        Args:
            entities: 实体列表
            
        Returns:
            过滤后的实体列表
        """
        valid_entities = []
        
        for entity in entities:
            text = entity.get('text', '')
            entity_type = entity.get('type', '')
            
            if cls.is_valid_entity(text, entity_type):
                valid_entities.append(entity)
        
        return valid_entities
    
    @classmethod
    def get_filter_stats(cls, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取过滤统计信息
        
        Args:
            entities: 实体列表
            
        Returns:
            统计信息
        """
        total = len(entities)
        filtered = 0
        reasons = {}
        
        for entity in entities:
            text = entity.get('text', '')
            entity_type = entity.get('type', '')
            
            if not cls.is_valid_entity(text, entity_type):
                filtered += 1
                
                # 统计过滤原因
                if len(text) < 2:
                    reasons['too_short'] = reasons.get('too_short', 0) + 1
                elif re.match(r'^[0-9]+$', text):
                    reasons['pure_digits'] = reasons.get('pure_digits', 0) + 1
                elif text in cls.STOP_WORDS:
                    reasons['stop_word'] = reasons.get('stop_word', 0) + 1
                elif entity_type in cls.LOW_QUALITY_TYPES:
                    reasons['low_quality_type'] = reasons.get('low_quality_type', 0) + 1
                else:
                    reasons['other'] = reasons.get('other', 0) + 1
        
        return {
            'total': total,
            'valid': total - filtered,
            'filtered': filtered,
            'filter_rate': filtered / total if total > 0 else 0,
            'reasons': reasons
        }
