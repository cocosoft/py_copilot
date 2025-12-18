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
    
    @staticmethod
    def get_parameter_with_priority(
        db: Session, 
        model_id: int,
        param_name: str
    ) -> Dict[str, Any]:
        """
        根据参数优先级获取最终参数值（模型级>类型级>系统级）
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            param_name: 参数名称
            
        Returns:
            参数信息字典，包含最终值和来源信息
        """
        from app.models.supplier_db import ModelDB, ModelParameter
        from app.models.model_category import ModelCategory
        from app.services.parameter_management.system_parameter_manager import SystemParameterManager
        
        # 1. 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 2. 获取系统级参数（最低优先级）
        system_param = None
        active_system_template = SystemParameterManager.get_active_system_parameter_template(db)
        if active_system_template and active_system_template.parameters:
            system_param = next((p for p in active_system_template.parameters 
                              if p.get('name') == param_name), None)
        
        # 3. 获取类型级参数（中等优先级）
        type_param = None
        if model.model_type_id:
            model_type = db.query(ModelCategory).filter(ModelCategory.id == model.model_type_id).first()
            if model_type and model_type.default_parameters:
                # 处理默认参数
                default_params = model_type.default_parameters
                if isinstance(default_params, str):
                    import json
                    default_params = json.loads(default_params)
                
                if isinstance(default_params, dict) and param_name in default_params:
                    type_param = {
                        'name': param_name,
                        'value': default_params[param_name],
                        'source': 'model_type',
                        'model_type_id': model.model_type_id
                    }
        
        # 4. 获取模型级参数（最高优先级）
        model_param = db.query(ModelParameter).filter(
            ModelParameter.model_id == model_id,
            ModelParameter.parameter_name == param_name
        ).first()
        
        # 5. 确定最终参数（优先级：模型级>类型级>系统级）
        final_param = {
            'name': param_name,
            'value': None,
            'source': 'none',
            'parameter_id': None,
            'is_override': False
        }
        
        if model_param:
            # 模型级参数优先
            final_param['value'] = ParameterNormalizer._convert_value(
                model_param.parameter_value, model_param.parameter_type
            )
            final_param['source'] = 'model'
            final_param['parameter_id'] = model_param.id
            final_param['is_override'] = model_param.is_override
        elif type_param:
            # 类型级参数次之
            final_param['value'] = type_param['value']
            final_param['source'] = type_param['source']
            final_param['model_type_id'] = type_param['model_type_id']
        elif system_param:
            # 系统级参数最后
            final_param['value'] = system_param.get('default_value')
            final_param['source'] = 'system'
        
        return final_param
    
    @staticmethod
    def get_all_parameters_with_priority(
        db: Session, 
        model_id: int
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取模型的所有参数，考虑优先级（模型级>类型级>系统级）
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            参数字典，键为参数名，值为包含最终值和来源信息的参数对象
        """
        from app.models.supplier_db import ModelDB, ModelParameter
        from app.models.model_category import ModelCategory
        from app.services.parameter_management.system_parameter_manager import SystemParameterManager
        from app.services.parameter_management.parameter_manager import ParameterManager
        
        # 获取所有参数源
        all_params = {}
        
        # 1. 获取系统级参数（最低优先级）
        active_system_template = SystemParameterManager.get_active_system_parameter_template(db)
        if active_system_template and active_system_template.parameters:
            for param in active_system_template.parameters:
                param_name = param.get('name')
                if param_name:
                    all_params[param_name] = {
                        'name': param_name,
                        'value': param.get('default_value'),
                        'source': 'system',
                        'parameter_id': None,
                        'is_override': False,
                        'type': param.get('type', 'string')
                    }
        
        # 2. 获取类型级参数（中等优先级，覆盖系统级）
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if model and model.model_type_id:
            model_type = db.query(ModelCategory).filter(ModelCategory.id == model.model_type_id).first()
            if model_type and model_type.default_parameters:
                default_params = model_type.default_parameters
                if isinstance(default_params, str):
                    import json
                    default_params = json.loads(default_params)
                
                if isinstance(default_params, dict):
                    for param_name, param_value in default_params.items():
                        all_params[param_name] = {
                            'name': param_name,
                            'value': param_value,
                            'source': 'model_type',
                            'model_type_id': model.model_type_id,
                            'parameter_id': None,
                            'is_override': False,
                            'type': type(param_value).__name__
                        }
        
        # 3. 获取模型级参数（最高优先级，覆盖类型级和系统级）
        model_params = db.query(ModelParameter).filter(ModelParameter.model_id == model_id).all()
        for param in model_params:
            param_name = param.parameter_name
            param_value = ParameterNormalizer._convert_value(
                param.parameter_value, param.parameter_type
            )
            all_params[param_name] = {
                'name': param_name,
                'value': param_value,
                'source': 'model',
                'parameter_id': param.id,
                'is_override': param.is_override,
                'type': param.parameter_type
            }
        
        return all_params
