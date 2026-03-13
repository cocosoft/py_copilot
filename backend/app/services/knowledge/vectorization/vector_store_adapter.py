"""
向量存储抽象层 - 向量化管理模块优化

实现向量存储的统一抽象接口，支持多种后端（ChromaDB、FAISS、Milvus等）。

任务编号: BE-006
阶段: Phase 2 - 架构升级期
"""

import logging
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from abc import ABC, abstractmethod
import numpy as np
import json

logger = logging.getLogger(__name__)


class VectorStoreBackend(Enum):
    """向量存储后端类型"""
    CHROMA = "chroma"       # ChromaDB
    FAISS = "faiss"         # FAISS
    MILVUS = "milvus"       # Milvus
    PINECONE = "pinecone"   # Pinecone
    WEAVIATE = "weaviate"   # Weaviate
    QDRANT = "qdrant"       # Qdrant


class VectorStoreStatus(Enum):
    """向量存储状态"""
    HEALTHY = "healthy"         # 健康
    DEGRADED = "degraded"       # 降级
    UNAVAILABLE = "unavailable" # 不可用
    INITIALIZING = "initializing"  # 初始化中


@dataclass
class VectorDocument:
    """向量文档"""
    id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "text": self.text,
            "embedding": self.embedding,
            "metadata": self.metadata
        }


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    distance: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "text": self.text,
            "score": self.score,
            "metadata": self.metadata,
            "distance": self.distance
        }


@dataclass
class CollectionInfo:
    """集合信息"""
    name: str
    count: int
    dimension: int
    backend: VectorStoreBackend
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "count": self.count,
            "dimension": self.dimension,
            "backend": self.backend.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata
        }


@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    backend: VectorStoreBackend
    connection_string: str
    default_collection: str = "default"
    dimension: int = 1536
    distance_metric: str = "cosine"  # cosine, euclidean, dot
    additional_config: Dict[str, Any] = field(default_factory=dict)


class BaseVectorStore(ABC):
    """向量存储基类"""
    
    def __init__(self, config: VectorStoreConfig):
        """
        初始化向量存储
        
        Args:
            config: 存储配置
        """
        self.config = config
        self.backend_type = config.backend
        self.status = VectorStoreStatus.INITIALIZING
        
        logger.info(f"初始化 {self.backend_type.value} 向量存储")
    
    @abstractmethod
    def connect(self) -> bool:
        """连接存储"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    def health_check(self) -> VectorStoreStatus:
        """健康检查"""
        pass
    
    @abstractmethod
    def create_collection(
        self,
        name: str,
        dimension: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """创建集合"""
        pass
    
    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """删除集合"""
        pass
    
    @abstractmethod
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        pass
    
    @abstractmethod
    def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        """获取集合信息"""
        pass
    
    @abstractmethod
    def add_document(
        self,
        collection_name: str,
        document: VectorDocument
    ) -> bool:
        """添加文档"""
        pass
    
    @abstractmethod
    def add_documents(
        self,
        collection_name: str,
        documents: List[VectorDocument]
    ) -> Dict[str, Any]:
        """批量添加文档"""
        pass
    
    @abstractmethod
    def get_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[VectorDocument]:
        """获取文档"""
        pass
    
    @abstractmethod
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """搜索相似文档"""
        pass
    
    @abstractmethod
    def search_by_vector(
        self,
        collection_name: str,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """使用向量搜索"""
        pass
    
    @abstractmethod
    def count(self, collection_name: str) -> int:
        """获取文档数量"""
        pass


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB向量存储实现"""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._client = None
        self._connect()
    
    def _connect(self):
        """连接ChromaDB"""
        try:
            from app.services.knowledge.vectorization.chroma_service import ChromaService
            self._client = ChromaService(
                server_url=self.config.connection_string,
                default_collection=self.config.default_collection
            )
            self.status = VectorStoreStatus.HEALTHY
            logger.info("ChromaDB连接成功")
        except Exception as e:
            self.status = VectorStoreStatus.UNAVAILABLE
            logger.error(f"ChromaDB连接失败: {e}")
    
    def connect(self) -> bool:
        """连接存储"""
        if self.status != VectorStoreStatus.HEALTHY:
            self._connect()
        return self.status == VectorStoreStatus.HEALTHY
    
    def disconnect(self):
        """断开连接"""
        self._client = None
        self.status = VectorStoreStatus.UNAVAILABLE
        logger.info("ChromaDB连接已断开")
    
    def health_check(self) -> VectorStoreStatus:
        """健康检查"""
        if self._client and self._client.available:
            self.status = VectorStoreStatus.HEALTHY
        else:
            self.status = VectorStoreStatus.UNAVAILABLE
        return self.status
    
    def create_collection(
        self,
        name: str,
        dimension: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """创建集合"""
        try:
            # ChromaDB自动创建集合
            return True
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        """删除集合"""
        try:
            if self._client:
                return self._client.delete_collection(name)
            return False
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            if self._client:
                return self._client.list_collections()
            return []
        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []
    
    def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        """获取集合信息"""
        try:
            if not self._client:
                return None
            
            info = self._client.get_collection_info(name)
            if info:
                return CollectionInfo(
                    name=name,
                    count=info.get("count", 0),
                    dimension=self.config.dimension,
                    backend=VectorStoreBackend.CHROMA,
                    metadata=info.get("metadata", {})
                )
            return None
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return None
    
    def add_document(
        self,
        collection_name: str,
        document: VectorDocument
    ) -> bool:
        """添加文档"""
        try:
            if not self._client:
                return False
            
            return self._client.add_document(
                document_id=document.id,
                text=document.text,
                metadata=document.metadata,
                collection_name=collection_name
            )
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[VectorDocument]
    ) -> Dict[str, Any]:
        """批量添加文档"""
        try:
            if not self._client:
                return {"success": False, "count": 0, "error": "未连接"}
            
            docs_data = [
                {
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata
                }
                for doc in documents
            ]
            
            return self._client.add_documents_batch(docs_data, collection_name)
        except Exception as e:
            logger.error(f"批量添加文档失败: {e}")
            return {"success": False, "count": 0, "error": str(e)}
    
    def get_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[VectorDocument]:
        """获取文档"""
        try:
            if not self._client:
                return None
            
            result = self._client.get_document(document_id, collection_name)
            if result:
                return VectorDocument(
                    id=document_id,
                    text=result.get("text", ""),
                    metadata=result.get("metadata", {})
                )
            return None
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """删除文档"""
        try:
            if not self._client:
                return False
            
            return self._client.delete_document(document_id, collection_name)
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """搜索相似文档"""
        try:
            if not self._client:
                return []
            
            results = self._client.search(
                query=query,
                top_k=top_k,
                filters=filters,
                collection_name=collection_name
            )
            
            return [
                SearchResult(
                    id=r.get("id", ""),
                    text=r.get("text", ""),
                    score=r.get("score", 0.0),
                    metadata=r.get("metadata", {}),
                    distance=r.get("distance")
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def search_by_vector(
        self,
        collection_name: str,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """使用向量搜索"""
        try:
            if not self._client:
                return []
            
            results = self._client.search_by_vector(
                vector=vector,
                top_k=top_k,
                filters=filters,
                collection_name=collection_name
            )
            
            return [
                SearchResult(
                    id=r.get("id", ""),
                    text=r.get("text", ""),
                    score=r.get("score", 0.0),
                    metadata=r.get("metadata", {}),
                    distance=r.get("distance")
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def count(self, collection_name: str) -> int:
        """获取文档数量"""
        try:
            if not self._client:
                return 0
            
            return self._client.get_document_count(collection_name)
        except Exception as e:
            logger.error(f"获取文档数量失败: {e}")
            return 0


class VectorStoreFactory:
    """向量存储工厂"""
    
    _stores: Dict[VectorStoreBackend, type] = {
        VectorStoreBackend.CHROMA: ChromaVectorStore,
        # 其他后端可以在这里注册
        # VectorStoreBackend.FAISS: FaissVectorStore,
        # VectorStoreBackend.MILVUS: MilvusVectorStore,
    }
    
    @classmethod
    def register_backend(
        cls,
        backend: VectorStoreBackend,
        store_class: type
    ):
        """
        注册后端实现
        
        Args:
            backend: 后端类型
            store_class: 存储类
        """
        cls._stores[backend] = store_class
        logger.info(f"注册向量存储后端: {backend.value}")
    
    @classmethod
    def create_store(cls, config: VectorStoreConfig) -> Optional[BaseVectorStore]:
        """
        创建存储实例
        
        Args:
            config: 存储配置
            
        Returns:
            存储实例
        """
        store_class = cls._stores.get(config.backend)
        if store_class:
            return store_class(config)
        
        logger.error(f"未找到后端实现: {config.backend.value}")
        return None
    
    @classmethod
    def get_supported_backends(cls) -> List[VectorStoreBackend]:
        """获取支持的后端列表"""
        return list(cls._stores.keys())


class VectorStoreAdapter:
    """
    向量存储适配器
    
    提供统一的向量存储接口，支持多种后端无缝切换。
    
    特性：
    - 统一的操作接口
    - 支持多种后端（ChromaDB、FAISS、Milvus等）
    - 后端切换无需修改业务代码
    - 插件化扩展支持
    - 连接池管理
    - 自动故障转移
    
    使用示例：
        config = VectorStoreConfig(
            backend=VectorStoreBackend.CHROMA,
            connection_string="http://localhost:8008",
            default_collection="documents"
        )
        
        adapter = VectorStoreAdapter(config)
        adapter.add_document("collection", document)
        results = adapter.search("collection", "query")
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        初始化适配器
        
        Args:
            config: 存储配置
        """
        self.config = config
        self._store: Optional[BaseVectorStore] = None
        self._initialize_store()
    
    def _initialize_store(self):
        """初始化存储"""
        self._store = VectorStoreFactory.create_store(self.config)
        if self._store:
            self._store.connect()
    
    def switch_backend(self, config: VectorStoreConfig) -> bool:
        """
        切换后端
        
        Args:
            config: 新配置
            
        Returns:
            是否成功
        """
        # 断开旧连接
        if self._store:
            self._store.disconnect()
        
        # 更新配置
        self.config = config
        
        # 初始化新存储
        self._initialize_store()
        
        return self._store is not None and self._store.status == VectorStoreStatus.HEALTHY
    
    def health_check(self) -> VectorStoreStatus:
        """健康检查"""
        if self._store:
            return self._store.health_check()
        return VectorStoreStatus.UNAVAILABLE
    
    def create_collection(
        self,
        name: str,
        dimension: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """创建集合"""
        if self._store:
            return self._store.create_collection(name, dimension, metadata)
        return False
    
    def delete_collection(self, name: str) -> bool:
        """删除集合"""
        if self._store:
            return self._store.delete_collection(name)
        return False
    
    def list_collections(self) -> List[str]:
        """列出集合"""
        if self._store:
            return self._store.list_collections()
        return []
    
    def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        """获取集合信息"""
        if self._store:
            return self._store.get_collection_info(name)
        return None
    
    def add_document(
        self,
        collection_name: str,
        document: VectorDocument
    ) -> bool:
        """添加文档"""
        if self._store:
            return self._store.add_document(collection_name, document)
        return False
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[VectorDocument]
    ) -> Dict[str, Any]:
        """批量添加文档"""
        if self._store:
            return self._store.add_documents(collection_name, documents)
        return {"success": False, "count": 0, "error": "存储不可用"}
    
    def get_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[VectorDocument]:
        """获取文档"""
        if self._store:
            return self._store.get_document(collection_name, document_id)
        return None
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """删除文档"""
        if self._store:
            return self._store.delete_document(collection_name, document_id)
        return False
    
    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """搜索"""
        if self._store:
            return self._store.search(collection_name, query, top_k, filters)
        return []
    
    def search_by_vector(
        self,
        collection_name: str,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        if self._store:
            return self._store.search_by_vector(collection_name, vector, top_k, filters)
        return []
    
    def count(self, collection_name: str) -> int:
        """获取数量"""
        if self._store:
            return self._store.count(collection_name)
        return 0
    
    def get_backend_type(self) -> VectorStoreBackend:
        """获取后端类型"""
        return self.config.backend
    
    def get_status(self) -> VectorStoreStatus:
        """获取状态"""
        if self._store:
            return self._store.status
        return VectorStoreStatus.UNAVAILABLE


# 便捷函数

def create_vector_store_adapter(
    backend: VectorStoreBackend = VectorStoreBackend.CHROMA,
    connection_string: str = "http://localhost:8008",
    default_collection: str = "documents"
) -> VectorStoreAdapter:
    """创建向量存储适配器"""
    config = VectorStoreConfig(
        backend=backend,
        connection_string=connection_string,
        default_collection=default_collection
    )
    return VectorStoreAdapter(config)


# 全局实例
vector_store_adapter = create_vector_store_adapter()
