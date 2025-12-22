"""能力相关API路由 - 向后兼容层"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.capability import CapabilityCreate, CapabilityUpdate, CapabilityResponse
from app.api.dependencies import get_db, get_current_user
from app.services.model_capability_service import model_capability_service

# 创建路由器
router = APIRouter()

@router.post("/capabilities", response_model=CapabilityResponse)
def create_capability(
    capability: CapabilityCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建新的能力"""
    from app.schemas.model_capability import ModelCapabilityCreate
    
    # 转换为ModelCapabilityCreate
    model_capability = ModelCapabilityCreate(
        name=capability.name,
        display_name=capability.display_name,
        description=capability.description,
        capability_type=capability.capability_type or "standard",
        domain="nlp",  # 默认领域
        input_types=None,
        output_types=None
    )
    
    # 使用服务层创建能力
    db_capability = model_capability_service.create_capability(db, model_capability)
    
    # 转换回CapabilityResponse
    return CapabilityResponse(
        id=db_capability.id,
        name=db_capability.name,
        display_name=db_capability.display_name,
        description=db_capability.description,
        capability_type=db_capability.capability_type,
        is_active=db_capability.is_active
    )

@router.get("/capabilities", response_model=List[CapabilityResponse])
def get_capabilities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取能力列表"""
    result = model_capability_service.get_capabilities(db, skip, limit)
    
    # 转换结果
    capabilities = []
    for cap in result["capabilities"]:
        capabilities.append(CapabilityResponse(
            id=cap.id,
            name=cap.name,
            display_name=cap.display_name,
            description=cap.description,
            capability_type=cap.capability_type,
            is_active=cap.is_active
        ))
    
    return capabilities

@router.get("/capabilities/{capability_id}", response_model=CapabilityResponse)
def get_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取单个能力"""
    try:
        db_capability = model_capability_service.get_capability(db, capability_id)
        
        # 转换为CapabilityResponse
        return CapabilityResponse(
            id=db_capability.id,
            name=db_capability.name,
            display_name=db_capability.display_name,
            description=db_capability.description,
            capability_type=db_capability.capability_type,
            is_active=db_capability.is_active
        )
    except HTTPException:
        raise

@router.put("/capabilities/{capability_id}", response_model=CapabilityResponse)
def update_capability(
    capability_id: int,
    capability_update: CapabilityUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新能力"""
    from app.schemas.model_capability import ModelCapabilityUpdate
    
    # 转换为ModelCapabilityUpdate
    model_update = ModelCapabilityUpdate(
        name=capability_update.name,
        display_name=capability_update.display_name,
        description=capability_update.description,
        capability_type=capability_update.capability_type,
        is_active=capability_update.is_active
    )
    
    try:
        db_capability = model_capability_service.update_capability(db, capability_id, model_update)
        
        # 转换为CapabilityResponse
        return CapabilityResponse(
            id=db_capability.id,
            name=db_capability.name,
            display_name=db_capability.display_name,
            description=db_capability.description,
            capability_type=db_capability.capability_type,
            is_active=db_capability.is_active
        )
    except HTTPException:
        raise

@router.delete("/capabilities/{capability_id}", status_code=204)
def delete_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除能力"""
    try:
        model_capability_service.delete_capability(db, capability_id)
        return None
    except HTTPException:
        raise