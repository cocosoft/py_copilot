"""
长期记忆机制模块

提供记忆的存储、检索、压缩和管理功能。
"""

from .memory_models import (
    MemoryItem, MemoryType, MemoryPriority, MemoryAccessPattern,
    MemoryManager, memory_manager
)

from .memory_retrieval import (
    MemoryRetrievalEngine, MemoryCompressionEngine,
    memory_retrieval_engine, memory_compression_engine
)

from .memory_api import (
    MemoryCreateRequest, MemoryUpdateRequest, MemoryResponse,
    MemoryRetrievalRequest, MemoryRetrievalResponse, MemoryStatsResponse,
    MemoryCompressionResponse, router as memory_router
)

__all__ = [
    # 数据模型
    "MemoryItem",
    "MemoryType",
    "MemoryPriority", 
    "MemoryAccessPattern",
    "MemoryManager",
    "memory_manager",
    
    # 检索算法
    "MemoryRetrievalEngine",
    "MemoryCompressionEngine",
    "memory_retrieval_engine",
    "memory_compression_engine",
    
    # API接口
    "MemoryCreateRequest",
    "MemoryUpdateRequest",
    "MemoryResponse",
    "MemoryRetrievalRequest",
    "MemoryRetrievalResponse",
    "MemoryStatsResponse",
    "MemoryCompressionResponse",
    "memory_router"
]