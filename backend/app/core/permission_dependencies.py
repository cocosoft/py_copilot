"""权限控制依赖函数模块"""
from typing import Any, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


def get_current_active_user(
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> User:
    """
    获取当前活跃用户
    
    Args:
        db: 数据库会话
        token: OAuth2令牌（可选）
    
    Returns:
        当前活跃用户对象
    
    Raises:
        HTTPException: 用户未激活时抛出
    """
    # 导入在这里避免循环导入
    from app.api.deps import get_current_user as get_current_user_func
    
    current_user = get_current_user_func(db, token)
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    return current_user


def get_current_active_superuser(
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> User:
    """
    获取当前活跃的超级用户
    
    Args:
        db: 数据库会话
        token: OAuth2令牌（可选）
    
    Returns:
        当前活跃的超级用户对象
    
    Raises:
        HTTPException: 用户不是超级用户时抛出
    """
    # 导入在这里避免循环导入
    from app.api.deps import get_current_user as get_current_user_func
    
    current_user = get_current_user_func(db, token)
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级用户权限"
        )
    return current_user


def get_current_verified_user(
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> User:
    """
    获取当前验证过的用户
    
    Args:
        db: 数据库会话
        token: OAuth2令牌（可选）
    
    Returns:
        当前验证过的用户对象
    
    Raises:
        HTTPException: 用户未验证时抛出
    """
    # 导入在这里避免循环导入
    from app.api.deps import get_current_user as get_current_user_func
    
    current_user = get_current_user_func(db, token)
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户邮箱未验证"
        )
    return current_user


def require_permissions(*required_permissions: str):
    """
    要求特定权限的装饰器
    
    Args:
        required_permissions: 所需权限列表
    
    Returns:
        依赖函数
    """
    def permission_checker(
        db: Session = Depends(get_db),
        token: Optional[str] = None
    ) -> User:
        # 导入在这里避免循环导入
        from app.api.deps import get_current_user as get_current_user_func
        
        current_user = get_current_user_func(db, token)
        
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用"
            )
        
        # 检查用户权限（这里可以根据实际需求扩展权限检查逻辑）
        # 目前简化处理：如果用户是超级用户，则具有所有权限
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return current_user
    
    return permission_checker


def require_superuser_permission(
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> User:
    """
    要求超级用户权限
    
    Args:
        db: 数据库会话
        token: OAuth2令牌（可选）
    
    Returns:
        当前超级用户对象
    
    Raises:
        HTTPException: 用户不是超级用户时抛出
    """
    return get_current_active_superuser(db, token)


def require_verified_user(
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> User:
    """
    要求验证过的用户
    
    Args:
        db: 数据库会话
        token: OAuth2令牌（可选）
    
    Returns:
        当前验证过的用户对象
    
    Raises:
        HTTPException: 用户未验证时抛出
    """
    return get_current_verified_user(db, token)