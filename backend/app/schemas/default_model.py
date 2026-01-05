"""默认模型相关请求/响应模式"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# 创建默认模型请求
class DefaultModelBase(BaseModel):
    """默认模型基础模式"""
    scope: str = Field(..., description="默认作用域：'global'（全局）、'scene'（场景）")
    scene: Optional[str] = Field(None, description="场景名称，当scope为'scene'时使用")
    model_id: int = Field(..., description="默认模型ID")
    priority: int = Field(1, description="模型优先级，数字越小优先级越高")
    fallback_model_id: Optional[int] = Field(None, description="备选模型ID")
    is_active: bool = Field(True, description="是否激活")

class DefaultModelCreate(DefaultModelBase):
    """创建默认模型请求"""
    pass

class DefaultModelUpdate(BaseModel):
    """更新默认模型请求"""
    scope: Optional[str] = Field(None, description="默认作用域：'global'（全局）、'scene'（场景）")
    scene: Optional[str] = Field(None, description="场景名称，当scope为'scene'时使用")
    model_id: Optional[int] = Field(None, description="默认模型ID")
    priority: Optional[int] = Field(None, description="模型优先级，数字越小优先级越高")
    fallback_model_id: Optional[int] = Field(None, description="备选模型ID")
    is_active: Optional[bool] = Field(None, description="是否激活")

class DefaultModelResponse(BaseModel):
    """默认模型响应"""
    id: int
    scope: str
    scene: Optional[str]
    model_id: int
    priority: int
    fallback_model_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class DefaultModelListResponse(BaseModel):
    """默认模型列表响应"""
    items: List[DefaultModelResponse]
    total: int
    page: int
    size: int
    pages: int

# 设置全局默认模型请求
class SetGlobalDefaultRequest(BaseModel):
    """设置全局默认模型请求"""
    model_id: int = Field(..., description="模型ID")
    fallback_model_id: Optional[int] = Field(None, description="备选模型ID")

# 设置场景默认模型请求
class SetSceneDefaultRequest(BaseModel):
    """设置场景默认模型请求"""
    scene: str = Field(..., description="场景名称")
    model_id: int = Field(..., description="模型ID")
    priority: Optional[int] = Field(1, description="模型优先级，数字越小优先级越高")
    fallback_model_id: Optional[int] = Field(None, description="备选模型ID")

# 获取推荐模型请求
class RecommendModelRequest(BaseModel):
    """获取推荐模型请求"""
    scene: str = Field(..., description="场景名称")
    model_type: Optional[str] = Field(None, description="模型类型，用于过滤")

# 模型推荐响应
class ModelRecommendationResponse(BaseModel):
    """模型推荐响应"""
    primary_model: int = Field(..., description="主推荐模型ID")
    fallback_model: Optional[int] = Field(None, description="备选模型ID")
    alternative_models: List[int] = Field(default_factory=list, description="其他可选模型ID列表")