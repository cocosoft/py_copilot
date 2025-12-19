"""搜索设置数据校验模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SearchSettingBase(BaseModel):
    """搜索设置基础模式"""
    default_search_engine: Optional[str] = Field("google", pattern="^(google|bing|baidu)$", description="默认搜索引擎")
    safe_search: Optional[bool] = Field(True, description="安全搜索开关")


class SearchSettingUpdate(SearchSettingBase):
    """更新搜索设置模式"""
    pass


class SearchSettingResponse(SearchSettingBase):
    """搜索设置响应模式"""
    id: int
    user_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
