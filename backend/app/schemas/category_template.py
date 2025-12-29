"""分类模板相关的Schema定义"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CategoryTemplateBase(BaseModel):
    """分类模板基础Schema"""
    name: str = Field(..., description="模板名称")
    display_name: str = Field(..., description="模板显示名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_data: Dict[str, Any] = Field(default_factory=dict, description="模板数据")
    is_active: bool = Field(default=True, description="是否激活")
    is_system: bool = Field(default=False, description="是否系统模板")


class CategoryTemplateCreate(CategoryTemplateBase):
    """创建分类模板的Schema"""
    pass


class CategoryTemplateUpdate(BaseModel):
    """更新分类模板的Schema"""
    name: Optional[str] = Field(None, description="模板名称")
    display_name: Optional[str] = Field(None, description="模板显示名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_data: Optional[Dict[str, Any]] = Field(None, description="模板数据")
    is_active: Optional[bool] = Field(None, description="是否激活")


class CategoryTemplateResponse(CategoryTemplateBase):
    """分类模板响应的Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ApplyTemplateResponse(BaseModel):
    """应用模板响应的Schema"""
    success: bool
    message: str
    template_data: Dict[str, Any]
    category_data: Optional[Dict[str, Any]] = None