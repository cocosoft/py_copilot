"""模型能力服务层，包含CRUD逻辑"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.supplier_db import ModelDB as Model
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
        # 检查模型是否存在
        model = db.query(Model).filter(
            Model.id == association_data.model_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {association_data.model_id} 不存在"
            )
        
        # 检查能力是否存在
        capability = ModelCapabilityService.get_capability(db, association_data.capability_id)
        
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
                detail="该模型已关联此能力"
            )
        
        # 创建关联
        db_association = ModelCapabilityAssociation(**association_data.model_dump())
        db.add(db_association)
        db.commit()
        db.refresh(db_association)
        
        return db_association
    
    @staticmethod
    def update_model_capability_association(
        db: Session,
        model_id: int,
        capability_id: int,
        association_update: ModelCapabilityAssociationUpdate
    ) -> ModelCapabilityAssociation:
        """更新模型能力关联"""
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
    def remove_capability_from_model(db: Session, model_id: int, capability_id: int) -> bool:
        """从模型中移除能力关联"""
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
        
        # 删除关联
        db.delete(association)
        db.commit()
        
        return True
    
    @staticmethod
    def get_models_by_capability(db: Session, capability_id: int) -> List[Model]:
        """获取具有指定能力的模型列表"""
        # 检查能力是否存在
        ModelCapabilityService.get_capability(db, capability_id)
        
        # 查询关联的模型，并预加载capabilities关系
        from sqlalchemy.orm import joinedload
        models = db.query(Model).join(
            ModelCapabilityAssociation
        ).filter(
            ModelCapabilityAssociation.capability_id == capability_id
        ).options(
            joinedload(Model.capabilities)
        ).all()
        
        return models
    
    @staticmethod
    def get_capabilities_by_model(db: Session, model_id: int) -> List[ModelCapability]:
        """获取模型的所有能力"""
        # 检查模型是否存在
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模型 ID {model_id} 不存在"
            )
        
        # 查询关联的能力
        capabilities = db.query(ModelCapability).join(
            ModelCapabilityAssociation
        ).filter(
            ModelCapabilityAssociation.model_id == model_id
        ).all()
        
        return capabilities


model_capability_service = ModelCapabilityService()