"""参数归一化引擎，负责将不同供应商的模型参数统一转换为标准格式"""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.parameter_template import ParameterTemplate
from app.models.supplier_db import ModelDB
from app.models.model_category import ModelCategory


class ParameterNormalizer:
    """参数归一化器，实现不同供应商参数的统一转换"""
    
    @staticmethod
    def get_normalization_rules(supplier_id: int, model_type: str = None) -> Dict[str, Any]:
        """
        获取供应商的参数归一化规则
        
        Args:
            supplier_id: 供应商ID
            model_type: 模型类型（可选）
            
        Returns:
            归一化规则字典
        """
        from app.models.parameter_normalization import ParameterNormalizationRule
        from sqlalchemy.orm import Session
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        rules = {}
        
        try:
            # 1. 查询默认规则（supplier_id=None, model_type=None）
            default_rules = db.query(ParameterNormalizationRule).filter(
                ParameterNormalizationRule.supplier_id == None,
                ParameterNormalizationRule.model_type == None,
                ParameterNormalizationRule.is_active == True
            ).all()
            
            # 2. 查询供应商特定规则（supplier_id=supplier_id, model_type=None）
            supplier_specific_rules = db.query(ParameterNormalizationRule).filter(
                ParameterNormalizationRule.supplier_id == supplier_id,
                ParameterNormalizationRule.model_type == None,
                ParameterNormalizationRule.is_active == True
            ).all()
            
            # 3. 查询供应商-模型类型特定规则（supplier_id=supplier_id, model_type=model_type）
            supplier_model_rules = []
            if model_type:
                supplier_model_rules = db.query(ParameterNormalizationRule).filter(
                    ParameterNormalizationRule.supplier_id == supplier_id,
                    ParameterNormalizationRule.model_type == model_type,
                    ParameterNormalizationRule.is_active == True
                ).all()
            
            # 合并所有规则，优先级：供应商-模型类型规则 > 供应商特定规则 > 默认规则
            all_rules = default_rules + supplier_specific_rules + supplier_model_rules
            
            for rule in all_rules:
                rule_dict = {
                    "standard_name": rule.standard_name,
                    "type": rule.param_type,
                    "default": rule.default_value
                }
                
                # 添加映射信息
                if rule.mapped_from:
                    rule_dict["mapped_from"] = rule.mapped_from
                
                # 添加范围信息
                if rule.range_min is not None and rule.range_max is not None:
                    rule_dict["range"] = [rule.range_min, rule.range_max]
                
                # 添加正则表达式
                if rule.regex_pattern:
                    rule_dict["regex"] = rule.regex_pattern
                
                # 添加枚举值
                if rule.enum_values:
                    rule_dict["enum_values"] = rule.enum_values
                
                # 使用参数名作为键
                rules[rule.param_name] = rule_dict
        finally:
            db.close()
        
        # 如果数据库中没有规则，使用默认规则
        if not rules:
            rules = {
                "temperature": {"standard_name": "temperature", "type": "float", "range": [0.0, 1.0], "default": 0.7},
                "top_p": {"standard_name": "top_p", "type": "float", "range": [0.0, 1.0], "default": 1.0},
                "max_tokens": {"standard_name": "max_tokens", "type": "int", "range": [1, 100000], "default": 1000},
                "frequency_penalty": {"standard_name": "frequency_penalty", "type": "float", "range": [-2.0, 2.0], "default": 0.0},
                "presence_penalty": {"standard_name": "presence_penalty", "type": "float", "range": [-2.0, 2.0], "default": 0.0},
                "stop": {"standard_name": "stop", "type": "array", "default": []},
                "stream": {"standard_name": "stream", "type": "bool", "default": False}
            }
        
        return rules
    
    @staticmethod
    def normalize_parameters(supplier_id: int, raw_params: Dict[str, Any], model_type: str = None) -> Dict[str, Any]:
        """
        将供应商原始参数转换为标准格式
        
        Args:
            supplier_id: 供应商ID
            raw_params: 供应商原始参数
            model_type: 模型类型（可选）
            
        Returns:
            标准格式参数
        """
        rules = ParameterNormalizer.get_normalization_rules(supplier_id, model_type)
        normalized_params = {}
        
        # 处理参数映射
        for param_name, value in raw_params.items():
            # 查找归一化规则
            rule = None
            
            # 首先检查是否有直接匹配的规则
            if param_name in rules:
                rule = rules[param_name]
            else:
                # 检查是否有从其他参数映射来的规则
                for r in rules.values():
                    if r.get("mapped_from") == param_name:
                        rule = r
                        break
            
            if rule:
                standard_name = rule["standard_name"]
                param_type = rule["type"]
                
                # 转换参数类型
                normalized_value = ParameterNormalizer._convert_value(value, param_type)
                
                # 应用范围限制
                if "range" in rule:
                    min_val, max_val = rule["range"]
                    if normalized_value < min_val:
                        normalized_value = min_val
                    elif normalized_value > max_val:
                        normalized_value = max_val
                
                normalized_params[standard_name] = normalized_value
        
        # 添加默认参数（如果未提供）
        for param_name, rule in rules.items():
            standard_name = rule["standard_name"]
            if standard_name not in normalized_params and "default" in rule:
                normalized_params[standard_name] = rule["default"]
        
        return normalized_params
    
    @staticmethod
    def _convert_value(value: Any, type_name: str) -> Any:
        """
        转换参数值到指定类型
        
        Args:
            value: 参数值
            type_name: 目标类型名称
            
        Returns:
            转换后的参数值
        """
        try:
            if type_name == "int":
                return int(value)
            elif type_name == "float":
                return float(value)
            elif type_name == "bool":
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ["true", "1", "yes", "y"]
            elif type_name == "string":
                return str(value)
            elif type_name == "array":
                if isinstance(value, list):
                    return value
                return json.loads(value)
            elif type_name == "object":
                if isinstance(value, dict):
                    return value
                return json.loads(value)
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            return value
    
    @staticmethod
    def denormalize_parameters(supplier_id: int, standard_params: Dict[str, Any], model_type: str = None) -> Dict[str, Any]:
        """
        将标准格式参数转换为供应商特定格式
        
        Args:
            supplier_id: 供应商ID
            standard_params: 标准格式参数
            model_type: 模型类型（可选）
            
        Returns:
            供应商特定格式参数
        """
        rules = ParameterNormalizer.get_normalization_rules(supplier_id, model_type)
        denormalized_params = {}
        
        # 处理参数反向映射
        for standard_name, value in standard_params.items():
            for param_name, rule in rules.items():
                if rule["standard_name"] == standard_name:
                    # 使用供应商特定的参数名
                    supplier_param_name = rule.get("mapped_from", param_name)
                    denormalized_params[supplier_param_name] = value
                    break
        
        return denormalized_params
    
    @staticmethod
    def normalize_model_parameters(db: Session, model_id: int, raw_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        对特定模型的参数进行归一化处理
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            raw_params: 原始参数
            
        Returns:
            归一化后的参数
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 获取模型类型
        model_type = model.model_type.name if model.model_type else None
        
        # 进行参数归一化
        return ParameterNormalizer.normalize_parameters(
            supplier_id=model.supplier_id,
            raw_params=raw_params,
            model_type=model_type
        )
    
    @staticmethod
    def apply_normalization_to_template(db: Session, template_id: int) -> ParameterTemplate:
        """
        对参数模板应用归一化规则，将参数转换为标准格式
        
        Args:
            db: 数据库会话
            template_id: 参数模板ID
            
        Returns:
            更新后的参数模板
        """
        # 获取参数模板
        template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"参数模板ID {template_id} 不存在")
        
        # 获取归一化规则
        supplier_id = None
        model_type = None
        
        # 根据模板级别获取供应商ID和模型类型
        if template.level == "model" and template.level_id:
            model = db.query(ModelDB).filter(ModelDB.id == template.level_id).first()
            if model:
                supplier_id = model.supplier_id
                model_type = model.model_type.name if model.model_type else None
        elif template.level == "model_type" and template.level_id:
            model_category = db.query(ModelCategory).filter(ModelCategory.id == template.level_id).first()
            if model_category and hasattr(model_category, 'supplier_id'):
                supplier_id = model_category.supplier_id
                model_type = model_category.name
        elif template.level == "supplier" and template.level_id:
            supplier_id = template.level_id
        
        # 获取归一化规则（如果有供应商ID）
        if supplier_id:
            rules = ParameterNormalizer.get_normalization_rules(supplier_id, model_type)
        else:
            # 使用默认规则
            rules = ParameterNormalizer.get_normalization_rules(0)
        
        # 对模板参数应用归一化
        normalized_params = []
        for param in template.parameters:
            normalized_param = param.copy()
            
            # 检查参数是否在归一化规则中
            rule = None
            param_name = param["name"]
            
            # 首先检查是否有直接匹配的规则
            if param_name in rules:
                rule = rules[param_name]
            else:
                # 检查是否有从其他参数映射来的规则
                for r in rules.values():
                    if r.get("mapped_from") == param_name:
                        rule = r
                        break
            
            if rule:
                # 标记为标准参数
                normalized_param["is_standard"] = True
                
                # 转换参数类型
                param_value = param.get("default_value")
                if param_value is not None:
                    normalized_value = ParameterNormalizer._convert_value(param_value, rule["type"])
                    normalized_param["default_value"] = normalized_value
                
                # 更新参数名称为标准名称
                normalized_param["name"] = rule["standard_name"]
                
                # 应用范围限制
                if "range" in rule and param_value is not None:
                    min_val, max_val = rule["range"]
                    if normalized_value < min_val:
                        normalized_param["default_value"] = min_val
                    elif normalized_value > max_val:
                        normalized_param["default_value"] = max_val
            else:
                # 非标准参数
                normalized_param["is_standard"] = False
            
            normalized_params.append(normalized_param)
        
        # 更新模板参数
        template.parameters = normalized_params
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def validate_normalized_params(params: Dict[str, Any], rules: Dict[str, Any] = None) -> bool:
        """
        验证归一化后的参数是否符合规则
        
        Args:
            params: 归一化后的参数
            rules: 归一化规则（可选）
            
        Returns:
            验证结果
        """
        if not rules:
            rules = ParameterNormalizer.get_normalization_rules(0)  # 使用默认规则
        
        for param_name, value in params.items():
            if param_name in rules:
                rule = rules[param_name]
                
                # 类型验证
                if "type" in rule:
                    expected_type = rule["type"]
                    if expected_type == "int" and not isinstance(value, int):
                        return False
                    elif expected_type == "float" and not isinstance(value, float):
                        return False
                    elif expected_type == "bool" and not isinstance(value, bool):
                        return False
                    elif expected_type == "array" and not isinstance(value, list):
                        return False
                    elif expected_type == "object" and not isinstance(value, dict):
                        return False
                
                # 范围验证
                if "range" in rule:
                    min_val, max_val = rule["range"]
                    if value < min_val or value > max_val:
                        return False
        
        return True
