"""增强的记忆缓存机制

提供智能的记忆检索缓存，减少重复检索
"""
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass, field

from app.core.cache import cache_service

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Any
    timestamp: datetime
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    ttl: timedelta = timedelta(minutes=5)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.timestamp + self.ttl
    
    def access(self):
        """记录访问"""
        self.access_count += 1
        self.last_access = datetime.now()


class MemoryRetrievalCache:
    """记忆检索缓存管理器"""
    
    def __init__(
        self,
        max_size: int = 500,
        default_ttl: timedelta = timedelta(minutes=5),
        enable_lru: bool = True,
        enable_stats: bool = True
    ):
        """
        初始化记忆检索缓存管理器
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认缓存过期时间
            enable_lru: 是否启用LRU淘汰策略
            enable_stats: 是否启用统计功能
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_lru = enable_lru
        self.enable_stats = enable_stats
        
        # 使用OrderedDict实现LRU
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0,
            "cache_size": 0
        }
        
        # 查询模式统计
        self.query_patterns: Dict[str, int] = {}
    
    def _generate_cache_key(
        self,
        query_type: str,
        params: Dict[str, Any]
    ) -> str:
        """
        生成缓存键
        
        Args:
            query_type: 查询类型（如：semantic_search, user_memories等）
            params: 查询参数
            
        Returns:
            缓存键
        """
        # 对参数进行排序，确保相同参数生成相同的键
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 将参数转换为字符串表示
        param_str = json.dumps(sorted_params, sort_keys=True, ensure_ascii=False)
        
        # 组合查询类型和参数
        full_str = f"{query_type}:{param_str}"
        
        # 使用哈希函数生成唯一键
        return hashlib.md5(full_str.encode('utf-8')).hexdigest()
    
    def _normalize_query(self, query: str) -> str:
        """
        规范化查询字符串
        
        Args:
            query: 原始查询字符串
            
        Returns:
            规范化后的查询字符串
        """
        # 转换为小写
        normalized = query.lower().strip()
        
        # 移除多余空格
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _should_cache(self, query_type: str, params: Dict[str, Any]) -> bool:
        """
        判断是否应该缓存此查询
        
        Args:
            query_type: 查询类型
            params: 查询参数
            
        Returns:
            是否应该缓存
        """
        # 某些查询类型不缓存
        non_cacheable_types = ["real_time_search", "live_updates"]
        if query_type in non_cacheable_types:
            return False
        
        # 某些参数组合不缓存
        if params.get("no_cache", False):
            return False
        
        return True
    
    def _evict_expired(self):
        """淘汰过期的缓存条目"""
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            if self.enable_stats:
                self.stats["evictions"] += 1
        
        if expired_keys:
            logger.debug(f"淘汰了 {len(expired_keys)} 个过期缓存条目")
    
    def _evict_lru(self):
        """使用LRU策略淘汰缓存条目"""
        if len(self.cache) <= self.max_size:
            return
        
        # 计算需要淘汰的条目数
        evict_count = len(self.cache) - self.max_size
        
        # 淘汰最久未使用的条目
        for _ in range(evict_count):
            key, _ = self.cache.popitem(last=False)
            if self.enable_stats:
                self.stats["evictions"] += 1
        
        logger.debug(f"LRU淘汰了 {evict_count} 个缓存条目")
    
    def _update_stats(self, hit: bool):
        """
        更新统计信息
        
        Args:
            hit: 是否命中缓存
        """
        if not self.enable_stats:
            return
        
        self.stats["total_queries"] += 1
        if hit:
            self.stats["hits"] += 1
        else:
            self.stats["misses"] += 1
        
        self.stats["cache_size"] = len(self.cache)
    
    def _track_query_pattern(self, query_type: str, params: Dict[str, Any]):
        """
        跟踪查询模式
        
        Args:
            query_type: 查询类型
            params: 查询参数
        """
        if not self.enable_stats:
            return
        
        # 提取查询模式（去除具体值）
        pattern = f"{query_type}:{','.join(sorted(params.keys()))}"
        self.query_patterns[pattern] = self.query_patterns.get(pattern, 0) + 1
    
    async def get(
        self,
        query_type: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            query_type: 查询类型
            params: 查询参数
            
        Returns:
            缓存的数据，如果不存在返回None
        """
        # 检查是否应该缓存此查询
        if not self._should_cache(query_type, params):
            return None
        
        # 生成缓存键
        cache_key = self._generate_cache_key(query_type, params)
        
        # 尝试从缓存获取
        entry = self.cache.get(cache_key)
        
        if entry is None:
            # 缓存未命中
            self._update_stats(hit=False)
            return None
        
        # 检查是否过期
        if entry.is_expired():
            del self.cache[cache_key]
            self._update_stats(hit=False)
            return None
        
        # 缓存命中
        entry.access()
        
        # 如果启用LRU，移动到最近使用
        if self.enable_lru:
            self.cache.move_to_end(cache_key)
        
        self._update_stats(hit=True)
        logger.debug(f"缓存命中: {query_type}")
        
        return entry.data
    
    async def set(
        self,
        query_type: str,
        params: Dict[str, Any],
        data: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        设置缓存数据
        
        Args:
            query_type: 查询类型
            params: 查询参数
            data: 要缓存的数据
            ttl: 缓存过期时间（可选）
            
        Returns:
            是否设置成功
        """
        # 检查是否应该缓存此查询
        if not self._should_cache(query_type, params):
            return False
        
        # 检查数据是否为空
        if data is None:
            return False
        
        # 生成缓存键
        cache_key = self._generate_cache_key(query_type, params)
        
        # 创建缓存条目
        entry = CacheEntry(
            key=cache_key,
            data=data,
            timestamp=datetime.now(),
            ttl=ttl or self.default_ttl
        )
        
        # 添加到缓存
        self.cache[cache_key] = entry
        
        # 如果启用LRU，移动到最近使用
        if self.enable_lru:
            self.cache.move_to_end(cache_key)
        
        # 检查缓存大小
        self._evict_expired()
        self._evict_lru()
        
        # 跟踪查询模式
        self._track_query_pattern(query_type, params)
        
        logger.debug(f"缓存设置: {query_type}")
        return True
    
    async def get_or_set(
        self,
        query_type: str,
        params: Dict[str, Any],
        fetch_func,
        ttl: Optional[timedelta] = None
    ) -> Any:
        """
        获取缓存数据，如果不存在则调用函数获取并缓存
        
        Args:
            query_type: 查询类型
            params: 查询参数
            fetch_func: 获取数据的函数
            ttl: 缓存过期时间（可选）
            
        Returns:
            数据
        """
        # 尝试从缓存获取
        data = await self.get(query_type, params)
        if data is not None:
            return data
        
        # 缓存未命中，调用函数获取数据
        try:
            data = await fetch_func()
            
            # 缓存数据
            if data is not None:
                await self.set(query_type, params, data, ttl)
            
            return data
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            raise
    
    async def invalidate(self, query_type: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
        """
        使缓存失效
        
        Args:
            query_type: 查询类型（可选，如果为None则使所有匹配类型的缓存失效）
            params: 查询参数（可选，如果为None则使所有匹配类型的缓存失效）
        """
        if query_type is None:
            # 清除所有缓存
            self.cache.clear()
            logger.info("清除了所有缓存")
            return
        
        if params is None:
            # 清除指定类型的所有缓存
            keys_to_remove = []
            for key, entry in self.cache.items():
                # 检查键是否匹配查询类型
                if key.startswith(query_type):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
            
            logger.info(f"清除了 {len(keys_to_remove)} 个 {query_type} 类型的缓存")
            return
        
        # 清除特定查询的缓存
        cache_key = self._generate_cache_key(query_type, params)
        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.debug(f"清除了缓存: {query_type}")
    
    async def invalidate_by_user(self, user_id: int):
        """
        使特定用户的所有缓存失效
        
        Args:
            user_id: 用户ID
        """
        keys_to_remove = []
        for key, entry in self.cache.items():
            # 检查缓存数据中是否包含用户ID
            if isinstance(entry.data, list):
                for item in entry.data:
                    if hasattr(item, 'user_id') and item.user_id == user_id:
                        keys_to_remove.append(key)
                        break
            elif hasattr(entry.data, 'user_id') and entry.data.user_id == user_id:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.info(f"清除了用户 {user_id} 的 {len(keys_to_remove)} 个缓存")
    
    async def invalidate_by_conversation(self, conversation_id: int):
        """
        使特定对话的所有缓存失效
        
        Args:
            conversation_id: 对话ID
        """
        keys_to_remove = []
        for key, entry in self.cache.items():
            # 检查缓存数据中是否包含对话ID
            if isinstance(entry.data, list):
                for item in entry.data:
                    if hasattr(item, 'conversation_id') and item.conversation_id == conversation_id:
                        keys_to_remove.append(key)
                        break
            elif hasattr(entry.data, 'conversation_id') and entry.data.conversation_id == conversation_id:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.info(f"清除了对话 {conversation_id} 的 {len(keys_to_remove)} 个缓存")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        if not self.enable_stats:
            return {"stats_enabled": False}
        
        hit_rate = 0.0
        if self.stats["total_queries"] > 0:
            hit_rate = self.stats["hits"] / self.stats["total_queries"]
        
        return {
            "stats_enabled": True,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "total_queries": self.stats["total_queries"],
            "cache_size": self.stats["cache_size"],
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "query_patterns": dict(sorted(
                self.query_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])  # 返回前10个最常用的查询模式
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0,
            "cache_size": len(self.cache)
        }
        self.query_patterns.clear()
        logger.info("重置了缓存统计信息")
    
    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        logger.info("清空了所有缓存")


# 创建全局记忆检索缓存实例
_default_cache: Optional[MemoryRetrievalCache] = None


def get_memory_retrieval_cache(
    max_size: int = 500,
    default_ttl: timedelta = timedelta(minutes=5)
) -> MemoryRetrievalCache:
    """
    获取全局记忆检索缓存实例
    
    Args:
        max_size: 最大缓存条目数
        default_ttl: 默认缓存过期时间
        
    Returns:
        记忆检索缓存实例
    """
    global _default_cache
    if _default_cache is None:
        _default_cache = MemoryRetrievalCache(
            max_size=max_size,
            default_ttl=default_ttl
        )
    return _default_cache


# 便捷函数
async def cache_semantic_search(
    query: str,
    user_id: int,
    results: List[Any],
    ttl: Optional[timedelta] = None
):
    """
    缓存语义搜索结果
    
    Args:
        query: 查询字符串
        user_id: 用户ID
        results: 搜索结果
        ttl: 缓存过期时间
    """
    cache = get_memory_retrieval_cache()
    await cache.set(
        query_type="semantic_search",
        params={"query": query, "user_id": user_id},
        data=results,
        ttl=ttl
    )


async def get_cached_semantic_search(
    query: str,
    user_id: int
) -> Optional[List[Any]]:
    """
    获取缓存的语义搜索结果
    
    Args:
        query: 查询字符串
        user_id: 用户ID
        
    Returns:
        缓存的搜索结果，如果不存在返回None
    """
    cache = get_memory_retrieval_cache()
    return await cache.get(
        query_type="semantic_search",
        params={"query": query, "user_id": user_id}
    )


async def cache_user_memories(
    user_id: int,
    memory_types: Optional[List[str]] = None,
    results: List[Any] = None,
    ttl: Optional[timedelta] = None
):
    """
    缓存用户记忆
    
    Args:
        user_id: 用户ID
        memory_types: 记忆类型列表
        results: 记忆列表
        ttl: 缓存过期时间
    """
    cache = get_memory_retrieval_cache()
    await cache.set(
        query_type="user_memories",
        params={
            "user_id": user_id,
            "memory_types": memory_types or []
        },
        data=results,
        ttl=ttl
    )


async def get_cached_user_memories(
    user_id: int,
    memory_types: Optional[List[str]] = None
) -> Optional[List[Any]]:
    """
    获取缓存的用户记忆
    
    Args:
        user_id: 用户ID
        memory_types: 记忆类型列表
        
    Returns:
        缓存的记忆列表，如果不存在返回None
    """
    cache = get_memory_retrieval_cache()
    return await cache.get(
        query_type="user_memories",
        params={
            "user_id": user_id,
            "memory_types": memory_types or []
        }
    )
