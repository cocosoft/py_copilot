"""
工作空间Schema定义

用于数据验证和序列化
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class WorkspaceBase(BaseModel):
    """
    工作空间基础Schema
    """
    name: str = Field(..., min_length=1, max_length=100, description="工作空间名称")
    description: Optional[str] = Field(None, max_length=500, description="工作空间描述")


class WorkspaceCreate(WorkspaceBase):
    """
    创建工作空间请求Schema
    """
    max_storage_bytes: int = Field(
        default=1073741824,
        ge=104857600,  # 最小100MB
        le=10737418240,  # 最大10GB
        description="最大存储空间（字节）"
    )


class WorkspaceUpdate(BaseModel):
    """
    更新工作空间请求Schema
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="工作空间名称")
    description: Optional[str] = Field(None, max_length=500, description="工作空间描述")
    max_storage_bytes: Optional[int] = Field(
        None,
        ge=104857600,
        le=10737418240,
        description="最大存储空间（字节）"
    )


class WorkspaceResponse(WorkspaceBase):
    """
    工作空间响应Schema
    """
    id: int = Field(..., description="工作空间ID")
    user_id: int = Field(..., description="所属用户ID")
    is_default: bool = Field(..., description="是否为默认工作空间")
    is_active: bool = Field(..., description="是否激活")
    max_storage_bytes: int = Field(..., description="最大存储空间（字节）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    """
    工作空间列表响应Schema
    """
    workspaces: List[WorkspaceResponse] = Field(..., description="工作空间列表")
    total: int = Field(..., description="总数")


class StorageUsageResponse(BaseModel):
    """
    存储使用情况响应Schema
    """
    workspace_id: int = Field(..., description="工作空间ID")
    max_storage_bytes: int = Field(..., description="最大存储空间（字节）")
    used_storage_bytes: int = Field(..., description="已用存储空间（字节）")
    available_storage_bytes: int = Field(..., description="可用存储空间（字节）")
    usage_percentage: float = Field(..., description="使用百分比")


class WorkspaceSwitchRequest(BaseModel):
    """
    切换工作空间请求Schema
    """
    workspace_id: int = Field(..., description="目标工作空间ID")
