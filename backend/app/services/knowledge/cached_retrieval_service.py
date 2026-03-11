"""
增强版检索服务 - 集成查询缓存

在原有检索服务基础上，集成 QueryCacheManager 实现：
- 缓存命中率 > 80%
- 查询响应时间减少 30%
- 支持缓存失效策略
- 缓存更新不影响查询

任务编号: BE-002
阶段: Phase 1 - 基础优化期
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Callable

from app.services.knowledge.retrieval_service import RetrievalService, AdvancedRetrievalService
from app.services.knowledge.query_cache_manager import (
    QueryCacheManager,
    CacheEvictionStrategy,
    query_cache_manager
)
from app.services.knowledge.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class CachedRetrievalService:
    """
    带缓存的检索服务
    
    为向量检索提供高性能缓存支持，显著提升查询响应速度。
    """
    
    def __init__(
        self,
        cache_manager: Optional[QueryCacheManager] = None,
        cache_ttl: int = 3600,  # 1小时
        enable_cache: bool = True
    ):
        """
        初始化带缓存的检索服务
        
        Args:
            cache_manager: 缓存管理器实例
            cache_ttl: 默认缓存过期时间（秒）
            enable_cache: 是否启用缓存
        """
        self.retrieval_service = RetrievalService()
        self.chroma_service = ChromaService()
        self.cache_manager = cache_manager or query_cache_manager
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache
        
        logger.info(
            f"带缓存的检索服务初始化完成: "
            f"enable_cache={enable_cache}, ttl={cache_ttl}s"
        )
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        knowledge_base_id: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        搜索文档（带缓存）
        
        Args:
            query: 查询文本
            limit: 返回结果数量
            knowledge_base_id: 知识库ID过滤
            use_cache: 是否使用缓存
            
        Returns:
            搜索结果列表
        """
        if not self.enable_cache or not use_cache:
            # 不使用缓存，直接查询
            return self.retrieval_service.search_documents(
                query, limit, knowledge_base_id
            )
        
        start_time = time.time()
        
        # 定义查询函数
        def fetch_documents():
            return self.retrieval_service.search_documents(
                query, limit, knowledge_base_id
            )
        
        # 使用缓存
        results, from_cache = await self.cache_manager.get_or_set(
            query=query,
            fetch_func=fetch_documents,
            knowledge_base_id=knowledge_base_id,
            limit=limit,
            ttl=self.cache_ttl
        )
        
        elapsed_time = time.time() - start_time
        
        if from_cache:
            logger.info(
                f"缓存命中: query='{query[:50]}...', "
                f"results={len(results)}, time={elapsed_time:.3f}s"
            )
        else:
            logger.info(
                f"缓存未命中: query='{query[:50]}...', "
                f"results={len(results)}, time={elapsed_time:.3f}s"
            )
        
        return results
    
    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        相似度搜索（带缓存）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            use_cache: 是否使用缓存
            
        Returns:
            搜索结果列表
        """
        if not self.enable_cache or not use_cache:
            return self.chroma_service.search_similar(query, top_k, filters)
        
        start_time = time.time()
        
        # 定义查询函数
        def fetch_similar():
            return self.chroma_service.search_similar(query, top_k, filters)
        
        # 使用缓存
        results, from_cache = await self.cache_manager.get_or_set(
            query=query,
            fetch_func=fetch_similar,
            filters=filters,
            limit=top_k,
            ttl=self.cache_ttl
        )
        
        elapsed_time = time.time() - start_time
        
        if from_cache:
            logger.debug(
                f"相似度搜索缓存命中: query='{query[:50]}...', "
                f"time={elapsed_time:.3f}s"
            )
        
        return results
    
    async def invalidate_cache(
        self,
        query: Optional[str] = None,
        knowledge_base_id: Optional[int] = None,
        pattern: Optional[str] = None
    ) -> int:
        """
        使缓存失效
        
        Args:
            query: 特定查询
            knowledge_base_id: 特定知识库
            pattern: 匹配模式
            
        Returns:
            失效的缓存数量
        """
        count = await self.cache_manager.invalidate(
            query=query,
            knowledge_base_id=knowledge_base_id,
            pattern=pattern
        )
        
        logger.info(f"已使 {count} 个缓存失效")
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        return self.cache_manager.get_stats()
    
    def reset_cache_stats(self):
        """重置缓存统计"""
        self.cache_manager.reset_stats()
        logger.info("缓存统计已重置")


class CachedAdvancedRetrievalService:
    """
    带缓存的高级检索服务
    
    为高级检索功能提供缓存支持，包括混合搜索、重排序等。
    """
    
    def __init__(
        self,
        cache_manager: Optional[QueryCacheManager] = None,
        cache_ttl: int = 1800,  # 30分钟（高级搜索缓存时间较短）
        enable_cache: bool = True
    ):
        """
        初始化带缓存的高级检索服务
        
        Args:
            cache_manager: 缓存管理器实例
            cache_ttl: 默认缓存过期时间（秒）
            enable_cache: 是否启用缓存
        """
        self.advanced_service = AdvancedRetrievalService()
        self.chroma_service = ChromaService()
        self.cache_manager = cache_manager or query_cache_manager
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache
        
        logger.info(
            f"带缓存的高级检索服务初始化完成: "
            f"enable_cache={enable_cache}, ttl={cache_ttl}s"
        )
    
    async def advanced_search(
        self,
        query: str,
        n_results: int = 10,
        knowledge_base_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "relevance",
        entity_filter: Optional[Dict[str, Any]] = None,
        use_rerank: bool = True,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        高级搜索（带缓存）
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            knowledge_base_id: 知识库ID
            tags: 标签过滤
            filters: 其他过滤条件
            sort_by: 排序方式
            entity_filter: 实体过滤
            use_rerank: 是否使用重排序
            use_cache: 是否使用缓存
            
        Returns:
            搜索结果列表
        """
        if not self.enable_cache or not use_cache:
            return self.advanced_service.advanced_search(
                query, n_results, knowledge_base_id, tags, filters,
                sort_by, entity_filter, use_rerank
            )
        
        start_time = time.time()
        
        # 定义查询函数
        def fetch_advanced():
            return self.advanced_service.advanced_search(
                query, n_results, knowledge_base_id, tags, filters,
                sort_by, entity_filter, use_rerank
            )
        
        # 使用缓存（包含所有参数）
        results, from_cache = await self.cache_manager.get_or_set(
            query=query,
            fetch_func=fetch_advanced,
            knowledge_base_id=knowledge_base_id,
            filters={
                "tags": tags,
                "entity_filter": entity_filter,
                "sort_by": sort_by,
                "use_rerank": use_rerank,
                **(filters or {})
            },
            limit=n_results,
            ttl=self.cache_ttl
        )
        
        elapsed_time = time.time() - start_time
        
        if from_cache:
            logger.info(
                f"高级搜索缓存命中: query='{query[:50]}...', "
                f"results={len(results)}, time={elapsed_time:.3f}s"
            )
        else:
            logger.info(
                f"高级搜索缓存未命中: query='{query[:50]}...', "
                f"results={len(results)}, time={elapsed_time:.3f}s"
            )
        
        return results
    
    async def hybrid_search(
        self,
        query: str,
        n_results: int = 10,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7,
        use_cache: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        混合搜索（带缓存）
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            keyword_weight: 关键词权重
            vector_weight: 向量权重
            use_cache: 是否使用缓存
            **kwargs: 其他参数
            
        Returns:
            搜索结果列表
        """
        if not self.enable_cache or not use_cache:
            return self.advanced_service.hybrid_search(
                query, n_results, keyword_weight, vector_weight, **kwargs
            )
        
        start_time = time.time()
        
        # 定义查询函数
        def fetch_hybrid():
            return self.advanced_service.hybrid_search(
                query, n_results, keyword_weight, vector_weight, **kwargs
            )
        
        # 使用缓存
        results, from_cache = await self.cache_manager.get_or_set(
            query=query,
            fetch_func=fetch_hybrid,
            filters={
                "keyword_weight": keyword_weight,
                "vector_weight": vector_weight,
                "search_type": "hybrid",
                **kwargs
            },
            limit=n_results,
            ttl=self.cache_ttl
        )
        
        elapsed_time = time.time() - start_time
        
        if from_cache:
            logger.debug(
                f"混合搜索缓存命中: query='{query[:50]}...', "
                f"time={elapsed_time:.3f}s"
            )
        
        return results
    
    async def invalidate_cache(
        self,
        query: Optional[str] = None,
        knowledge_base_id: Optional[int] = None,
        pattern: Optional[str] = None
    ) -> int:
        """
        使缓存失效
        
        Args:
            query: 特定查询
            knowledge_base_id: 特定知识库
            pattern: 匹配模式
            
        Returns:
            失效的缓存数量
        """
        count = await self.cache_manager.invalidate(
            query=query,
            knowledge_base_id=knowledge_base_id,
            pattern=pattern
        )
        
        logger.info(f"已使 {count} 个高级搜索缓存失效")
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        return self.cache_manager.get_stats()
    
    def reset_cache_stats(self):
        """重置缓存统计"""
        self.cache_manager.reset_stats()
        logger.info("高级搜索缓存统计已重置")


# 缓存预热功能

class CacheWarmer:
    """缓存预热器"""
    
    def __init__(self, cache_manager: Optional[QueryCacheManager] = None):
        """
        初始化缓存预热器
        
        Args:
            cache_manager: 缓存管理器实例
        """
        self.cache_manager = cache_manager or query_cache_manager
        self.warm_queries: List[Dict[str, Any]] = []
    
    def add_warm_query(
        self,
        query: str,
        knowledge_base_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ):
        """
        添加预热查询
        
        Args:
            query: 查询文本
            knowledge_base_id: 知识库ID
            filters: 过滤条件
            limit: 结果数量
        """
        self.warm_queries.append({
            "query": query,
            "knowledge_base_id": knowledge_base_id,
            "filters": filters,
            "limit": limit
        })
    
    async def warm_cache(
        self,
        fetch_func: Callable,
        ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        执行缓存预热
        
        Args:
            fetch_func: 获取数据的函数
            ttl: 缓存过期时间
            
        Returns:
            预热结果统计
        """
        warmed_count = 0
        failed_count = 0
        
        logger.info(f"开始缓存预热，共 {len(self.warm_queries)} 个查询")
        
        for query_info in self.warm_queries:
            try:
                # 执行查询
                if asyncio.iscoroutinefunction(fetch_func):
                    results = await fetch_func(**query_info)
                else:
                    loop = asyncio.get_event_loop()
                    results = await loop.run_in_executor(None, fetch_func, **query_info)
                
                # 设置缓存
                await self.cache_manager.set(
                    query=query_info["query"],
                    data=results,
                    knowledge_base_id=query_info.get("knowledge_base_id"),
                    filters=query_info.get("filters"),
                    limit=query_info.get("limit", 10),
                    ttl=ttl
                )
                
                warmed_count += 1
                
            except Exception as e:
                logger.error(f"预热查询失败: {query_info}, error={e}")
                failed_count += 1
        
        logger.info(f"缓存预热完成: {warmed_count} 成功, {failed_count} 失败")
        
        return {
            "total": len(self.warm_queries),
            "warmed": warmed_count,
            "failed": failed_count
        }


# 便捷函数

async def cached_search(
    query: str,
    limit: int = 10,
    knowledge_base_id: Optional[int] = None,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    带缓存的文档搜索便捷函数
    
    Args:
        query: 查询文本
        limit: 返回结果数量
        knowledge_base_id: 知识库ID
        use_cache: 是否使用缓存
        
    Returns:
        搜索结果列表
    """
    service = CachedRetrievalService()
    return await service.search_documents(query, limit, knowledge_base_id, use_cache)


async def cached_advanced_search(
    query: str,
    n_results: int = 10,
    knowledge_base_id: Optional[int] = None,
    use_cache: bool = True,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    带缓存的高级搜索便捷函数
    
    Args:
        query: 查询文本
        n_results: 返回结果数量
        knowledge_base_id: 知识库ID
        use_cache: 是否使用缓存
        **kwargs: 其他参数
        
    Returns:
        搜索结果列表
    """
    service = CachedAdvancedRetrievalService()
    return await service.advanced_search(
        query, n_results, knowledge_base_id, use_cache=use_cache, **kwargs
    )


def get_cache_performance_report() -> Dict[str, Any]:
    """
    获取缓存性能报告
    
    Returns:
        性能报告字典
    """
    stats = query_cache_manager.get_stats()
    
    return {
        "hit_rate": f"{stats['hit_rate']:.1%}",
        "miss_rate": f"{stats['miss_rate']:.1%}",
        "total_requests": stats["total_requests"],
        "cache_hits": stats["cache_hits"],
        "cache_misses": stats["cache_misses"],
        "avg_query_time": f"{stats['avg_query_time']:.3f}s",
        "avg_cache_time": f"{stats['avg_cache_time']:.3f}s",
        "time_saved": f"{stats['time_saved']:.1f}s",
        "performance_improvement": (
            f"{((stats['avg_query_time'] - stats['avg_cache_time']) / stats['avg_query_time'] * 100):.1f}%"
            if stats['avg_query_time'] > 0 else "N/A"
        )
    }
