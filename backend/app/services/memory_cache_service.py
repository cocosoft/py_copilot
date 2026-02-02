from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import json
import logging

from app.models.memory import GlobalMemory
from app.core.cache import cache_service
from app.core.memory_retrieval_cache import (
    get_memory_retrieval_cache,
    cache_semantic_search,
    get_cached_semantic_search,
    cache_user_memories,
    get_cached_user_memories
)

logger = logging.getLogger(__name__)


class MemoryCacheService:
    """记忆缓存服务，用于优化记忆检索性能"""
    
    def __init__(self, cache_size: int = 1000, cache_timeout: int = 300):
        """初始化缓存服务
        
        Args:
            cache_size: 缓存最大条目数（仅用于兼容旧代码）
            cache_timeout: 缓存超时时间（秒）
        """
        self.cache_timeout = timedelta(seconds=cache_timeout)
        # 使用增强的记忆检索缓存
        self.retrieval_cache = get_memory_retrieval_cache(
            max_size=cache_size,
            default_ttl=self.cache_timeout
        )
    
    async def get_user_memories(self, db: Session, user_id: int, memory_types: Optional[List[str]] = None,
                        memory_categories: Optional[List[str]] = None, limit: int = 20,
                        offset: int = 0, session_id: Optional[str] = None) -> List[GlobalMemory]:
        """获取用户记忆，使用缓存优化"""
        # 首先尝试从增强缓存获取
        cached_data = await get_cached_user_memories(user_id, memory_types)
        if cached_data is not None:
            logger.debug(f"使用增强缓存的用户记忆: {user_id}")
            return cached_data
        
        # 构建缓存键
        cache_key = self._build_cache_key({
            "type": "user_memories",
            "user_id": user_id,
            "memory_types": memory_types,
            "memory_categories": memory_categories,
            "limit": limit,
            "offset": offset,
            "session_id": session_id
        })
        
        def fetch_data():
            """从数据库获取数据"""
            # 基础查询
            query = db.query(GlobalMemory).filter(
                GlobalMemory.user_id == user_id,
                GlobalMemory.is_active == True
            )
            
            # 过滤条件
            if memory_types:
                query = query.filter(GlobalMemory.memory_type.in_(memory_types))
            
            if memory_categories:
                query = query.filter(GlobalMemory.memory_category.in_(memory_categories))
            
            if session_id:
                query = query.filter(GlobalMemory.session_id == session_id)
            
            # 排序和分页
            query = query.order_by(GlobalMemory.created_at.desc())
            results = query.offset(offset).limit(limit).all()
            
            return {
                "data": results,
                "timestamp": datetime.now().isoformat()
            }
        
        # 使用异步缓存服务
        cached_data = await cache_service.get_or_set(cache_key, fetch_data, self.cache_timeout)
        
        # 同时缓存到增强缓存
        await cache_user_memories(user_id, memory_types, cached_data["data"], self.cache_timeout)
        
        logger.debug(f"使用缓存的用户记忆: {user_id}")
        return cached_data["data"]
    
    async def get_conversation_memories(self, db: Session, conversation_id: int, user_id: int, 
                                limit: int = 20, offset: int = 0) -> List[GlobalMemory]:
        """获取对话记忆，使用缓存优化"""
        # 构建缓存键
        cache_key = self._build_cache_key({
            "type": "conversation_memories",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        })
        
        def fetch_data():
            """从数据库获取数据"""
            from app.models.memory import GlobalMemory, ConversationMemoryMapping
            
            # 获取与对话相关的记忆ID
            query = db.query(GlobalMemory).join(
                ConversationMemoryMapping, 
                and_(
                    ConversationMemoryMapping.memory_id == GlobalMemory.id,
                    ConversationMemoryMapping.conversation_id == conversation_id,
                    GlobalMemory.user_id == user_id,
                    GlobalMemory.is_active == True
                )
            ).order_by(GlobalMemory.created_at.desc())
            
            results = query.offset(offset).limit(limit).all()
            
            return {
                "data": results,
                "timestamp": datetime.now().isoformat()
            }
        
        # 使用异步缓存服务
        cached_data = await cache_service.get_or_set(cache_key, fetch_data, self.cache_timeout)
        
        logger.debug(f"使用缓存的对话记忆: {conversation_id}")
        return cached_data["data"]
    
    async def cache_semantic_search(self, query: str, user_id: int, results: List[GlobalMemory]):
        """缓存语义搜索结果"""
        # 使用增强缓存
        await cache_semantic_search(query, user_id, results, self.cache_timeout)
        
        # 同时使用旧缓存（向后兼容）
        cache_key = self._build_cache_key({
            "type": "semantic_search",
            "query": query,
            "user_id": user_id
        })
        
        # 直接使用异步缓存服务
        await cache_service.set(
            cache_key,
            {
                "data": results,
                "timestamp": datetime.now().isoformat()
            },
            self.cache_timeout
        )
        
    async def get_cached_semantic_search(self, query: str, user_id: int) -> Optional[List[GlobalMemory]]:
        """获取缓存的语义搜索结果"""
        # 首先尝试从增强缓存获取
        cached_data = await get_cached_semantic_search(query, user_id)
        if cached_data is not None:
            logger.debug(f"使用增强缓存的语义搜索结果: {query[:50]}...")
            return cached_data
        
        # 使用旧缓存（向后兼容）
        cache_key = self._build_cache_key({
            "type": "semantic_search",
            "query": query,
            "user_id": user_id
        })
        
        # 直接使用异步缓存服务
        cached_data = await cache_service.get(cache_key)
        
        if cached_data:
            logger.debug(f"使用缓存的语义搜索结果: {query[:50]}...")
            return cached_data["data"]
        
        return None
    
    async def clear_user_cache(self, user_id: int):
        """清除特定用户的缓存"""
        # 使用增强缓存清除
        await self.retrieval_cache.invalidate_by_user(user_id)
        
        # 由于使用了统一的缓存键格式，这里需要异步清除相关缓存
        # 注意：实际应用中可能需要更精细的缓存键管理
        logger.info(f"清除用户缓存: {user_id}")
        # 这里只是记录日志，实际清除需要根据缓存后端的特性实现
    
    async def clear_conversation_cache(self, conversation_id: int):
        """清除特定对话的缓存"""
        # 使用增强缓存清除
        await self.retrieval_cache.invalidate_by_conversation(conversation_id)
        
        logger.info(f"清除对话缓存: {conversation_id}")
        # 这里只是记录日志，实际清除需要根据缓存后端的特性实现
    
    async def clear_all_cache(self):
        """清除所有缓存"""
        logger.info("清除所有缓存")
        # 清除增强缓存
        self.retrieval_cache.clear()
        # 清除旧缓存
        await cache_service.clear()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.retrieval_cache.get_stats()
    
    def _build_cache_key(self, params: Dict[str, Any]) -> str:
        """构建缓存键"""
        # 对参数进行排序，确保相同参数生成相同的键
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 将参数转换为字符串表示
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        # 使用哈希函数生成唯一键
        import hashlib
        return hashlib.md5(param_str.encode()).hexdigest()


    def get_user_memories_sync(self, db: Session, user_id: int, memory_types: Optional[List[str]] = None,
                        memory_categories: Optional[List[str]] = None, limit: int = 20,
                        offset: int = 0, session_id: Optional[str] = None) -> List[GlobalMemory]:
        """获取用户记忆，同步版本"""
        import asyncio
        
        async def _get():
            return await self.get_user_memories(db, user_id, memory_types, memory_categories, limit, offset, session_id)
        
        try:
            return asyncio.run(_get())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                logger.warning("在已有事件循环中运行，尝试使用当前事件循环")
                import sys
                if sys.version_info >= (3, 7):
                    loop = asyncio.get_running_loop()
                    return loop.run_until_complete(_get())
            raise

    def get_conversation_memories_sync(self, db: Session, conversation_id: int, user_id: int, 
                                limit: int = 20, offset: int = 0) -> List[GlobalMemory]:
        """获取对话记忆，同步版本"""
        import asyncio
        
        async def _get():
            return await self.get_conversation_memories(db, conversation_id, user_id, limit, offset)
        
        try:
            return asyncio.run(_get())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                logger.warning("在已有事件循环中运行，尝试使用当前事件循环")
                import sys
                if sys.version_info >= (3, 7):
                    loop = asyncio.get_running_loop()
                    return loop.run_until_complete(_get())
            raise

    def cache_semantic_search_sync(self, query: str, user_id: int, results: List[GlobalMemory]):
        """缓存语义搜索结果，同步版本"""
        import asyncio
        
        async def _cache():
            await self.cache_semantic_search(query, user_id, results)
        
        try:
            asyncio.run(_cache())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                logger.warning("在已有事件循环中运行，尝试使用当前事件循环")
                import sys
                if sys.version_info >= (3, 7):
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(_cache())
            raise

    def get_cached_semantic_search_sync(self, query: str, user_id: int) -> Optional[List[GlobalMemory]]:
        """获取缓存的语义搜索结果，同步版本"""
        import asyncio
        
        async def _get():
            return await self.get_cached_semantic_search(query, user_id)
        
        try:
            return asyncio.run(_get())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                logger.warning("在已有事件循环中运行，尝试使用当前事件循环")
                import sys
                if sys.version_info >= (3, 7):
                    loop = asyncio.get_running_loop()
                    return loop.run_until_complete(_get())
            raise

    def clear_user_cache_sync(self, user_id: int):
        """清除特定用户的缓存，同步版本"""
        import asyncio
        
        async def _clear():
            await self.clear_user_cache(user_id)
        
        try:
            asyncio.run(_clear())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                logger.warning("在已有事件循环中运行，尝试使用当前事件循环")
                import sys
                if sys.version_info >= (3, 7):
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(_clear())
            raise

    def clear_conversation_cache_sync(self, conversation_id: int):
        """清除特定对话的缓存，同步版本"""
        import asyncio
        
        async def _clear():
            await self.clear_conversation_cache(conversation_id)
        
        try:
            asyncio.run(_clear())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                logger.warning("在已有事件循环中运行，尝试使用当前事件循环")
                import sys
                if sys.version_info >= (3, 7):
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(_clear())
            raise

    def clear_all_cache_sync(self):
        """清除所有缓存，同步版本"""
        import asyncio
        
        async def _clear():
            await self.clear_all_cache()
        
        try:
            asyncio.run(_clear())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                logger.warning("在已有事件循环中运行，尝试使用当前事件循环")
                import sys
                if sys.version_info >= (3, 7):
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(_clear())
            raise


# 创建全局缓存服务实例
memory_cache_service = MemoryCacheService()