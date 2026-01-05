"""参数模板模式定义"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class ParameterTemplateBase(BaseModel):
    """参数模板基础模式"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    scene: str = Field(..., description="适用场景")
    parameters: Union[Dict[str, Any], List[Any]] = Field(..., description="参数配置")


class ParameterTemplateCreate(ParameterTemplateBase):
    """创建参数模板请求"""
    is_default: bool = Field(False, description="是否为该场景的默认模板")


class ParameterTemplateUpdate(BaseModel):
    """更新参数模板请求"""
    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    scene: Optional[str] = Field(None, description="适用场景")
    parameters: Optional[Union[Dict[str, Any], List[Any]]] = Field(None, description="参数配置")
    is_default: Optional[bool] = Field(None, description="是否为该场景的默认模板")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ParameterTemplateResponse(BaseModel):
    """参数模板响应"""
    id: int
    name: str
    description: Optional[str]
    scene: str
    is_default: bool
    parameters: Union[Dict[str, Any], List[Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ParameterTemplateListResponse(BaseModel):
    """参数模板列表响应"""
    items: List[ParameterTemplateResponse]
    total: int
    page: int
    size: int
    pages: int


class ParameterTemplateVersionBase(BaseModel):
    """参数模板版本基础模式"""
    parameters: Union[Dict[str, Any], List[Any]] = Field(..., description="参数配置")


class ParameterTemplateVersionCreate(ParameterTemplateVersionBase):
    """创建参数模板版本请求"""
    changelog: Optional[str] = Field(None, description="版本变更说明")


class ParameterTemplateVersionResponse(BaseModel):
    """参数模板版本响应"""
    id: int
    template_id: int
    version: int
    parameters: Union[Dict[str, Any], List[Any]]
    changelog: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ParameterTemplateVersionListResponse(BaseModel):
    """参数模板版本列表响应"""
    items: List[ParameterTemplateVersionResponse]
    total: int
    page: int
    size: int
    pages: int