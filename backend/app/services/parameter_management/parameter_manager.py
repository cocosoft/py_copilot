"""模型参数管理服务"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.model_category import ModelCategory
from app.models.supplier_db import ModelDB, ModelParameter
from app.schemas.model_category import ModelCategoryUpdate
from app.schemas.model_management import ModelParameterCreate, ModelParameterUpdate


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
                import json
                return json.loads(value)
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