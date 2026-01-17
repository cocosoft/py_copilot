"""缓存服务核心模块"""
import logging
import json
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from datetime import datetime, timedelta

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheBackend(Generic[T]):
    """缓存后端接口"""
    
    async def get(self, key: str) -> Optional[T]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在返回None
        """
        raise NotImplementedError
    
    async def set(self, key: str, value: T, timeout: Optional[timedelta] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 缓存超时时间
            
        Returns:
            是否设置成功
        """
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        raise NotImplementedError
    
    async def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否清空成功
        """
        raise NotImplementedError


class RedisCacheBackend(CacheBackend[Dict[str, Any]]):
    """Redis缓存后端实现"""
    
    def __init__(self):
        """初始化Redis缓存后端"""
        self.redis_client = get_redis()
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取Redis缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在返回None
        """
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis缓存获取失败: {str(e)}")
            return None
    
    async def set(self, key: str, value: Dict[str, Any], timeout: Optional[timedelta] = None) -> bool:
        """
        设置Redis缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 缓存超时时间
            
        Returns:
            是否设置成功
        """
        if not self.redis_client:
            return False
        
        try:
            ttl = timeout.seconds if timeout else None
            value_str = json.dumps(value)
            self.redis_client.set(key, value_str, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis缓存设置失败: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        删除Redis缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis缓存删除失败: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """
        清空所有Redis缓存
        
        Returns:
            是否清空成功
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis缓存清空失败: {str(e)}")
            return False


class MemoryCacheBackend(CacheBackend[Dict[str, Any]]):
    """内存缓存后端实现"""
    
    def __init__(self, cache_size: int = 1000):
        """
        初始化内存缓存后端
        
        Args:
            cache_size: 缓存最大条目数
        """
        from collections import OrderedDict
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.cache_size = cache_size
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取内存缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在返回None
        """
        if key in self.cache:
            # 移动到最近使用
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    async def set(self, key: str, value: Dict[str, Any], timeout: Optional[timedelta] = None) -> bool:
        """
        设置内存缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 缓存超时时间（内存缓存忽略此参数）
            
        Returns:
            是否设置成功
        """
        # 添加过期时间信息
        if timeout:
            value["expires_at"] = (datetime.now() + timeout).isoformat()
        
        # 添加到缓存
        self.cache[key] = value
        
        # 保持缓存大小
        if len(self.cache) > self.cache_size:
            # 删除最旧的条目
            self.cache.popitem(last=False)
        
        return True
    
    async def delete(self, key: str) -> bool:
        """
        删除内存缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        """
        清空所有内存缓存
        
        Returns:
            是否清空成功
        """
        self.cache.clear()
        return True


class CacheService:
    """缓存服务类"""
    
    def __init__(self, backend: CacheBackend[Dict[str, Any]]):
        """
        初始化缓存服务
        
        Args:
            backend: 缓存后端实例
        """
        self.backend = backend
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期返回None
        """
        value = await self.backend.get(key)
        if value:
            # 检查是否过期
            if "expires_at" in value:
                try:
                    expires_at = datetime.fromisoformat(value["expires_at"])
                    if datetime.now() > expires_at:
                        # 已过期，删除缓存
                        await self.backend.delete(key)
                        return None
                except ValueError:
                    # 时间格式错误，删除缓存
                    await self.backend.delete(key)
                    return None
            
            return value
        return None
    
    async def set(self, key: str, value: Dict[str, Any], timeout: Optional[timedelta] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 缓存超时时间
            
        Returns:
            是否设置成功
        """
        return await self.backend.set(key, value, timeout)
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        return await self.backend.delete(key)
    
    async def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否清空成功
        """
        return await self.backend.clear()
    
    async def get_or_set(self, key: str, func: Callable[[], Dict[str, Any]], 
                         timeout: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        获取缓存值，如果不存在则调用函数生成并缓存
        
        Args:
            key: 缓存键
            func: 生成缓存值的函数
            timeout: 缓存超时时间
            
        Returns:
            缓存值
        """
        # 尝试获取缓存
        value = await self.get(key)
        if value:
            return value
        
        # 缓存未命中，调用函数生成值
        value = func()
        
        # 设置缓存
        await self.set(key, value, timeout)
        
        return value


# 创建全局缓存服务实例
def get_cache_service() -> CacheService:
    """
    获取全局缓存服务实例
    
    Returns:
        缓存服务实例
    """
    from app.core.config import settings
    
    # 根据配置选择缓存后端
    if hasattr(settings, 'CACHE_BACKEND') and settings.CACHE_BACKEND == 'redis':
        # 使用Redis缓存后端
        return CacheService(RedisCacheBackend())
    else:
        # 默认使用内存缓存后端
        return CacheService(MemoryCacheBackend())


# 全局缓存服务实例
cache_service = get_cache_service()
