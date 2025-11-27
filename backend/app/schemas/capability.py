"""能力相关Pydantic模型"""
from pydantic import BaseModel, ConfigDict
from typing import Optional

class CapabilityBase(BaseModel):
    """能力基础模型"""
    name: str
    display_name: str
    description: Optional[str] = None
    capability_type: Optional[str] = None  # 添加能力类型字段
    is_active: bool = True

class CapabilityCreate(CapabilityBase):
    """创建能力请求模型"""
    pass

class CapabilityUpdate(BaseModel):
    """更新能力请求模型"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    capability_type: Optional[str] = None  # 添加能力类型字段
    is_active: Optional[bool] = None

class CapabilityResponse(CapabilityBase):
    """能力响应模型"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)