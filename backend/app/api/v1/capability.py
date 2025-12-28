"""能力相关API路由 - 向后兼容层"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.capability import CapabilityCreate, CapabilityUpdate, CapabilityResponse
from app.api.dependencies import get_db, get_current_user
from app.services.model_capability_service import model_capability_service
from app.core.logging_config import logger

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

@router.get("/capabilities/{capability_id}/parameter-templates")
def get_capability_parameter_templates(
    capability_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取与能力关联的参数模板"""
    try:
        templates = model_capability_service.get_parameter_templates_by_capability(db, capability_id)
        return templates
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取能力参数模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取能力参数模板失败: {str(e)}"
        )

# 分类默认能力相关API
from app.modules.capability_category.services.model_category_service import model_category_service

@router.get("/capability/categories/{category_id}/default-capabilities")
def get_category_default_capabilities(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取分类的默认能力"""
    try:
        return model_category_service.get_default_capabilities_by_category(db, category_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类默认能力失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类默认能力失败: {str(e)}"
        )

@router.post("/capability/categories/{category_id}/default-capabilities")
def set_category_default_capabilities(
    category_id: int,
    capability_data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """设置分类的默认能力"""
    try:
        capability_ids = capability_data.get("capability_ids", [])
        model_category_service.set_default_capabilities(db, category_id, capability_ids)
        return {"status": "success", "message": "默认能力设置成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置分类默认能力失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置分类默认能力失败: {str(e)}"
        )