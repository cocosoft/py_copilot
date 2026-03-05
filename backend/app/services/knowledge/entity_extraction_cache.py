"""实体提取缓存服务

提供实体提取结果的缓存功能，减少重复调用LLM，提高性能并降低成本。
"""
import hashlib
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EntityExtractionCache:
    """实体提取结果缓存
    
    使用内存缓存 + 可选的Redis缓存，提供两级缓存机制。
    """
    
    # 内存缓存
    _memory_cache = {}
    _cache_timestamps = {}
    
    # 缓存配置
    CACHE_PREFIX = "entity_extraction:"
    DEFAULT_TTL = 3600  # 默认1小时
    MAX_MEMORY_CACHE_SIZE = 1000  # 最大内存缓存条目数
    
    @staticmethod
    def _generate_cache_key(text: str) -> str:
        """生成缓存键
        
        使用文本的MD5哈希作为缓存键，确保相同文本产生相同的键。
        
        Args:
            text: 输入文本
            
        Returns:
            缓存键
        """
        # 标准化文本（去除首尾空格，统一换行符）
        normalized_text = text.strip().replace('\r\n', '\n').replace('\r', '\n')
        text_hash = hashlib.md5(normalized_text.encode('utf-8')).hexdigest()
        return f"{EntityExtractionCache.CACHE_PREFIX}{text_hash}"
    
    @staticmethod
    def _is_cache_valid(timestamp: datetime, ttl: int) -> bool:
        """检查缓存是否有效
        
        Args:
            timestamp: 缓存时间戳
            ttl: 有效期（秒）
            
        Returns:
            是否有效
        """
        if timestamp is None:
            return False
        return datetime.now() - timestamp < timedelta(seconds=ttl)
    
    @staticmethod
    async def get_cached_result(text: str, use_redis: bool = True) -> Optional[Tuple[List[Dict], List[Dict]]]:
        """获取缓存的提取结果
        
        先检查内存缓存，再检查Redis缓存（如果启用）。
        
        Args:
            text: 输入文本
            use_redis: 是否使用Redis缓存
            
        Returns:
            (实体列表, 关系列表) 或 None
        """
        cache_key = EntityExtractionCache._generate_cache_key(text)
        
        # 1. 检查内存缓存
        if cache_key in EntityExtractionCache._memory_cache:
            timestamp = EntityExtractionCache._cache_timestamps.get(cache_key)
            if EntityExtractionCache._is_cache_valid(timestamp, EntityExtractionCache.DEFAULT_TTL):
                logger.debug(f"内存缓存命中: {cache_key[:16]}...")
                return EntityExtractionCache._memory_cache[cache_key]
            else:
                # 缓存过期，清理
                del EntityExtractionCache._memory_cache[cache_key]
                del EntityExtractionCache._cache_timestamps[cache_key]
        
        # 2. 检查Redis缓存
        if use_redis:
            try:
                from app.services.redis_service import redis_service
                cached_data = await redis_service.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    result = (data.get('entities', []), data.get('relationships', []))
                    
                    # 同时更新内存缓存
                    EntityExtractionCache._update_memory_cache(cache_key, result)
                    
                    logger.debug(f"Redis缓存命中: {cache_key[:16]}...")
                    return result
            except Exception as e:
                logger.warning(f"Redis缓存读取失败: {e}")
        
        return None
    
    @staticmethod
    def _update_memory_cache(cache_key: str, result: Tuple[List[Dict], List[Dict]]):
        """更新内存缓存
        
        Args:
            cache_key: 缓存键
            result: 缓存结果
        """
        # 清理过期缓存
        EntityExtractionCache._cleanup_expired_cache()
        
        # 如果内存缓存已满，清理最旧的条目
        if len(EntityExtractionCache._memory_cache) >= EntityExtractionCache.MAX_MEMORY_CACHE_SIZE:
            EntityExtractionCache._cleanup_oldest_cache(100)  # 清理100个最旧的
        
        # 添加新缓存
        EntityExtractionCache._memory_cache[cache_key] = result
        EntityExtractionCache._cache_timestamps[cache_key] = datetime.now()
    
    @staticmethod
    def _cleanup_expired_cache():
        """清理过期的内存缓存"""
        now = datetime.now()
        expired_keys = []
        
        for key, timestamp in EntityExtractionCache._cache_timestamps.items():
            if now - timestamp > timedelta(seconds=EntityExtractionCache.DEFAULT_TTL):
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in EntityExtractionCache._memory_cache:
                del EntityExtractionCache._memory_cache[key]
            if key in EntityExtractionCache._cache_timestamps:
                del EntityExtractionCache._cache_timestamps[key]
        
        if expired_keys:
            logger.debug(f"清理 {len(expired_keys)} 个过期缓存")
    
    @staticmethod
    def _cleanup_oldest_cache(count: int):
        """清理最旧的缓存条目
        
        Args:
            count: 清理数量
        """
        # 按时间戳排序
        sorted_items = sorted(
            EntityExtractionCache._cache_timestamps.items(),
            key=lambda x: x[1]
        )
        
        # 删除最旧的
        for key, _ in sorted_items[:count]:
            if key in EntityExtractionCache._memory_cache:
                del EntityExtractionCache._memory_cache[key]
            if key in EntityExtractionCache._cache_timestamps:
                del EntityExtractionCache._cache_timestamps[key]
        
        logger.debug(f"清理 {count} 个最旧缓存")
    
    @staticmethod
    async def cache_result(text: str, entities: List[Dict], relationships: List[Dict],
                          use_redis: bool = True, ttl: int = None):
        """缓存提取结果
        
        Args:
            text: 输入文本
            entities: 实体列表
            relationships: 关系列表
            use_redis: 是否使用Redis缓存
            ttl: 有效期（秒），默认使用DEFAULT_TTL
        """
        cache_key = EntityExtractionCache._generate_cache_key(text)
        result = (entities, relationships)
        
        # 1. 更新内存缓存
        EntityExtractionCache._update_memory_cache(cache_key, result)
        
        # 2. 更新Redis缓存
        if use_redis:
            try:
                from app.services.redis_service import redis_service
                
                data = {
                    'entities': entities,
                    'relationships': relationships,
                    'cached_at': datetime.now().isoformat()
                }
                
                await redis_service.set(
                    cache_key,
                    json.dumps(data, ensure_ascii=False),
                    expire=ttl or EntityExtractionCache.DEFAULT_TTL
                )
                logger.debug(f"结果已缓存到Redis: {cache_key[:16]}...")
            except Exception as e:
                logger.warning(f"Redis缓存写入失败: {e}")
    
    @staticmethod
    async def invalidate_cache(text: str = None, use_redis: bool = True):
        """使缓存失效
        
        Args:
            text: 特定文本的缓存，如果为None则清空所有缓存
            use_redis: 是否清理Redis缓存
        """
        if text:
            cache_key = EntityExtractionCache._generate_cache_key(text)
            
            # 清理内存缓存
            if cache_key in EntityExtractionCache._memory_cache:
                del EntityExtractionCache._memory_cache[cache_key]
            if cache_key in EntityExtractionCache._cache_timestamps:
                del EntityExtractionCache._cache_timestamps[cache_key]
            
            # 清理Redis缓存
            if use_redis:
                try:
                    from app.services.redis_service import redis_service
                    await redis_service.delete(cache_key)
                except Exception as e:
                    logger.warning(f"Redis缓存删除失败: {e}")
            
            logger.info(f"缓存已失效: {cache_key[:16]}...")
        else:
            # 清空所有缓存
            EntityExtractionCache._memory_cache.clear()
            EntityExtractionCache._cache_timestamps.clear()
            
            if use_redis:
                try:
                    from app.services.redis_service import redis_service
                    # 删除所有以CACHE_PREFIX开头的键
                    # 注意：这可能需要Redis的SCAN命令来安全地删除
                    logger.info("请手动清理Redis中所有以 'entity_extraction:' 开头的键")
                except Exception as e:
                    logger.warning(f"Redis缓存清理失败: {e}")
            
            logger.info("所有缓存已清空")
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        EntityExtractionCache._cleanup_expired_cache()
        
        return {
            "memory_cache_size": len(EntityExtractionCache._memory_cache),
            "max_memory_cache_size": EntityExtractionCache.MAX_MEMORY_CACHE_SIZE,
            "default_ttl": EntityExtractionCache.DEFAULT_TTL,
            "cache_prefix": EntityExtractionCache.CACHE_PREFIX
        }


# 便捷函数

async def get_cached_entities(text: str) -> Optional[Tuple[List[Dict], List[Dict]]]:
    """获取缓存的实体提取结果"""
    return await EntityExtractionCache.get_cached_result(text)


async def cache_entities(text: str, entities: List[Dict], relationships: List[Dict]):
    """缓存实体提取结果"""
    await EntityExtractionCache.cache_result(text, entities, relationships)


async def clear_cache(text: str = None):
    """清除缓存"""
    await EntityExtractionCache.invalidate_cache(text)
