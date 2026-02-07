"""本地模型管理API接口"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.dependencies import get_db
from app.models.supplier_db import ModelDB, SupplierDB
from app.schemas.model_management import ModelResponse

# 创建路由器
router = APIRouter()


@router.get("/local-models", response_model=List[ModelResponse])
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
    # 直接返回所有活跃的模型，不进行关联查询
    query = db.query(ModelDB).filter(
        ModelDB.is_active == True
    )
    
    # 执行查询
    local_models = query.all()
    
    # 创建符合ModelResponse模式的字典对象
    model_responses = []
    for model in local_models:
        # 创建包含所有必要字段的字典
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
            "categories": []
        }
        model_responses.append(model_dict)
    
    return model_responses


@router.get("/local-models/{model_id}", response_model=Optional[ModelResponse])
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
    # 直接获取指定的活跃模型，不进行关联查询
    model = db.query(ModelDB).filter(
        ModelDB.id == model_id,
        ModelDB.is_active == True
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"本地模型 ID {model_id} 不存在"
        )
    
    # 创建符合ModelResponse模式的字典对象
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
        "categories": []
    }
    
    return model_dict
