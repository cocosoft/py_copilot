"""核心依赖函数模块"""
from typing import Generator, Optional
from sqlalchemy.orm import Session
import sqlalchemy
from fastapi import Depends

# 数据库配置
import os
# 使用与初始化脚本一致的数据库文件路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'py_copilot.db')}"
DATABASE_CONNECT_ARGS = {"check_same_thread": False}

# 创建数据库引擎
engine = sqlalchemy.create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=DATABASE_CONNECT_ARGS
)
SessionLocal = sqlalchemy.orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """获取数据库会话的依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 从api.deps导入实际的认证依赖
from app.api.deps import get_current_user as get_current_user_real

# 为了向后兼容，保留这个名称，但使用实际的实现
get_current_user = get_current_user_real

# 导入服务类
from app.services.skill_service import (
    SkillService, 
    SkillSessionService, 
    SkillExecutionService, 
    SkillRepositoryService
)

# 服务依赖
def get_skill_service(db: Session = Depends(get_db)) -> SkillService:
    """获取技能服务实例的依赖"""
    return SkillService(db)

def get_session_service(db: Session = Depends(get_db)) -> SkillSessionService:
    """获取技能会话服务实例的依赖"""
    return SkillSessionService(db)

def get_execution_service(db: Session = Depends(get_db)) -> SkillExecutionService:
    """获取技能执行服务实例的依赖"""
    return SkillExecutionService(db)

def get_repository_service(db: Session = Depends(get_db)) -> SkillRepositoryService:
    """获取技能仓库服务实例的依赖"""
    return SkillRepositoryService(db)

# 保留原始的JWT验证相关代码注释
# 注意：以下代码已被注释，如需使用请取消注释
# from jose import JWTError, jwt
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from app.core.config import settings
# from app.models.user import User
# 
# # OAuth2 scheme for token authentication
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
# 
# async def get_current_user_jwt(
#     db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
# ) -> User:
#     """获取当前用户的依赖(使用JWT)"""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(
#             token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
#         )
#         user_id: str = payload.get("sub")
#         if user_id is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     user = db.query(User).filter(User.id == int(user_id)).first()
#     if user is None:
#         raise credentials_exception
#     return user
# 
# async def get_current_active_user(
#     current_user: User = Depends(get_current_user_jwt),
# ) -> User:
#     """获取当前活跃用户的依赖"""
#     if not current_user.is_active:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return user

# 模拟用户模型 - 保留以兼容现有代码
class MockUser:
    def __init__(self, id: str, username: str, email: str, is_active: bool = True):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = is_active