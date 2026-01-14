"""参数模板管理服务，支持模板版本控制和管理"""
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.parameter_template import ParameterTemplate
from app.models.supplier_db import ModelDB
from app.schemas.parameter_template import (
    ParameterTemplateCreate, 
    ParameterTemplateUpdate, 
    ParameterTemplateVersion
)


class TemplateManager:
    """参数模板管理器，支持模板的创建、版本控制、继承和应用"""
    
    @staticmethod
    def create_template(
        db: Session, 
        template_data: ParameterTemplateCreate
    ) -> ParameterTemplate:
        """
        创建新的参数模板
        
        Args:
            db: 数据库会话
            template_data: 模板创建数据
            
        Returns:
            创建的模板对象
        """
        # 验证模板名称唯一性
        existing_template = db.query(ParameterTemplate).filter(
            and_(
                ParameterTemplate.name == template_data.name,
                ParameterTemplate.scene == template_data.scene
            )
        ).first()
        
        if existing_template:
            raise ValueError(f"在场景 {template_data.scene} 下已存在同名模板 '{template_data.name}'")
        
        # 验证能力维度关系
        is_valid, errors = TemplateManager.validate_capability_relations(
            db, 
            template_data.dimension_id, 
            template_data.subdimension_id, 
            template_data.capability_id
        )
        
        if not is_valid:
            raise ValueError(f"能力维度关系验证失败: {', '.join(errors)}")
        
        # 创建新模板
        template = ParameterTemplate(
            name=template_data.name,
            description=template_data.description,
            level=template_data.level,
            level_id=template_data.level_id,
            parameters=template_data.parameters,
            version=template_data.version,
            is_active=template_data.is_active,
            parent_id=template_data.parent_id,
            
            # 能力维度关联字段
            dimension_id=template_data.dimension_id,
            subdimension_id=template_data.subdimension_id,
            capability_id=template_data.capability_id
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def update_template(
        db: Session, 
        template_id: int, 
        template_data: ParameterTemplateUpdate
    ) -> ParameterTemplate:
        """
        更新参数模板，创建新版本
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            template_data: 模板更新数据
            
        Returns:
            更新后的模板对象
        """
        template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"模板ID {template_id} 不存在")
        
        # 获取当前模板的字段值作为默认值
        current_data = template.__dict__.copy()
        current_data.pop('_sa_instance_state')
        
        # 准备更新数据，使用当前值作为默认值
        update_data = template_data.model_dump(exclude_unset=True)
        
        # 获取更新后的能力维度字段值
        dimension_id = update_data.get('dimension_id', current_data.get('dimension_id'))
        subdimension_id = update_data.get('subdimension_id', current_data.get('subdimension_id'))
        capability_id = update_data.get('capability_id', current_data.get('capability_id'))
        
        # 验证能力维度关系
        is_valid, errors = TemplateManager.validate_capability_relations(
            db, dimension_id, subdimension_id, capability_id
        )
        
        if not is_valid:
            raise ValueError(f"能力维度关系验证失败: {', '.join(errors)}")
        
        # 创建新版本（保留历史版本）
        old_version = template.version
        
        # 更新模板信息
        for field, value in update_data.items():
            setattr(template, field, value)
        
        # 更新版本号（如果指定了版本号或更新了参数）
        if update_data.get('version'):
            template.version = update_data.get('version')
        elif 'parameters' in update_data:
            # 自动生成新版本号
            template.version = TemplateManager._generate_next_version(old_version)
        
        template.updated_at = datetime.now()
        
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def get_template_by_id(db: Session, template_id: int) -> Optional[ParameterTemplate]:
        """根据ID获取模板"""
        return db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    
    @staticmethod
    def get_templates_by_scene(
        db: Session, 
        scene: str, 
        scene_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[ParameterTemplate]:
        """
        根据场景获取模板列表
        
        Args:
            db: 数据库会话
            scene: 场景名称
            scene_id: 场景特定ID
            active_only: 是否只返回激活的模板
            
        Returns:
            模板列表
        """
        query = db.query(ParameterTemplate).filter(ParameterTemplate.scene == scene)
        
        if scene_id is not None:
            query = query.filter(ParameterTemplate.id == scene_id)
        
        if active_only:
            query = query.filter(ParameterTemplate.is_active == True)
        
        return query.order_by(ParameterTemplate.created_at.desc()).all()
    
    @staticmethod
    def get_template_versions(db: Session, template_id: int) -> List[ParameterTemplateVersion]:
        """
        获取模板的所有版本历史
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            
        Returns:
            版本历史列表
        """
        # 在实际实现中，这里应该查询版本历史表
        # 目前简化实现，返回当前模板信息
        template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
        if not template:
            return []
        
        return [ParameterTemplateVersion(
            version=template.version,
            parameters=template.parameters,
            created_at=template.created_at,
            updated_at=template.updated_at
        )]
    
    @staticmethod
    def apply_template_to_model(
        db: Session, 
        template_id: int, 
        model_id: int
    ) -> Dict[str, Any]:
        """
        将模板应用到模型
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            model_id: 模型ID
            
        Returns:
            应用结果信息
        """
        template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"模板ID {template_id} 不存在")
        
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 检查模板层级是否匹配
        if template.level != "model":
            raise ValueError(f"模板层级 {template.level} 不适用于模型应用")
        
        # 应用模板参数到模型
        applied_params = []
        for param in template.parameters:
            # 这里应该调用参数管理器来实际应用参数
            # 简化实现，只记录应用信息
            applied_params.append({
                "name": param.get("name"),
                "value": param.get("default_value"),
                "type": param.get("type", "string")
            })
        
        # 更新模型的模板关联
        model.parameter_template_id = template_id
        db.commit()
        
        return {
            "template_id": template_id,
            "template_name": template.name,
            "model_id": model_id,
            "model_name": model.model_name,
            "applied_parameters": applied_params,
            "applied_count": len(applied_params)
        }
    
    @staticmethod
    def merge_templates(
        db: Session, 
        base_template_id: int, 
        override_template_id: int
    ) -> Dict[str, Any]:
        """
        合并两个模板，基础模板参数被覆盖模板参数覆盖
        
        Args:
            db: 数据库会话
            base_template_id: 基础模板ID
            override_template_id: 覆盖模板ID
            
        Returns:
            合并后的模板信息
        """
        base_template = db.query(ParameterTemplate).filter(ParameterTemplate.id == base_template_id).first()
        override_template = db.query(ParameterTemplate).filter(ParameterTemplate.id == override_template_id).first()
        
        if not base_template:
            raise ValueError(f"基础模板ID {base_template_id} 不存在")
        if not override_template:
            raise ValueError(f"覆盖模板ID {override_template_id} 不存在")
        
        # 合并参数
        base_params = {param.get("name"): param for param in base_template.parameters}
        override_params = {param.get("name"): param for param in override_template.parameters}
        
        # 应用覆盖
        merged_params = base_params.copy()
        merged_params.update(override_params)
        
        # 转换为列表
        merged_parameters = list(merged_params.values())
        
        return {
            "base_template": base_template.name,
            "override_template": override_template.name,
            "merged_parameters": merged_parameters,
            "base_parameter_count": len(base_template.parameters),
            "override_parameter_count": len(override_template.parameters),
            "merged_parameter_count": len(merged_parameters)
        }
    
    @staticmethod
    def search_templates(
        db: Session,
        name: Optional[str] = None,
        scene: Optional[str] = None,
        description: Optional[str] = None,
        active_only: bool = True,
        dimension_id: Optional[int] = None,
        subdimension_id: Optional[int] = None,
        capability_id: Optional[int] = None
    ) -> List[ParameterTemplate]:
        """
        搜索模板
        
        Args:
            db: 数据库会话
            name: 模板名称（模糊匹配）
            scene: 场景
            description: 描述（模糊匹配）
            active_only: 是否只返回激活的模板
            dimension_id: 能力维度ID
            subdimension_id: 能力子维度ID
            capability_id: 模型能力ID
            
        Returns:
            匹配的模板列表
        """
        query = db.query(ParameterTemplate)
        
        if name:
            query = query.filter(ParameterTemplate.name.ilike(f"%{name}%"))
        
        if scene:
            query = query.filter(ParameterTemplate.scene == scene)
        
        if description:
            query = query.filter(ParameterTemplate.description.ilike(f"%{description}%"))
        
        if dimension_id:
            query = query.filter(ParameterTemplate.dimension_id == dimension_id)
        
        if subdimension_id:
            query = query.filter(ParameterTemplate.subdimension_id == subdimension_id)
        
        if capability_id:
            query = query.filter(ParameterTemplate.capability_id == capability_id)
        
        if active_only:
            query = query.filter(ParameterTemplate.is_active == True)
        
        return query.order_by(ParameterTemplate.created_at.desc()).all()
    
    @staticmethod
    def get_templates_by_dimension(
        db: Session,
        dimension_id: int,
        active_only: bool = True
    ) -> List[ParameterTemplate]:
        """
        根据能力维度获取模板列表
        
        Args:
            db: 数据库会话
            dimension_id: 能力维度ID
            active_only: 是否只返回激活的模板
            
        Returns:
            匹配的模板列表
        """
        query = db.query(ParameterTemplate).filter(ParameterTemplate.dimension_id == dimension_id)
        
        if active_only:
            query = query.filter(ParameterTemplate.is_active == True)
        
        return query.order_by(ParameterTemplate.created_at.desc()).all()
    
    @staticmethod
    def get_templates_by_subdimension(
        db: Session,
        subdimension_id: int,
        active_only: bool = True
    ) -> List[ParameterTemplate]:
        """
        根据能力子维度获取模板列表
        
        Args:
            db: 数据库会话
            subdimension_id: 能力子维度ID
            active_only: 是否只返回激活的模板
            
        Returns:
            匹配的模板列表
        """
        query = db.query(ParameterTemplate).filter(ParameterTemplate.subdimension_id == subdimension_id)
        
        if active_only:
            query = query.filter(ParameterTemplate.is_active == True)
        
        return query.order_by(ParameterTemplate.created_at.desc()).all()
    
    @staticmethod
    def get_templates_by_capability(
        db: Session,
        capability_id: int,
        active_only: bool = True
    ) -> List[ParameterTemplate]:
        """
        根据模型能力获取模板列表
        
        Args:
            db: 数据库会话
            capability_id: 模型能力ID
            active_only: 是否只返回激活的模板
            
        Returns:
            匹配的模板列表
        """
        query = db.query(ParameterTemplate).filter(ParameterTemplate.capability_id == capability_id)
        
        if active_only:
            query = query.filter(ParameterTemplate.is_active == True)
        
        return query.order_by(ParameterTemplate.created_at.desc()).all()
    
    @staticmethod
    def validate_capability_relations(
        db: Session,
        dimension_id: Optional[int] = None,
        subdimension_id: Optional[int] = None,
        capability_id: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """
        验证能力维度、子维度和能力之间的关系
        
        Args:
            db: 数据库会话
            dimension_id: 能力维度ID
            subdimension_id: 能力子维度ID
            capability_id: 模型能力ID
            
        Returns:
            (是否有效, 错误消息列表)
        """
        from app.models.capability_dimension import CapabilityDimension, CapabilitySubdimension
        from app.models.model_capability import ModelCapability
        
        errors = []
        
        # 验证子维度是否属于指定的维度
        if subdimension_id and dimension_id:
            subdimension = db.query(CapabilitySubdimension).filter(
                CapabilitySubdimension.id == subdimension_id
            ).first()
            
            if not subdimension:
                errors.append(f"能力子维度ID {subdimension_id} 不存在")
            elif subdimension.dimension_id != dimension_id:
                errors.append(f"能力子维度ID {subdimension_id} 不属于能力维度ID {dimension_id}")
        
        # 验证能力是否属于指定的维度和子维度
        if capability_id:
            capability = db.query(ModelCapability).filter(
                ModelCapability.id == capability_id
            ).first()
            
            if not capability:
                errors.append(f"模型能力ID {capability_id} 不存在")
            else:
                # 验证能力与维度的关系
                if dimension_id and capability.dimension_id != dimension_id:
                    errors.append(f"模型能力ID {capability_id} 不属于能力维度ID {dimension_id}")
                
                # 验证能力与子维度的关系
                if subdimension_id and capability.subdimension_id != subdimension_id:
                    errors.append(f"模型能力ID {capability_id} 不属于能力子维度ID {subdimension_id}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _generate_next_version(current_version: str) -> str:
        """
        生成下一个版本号
        
        Args:
            current_version: 当前版本号
            
        Returns:
            下一个版本号
        """
        try:
            # 简单版本号递增逻辑
            parts = current_version.split(".")
            if len(parts) == 3:
                # 语义化版本号：主版本.次版本.修订版本
                major, minor, patch = map(int, parts)
                patch += 1
                return f"{major}.{minor}.{patch}"
            else:
                # 简单版本号
                return f"{current_version}.1"
        except:
            # 如果版本号格式不标准，使用默认递增
            return f"{current_version}.1"
    
    @staticmethod
    def validate_parameters(parameters: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        验证参数配置的有效性
        
        Args:
            parameters: 参数列表
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        for param in parameters:
            # 检查必需字段
            if "name" not in param:
                errors.append("参数缺少名称字段")
                continue
            
            param_name = param["name"]
            
            # 检查名称格式
            if not isinstance(param_name, str) or not param_name.strip():
                errors.append(f"参数名称 '{param_name}' 格式无效")
            
            # 检查默认值类型
            if "default_value" not in param:
                errors.append(f"参数 '{param_name}' 缺少默认值")
            
            # 检查参数类型
            param_type = param.get("type", "string")
            if param_type not in ["string", "integer", "float", "boolean", "array", "object"]:
                errors.append(f"参数 '{param_name}' 的类型 '{param_type}' 无效")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def export_template(template: ParameterTemplate) -> Dict[str, Any]:
        """
        导出模板为可序列化的格式
        
        Args:
            template: 模板对象
            
        Returns:
            导出的模板数据
        """
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "level": template.level,
            "level_id": template.level_id,
            "version": template.version,
            "is_active": template.is_active,
            "parameters": template.parameters,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
            "parent_id": template.parent_id
        }
    
    @staticmethod
    def import_template(db: Session, template_data: Dict[str, Any]) -> ParameterTemplate:
        """
        导入模板
        
        Args:
            db: 数据库会话
            template_data: 模板数据
            
        Returns:
            导入的模板对象
        """
        # 验证必需字段
        required_fields = ["name", "level", "parameters"]
        for field in required_fields:
            if field not in template_data:
                raise ValueError(f"导入数据缺少必需字段: {field}")
        
        # 验证能力维度关系
        dimension_id = template_data.get("dimension_id")
        subdimension_id = template_data.get("subdimension_id")
        capability_id = template_data.get("capability_id")
        
        if any([dimension_id, subdimension_id, capability_id]):
            is_valid, errors = TemplateManager.validate_capability_relations(
                db, dimension_id, subdimension_id, capability_id
            )
            
            if not is_valid:
                raise ValueError(f"能力维度关系验证失败: {', '.join(errors)}")
        
        # 创建新模板
        template = ParameterTemplate(
            name=template_data["name"],
            description=template_data.get("description"),
            level=template_data["level"],
            level_id=template_data.get("level_id"),
            parameters=template_data["parameters"],
            version=template_data.get("version", "1.0.0"),
            is_active=template_data.get("is_active", True),
            parent_id=template_data.get("parent_id"),
            
            # 能力维度关联字段
            dimension_id=dimension_id,
            subdimension_id=subdimension_id,
            capability_id=capability_id
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return template