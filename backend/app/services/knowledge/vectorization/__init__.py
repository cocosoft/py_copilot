"""
向量存储模块

提供多种向量存储后端支持：
- SQLiteVectorStore: 基于 SQLite 的向量存储，无需外部服务
- ChromaDBVectorStore: 基于 ChromaDB 的专业向量存储

使用示例：
    from app.services.knowledge.vectorization import VectorStoreFactory
    
    # 获取默认存储实例
    store = VectorStoreFactory.get_store()
    
    # 添加文档
    store.add_document("doc_1", "文本内容", {"key": "value"})
    
    # 搜索
    results = store.search("查询文本", top_k=5)
"""

from .base import VectorStoreBase
from .factory import VectorStoreFactory
from .sqlite_store import SQLiteVectorStore
from .chromadb_store import ChromaDBVectorStore

__all__ = ['VectorStoreBase', 'VectorStoreFactory', 'SQLiteVectorStore', 'ChromaDBVectorStore']
