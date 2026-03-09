"""
模型管理缓存服务

提供模型管理相关的缓存功能，包括：
- 模型列表缓存
- 模型详情缓存
- 模型参数缓存
- 缓存键命名规范和版本管理
- 缓存失效策略
"""

import logging
import json
from typing import Any, Dict, List, Optional, Callable
from datetime import timedelta
from functools import wraps

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class ModelCacheKeys:
    """
    模型缓存键管理类
    
    定义缓存键的命名规范，确保键名一致性和可维护性。
    键名格式: model:{类型}:{标识}:{版本}
    """
    
    # 缓存键前缀
    PREFIX = "model"
    
    # 缓存版本号（用于批量失效）
    VERSION = "v1"
    
    # 缓存键模板
    KEYS = {
        # 模型列表缓存
        "all_models": "{prefix}:list:all:{version}",
        "supplier_models": "{prefix}:list:supplier:{supplier_id}:{version}",
        
        # 模型详情缓存
        "model_detail": "{prefix}:detail:{model_id}:{version}",
        "model_by_model_id": "{prefix}:detail:mid:{model_id_str}:{version}",
        
        # 模型参数缓存
        "model_parameters": "{prefix}:params:{model_id}:{version}",
        
        # 默认模型缓存
        "default_model": "{prefix}:default:{supplier_id}:{version}",
        
        # 模型分类缓存
        "model_categories": "{prefix}:categories:{model_id}:{version}",
    }
    
    @classmethod
    def get_key(cls, key_type: str, **kwargs) -> str:
        """
        获取缓存键
        
        Args:
            key_type: 键类型
            **kwargs: 键参数
        
        Returns:
            格式化后的缓存键
        """
        template = cls.KEYS.get(key_type)
        if not template:
            raise ValueError(f"未知的缓存键类型: {key_type}")
        
        return template.format(
            prefix=cls.PREFIX,
            version=cls.VERSION,
            **kwargs
        )
    
    @classmethod
    def get_pattern(cls, key_type: str, **kwargs) -> str:
        """
        获取缓存键模式（用于批量删除）
        
        Args:
            key_type: 键类型
            **kwargs: 键参数
        
        Returns:
            格式化后的缓存键模式
        """
        template = cls.KEYS.get(key_type)
        if not template:
            raise ValueError(f"未知的缓存键类型: {key_type}")
        
        # 将所有参数替换为通配符
        pattern = template.format(
            prefix=cls.PREFIX,
            version="*",
            **{k: "*" for k in kwargs}
        )
        
        return pattern


class ModelCacheService:
    """
    模型缓存服务类
    
    提供模型数据的缓存功能，支持Redis和内存缓存。
    实现缓存预热、失效策略等功能。
    """
    
    # 缓存过期时间配置（秒）
    TTL_CONFIG = {
        "model_list": 300,        # 模型列表缓存5分钟
        "model_detail": 600,      # 模型详情缓存10分钟
        "model_parameters": 600,  # 模型参数缓存10分钟
        "default_model": 300,     # 默认模型缓存5分钟
    }
    
    def __init__(self):
        """初始化模型缓存服务"""
        self.redis_client = get_redis()
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
    
    # ==================== 缓存读取操作 ====================
    
    async def get_all_models(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取所有模型的缓存
        
        Returns:
            模型列表，不存在时返回None
        """
        key = ModelCacheKeys.get_key("all_models")
        return await self._get(key)
    
    async def get_supplier_models(
        self,
        supplier_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取供应商模型列表的缓存
        
        Args:
            supplier_id: 供应商ID
        
        Returns:
            模型列表，不存在时返回None
        """
        key = ModelCacheKeys.get_key("supplier_models", supplier_id=supplier_id)
        return await self._get(key)
    
    async def get_model_detail(
        self,
        model_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取模型详情的缓存
        
        Args:
            model_id: 模型ID
        
        Returns:
            模型详情，不存在时返回None
        """
        key = ModelCacheKeys.get_key("model_detail", model_id=model_id)
        return await self._get(key)
    
    async def get_model_by_model_id(
        self,
        model_id_str: str
    ) -> Optional[Dict[str, Any]]:
        """
        根据模型标识符获取模型缓存
        
        Args:
            model_id_str: 模型标识符
        
        Returns:
            模型详情，不存在时返回None
        """
        key = ModelCacheKeys.get_key("model_by_model_id", model_id_str=model_id_str)
        return await self._get(key)
    
    async def get_model_parameters(
        self,
        model_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取模型参数的缓存
        
        Args:
            model_id: 模型ID
        
        Returns:
            参数列表，不存在时返回None
        """
        key = ModelCacheKeys.get_key("model_parameters", model_id=model_id)
        return await self._get(key)
    
    async def get_default_model(
        self,
        supplier_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取默认模型的缓存
        
        Args:
            supplier_id: 供应商ID（可选）
        
        Returns:
            默认模型详情，不存在时返回None
        """
        supplier_key = supplier_id if supplier_id else "global"
        key = ModelCacheKeys.get_key("default_model", supplier_id=supplier_key)
        return await self._get(key)
    
    # ==================== 缓存写入操作 ====================
    
    async def set_all_models(
        self,
        models: List[Dict[str, Any]]
    ) -> bool:
        """
        设置所有模型的缓存
        
        Args:
            models: 模型列表
        
        Returns:
            是否设置成功
        """
        key = ModelCacheKeys.get_key("all_models")
        ttl = self.TTL_CONFIG["model_list"]
        return await self._set(key, models, ttl)
    
    async def set_supplier_models(
        self,
        supplier_id: int,
        models: List[Dict[str, Any]]
    ) -> bool:
        """
        设置供应商模型列表的缓存
        
        Args:
            supplier_id: 供应商ID
            models: 模型列表
        
        Returns:
            是否设置成功
        """
        key = ModelCacheKeys.get_key("supplier_models", supplier_id=supplier_id)
        ttl = self.TTL_CONFIG["model_list"]
        return await self._set(key, models, ttl)
    
    async def set_model_detail(
        self,
        model_id: int,
        model: Dict[str, Any]
    ) -> bool:
        """
        设置模型详情的缓存
        
        Args:
            model_id: 模型ID
            model: 模型详情
        
        Returns:
            是否设置成功
        """
        key = ModelCacheKeys.get_key("model_detail", model_id=model_id)
        ttl = self.TTL_CONFIG["model_detail"]
        return await self._set(key, model, ttl)
    
    async def set_model_parameters(
        self,
        model_id: int,
        parameters: List[Dict[str, Any]]
    ) -> bool:
        """
        设置模型参数的缓存
        
        Args:
            model_id: 模型ID
            parameters: 参数列表
        
        Returns:
            是否设置成功
        """
        key = ModelCacheKeys.get_key("model_parameters", model_id=model_id)
        ttl = self.TTL_CONFIG["model_parameters"]
        return await self._set(key, parameters, ttl)
    
    async def set_default_model(
        self,
        model: Dict[str, Any],
        supplier_id: Optional[int] = None
    ) -> bool:
        """
        设置默认模型的缓存
        
        Args:
            model: 默认模型详情
            supplier_id: 供应商ID（可选）
        
        Returns:
            是否设置成功
        """
        supplier_key = supplier_id if supplier_id else "global"
        key = ModelCacheKeys.get_key("default_model", supplier_id=supplier_key)
        ttl = self.TTL_CONFIG["default_model"]
        return await self._set(key, model, ttl)
    
    # ==================== 缓存失效操作 ====================
    
    async def invalidate_model(self, model_id: int) -> bool:
        """
        使指定模型相关的所有缓存失效
        
        Args:
            model_id: 模型ID
        
        Returns:
            是否失效成功
        """
        keys_to_delete = [
            ModelCacheKeys.get_key("model_detail", model_id=model_id),
            ModelCacheKeys.get_key("model_parameters", model_id=model_id),
        ]
        
        return await self._delete_keys(keys_to_delete)
    
    async def invalidate_supplier_models(self, supplier_id: int) -> bool:
        """
        使指定供应商的模型列表缓存失效
        
        Args:
            supplier_id: 供应商ID
        
        Returns:
            是否失效成功
        """
        keys_to_delete = [
            ModelCacheKeys.get_key("all_models"),
            ModelCacheKeys.get_key("supplier_models", supplier_id=supplier_id),
            ModelCacheKeys.get_key("default_model", supplier_id=supplier_id),
        ]
        
        return await self._delete_keys(keys_to_delete)
    
    async def invalidate_all_models(self) -> bool:
        """
        使所有模型列表缓存失效
        
        Returns:
            是否失效成功
        """
        if self.redis_client:
            try:
                # 使用模式匹配删除所有模型列表缓存
                pattern = f"{ModelCacheKeys.PREFIX}:list:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                
                # 删除默认模型缓存
                default_pattern = f"{ModelCacheKeys.PREFIX}:default:*"
                default_keys = self.redis_client.keys(default_pattern)
                if default_keys:
                    self.redis_client.delete(*default_keys)
                
                return True
            except Exception as e:
                logger.error(f"Redis缓存批量失效失败: {str(e)}")
                return False
        
        # 内存缓存清空
        self._memory_cache.clear()
        return True
    
    # ==================== 缓存预热 ====================
    
    async def warm_up(
        self,
        model_service: Any
    ) -> bool:
        """
        缓存预热：预先加载常用数据到缓存
        
        Args:
            model_service: 模型管理服务实例
        
        Returns:
            是否预热成功
        """
        try:
            # 预热所有模型列表
            models, _ = model_service.get_all_models(skip=0, limit=1000)
            await self.set_all_models([m.model_dump() for m in models])
            
            logger.info("模型缓存预热完成")
            return True
            
        except Exception as e:
            logger.error(f"模型缓存预热失败: {str(e)}")
            return False
    
    # ==================== 底层缓存操作 ====================
    
    async def _get(self, key: str) -> Optional[Any]:
        """
        底层缓存获取操作
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值，不存在时返回None
        """
        # 优先使用Redis
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis缓存获取失败，降级到内存缓存: {str(e)}")
        
        # 降级到内存缓存
        return self._memory_cache.get(key)
    
    async def _set(
        self,
        key: str,
        value: Any,
        ttl: int
    ) -> bool:
        """
        底层缓存设置操作
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        
        Returns:
            是否设置成功
        """
        success = True
        
        # 写入Redis
        if self.redis_client:
            try:
                value_str = json.dumps(value, ensure_ascii=False, default=str)
                self.redis_client.set(key, value_str, ex=ttl)
            except Exception as e:
                logger.warning(f"Redis缓存设置失败: {str(e)}")
                success = False
        
        # 同时写入内存缓存（作为备份）
        self._memory_cache[key] = value
        
        return success
    
    async def _delete_keys(self, keys: List[str]) -> bool:
        """
        批量删除缓存键
        
        Args:
            keys: 要删除的键列表
        
        Returns:
            是否删除成功
        """
        success = True
        
        # 从Redis删除
        if self.redis_client:
            try:
                for key in keys:
                    self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis缓存删除失败: {str(e)}")
                success = False
        
        # 从内存缓存删除
        for key in keys:
            self._memory_cache.pop(key, None)
        
        return success


def cached_model(
    key_type: str,
    ttl_config_key: str = "model_detail"
):
    """
    模型缓存装饰器
    
    自动缓存函数返回值，并在缓存不存在时调用原函数获取数据。
    
    Args:
        key_type: 缓存键类型
        ttl_config_key: TTL配置键
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取缓存服务实例
            cache_service = ModelCacheService()
            
            # 构建缓存键
            cache_key = ModelCacheKeys.get_key(key_type, **kwargs)
            
            # 尝试从缓存获取
            cached_value = await cache_service._get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 缓存不存在，调用原函数
            result = await func(*args, **kwargs)
            
            # 写入缓存
            if result is not None:
                ttl = ModelCacheService.TTL_CONFIG.get(ttl_config_key, 300)
                await cache_service._set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator


# 创建全局缓存服务实例
model_cache_service = ModelCacheService()
