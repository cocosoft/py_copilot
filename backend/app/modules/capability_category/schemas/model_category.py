"""模型分类相关的数据校验模型"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ModelCategory 相关schemas
class ModelCategoryBase(BaseModel):
    """模型分类基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category_type: str = Field(default="main", pattern="^(main|secondary|tag)$")
    parent_id: Optional[int] = None
    is_active: bool = True
    is_system: bool = False
    logo: Optional[str] = None
    weight: int = Field(default=0, ge=0)
    dimension: Optional[str] = Field(None, max_length=50)
    default_parameters: Optional[Dict[str, Any]] = None


class ModelCategoryCreate(ModelCategoryBase):
    """创建模型分类请求模型"""
    pass


class ModelCategoryUpdate(BaseModel):
    """更新模型分类请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category_type: Optional[str] = Field(None, pattern="^(main|secondary|tag)$")
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    logo: Optional[str] = None
    weight: Optional[int] = Field(None, ge=0)
    dimension: Optional[str] = Field(None, max_length=50)
    default_parameters: Optional[Dict[str, Any]] = None


class ModelCategoryResponse(ModelCategoryBase):
    """模型分类响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    default_parameters: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ModelCategoryWithChildrenResponse(ModelCategoryResponse):
    """包含子分类的模型分类响应模型"""
    children: List['ModelCategoryWithChildrenResponse'] = []


# 为了支持循环引用，需要更新前向引用
ModelCategoryWithChildrenResponse.model_rebuild()


class ModelCategoryListResponse(BaseModel):
    """模型分类列表响应模型"""
    categories: List[ModelCategoryResponse]
    total: int


# 模型分类关联相关schemas
class ModelCategoryAssociationCreate(BaseModel):
    """创建模型分类关联请求模型"""
    model_id: int = Field(..., gt=0)
    category_id: int = Field(..., gt=0)


class ModelCategoryAssociationResponse(BaseModel):
    """模型分类关联响应模型"""
    id: int
    model_id: int
    category_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelWithCategoriesResponse(BaseModel):
    """包含分类信息的模型响应模型"""
    id: int
    name: str
    model_id: str
    categories: List[ModelCategoryResponse]
    
    model_config = ConfigDict(from_attributes=True)


class CategoryWithModelsResponse(BaseModel):
    """包含模型信息的分类响应模型"""
    id: int
    name: str
    display_name: str
    models: List[Dict[str, Any]]  # 简化的模型信息
    
    model_config = ConfigDict(from_attributes=True)