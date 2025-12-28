"""能力类型相关的数据校验模型"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CapabilityTypeBase(BaseModel):
    """能力类型基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    name: str = Field(..., min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(default="general", max_length=50)
    icon: Optional[str] = None
    is_active: bool = True
    is_system: bool = False


class CapabilityTypeCreate(CapabilityTypeBase):
    """创建能力类型请求模型"""
    pass


class CapabilityTypeUpdate(BaseModel):
    """更新能力类型请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class CapabilityTypeResponse(CapabilityTypeBase):
    """能力类型响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class CapabilityTypeListResponse(BaseModel):
    """能力类型列表响应模型"""
    capability_types: List[CapabilityTypeResponse]
    total: int
