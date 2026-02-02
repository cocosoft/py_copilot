"""数据库连接配置"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator, Optional, List

from app.core.config import settings
from app.core.logging_config import logger


class DatabaseConnectionPool:
    """数据库连接池管理器"""
    
    def __init__(self, database_url: str, pool_type: str = "master"):
        """
        初始化数据库连接池
        
        Args:
            database_url: 数据库连接URL
            pool_type: 连接池类型，master（主库，支持读写）或 slave（从库，仅支持读）
        """
        self.database_url = database_url
        self.pool_type = pool_type
        self.engine = None
        self.session_factory = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """初始化数据库连接池"""
        try:
            # SQLite需要特殊的连接参数
            connect_args = {}
            poolclass = None
            
            if "sqlite" in self.database_url:
                connect_args = {"check_same_thread": False}
                # SQLite使用NullPool，因为SQLite不支持真正的连接池
                from sqlalchemy.pool import NullPool
                poolclass = NullPool
                logger.info(f"使用SQLite数据库，配置NullPool连接池 ({self.pool_type})")
            else:
                # 其他数据库使用QueuePool
                poolclass = QueuePool
                logger.info(f"使用QueuePool连接池 ({self.pool_type})")
            
            # 创建数据库引擎，配置连接池参数
            engine_kwargs = {
                "url": self.database_url,
                "connect_args": connect_args,
                "poolclass": poolclass,
                "echo": False  # 不输出SQL日志
            }
            
            # 只有当不是使用NullPool时，才添加连接池参数
            if poolclass != NullPool:
                pool_size = 10
                max_overflow = 20
                
                # 从库可以配置更大的连接池，因为只读操作通常更轻量
                if self.pool_type == "slave":
                    pool_size = 15
                    max_overflow = 30
                
                engine_kwargs.update({
                    "pool_pre_ping": True,  # 连接前检查连接是否有效
                    "pool_size": pool_size,  # 连接池大小
                    "max_overflow": max_overflow,  # 最大溢出连接数
                    "pool_recycle": 3600,  # 连接回收时间（秒），1小时
                    "pool_timeout": 30,  # 获取连接超时时间（秒）
                })
            else:
                # NullPool不需要连接池参数，但仍然需要pool_pre_ping
                engine_kwargs["pool_pre_ping"] = True
            
            self.engine = create_engine(**engine_kwargs)
            
            # 创建会话工厂
            self.session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"数据库连接池初始化成功 - URL: {self.database_url} ({self.pool_type})")
            
        except Exception as e:
            logger.error(f"数据库连接池初始化失败 ({self.pool_type}): {str(e)}")
            raise
    
    def get_session(self) -> sessionmaker:
        """获取会话工厂"""
        return self.session_factory
    
    @contextmanager
    def get_db_session(self):
        """
        获取数据库会话的上下文管理器
        
        Yields:
            数据库会话
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_pool_status(self) -> dict:
        """
        获取连接池状态信息
        
        Returns:
            连接池状态字典
        """
        pool = self.engine.pool
        status = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": pool.max_overflow,
            "timeout": pool.timeout
        }
        return status
    
    def close_pool(self):
        """
        关闭连接池
        """
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("数据库连接池已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接池失败: {str(e)}")


class DatabaseRouter:
    """数据库路由器 - 实现读写分离"""
    
    def __init__(self, master_url: str, slave_urls: Optional[List[str]] = None):
        """
        初始化数据库路由器
        
        Args:
            master_url: 主库连接URL
            slave_urls: 从库连接URL列表
        """
        self.master_url = master_url
        self.slave_urls = slave_urls or []
        self.master_pool = DatabaseConnectionPool(master_url, "master")
        self.slave_pools = []
        
        # 初始化从库连接池
        for i, slave_url in enumerate(self.slave_urls):
            try:
                slave_pool = DatabaseConnectionPool(slave_url, "slave")
                self.slave_pools.append(slave_pool)
                logger.info(f"从库连接池 {i+1} 初始化成功")
            except Exception as e:
                logger.error(f"从库连接池 {i+1} 初始化失败: {str(e)}")
        
        self.slave_index = 0
        logger.info(f"数据库路由器初始化完成 - 主库: 1, 从库: {len(self.slave_pools)}")
    
    def get_master_pool(self) -> DatabaseConnectionPool:
        """
        获取主库连接池
        
        Returns:
            主库连接池
        """
        return self.master_pool
    
    def get_slave_pool(self) -> Optional[DatabaseConnectionPool]:
        """
        获取从库连接池（轮询选择）
        
        Returns:
            从库连接池，如果没有从库则返回None
        """
        if not self.slave_pools:
            return None
        
        # 轮询选择从库
        slave_pool = self.slave_pools[self.slave_index]
        self.slave_index = (self.slave_index + 1) % len(self.slave_pools)
        return slave_pool
    
    def get_pool_for_operation(self, operation: str) -> DatabaseConnectionPool:
        """
        根据操作类型选择连接池
        
        Args:
            operation: 操作类型，read或write
            
        Returns:
            适合该操作的连接池
        """
        if operation == "write":
            return self.master_pool
        else:
            # 读操作优先使用从库
            slave_pool = self.get_slave_pool()
            if slave_pool:
                return slave_pool
            else:
                # 没有从库时使用主库
                return self.master_pool
    
    @contextmanager
    def get_session(self, operation: str = "read"):
        """
        获取数据库会话的上下文管理器
        
        Args:
            operation: 操作类型，read或write
            
        Yields:
            数据库会话
        """
        pool = self.get_pool_for_operation(operation)
        session = pool.session_factory()
        
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败 ({operation}): {str(e)}")
            raise
        finally:
            session.close()
    
    def close_all_pools(self):
        """
        关闭所有连接池
        """
        try:
            self.master_pool.close_pool()
            for slave_pool in self.slave_pools:
                slave_pool.close_pool()
            logger.info("所有数据库连接池已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接池失败: {str(e)}")
    
    def get_router_status(self) -> dict:
        """
        获取路由器状态
        
        Returns:
            路由器状态字典
        """
        status = {
            "master_pool": self.master_pool.get_pool_status(),
            "slave_pools_count": len(self.slave_pools),
            "slave_pools_status": []
        }
        
        for i, slave_pool in enumerate(self.slave_pools):
            status["slave_pools_status"].append({
                "index": i+1,
                "status": slave_pool.get_pool_status()
            })
        
        return status


# 创建全局数据库连接池实例
_db_pool: DatabaseConnectionPool = None
_db_router: Optional[DatabaseRouter] = None


def get_db_pool() -> DatabaseConnectionPool:
    """获取数据库连接池实例"""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabaseConnectionPool(settings.database_url, "master")
    return _db_pool


def get_db_router() -> DatabaseRouter:
    """获取数据库路由器实例"""
    global _db_router
    if _db_router is None:
        # 从配置中获取从库URL列表
        # 注意：当前使用SQLite，不支持真正的主从复制
        # 这里创建一个路由器，后续可以通过配置添加从库
        slave_urls = []
        _db_router = DatabaseRouter(settings.database_url, slave_urls)
    return _db_router


# 初始化连接池
engine = None
SessionLocal = None


try:
    db_pool = get_db_pool()
    engine = db_pool.engine
    SessionLocal = db_pool.session_factory
except Exception as e:
    logger.error(f"初始化数据库连接失败: {str(e)}")
    raise


# 创建基类
Base = declarative_base()


def get_db() -> Generator:
    """
    获取数据库会话的依赖函数（用于FastAPI依赖注入）
    
    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_for_write() -> Generator:
    """
    获取写操作的数据库会话
    
    Yields:
        数据库会话
    """
    router = get_db_router()
    with router.get_session("write") as session:
        yield session


def get_db_for_read() -> Generator:
    """
    获取读操作的数据库会话
    
    Yields:
        数据库会话
    """
    router = get_db_router()
    with router.get_session("read") as session:
        yield session


def get_pool_status() -> dict:
    """
    获取连接池状态
    
    Returns:
        连接池状态字典
    """
    return get_db_pool().get_pool_status()


def get_router_status() -> dict:
    """
    获取数据库路由器状态
    
    Returns:
        路由器状态字典
    """
    return get_db_router().get_router_status()