"""认证相关API路由"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import config, security
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas import auth as auth_schemas

router = APIRouter()


@router.post("/register", response_model=auth_schemas.UserResponse)
async def register(
    user_in: auth_schemas.UserRegister,
    db: Session = Depends(get_db)
) -> Any:
    """
    用户注册接口
    
    Args:
        user_in: 用户注册信息
        db: 数据库会话
    
    Returns:
        注册成功的用户信息
    """
    # 检查邮箱是否已存在
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被使用"
        )
    
    # 创建新用户
    hashed_password = security.get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=auth_schemas.LoginResponse)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    用户登录接口（使用OAuth2标准格式）
    
    Args:
        db: 数据库会话
        form_data: OAuth2密码请求表单
    
    Returns:
        登录令牌和用户信息
    """
    # OAuth2表单使用username字段，但我们使用email登录
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # 构建响应
    token_data = auth_schemas.Token(
        access_token=access_token,
        expires_in=access_token_expires.seconds
    )
    
    return auth_schemas.LoginResponse(
        token=token_data,
        user=user
    )


@router.post("/login/json", response_model=auth_schemas.LoginResponse)
async def login_json(
    user_in: auth_schemas.UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    用户登录接口（JSON格式）
    
    Args:
        user_in: 用户登录信息
        db: 数据库会话
    
    Returns:
        登录令牌和用户信息
    """
    # 查找用户
    user = db.query(User).filter(User.email == user_in.email).first()
    
    if not user or not security.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # 构建响应
    token_data = auth_schemas.Token(
        access_token=access_token,
        expires_in=access_token_expires.seconds
    )
    
    return auth_schemas.LoginResponse(
        token=token_data,
        user=user
    )


@router.get("/me", response_model=auth_schemas.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取当前登录用户信息
    
    Args:
        current_user: 当前活跃用户
    
    Returns:
        用户信息
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: auth_schemas.ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    修改用户密码
    
    Args:
        password_data: 密码修改信息
        current_user: 当前活跃用户
        db: 数据库会话
    
    Returns:
        操作结果
    """
    # 验证旧密码
    if not security.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 更新密码
    current_user.hashed_password = security.get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "密码修改成功"}


@router.put("/me", response_model=auth_schemas.UserResponse)
async def update_user_info(
    user_update: auth_schemas.UpdateUser,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新用户信息
    
    Args:
        user_update: 用户更新信息
        current_user: 当前活跃用户
        db: 数据库会话
    
    Returns:
        更新后的用户信息
    """
    # 检查邮箱是否被其他用户使用
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被其他用户使用"
            )
    
    # 检查用户名是否被其他用户使用
    if user_update.username and user_update.username != current_user.username:
        existing_user = db.query(User).filter(User.username == user_update.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户名已被其他用户使用"
            )
    
    # 更新用户信息
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user