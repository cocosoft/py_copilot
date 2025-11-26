"""供应商和模型相关的数据校验模型"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# 供应商相关Pydantic模型
class SupplierBase(BaseModel):
    name: str
    description: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key_required: bool = False
    # 新增字段
    logo: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    api_docs: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = True
    # 接受前端传递的isDomestic字段但不保存到数据库
    isDomestic: Optional[bool] = None
    
    class Config:
        extra = 'allow'

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key_required: Optional[bool] = False
    # 新增字段
    logo: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    api_docs: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

# 模型相关Pydantic模型
class ModelBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    is_default: bool = False
    is_active: bool = True

class ModelCreate(ModelBase):
    supplier_id: int

class ModelResponse(BaseModel):
    id: int
    name: str
    display_name: Optional[str] = None
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
