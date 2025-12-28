"""认证相关的Schema定义"""
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """令牌载荷模型"""
    sub: Optional[int] = None


class UserLogin(BaseModel):
    """用户登录请求模型"""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应模型"""
    token: Token
    user: UserResponse


class ChangePassword(BaseModel):
    """修改密码请求模型"""
    old_password: str
    new_password: str = Field(..., min_length=6)


class UpdateUser(BaseModel):
    """更新用户信息请求模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None