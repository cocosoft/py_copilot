"""能力相关API路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.modules.capability_category.models.capability_db import CapabilityDB
from app.modules.capability_category.schemas.capability import CapabilityCreate, CapabilityUpdate, CapabilityResponse
from app.core.dependencies import get_db, get_current_user

# 创建路由器
router = APIRouter()

@router.post("/model/capabilities", response_model=CapabilityResponse)
def create_capability(
    capability: CapabilityCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建新的能力"""
    # 检查名称是否已存在
    existing_capability = db.query(CapabilityDB).filter(CapabilityDB.name == capability.name).first()
    if existing_capability:
        raise HTTPException(status_code=400, detail="Capability name already exists")
    
    # 创建新能力
    db_capability = CapabilityDB(**capability.dict())
    db.add(db_capability)
    db.commit()
    db.refresh(db_capability)
    
    return db_capability

@router.get("/model/capabilities", response_model=List[CapabilityResponse])
def get_capabilities(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取能力列表"""
    query = db.query(CapabilityDB)
    
    # 过滤活跃状态
    if is_active is not None:
        query = query.filter(CapabilityDB.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

@router.get("/model/capabilities/{capability_id}", response_model=CapabilityResponse)
def get_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取单个能力"""
    capability = db.query(CapabilityDB).filter(CapabilityDB.id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")
    return capability

@router.put("/model/capabilities/{capability_id}", response_model=CapabilityResponse)
def update_capability(
    capability_id: int,
    capability_update: CapabilityUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新能力"""
    # 查找要更新的能力
    capability = db.query(CapabilityDB).filter(CapabilityDB.id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")
    
    # 如果更新名称，检查新名称是否已存在
    if capability_update.name and capability_update.name != capability.name:
        existing_capability = db.query(CapabilityDB).filter(CapabilityDB.name == capability_update.name).first()
        if existing_capability:
            raise HTTPException(status_code=400, detail="Capability name already exists")
    
    # 更新非空字段
    update_data = capability_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(capability, field, value)
    
    db.commit()
    db.refresh(capability)
    return capability

@router.delete("/model/capabilities/{capability_id}", status_code=204)
def delete_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除能力"""
    # 查找要删除的能力
    capability = db.query(CapabilityDB).filter(CapabilityDB.id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")
    
    # 软删除：将is_active设置为False
    capability.is_active = False
    db.commit()
    return None