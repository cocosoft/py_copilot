"""能力相关Pydantic模型"""
from pydantic import BaseModel, ConfigDict
from typing import Optional

class CapabilityBase(BaseModel):
    """能力基础模型"""
    name: str
    display_name: str
    description: Optional[str] = None
    is_active: bool = True

class CapabilityCreate(CapabilityBase):
    """创建能力请求模型"""
    pass

class CapabilityResponse(CapabilityBase):
    """能力响应模型"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)