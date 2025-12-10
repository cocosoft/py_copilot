"""供应商和模型相关的数据校验模型"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import UploadFile, File


# 供应商相关Pydantic模型
class SupplierBase(BaseModel):
    name: str = Field(..., description="供应商名称")
    description: Optional[str] = Field(None, description="供应商描述")
    website: Optional[str] = Field(None, description="供应商官网")

class SupplierCreate(SupplierBase):
    logo_url: Optional[str] = None

class SupplierResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True

# 模型相关Pydantic模型
class ModelBase(BaseModel):
    model_id: str
    model_name: Optional[str] = None
    description: Optional[str] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    is_default: bool = False
    is_active: bool = True

class ModelCreate(ModelBase):
    pass

class ModelResponse(BaseModel):
    id: int
    model_id: str
    model_name: Optional[str] = None
    description: Optional[str] = None
    supplier_id: int
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    is_default: bool = False
    is_active: bool = True
    
    class Config:
        from_attributes = True

class ModelListResponse(BaseModel):
    models: List[ModelResponse]
    total: int
