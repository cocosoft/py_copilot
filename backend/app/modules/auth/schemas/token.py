"""令牌相关的数据校验模型"""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """令牌负载模型"""
    sub: Optional[int] = None
    exp: Optional[int] = None