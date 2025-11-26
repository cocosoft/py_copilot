"""核心依赖函数模块"""
from typing import Generator, Optional
from sqlalchemy.orm import Session
import sqlalchemy

# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./py_copilot.db"
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

def get_current_user():
    """获取当前用户的依赖 - 简化版本"""
    return {"id": 1, "username": "admin"}  # 临时实现，生产环境应该使用JWT验证

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