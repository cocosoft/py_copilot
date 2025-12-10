"""智能体分类数据验证模式"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AgentCategoryBase(BaseModel):
    """智能体分类基础信息"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    logo: Optional[str] = Field(None, description="分类logo")
    is_system: Optional[bool] = Field(False, description="是否系统分类")


class AgentCategoryCreate(AgentCategoryBase):
    """创建智能体分类请求"""
    pass


class AgentCategoryUpdate(AgentCategoryBase):
    """更新智能体分类请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="分类名称")


class AgentCategoryResponse(AgentCategoryBase):
    """智能体分类响应"""
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class AgentCategoryListResponse(BaseModel):
    """智能体分类列表响应"""
    categories: list[AgentCategoryResponse]
    total: int