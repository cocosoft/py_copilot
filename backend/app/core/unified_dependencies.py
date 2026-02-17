"""统一依赖管理模块 - 整合所有API依赖函数"""
from typing import Generator, Optional
from sqlalchemy.orm import Session
import sqlalchemy
from fastapi import Depends, HTTPException, status, Query, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core.config import settings
from app.models.user import User
from app.schemas.token import TokenPayload


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        import os
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.database_url = f"sqlite:///{os.path.join(BASE_DIR, 'py_copilot.db')}"
        self.connect_args = {"check_same_thread": False}
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """初始化数据库引擎和会话工厂"""
        self.engine = sqlalchemy.create_engine(
            self.database_url,
            connect_args=self.connect_args,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.SessionLocal = sqlalchemy.orm.sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_db(self) -> Generator[Session, None, None]:
        """获取数据库会话"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


class AuthenticationManager:
    """认证管理器"""
    
    def __init__(self):
        self.oauth2_scheme = OAuth2PasswordBearer(
            tokenUrl=f"{settings.api_v1_str}/auth/login"
        )
    
    def get_current_user(
        self,
        db: Session,
        token: Optional[str] = None
    ) -> User:
        """
        获取当前用户
        
        Args:
            db: 数据库会话
            token: 可选的OAuth2令牌
        
        Returns:
            当前用户对象
        
        Raises:
            HTTPException: 认证失败时抛出
        """
        if not settings.enable_auth:
            return self._create_mock_user()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证令牌缺失"
            )
        
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            token_data = TokenPayload(**payload)
        except (JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无法验证凭据",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = db.query(User).filter(User.id == token_data.sub).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return user
    
    def _create_mock_user(self) -> User:
        """创建模拟用户对象"""
        mock_user = User(
            id=1,
            username="admin",
            email="admin@example.com",
            hashed_password="",
            full_name="管理员",
            is_active=True,
            is_superuser=True,
            is_verified=True
        )
        mock_user.__dict__.update({
            'id': 1,
            'username': 'admin',
            'email': 'admin@example.com',
            'is_active': True,
            'is_superuser': True,
            'is_verified': True
        })
        return mock_user
    
    def get_current_active_user(self, current_user: User) -> User:
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
    
    def get_current_active_superuser(self, current_user: User) -> User:
        """
        获取当前活跃的超级用户
        
        Args:
            current_user: 当前用户
        
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


class ExternalAPIAuthManager:
    """外部API认证管理器"""
    
    def verify_api_key(
        self,
        api_key: Optional[str] = None,
        x_api_key: Optional[str] = None
    ) -> bool:
        """
        验证外部API密钥
        
        Args:
            api_key: 查询参数中的API密钥
            x_api_key: 请求头中的API密钥
        
        Returns:
            验证成功返回True
        
        Raises:
            HTTPException: 验证失败时抛出
        """
        if not settings.enable_external_api:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="外部API未启用"
            )
        
        key_to_check = x_api_key if x_api_key else api_key
        
        if not key_to_check:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API密钥缺失"
            )
        
        if key_to_check != settings.external_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的API密钥"
            )
        
        return True


class ServiceDependencyManager:
    """服务依赖管理器"""
    
    @staticmethod
    def get_skill_service(db: Session):
        """获取技能服务实例"""
        from app.services.skill_service import SkillService
        return SkillService(db)
    
    @staticmethod
    def get_session_service(db: Session):
        """获取技能会话服务实例"""
        from app.services.skill_service import SkillSessionService
        return SkillSessionService(db)
    
    @staticmethod
    def get_execution_service(db: Session):
        """获取技能执行服务实例"""
        from app.services.skill_service import SkillExecutionService
        return SkillExecutionService(db)
    
    @staticmethod
    def get_repository_service(db: Session):
        """获取技能仓库服务实例"""
        from app.services.skill_service import SkillRepositoryService
        return SkillRepositoryService(db)
    
    @staticmethod
    def get_skill_execution_engine(db: Session):
        """获取技能执行引擎实例"""
        from app.services.skill_execution_engine import SkillExecutionEngine
        return SkillExecutionEngine(db)


class DependencyManager:
    """统一的依赖管理器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthenticationManager()
        self.external_auth_manager = ExternalAPIAuthManager()
        self.service_manager = ServiceDependencyManager()


# 全局依赖管理器实例
dependency_manager = DependencyManager()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话的依赖"""
    return dependency_manager.db_manager.get_db()


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = None
) -> User:
    """获取当前用户的依赖"""
    return dependency_manager.auth_manager.get_current_user(db, token)


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户的依赖"""
    return dependency_manager.auth_manager.get_current_active_user(current_user)


def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前活跃超级用户的依赖"""
    return dependency_manager.auth_manager.get_current_active_superuser(current_user)


def verify_external_api_key(
    api_key: Optional[str] = None,
    x_api_key: Optional[str] = None
) -> bool:
    """验证外部API密钥"""
    return dependency_manager.external_auth_manager.verify_api_key(api_key, x_api_key)


def get_external_api_auth(
    api_key: Optional[str] = Query(None, description="API密钥"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key", description="请求头中的API密钥")
) -> bool:
    """获取外部API认证依赖"""
    return verify_external_api_key(api_key=api_key, x_api_key=x_api_key)


def get_skill_service(db: Session = Depends(get_db)):
    """获取技能服务实例的依赖"""
    return dependency_manager.service_manager.get_skill_service(db)


def get_session_service(db: Session = Depends(get_db)):
    """获取技能会话服务实例的依赖"""
    return dependency_manager.service_manager.get_session_service(db)


def get_execution_service(db: Session = Depends(get_db)):
    """获取技能执行服务实例的依赖"""
    return dependency_manager.service_manager.get_execution_service(db)


def get_repository_service(db: Session = Depends(get_db)):
    """获取技能仓库服务实例的依赖"""
    return dependency_manager.service_manager.get_repository_service(db)


def get_skill_execution_engine(db: Session = Depends(get_db)):
    """获取技能执行引擎实例的依赖"""
    return dependency_manager.service_manager.get_skill_execution_engine(db)


# 导出数据库引擎（用于其他模块）
engine = dependency_manager.db_manager.engine
