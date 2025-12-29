"""模型能力相关的数据校验模型"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ModelCapability 相关schemas
class ModelCapabilityBase(BaseModel):
    """模型能力基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    capability_type: str = Field(default="standard", pattern="^[a-zA-Z0-9_]+$")
    is_active: bool = True


class ModelCapabilityCreate(ModelCapabilityBase):
    """创建模型能力请求模型"""
    pass


class ModelCapabilityUpdate(BaseModel):
    """更新模型能力请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    capability_type: Optional[str] = Field(None, pattern="^[a-zA-Z0-9_]+$")
    is_active: Optional[bool] = None


class ModelCapabilityResponse(ModelCapabilityBase):
    """模型能力响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ModelCapabilityListResponse(BaseModel):
    """模型能力列表响应模型"""
    capabilities: List[ModelCapabilityResponse]
    total: int


# 模型能力关联相关schemas
class ModelCapabilityAssociationCreate(BaseModel):
    """创建模型能力关联请求模型"""
    model_id: int = Field(..., gt=0)
    capability_id: int = Field(..., gt=0)


class ModelCapabilityAssociationUpdate(BaseModel):
    """更新模型能力关联请求模型"""
    pass


class ModelCapabilityAssociationResponse(BaseModel):
    """模型能力关联响应模型"""
    id: int
    model_id: int
    capability_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelWithCapabilitiesResponse(BaseModel):
    """包含能力信息的模型响应模型"""
    id: int
    name: str
    model_id: str
    capabilities: List[ModelCapabilityResponse]
    
    model_config = ConfigDict(from_attributes=True)


class CapabilityWithModelsResponse(BaseModel):
    """包含模型信息的能力响应模型"""
    id: int
    name: str
    display_name: str
    models: List[Dict[str, Any]]  # 简化的模型信息
    
    model_config = ConfigDict(from_attributes=True)