from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class SettingBase(BaseModel):
    """设置基础模型"""
    setting_type: str
    setting_data: Dict[str, Any]


class SettingCreate(SettingBase):
    """创建设置模型"""
    pass


class SettingUpdate(BaseModel):
    """更新设置模型"""
    setting_data: Dict[str, Any]


class SettingResponse(SettingBase):
    """设置响应模型"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SettingsResponse(BaseModel):
    """设置列表响应模型"""
    general: Optional[Dict[str, Any]] = None
    personalization: Optional[Dict[str, Any]] = None
    emotion: Optional[Dict[str, Any]] = None
    learning: Optional[Dict[str, Any]] = None
    relationship: Optional[Dict[str, Any]] = None