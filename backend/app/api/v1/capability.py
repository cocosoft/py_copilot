"""能力相关API路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models.capability_db import CapabilityDB
from app.schemas.capability import CapabilityCreate, CapabilityResponse
from app.api.dependencies import get_db, get_current_user

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
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取能力列表"""
    return db.query(CapabilityDB).offset(skip).limit(limit).all()

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