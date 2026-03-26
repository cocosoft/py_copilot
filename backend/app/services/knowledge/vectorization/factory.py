"""
向量存储工厂

提供统一的接口创建向量存储实例
支持多种后端：SQLite、ChromaDB
"""

import logging
from typing import Optional

from .base import VectorStoreBase
from .sqlite_store import SQLiteVectorStore

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """
    向量存储工厂类
    
    使用工厂模式创建向量存储实例，支持多种后端
    
    使用示例：
        # 获取默认存储实例
        store = VectorStoreFactory.get_store()
        
        # 获取指定后端
        sqlite_store = VectorStoreFactory.get_store("sqlite")
        chroma_store = VectorStoreFactory.get_store("chromadb")
    """
    
    _instances = {}
    _default_backend = None  # 将从配置中读取
    
    @classmethod
    def _get_default_backend(cls) -> str:
        """从配置获取默认后端"""
        if cls._default_backend is None:
            try:
                from app.core.config import settings
                cls._default_backend = settings.vector_store_backend
            except Exception as e:
                logger.warning(f"读取向量存储配置失败: {e}，使用默认值 sqlite")
                cls._default_backend = "sqlite"
        return cls._default_backend
    
    @classmethod
    def get_store(cls, backend: Optional[str] = None) -> VectorStoreBase:
        """
        获取向量存储实例
        
        Args:
            backend: 存储后端类型，可选 "sqlite" 或 "chromadb"
                    如果为 None，使用默认后端
                    
        Returns:
            向量存储实例
            
        Raises:
            ValueError: 如果后端类型不支持
        """
        if backend is None:
            backend = cls._get_default_backend()
        
        # 检查是否已有实例
        if backend not in cls._instances:
            logger.info(f"创建 {backend} 向量存储实例")
            
            if backend == "sqlite":
                # 从配置读取数据库路径
                try:
                    from app.core.config import settings
                    db_path = settings.vector_store_db_path
                    cls._instances[backend] = SQLiteVectorStore(db_path=db_path)
                except Exception as e:
                    logger.warning(f"读取 SQLite 配置失败: {e}，使用默认路径")
                    cls._instances[backend] = SQLiteVectorStore()
            elif backend == "chromadb":
                # 延迟导入，避免循环依赖
                try:
                    from .chromadb_store import ChromaDBVectorStore
                    from app.core.config import settings
                    cls._instances[backend] = ChromaDBVectorStore(
                        server_url=settings.chromadb_server_url,
                        default_collection=settings.chromadb_collection
                    )
                except ImportError:
                    logger.warning("ChromaDBVectorStore 未实现，使用 SQLite 替代")
                    cls._instances[backend] = SQLiteVectorStore()
            else:
                raise ValueError(f"不支持的向量存储后端: {backend}，可选: sqlite, chromadb")
        
        return cls._instances[backend]
    
    @classmethod
    def set_default_backend(cls, backend: str):
        """
        设置默认存储后端
        
        Args:
            backend: 后端类型，"sqlite" 或 "chromadb"
        """
        if backend not in ["sqlite", "chromadb"]:
            raise ValueError(f"不支持的向量存储后端: {backend}")
        
        cls._default_backend = backend
        logger.info(f"默认向量存储后端设置为: {backend}")
    
    @classmethod
    def get_default_backend(cls) -> str:
        """
        获取默认存储后端
        
        Returns:
            默认后端类型
        """
        return cls._default_backend
    
    @classmethod
    def reset_instance(cls, backend: Optional[str] = None):
        """
        重置存储实例
        
        用于重新创建存储实例，例如在配置更改后
        
        Args:
            backend: 要重置的后端，如果为 None 则重置所有
        """
        if backend is None:
            # 关闭所有实例
            for store in cls._instances.values():
                try:
                    store.close()
                except Exception as e:
                    logger.warning(f"关闭存储实例时出错: {e}")
            
            cls._instances.clear()
            logger.info("所有向量存储实例已重置")
        else:
            if backend in cls._instances:
                try:
                    cls._instances[backend].close()
                except Exception as e:
                    logger.warning(f"关闭存储实例时出错: {e}")
                
                del cls._instances[backend]
                logger.info(f"{backend} 向量存储实例已重置")
    
    @classmethod
    def health_check(cls, backend: Optional[str] = None) -> dict:
        """
        健康检查
        
        Args:
            backend: 要检查的后端，如果为 None 则检查所有
            
        Returns:
            健康状态信息
        """
        results = {}
        
        if backend:
            backends = [backend]
        else:
            backends = ["sqlite", "chromadb"]
        
        for b in backends:
            try:
                store = cls.get_store(b)
                results[b] = store.health_check()
            except Exception as e:
                results[b] = {
                    "healthy": False,
                    "message": f"健康检查失败: {str(e)}"
                }
        
        return results
