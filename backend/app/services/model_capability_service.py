"""模型能力服务层，包含CRUD逻辑"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.supplier_db import ModelDB
from app.models.category_capability_association import CategoryCapabilityAssociation
from app.models.capability_version import ModelCapabilityVersion
from app.schemas.model_capability import ModelCapabilityCreate, ModelCapabilityUpdate, ModelCapabilityAssociationCreate, ModelCapabilityAssociationUpdate


class ModelCapabilityService:
    """模型能力服务类"""
    
    @staticmethod
    def create_capability(db: Session, capability_data: ModelCapabilityCreate) -> ModelCapability:
        """创建模型能力"""
        # 检查名称是否已存在
        existing_capability = db.query(ModelCapability).filter(
            ModelCapability.name == capability_data.name
        ).first()
        
        if existing_capability:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"模型能力 '{capability_data.name}' 已存在"
            )
        
        # 创建新能力
        db_capability = ModelCapability(**capability_data.model_dump())
        db.add(db_capability)
        db.commit()
        db.refresh(db_capability)
        
        return db_capability
    
    @staticmethod
    def get_capability(db: Session, capability_id: int) -> Optional[ModelCapability]:
        """获取单个模型能力"""
        capability = db.query(ModelCapability).filter(
            ModelCapability.id == capability_id
        ).first()
        
        if not capability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型能力 ID {capability_id} 不存在"
            )
        
        return capability
    
    @staticmethod
    def get_capability_by_name(db: Session, name: str) -> Optional[ModelCapability]:
        """根据名称获取模型能力"""
        return db.query(ModelCapability).filter(
            ModelCapability.name == name
        ).first()
    
    @staticmethod
    def get_capabilities(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        capability_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """获取模型能力列表"""
        query = db.query(ModelCapability)
        
        # 应用过滤条件
        if capability_type:
            query = query.filter(ModelCapability.capability_type == capability_type)
        if is_active is not None:
            query = query.filter(ModelCapability.is_active == is_active)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        capabilities = query.offset(skip).limit(limit).all()
        
        return {
            "capabilities": capabilities,
            "total": total
        }
    
    @staticmethod
    def update_capability(
        db: Session,
        capability_id: int,
        capability_update: ModelCapabilityUpdate
    ) -> ModelCapability:
        """更新模型能力"""
        db_capability = ModelCapabilityService.get_capability(db, capability_id)
        
        # 检查是否为系统能力
        if db_capability.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="系统能力不允许修改"
            )
        
        # 更新非空字段
        update_data = capability_update.model_dump(exclude_unset=True)
        
        # 如果更新名称，检查是否重复
        if "name" in update_data:
            existing_capability = db.query(ModelCapability).filter(
                and_(
                    ModelCapability.name == update_data["name"],
                    ModelCapability.id != capability_id
                )
            ).first()
            
            if existing_capability:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模型能力名称 '{update_data['name']}' 已存在"
                )
        
        # 执行更新
        for field, value in update_data.items():
            setattr(db_capability, field, value)
        
        db.commit()
        db.refresh(db_capability)
        
        return db_capability
    
    @staticmethod
    def delete_capability(db: Session, capability_id: int) -> bool:
        """删除模型能力（软删除）"""
        db_capability = ModelCapabilityService.get_capability(db, capability_id)
        
        # 检查是否为系统能力
        if db_capability.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="系统能力不允许删除"
            )
        
        # 检查是否有模型关联
        model_associations = db.query(ModelCapabilityAssociation).filter(
            ModelCapabilityAssociation.capability_id == capability_id
        ).count()
        
        if model_associations > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该能力下有模型关联，无法删除"
            )
        
        # 软删除
        db_capability.is_active = False
        db.commit()
        
        return True
    
    @staticmethod
    def add_capability_to_model(
        db: Session, 
        association_data: ModelCapabilityAssociationCreate
    ) -> ModelCapabilityAssociation:
        """为模型添加能力关联"""
        # 添加详细日志
        print(f"[DEBUG] 接收到的关联数据: {association_data.model_dump()}")
        
        # 检查模型是否存在
        print(f"[DEBUG] 检查模型 ID {association_data.model_id} 是否存在...")
        model = db.query(ModelDB).filter(
            ModelDB.id == association_data.model_id
        ).first()
        
        print(f"[DEBUG] 模型查询结果: {model}")
        
        if not model:
            print(f"[DEBUG] 模型 ID {association_data.model_id} 不存在，抛出404错误")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {association_data.model_id} 不存在"
            )
        
        # 检查能力是否存在
        print(f"[DEBUG] 检查能力 ID {association_data.capability_id} 是否存在...")
        capability = ModelCapabilityService.get_capability(db, association_data.capability_id)
        print(f"[DEBUG] 能力查询结果: {capability}")
        
        # 检查关联是否已存在
        print(f"[DEBUG] 检查关联是否已存在...")
        existing_association = db.query(ModelCapabilityAssociation).filter(
            and_(
                ModelCapabilityAssociation.model_id == association_data.model_id,
                ModelCapabilityAssociation.capability_id == association_data.capability_id
            )
        ).first()
        
        print(f"[DEBUG] 关联查询结果: {existing_association}")
        
        if existing_association:
            print(f"[DEBUG] 关联已存在，抛出409错误")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该模型已关联此能力"
            )
        
        # 创建关联
        print(f"[DEBUG] 开始创建关联...")
        try:
            # 将关联数据转换为字典
            association_dict = association_data.model_dump()
            print(f"[DEBUG] 关联数据字典: {association_dict}")
            
            # 创建关联对象
            db_association = ModelCapabilityAssociation(**association_dict)
            print(f"[DEBUG] 创建的关联对象: {db_association}")
            
            # 添加到数据库
            db.add(db_association)
            print(f"[DEBUG] 已添加到数据库会话")
            
            # 提交事务
            db.commit()
            print(f"[DEBUG] 已提交事务")
            
            # 刷新关联对象
            db.refresh(db_association)
            print(f"[DEBUG] 已刷新关联对象")
        except Exception as e:
            print(f"[DEBUG] 创建关联时出错: {str(e)}")
            db.rollback()  # 回滚事务
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"创建关联时出错: {str(e)}"
            )
        
        # 清理缓存
        from app.core.redis import redis_client
        if redis_client:
            try:
                cache_key = f"model_capabilities:{association_data.model_id}"
                redis_client.delete(cache_key)
            except Exception as e:
                print(f"缓存清理失败: {e}")
        
        return db_association
    
    @staticmethod
    def create_capabilities_batch(
        db: Session, 
        capabilities_data: List[ModelCapabilityCreate]
    ) -> List[ModelCapability]:
        """批量创建模型能力"""
        created_capabilities = []
        
        for capability_data in capabilities_data:
            # 检查名称是否已存在
            existing_capability = db.query(ModelCapability).filter(
                ModelCapability.name == capability_data.name
            ).first()
            
            if existing_capability:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模型能力 '{capability_data.name}' 已存在"
                )
            
            # 创建新能力
            db_capability = ModelCapability(**capability_data.model_dump())
            db.add(db_capability)
            created_capabilities.append(db_capability)
        
        db.commit()
        
        # 刷新所有创建的能力
        for capability in created_capabilities:
            db.refresh(capability)
        
        return created_capabilities
    
    @staticmethod
    def update_capabilities_batch(
        db: Session, 
        updates_data: List[Dict[str, Any]]
    ) -> List[ModelCapability]:
        """批量更新模型能力"""
        updated_capabilities = []
        
        for update_data in updates_data:
            capability_id = update_data.get("id")
            if not capability_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="更新数据缺少能力ID"
                )
            
            # 获取能力
            capability = ModelCapabilityService.get_capability(db, capability_id)
            
            # 检查是否为系统能力
            if capability.is_system:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"系统能力 {capability.name} 不允许修改"
                )
            
            # 更新非空字段
            update_fields = update_data.copy()
            update_fields.pop("id")
            
            # 如果更新名称，检查是否重复
            if "name" in update_fields:
                existing_capability = db.query(ModelCapability).filter(
                    and_(
                        ModelCapability.name == update_fields["name"],
                        ModelCapability.id != capability_id
                    )
                ).first()
                
                if existing_capability:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"模型能力名称 '{update_fields['name']}' 已存在"
                    )
            
            # 执行更新
            for field, value in update_fields.items():
                setattr(capability, field, value)
            
            updated_capabilities.append(capability)
        
        db.commit()
        
        # 刷新所有更新的能力
        for capability in updated_capabilities:
            db.refresh(capability)
        
        return updated_capabilities
    
    @staticmethod
    def delete_capabilities_batch(
        db: Session, 
        capability_ids: List[int]
    ) -> bool:
        """批量删除模型能力（软删除）"""
        for capability_id in capability_ids:
            # 获取能力
            capability = ModelCapabilityService.get_capability(db, capability_id)
            
            # 检查是否为系统能力
            if capability.is_system:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"系统能力 {capability.name} 不允许删除"
                )
            
            # 检查是否有模型关联
            model_associations = db.query(ModelCapabilityAssociation).filter(
                ModelCapabilityAssociation.capability_id == capability_id
            ).count()
            
            if model_associations > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"能力 {capability.name} 下有模型关联，无法删除"
                )
            
            # 软删除
            capability.is_active = False
        
        db.commit()
        return True
    
    @staticmethod
    def create_associations_batch(
        db: Session, 
        associations_data: List[ModelCapabilityAssociationCreate]
    ) -> List[ModelCapabilityAssociation]:
        """批量创建模型能力关联"""
        created_associations = []
        
        for association_data in associations_data:
            # 检查模型是否存在
            model = db.query(ModelDB).filter(
                ModelDB.id == association_data.model_id
            ).first()
            
            if not model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"模型 ID {association_data.model_id} 不存在"
                )
            
            # 检查能力是否存在
            try:
                capability = ModelCapabilityService.get_capability(db, association_data.capability_id)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"能力 ID {association_data.capability_id} 不存在"
                )
            
            # 检查关联是否已存在
            existing_association = db.query(ModelCapabilityAssociation).filter(
                and_(
                    ModelCapabilityAssociation.model_id == association_data.model_id,
                    ModelCapabilityAssociation.capability_id == association_data.capability_id
                )
            ).first()
            
            if existing_association:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模型 ID {association_data.model_id} 已关联能力 ID {association_data.capability_id}"
                )
            
            # 创建关联
            db_association = ModelCapabilityAssociation(**association_data.model_dump())
            db.add(db_association)
            created_associations.append(db_association)
        
        db.commit()
        
        # 刷新所有创建的关联
        for association in created_associations:
            db.refresh(association)
        
        return created_associations
    
    @staticmethod
    def delete_associations_batch(
        db: Session, 
        associations: List[Dict[str, int]]
    ) -> bool:
        """批量删除模型能力关联"""
        # 收集需要清理缓存的模型ID
        model_ids_to_clean = set()
        
        for association in associations:
            model_id = association.get("model_id")
            capability_id = association.get("capability_id")
            
            if not model_id or not capability_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="批量删除数据缺少模型ID或能力ID"
                )
            
            # 添加到需要清理缓存的模型ID集合
            model_ids_to_clean.add(model_id)
            
            # 检查关联是否存在
            existing_association = db.query(ModelCapabilityAssociation).filter(
                and_(
                    ModelCapabilityAssociation.model_id == model_id,
                    ModelCapabilityAssociation.capability_id == capability_id
                )
            ).first()
            
            if not existing_association:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"模型 ID {model_id} 与能力 ID {capability_id} 的关联不存在"
                )
            
            # 删除关联
            db.delete(existing_association)
        
        db.commit()
        
        # 清理缓存
        from app.core.redis import redis_client
        if redis_client:
            try:
                for model_id in model_ids_to_clean:
                    cache_key = f"model_capabilities:{model_id}"
                    redis_client.delete(cache_key)
            except Exception as e:
                print(f"批量缓存清理失败: {e}")
        
        return True
    
    @staticmethod
    def update_associations_batch(
        db: Session, 
        updates: List[Dict[str, Any]]
    ) -> List[ModelCapabilityAssociation]:
        """批量更新模型能力关联"""
        # 收集需要清理缓存的模型ID
        model_ids_to_clean = set()
        updated_associations = []
        
        for update_data in updates:
            model_id = update_data.get("model_id")
            capability_id = update_data.get("capability_id")
            update_fields = update_data.get("update_fields")
            
            if not model_id or not capability_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="批量更新数据缺少模型ID或能力ID"
                )
                
            if not update_fields or not isinstance(update_fields, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="批量更新数据缺少需要更新的字段"
                )
            
            # 添加到需要清理缓存的模型ID集合
            model_ids_to_clean.add(model_id)
            
            # 检查关联是否存在
            association = db.query(ModelCapabilityAssociation).filter(
                and_(
                    ModelCapabilityAssociation.model_id == model_id,
                    ModelCapabilityAssociation.capability_id == capability_id
                )
            ).first()
            
            if not association:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"模型 ID {model_id} 与能力 ID {capability_id} 的关联不存在"
                )
            
            # 验证更新字段
            valid_fields = [
                "actual_strength", "confidence_score", "assessment_method", 
                "assessment_data", "config", "config_json", "weight", "is_default"
            ]
            
            for field, value in update_fields.items():
                if field in valid_fields:
                    if field == "actual_strength" and not (1 <= value <= 5):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"actual_strength 必须在1-5之间"
                        )
                    if field == "confidence_score" and not (0 <= value <= 100):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"confidence_score 必须在0-100之间"
                        )
                    if field == "assessment_method" and value not in ["automated", "manual", "hybrid"]:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"assessment_method 必须是 automated、manual 或 hybrid"
                        )
                    setattr(association, field, value)
            
            updated_associations.append(association)
        
        db.commit()
        
        # 清理缓存
        from app.core.redis import redis_client
        if redis_client:
            try:
                for model_id in model_ids_to_clean:
                    cache_key = f"model_capabilities:{model_id}"
                    redis_client.delete(cache_key)
            except Exception as e:
                print(f"批量缓存清理失败: {e}")
        
        return updated_associations
    
    @staticmethod
    def remove_capability_from_model(
        db: Session, 
        model_id: int, 
        capability_id: int
    ) -> bool:
        """
        从模型中移除能力关联
        """
        # 检查关联是否存在
        association = db.query(ModelCapabilityAssociation).filter(
            and_(
                ModelCapabilityAssociation.model_id == model_id,
                ModelCapabilityAssociation.capability_id == capability_id
            )
        ).first()
        
        if not association:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {model_id} 与能力 ID {capability_id} 的关联不存在"
            )
        
        # 删除关联
        db.delete(association)
        db.commit()
        
        # 清理缓存
        from app.core.redis import redis_client
        if redis_client:
            try:
                cache_key = f"model_capabilities:{model_id}"
                redis_client.delete(cache_key)
            except Exception as e:
                print(f"缓存清理失败: {e}")
        
        return True
    
    @staticmethod
    def update_model_capability_association(
        db: Session,
        model_id: int,
        capability_id: int,
        association_update: ModelCapabilityAssociationUpdate
    ) -> ModelCapabilityAssociation:
        """
        更新模型能力关联
        """
        # 查找关联
        association = db.query(ModelCapabilityAssociation).filter(
            and_(
                ModelCapabilityAssociation.model_id == model_id,
                ModelCapabilityAssociation.capability_id == capability_id
            )
        ).first()
        
        if not association:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型能力关联不存在"
            )
        
        # 更新数据
        update_data = association_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(association, field, value)
        
        db.commit()
        db.refresh(association)
        
        return association
    
    @staticmethod
    def get_models_by_capability(db: Session, capability_id: int) -> List[ModelDB]:
        """获取具有指定能力的模型列表"""
        # 检查能力是否存在
        ModelCapabilityService.get_capability(db, capability_id)
        
        # 查询关联的模型，并预加载capabilities关系
        from sqlalchemy.orm import joinedload
        models = db.query(ModelDB).join(
            ModelCapabilityAssociation
        ).filter(
            ModelCapabilityAssociation.capability_id == capability_id
        ).options(
            joinedload(ModelDB.capabilities)
        ).all()
        
        return models
    
    @staticmethod
    def get_capabilities_by_model(db: Session, model_id: int) -> List[Dict[str, Any]]:
        """
        获取模型的所有能力（返回关联对象的字典格式）
        """
        # 检查模型是否存在
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {model_id} 不存在"
            )
        
        # 尝试从缓存获取
        from app.core.redis import redis_client
        cache_key = f"model_capabilities:{model_id}"
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    import json
                    return json.loads(cached_data)
            except Exception as e:
                print(f"缓存读取失败: {e}")
        
        # 查询模型能力关联
        associations = db.query(ModelCapabilityAssociation).join(
            ModelCapability
        ).filter(
            ModelCapabilityAssociation.model_id == model_id
        ).all()
        
        # 转换为关联对象数组格式 - 包含关联ID和关联的能力信息
        associations_list = []
        for association in associations:
            # 构建关联对象，包含关联ID和完整的能力信息
            association_dict = {
                'id': association.id,
                'model_id': association.model_id,
                'capability_id': association.capability_id,
                'actual_strength': association.actual_strength,
                'confidence_score': association.confidence_score,
                'assessment_method': association.assessment_method,
                'assessment_data': association.assessment_data,
                'config': association.config_json,
                'config_json': association.config_json,
                'weight': association.weight,
                'is_default': association.is_default,
                'created_at': association.created_at.isoformat() if association.created_at else None,
                'updated_at': association.updated_at.isoformat() if association.updated_at else None,
                # 包含完整的能力信息
                'capability': {
                    'id': association.capability.id,
                    'name': association.capability.name,
                    'display_name': association.capability.display_name,
                    'capability_type': association.capability.capability_type,
                    'description': association.capability.description,
                    'is_active': association.capability.is_active,
                    'is_system': association.capability.is_system,
                    'created_at': association.capability.created_at.isoformat() if association.capability.created_at else None
                }
            }
            associations_list.append(association_dict)
        
        # 保存到缓存
        if redis_client:
            try:
                import json
                redis_client.setex(
                    cache_key,
                    3600,  # 缓存1小时
                    json.dumps(associations_list)
                )
            except Exception as e:
                print(f"缓存写入失败: {e}")
        
        return associations_list
    
    @staticmethod
    def get_parameter_templates_by_capability(db: Session, capability_id: int) -> List[Dict[str, Any]]:
        """
        获取与能力关联的参数模板
        
        Args:
            db: 数据库会话
            capability_id: 模型能力ID
            
        Returns:
            与能力关联的参数模板列表
        """
        # 检查能力是否存在
        ModelCapabilityService.get_capability(db, capability_id)
        
        # 导入参数模板模型
        from app.models.parameter_template import ParameterTemplate
        
        try:
            # 首先尝试按capability_id查询（如果数据库中有这个字段）
            templates = db.query(ParameterTemplate).filter(
                ParameterTemplate.is_active == True
            ).all()
            
            # 转换为字典格式返回
            template_list = []
            for template in templates:
                # 检查模板是否有capability_id属性，并且与指定的capability_id匹配
                if hasattr(template, "capability_id") and template.capability_id == capability_id:
                    template_list.append({
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "parameters": template.parameters,
                        "level": template.level,
                        "version": template.version,
                        "created_at": template.created_at.isoformat() if hasattr(template, "created_at") and template.created_at else None,
                        "updated_at": template.updated_at.isoformat() if hasattr(template, "updated_at") and template.updated_at else None
                    })
            
            return template_list
        except Exception as e:
            # 如果查询失败（可能是因为表结构不匹配），返回空列表
            print(f"查询参数模板失败: {str(e)}")
            return []
    
    @staticmethod
    def auto_associate_default_capabilities(db: Session, model_id: int) -> List[ModelCapabilityAssociation]:
        """
        根据模型的分类自动关联默认能力
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            
        Returns:
            自动关联的能力列表
        """
        from app.services.model_category_service import model_category_service
        
        # 检查模型是否存在
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {model_id} 不存在"
            )
        
        # 获取模型的所有分类
        categories = model_category_service.get_categories_by_model(db, model_id)
        
        # 获取所有分类的默认能力
        default_capability_ids = set()
        for category in categories:
            # 查询该分类的默认能力
            category_capabilities = db.query(CategoryCapabilityAssociation).filter(
                and_(
                    CategoryCapabilityAssociation.category_id == category.id,
                    CategoryCapabilityAssociation.is_default == True
                )
            ).all()
            
            # 添加到默认能力集合
            for cat_cap in category_capabilities:
                default_capability_ids.add(cat_cap.capability_id)
        
        # 为模型添加这些默认能力（如果尚未关联）
        associated_capabilities = []
        for capability_id in default_capability_ids:
            # 检查模型是否已关联该能力
            existing_association = db.query(ModelCapabilityAssociation).filter(
                and_(
                    ModelCapabilityAssociation.model_id == model_id,
                    ModelCapabilityAssociation.capability_id == capability_id
                )
            ).first()
            
            if not existing_association:
                # 创建关联
                association_data = ModelCapabilityAssociationCreate(
                    model_id=model_id,
                    capability_id=capability_id,
                    is_default=True
                )
                
                try:
                    association = ModelCapabilityService.add_capability_to_model(db, association_data)
                    associated_capabilities.append(association)
                except HTTPException:
                    # 忽略已存在的关联或其他错误
                    continue
        
        return associated_capabilities
    
    @staticmethod
    def create_capability_version(db: Session, capability_id: int, version_data: Dict[str, Any]) -> ModelCapabilityVersion:
        """
        创建能力版本
        
        Args:
            db: 数据库会话
            capability_id: 模型能力ID
            version_data: 版本数据
            
        Returns:
            创建的版本记录
        """
        # 检查能力是否存在
        capability = ModelCapabilityService.get_capability(db, capability_id)
        
        # 自动生成版本号如果未提供
        if not version_data.get('version'):
            current_version = capability.current_version
            # 简单的版本号递增逻辑
            version_parts = list(map(int, current_version.split('.')))
            version_parts[-1] += 1
            new_version = '.'.join(map(str, version_parts))
            version_data['version'] = new_version
        
        # 设置版本数据
        version_data['capability_id'] = capability_id
        
        # 如果设置为当前版本，先将其他版本设置为非当前
        if version_data.get('is_current', False):
            db.query(ModelCapabilityVersion).filter(
                ModelCapabilityVersion.capability_id == capability_id
            ).update({'is_current': False})
            
            # 更新能力表的当前版本
            capability.current_version = version_data['version']
        
        # 如果设置为稳定版本，更新能力表的稳定版本
        if version_data.get('is_stable', False):
            capability.stable_version = version_data['version']
        
        # 创建版本记录，复制能力的当前状态
        version_record = ModelCapabilityVersion(
            **version_data,
            # 从能力表复制当前状态
            name=capability.name,
            display_name=capability.display_name,
            description=capability.description,
            capability_dimension=capability.capability_dimension,
            capability_subdimension=capability.capability_subdimension,
            base_strength=capability.base_strength,
            max_strength=capability.max_strength,
            assessment_metrics=capability.assessment_metrics,
            benchmark_datasets=capability.benchmark_datasets,
            dependencies=capability.dependencies,
            capability_type=capability.capability_type,
            input_types=capability.input_types,
            output_types=capability.output_types,
            domain=capability.domain
        )
        
        db.add(version_record)
        db.commit()
        db.refresh(version_record)
        
        return version_record
    
    @staticmethod
    def get_capability_versions(db: Session, capability_id: int) -> List[ModelCapabilityVersion]:
        """
        获取能力的所有版本
        
        Args:
            db: 数据库会话
            capability_id: 模型能力ID
            
        Returns:
            版本列表
        """
        # 检查能力是否存在
        ModelCapabilityService.get_capability(db, capability_id)
        
        # 查询所有版本，按创建时间降序排序
        versions = db.query(ModelCapabilityVersion).filter(
            ModelCapabilityVersion.capability_id == capability_id
        ).order_by(
            ModelCapabilityVersion.created_at.desc()
        ).all()
        
        return versions
    
    @staticmethod
    def get_capability_version(db: Session, capability_id: int, version_id: int) -> ModelCapabilityVersion:
        """
        获取特定版本的能力
        
        Args:
            db: 数据库会话
            capability_id: 模型能力ID
            version_id: 版本ID
            
        Returns:
            版本记录
        """
        # 查询版本
        version = db.query(ModelCapabilityVersion).filter(
            and_(
                ModelCapabilityVersion.id == version_id,
                ModelCapabilityVersion.capability_id == capability_id
            )
        ).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"版本 ID {version_id} 不存在"
            )
        
        return version
    
    @staticmethod
    def set_current_version(db: Session, capability_id: int, version_id: int) -> ModelCapabilityVersion:
        """
        将版本设置为当前版本
        
        Args:
            db: 数据库会话
            capability_id: 模型能力ID
            version_id: 版本ID
            
        Returns:
            更新后的版本记录
        """
        # 检查版本是否存在
        version = ModelCapabilityService.get_capability_version(db, capability_id, version_id)
        
        # 先将其他版本设置为非当前
        db.query(ModelCapabilityVersion).filter(
            ModelCapabilityVersion.capability_id == capability_id
        ).update({'is_current': False})
        
        # 更新该版本为当前版本
        version.is_current = True
        
        # 更新能力表的当前版本
        capability = ModelCapabilityService.get_capability(db, capability_id)
        capability.current_version = version.version
        
        db.commit()
        db.refresh(version)
        
        return version
    
    @staticmethod
    def set_stable_version(db: Session, capability_id: int, version_id: int) -> ModelCapabilityVersion:
        """
        将版本设置为稳定版本
        
        Args:
            db: 数据库会话
            capability_id: 模型能力ID
            version_id: 版本ID
            
        Returns:
            更新后的版本记录
        """
        # 检查版本是否存在
        version = ModelCapabilityService.get_capability_version(db, capability_id, version_id)
        
        # 更新该版本为稳定版本
        version.is_stable = True
        
        # 更新能力表的稳定版本
        capability = ModelCapabilityService.get_capability(db, capability_id)
        capability.stable_version = version.version
        
        db.commit()
        db.refresh(version)
        
        return version

model_capability_service = ModelCapabilityService()