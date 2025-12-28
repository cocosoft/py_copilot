"""能力类型相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.capability_type import (
    CapabilityTypeCreate,
    CapabilityTypeUpdate,
    CapabilityTypeResponse,
    CapabilityTypeListResponse
)
from app.schemas.response import SuccessResponse, SuccessData, ListResponse
from app.utils.response_utils import (
    success_with_data,
    success_with_message,
    list_response,
    raise_http_exception
)
from app.services.capability_type_service import capability_type_service
from app.api.deps import get_current_user
from app.models.user import User

# 创建路由器
router = APIRouter(prefix="/capability/types", tags=["capability_types"])


@router.post("/", response_model=SuccessData[CapabilityTypeResponse], status_code=status.HTTP_201_CREATED)
async def create_capability_type(
    capability_type: CapabilityTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的能力类型"""
    try:
        db_capability_type = capability_type_service.create_capability_type(db, capability_type)
        return success_with_data(db_capability_type, message="能力类型创建成功", code=201)
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="创建能力类型失败",
            detail=str(e)
        )


@router.get("/{capability_type_id}", response_model=SuccessData[CapabilityTypeResponse])
async def get_capability_type(
    capability_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个能力类型"""
    try:
        db_capability_type = capability_type_service.get_capability_type(db, capability_type_id)
        if not db_capability_type:
            raise HTTPException(status_code=404, detail="能力类型不存在")
        return success_with_data(db_capability_type, message="获取能力类型成功")
    except HTTPException:
        raise
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取能力类型失败",
            detail=str(e)
        )


@router.get("/", response_model=ListResponse[CapabilityTypeResponse])
async def get_capability_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取能力类型列表"""
    try:
        result = capability_type_service.get_capability_types(
            db=db,
            skip=skip,
            limit=limit,
            is_active=is_active,
            category=category
        )
        return list_response(
            data=result["capability_types"],
            total=result["total"],
            page=skip // limit + 1 if limit > 0 else None,
            size=limit,
            message="获取能力类型列表成功"
        )
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取能力类型列表失败",
            detail=str(e)
        )


@router.put("/{capability_type_id}", response_model=SuccessData[CapabilityTypeResponse])
async def update_capability_type(
    capability_type_id: int,
    capability_type_update: CapabilityTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新能力类型"""
    try:
        updated_capability_type = capability_type_service.update_capability_type(
            db, capability_type_id, capability_type_update
        )
        return success_with_data(updated_capability_type, message="能力类型更新成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="更新能力类型失败",
            detail=str(e)
        )


@router.delete("/{capability_type_id}", response_model=SuccessResponse)
async def delete_capability_type(
    capability_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除能力类型（软删除）"""
    try:
        capability_type_service.delete_capability_type(db, capability_type_id)
        return success_with_message("能力类型删除成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="删除能力类型失败",
            detail=str(e)
        )
