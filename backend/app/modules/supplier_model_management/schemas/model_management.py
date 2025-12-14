"""模型管理相关的数据校验模型"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.model_category import ModelCategoryResponse


# ModelSupplier 相关schemas
class ModelSupplierBase(BaseModel):
    """模型供应商基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    api_endpoint: Optional[str] = None  # 改为与数据库字段匹配
    api_key_required: bool = False
    is_active: bool = True
    logo: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    api_docs: Optional[str] = None
    api_key: Optional[str] = None


class ModelSupplierCreate(ModelSupplierBase):
    """创建模型供应商请求模型"""
    pass


class ModelSupplierUpdate(BaseModel):
    """更新模型供应商请求模型"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key_required: Optional[bool] = None
    is_active: Optional[bool] = None
    logo: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    api_docs: Optional[str] = None
    api_key: Optional[str] = None


class ModelSupplierResponse(ModelSupplierBase):
    """模型供应商响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Model 相关schemas
class ModelBase(BaseModel):
    """模型基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    model_id: str = Field(..., min_length=1, max_length=100)
    model_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    model_type_id: Optional[int] = None  # 模型类型ID，关联到model_categories表
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = False
    is_active: bool = True
    logo: Optional[str] = None


class ModelCreate(ModelBase):
    """创建模型请求模型"""
    pass


class ModelUpdate(BaseModel):
    """更新模型请求模型"""
    model_id: Optional[str] = Field(None, min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    model_type_id: Optional[int] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    logo: Optional[str] = None


class ModelResponse(BaseModel):
    """模型响应模型"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_id: int
    model_id: str
    model_name: str
    description: Optional[str] = None
    model_type_id: Optional[int] = None
    model_type_name: Optional[str] = None  # 模型类型名称，从关联的model_categories表获取
    model_type_logo: Optional[str] = None  # 模型类型logo
    model_type_display_name: Optional[str] = None  # 模型类型显示名称（中文）
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = False
    is_active: bool
    logo: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ModelWithSupplierResponse(ModelResponse):
    """包含供应商信息的模型响应模型"""
    supplier: ModelSupplierResponse


# 列表响应模型
class ModelSupplierListResponse(BaseModel):
    """模型供应商列表响应模型"""
    suppliers: List[ModelSupplierResponse]
    total: int


class ModelListResponse(BaseModel):
    """模型列表响应模型"""
    models: List[ModelResponse]
    total: int


# 设置默认模型请求
class SetDefaultModelRequest(BaseModel):
    """设置默认模型请求模型"""
    model_id: int