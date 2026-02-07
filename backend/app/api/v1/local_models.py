"""本地模型管理API接口"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.dependencies import get_db
from app.models.supplier_db import ModelDB, SupplierDB
from app.schemas.model_management import ModelResponse, ModelWithSupplierResponse, ModelSupplierResponse

# 创建路由器
router = APIRouter()


@router.get("/local-models", response_model=List[ModelWithSupplierResponse])
async def get_local_models(
    supplier: Optional[str] = Query(None, description="供应商名称，用于过滤"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取本地模型列表
    
    Args:
        supplier: 供应商名称，用于过滤
        db: 数据库会话
    
    Returns:
        本地模型列表
    """
    # 根据供应商的is_local字段筛选本地模型
    query = db.query(ModelDB).join(SupplierDB).filter(
        ModelDB.is_active == True,
        SupplierDB.is_local == True
    )
    
    # 如果指定了供应商名称，进一步过滤
    if supplier:
        query = query.filter(SupplierDB.name.ilike(f"%{supplier}%"))
    
    # 执行查询
    local_models = query.all()
    
    # 创建符合ModelWithSupplierResponse模式的字典对象，包含供应商信息
    model_responses = []
    for model in local_models:
        # 创建包含所有必要字段的字典，包括供应商信息
        model_dict = {
            "id": model.id,
            "model_id": model.model_id,
            "model_name": model.model_name,
            "description": model.description or "",
            "type": "chat",  # 设置默认值为"chat"
            "context_window": model.context_window or 8000,
            "default_temperature": 0.7,
            "default_max_tokens": 1000,
            "default_top_p": 1.0,
            "default_frequency_penalty": 0.0,
            "default_presence_penalty": 0.0,
            "custom_params": {},
            "is_active": model.is_active,
            "is_default": model.is_default,
            "logo": model.logo,
            "supplier_id": model.supplier_id,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "categories": [],
            # 添加供应商信息（符合ModelWithSupplierResponse要求）
            "supplier": {
                "id": model.supplier.id,
                "name": model.supplier.name,
                "display_name": model.supplier.display_name if model.supplier.display_name else model.supplier.name,
                "description": model.supplier.description,
                "logo": model.supplier.logo,
                "is_active": model.supplier.is_active,
                "api_endpoint": model.supplier.api_endpoint,
                "api_key_required": model.supplier.api_key_required,
                "category": model.supplier.category,
                "website": model.supplier.website,
                "api_docs": model.supplier.api_docs,
                "created_at": model.supplier.created_at,
                "updated_at": model.supplier.updated_at
            }
        }
        model_responses.append(model_dict)
    
    return model_responses


@router.get("/local-models/{model_id}", response_model=Optional[ModelWithSupplierResponse])
async def get_local_model(
    model_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取指定的本地模型
    
    Args:
        model_id: 模型ID
        db: 数据库会话
    
    Returns:
        本地模型信息，如果不存在则返回None
    """
    # 获取指定的活跃本地模型（通过本地供应商）
    model = db.query(ModelDB).join(SupplierDB).filter(
        ModelDB.id == model_id,
        ModelDB.is_active == True,
        SupplierDB.is_local == True
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"本地模型 ID {model_id} 不存在"
        )
    
    # 创建符合ModelWithSupplierResponse模式的字典对象，包含供应商信息
    model_dict = {
        "id": model.id,
        "model_id": model.model_id,
        "model_name": model.model_name,
        "description": model.description or "",
        "type": "chat",  # 设置默认值为"chat"
        "context_window": model.context_window or 8000,
        "default_temperature": 0.7,
        "default_max_tokens": 1000,
        "default_top_p": 1.0,
        "default_frequency_penalty": 0.0,
        "default_presence_penalty": 0.0,
        "custom_params": {},
        "is_active": model.is_active,
        "is_default": model.is_default,
        "logo": model.logo,
        "supplier_id": model.supplier_id,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "categories": [],
        # 添加供应商信息（符合ModelWithSupplierResponse要求）
        "supplier": {
            "id": model.supplier.id,
            "name": model.supplier.name,
            "display_name": model.supplier.display_name if model.supplier.display_name else model.supplier.name,
            "description": model.supplier.description,
            "logo": model.supplier.logo,
            "is_active": model.supplier.is_active,
            "api_endpoint": model.supplier.api_endpoint,
            "api_key_required": model.supplier.api_key_required,
            "category": model.supplier.category,
            "website": model.supplier.website,
            "api_docs": model.supplier.api_docs,
            "created_at": model.supplier.created_at,
            "updated_at": model.supplier.updated_at
        }
    }
    
    return model_dict
