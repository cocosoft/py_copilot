"""能力维度相关的数据校验模型"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# 能力子维度相关schemas
class CapabilitySubdimensionBase(BaseModel):
    """能力子维度基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    name: str = Field(..., min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    dimension_id: int = Field(..., gt=0)
    is_active: bool = True
    is_system: bool = False


class CapabilitySubdimensionCreate(CapabilitySubdimensionBase):
    """创建能力子维度请求模型"""
    pass


class CapabilitySubdimensionUpdate(BaseModel):
    """更新能力子维度请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CapabilitySubdimensionResponse(CapabilitySubdimensionBase):
    """能力子维度响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# 能力维度相关schemas
class CapabilityDimensionBase(BaseModel):
    """能力维度基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    name: str = Field(..., min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    is_system: bool = False


class CapabilityDimensionCreate(CapabilityDimensionBase):
    """创建能力维度请求模型"""
    pass


class CapabilityDimensionUpdate(BaseModel):
    """更新能力维度请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CapabilityDimensionResponse(CapabilityDimensionBase):
    """能力维度响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 包含子维度列表（嵌套响应）
    subdimensions: List[CapabilitySubdimensionResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class CapabilityDimensionListResponse(BaseModel):
    """能力维度列表响应模型"""
    capability_dimensions: List[CapabilityDimensionResponse]
    total: int


class CapabilitySubdimensionListResponse(BaseModel):
    """能力子维度列表响应模型"""
    capability_subdimensions: List[CapabilitySubdimensionResponse]
    total: int
