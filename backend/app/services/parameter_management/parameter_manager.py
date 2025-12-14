"""模型参数管理服务"""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.model_category import ModelCategory
from app.models.supplier_db import ModelDB, ModelParameter
from app.models.parameter_template import ParameterTemplate
from app.schemas.model_category import ModelCategoryUpdate
from app.schemas.model_management import ModelParameterCreate, ModelParameterUpdate
from app.services.parameter_management.parameter_normalizer import ParameterNormalizer
from app.services.parameter_management.system_parameter_manager import SystemParameterManager


class ParameterManager:
    """参数管理器，负责模型参数的继承、覆盖和合并逻辑"""
    
    @staticmethod
    def get_model_parameters(db: Session, model_id: int) -> List[Dict[str, Any]]:
        """
        获取模型的完整参数配置，包括继承自类型的默认参数和模型自身的参数
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            合并后的完整参数配置列表，每个参数包含inherited字段
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            return []
        
        # 基础参数列表
        parameters_list = []
        
        # 1. 获取模型类型的默认参数
        default_params_dict = {}
        if model.model_type_id:
            model_type = db.query(ModelCategory).filter(ModelCategory.id == model.model_type_id).first()
            if model_type and model_type.default_parameters:
                # 处理默认参数（兼容不同的数据库JSON字段处理方式）
                default_params = model_type.default_parameters
                if isinstance(default_params, str):
                    import json
                    default_params = json.loads(default_params)
                
                # 添加默认参数到列表中，标记为继承
                from datetime import datetime
                temp_id_counter = -1  # 为默认参数生成临时负ID
                for param_name, param_value in default_params.items():
                    parameters_list.append({
                        "id": temp_id_counter,  # 使用临时负ID
                        "parameter_name": param_name,
                        "parameter_value": str(param_value),
                        "parameter_type": "string",  # 默认类型
                        "default_value": param_value,
                        "description": "",
                        "is_required": False,
                        "model_id": model_id,
                        "created_at": datetime.now(),  # 添加当前时间
                        "updated_at": datetime.now(),  # 添加当前时间
                        "inherited": True,
                        "parameter_source": "model_type",
                        "is_default": True,
                        "is_override": False
                    })
                    default_params_dict[param_name] = param_value
                    temp_id_counter -= 1
        
        # 2. 获取模型自身的参数（覆盖类型默认参数）
        model_params = db.query(ModelParameter).filter(ModelParameter.model_id == model_id).all()
        
        # 创建一个集合存储模型自身的参数名
        model_param_names = set()
        
        # 添加模型自身的参数到列表中，标记为非继承
        for param in model_params:
            # 转换参数值到字符串类型
            param_value = param.parameter_value
            
            parameters_list.append({
                "id": param.id,
                "parameter_name": param.parameter_name,
                "parameter_value": param_value,
                "parameter_type": param.parameter_type,
                "default_value": param.parameter_value,
                "description": param.description,
                "is_required": False,
                "model_id": model_id,
                "created_at": param.created_at,
                "updated_at": param.updated_at,
                "inherited": False,
                "parameter_source": param.parameter_source,
                "is_default": param.is_default,
                "is_override": param.is_override
            })
            
            model_param_names.add(param.parameter_name)
        
        # 3. 如果模型自身的参数覆盖了默认参数，将默认参数标记为非继承
        for param in parameters_list:
            if param["inherited"] and param["parameter_name"] in model_param_names:
                param["inherited"] = False
        
        return parameters_list
    
    @staticmethod
    def update_model_type_default_parameters(
        db: Session, 
        model_type_id: int, 
        parameters: Dict[str, Any]
    ) -> Optional[ModelCategory]:
        """
        更新模型类型的默认参数
        
        Args:
            db: 数据库会话
            model_type_id: 模型类型ID
            parameters: 要更新的默认参数
            
        Returns:
            更新后的模型类型对象，或None
        """
        model_type = db.query(ModelCategory).filter(ModelCategory.id == model_type_id).first()
        if not model_type:
            return None
        
        # 处理默认参数（兼容不同的数据库JSON字段处理方式）
        if model_type.default_parameters is None:
            current_params = {}
        elif isinstance(model_type.default_parameters, str):
            import json
            current_params = json.loads(model_type.default_parameters)
        else:
            current_params = model_type.default_parameters.copy()
            
        current_params.update(parameters)
        model_type.default_parameters = current_params
        
        db.commit()
        db.refresh(model_type)
        return model_type
    
    @staticmethod
    def create_or_update_model_parameter(
        db: Session, 
        model_id: int, 
        param_data: ModelParameterCreate
    ) -> ModelParameter:
        """
        创建或更新模型参数
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            param_data: 参数数据
            
        Returns:
            创建或更新后的参数对象
            
        Raises:
            ValueError: 当参数值无法转换为指定类型时
        """
        # 验证参数值与类型是否匹配
        ParameterManager._convert_parameter_value(param_data.parameter_value, param_data.parameter_type)
        
        # 检查参数是否已存在
        existing_param = db.query(ModelParameter).filter(
            ModelParameter.model_id == model_id, 
            ModelParameter.parameter_name == param_data.parameter_name
        ).first()
        
        if existing_param:
            # 更新现有参数
            existing_param.parameter_type = param_data.parameter_type
            existing_param.parameter_value = param_data.parameter_value
            existing_param.description = param_data.description
            existing_param.is_default = param_data.is_default
            existing_param.parameter_source = param_data.parameter_source
            existing_param.is_override = param_data.is_override
        else:
            # 创建新参数
            existing_param = ModelParameter(
                model_id=model_id,
                parameter_name=param_data.parameter_name,
                parameter_type=param_data.parameter_type,
                parameter_value=param_data.parameter_value,
                description=param_data.description,
                is_default=param_data.is_default,
                parameter_source=param_data.parameter_source,
                is_override=param_data.is_override
            )
            db.add(existing_param)
        
        db.commit()
        db.refresh(existing_param)
        return existing_param
    
    @staticmethod
    def delete_model_parameter(
        db: Session, 
        model_id: int, 
        parameter_name: str
    ) -> bool:
        """
        删除模型参数
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            parameter_name: 参数名称
            
        Returns:
            是否成功删除
        """
        param = db.query(ModelParameter).filter(
            ModelParameter.model_id == model_id,
            ModelParameter.parameter_name == parameter_name
        ).first()
        
        if param:
            db.delete(param)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_model_type_parameters(
        db: Session, 
        model_type_id: int
    ) -> Dict[str, Any]:
        """
        获取模型类型的默认参数
        
        Args:
            db: 数据库会话
            model_type_id: 模型类型ID
            
        Returns:
            默认参数配置
        """
        model_type = db.query(ModelCategory).filter(ModelCategory.id == model_type_id).first()
        if not model_type:
            return {}
        
        return model_type.default_parameters or {}
    
    @staticmethod
    def _convert_parameter_value(value: str, type_name: str) -> Any:
        """
        将字符串类型的参数值转换为指定类型
        
        Args:
            value: 字符串类型的参数值
            type_name: 参数类型名称
            
        Returns:
            转换后的参数值
            
        Raises:
            ValueError: 当参数值无法转换为指定类型时
        """
        try:
            if type_name == "int":
                return int(value)
            elif type_name == "float":
                return float(value)
            elif type_name == "bool":
                return value.lower() in ["true", "1", "yes", "y"]
            elif type_name == "json":
                return json.loads(value)
            elif type_name == "array":
                return json.loads(value)
            elif type_name == "object":
                return json.loads(value)
            elif type_name == "enum":
                # 枚举类型直接返回字符串值，验证在验证规则中进行
                return value
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            raise ValueError(f"参数值 '{value}' 无法转换为类型 '{type_name}'")
    
    @staticmethod
    def get_model_parameters_diff(
        db: Session, 
        model_id: int
    ) -> Dict[str, Any]:
        """
        获取模型参数与类型默认参数的差异
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            仅包含模型自身定义的参数（不包括继承的参数）
        """
        model_params = db.query(ModelParameter).filter(ModelParameter.model_id == model_id).all()
        diff_params = {}
        
        for param in model_params:
            param_value = ParameterManager._convert_parameter_value(param.parameter_value, param.parameter_type)
            diff_params[param.parameter_name] = {
                "value": param_value,
                "type": param.parameter_type,
                "description": param.description,
                "is_default": param.is_default,
                "parameter_source": param.parameter_source,
                "is_override": param.is_override
            }
        
        return diff_params
    
    @staticmethod
    def merge_parameters(parent_params, child_params):
        """
        合并父子参数，子参数覆盖父参数
        
        Args:
            parent_params: 父参数列表
            child_params: 子参数列表
            
        Returns:
            合并后的参数列表
        """
        # 确保参数列表不为None
        parent_params = parent_params or []
        child_params = child_params or []
        
        merged = {p['name']: p.copy() for p in parent_params}
        for child_param in child_params:
            param_name = child_param['name']
            if param_name in merged:
                merged[param_name].update(child_param)
                merged[param_name]['is_override'] = True
            else:
                merged[param_name] = child_param
        return list(merged.values())
    
    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[ParameterTemplate]:
        """
        获取单个参数模板
        
        Args:
            db: 数据库会话
            template_id: 参数模板ID
            
        Returns:
            参数模板对象，或None
        """
        return db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    
    @staticmethod
    def get_merged_parameters(db: Session, template_id: int) -> List[Dict[str, Any]]:
        """
        递归合并多层级参数模板
        
        Args:
            db: 数据库会话
            template_id: 参数模板ID
            
        Returns:
            合并后的参数列表
        """
        template = ParameterManager.get_template(db, template_id)
        if not template:
            return []
        
        if template.level == "system":
            # 系统级模板没有父模板
            return template.parameters
        
        if not template.parent_id:
            # 如果没有父模板，使用系统级参数作为默认参数
            system_params = []
            active_system_template = SystemParameterManager.get_active_system_parameter_template(db)
            if active_system_template:
                system_params = active_system_template.parameters
            return ParameterManager.merge_parameters(system_params, template.parameters)
            
        # 有父模板，递归合并
        parent_template = ParameterManager.get_template(db, template.parent_id)
        parent_params = ParameterManager.get_merged_parameters(db, parent_template.id)
        return ParameterManager.merge_parameters(parent_params, template.parameters)
    
    @staticmethod
    def validate_parameter(param: Dict[str, Any], param_value: Any = None) -> bool:
        """
        验证单个参数是否符合定义的验证规则
        
        Args:
            param: 参数定义（包含类型、验证规则等）
            param_value: 要验证的参数值，如果为None则使用param['default_value']
            
        Returns:
            True如果验证通过，否则False
            
        Raises:
            ValueError: 当参数验证失败时
        """
        # 如果没有提供值，使用默认值
        if param_value is None:
            if 'default_value' not in param and param.get('required', False):
                raise ValueError(f"参数 '{param['name']}' 是必填的，但没有提供值")
            param_value = param.get('default_value')
            
        # 1. 必填验证
        if param.get('required', False) and param_value is None:
            raise ValueError(f"参数 '{param['name']}' 是必填的")
            
        # 如果值为None且不是必填，则不需要进一步验证
        if param_value is None:
            return True
            
        # 2. 类型验证
        param_type = param.get('type', 'string')
        try:
            converted_value = ParameterManager._convert_parameter_value(str(param_value), param_type)
        except ValueError as e:
            raise ValueError(f"参数 '{param['name']}' 类型验证失败: {str(e)}")
            
        # 获取验证规则
        validation_rules = param.get('validation_rules', {})
        
        # 3. 范围验证（针对数值类型）
        if param_type in ['int', 'float']:
            if 'min' in validation_rules and converted_value < validation_rules['min']:
                raise ValueError(f"参数 '{param['name']}' 的值 {converted_value} 小于最小值 {validation_rules['min']}")
                
            if 'max' in validation_rules and converted_value > validation_rules['max']:
                raise ValueError(f"参数 '{param['name']}' 的值 {converted_value} 大于最大值 {validation_rules['max']}")
        
        # 4. 格式验证（针对字符串类型）
        if param_type == 'string' and 'regex' in validation_rules:
            import re
            if not re.match(validation_rules['regex'], str(param_value)):
                raise ValueError(f"参数 '{param['name']}' 的值 {param_value} 不符合格式要求")
        
        # 5. 枚举验证
        if param_type == 'enum' and 'enum_values' in validation_rules:
            if param_value not in validation_rules['enum_values']:
                raise ValueError(f"参数 '{param['name']}' 的值 {param_value} 不在枚举列表 {validation_rules['enum_values']} 中")
        
        # 6. 依赖验证
        if 'depends_on' in validation_rules:
            depends_on = validation_rules['depends_on']
            # 注意：依赖验证需要上下文信息，这里简化处理
            # 实际实现可能需要传递所有参数或参数上下文
        
        return True
    
    @staticmethod
    def validate_parameters(params: List[Dict[str, Any]]) -> bool:
        """
        验证参数列表是否符合定义的验证规则
        
        Args:
            params: 参数列表
            
        Returns:
            True如果所有参数验证通过，否则False
            
        Raises:
            ValueError: 当任何参数验证失败时
        """
        for param in params:
            ParameterManager.validate_parameter(param)
        return True
    
    @staticmethod
    def get_model_parameters_with_templates(db: Session, model_id: int) -> List[Dict[str, Any]]:
        """
        获取模型参数，包括参数模板的继承

        Args:
            db: 数据库会话
            model_id: 模型ID

        Returns:
            合并后的参数列表，与ModelParameterResponse兼容
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            return []

        # 获取应用于该模型的参数模板
        model_template = db.query(ParameterTemplate).filter(
            ParameterTemplate.level == "model",
            ParameterTemplate.level_id == model_id
        ).first()

        if model_template:
            # 如果有模型级别的参数模板，使用该模板的合并参数
            merged_params = ParameterManager.get_merged_parameters(db, model_template.id)
            
            # 将模板参数转换为与ModelParameterResponse兼容的格式
            compatible_params = []
            from datetime import datetime
            temp_id_counter = -1  # 为模板参数生成临时负ID
            
            for param in merged_params:
                # 确保参数包含所有必要字段
                compatible_param = {
                    "id": temp_id_counter,
                    "model_id": model_id,
                    "parameter_name": param.get("name", ""),
                    "parameter_value": str(param.get("value", "")),
                    "parameter_type": param.get("type", "string"),
                    "description": param.get("description", ""),
                    "parameter_source": param.get("source", "model"),
                    "is_override": param.get("is_override", False),
                    "is_default": param.get("is_default", False),
                    "inherited": param.get("inherited", False),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                compatible_params.append(compatible_param)
                temp_id_counter -= 1
                
            merged_params = compatible_params
        else:
            # 否则，使用传统的模型参数获取方式
            merged_params = ParameterManager.get_model_parameters(db, model_id)

        return merged_params
    
    @staticmethod
    def apply_parameter_template_to_model(db: Session, model_id: int, template_id: int) -> ModelDB:
        """
        将参数模板应用到模型，并将模板参数同步到ModelParameter表
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            template_id: 参数模板ID
            
        Returns:
            更新后的模型对象
            
        Raises:
            ValueError: 当模板不存在或模型不存在时
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 获取参数模板
        template = ParameterManager.get_template(db, template_id)
        if not template:
            raise ValueError(f"参数模板ID {template_id} 不存在")
        
        # 关联模板到模型
        model.parameter_template_id = template_id
        
        # 获取合并后的参数
        merged_params = ParameterManager.get_merged_parameters(db, template_id)
        
        # 同步参数到ModelParameter表
        ParameterManager._sync_template_params_to_model_params(db, model_id, merged_params)
        
        db.commit()
        db.refresh(model)
        return model
    
    @staticmethod
    def _sync_template_params_to_model_params(db: Session, model_id: int, template_params: List[Dict[str, Any]]):
        """
        将模板参数同步到ModelParameter表
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            template_params: 参数模板中的参数列表
        """
        # 获取模型当前的参数
        current_params = db.query(ModelParameter).filter(ModelParameter.model_id == model_id).all()
        current_params_dict = {param.parameter_name: param for param in current_params}
        
        # 需要保留的参数名称集合
        template_param_names = set()
        
        for template_param in template_params:
            param_name = template_param['name']
            template_param_names.add(param_name)
            
            # 转换模板参数到ModelParameter格式
            param_data = ModelParameterCreate(
                parameter_name=param_name,
                parameter_type=template_param.get('type', 'string'),
                parameter_value=str(template_param.get('default_value', '')),
                description=template_param.get('description', ''),
                is_default=True,
                parameter_source='template',
                is_override=template_param.get('is_override', False)
            )
            
            # 创建或更新参数
            ParameterManager.create_or_update_model_parameter(db, model_id, param_data)
        
        # 删除模板中不存在的参数（仅删除模板来源的参数）
        for param_name, param in current_params_dict.items():
            if param_name not in template_param_names and param.parameter_source == 'template':
                db.delete(param)
    
    @staticmethod
    def convert_template_to_model_params(template_params: List[Dict[str, Any]]) -> List[ModelParameterCreate]:
        """
        将参数模板格式转换为ModelParameter创建格式
        
        Args:
            template_params: 参数模板中的参数列表
            
        Returns:
            ModelParameterCreate对象列表
        """
        model_params = []
        for template_param in template_params:
            model_param = ModelParameterCreate(
                parameter_name=template_param['name'],
                parameter_type=template_param.get('type', 'string'),
                parameter_value=str(template_param.get('default_value', '')),
                description=template_param.get('description', ''),
                is_default=True,
                parameter_source='template',
                is_override=template_param.get('is_override', False)
            )
            model_params.append(model_param)
        return model_params
    
    @staticmethod
    def normalize_parameters(db: Session, model_id: int, raw_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        对模型参数进行归一化处理
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            raw_params: 原始参数
            
        Returns:
            归一化后的参数
        """
        return ParameterNormalizer.normalize_model_parameters(db, model_id, raw_params)
    
    @staticmethod
    def denormalize_parameters(db: Session, model_id: int, normalized_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        将归一化参数转换为供应商特定格式
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            normalized_params: 归一化参数
            
        Returns:
            供应商特定格式参数
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 获取模型类型
        model_type = model.model_type.name if model.model_type else None
        
        # 进行参数反归一化
        return ParameterNormalizer.denormalize_parameters(
            supplier_id=model.supplier_id,
            standard_params=normalized_params,
            model_type=model_type
        )
    
    @staticmethod
    def convert_supplier_params_to_standard(db: Session, supplier_id: int, model_type: str, supplier_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        将供应商特定参数转换为标准参数
        
        Args:
            db: 数据库会话
            supplier_id: 供应商ID
            model_type: 模型类型
            supplier_params: 供应商特定参数
            
        Returns:
            标准格式参数
        """
        return ParameterNormalizer.normalize_parameters(
            supplier_id=supplier_id,
            raw_params=supplier_params,
            model_type=model_type
        )
    
    @staticmethod
    def convert_standard_params_to_supplier(db: Session, supplier_id: int, model_type: str, standard_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        将标准参数转换为供应商特定参数
        
        Args:
            db: 数据库会话
            supplier_id: 供应商ID
            model_type: 模型类型
            standard_params: 标准参数
            
        Returns:
            供应商特定格式参数
        """
        return ParameterNormalizer.denormalize_parameters(
            supplier_id=supplier_id,
            standard_params=standard_params,
            model_type=model_type
        )
    
    @staticmethod
    def auto_convert_parameters(db: Session, source_params: Dict[str, Any], conversion_type: str, **kwargs) -> Dict[str, Any]:
        """
        自动转换参数格式
        
        Args:
            db: 数据库会话
            source_params: 源参数
            conversion_type: 转换类型
                - supplier_to_standard: 供应商参数到标准参数
                - standard_to_supplier: 标准参数到供应商参数
                - model_specific: 模型特定参数转换
            **kwargs: 转换选项
                - supplier_id: 供应商ID
                - model_type: 模型类型
                - model_id: 模型ID
            
        Returns:
            转换后的参数
        
        Raises:
            ValueError: 当转换类型不支持或缺少必要参数时
        """
        if conversion_type == "supplier_to_standard":
            # 供应商参数到标准参数
            if "supplier_id" not in kwargs:
                raise ValueError("供应商ID是必需的")
            return ParameterManager.convert_supplier_params_to_standard(
                db=db,
                supplier_id=kwargs["supplier_id"],
                model_type=kwargs.get("model_type"),
                supplier_params=source_params
            )
        elif conversion_type == "standard_to_supplier":
            # 标准参数到供应商参数
            if "supplier_id" not in kwargs:
                raise ValueError("供应商ID是必需的")
            return ParameterManager.convert_standard_params_to_supplier(
                db=db,
                supplier_id=kwargs["supplier_id"],
                model_type=kwargs.get("model_type"),
                standard_params=source_params
            )
        elif conversion_type == "model_specific":
            # 模型特定参数转换
            if "model_id" not in kwargs:
                raise ValueError("模型ID是必需的")
            return ParameterManager.normalize_parameters(
                db=db,
                model_id=kwargs["model_id"],
                raw_params=source_params
            )
        else:
            raise ValueError(f"不支持的转换类型: {conversion_type}")
    
    @staticmethod
    def sync_model_parameters_with_template(db: Session, model_id: int, template_id: Optional[int] = None) -> ModelDB:
        """
        自动同步模型参数与参数模板，实现参数的自动转换和同步
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            template_id: 参数模板ID（可选），如果未提供则使用模型关联的模板
            
        Returns:
            更新后的模型对象
            
        Raises:
            ValueError: 当模型不存在或模板不存在时
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 获取模板ID
        if not template_id:
            template_id = model.parameter_template_id
            if not template_id:
                raise ValueError(f"模型ID {model_id} 没有关联的参数模板")
        
        # 获取参数模板
        template = ParameterManager.get_template(db, template_id)
        if not template:
            raise ValueError(f"参数模板ID {template_id} 不存在")
        
        # 对模板应用归一化规则
        template = ParameterNormalizer.apply_normalization_to_template(db, template_id)
        
        # 获取合并后的参数
        merged_params = ParameterManager.get_merged_parameters(db, template_id)
        
        # 将模板参数同步到ModelParameter表
        ParameterManager._sync_template_params_to_model_params(db, model_id, merged_params)
        
        db.commit()
        db.refresh(model)
        
        return model
    
    @staticmethod
    def apply_normalization_to_template(db: Session, template_id: int) -> ParameterTemplate:
        """
        对参数模板应用归一化规则
        
        Args:
            db: 数据库会话
            template_id: 参数模板ID
            
        Returns:
            更新后的参数模板
        """
        return ParameterNormalizer.apply_normalization_to_template(db, template_id)