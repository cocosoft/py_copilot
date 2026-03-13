"""
查询缓存管理器使用示例

展示如何使用 QueryCacheManager 和 CachedRetrievalService 进行高效的查询缓存。

任务编号: BE-002
阶段: Phase 1 - 基础优化期
"""

import asyncio
import logging
import time
from typing import List, Dict, Any

from app.services.knowledge.query_cache_manager import (
    QueryCacheManager,
    CacheEvictionStrategy,
    CacheWarmer,
    cached_query
)
from app.services.knowledge.cached_retrieval_service import (
    CachedRetrievalService,
    CachedAdvancedRetrievalService,
    get_cache_performance_report
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本用法 ====================

async def example_basic_usage():
    """基本用法示例"""
    
    logger.info("=" * 50)
    logger.info("示例 1: 查询缓存基本用法")
    logger.info("=" * 50)
    
    # 创建缓存管理器
    cache_manager = QueryCacheManager(
        prefix="example:",
        default_ttl=300,  # 5分钟
        eviction_strategy=CacheEvictionStrategy.TTL
    )
    
    # 模拟查询函数
    def fetch_data(query: str) -> Dict[str, Any]:
        """模拟数据查询"""
        time.sleep(0.5)  # 模拟查询延迟
        return {
            "query": query,
            "results": [f"Result {i} for '{query}'" for i in range(5)],
            "timestamp": time.time()
        }
    
    query = "人工智能发展趋势"
    
    # 第一次查询（缓存未命中）
    logger.info("\n第一次查询（缓存未命中）:")
    start = time.time()
    result1, from_cache1 = await cache_manager.get_or_set(
        query=query,
        fetch_func=lambda: fetch_data(query),
        knowledge_base_id=1,
        limit=5
    )
    elapsed1 = time.time() - start
    logger.info(f"  来自缓存: {from_cache1}")
    logger.info(f"  耗时: {elapsed1:.3f}s")
    logger.info(f"  结果数: {len(result1['results'])}")
    
    # 第二次查询（缓存命中）
    logger.info("\n第二次查询（缓存命中）:")
    start = time.time()
    result2, from_cache2 = await cache_manager.get_or_set(
        query=query,
        fetch_func=lambda: fetch_data(query),
        knowledge_base_id=1,
        limit=5
    )
    elapsed2 = time.time() - start
    logger.info(f"  来自缓存: {from_cache2}")
    logger.info(f"  耗时: {elapsed2:.3f}s")
    logger.info(f"  结果数: {len(result2['results'])}")
    
    # 显示性能提升
    if elapsed1 > 0:
        improvement = (elapsed1 - elapsed2) / elapsed1 * 100
        logger.info(f"\n性能提升: {improvement:.1f}%")
    
    # 显示缓存统计
    stats = cache_manager.get_stats()
    logger.info(f"\n缓存统计:")
    logger.info(f"  命中率: {stats['hit_rate']:.1%}")
    logger.info(f"  总请求: {stats['total_requests']}")
    logger.info(f"  缓存命中: {stats['cache_hits']}")
    logger.info(f"  缓存未命中: {stats['cache_misses']}")


# ==================== 示例 2: 不同失效策略 ====================

async def example_eviction_strategies():
    """不同缓存失效策略示例"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 2: 缓存失效策略对比")
    logger.info("=" * 50)
    
    strategies = [
        CacheEvictionStrategy.TTL,
        CacheEvictionStrategy.LRU,
        CacheEvictionStrategy.LFU,
        CacheEvictionStrategy.FIFO
    ]
    
    for strategy in strategies:
        logger.info(f"\n策略: {strategy.value.upper()}")
        
        cache_manager = QueryCacheManager(
            prefix=f"example_{strategy.value}:",
            default_ttl=60,
            eviction_strategy=strategy,
            max_size=1024 * 1024  # 1MB
        )
        
        # 添加一些缓存数据
        for i in range(10):
            await cache_manager.set(
                query=f"query_{i}",
                data={"index": i, "data": "x" * 100},
                ttl=300
            )
        
        # 模拟访问（用于 LRU/LFU）
        if strategy in [CacheEvictionStrategy.LRU, CacheEvictionStrategy.LFU]:
            for _ in range(5):
                await cache_manager.get(query="query_0")
                await cache_manager.get(query="query_1")
                await cache_manager.get(query="query_2")
        
        stats = cache_manager.get_stats()
        logger.info(f"  本地缓存大小: {stats['local_cache_size']} 条目")
        logger.info(f"  本地缓存字节: {stats['local_cache_bytes']} bytes")


# ==================== 示例 3: 缓存预热 ====================

async def example_cache_warming():
    """缓存预热示例"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 3: 缓存预热")
    logger.info("=" * 50)
    
    cache_manager = QueryCacheManager(prefix="warmup:")
    warmer = CacheWarmer(cache_manager)
    
    # 添加预热查询
    warm_queries = [
        "机器学习基础",
        "深度学习算法",
        "自然语言处理",
        "计算机视觉",
        "强化学习"
    ]
    
    for query in warm_queries:
        warmer.add_warm_query(
            query=query,
            knowledge_base_id=1,
            limit=10
        )
    
    # 模拟查询函数
    def fetch_warm_data(query: str, knowledge_base_id: int = None, limit: int = 10):
        time.sleep(0.2)  # 模拟查询延迟
        return {
            "query": query,
            "knowledge_base_id": knowledge_base_id,
            "results": [f"Result {i}" for i in range(limit)]
        }
    
    # 执行预热
    logger.info("开始缓存预热...")
    result = await warmer.warm_cache(fetch_warm_data, ttl=600)
    
    logger.info(f"预热完成:")
    logger.info(f"  总查询: {result['total']}")
    logger.info(f"  成功: {result['warmed']}")
    logger.info(f"  失败: {result['failed']}")
    
    # 验证缓存
    logger.info("\n验证缓存命中:")
    for query in warm_queries[:3]:
        _, hit = await cache_manager.get(query=query, knowledge_base_id=1)
        logger.info(f"  '{query}': {'命中' if hit else '未命中'}")


# ==================== 示例 4: 缓存失效 ====================

async def example_cache_invalidation():
    """缓存失效示例"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 4: 缓存失效")
    logger.info("=" * 50)
    
    cache_manager = QueryCacheManager(prefix="invalidation:")
    
    # 添加一些缓存
    queries = ["query_a", "query_b", "query_c", "query_d", "query_e"]
    for query in queries:
        await cache_manager.set(
            query=query,
            data={"query": query, "value": f"data_for_{query}"},
            ttl=300
        )
    
    logger.info(f"添加了 {len(queries)} 个缓存")
    
    # 验证缓存存在
    for query in queries:
        _, hit = await cache_manager.get(query=query)
        logger.info(f"  '{query}': {'存在' if hit else '不存在'}")
    
    # 使特定查询失效
    logger.info("\n使 'query_b' 失效:")
    count = await cache_manager.invalidate(query="query_b")
    logger.info(f"  失效数量: {count}")
    
    # 验证
    _, hit = await cache_manager.get(query="query_b")
    logger.info(f"  'query_b' 现在: {'存在' if hit else '不存在'}")
    
    # 使匹配模式的缓存失效
    logger.info("\n使匹配 'query_' 模式的缓存失效:")
    count = await cache_manager.invalidate(pattern="*")
    logger.info(f"  失效数量: {count}")
    
    # 验证所有缓存已失效
    remaining = 0
    for query in queries:
        _, hit = await cache_manager.get(query=query)
        if hit:
            remaining += 1
    logger.info(f"  剩余缓存: {remaining}")


# ==================== 示例 5: 性能测试 ====================

async def example_performance_test():
    """缓存性能测试"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 5: 缓存性能测试")
    logger.info("=" * 50)
    
    cache_manager = QueryCacheManager(
        prefix="perf:",
        default_ttl=300
    )
    
    # 模拟慢查询
    def slow_query(query: str) -> Dict[str, Any]:
        time.sleep(0.1)  # 100ms 延迟
        return {
            "query": query,
            "results": list(range(100)),
            "metadata": {"count": 100}
        }
    
    num_queries = 100
    num_unique = 20
    
    # 生成查询（有重复）
    import random
    test_queries = [f"query_{i % num_unique}" for i in range(num_queries)]
    random.shuffle(test_queries)
    
    logger.info(f"执行 {num_queries} 次查询（{num_unique} 个唯一查询）")
    
    # 执行查询
    start_total = time.time()
    
    for query in test_queries:
        await cache_manager.get_or_set(
            query=query,
            fetch_func=lambda q=query: slow_query(q)
        )
    
    total_time = time.time() - start_total
    
    # 显示结果
    stats = cache_manager.get_stats()
    
    logger.info(f"\n性能测试结果:")
    logger.info(f"  总耗时: {total_time:.3f}s")
    logger.info(f"  平均每次查询: {total_time/num_queries*1000:.1f}ms")
    logger.info(f"  理论无缓存耗时: {num_queries * 0.1:.1f}s")
    logger.info(f"  实际节省时间: {num_queries * 0.1 - total_time:.1f}s")
    logger.info(f"  性能提升: {((num_queries * 0.1 - total_time) / (num_queries * 0.1) * 100):.1f}%")
    
    logger.info(f"\n缓存统计:")
    logger.info(f"  命中率: {stats['hit_rate']:.1%}")
    logger.info(f"  命中次数: {stats['cache_hits']}")
    logger.info(f"  未命中次数: {stats['cache_misses']}")
    logger.info(f"  平均查询时间: {stats['avg_query_time']:.3f}s")
    logger.info(f"  平均缓存时间: {stats['avg_cache_time']:.3f}s")


# ==================== 示例 6: 装饰器用法 ====================

async def example_decorator_usage():
    """装饰器用法示例"""
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 6: 装饰器用法")
    logger.info("=" * 50)
    
    cache_manager = QueryCacheManager(prefix="decorator:", default_ttl=300)
    
    # 使用装饰器缓存函数结果
    @cached_query(cache_manager, ttl=60)
    async def expensive_computation(query: str, multiplier: int = 1) -> Dict[str, Any]:
        """模拟耗时计算"""
        logger.info(f"  执行耗时计算: query='{query}', multiplier={multiplier}")
        await asyncio.sleep(0.3)  # 模拟耗时操作
        return {
            "query": query,
            "multiplier": multiplier,
            "result": len(query) * multiplier,
            "timestamp": time.time()
        }
    
    # 第一次调用
    logger.info("\n第一次调用:")
    start = time.time()
    result1 = await expensive_computation("测试查询", multiplier=2)
    logger.info(f"  耗时: {time.time() - start:.3f}s")
    logger.info(f"  结果: {result1}")
    
    # 第二次调用（应该使用缓存）
    logger.info("\n第二次调用（相同参数）:")
    start = time.time()
    result2 = await expensive_computation("测试查询", multiplier=2)
    logger.info(f"  耗时: {time.time() - start:.3f}s")
    logger.info(f"  结果: {result2}")
    
    # 第三次调用（不同参数）
    logger.info("\n第三次调用（不同参数）:")
    start = time.time()
    result3 = await expensive_computation("测试查询", multiplier=3)
    logger.info(f"  耗时: {time.time() - start:.3f}s")
    logger.info(f"  结果: {result3}")


# ==================== 示例 7: 实际应用场景 ====================

async def example_real_world_scenario():
    """
    实际应用场景：知识库搜索缓存
    
    展示如何在实际应用中使用查询缓存。
    """
    
    logger.info("\n" + "=" * 50)
    logger.info("示例 7: 实际应用场景 - 知识库搜索缓存")
    logger.info("=" * 50)
    
    # 创建带缓存的检索服务
    cached_service = CachedRetrievalService(
        cache_ttl=1800,  # 30分钟
        enable_cache=True
    )
    
    # 模拟搜索查询（实际应用中这里会调用真实的检索服务）
    def mock_search(query: str, limit: int, knowledge_base_id: int = None):
        """模拟搜索"""
        time.sleep(0.2)  # 模拟搜索延迟
        return [
            {
                "id": f"doc_{i}",
                "title": f"文档 {i}",
                "content": f"这是关于 '{query}' 的文档 {i} 内容...",
                "score": 0.95 - i * 0.05
            }
            for i in range(limit)
        ]
    
    # 替换实际的搜索方法
    cached_service.retrieval_service.search_documents = mock_search
    
    # 热门查询
    popular_queries = [
        "机器学习",
        "深度学习",
        "自然语言处理",
        "机器学习",  # 重复查询
        "计算机视觉",
        "深度学习",  # 重复查询
        "强化学习",
        "机器学习",  # 重复查询
    ]
    
    logger.info(f"执行 {len(popular_queries)} 次搜索查询")
    
    for i, query in enumerate(popular_queries):
        start = time.time()
        results = await cached_service.search_documents(
            query=query,
            limit=5,
            knowledge_base_id=1
        )
        elapsed = time.time() - start
        
        logger.info(f"  [{i+1}] '{query}': {len(results)} 结果, {elapsed*1000:.1f}ms")
    
    # 显示缓存性能报告
    logger.info("\n缓存性能报告:")
    report = get_cache_performance_report()
    for key, value in report.items():
        logger.info(f"  {key}: {value}")


# ==================== 主函数 ====================

async def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("查询缓存管理器使用示例")
    logger.info("=" * 60)
    
    try:
        await example_basic_usage()
        await example_eviction_strategies()
        await example_cache_warming()
        await example_cache_invalidation()
        await example_performance_test()
        await example_decorator_usage()
        await example_real_world_scenario()
        
        logger.info("\n" + "=" * 60)
        logger.info("所有示例运行完成!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
