"""能力维度相关的API路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.capability_dimension import (
    CapabilityDimensionCreate,
    CapabilityDimensionUpdate,
    CapabilityDimensionResponse,
    CapabilitySubdimensionCreate,
    CapabilitySubdimensionUpdate,
    CapabilitySubdimensionResponse,
    CapabilityDimensionListResponse,
    CapabilitySubdimensionListResponse
)
from app.schemas.response import SuccessResponse, SuccessData, ListResponse
from app.utils.response_utils import (
    success_with_data,
    success_with_message,
    list_response,
    raise_http_exception
)
from app.services.capability_dimension_service import capability_dimension_service
from app.api.deps import get_current_user
from app.models.user import User

# 创建路由器
router = APIRouter(prefix="/capability/dimensions", tags=["capability_dimensions"])


# ---------------------------
# 能力维度相关接口
# ---------------------------
@router.post("/", response_model=SuccessData[CapabilityDimensionResponse], status_code=status.HTTP_201_CREATED)
async def create_capability_dimension(
    dimension: CapabilityDimensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的能力维度"""
    try:
        db_dimension = capability_dimension_service.create_dimension(db, dimension)
        return success_with_data(db_dimension, message="能力维度创建成功", code=201)
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="创建能力维度失败",
            detail=str(e)
        )


@router.get("/", response_model=ListResponse[CapabilityDimensionResponse])
async def get_capability_dimensions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取能力维度列表（包含子维度）"""
    try:
        result = capability_dimension_service.get_dimensions(
            db=db,
            skip=skip,
            limit=limit,
            is_active=is_active
        )
        return list_response(
            data=result["capability_dimensions"],
            total=result["total"],
            page=skip // limit + 1 if limit > 0 else None,
            size=limit,
            message="获取能力维度列表成功"
        )
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取能力维度列表失败",
            detail=str(e)
        )


# ---------------------------
# 能力子维度相关接口
# ---------------------------
@router.post("/subdimensions", response_model=SuccessData[CapabilitySubdimensionResponse], status_code=status.HTTP_201_CREATED)
async def create_capability_subdimension(
    subdimension: CapabilitySubdimensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的能力子维度"""
    try:
        db_subdimension = capability_dimension_service.create_subdimension(db, subdimension)
        return success_with_data(db_subdimension, message="能力子维度创建成功", code=201)
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="创建能力子维度失败",
            detail=str(e)
        )


@router.get("/subdimensions", response_model=ListResponse[CapabilitySubdimensionResponse])
async def get_capability_subdimensions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    dimension_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取能力子维度列表"""
    try:
        result = capability_dimension_service.get_subdimensions(
            db=db,
            skip=skip,
            limit=limit,
            is_active=is_active,
            dimension_id=dimension_id
        )
        return list_response(
            data=result["capability_subdimensions"],
            total=result["total"],
            page=skip // limit + 1 if limit > 0 else None,
            size=limit,
            message="获取能力子维度列表成功"
        )
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取能力子维度列表失败",
            detail=str(e)
        )


@router.get("/subdimensions/{subdimension_id}", response_model=SuccessData[CapabilitySubdimensionResponse])
async def get_capability_subdimension(
    subdimension_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个能力子维度"""
    try:
        db_subdimension = capability_dimension_service.get_subdimension(db, subdimension_id)
        if not db_subdimension:
            raise HTTPException(status_code=404, detail="能力子维度不存在")
        return success_with_data(db_subdimension, message="获取能力子维度成功")
    except HTTPException:
        raise
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取能力子维度失败",
            detail=str(e)
        )


@router.put("/subdimensions/{subdimension_id}", response_model=SuccessData[CapabilitySubdimensionResponse])
async def update_capability_subdimension(
    subdimension_id: int,
    subdimension_update: CapabilitySubdimensionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新能力子维度"""
    try:
        updated_subdimension = capability_dimension_service.update_subdimension(
            db, subdimension_id, subdimension_update
        )
        return success_with_data(updated_subdimension, message="能力子维度更新成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="更新能力子维度失败",
            detail=str(e)
        )


@router.delete("/subdimensions/{subdimension_id}", response_model=SuccessResponse)
async def delete_capability_subdimension(
    subdimension_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除能力子维度（软删除）"""
    try:
        capability_dimension_service.delete_subdimension(db, subdimension_id)
        return success_with_message("能力子维度删除成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="删除能力子维度失败",
            detail=str(e)
        )


# ---------------------------
# 能力维度相关接口（单个操作）
# ---------------------------
@router.get("/{dimension_id}", response_model=SuccessData[CapabilityDimensionResponse])
async def get_capability_dimension(
    dimension_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个能力维度"""
    try:
        db_dimension = capability_dimension_service.get_dimension(db, dimension_id)
        if not db_dimension:
            raise HTTPException(status_code=404, detail="能力维度不存在")
        return success_with_data(db_dimension, message="获取能力维度成功")
    except HTTPException:
        raise
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="获取能力维度失败",
            detail=str(e)
        )


@router.put("/{dimension_id}", response_model=SuccessData[CapabilityDimensionResponse])
async def update_capability_dimension(
    dimension_id: int,
    dimension_update: CapabilityDimensionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新能力维度"""
    try:
        updated_dimension = capability_dimension_service.update_dimension(
            db, dimension_id, dimension_update
        )
        return success_with_data(updated_dimension, message="能力维度更新成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="更新能力维度失败",
            detail=str(e)
        )


@router.delete("/{dimension_id}", response_model=SuccessResponse)
async def delete_capability_dimension(
    dimension_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除能力维度（软删除）"""
    try:
        capability_dimension_service.delete_dimension(db, dimension_id)
        return success_with_message("能力维度删除成功")
    except Exception as e:
        raise_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="删除能力维度失败",
            detail=str(e)
        )
