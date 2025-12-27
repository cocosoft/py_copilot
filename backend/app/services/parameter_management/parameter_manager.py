"""模型参数管理服务"""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.model_category import ModelCategory
from app.models.supplier_db import ModelDB, ModelParameter, ParameterVersion
from app.models.parameter_template import ParameterTemplate
from app.schemas.model_category import ModelCategoryUpdate
from app.schemas.model_management import ModelParameterCreate, ModelParameterUpdate
from app.services.parameter_management.parameter_normalizer import ParameterNormalizer
from app.services.parameter_management.system_parameter_manager import SystemParameterManager


class ParameterManager:
    """参数管理器，负责模型参数的继承、覆盖和合并逻辑"""
    
    @staticmethod
    def get_model_parameters(db: Session, model_id: int, dimension: str = None) -> List[Dict[str, Any]]:
        """
        获取模型的完整参数配置，支持维度隔离的参数继承
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            dimension: 维度标识，如果提供则只返回该维度下的参数
            
        Returns:
            合并后的完整参数配置列表，每个参数包含inherited字段和dimension字段
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            return []
        
        # 基础参数列表
        parameters_list = []
        
        # 1. 获取模型在指定维度下的分类关联
        model_categories = []
        if dimension:
            # 获取模型在指定维度下的所有分类
            from app.models.model_category import ModelCategoryAssociation
            associations = db.query(ModelCategoryAssociation).filter(
                ModelCategoryAssociation.model_id == model_id
            ).all()
            
            for association in associations:
                category = db.query(ModelCategory).filter(
                    ModelCategory.id == association.category_id,
                    ModelCategory.dimension == dimension
                ).first()
                if category:
                    model_categories.append(category)
        else:
            # 如果没有指定维度，获取所有分类
            from app.models.model_category import ModelCategoryAssociation
            associations = db.query(ModelCategoryAssociation).filter(
                ModelCategoryAssociation.model_id == model_id
            ).all()
            
            for association in associations:
                category = db.query(ModelCategory).filter(
                    ModelCategory.id == association.category_id
                ).first()
                if category:
                    model_categories.append(category)
        
        # 2. 获取分类的默认参数（维度隔离）
        default_params_dict = {}
        for category in model_categories:
            if category and category.default_parameters:
                # 处理默认参数（兼容不同的数据库JSON字段处理方式）
                default_params = category.default_parameters
                if isinstance(default_params, str):
                    import json
                    default_params = json.loads(default_params)
                
                # 添加默认参数到列表中，标记为继承
                from datetime import datetime
                temp_id_counter = -1  # 为默认参数生成临时负ID
                
                # 兼容列表和字典两种格式
                if isinstance(default_params, list):
                    for param in default_params:
                        param_name = param.get("name")
                        param_value = param.get("default_value", param.get("value"))
                        parameters_list.append({
                            "id": temp_id_counter,
                            "parameter_name": param_name,
                            "parameter_value": str(param_value),
                            "parameter_type": param.get("type", "string"),
                            "default_value": param_value,
                            "description": param.get("description", ""),
                            "is_required": param.get("is_required", False),
                            "model_id": model_id,
                            "created_at": datetime.now(),
                            "updated_at": datetime.now(),
                            "inherited": True,
                            "parameter_source": "model_category",
                            "is_default": True,
                            "is_override": False,
                            "dimension": category.dimension,
                            "category_id": category.id,
                            "category_name": category.name
                        })
                        default_params_dict[param_name] = param_value
                        temp_id_counter -= 1
                elif isinstance(default_params, dict):
                    for param_name, param_value in default_params.items():
                        parameters_list.append({
                            "id": temp_id_counter,
                            "parameter_name": param_name,
                            "parameter_value": str(param_value),
                            "parameter_type": "string",
                            "default_value": param_value,
                            "description": "",
                            "is_required": False,
                            "model_id": model_id,
                            "created_at": datetime.now(),
                            "updated_at": datetime.now(),
                            "inherited": True,
                            "parameter_source": "model_category",
                            "is_default": True,
                            "is_override": False,
                            "dimension": category.dimension,
                            "category_id": category.id,
                            "category_name": category.name
                        })
                        default_params_dict[param_name] = param_value
                        temp_id_counter -= 1
        
        # 3. 获取模型自身的参数（覆盖分类默认参数）
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
                "is_override": param.is_override,
                "dimension": "model_specific"  # 模型特定参数不属于任何维度
            })
            
            model_param_names.add(param.parameter_name)
        
        # 4. 如果模型自身的参数覆盖了默认参数，将默认参数标记为非继承
        for param in parameters_list:
            if param["inherited"] and param["parameter_name"] in model_param_names:
                param["inherited"] = False
        
        # 5. 如果指定了维度，过滤只返回该维度下的参数
        if dimension:
            parameters_list = [param for param in parameters_list 
                             if param.get("dimension") == dimension or 
                                param.get("dimension") == "model_specific"]
        
        return parameters_list
    
    @staticmethod
    def update_model_category_default_parameters(
        db: Session, 
        category_id: int, 
        parameters: Dict[str, Any]
    ) -> Optional[ModelCategory]:
        """
        更新模型分类的默认参数，并级联更新所有关联模型的继承参数（维度隔离）
        
        Args:
            db: 数据库会话
            category_id: 模型分类ID
            parameters: 要更新的默认参数
            
        Returns:
            更新后的模型分类对象，或None
        """
        category = db.query(ModelCategory).filter(ModelCategory.id == category_id).first()
        if not category:
            return None
        
        # 处理默认参数（兼容不同的数据库JSON字段处理方式）
        if category.default_parameters is None:
            current_params = {}
        elif isinstance(category.default_parameters, str):
            current_params = json.loads(category.default_parameters)
        else:
            current_params = category.default_parameters.copy()
            
        current_params.update(parameters)
        category.default_parameters = current_params
        
        # 为模型分类创建或更新分类级参数记录
        for param_name, param_value in parameters.items():
            param_type = type(param_value).__name__
            
            # 检查分类级参数是否已存在
            category_param = db.query(ModelParameter).filter(
                ModelParameter.parameter_name == param_name,
                ModelParameter.parameter_source == "model_category"
            ).first()
            
            if category_param:
                # 更新现有分类级参数
                category_param.parameter_value = str(param_value)
                category_param.parameter_type = param_type
                category_param.description = f"Default {param_type} parameter for {category.name}"
                category_param.parameter_source = "model_category"
                category_param.is_default = True
            else:
                # 创建新的分类级参数
                category_param = ModelParameter(
                    parameter_name=param_name,
                    parameter_value=str(param_value),
                    parameter_type=param_type,
                    description=f"Default {param_type} parameter for {category.name}",
                    parameter_source="model_category",
                    is_default=True
                )
                db.add(category_param)
        
        # 级联更新所有关联模型的继承参数（维度隔离）
        # 获取所有关联该分类的模型
        from app.models.model_category import ModelCategoryAssociation
        associations = db.query(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.category_id == category_id
        ).all()
        
        for association in associations:
            model = db.query(ModelDB).filter(ModelDB.id == association.model_id).first()
            if not model:
                continue
                
            # 获取模型的所有参数
            model_params = db.query(ModelParameter).filter(
                ModelParameter.model_id == model.id
            ).all()
            
            # 创建参数名称集合以便快速查找
            existing_param_names = set(p.parameter_name for p in model_params)
            
            # 更新继承自模型分类的参数（仅更新未被覆盖的参数）
            for param_name, param_value in parameters.items():
                param_type = type(param_value).__name__
                
                # 查找分类级参数作为父参数
                parent_param = db.query(ModelParameter).filter(
                    ModelParameter.parameter_name == param_name,
                    ModelParameter.parameter_source == "model_category"
                ).first()
                
                # 查找该模型中对应的继承参数
                inherited_param = next((p for p in model_params 
                                     if p.parameter_name == param_name and 
                                     p.parameter_source == "model_category" and 
                                     not p.is_override), None)
                
                if inherited_param:
                    # 更新现有继承参数
                    inherited_param.parameter_value = str(param_value)
                    inherited_param.parameter_type = param_type
                    db.add(inherited_param)
                elif param_name not in existing_param_names:
                    # 如果该参数不存在且不是自定义参数，则创建新的继承参数
                    new_param = ModelParameter(
                        model_id=model.id,
                        parameter_name=param_name,
                        parameter_value=str(param_value),
                        parameter_type=param_type,
                        parameter_source="model_category",
                        is_override=False
                    )
                    db.add(new_param)
        
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def cascade_update_parameters(
        db: Session,
        source_type: str,  # 'model_category' 或 'model'
        source_id: int,    # 来源ID
        parameter_updates: Dict[str, Any],
        dimension: str = None  # 新增维度参数
    ) -> List[ModelParameter]:
        """
        级联更新参数，支持维度隔离的参数继承链
        
        Args:
            db: 数据库会话
            source_type: 来源类型 ('model_category' 或 'model')
            source_id: 来源ID
            parameter_updates: 参数更新字典 {参数名: 新值}
            dimension: 维度标识，用于维度隔离
            
        Returns:
            更新的参数列表
        """
        updated_params = []
        
        if source_type == 'model_category':
            # 分类级参数更新，级联更新所有关联该分类的模型
            category = db.query(ModelCategory).filter(ModelCategory.id == source_id).first()
            if not category:
                raise ValueError(f"模型分类ID {source_id} 不存在")
            
            # 更新模型分类的默认参数
            updated_category = ParameterManager.update_model_category_default_parameters(
                db, source_id, parameter_updates
            )
            
            if updated_category:
                # 获取所有受影响的参数
                for param_name in parameter_updates.keys():
                    param = db.query(ModelParameter).filter(
                        ModelParameter.parameter_name == param_name,
                        ModelParameter.parameter_source == "model_category"
                    ).first()
                    if param:
                        updated_params.append(param)
            
        elif source_type == 'model':
            # 模型级参数更新，支持更新单个参数或多个参数
            model = db.query(ModelDB).filter(ModelDB.id == source_id).first()
            if not model:
                raise ValueError(f"模型ID {source_id} 不存在")
            
            # 更新模型的每个参数
            for param_name, param_value in parameter_updates.items():
                # 确定参数类型
                param_type = type(param_value).__name__
                
                # 查找现有参数
                existing_param = db.query(ModelParameter).filter(
                    ModelParameter.model_id == source_id,
                    ModelParameter.parameter_name == param_name
                ).first()
                
                if existing_param:
                    # 更新现有参数
                    from app.schemas.model_management import ModelParameterUpdate
                    
                    update_data = ModelParameterUpdate(
                        parameter_value=str(param_value),
                        parameter_type=param_type,
                        description=existing_param.description,
                        is_default=existing_param.is_default,
                        parameter_source=existing_param.parameter_source,
                        is_override=existing_param.is_override
                    )
                    
                    # 更新参数
                    for key, value in update_data.model_dump(exclude_unset=True).items():
                        setattr(existing_param, key, value)
                    
                    db.add(existing_param)
                    updated_params.append(existing_param)
                else:
                    # 创建新参数
                    from app.schemas.model_management import ModelParameterCreate
                    
                    create_data = ModelParameterCreate(
                        parameter_name=param_name,
                        parameter_value=str(param_value),
                        parameter_type=param_type,
                        description=f"Parameter for model {model.name}",
                        is_default=False,
                        parameter_source="model",
                        is_override=False
                    )
                    
                    new_param = ParameterManager.create_or_update_model_parameter(
                        db, source_id, create_data
                    )
                    updated_params.append(new_param)
            
            db.commit()
        
        return updated_params
    
    @staticmethod
    def get_parameters_by_dimension(db: Session, model_id: int, dimension: str) -> List[Dict[str, Any]]:
        """
        获取指定模型在特定维度下的参数配置
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            dimension: 维度标识
            
        Returns:
            该维度下的参数配置列表
        """
        return ParameterManager.get_model_parameters(db, model_id, dimension)
    
    @staticmethod
    def get_all_dimension_parameters(db: Session, model_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取模型在所有维度下的参数配置
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            按维度分组的参数配置字典
        """
        # 获取模型的所有维度
        from app.models.model_category import ModelCategoryAssociation
        associations = db.query(ModelCategoryAssociation).filter(
            ModelCategoryAssociation.model_id == model_id
        ).all()
        
        dimensions = set()
        for association in associations:
            category = db.query(ModelCategory).filter(ModelCategory.id == association.category_id).first()
            if category and category.dimension:
                dimensions.add(category.dimension)
        
        # 获取每个维度下的参数
        result = {}
        for dimension in dimensions:
            result[dimension] = ParameterManager.get_model_parameters(db, model_id, dimension)
        
        # 添加模型特定参数（不属于任何维度）
        model_specific_params = [param for param in ParameterManager.get_model_parameters(db, model_id) 
                               if param.get("dimension") == "model_specific"]
        if model_specific_params:
            result["model_specific"] = model_specific_params
        
        return result
    
    @staticmethod
    def update_parameter_inheritance_chain(
        db: Session,
        parameter_id: int,
        new_value: str,
        new_type: Optional[str] = None
    ) -> ModelParameter:
        """
        更新参数继承链，确保所有子参数都能正确继承新值（如果它们没有被覆盖）
        
        Args:
            db: 数据库会话
            parameter_id: 参数ID
            new_value: 新参数值
            new_type: 新参数类型（可选）
            
        Returns:
            更新后的参数对象
        """
        # 获取当前参数
        param = db.query(ModelParameter).filter(ModelParameter.id == parameter_id).first()
        if not param:
            raise ValueError(f"参数ID {parameter_id} 不存在")
        
        # 更新当前参数
        param.parameter_value = new_value
        if new_type:
            param.parameter_type = new_type
        
        db.add(param)
        
        # 查找所有继承此参数的子参数
        # 注意：由于parent_parameter_id列不存在，暂时无法实现继承链更新
        # child_params = db.query(ModelParameter).filter(
        #     ModelParameter.parent_parameter_id == parameter_id,
        #     not ModelParameter.is_override  # 只更新未被覆盖的子参数
        # ).all()
        # 
        # 更新所有子参数
        # for child_param in child_params:
        #     child_param.parameter_value = new_value
        #     if new_type:
        #         child_param.parameter_type = new_type
        #     db.add(child_param)
        
        db.commit()
        db.refresh(param)
        return param
    
    @staticmethod
    def _create_parameter_version(db: Session, parameter: ModelParameter, updated_by: Optional[str] = None) -> ParameterVersion:
        """
        创建参数版本记录
        
        Args:
            db: 数据库会话
            parameter: 要创建版本的参数对象
            updated_by: 更新人，可选
            
        Returns:
            创建的版本记录对象
        """
        # 获取当前参数的最大版本号
        max_version = db.query(ParameterVersion.version_number).filter(
            ParameterVersion.parameter_id == parameter.id
        ).order_by(ParameterVersion.version_number.desc()).first()
        
        version_number = 1 if max_version is None else max_version[0] + 1
        
        # 创建新版本记录
        version = ParameterVersion(
            parameter_id=parameter.id,
            version_number=version_number,
            parameter_value=parameter.parameter_value,
            updated_by=updated_by
        )
        
        db.add(version)
        return version
    
    @staticmethod
    def get_parameter_versions(db: Session, parameter_id: int) -> List[ParameterVersion]:
        """
        获取参数的所有版本历史
        
        Args:
            db: 数据库会话
            parameter_id: 参数ID
            
        Returns:
            参数版本历史列表，按版本号降序排列
        """
        return db.query(ParameterVersion).filter(
            ParameterVersion.parameter_id == parameter_id
        ).order_by(ParameterVersion.version_number.desc()).all()
    
    @staticmethod
    def revert_parameter_to_version(db: Session, parameter_id: int, version_number: int, updated_by: Optional[str] = None) -> ModelParameter:
        """
        将参数回滚到指定版本
        
        Args:
            db: 数据库会话
            parameter_id: 参数ID
            version_number: 要回滚到的版本号
            updated_by: 更新人，可选
            
        Returns:
            更新后的参数对象
            
        Raises:
            ValueError: 当参数或版本不存在时
        """
        # 检查参数是否存在
        parameter = db.query(ModelParameter).filter(ModelParameter.id == parameter_id).first()
        if not parameter:
            raise ValueError(f"参数ID {parameter_id} 不存在")
        
        # 检查版本是否存在
        version = db.query(ParameterVersion).filter(
            ParameterVersion.parameter_id == parameter_id,
            ParameterVersion.version_number == version_number
        ).first()
        if not version:
            raise ValueError(f"参数ID {parameter_id} 的版本号 {version_number} 不存在")
        
        # 先创建当前版本的快照
        ParameterManager._create_parameter_version(db, parameter, updated_by)
        
        # 回滚参数值
        parameter.parameter_value = version.parameter_value
        
        db.commit()
        db.refresh(parameter)
        return parameter
    
    @staticmethod
    def create_or_update_model_parameter(
        db: Session, 
        model_id: int, 
        param_data: ModelParameterCreate,
        updated_by: Optional[str] = None
    ) -> ModelParameter:
        """
        创建或更新模型参数
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            param_data: 参数数据
            updated_by: 更新人，可选
            
        Returns:
            创建或更新后的参数对象
            
        Raises:
            ValueError: 当参数值无法转换为指定类型时
        """
        # 验证参数值与类型是否匹配
        ParameterManager._convert_parameter_value(param_data.parameter_value, param_data.parameter_type)
        
        # 获取模型信息，确定参数层级和继承关系
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 确定参数层级
        # 注意：由于parameter_level, inherit_from, parent_parameter_id列不存在，暂时简化层级逻辑
        # parameter_level = 1  # 默认层级为1（模型级）
        # inherit_from = None
        # parent_parameter_id = None
        
        # 如果参数来自模型类型，设置继承关系
        # if param_data.parameter_source == "model_type" and model.model_type_id:
        #     parameter_level = 0  # 类型级参数层级为0
        #     inherit_from = f"model_type:{model.model_type_id}"
        #     
        #     # 查找父参数
        #     parent_param = db.query(ModelParameter).filter(
        #         ModelParameter.parameter_name == param_data.parameter_name,
        #         ModelParameter.parameter_source == "model_type",
        #         ModelParameter.inherit_from == f"model_type:{model.model_type_id}"
        #     ).first()
        #     if parent_param:
        #         parent_parameter_id = parent_param.id
        
        # 检查参数是否已存在
        existing_param = db.query(ModelParameter).filter(
            ModelParameter.model_id == model_id,
            ModelParameter.parameter_name == param_data.parameter_name
        ).first()
        
        if existing_param:
            # 在更新前创建版本记录
            ParameterManager._create_parameter_version(db, existing_param, updated_by)
            
            # 更新现有参数
            existing_param.parameter_type = param_data.parameter_type
            existing_param.parameter_value = param_data.parameter_value
            existing_param.description = param_data.description
            existing_param.is_default = param_data.is_default
            existing_param.parameter_source = param_data.parameter_source
            existing_param.is_override = param_data.is_override
            # 注意：由于parameter_level, inherit_from, parent_parameter_id, is_inherited列不存在，暂时跳过这些字段
            # existing_param.parameter_level = parameter_level
            # existing_param.inherit_from = inherit_from
            # existing_param.parent_parameter_id = parent_parameter_id
            # existing_param.is_inherited = param_data.parameter_source == "model_type"
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
                # 注意：由于parameter_level, inherit_from, parent_parameter_id, is_inherited列不存在，暂时跳过这些字段
                # parameter_level=parameter_level,
                # inherit_from=inherit_from,
                # parent_parameter_id=parent_parameter_id,
                # is_inherited=param_data.parameter_source == "model_type"
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
    def inherit_model_type_parameters(
        db: Session,
        model_id: int,
        model_type_id: int,
        updated_by: Optional[str] = None
    ) -> List[ModelParameter]:
        """
        当模型类型变更时，自动从新类型继承默认参数
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            model_type_id: 新的模型类型ID
            updated_by: 更新人，可选
            
        Returns:
            继承的参数列表
        """
        # 获取模型和模型类型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        model_type = db.query(ModelCategory).filter(ModelCategory.id == model_type_id).first()
        if not model_type:
            raise ValueError(f"模型类型ID {model_type_id} 不存在")
        
        # 更新模型的类型ID
        model.model_type_id = model_type_id
        
        # 获取模型类型的所有默认参数
        type_params = db.query(ModelParameter).filter(
            ModelParameter.parameter_source == "model_type"
            # 注意：由于inherit_from列不存在，暂时简化查询条件
            # ModelParameter.inherit_from == f"model_type:{model_type_id}"
        ).all()
        
        # 获取模型现有的参数
        existing_model_params = db.query(ModelParameter).filter(
            ModelParameter.model_id == model_id
        ).all()
        existing_param_names = {p.parameter_name for p in existing_model_params}
        
        # 继承的参数列表
        inherited_params = []
        
        # 从模型类型继承参数
        for type_param in type_params:
            # 如果模型已经有同名参数，则跳过（不覆盖）
            if type_param.parameter_name in existing_param_names:
                continue
            
            # 创建新的继承参数
            inherited_param = ModelParameter(
                model_id=model_id,
                parameter_name=type_param.parameter_name,
                parameter_value=type_param.parameter_value,
                parameter_type=type_param.parameter_type,
                description=type_param.description,
                parameter_source="model_type",
                is_default=type_param.is_default,
                is_override=False
                # 注意：由于parent_parameter_id, parameter_level, inherit_from, is_inherited列不存在，暂时跳过这些字段
                # parent_parameter_id=type_param.id,
                # parameter_level=1,
                # inherit_from=f"model_type:{model_type_id}",
                # is_inherited=True
            )
            db.add(inherited_param)
            inherited_params.append(inherited_param)
        
        db.commit()
        return inherited_params
    
    @staticmethod
    def get_parameter_inheritance_chain(
        db: Session,
        parameter_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取参数的完整继承链
        
        Args:
            db: 数据库会话
            parameter_id: 参数ID
            
        Returns:
            参数继承链列表，包含所有父参数信息
        """
        inheritance_chain = []
        current_param = db.query(ModelParameter).filter(ModelParameter.id == parameter_id).first()
        
        while current_param:
            # 添加参数信息到继承链
            param_info = {
                "id": current_param.id,
                "parameter_name": current_param.parameter_name,
                "parameter_value": current_param.parameter_value,
                "parameter_type": current_param.parameter_type,
                "description": current_param.description,
                "parameter_source": current_param.parameter_source,
                "is_override": current_param.is_override,
                "model_id": current_param.model_id,
                "created_at": current_param.created_at,
                "updated_at": current_param.updated_at
                # 注意：由于parameter_level, is_inherited, inherit_from, model_type_id列不存在，暂时跳过这些字段
                # "parameter_level": current_param.parameter_level,
                # "is_inherited": current_param.is_inherited,
                # "inherit_from": current_param.inherit_from,
                # "model_type_id": current_param.model_type_id,
            }
            inheritance_chain.append(param_info)
            
            # 查找父参数
            # 注意：由于parent_parameter_id列不存在，暂时无法实现继承链查找
            # if current_param.parent_parameter_id:
            #     current_param = db.query(ModelParameter).filter(
            #         ModelParameter.id == current_param.parent_parameter_id
            #     ).first()
            # else:
            #     current_param = None
            current_param = None
        
        return inheritance_chain
    
    @staticmethod
    def sync_model_type_parameters(
        db: Session,
        model_type_id: int
    ) -> List[ModelDB]:
        """
        同步模型类型的参数到所有关联模型
        
        Args:
            db: 数据库会话
            model_type_id: 模型类型ID
            
        Returns:
            受影响的模型列表
        """
        # 获取所有使用该模型类型的模型
        models = db.query(ModelDB).filter(ModelDB.model_type_id == model_type_id).all()
        
        for model in models:
            # 重新继承模型类型参数
            ParameterManager.inherit_model_type_parameters(db, model.id, model_type_id)
        
        return models
    
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
    def validate_parameter(param: Dict[str, Any], param_value: Any = None, all_params: Optional[Dict[str, Any]] = None) -> bool:
        """
        验证单个参数是否符合定义的验证规则
        
        Args:
            param: 参数定义（包含类型、验证规则等）
            param_value: 要验证的参数值，如果为None则使用param['default_value']
            all_params: 所有参数的字典，用于依赖验证
            
        Returns:
            True如果验证通过，否则False
            
        Raises:
            ValueError: 当参数验证失败时
        """
        param_name = param.get('name', 'unknown')
        
        # 如果没有提供值，使用默认值
        if param_value is None:
            if 'default_value' not in param and param.get('required', False):
                raise ValueError(f"参数 '{param_name}' 是必填的，但没有提供值")
            param_value = param.get('default_value')
            
        # 1. 必填验证
        if param.get('required', False) and param_value is None:
            raise ValueError(f"参数 '{param_name}' 是必填的")
            
        # 如果值为None且不是必填，则不需要进一步验证
        if param_value is None:
            return True
            
        # 2. 类型验证
        param_type = param.get('type', 'string')
        try:
            converted_value = ParameterManager._convert_parameter_value(str(param_value), param_type)
        except ValueError as e:
            raise ValueError(f"参数 '{param_name}' 类型验证失败: {str(e)}")
            
        # 获取验证规则
        validation_rules = param.get('validation_rules', {})
        
        # 3. 范围验证（针对数值类型）
        if param_type in ['int', 'float']:
            if 'min' in validation_rules and converted_value < validation_rules['min']:
                raise ValueError(f"参数 '{param_name}' 的值 {converted_value} 小于最小值 {validation_rules['min']}")
                
            if 'max' in validation_rules and converted_value > validation_rules['max']:
                raise ValueError(f"参数 '{param_name}' 的值 {converted_value} 大于最大值 {validation_rules['max']}")
                
            if 'step' in validation_rules:
                step = validation_rules['step']
                if param_type == 'int' and (converted_value % step) != 0:
                    raise ValueError(f"参数 '{param_name}' 的值 {converted_value} 必须是 {step} 的整数倍")
                elif param_type == 'float' and abs(converted_value % step) > 1e-9:  # 处理浮点数精度问题
                    raise ValueError(f"参数 '{param_name}' 的值 {converted_value} 必须是 {step} 的倍数")
        
        # 4. 字符串验证
        if param_type == 'string':
            if 'min_length' in validation_rules and len(param_value) < validation_rules['min_length']:
                raise ValueError(f"参数 '{param_name}' 的长度 {len(param_value)} 小于最小长度 {validation_rules['min_length']}")
                
            if 'max_length' in validation_rules and len(param_value) > validation_rules['max_length']:
                raise ValueError(f"参数 '{param_name}' 的长度 {len(param_value)} 大于最大长度 {validation_rules['max_length']}")
                
            if 'regex' in validation_rules:
                import re
                if not re.match(validation_rules['regex'], param_value):
                    raise ValueError(f"参数 '{param_name}' 的值 '{param_value}' 不符合格式要求")
                
            if 'contains' in validation_rules and validation_rules['contains'] not in param_value:
                raise ValueError(f"参数 '{param_name}' 的值必须包含 '{validation_rules['contains']}'")
                
            if 'starts_with' in validation_rules and not param_value.startswith(validation_rules['starts_with']):
                raise ValueError(f"参数 '{param_name}' 的值必须以 '{validation_rules['starts_with']}' 开头")
                
            if 'ends_with' in validation_rules and not param_value.endswith(validation_rules['ends_with']):
                raise ValueError(f"参数 '{param_name}' 的值必须以 '{validation_rules['ends_with']}' 结尾")
        
        # 5. 枚举验证
        if param_type == 'enum' and 'enum_values' in validation_rules:
            if param_value not in validation_rules['enum_values']:
                raise ValueError(f"参数 '{param_name}' 的值 '{param_value}' 不在枚举列表 {validation_rules['enum_values']} 中")
        
        # 6. 数组验证
        if param_type in ['array', 'list']:
            if 'min_items' in validation_rules and len(converted_value) < validation_rules['min_items']:
                raise ValueError(f"参数 '{param_name}' 的数组长度 {len(converted_value)} 小于最小长度 {validation_rules['min_items']}")
                
            if 'max_items' in validation_rules and len(converted_value) > validation_rules['max_items']:
                raise ValueError(f"参数 '{param_name}' 的数组长度 {len(converted_value)} 大于最大长度 {validation_rules['max_items']}")
                
            if 'unique_items' in validation_rules and validation_rules['unique_items']:
                if len(converted_value) != len(set(converted_value)):
                    raise ValueError(f"参数 '{param_name}' 的数组必须包含唯一元素")
        
        # 7. 对象验证
        if param_type == 'object':
            if 'required_properties' in validation_rules:
                for prop in validation_rules['required_properties']:
                    if prop not in converted_value:
                        raise ValueError(f"参数 '{param_name}' 的对象必须包含属性 '{prop}'")
        
        # 8. 依赖验证
        if 'depends_on' in validation_rules:
            if all_params is None:
                raise ValueError(f"参数 '{param_name}' 的依赖验证需要提供所有参数信息")
                
            depends_on = validation_rules['depends_on']
            if isinstance(depends_on, str):
                # 简单依赖：依赖的参数必须存在且有值
                if depends_on not in all_params or all_params[depends_on] is None:
                    raise ValueError(f"参数 '{param_name}' 依赖于参数 '{depends_on}'，但该参数不存在或为空")
            elif isinstance(depends_on, dict):
                # 条件依赖：依赖的参数必须满足特定条件
                for dep_param, dep_value in depends_on.items():
                    if dep_param not in all_params:
                        raise ValueError(f"参数 '{param_name}' 依赖于参数 '{dep_param}'，但该参数不存在")
                    if all_params[dep_param] != dep_value:
                        raise ValueError(f"参数 '{param_name}' 仅当参数 '{dep_param}' 为 '{dep_value}' 时可用")
        
        return True
    
    @staticmethod
    def inherit_parameters(db: Session, model_id: int) -> List[ModelParameter]:
        """
        从模型类型继承默认参数到指定模型
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            继承的参数列表
            
        Raises:
            ValueError: 当模型不存在时
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 获取模型类型
        if not model.model_type_id:
            return []  # 没有模型类型，无法继承参数
            
        model_type = db.query(ModelCategory).filter(ModelCategory.id == model.model_type_id).first()
        if not model_type:
            return []  # 模型类型不存在，无法继承参数
        
        # 获取模型类型的默认参数
        default_params = model_type.default_parameters or {}
        if isinstance(default_params, str):
            default_params = json.loads(default_params)
        
        # 获取模型已有的参数
        existing_params = db.query(ModelParameter).filter(
            ModelParameter.model_id == model_id
        ).all()
        existing_param_names = set(param.parameter_name for param in existing_params)
        
        inherited_params = []
        
        # 为每个默认参数创建模型参数记录
        for param_name, param_value in default_params.items():
            # 跳过模型已经存在的参数（避免覆盖）
            if param_name in existing_param_names:
                continue
                
            param_type = type(param_value).__name__
            param = ModelParameter(
                model_id=model_id,
                parameter_name=param_name,
                parameter_value=json.dumps(param_value),
                parameter_type=param_type,
                parameter_source="model_type",
                is_override=False
            )
            db.add(param)
            inherited_params.append(param)
        
        db.commit()
        return inherited_params
    
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
        # 创建参数字典，用于依赖验证
        params_dict = {}
        for param in params:
            param_name = param.get('name')
            if param_name:
                params_dict[param_name] = param.get('default_value')
        
        # 验证所有参数
        for param in params:
            ParameterManager.validate_parameter(param, all_params=params_dict)
        
        return True
    
    @staticmethod
    def validate_parameters_with_values(
        params: List[Dict[str, Any]], 
        param_values: Dict[str, Any]
    ) -> bool:
        """
        使用提供的参数值验证参数列表
        
        Args:
            params: 参数列表
            param_values: 参数值字典，键为参数名，值为参数值
            
        Returns:
            True如果所有参数验证通过，否则False
            
        Raises:
            ValueError: 当任何参数验证失败时
        """
        # 验证所有参数
        for param in params:
            param_name = param.get('name')
            if param_name in param_values:
                param_value = param_values[param_name]
                ParameterManager.validate_parameter(
                    param, 
                    param_value=param_value, 
                    all_params=param_values
                )
            else:
                # 使用参数定义中的默认值
                ParameterManager.validate_parameter(
                    param, 
                    all_params=param_values
                )
        
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
            # 确保参数有名称字段
            param_name = template_param.get('name')
            if not param_name:
                continue  # 跳过没有名称的参数
                
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
    def get_parameter_inheritance_tree(db: Session, model_id: int, parameter_name: str) -> Dict[str, Any]:
        """
        获取参数的完整继承树
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            parameter_name: 参数名称
            
        Returns:
            参数继承树结构，包含model_type, model, agent等层级
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            return {}  # 返回空结构
        
        # 获取模型类型信息
        model_type = model.model_type
        model_type_name = model_type.display_name if model_type else "未知类型"
        
        # 构建继承树结构
        inheritance_tree = {
            "level": "model_type",
            "name": model_type_name,
            "parameters": [],
            "children": [
                {
                    "level": "model",
                    "name": model.model_name,
                    "parameters": [],
                    "children": []
                }
            ]
        }
        
        # 获取模型类型级参数模板
        model_type_template = db.query(ParameterTemplate).filter(
            ParameterTemplate.level == "model_type",
            ParameterTemplate.level_id == model.model_type_id
        ).first()
        
        # 获取模型级参数模板
        model_template = db.query(ParameterTemplate).filter(
            ParameterTemplate.level == "model",
            ParameterTemplate.level_id == model_id
        ).first()
        
        # 获取模型自身的参数
        model_params = db.query(ModelParameter).filter(
            ModelParameter.model_id == model_id,
            ModelParameter.parameter_name == parameter_name
        ).first()
        
        # 查找各层级的参数值
        # 模型类型级参数
        model_type_param_value = None
        model_type_override = False
        
        if model_type_template and model_type_template.parameters:
            for param in model_type_template.parameters:
                if param.get("name") == parameter_name:
                    model_type_param_value = param.get("default_value")
                    model_type_override = True
                    inheritance_tree["parameters"].append({
                        "id": f"mt-{parameter_name}",
                        "parameter_name": parameter_name,
                        "parameter_value": str(model_type_param_value),
                        "parameter_type": param.get("type", "string"),
                        "inherited": False,
                        "override": False
                    })
                    break
        
        model_param_value = model_type_param_value
        model_override = False
        
        if model_template and model_template.parameters:
            for param in model_template.parameters:
                if param.get("name") == parameter_name:
                    model_param_value = param.get("default_value")
                    model_override = True
                    break
        
        if model_params:
            model_param_value = model_params.parameter_value
            model_override = True
        
        inheritance_tree["children"][0]["parameters"].append({
            "id": f"md-{parameter_name}",
            "parameter_name": parameter_name,
            "parameter_value": str(model_param_value),
            "parameter_type": model_params.parameter_type if model_params else "string",
            "inherited": model_type_param_value is not None,
            "override": model_override,
            "source": "model_type" if model_type_param_value is not None else None
        })
        
        return inheritance_tree
    
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
    
    @staticmethod
    def batch_update_model_parameters(
        db: Session, 
        model_id: int, 
        params_data: List[Dict[str, Any]],
        updated_by: Optional[str] = None
    ) -> List[ModelParameter]:
        """
        批量更新模型参数
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            params_data: 参数数据列表，每个元素包含parameter_name、parameter_value、parameter_type等字段
            updated_by: 更新人，可选
            
        Returns:
            更新后的参数对象列表
            
        Raises:
            ValueError: 当参数值无法转换为指定类型时
        """
        # 获取模型信息
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        updated_params = []
        
        for param_data in params_data:
            # 检查必要字段
            if 'parameter_name' not in param_data:
                raise ValueError("参数名称是必填的")
            
            if 'parameter_value' not in param_data:
                raise ValueError(f"参数 '{param_data['parameter_name']}' 的值是必填的")
            
            if 'parameter_type' not in param_data:
                raise ValueError(f"参数 '{param_data['parameter_name']}' 的类型是必填的")
            
            # 验证参数值与类型是否匹配
            ParameterManager._convert_parameter_value(
                param_data['parameter_value'], 
                param_data['parameter_type']
            )
            
            # 转换为ModelParameterCreate对象
            create_data = ModelParameterCreate(
                parameter_name=param_data['parameter_name'],
                parameter_value=param_data['parameter_value'],
                parameter_type=param_data['parameter_type'],
                description=param_data.get('description', ''),
                is_default=param_data.get('is_default', False),
                parameter_source=param_data.get('parameter_source', 'model'),
                is_override=param_data.get('is_override', False)
            )
            
            # 创建或更新参数
            param = ParameterManager.create_or_update_model_parameter(
                db, model_id, create_data, updated_by
            )
            updated_params.append(param)
        
        db.commit()
        return updated_params