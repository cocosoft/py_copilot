"""安全认证相关功能模块"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌

    Args:
        subject: 令牌主体，通常是用户ID
        expires_delta: 过期时间增量

    Returns:
        编码后的JWT令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希值

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT令牌

    Args:
        token: JWT令牌

    Returns:
        解码后的令牌数据，如果令牌无效则返回None
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    从令牌中获取用户ID

    Args:
        token: JWT令牌

    Returns:
        用户ID，如果令牌无效则返回None
    """
    payload = decode_token(token)
    if payload:
        try:
            return int(payload.get("sub"))
        except (ValueError, TypeError):
            return None
    return None