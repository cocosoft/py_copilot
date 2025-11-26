"""模型能力相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.model_capability import (
    ModelCapabilityCreate,
    ModelCapabilityUpdate,
    ModelCapabilityResponse,
    ModelCapabilityListResponse,
    ModelCapabilityAssociationCreate,
    ModelCapabilityAssociationUpdate,
    ModelCapabilityAssociationResponse,
    ModelWithCapabilitiesResponse,
    CapabilityWithModelsResponse
)
from app.services.model_capability_service import model_capability_service

# 创建路由器
router = APIRouter(prefix="/capabilities", tags=["model_capabilities"])


# 模拟用户认证依赖
async def get_current_user():
    """获取当前用户"""
    # 实际项目中应该有真实的认证逻辑
    return {"id": 1, "username": "admin"}


@router.post("/", response_model=ModelCapabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_capability(
    capability: ModelCapabilityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新的模型能力"""
    db_capability = model_capability_service.create_capability(db, capability)
    return db_capability


@router.get("/{capability_id}", response_model=ModelCapabilityResponse)
async def get_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个模型能力"""
    db_capability = model_capability_service.get_capability(db, capability_id)
    return db_capability


@router.get("/", response_model=ModelCapabilityListResponse)
async def get_capabilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    capability_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取模型能力列表"""
    result = model_capability_service.get_capabilities(
        db=db,
        skip=skip,
        limit=limit,
        capability_type=capability_type,
        is_active=is_active
    )
    return result


@router.put("/{capability_id}", response_model=ModelCapabilityResponse)
async def update_capability(
    capability_id: int,
    capability_update: ModelCapabilityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新模型能力"""
    updated_capability = model_capability_service.update_capability(
        db, capability_id, capability_update
    )
    return updated_capability


@router.delete("/{capability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除模型能力（软删除）"""
    model_capability_service.delete_capability(db, capability_id)
    return None


@router.post("/associations", response_model=ModelCapabilityAssociationResponse, status_code=status.HTTP_201_CREATED)
async def create_model_capability_association(
    association: ModelCapabilityAssociationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建模型和能力的关联"""
    db_association = model_capability_service.add_capability_to_model(db, association)
    return db_association


@router.put("/associations/model/{model_id}/capability/{capability_id}", response_model=ModelCapabilityAssociationResponse)
async def update_model_capability_association(
    model_id: int,
    capability_id: int,
    association_update: ModelCapabilityAssociationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新模型和能力的关联"""
    db_association = model_capability_service.update_model_capability_association(
        db, model_id, capability_id, association_update
    )
    return db_association


@router.delete("/associations/model/{model_id}/capability/{capability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_capability_association(
    model_id: int,
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除模型和能力的关联"""
    model_capability_service.remove_capability_from_model(db, model_id, capability_id)
    return None


@router.get("/{capability_id}/models", response_model=List[ModelWithCapabilitiesResponse])
async def get_models_by_capability(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取具有指定能力的模型列表"""
    models = model_capability_service.get_models_by_capability(db, capability_id)
    return models


@router.get("/model/{model_id}/capabilities", response_model=List[ModelCapabilityResponse])
async def get_capabilities_by_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取指定模型的所有能力"""
    capabilities = model_capability_service.get_capabilities_by_model(db, model_id)
    return capabilities