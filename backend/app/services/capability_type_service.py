"""能力类型服务层，包含CRUD逻辑"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.capability_type import CapabilityType
from app.schemas.capability_type import CapabilityTypeCreate, CapabilityTypeUpdate


class CapabilityTypeService:
    """能力类型服务类"""
    
    def get_capability_type(self, db: Session, capability_type_id: int) -> Optional[CapabilityType]:
        """
        根据ID获取能力类型
        
        Args:
            db: 数据库会话
            capability_type_id: 能力类型ID
            
        Returns:
            能力类型对象或None
        """
        return db.query(CapabilityType).filter(CapabilityType.id == capability_type_id).first()
    
    def get_capability_type_by_name(self, db: Session, name: str) -> Optional[CapabilityType]:
        """
        根据名称获取能力类型
        
        Args:
            db: 数据库会话
            name: 能力类型名称
            
        Returns:
            能力类型对象或None
        """
        return db.query(CapabilityType).filter(CapabilityType.name == name).first()
    
    def get_capability_types(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        is_active: Optional[bool] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取能力类型列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数
            is_active: 是否仅获取激活状态的类型
            category: 按分类筛选
            
        Returns:
            包含能力类型列表和总数的字典
        """
        query = db.query(CapabilityType)
        
        # 应用筛选条件
        if is_active is not None:
            query = query.filter(CapabilityType.is_active == is_active)
        
        if category:
            query = query.filter(CapabilityType.category == category)
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        capability_types = query.offset(skip).limit(limit).all()
        
        return {"capability_types": capability_types, "total": total}
    
    def create_capability_type(self, db: Session, capability_type_in: CapabilityTypeCreate) -> CapabilityType:
        """
        创建新的能力类型
        
        Args:
            db: 数据库会话
            capability_type_in: 创建能力类型的请求数据
            
        Returns:
            创建的能力类型对象
            
        Raises:
            HTTPException: 当能力类型名称已存在时
        """
        # 检查名称是否已存在
        existing_type = self.get_capability_type_by_name(db, capability_type_in.name)
        if existing_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"能力类型名称 '{capability_type_in.name}' 已存在"
            )
        
        # 创建能力类型
        capability_type = CapabilityType(**capability_type_in.model_dump())
        db.add(capability_type)
        db.commit()
        db.refresh(capability_type)
        
        return capability_type
    
    def update_capability_type(
        self, 
        db: Session, 
        capability_type_id: int, 
        capability_type_in: CapabilityTypeUpdate
    ) -> CapabilityType:
        """
        更新能力类型
        
        Args:
            db: 数据库会话
            capability_type_id: 能力类型ID
            capability_type_in: 更新能力类型的请求数据
            
        Returns:
            更新后的能力类型对象
            
        Raises:
            HTTPException: 当能力类型不存在时
            HTTPException: 当更新的名称已存在时
        """
        # 获取能力类型
        capability_type = self.get_capability_type(db, capability_type_id)
        if not capability_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"能力类型ID {capability_type_id} 不存在"
            )
        
        # 检查名称是否已被其他类型使用
        if capability_type_in.name and capability_type_in.name != capability_type.name:
            existing_type = self.get_capability_type_by_name(db, capability_type_in.name)
            if existing_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"能力类型名称 '{capability_type_in.name}' 已存在"
                )
        
        # 更新字段
        update_data = capability_type_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(capability_type, field, value)
        
        db.add(capability_type)
        db.commit()
        db.refresh(capability_type)
        
        return capability_type
    
    def delete_capability_type(self, db: Session, capability_type_id: int) -> None:
        """
        删除能力类型（软删除，仅更新is_active状态）
        
        Args:
            db: 数据库会话
            capability_type_id: 能力类型ID
            
        Raises:
            HTTPException: 当能力类型不存在时
            HTTPException: 当能力类型是系统内置类型时
        """
        # 获取能力类型
        capability_type = self.get_capability_type(db, capability_type_id)
        if not capability_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"能力类型ID {capability_type_id} 不存在"
            )
        
        # 系统内置类型不允许删除
        if capability_type.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统内置能力类型不允许删除"
            )
        
        # 软删除
        capability_type.is_active = False
        db.add(capability_type)
        db.commit()


# 创建服务实例
capability_type_service = CapabilityTypeService()
