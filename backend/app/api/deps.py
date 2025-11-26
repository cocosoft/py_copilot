"""API依赖函数模块"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.token import TokenPayload

# OAuth2 密码承载令牌
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_str}/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前用户
    
    Args:
        db: 数据库会话
        token: OAuth2令牌
    
    Returns:
        当前用户对象
    
    Raises:
        HTTPException: 认证失败时抛出
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        当前活跃用户对象
    
    Raises:
        HTTPException: 用户未激活时抛出
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    获取当前活跃的超级用户
    
    Args:
        current_user: 当前活跃用户
    
    Returns:
        当前活跃的超级用户对象
    
    Raises:
        HTTPException: 用户不是超级用户时抛出
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="需要超级用户权限"
        )
    return current_user