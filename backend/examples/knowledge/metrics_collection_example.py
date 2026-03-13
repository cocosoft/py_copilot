"""
指标收集系统使用示例 - 向量化管理模块优化

展示如何使用 MetricsCollectionService 进行指标收集、分析和报告生成。

任务编号: BE-003
阶段: Phase 1 - 基础优化期
"""

import time
import random
import logging
from datetime import datetime, timedelta

from app.services.knowledge.metrics_collection_service import (
    MetricsCollectionService,
    MetricsCollector,
    InMemoryMetricsStorage,
    MetricCategory,
    AggregationType,
    MetricDefinition,
    MetricReport,
    TimeSeries,
    metrics_collection_service
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本使用 ====================

def example_basic_usage():
    """基本使用示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本使用")
    logger.info("=" * 60)
    
    # 创建指标收集服务
    service = MetricsCollectionService()
    
    # 记录一些指标
    logger.info("记录指标...")
    
    # 系统指标
    service.gauge("system.cpu.percent", 45.5, MetricCategory.SYSTEM, unit="percent")
    service.gauge("system.memory.percent", 62.3, MetricCategory.SYSTEM, unit="percent")
    
    # 业务指标
    service.increment("requests.total", 100, MetricCategory.BUSINESS)
    service.increment("requests.error", 2, MetricCategory.BUSINESS)
    
    # 性能指标
    service.timing("query.latency", 150.5)
    service.timing("query.latency", 200.3)
    service.timing("query.latency", 180.7)
    
    logger.info("指标记录完成")
    
    # 查询指标
    points = service.query(name="query.latency")
    logger.info(f"查询到 {len(points)} 个 query.latency 指标点")
    
    # 获取统计信息
    stats = service.get_stats("query.latency")
    logger.info(f"\n查询延迟统计:")
    logger.info(f"  数量: {stats.get('count', 0)}")
    logger.info(f"  平均值: {stats.get('avg', 0):.2f}ms")
    logger.info(f"  最小值: {stats.get('min', 0):.2f}ms")
    logger.info(f"  最大值: {stats.get('max', 0):.2f}ms")
    logger.info(f"  P95: {stats.get('p95', 0):.2f}ms")


# ==================== 示例 2: 指标类别 ====================

def example_metric_categories():
    """指标类别示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 指标类别")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    # 系统指标
    logger.info("\n记录系统指标...")
    for i in range(5):
        service.gauge(
            "system.cpu.percent",
            30 + i * 5,
            MetricCategory.SYSTEM,
            unit="percent",
            description="CPU使用率"
        )
        time.sleep(0.1)
    
    # 业务指标
    logger.info("记录业务指标...")
    endpoints = ["/search", "/upload", "/delete"]
    for endpoint in endpoints:
        service.increment(
            "requests.total",
            random.randint(10, 100),
            MetricCategory.BUSINESS,
            labels={"endpoint": endpoint}
        )
    
    # 性能指标
    logger.info("记录性能指标...")
    for i in range(10):
        service.timing(
            "api.response.time",
            random.randint(50, 500),
            labels={"api": "search"}
        )
    
    # 资源指标
    logger.info("记录资源指标...")
    service.gauge(
        "documents.total",
        10000,
        MetricCategory.RESOURCE,
        unit="count"
    )
    service.gauge(
        "vectors.total",
        50000,
        MetricCategory.RESOURCE,
        unit="count"
    )
    
    # 质量指标
    logger.info("记录质量指标...")
    service.gauge(
        "accuracy.score",
        0.95,
        MetricCategory.QUALITY,
        unit="ratio"
    )
    
    # 按类别查询
    for category in MetricCategory:
        points = service.query(category=category)
        logger.info(f"  {category.value}: {len(points)} 个指标点")


# ==================== 示例 3: 标签维度 ====================

def example_labels_dimension():
    """标签维度示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 标签维度")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    # 记录带标签的指标
    logger.info("记录带标签的指标...")
    
    # 不同知识库的查询延迟
    knowledge_bases = ["kb_1", "kb_2", "kb_3"]
    for kb_id in knowledge_bases:
        for i in range(5):
            service.timing(
                "query.latency",
                random.randint(100, 300),
                labels={
                    "knowledge_base_id": kb_id,
                    "query_type": "semantic_search"
                }
            )
    
    # 不同服务的请求数
    services = ["retrieval", "processing", "indexing"]
    for svc in services:
        service.increment(
            "requests.total",
            random.randint(50, 200),
            labels={"service": svc, "method": "POST"}
        )
    
    # 按标签查询
    logger.info("\n按标签查询:")
    
    # 查询特定知识库的指标
    kb1_points = service.query(
        name="query.latency",
        labels={"knowledge_base_id": "kb_1"}
    )
    logger.info(f"  kb_1 查询延迟指标: {len(kb1_points)} 个")
    
    # 查询特定服务的指标
    retrieval_points = service.query(
        name="requests.total",
        labels={"service": "retrieval"}
    )
    logger.info(f"  retrieval 服务请求数: {len(retrieval_points)} 个")


# ==================== 示例 4: 聚合计算 ====================

def example_aggregation():
    """聚合计算示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 聚合计算")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    # 生成测试数据
    logger.info("生成测试数据...")
    latencies = [100, 150, 200, 180, 220, 300, 250, 190, 170, 210,
                 160, 140, 230, 280, 320, 190, 200, 210, 180, 160]
    
    for latency in latencies:
        service.timing("response.time", latency)
    
    logger.info(f"记录了 {len(latencies)} 个响应时间指标")
    
    # 各种聚合计算
    logger.info("\n聚合计算结果:")
    
    aggregations = [
        (AggregationType.SUM, "总和"),
        (AggregationType.AVG, "平均值"),
        (AggregationType.MIN, "最小值"),
        (AggregationType.MAX, "最大值"),
        (AggregationType.COUNT, "数量"),
        (AggregationType.P50, "P50"),
        (AggregationType.P90, "P90"),
        (AggregationType.P95, "P95"),
        (AggregationType.P99, "P99"),
    ]
    
    for agg_type, name in aggregations:
        result = service.aggregate("response.time", agg_type)
        if result is not None:
            logger.info(f"  {name}: {result:.2f}ms")


# ==================== 示例 5: 时间范围查询 ====================

def example_time_range_query():
    """时间范围查询示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 时间范围查询")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    now = datetime.now()
    
    # 记录不同时间点的指标
    logger.info("记录不同时间点的指标...")
    
    # 1小时前的数据
    for i in range(5):
        point_time = now - timedelta(hours=1, minutes=i*10)
        service.collector.record(
            "cpu.usage",
            40 + i * 2,
            MetricCategory.SYSTEM,
            unit="percent"
        )
    
    # 30分钟前的数据
    for i in range(5):
        point_time = now - timedelta(minutes=30, seconds=i*60)
        service.collector.record(
            "cpu.usage",
            50 + i * 3,
            MetricCategory.SYSTEM,
            unit="percent"
        )
    
    # 当前数据
    for i in range(5):
        service.gauge("cpu.usage", 60 + i, MetricCategory.SYSTEM, unit="percent")
    
    # 查询最近1小时的数据
    one_hour_ago = now - timedelta(hours=1)
    recent_points = service.query(
        name="cpu.usage",
        start=one_hour_ago
    )
    logger.info(f"最近1小时的 CPU 指标: {len(recent_points)} 个")
    
    # 查询最近30分钟的数据
    thirty_mins_ago = now - timedelta(minutes=30)
    very_recent = service.query(
        name="cpu.usage",
        start=thirty_mins_ago
    )
    logger.info(f"最近30分钟的 CPU 指标: {len(very_recent)} 个")


# ==================== 示例 6: 指标定义注册 ====================

def example_metric_definitions():
    """指标定义注册示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 指标定义注册")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    # 注册自定义指标定义
    custom_metrics = [
        MetricDefinition(
            name="custom.query.latency",
            category=MetricCategory.PERFORMANCE,
            description="自定义查询延迟",
            unit="ms",
            aggregation_types=[AggregationType.AVG, AggregationType.P95, AggregationType.P99],
            labels=["query_type", "knowledge_base_id"],
            retention_days=60
        ),
        MetricDefinition(
            name="custom.documents.processed",
            category=MetricCategory.BUSINESS,
            description="处理的文档数",
            unit="count",
            aggregation_types=[AggregationType.SUM, AggregationType.RATE],
            labels=["status", "document_type"],
            retention_days=90
        ),
        MetricDefinition(
            name="custom.index.size",
            category=MetricCategory.RESOURCE,
            description="索引大小",
            unit="bytes",
            aggregation_types=[AggregationType.MAX, AggregationType.AVG],
            retention_days=30
        )
    ]
    
    logger.info("注册自定义指标定义...")
    for metric in custom_metrics:
        service.collector.register_metric(metric)
        logger.info(f"  已注册: {metric.name}")
    
    logger.info(f"\n总共注册了 {len(service.collector.definitions)} 个指标定义")
    
    # 使用自定义指标
    logger.info("\n记录自定义指标...")
    service.timing(
        "custom.query.latency",
        250.5,
        labels={"query_type": "semantic", "knowledge_base_id": "kb_1"}
    )
    service.increment(
        "custom.documents.processed",
        10,
        labels={"status": "success", "document_type": "pdf"}
    )
    service.gauge(
        "custom.index.size",
        1024 * 1024 * 100,  # 100MB
        unit="bytes"
    )


# ==================== 示例 7: 报告生成 ====================

def example_report_generation():
    """报告生成示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 报告生成")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    # 生成各类指标数据
    logger.info("生成测试数据...")
    
    # 系统指标
    for i in range(20):
        service.gauge("system.cpu.percent", random.uniform(30, 80), MetricCategory.SYSTEM, unit="percent")
        service.gauge("system.memory.percent", random.uniform(40, 70), MetricCategory.SYSTEM, unit="percent")
    
    # 业务指标
    for i in range(100):
        service.increment("requests.total", 1, MetricCategory.BUSINESS)
        if random.random() < 0.05:  # 5% 错误率
            service.increment("requests.error", 1, MetricCategory.BUSINESS)
    
    # 性能指标
    for i in range(50):
        service.timing("api.latency", random.randint(50, 500))
    
    # 生成报告
    logger.info("\n生成指标报告...")
    report = service.generate_report("系统性能报告", period_hours=1)
    
    logger.info(f"\n报告标题: {report.title}")
    logger.info(f"生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"统计周期: {report.period_start.strftime('%H:%M')} - {report.period_end.strftime('%H:%M')}")
    
    logger.info(f"\n摘要:")
    for key, value in report.summary.items():
        logger.info(f"  {key}: {value}")
    
    logger.info(f"\n各类别指标:")
    for category, metrics in report.metrics.items():
        logger.info(f"  {category}:")
        for name, stats in metrics.items():
            logger.info(f"    {name}: count={stats['count']}, avg={stats['avg']:.2f}")


# ==================== 示例 8: 计数器和仪表盘 ====================

def example_counters_and_gauges():
    """计数器和表示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 计数器和仪表盘")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    # 计数器示例 - 累加型指标
    logger.info("\n计数器示例（累加型）:")
    
    # 模拟请求计数
    for i in range(5):
        service.increment("http.requests.total", 10)
        current = service.collector._counters.get("http.requests.total", 0)
        logger.info(f"  第{i+1}次增加后: {current}")
    
    # 仪表盘示例 - 瞬时值指标
    logger.info("\n仪表盘示例（瞬时值）:")
    
    # 模拟温度变化
    temperatures = [22.5, 23.0, 24.5, 25.0, 24.0]
    for temp in temperatures:
        service.gauge("server.temperature", temp, unit="celsius")
        logger.info(f"  当前温度: {temp}°C")
    
    # 查询最终值
    stats = service.get_stats("http.requests.total")
    logger.info(f"\n最终请求总数: {stats.get('latest', 0)}")
    
    temp_stats = service.get_stats("server.temperature")
    logger.info(f"温度统计: min={temp_stats.get('min')}°C, max={temp_stats.get('max')}°C")


# ==================== 示例 9: 实际应用场景 ====================

def example_real_world_scenario():
    """
    实际应用场景：知识库系统指标监控
    
    展示如何在实际应用中使用指标收集系统。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 实际应用场景 - 知识库系统监控")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    # 模拟知识库系统运行
    logger.info("\n模拟知识库系统运行...")
    
    knowledge_base_id = "kb_production_001"
    
    # 模拟一段时间的运行
    for minute in range(10):
        logger.info(f"\n--- 第 {minute + 1} 分钟 ---")
        
        # 系统资源
        cpu_usage = random.uniform(30, 70)
        memory_usage = random.uniform(50, 80)
        service.gauge("system.cpu.percent", cpu_usage, MetricCategory.SYSTEM, unit="percent")
        service.gauge("system.memory.percent", memory_usage, MetricCategory.SYSTEM, unit="percent")
        logger.info(f"  CPU: {cpu_usage:.1f}%, 内存: {memory_usage:.1f}%")
        
        # 查询处理
        query_count = random.randint(50, 150)
        for i in range(query_count):
            latency = random.randint(50, 300)
            service.timing(
                "search.query.latency",
                latency,
                labels={"knowledge_base_id": knowledge_base_id, "type": "semantic"}
            )
        service.increment("search.query.count", query_count, labels={"kb": knowledge_base_id})
        logger.info(f"  处理查询: {query_count} 次")
        
        # 文档处理
        doc_count = random.randint(5, 20)
        for i in range(doc_count):
            processing_time = random.randint(1000, 5000)
            service.timing(
                "document.processing.time",
                processing_time,
                labels={"knowledge_base_id": knowledge_base_id}
            )
        service.increment("documents.processed", doc_count, labels={"kb": knowledge_base_id})
        logger.info(f"  处理文档: {doc_count} 个")
        
        # 错误统计
        error_count = random.randint(0, 3)
        if error_count > 0:
            service.increment("errors.total", error_count, labels={"kb": knowledge_base_id})
            logger.info(f"  错误数: {error_count}")
    
    # 生成监控报告
    logger.info("\n" + "=" * 60)
    logger.info("生成监控报告")
    logger.info("=" * 60)
    
    # 查询延迟统计
    latency_stats = service.get_stats("search.query.latency")
    logger.info("\n查询延迟统计:")
    logger.info(f"  总查询数: {latency_stats.get('count', 0)}")
    logger.info(f"  平均延迟: {latency_stats.get('avg', 0):.2f}ms")
    logger.info(f"  P95延迟: {latency_stats.get('p95', 0):.2f}ms")
    logger.info(f"  P99延迟: {latency_stats.get('p99', 0):.2f}ms")
    
    # 文档处理统计
    doc_stats = service.get_stats("document.processing.time")
    logger.info("\n文档处理统计:")
    logger.info(f"  处理文档数: {doc_stats.get('count', 0)}")
    logger.info(f"  平均处理时间: {doc_stats.get('avg', 0):.2f}ms")
    
    # 错误率计算
    total_queries = service.collector._counters.get("search.query.count", 0)
    total_errors = service.collector._counters.get("errors.total", 0)
    error_rate = (total_errors / total_queries * 100) if total_queries > 0 else 0
    logger.info(f"\n错误率: {error_rate:.2f}%")
    
    # 生成完整报告
    report = service.generate_report("知识库系统监控报告", period_hours=1)
    logger.info(f"\n报告生成完成: {report.title}")
    logger.info(f"指标类别: {', '.join(report.summary.get('categories', []))}")


# ==================== 示例 10: 性能测试 ====================

def example_performance_test():
    """性能测试示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 性能测试")
    logger.info("=" * 60)
    
    service = MetricsCollectionService()
    
    # 测试指标记录性能
    logger.info("\n测试指标记录性能...")
    
    count = 10000
    start_time = time.time()
    
    for i in range(count):
        service.timing("perf.test.latency", random.randint(10, 100))
    
    elapsed = time.time() - start_time
    
    logger.info(f"记录了 {count} 个指标")
    logger.info(f"总耗时: {elapsed:.2f}秒")
    logger.info(f"平均每秒: {count / elapsed:.0f} 个指标")
    
    # 测试查询性能
    logger.info("\n测试查询性能...")
    
    start_time = time.time()
    points = service.query(name="perf.test.latency")
    query_time = time.time() - start_time
    
    logger.info(f"查询到 {len(points)} 个指标点")
    logger.info(f"查询耗时: {query_time * 1000:.2f}ms")
    
    # 测试聚合性能
    logger.info("\n测试聚合性能...")
    
    start_time = time.time()
    result = service.aggregate("perf.test.latency", AggregationType.P95)
    agg_time = time.time() - start_time
    
    logger.info(f"P95聚合结果: {result:.2f}ms")
    logger.info(f"聚合耗时: {agg_time * 1000:.2f}ms")


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("指标收集系统使用示例")
    logger.info("=" * 70)
    
    try:
        example_basic_usage()
        example_metric_categories()
        example_labels_dimension()
        example_aggregation()
        example_time_range_query()
        example_metric_definitions()
        example_report_generation()
        example_counters_and_gauges()
        # example_real_world_scenario()  # 输出较多，可选运行
        # example_performance_test()  # 耗时较长，可选运行
        
        logger.info("\n" + "=" * 70)
        logger.info("示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
