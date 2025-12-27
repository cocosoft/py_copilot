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
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: bool = True
    logo: Optional[str] = None


class ModelSupplierCreate(ModelSupplierBase):
    """创建模型供应商请求模型"""
    pass


class ModelSupplierUpdate(BaseModel):
    """更新模型供应商请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ModelSupplierResponse(ModelSupplierBase):
    """模型供应商响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    api_endpoint: Optional[str] = None
    api_key_required: bool = False
    category: Optional[str] = None
    website: Optional[str] = None
    api_docs: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Model 相关schemas
class ModelBase(BaseModel):
    """模型基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    model_id: str = Field(..., min_length=1, max_length=100)
    model_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    type: str = Field(..., pattern="^(chat|completion|embedding)$")
    context_window: int = Field(default=8000, ge=1)
    default_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    default_max_tokens: int = Field(default=1000, ge=1)
    default_top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    default_frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    default_presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    custom_params: Optional[Dict[str, Any]] = None
    is_active: bool = True
    is_default: bool = False
    logo: Optional[str] = None


class ModelCreate(ModelBase):
    """创建模型请求模型"""
    pass


class ModelUpdate(BaseModel):
    """更新模型请求模型"""
    model_id: Optional[str] = Field(None, min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(chat|completion|embedding)$")
    context_window: Optional[int] = Field(None, ge=1)
    default_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    default_max_tokens: Optional[int] = Field(None, ge=1)
    default_top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    default_frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    default_presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    custom_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    logo: Optional[str] = None


class ModelResponse(ModelBase):
    """模型响应模型"""
    id: int
    supplier_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    categories: List[ModelCategoryResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


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
    models: List[ModelWithSupplierResponse]
    total: int


# 设置默认模型请求
class SetDefaultModelRequest(BaseModel):
    """设置默认模型请求模型"""
    model_id: int


# Model Parameter 相关schemas
class ModelParameterBase(BaseModel):
    """模型参数基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    parameter_name: str = Field(..., min_length=1, max_length=100)
    parameter_value: str = Field(..., min_length=1)
    parameter_type: str = Field(default="string", pattern="^(string|number|float|integer|int|double|boolean|json)$")
    description: Optional[str] = None
    parameter_source: str = Field(default="model", pattern="^(model_type|model)$")
    is_override: bool = Field(default=False)
    is_default: bool = Field(default=False)
    parent_parameter_id: Optional[int] = None  # 父参数ID，用于参数继承链
    parameter_level: int = Field(default=0)  # 参数层级，0表示基础层级，数字越大层级越高
    inherit_from: Optional[str] = None  # 继承来源，如"model_type:123"
    is_inherited: bool = Field(default=False)  # 是否为继承参数


class ModelParameterCreate(ModelParameterBase):
    """创建模型参数请求模型"""
    model_type_id: Optional[int] = None  # 可选的模型类型ID，用于类型级参数


class ModelParameterUpdate(BaseModel):
    """更新模型参数请求模型"""
    parameter_name: Optional[str] = Field(None, min_length=1, max_length=100)
    parameter_value: Optional[str] = None
    parameter_type: Optional[str] = Field(None, pattern="^(string|number|float|integer|int|double|boolean|json)$")
    description: Optional[str] = None
    parameter_source: Optional[str] = Field(None, pattern="^(model_type|model)$")
    is_override: Optional[bool] = None
    is_default: Optional[bool] = None
    parent_parameter_id: Optional[int] = None
    parameter_level: Optional[int] = None
    inherit_from: Optional[str] = None
    is_inherited: Optional[bool] = None


class ModelParameterResponse(ModelParameterBase):
    """模型参数响应模型"""
    id: int
    model_id: Optional[int] = None  # 模型ID，类型级参数可能为空
    model_type_id: Optional[int] = None  # 模型类型ID，用于类型级参数
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ModelParameterListResponse(BaseModel):
    """模型参数列表响应模型"""
    model_id: int
    supplier_id: int
    parameters: List[ModelParameterResponse]