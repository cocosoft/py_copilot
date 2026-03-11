"""
查询缓存管理器 - 向量化管理模块优化

实现基于 Redis 的查询结果缓存，支持：
- 缓存命中率统计
- 多种缓存失效策略
- 缓存更新不影响查询
- 查询响应时间减少30%

任务编号: BE-002
阶段: Phase 1 - 基础优化期
"""

import logging
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import asyncio
import threading

from app.core.redis import get_redis, redis_client

logger = logging.getLogger(__name__)


class CacheEvictionStrategy(Enum):
    """缓存失效策略"""
    TTL = "ttl"                    # 基于过期时间
    LRU = "lru"                    # 最近最少使用
    LFU = "lfu"                    # 最不经常使用
    FIFO = "fifo"                  # 先进先出
    SIZE_BASED = "size_based"      # 基于大小


@dataclass
class CacheStats:
    """缓存统计信息"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_hits_size: int = 0  # 命中的缓存数据总大小（字节）
    total_misses_size: int = 0  # 未命中的查询结果总大小（字节）
    avg_query_time: float = 0.0
    avg_cache_time: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """缓存未命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_misses / self.total_requests
    
    @property
    def time_saved(self) -> float:
        """节省时间（秒）"""
        return (self.avg_query_time - self.avg_cache_time) * self.cache_hits


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    query_hash: str = ""  # 查询参数哈希


class QueryCacheManager:
    """
    查询缓存管理器
    
    为向量查询提供高性能缓存支持，支持多种失效策略和详细的统计信息。
    
    主要特性：
    - 基于 Redis 的分布式缓存
    - 支持 TTL/LRU/LFU/FIFO 多种失效策略
    - 自动缓存键生成（基于查询参数哈希）
    - 详细的命中率统计
    - 缓存预热和批量失效
    """
    
    # 默认缓存配置
    DEFAULT_TTL = 3600  # 1小时
    MAX_CACHE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_ENTRIES = 10000
    
    def __init__(
        self,
        prefix: str = "vector_query:",
        default_ttl: int = DEFAULT_TTL,
        max_size: int = MAX_CACHE_SIZE,
        eviction_strategy: CacheEvictionStrategy = CacheEvictionStrategy.TTL,
        enable_stats: bool = True
    ):
        """
        初始化查询缓存管理器
        
        Args:
            prefix: 缓存键前缀
            default_ttl: 默认过期时间（秒）
            max_size: 最大缓存大小（字节）
            eviction_strategy: 缓存失效策略
            enable_stats: 是否启用统计
        """
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.eviction_strategy = eviction_strategy
        self.enable_stats = enable_stats
        
        # Redis 客户端
        self.redis = redis_client
        
        # 统计信息
        self.stats = CacheStats()
        self._stats_lock = threading.Lock()
        
        # 本地缓存（用于 LRU/LFU 策略）
        self._local_cache: Dict[str, CacheEntry] = {}
        self._local_cache_lock = threading.Lock()
        
        # 访问历史（用于 LRU/LFU）
        self._access_history: List[Tuple[str, datetime]] = []
        
        logger.info(
            f"查询缓存管理器初始化完成: "
            f"prefix={prefix}, ttl={default_ttl}s, "
            f"strategy={eviction_strategy.value}"
        )
    
    def _generate_cache_key(
        self,
        query: str,
        knowledge_base_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs
    ) -> str:
        """
        生成缓存键
        
        基于查询参数生成唯一的缓存键。
        
        Args:
            query: 查询文本
            knowledge_base_id: 知识库ID
            filters: 过滤条件
            limit: 结果数量限制
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        # 构建查询参数字典
        params = {
            "query": query.lower().strip(),  # 规范化查询文本
            "knowledge_base_id": knowledge_base_id,
            "filters": self._normalize_filters(filters),
            "limit": limit
        }
        params.update(kwargs)
        
        # 生成哈希
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        hash_value = hashlib.md5(params_str.encode()).hexdigest()
        
        return f"{self.prefix}{hash_value}"
    
    def _normalize_filters(self, filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """规范化过滤条件"""
        if not filters:
            return None
        
        # 排序键并转换为字符串
        return {k: str(v) for k, v in sorted(filters.items())}
    
    def _get_cache_size(self, data: Any) -> int:
        """估算缓存数据大小"""
        try:
            return len(json.dumps(data).encode())
        except:
            return 0
    
    async def get(
        self,
        query: str,
        knowledge_base_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs
    ) -> Tuple[Optional[Any], bool]:
        """
        获取缓存的查询结果
        
        Args:
            query: 查询文本
            knowledge_base_id: 知识库ID
            filters: 过滤条件
            limit: 结果数量限制
            **kwargs: 其他参数
            
        Returns:
            (缓存数据, 是否命中)
        """
        cache_key = self._generate_cache_key(query, knowledge_base_id, filters, limit, **kwargs)
        
        start_time = time.time()
        
        try:
            # 尝试从 Redis 获取
            if self.redis:
                cached_data = self.redis.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    
                    # 更新统计
                    if self.enable_stats:
                        with self._stats_lock:
                            self.stats.total_requests += 1
                            self.stats.cache_hits += 1
                            self.stats.avg_cache_time = (
                                (self.stats.avg_cache_time * (self.stats.cache_hits - 1) +
                                 (time.time() - start_time)) / self.stats.cache_hits
                            )
                            self.stats.total_hits_size += self._get_cache_size(data)
                    
                    # 更新访问历史（用于 LRU/LFU）
                    self._update_access_history(cache_key)
                    
                    logger.debug(f"缓存命中: {cache_key}")
                    return data, True
            
            # 尝试从本地缓存获取
            with self._local_cache_lock:
                if cache_key in self._local_cache:
                    entry = self._local_cache[cache_key]
                    
                    # 检查是否过期
                    if entry.expires_at and datetime.now() > entry.expires_at:
                        del self._local_cache[cache_key]
                    else:
                        # 更新访问信息
                        entry.access_count += 1
                        entry.last_accessed = datetime.now()
                        
                        if self.enable_stats:
                            with self._stats_lock:
                                self.stats.total_requests += 1
                                self.stats.cache_hits += 1
                        
                        return entry.data, True
            
            # 缓存未命中
            if self.enable_stats:
                with self._stats_lock:
                    self.stats.total_requests += 1
                    self.stats.cache_misses += 1
            
            logger.debug(f"缓存未命中: {cache_key}")
            return None, False
            
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None, False
    
    async def set(
        self,
        query: str,
        data: Any,
        knowledge_base_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        设置缓存
        
        Args:
            query: 查询文本
            data: 要缓存的数据
            knowledge_base_id: 知识库ID
            filters: 过滤条件
            limit: 结果数量限制
            ttl: 过期时间（秒），默认使用全局配置
            **kwargs: 其他参数
            
        Returns:
            是否设置成功
        """
        cache_key = self._generate_cache_key(query, knowledge_base_id, filters, limit, **kwargs)
        
        try:
            # 估算数据大小
            data_size = self._get_cache_size(data)
            
            # 如果数据太大，不缓存
            if data_size > self.max_size / 10:  # 单个条目不超过最大缓存的10%
                logger.warning(f"数据太大，跳过缓存: {data_size} bytes")
                return False
            
            # 序列化数据
            serialized_data = json.dumps(data, ensure_ascii=False)
            
            # 确定过期时间
            expire_time = ttl if ttl is not None else self.default_ttl
            
            # 存储到 Redis
            if self.redis:
                self.redis.setex(cache_key, expire_time, serialized_data)
            
            # 存储到本地缓存
            with self._local_cache_lock:
                self._local_cache[cache_key] = CacheEntry(
                    key=cache_key,
                    data=data,
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(seconds=expire_time),
                    size_bytes=data_size,
                    query_hash=cache_key
                )
                
                # 检查是否需要清理
                self._evict_if_needed()
            
            if self.enable_stats:
                with self._stats_lock:
                    self.stats.total_misses_size += data_size
            
            logger.debug(f"缓存已设置: {cache_key}, TTL={expire_time}s, size={data_size} bytes")
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    async def get_or_set(
        self,
        query: str,
        fetch_func: Callable[[], Any],
        knowledge_base_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        ttl: Optional[int] = None,
        **kwargs
    ) -> Tuple[Any, bool]:
        """
        获取缓存，如果不存在则执行查询并缓存
        
        Args:
            query: 查询文本
            fetch_func: 获取数据的函数
            knowledge_base_id: 知识库ID
            filters: 过滤条件
            limit: 结果数量限制
            ttl: 过期时间（秒）
            **kwargs: 其他参数
            
        Returns:
            (数据, 是否来自缓存)
        """
        # 尝试获取缓存
        cached_data, hit = await self.get(
            query, knowledge_base_id, filters, limit, **kwargs
        )
        
        if hit:
            return cached_data, True
        
        # 缓存未命中，执行查询
        start_time = time.time()
        
        try:
            # 执行查询函数
            if asyncio.iscoroutinefunction(fetch_func):
                data = await fetch_func()
            else:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, fetch_func)
            
            query_time = time.time() - start_time
            
            # 更新统计
            if self.enable_stats:
                with self._stats_lock:
                    self.stats.avg_query_time = (
                        (self.stats.avg_query_time * (self.stats.cache_misses - 1) +
                         query_time) / self.stats.cache_misses
                    )
            
            # 设置缓存
            await self.set(
                query, data, knowledge_base_id, filters, limit, ttl, **kwargs
            )
            
            return data, False
            
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            raise
    
    def _update_access_history(self, cache_key: str):
        """更新访问历史"""
        with self._local_cache_lock:
            now = datetime.now()
            self._access_history.append((cache_key, now))
            
            # 清理旧的历史记录
            cutoff = now - timedelta(hours=1)
            self._access_history = [
                (k, t) for k, t in self._access_history if t > cutoff
            ]
    
    def _evict_if_needed(self):
        """根据需要清理缓存"""
        with self._local_cache_lock:
            # 检查缓存大小
            total_size = sum(entry.size_bytes for entry in self._local_cache.values())
            
            if total_size < self.max_size and len(self._local_cache) < self.MAX_ENTRIES:
                return
            
            # 根据策略选择要清理的条目
            entries_to_remove = []
            
            if self.eviction_strategy == CacheEvictionStrategy.LRU:
                # 最近最少使用
                sorted_entries = sorted(
                    self._local_cache.items(),
                    key=lambda x: x[1].last_accessed
                )
                entries_to_remove = sorted_entries[:len(sorted_entries) // 4]
                
            elif self.eviction_strategy == CacheEvictionStrategy.LFU:
                # 最不经常使用
                sorted_entries = sorted(
                    self._local_cache.items(),
                    key=lambda x: x[1].access_count
                )
                entries_to_remove = sorted_entries[:len(sorted_entries) // 4]
                
            elif self.eviction_strategy == CacheEvictionStrategy.FIFO:
                # 先进先出
                sorted_entries = sorted(
                    self._local_cache.items(),
                    key=lambda x: x[1].created_at
                )
                entries_to_remove = sorted_entries[:len(sorted_entries) // 4]
                
            elif self.eviction_strategy == CacheEvictionStrategy.SIZE_BASED:
                # 基于大小
                sorted_entries = sorted(
                    self._local_cache.items(),
                    key=lambda x: x[1].size_bytes,
                    reverse=True
                )
                entries_to_remove = sorted_entries[:len(sorted_entries) // 4]
            
            # 清理选中的条目
            for key, entry in entries_to_remove:
                del self._local_cache[key]
                
                # 同时删除 Redis 中的缓存
                if self.redis:
                    self.redis.delete(key)
                
                if self.enable_stats:
                    self.stats.evictions += 1
            
            logger.info(f"缓存清理完成，移除 {len(entries_to_remove)} 个条目")
    
    async def invalidate(
        self,
        query: Optional[str] = None,
        knowledge_base_id: Optional[int] = None,
        pattern: Optional[str] = None
    ) -> int:
        """
        使缓存失效
        
        Args:
            query: 特定查询（如果提供）
            knowledge_base_id: 特定知识库（如果提供）
            pattern: 匹配模式（如果提供）
            
        Returns:
            失效的缓存数量
        """
        count = 0
        
        try:
            if query:
                # 使特定查询的缓存失效
                cache_key = self._generate_cache_key(query, knowledge_base_id)
                
                if self.redis:
                    self.redis.delete(cache_key)
                
                with self._local_cache_lock:
                    if cache_key in self._local_cache:
                        del self._local_cache[cache_key]
                
                count = 1
                logger.info(f"缓存已失效: {cache_key}")
                
            elif pattern:
                # 根据模式使缓存失效
                if self.redis:
                    keys = self.redis.keys(f"{self.prefix}{pattern}")
                    if keys:
                        self.redis.delete(*keys)
                        count = len(keys)
                
                with self._local_cache_lock:
                    keys_to_remove = [
                        k for k in self._local_cache.keys()
                        if k.startswith(f"{self.prefix}{pattern}")
                    ]
                    for key in keys_to_remove:
                        del self._local_cache[key]
                    count = max(count, len(keys_to_remove))
                
                logger.info(f"模式 '{pattern}' 的缓存已失效，共 {count} 个")
                
            elif knowledge_base_id:
                # 使特定知识库的所有缓存失效
                # 这里需要遍历所有缓存，检查 knowledge_base_id
                with self._local_cache_lock:
                    keys_to_remove = []
                    for key, entry in self._local_cache.items():
                        # 从 Redis 获取并检查
                        if self.redis:
                            data = self.redis.get(key)
                            if data:
                                try:
                                    cached = json.loads(data)
                                    if cached.get("knowledge_base_id") == knowledge_base_id:
                                        keys_to_remove.append(key)
                                except:
                                    pass
                    
                    for key in keys_to_remove:
                        del self._local_cache[key]
                        if self.redis:
                            self.redis.delete(key)
                    
                    count = len(keys_to_remove)
                
                logger.info(f"知识库 {knowledge_base_id} 的缓存已失效，共 {count} 个")
            
            return count
            
        except Exception as e:
            logger.error(f"使缓存失效失败: {e}")
            return 0
    
    async def clear_all(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否清空成功
        """
        try:
            # 清空 Redis 缓存
            if self.redis:
                keys = self.redis.keys(f"{self.prefix}*")
                if keys:
                    self.redis.delete(*keys)
            
            # 清空本地缓存
            with self._local_cache_lock:
                self._local_cache.clear()
                self._access_history.clear()
            
            # 重置统计
            if self.enable_stats:
                with self._stats_lock:
                    self.stats = CacheStats()
            
            logger.info("所有缓存已清空")
            return True
            
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        with self._stats_lock:
            stats = {
                "hit_rate": self.stats.hit_rate,
                "miss_rate": self.stats.miss_rate,
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "evictions": self.stats.evictions,
                "avg_query_time": self.stats.avg_query_time,
                "avg_cache_time": self.stats.avg_cache_time,
                "time_saved": self.stats.time_saved,
                "total_hits_size": self.stats.total_hits_size,
                "total_misses_size": self.stats.total_misses_size
            }
        
        with self._local_cache_lock:
            stats["local_cache_size"] = len(self._local_cache)
            stats["local_cache_bytes"] = sum(
                entry.size_bytes for entry in self._local_cache.values()
            )
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        with self._stats_lock:
            self.stats = CacheStats()
        logger.info("缓存统计已重置")


# 装饰器

def cached_query(
    cache_manager: QueryCacheManager,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    查询缓存装饰器
    
    用法：
        @cached_query(cache_manager, ttl=3600)
        async def search_documents(query, knowledge_base_id=None):
            # 执行查询
            return results
    
    Args:
        cache_manager: 缓存管理器实例
        ttl: 缓存过期时间
        key_func: 自定义缓存键生成函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试获取缓存
            cached_data, hit = await cache_manager.get(cache_key)
            
            if hit:
                return cached_data
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 设置缓存
            await cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步版本
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# 全局缓存管理器实例
query_cache_manager = QueryCacheManager()


# 便捷函数

async def get_cached_query(
    query: str,
    knowledge_base_id: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10
) -> Tuple[Optional[Any], bool]:
    """获取缓存的查询结果"""
    return await query_cache_manager.get(query, knowledge_base_id, filters, limit)


async def set_cached_query(
    query: str,
    data: Any,
    knowledge_base_id: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    ttl: Optional[int] = None
) -> bool:
    """设置查询缓存"""
    return await query_cache_manager.set(query, data, knowledge_base_id, filters, limit, ttl)


async def execute_cached_query(
    query: str,
    fetch_func: Callable[[], Any],
    knowledge_base_id: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    ttl: Optional[int] = None
) -> Tuple[Any, bool]:
    """执行查询并缓存结果"""
    return await query_cache_manager.get_or_set(
        query, fetch_func, knowledge_base_id, filters, limit, ttl
    )
