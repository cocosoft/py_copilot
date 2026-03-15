"""用户相关的Schema"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6)


class UserInDBBase(UserBase):
    """数据库中的用户基础模型"""
    id: int
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    current_workspace_id: Optional[int]

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """用户响应模型"""
    pass


class UserInDB(UserInDBBase):
    """数据库中的用户模型"""
    hashed_password: str
