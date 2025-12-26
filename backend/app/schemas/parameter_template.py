"""参数模板相关的数据校验模型"""
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ParameterTemplateBase(BaseModel):
    """参数模板基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    parameters: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(default_factory=list, description="参数配置")
    is_active: bool = Field(default=True, description="是否激活")


class ParameterTemplateCreate(ParameterTemplateBase):
    """创建参数模板请求模型"""
    pass


class ParameterTemplateUpdate(BaseModel):
    """更新参数模板请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    parameters: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = Field(None, description="参数配置")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ParameterTemplateResponse(ParameterTemplateBase):
    """参数模板响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ParameterTemplateListResponse(BaseModel):
    """参数模板列表响应模型"""
    templates: List[ParameterTemplateResponse]
    total: int


class MergedParametersResponse(BaseModel):
    """合并参数响应模型"""
    template_id: int
    level: str
    merged_parameters: List[Dict[str, Any]]
    inheritance_path: List[int]  # 继承路径，从最顶层到当前模板


class ParameterTemplateLinkRequest(BaseModel):
    """关联参数模板请求模型"""
    template_id: int


class ParameterTemplateLinkResponse(BaseModel):
    """关联参数模板响应模型"""
    success: bool
    message: str
    model_id: Optional[int] = None
    supplier_id: Optional[int] = None
    template_id: Optional[int] = None


class ParameterTemplateVersion(BaseModel):
    """参数模板版本模型"""
    version: str = Field(..., description="版本号")
    parameters: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(..., description="参数配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
