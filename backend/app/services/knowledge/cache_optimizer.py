"""缓存优化服务

提供高级缓存策略，包括缓存预热、过期策略优化、缓存键管理等。
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
import hashlib
import json

from app.core.cache import cache_service
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class CacheOptimizer:
    """缓存优化器
    
    提供高级缓存策略和优化功能。
    """
    
    def __init__(self):
        """初始化缓存优化器"""
        self.redis_client = get_redis()
        self.cache_prefix = "knowledge:"
        self.warmup_tasks: Set[asyncio.Task] = set()
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """生成标准化的缓存键
        
        Args:
            prefix: 缓存键前缀
            *args: 可变参数
            **kwargs: 关键字参数
            
        Returns:
            生成的缓存键
        """
        # 构建基础键
        base_key = f"{self.cache_prefix}{prefix}"
        
        # 添加参数
        if args:
            base_key += ":" + ":".join(str(arg) for arg in args)
        
        # 添加关键字参数（排序以确保一致性）
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = ":".join(f"{k}={v}" for k, v in sorted_kwargs)
            base_key += f":{kwargs_str}"
        
        # 对长键进行哈希处理
        if len(base_key) > 100:
            hash_part = hashlib.md5(base_key.encode()).hexdigest()
            base_key = f"{self.cache_prefix}{prefix}:{hash_part}"
        
        return base_key
    
    async def warmup_cache(self, keys: List[str], data_funcs: List[Callable[[], Dict[str, Any]]], 
                          timeout: Optional[timedelta] = None):
        """预热缓存
        
        Args:
            keys: 缓存键列表
            data_funcs: 生成数据的函数列表
            timeout: 缓存超时时间
            
        Returns:
            预热成功的键数量
        """
        if len(keys) != len(data_funcs):
            raise ValueError("keys和data_funcs长度必须相等")
        
        success_count = 0
        
        for key, data_func in zip(keys, data_funcs):
            try:
                data = data_func()
                success = await cache_service.set(key, data, timeout)
                if success:
                    success_count += 1
                    logger.debug(f"缓存预热成功: {key}")
                else:
                    logger.warning(f"缓存预热失败: {key}")
            except Exception as e:
                logger.error(f"缓存预热异常 {key}: {str(e)}")
        
        return success_count
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """批量获取缓存
        
        Args:
            keys: 缓存键列表
            
        Returns:
            键到值的映射
        """
        results = {}
        
        # 使用Redis的mget命令批量获取（如果Redis可用）
        if self.redis_client:
            try:
                values = self.redis_client.mget(keys)
                for key, value in zip(keys, values):
                    if value:
                        try:
                            results[key] = json.loads(value)
                        except json.JSONDecodeError:
                            results[key] = None
                    else:
                        results[key] = None
                return results
            except Exception as e:
                logger.error(f"批量获取缓存失败: {str(e)}")
        
        # 回退到逐个获取
        for key in keys:
            results[key] = await cache_service.get(key)
        
        return results
    
    async def batch_set(self, items: Dict[str, Dict[str, Any]], timeout: Optional[timedelta] = None) -> int:
        """批量设置缓存
        
        Args:
            items: 键值对映射
            timeout: 缓存超时时间
            
        Returns:
            设置成功的键数量
        """
        success_count = 0
        
        # 使用Redis的pipeline批量设置（如果Redis可用）
        if self.redis_client:
            try:
                pipeline = self.redis_client.pipeline()
                ttl = timeout.seconds if timeout else None
                
                for key, value in items.items():
                    value_str = json.dumps(value)
                    if ttl:
                        pipeline.set(key, value_str, ex=ttl)
                    else:
                        pipeline.set(key, value_str)
                
                results = pipeline.execute()
                success_count = sum(1 for result in results if result)
                return success_count
            except Exception as e:
                logger.error(f"批量设置缓存失败: {str(e)}")
        
        # 回退到逐个设置
        for key, value in items.items():
            success = await cache_service.set(key, value, timeout)
            if success:
                success_count += 1
        
        return success_count
    
    def get_optimal_ttl(self, data_type: str, access_pattern: str = "regular") -> timedelta:
        """获取最优的缓存过期时间
        
        Args:
            data_type: 数据类型
            access_pattern: 访问模式 (regular, frequent, rare)
            
        Returns:
            最优的过期时间
        """
        # 基于数据类型和访问模式的TTL策略
        ttl_map = {
            "knowledge_graph": {
                "regular": timedelta(hours=48),
                "frequent": timedelta(hours=12),
                "rare": timedelta(days=7)
            },
            "entity_extraction": {
                "regular": timedelta(hours=24),
                "frequent": timedelta(hours=6),
                "rare": timedelta(days=3)
            },
            "document_processing": {
                "regular": timedelta(hours=12),
                "frequent": timedelta(hours=3),
                "rare": timedelta(days=2)
            },
            "search_results": {
                "regular": timedelta(minutes=30),
                "frequent": timedelta(minutes=10),
                "rare": timedelta(hours=2)
            },
            "statistics": {
                "regular": timedelta(minutes=15),
                "frequent": timedelta(minutes=5),
                "rare": timedelta(hours=1)
            }
        }
        
        # 默认TTL
        default_ttl = timedelta(hours=1)
        
        return ttl_map.get(data_type, {}).get(access_pattern, default_ttl)
    
    async def refresh_cache(self, key: str, data_func: Callable[[], Dict[str, Any]], 
                          timeout: Optional[timedelta] = None) -> bool:
        """刷新缓存
        
        Args:
            key: 缓存键
            data_func: 生成数据的函数
            timeout: 缓存超时时间
            
        Returns:
            是否刷新成功
        """
        try:
            # 生成新数据
            data = data_func()
            
            # 设置缓存
            success = await cache_service.set(key, data, timeout)
            
            if success:
                logger.debug(f"缓存刷新成功: {key}")
            else:
                logger.warning(f"缓存刷新失败: {key}")
            
            return success
        except Exception as e:
            logger.error(f"缓存刷新异常 {key}: {str(e)}")
            return False
    
    async def invalidate_pattern(self, pattern: str):
        """根据模式使缓存失效
        
        Args:
            pattern: 缓存键模式（支持通配符）
        """
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"使 {len(keys)} 个缓存键失效: {pattern}")
            except Exception as e:
                logger.error(f"使缓存失效失败: {str(e)}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        stats = {
            "backend": "redis" if self.redis_client else "memory",
            "timestamp": datetime.now().isoformat()
        }
        
        if self.redis_client:
            try:
                # 获取Redis信息
                info = self.redis_client.info()
                stats.update({
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "keys": info.get("db0", {}).get("keys", 0),
                    "expired_keys": info.get("expired_keys", 0),
                    "evicted_keys": info.get("evicted_keys", 0)
                })
            except Exception as e:
                logger.error(f"获取Redis统计失败: {str(e)}")
        
        return stats
    
    def is_cache_healthy(self) -> bool:
        """检查缓存健康状态
        
        Returns:
            缓存是否健康
        """
        if self.redis_client:
            try:
                self.redis_client.ping()
                return True
            except Exception:
                return False
        return True  # 内存缓存始终健康
    
    async def optimize_cache(self):
        """优化缓存
        
        执行缓存优化操作，如清理过期数据、优化内存使用等。
        """
        if self.redis_client:
            try:
                # 清理过期数据
                # Redis会自动清理过期数据，这里可以添加其他优化操作
                logger.info("缓存优化完成")
            except Exception as e:
                logger.error(f"缓存优化失败: {str(e)}")


# 全局缓存优化器实例
cache_optimizer = CacheOptimizer()


# 装饰器
def cached(prefix: str, timeout: Optional[timedelta] = None, data_type: str = "regular"):
    """缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        timeout: 缓存超时时间
        data_type: 数据类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key = cache_optimizer.generate_cache_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = await cache_service.get(key)
            if cached_value:
                return cached_value
            
            # 缓存未命中，执行函数
            result = await func(*args, **kwargs)
            
            # 确定TTL
            if not timeout:
                ttl = cache_optimizer.get_optimal_ttl(data_type)
            else:
                ttl = timeout
            
            # 设置缓存
            await cache_service.set(key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator


# 便捷函数

async def warmup_knowledge_graph_cache(knowledge_base_id: int, document_ids: List[int]):
    """预热知识图谱缓存
    
    Args:
        knowledge_base_id: 知识库ID
        document_ids: 文档ID列表
    """
    from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService
    
    kg_service = KnowledgeGraphService()
    
    keys = []
    funcs = []
    
    for doc_id in document_ids:
        key = cache_optimizer.generate_cache_key(
            "knowledge_graph",
            knowledge_base_id=knowledge_base_id,
            document_id=doc_id
        )
        
        def create_func(did):
            def func():
                from app.core.database import SessionLocal
                with SessionLocal() as db:
                    return kg_service.build_document_graph(did, db)
            return func
        
        keys.append(key)
        funcs.append(create_func(doc_id))
    
    return await cache_optimizer.warmup_cache(keys, funcs)


async def warmup_entity_extraction_cache(document_ids: List[int]):
    """预热实体提取缓存
    
    Args:
        document_ids: 文档ID列表
    """
    from app.services.knowledge.extraction.llm_extractor import LLMEntityExtractor
    
    extractor = LLMEntityExtractor()
    
    keys = []
    funcs = []
    
    for doc_id in document_ids:
        key = cache_optimizer.generate_cache_key("entity_extraction", document_id=doc_id)
        
        def create_func(did):
            def func():
                from app.core.database import SessionLocal
                with SessionLocal() as db:
                    return extractor.extract_from_document(did, db)
            return func
        
        keys.append(key)
        funcs.append(create_func(doc_id))
    
    return await cache_optimizer.warmup_cache(keys, funcs)


async def invalidate_document_cache(document_id: int):
    """使文档相关的缓存失效
    
    Args:
        document_id: 文档ID
    """
    patterns = [
        f"knowledge:knowledge_graph:*:document_id={document_id}",
        f"knowledge:entity_extraction:*:document_id={document_id}",
        f"knowledge:document_processing:*:document_id={document_id}"
    ]
    
    for pattern in patterns:
        await cache_optimizer.invalidate_pattern(pattern)


async def get_cache_health_status():
    """获取缓存健康状态
    
    Returns:
        健康状态
    """
    return {
        "healthy": cache_optimizer.is_cache_healthy(),
        "stats": await cache_optimizer.get_cache_stats()
    }