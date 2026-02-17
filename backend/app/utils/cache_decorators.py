"""缓存装饰器工具"""
from functools import wraps
from typing import Optional, Callable, Any
from datetime import timedelta
from app.core.cache import cache_service
import logging

logger = logging.getLogger(__name__)

def cache_result(ttl: int = 300, cache_key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒），默认5分钟
        cache_key_prefix: 缓存键前缀
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            cache_key = f"{cache_key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached = await cache_service.get(cache_key)
            if cached:
                logger.info(f"从缓存获取: {cache_key}")
                return cached.get("data")
            
            # 缓存未命中，执行函数
            result = await func(*args, **kwargs)
            
            # 设置缓存
            await cache_service.set(
                cache_key,
                {"data": result},
                timeout=timedelta(seconds=ttl)
            )
            logger.info(f"设置缓存: {cache_key}, TTL: {ttl}秒")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            cache_key = f"{cache_key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 同步函数需要使用asyncio运行异步缓存操作
            import asyncio
            
            # 尝试从缓存获取
            cached = asyncio.run(cache_service.get(cache_key))
            if cached:
                logger.info(f"从缓存获取: {cache_key}")
                return cached.get("data")
            
            # 缓存未命中，执行函数
            result = func(*args, **kwargs)
            
            # 设置缓存
            asyncio.run(cache_service.set(
                cache_key,
                {"data": result},
                timeout=timedelta(seconds=ttl)
            ))
            logger.info(f"设置缓存: {cache_key}, TTL: {ttl}秒")
            
            return result
        
        # 根据函数类型返回对应的包装器
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(pattern: str):
    """
    缓存失效装饰器
    
    Args:
        pattern: 缓存键模式
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 失效匹配的缓存
            try:
                # 这里简化实现，实际可能需要更复杂的模式匹配
                # 由于cache_service没有模式匹配功能，这里只做示例
                logger.info(f"缓存失效模式: {pattern}")
                # 实际实现中，需要根据pattern删除匹配的缓存键
            except Exception as e:
                logger.error(f"缓存失效失败: {e}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 失效匹配的缓存
            try:
                import asyncio
                logger.info(f"缓存失效模式: {pattern}")
                # 实际实现中，需要根据pattern删除匹配的缓存键
            except Exception as e:
                logger.error(f"缓存失效失败: {e}")
            
            return result
        
        # 根据函数类型返回对应的包装器
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
