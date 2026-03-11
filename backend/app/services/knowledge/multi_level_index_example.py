"""
多级索引服务使用示例 - 向量化管理模块优化

展示如何使用 MultiLevelIndexService 实现多级索引策略。

任务编号: BE-008
阶段: Phase 2 - 架构升级期
"""

import logging
import random
import time
from typing import List

from app.services.knowledge.multi_level_index_service import (
    MultiLevelIndexService,
    IndexSelector,
    IndexWarmer,
    IndexType,
    IndexStatus,
    DataDistribution,
    IndexLevel,
    IndexConfig,
    IndexStats,
    FlatIndex,
    HNSWIndex,
    create_multi_level_index,
    multi_level_index_service
)

from app.services.knowledge.vector_store_adapter import VectorDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 自动选择索引 ====================

def example_auto_index_selection():
    """自动选择索引示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 自动选择索引")
    logger.info("=" * 60)
    
    selector = IndexSelector()
    
    # 测试不同数据量下的索引选择
    test_cases = [
        (500, 384, DataDistribution.UNIFORM, "小数据集"),
        (5000, 384, DataDistribution.UNIFORM, "中等数据集"),
        (50000, 384, DataDistribution.CLUSTERED, "大数据集"),
        (200000, 768, DataDistribution.HIGH_DIM, "超大高维数据集"),
        (100, 384, DataDistribution.SPARSE, "稀疏小数据集")
    ]
    
    logger.info("\n自动索引选择结果:")
    for size, dim, dist, desc in test_cases:
        index_type = selector.select_index(size, dim, dist)
        params = selector.get_recommended_params(index_type, size, dim)
        
        logger.info(f"\n  {desc}:")
        logger.info(f"    数据量: {size}, 维度: {dim}, 分布: {dist.value}")
        logger.info(f"    推荐索引: {index_type.value}")
        logger.info(f"    推荐参数: {params}")


# ==================== 示例 2: 创建不同索引 ====================

def example_create_different_indexes():
    """创建不同索引示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 创建不同索引")
    logger.info("=" * 60)
    
    service = MultiLevelIndexService()
    
    # 生成测试数据
    def generate_documents(count: int, dimension: int) -> List[VectorDocument]:
        return [
            VectorDocument(
                id=f"doc_{i}",
                text=f"文档 {i}",
                embedding=[random.random() for _ in range(dimension)],
                metadata={"index": i, "category": f"cat_{i % 5}"}
            )
            for i in range(count)
        ]
    
    dimension = 128
    
    # 创建Flat索引
    logger.info("\n创建Flat索引...")
    flat_docs = generate_documents(500, dimension)
    flat_index = service.create_index(
        documents=flat_docs,
        dimension=dimension,
        index_type=IndexType.FLAT,
        index_id="flat_test"
    )
    logger.info(f"  状态: {flat_index.status.value}")
    logger.info(f"  文档数: {flat_index.stats.index_size}")
    
    # 创建HNSW索引
    logger.info("\n创建HNSW索引...")
    hnsw_docs = generate_documents(5000, dimension)
    hnsw_index = service.create_index(
        documents=hnsw_docs,
        dimension=dimension,
        index_type=IndexType.HNSW,
        index_id="hnsw_test"
    )
    logger.info(f"  状态: {hnsw_index.status.value}")
    logger.info(f"  文档数: {hnsw_index.stats.index_size}")
    
    # 自动选择索引
    logger.info("\n自动选择索引...")
    auto_docs = generate_documents(3000, dimension)
    auto_index = service.create_index(
        documents=auto_docs,
        dimension=dimension,
        index_type=None,  # 自动选择
        index_id="auto_test"
    )
    logger.info(f"  自动选择类型: {auto_index.config.index_type.value}")
    logger.info(f"  状态: {auto_index.status.value}")


# ==================== 示例 3: 索引搜索 ====================

def example_index_search():
    """索引搜索示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 索引搜索")
    logger.info("=" * 60)
    
    service = MultiLevelIndexService()
    
    # 创建测试数据
    dimension = 128
    documents = [
        VectorDocument(
            id=f"doc_{i}",
            text=f"这是关于主题 {i % 10} 的文档",
            embedding=[random.random() for _ in range(dimension)],
            metadata={"topic": i % 10, "length": random.randint(100, 1000)}
        )
        for i in range(1000)
    ]
    
    # 创建索引
    service.create_index(documents, dimension, index_id="search_test")
    
    # 生成查询向量
    query_vector = [random.random() for _ in range(dimension)]
    
    # 基本搜索
    logger.info("\n基本搜索:")
    results = service.search(query_vector, top_k=5, index_id="search_test")
    
    logger.info(f"  查询返回 {len(results)} 个结果:")
    for i, result in enumerate(results, 1):
        logger.info(f"    {i}. {result.id} (得分: {result.score:.4f})")
    
    # 带过滤的搜索
    logger.info("\n带过滤的搜索 (topic=3):")
    results = service.search(
        query_vector,
        top_k=5,
        filters={"topic": 3},
        index_id="search_test"
    )
    
    logger.info(f"  过滤后返回 {len(results)} 个结果")
    for result in results:
        logger.info(f"    - {result.id}: topic={result.metadata.get('topic')}")


# ==================== 示例 4: 索引预热 ====================

def example_index_warmup():
    """索引预热示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 索引预热")
    logger.info("=" * 60)
    
    # 创建带预热的服务
    service = MultiLevelIndexService(enable_warmup=True)
    
    # 创建测试数据
    dimension = 128
    documents = [
        VectorDocument(
            id=f"doc_{i}",
            text=f"文档 {i}",
            embedding=[random.random() for _ in range(dimension)]
        )
        for i in range(2000)
    ]
    
    # 创建索引（会自动预热）
    logger.info("创建索引并自动预热...")
    index = service.create_index(
        documents,
        dimension,
        index_type=IndexType.HNSW,
        index_id="warmup_test"
    )
    
    logger.info(f"  索引状态: {index.status.value}")
    logger.info(f"  访问次数: {index.stats.access_count}")
    
    # 手动预热
    logger.info("\n手动预热索引...")
    service.warmup_index("warmup_test")
    logger.info(f"  预热后访问次数: {index.stats.access_count}")


# ==================== 示例 5: 性能对比 ====================

def example_performance_comparison():
    """性能对比示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 性能对比 (Flat vs HNSW)")
    logger.info("=" * 60)
    
    dimension = 128
    data_sizes = [100, 500, 1000]
    
    for size in data_sizes:
        logger.info(f"\n数据量: {size}")
        
        # 生成数据
        documents = [
            VectorDocument(
                id=f"doc_{i}",
                text=f"文档 {i}",
                embedding=[random.random() for _ in range(dimension)]
            )
            for i in range(size)
        ]
        
        # 测试Flat索引
        flat_service = MultiLevelIndexService(enable_warmup=False)
        flat_start = time.time()
        flat_index = flat_service.create_index(
            documents,
            dimension,
            index_type=IndexType.FLAT,
            index_id=f"flat_{size}"
        )
        flat_build_time = (time.time() - flat_start) * 1000
        
        # 测试HNSW索引
        hnsw_service = MultiLevelIndexService(enable_warmup=False)
        hnsw_start = time.time()
        hnsw_index = hnsw_service.create_index(
            documents,
            dimension,
            index_type=IndexType.HNSW,
            index_id=f"hnsw_{size}"
        )
        hnsw_build_time = (time.time() - hnsw_start) * 1000
        
        # 测试查询性能
        query_times = 50
        query_vector = [random.random() for _ in range(dimension)]
        
        # Flat查询
        flat_query_start = time.time()
        for _ in range(query_times):
            flat_service.search(query_vector, top_k=10, index_id=f"flat_{size}")
        flat_query_time = (time.time() - flat_query_start) * 1000 / query_times
        
        # HNSW查询
        hnsw_query_start = time.time()
        for _ in range(query_times):
            hnsw_service.search(query_vector, top_k=10, index_id=f"hnsw_{size}")
        hnsw_query_time = (time.time() - hnsw_query_start) * 1000 / query_times
        
        logger.info(f"  Flat索引:")
        logger.info(f"    构建时间: {flat_build_time:.2f}ms")
        logger.info(f"    平均查询: {flat_query_time:.4f}ms")
        
        logger.info(f"  HNSW索引:")
        logger.info(f"    构建时间: {hnsw_build_time:.2f}ms")
        logger.info(f"    平均查询: {hnsw_query_time:.4f}ms")
        
        if flat_query_time > 0:
            speedup = flat_query_time / hnsw_query_time
            logger.info(f"  加速比: {speedup:.2f}x")


# ==================== 示例 6: 索引统计 ====================

def example_index_statistics():
    """索引统计示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 索引统计")
    logger.info("=" * 60)
    
    service = MultiLevelIndexService()
    
    # 创建多个索引
    dimension = 128
    
    for idx_type in [IndexType.FLAT, IndexType.HNSW]:
        documents = [
            VectorDocument(
                id=f"doc_{i}",
                text=f"文档 {i}",
                embedding=[random.random() for _ in range(dimension)]
            )
            for i in range(1000)
        ]
        
        service.create_index(
            documents,
            dimension,
            index_type=idx_type,
            index_id=f"stats_{idx_type.value}"
        )
    
    # 执行一些查询
    query_vector = [random.random() for _ in range(dimension)]
    for _ in range(10):
        service.search(query_vector, index_id="stats_flat")
        service.search(query_vector, index_id="stats_hnsw")
    
    # 获取统计
    logger.info("\n索引统计信息:")
    all_stats = service.get_all_stats()
    
    for index_id, stats in all_stats.items():
        logger.info(f"\n  {index_id}:")
        for key, value in stats.items():
            logger.info(f"    {key}: {value}")


# ==================== 示例 7: 多级索引策略 ====================

def example_multi_level_strategy():
    """多级索引策略示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 多级索引策略")
    logger.info("=" * 60)
    
    selector = IndexSelector()
    
    # 显示多级策略
    logger.info("\n多级索引策略:")
    levels = [
        IndexLevel(1, IndexType.FLAT, 1000, "小数据集"),
        IndexLevel(2, IndexType.HNSW, 10000, "中等数据集"),
        IndexLevel(3, IndexType.IVF, 100000, "大数据集"),
        IndexLevel(4, IndexType.IVF_PQ, float('inf'), "超大数据集")
    ]
    
    for level in levels:
        logger.info(f"\n  级别 {level.level}:")
        logger.info(f"    索引类型: {level.index_type.value}")
        logger.info(f"    数据阈值: {level.threshold}")
        logger.info(f"    描述: {level.description}")
    
    # 测试数据增长时的索引切换
    logger.info("\n数据增长时的索引选择:")
    
    data_sizes = [100, 800, 3000, 15000, 200000]
    
    for size in data_sizes:
        index_type = selector.select_index(size, 384)
        logger.info(f"  数据量 {size:>6} -> {index_type.value}")


# ==================== 示例 8: 基准测试 ====================

def example_benchmark():
    """基准测试示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 基准测试")
    logger.info("=" * 60)
    
    service = MultiLevelIndexService()
    
    # 创建测试数据
    dimension = 128
    doc_count = 1000
    
    documents = [
        VectorDocument(
            id=f"doc_{i}",
            text=f"文档 {i}",
            embedding=[random.random() for _ in range(dimension)]
        )
        for i in range(doc_count)
    ]
    
    service.create_index(documents, dimension, index_id="benchmark")
    
    # 生成查询向量和真实结果
    query_count = 20
    query_vectors = [[random.random() for _ in range(dimension)] for _ in range(query_count)]
    
    # 使用暴力搜索获取真实结果
    flat_service = MultiLevelIndexService()
    flat_service.create_index(documents, dimension, index_type=IndexType.FLAT)
    
    ground_truth = []
    for query in query_vectors:
        results = flat_service.search(query, top_k=5)
        ground_truth.append([r.id for r in results])
    
    # 运行基准测试
    logger.info("\n运行基准测试...")
    results = service.benchmark_index(query_vectors, ground_truth, "benchmark")
    
    logger.info("\n测试结果:")
    for key, value in results.items():
        logger.info(f"  {key}: {value}")


# ==================== 示例 9: 实际应用场景 ====================

def example_real_world_scenario():
    """
    实际应用场景：大规模文档检索系统
    
    展示如何在实际应用中使用多级索引服务。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 实际应用场景 - 大规模文档检索系统")
    logger.info("=" * 60)
    
    logger.info("\n场景描述:")
    logger.info("  - 企业知识库系统")
    logger.info("  - 100万+ 文档")
    logger.info("  - 需要毫秒级响应")
    logger.info("  - 高并发查询")
    
    # 模拟不同规模的数据
    scenarios = [
        (1000, "部门级知识库"),
        (10000, "公司级知识库"),
        (100000, "集团级知识库"),
        (500000, "大型平台知识库")
    ]
    
    logger.info("\n不同规模的索引策略:")
    
    for size, desc in scenarios:
        selector = IndexSelector()
        index_type = selector.select_index(size, 768)
        params = selector.get_recommended_params(index_type, size, 768)
        
        logger.info(f"\n  {desc} ({size} 文档):")
        logger.info(f"    推荐索引: {index_type.value}")
        logger.info(f"    参数配置: {params}")
        
        # 估算性能
        if index_type == IndexType.FLAT:
            qps = 10
        elif index_type == IndexType.HNSW:
            qps = 500
        elif index_type == IndexType.IVF:
            qps = 1000
        else:
            qps = 2000
        
        logger.info(f"    预估 QPS: {qps}")
    
    logger.info("\n性能优化建议:")
    logger.info("  1. 小数据集使用Flat索引，保证100%召回率")
    logger.info("  2. 中等数据集使用HNSW，平衡速度和精度")
    logger.info("  3. 大数据集使用IVF+PQ，最大化吞吐量")
    logger.info("  4. 定期预热索引，保持查询性能")
    logger.info("  5. 监控索引状态，及时重建异常索引")


# ==================== 示例 10: 动态索引管理 ====================

def example_dynamic_index_management():
    """动态索引管理示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 动态索引管理")
    logger.info("=" * 60)
    
    service = MultiLevelIndexService()
    
    dimension = 128
    
    # 创建多个索引
    logger.info("\n创建多个索引...")
    
    for i, idx_type in enumerate([IndexType.FLAT, IndexType.HNSW]):
        documents = [
            VectorDocument(
                id=f"doc_{j}",
                text=f"文档 {j}",
                embedding=[random.random() for _ in range(dimension)]
            )
            for j in range(500 * (i + 1))
        ]
        
        service.create_index(
            documents,
            dimension,
            index_type=idx_type,
            index_id=f"index_{idx_type.value}"
        )
        logger.info(f"  创建索引: index_{idx_type.value}")
    
    # 列出所有索引
    logger.info("\n所有索引:")
    indexes = service.list_indexes()
    for idx_id in indexes:
        logger.info(f"  - {idx_id}")
    
    # 切换索引
    logger.info("\n切换当前索引...")
    service.switch_index("index_hnsw")
    current_type = service.get_current_index_type()
    logger.info(f"  当前索引类型: {current_type.value if current_type else 'None'}")
    
    # 获取索引统计
    logger.info("\n各索引统计:")
    for idx_id in indexes:
        stats = service.get_index_stats(idx_id)
        if stats:
            logger.info(f"  {idx_id}:")
            logger.info(f"    类型: {stats.index_type.value}")
            logger.info(f"    大小: {stats.index_size}")
            logger.info(f"    状态: {stats.to_dict().get('index_status', 'unknown')}")


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("多级索引服务使用示例")
    logger.info("=" * 70)
    
    try:
        example_auto_index_selection()
        example_create_different_indexes()
        example_index_search()
        example_index_warmup()
        example_performance_comparison()
        example_index_statistics()
        example_multi_level_strategy()
        # example_benchmark()  # 可选：基准测试
        example_real_world_scenario()
        example_dynamic_index_management()
        
        logger.info("\n" + "=" * 70)
        logger.info("示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
