"""能力维度服务层，包含CRUD逻辑"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.capability_dimension import CapabilityDimension, CapabilitySubdimension
from app.schemas.capability_dimension import (
    CapabilityDimensionCreate,
    CapabilityDimensionUpdate,
    CapabilitySubdimensionCreate,
    CapabilitySubdimensionUpdate
)


class CapabilityDimensionService:
    """能力维度服务类"""
    
    # ---------------------------
    # 维度相关方法
    # ---------------------------
    def get_dimension(self, db: Session, dimension_id: int) -> Optional[CapabilityDimension]:
        """
        根据ID获取能力维度
        
        Args:
            db: 数据库会话
            dimension_id: 维度ID
            
        Returns:
            能力维度对象或None
        """
        return db.query(CapabilityDimension).filter(CapabilityDimension.id == dimension_id).first()
    
    def get_dimension_by_name(self, db: Session, name: str) -> Optional[CapabilityDimension]:
        """
        根据名称获取能力维度
        
        Args:
            db: 数据库会话
            name: 维度名称
            
        Returns:
            能力维度对象或None
        """
        return db.query(CapabilityDimension).filter(CapabilityDimension.name == name).first()
    
    def get_dimensions(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        获取能力维度列表（包含子维度）
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数
            is_active: 是否仅获取激活状态的维度
            
        Returns:
            包含维度列表和总数的字典
        """
        query = db.query(CapabilityDimension).options(
            joinedload(CapabilityDimension.subdimensions)
        )
        
        # 应用筛选条件
        if is_active is not None:
            query = query.filter(CapabilityDimension.is_active == is_active)
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        dimensions = query.offset(skip).limit(limit).all()
        
        return {"capability_dimensions": dimensions, "total": total}
    
    def create_dimension(self, db: Session, dimension_in: CapabilityDimensionCreate) -> CapabilityDimension:
        """
        创建新的能力维度
        
        Args:
            db: 数据库会话
            dimension_in: 创建维度的请求数据
            
        Returns:
            创建的维度对象
            
        Raises:
            HTTPException: 当维度名称已存在时
        """
        # 检查名称是否已存在
        existing_dimension = self.get_dimension_by_name(db, dimension_in.name)
        if existing_dimension:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"能力维度名称 '{dimension_in.name}' 已存在"
            )
        
        # 创建维度
        dimension = CapabilityDimension(**dimension_in.model_dump())
        db.add(dimension)
        db.commit()
        db.refresh(dimension)
        
        return dimension
    
    def update_dimension(
        self, 
        db: Session, 
        dimension_id: int, 
        dimension_in: CapabilityDimensionUpdate
    ) -> CapabilityDimension:
        """
        更新能力维度
        
        Args:
            db: 数据库会话
            dimension_id: 维度ID
            dimension_in: 更新维度的请求数据
            
        Returns:
            更新后的维度对象
            
        Raises:
            HTTPException: 当维度不存在时
            HTTPException: 当更新的名称已存在时
        """
        # 获取维度
        dimension = self.get_dimension(db, dimension_id)
        if not dimension:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"能力维度ID {dimension_id} 不存在"
            )
        
        # 检查名称是否已被其他维度使用
        if dimension_in.name and dimension_in.name != dimension.name:
            existing_dimension = self.get_dimension_by_name(db, dimension_in.name)
            if existing_dimension:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"能力维度名称 '{dimension_in.name}' 已存在"
                )
        
        # 更新字段
        update_data = dimension_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dimension, field, value)
        
        db.add(dimension)
        db.commit()
        db.refresh(dimension)
        
        return dimension
    
    def delete_dimension(self, db: Session, dimension_id: int) -> None:
        """
        删除能力维度（软删除，仅更新is_active状态）
        
        Args:
            db: 数据库会话
            dimension_id: 维度ID
            
        Raises:
            HTTPException: 当维度不存在时
            HTTPException: 当维度是系统内置维度时
        """
        # 获取维度
        dimension = self.get_dimension(db, dimension_id)
        if not dimension:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"能力维度ID {dimension_id} 不存在"
            )
        
        # 系统内置维度不允许删除
        if dimension.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统内置能力维度不允许删除"
            )
        
        # 软删除
        dimension.is_active = False
        
        # 同时将所属子维度也设为非激活
        for subdimension in dimension.subdimensions:
            subdimension.is_active = False
        
        db.add(dimension)
        db.commit()
    
    # ---------------------------
    # 子维度相关方法
    # ---------------------------
    def get_subdimension(self, db: Session, subdimension_id: int) -> Optional[CapabilitySubdimension]:
        """
        根据ID获取能力子维度
        
        Args:
            db: 数据库会话
            subdimension_id: 子维度ID
            
        Returns:
            能力子维度对象或None
        """
        return db.query(CapabilitySubdimension).filter(CapabilitySubdimension.id == subdimension_id).first()
    
    def get_subdimension_by_name(self, db: Session, name: str) -> Optional[CapabilitySubdimension]:
        """
        根据名称获取能力子维度
        
        Args:
            db: 数据库会话
            name: 子维度名称
            
        Returns:
            能力子维度对象或None
        """
        return db.query(CapabilitySubdimension).filter(CapabilitySubdimension.name == name).first()
    
    def get_subdimensions(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        is_active: Optional[bool] = None,
        dimension_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取能力子维度列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数
            is_active: 是否仅获取激活状态的子维度
            dimension_id: 按维度筛选
            
        Returns:
            包含子维度列表和总数的字典
        """
        # 只查询dimension_id不为null的记录，避免Pydantic验证失败
        query = db.query(CapabilitySubdimension).filter(
            CapabilitySubdimension.dimension_id.isnot(None)
        )
        
        # 应用筛选条件
        if is_active is not None:
            query = query.filter(CapabilitySubdimension.is_active == is_active)
        
        if dimension_id:
            query = query.filter(CapabilitySubdimension.dimension_id == dimension_id)
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        subdimensions = query.offset(skip).limit(limit).all()
        
        return {"capability_subdimensions": subdimensions, "total": total}
    
    def create_subdimension(self, db: Session, subdimension_in: CapabilitySubdimensionCreate) -> CapabilitySubdimension:
        """
        创建新的能力子维度
        
        Args:
            db: 数据库会话
            subdimension_in: 创建子维度的请求数据
            
        Returns:
            创建的子维度对象
            
        Raises:
            HTTPException: 当子维度名称已存在时
            HTTPException: 当所属维度不存在时
        """
        # 检查名称是否已存在
        existing_subdimension = self.get_subdimension_by_name(db, subdimension_in.name)
        if existing_subdimension:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"能力子维度名称 '{subdimension_in.name}' 已存在"
            )
        
        # 检查所属维度是否存在
        dimension = self.get_dimension(db, subdimension_in.dimension_id)
        if not dimension:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"所属维度ID {subdimension_in.dimension_id} 不存在"
            )
        
        # 创建子维度
        subdimension = CapabilitySubdimension(**subdimension_in.model_dump())
        db.add(subdimension)
        db.commit()
        db.refresh(subdimension)
        
        return subdimension
    
    def update_subdimension(
        self, 
        db: Session, 
        subdimension_id: int, 
        subdimension_in: CapabilitySubdimensionUpdate
    ) -> CapabilitySubdimension:
        """
        更新能力子维度
        
        Args:
            db: 数据库会话
            subdimension_id: 子维度ID
            subdimension_in: 更新子维度的请求数据
            
        Returns:
            更新后的子维度对象
            
        Raises:
            HTTPException: 当子维度不存在时
            HTTPException: 当更新的名称已存在时
        """
        # 获取子维度
        subdimension = self.get_subdimension(db, subdimension_id)
        if not subdimension:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"能力子维度ID {subdimension_id} 不存在"
            )
        
        # 检查名称是否已被其他子维度使用
        if subdimension_in.name and subdimension_in.name != subdimension.name:
            existing_subdimension = self.get_subdimension_by_name(db, subdimension_in.name)
            if existing_subdimension:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"能力子维度名称 '{subdimension_in.name}' 已存在"
                )
        
        # 更新字段
        update_data = subdimension_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subdimension, field, value)
        
        db.add(subdimension)
        db.commit()
        db.refresh(subdimension)
        
        return subdimension
    
    def delete_subdimension(self, db: Session, subdimension_id: int) -> None:
        """
        删除能力子维度（软删除，仅更新is_active状态）
        
        Args:
            db: 数据库会话
            subdimension_id: 子维度ID
            
        Raises:
            HTTPException: 当子维度不存在时
            HTTPException: 当子维度是系统内置子维度时
        """
        # 获取子维度
        subdimension = self.get_subdimension(db, subdimension_id)
        if not subdimension:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"能力子维度ID {subdimension_id} 不存在"
            )
        
        # 系统内置子维度不允许删除
        if subdimension.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统内置能力子维度不允许删除"
            )
        
        # 软删除
        subdimension.is_active = False
        db.add(subdimension)
        db.commit()


# 创建服务实例
capability_dimension_service = CapabilityDimensionService()
