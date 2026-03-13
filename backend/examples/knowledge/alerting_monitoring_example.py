"""
监控告警系统使用示例 - 向量化管理模块优化

展示如何使用 AlertingMonitoringService 进行系统监控和告警管理。

任务编号: BE-013
阶段: Phase 4 - 功能完善期
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.knowledge.alerting_monitoring_service import (
    AlertingMonitoringService,
    AlertRule,
    AlertLevel,
    AlertStatus,
    AlertChannel,
    MetricType,
    create_default_alert_rules,
    alerting_monitoring_service
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 示例 1: 基本使用 ====================

def example_basic_usage():
    """基本使用示例"""
    
    logger.info("=" * 60)
    logger.info("示例 1: 基本使用")
    logger.info("=" * 60)
    
    # 创建监控服务
    service = AlertingMonitoringService(
        check_interval=10,  # 每10秒检查一次
        metrics_retention_hours=1
    )
    
    # 添加默认告警规则
    for rule in create_default_alert_rules():
        service.add_alert_rule(rule)
    
    # 启动服务
    service.start()
    
    logger.info("监控服务已启动")
    logger.info(f"告警规则数: {len(service.alert_rules)}")
    
    # 运行一段时间
    logger.info("运行30秒...")
    time.sleep(30)
    
    # 获取活跃告警
    active_alerts = service.get_active_alerts()
    logger.info(f"活跃告警数: {len(active_alerts)}")
    
    # 停止服务
    service.stop()
    logger.info("监控服务已停止")


# ==================== 示例 2: 自定义告警规则 ====================

def example_custom_alert_rules():
    """自定义告警规则示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 自定义告警规则")
    logger.info("=" * 60)
    
    service = AlertingMonitoringService()
    
    # 创建自定义告警规则
    custom_rules = [
        AlertRule(
            id="query_latency_high",
            name="查询延迟过高",
            description="查询平均延迟超过500ms",
            metric_name="query.latency.avg",
            condition=">",
            threshold=500,
            duration=60,
            level=AlertLevel.WARNING,
            channels=[AlertChannel.LOG, AlertChannel.CONSOLE],
            labels={"service": "retrieval"}
        ),
        AlertRule(
            id="error_rate_high",
            name="错误率过高",
            description="错误率超过5%",
            metric_name="error.rate",
            condition=">",
            threshold=0.05,
            duration=120,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.LOG, AlertChannel.CONSOLE],
            cooldown=600
        ),
        AlertRule(
            id="cache_hit_rate_low",
            name="缓存命中率过低",
            description="缓存命中率低于70%",
            metric_name="cache.hit_rate",
            condition="<",
            threshold=0.7,
            duration=300,
            level=AlertLevel.WARNING,
            channels=[AlertChannel.LOG]
        )
    ]
    
    for rule in custom_rules:
        service.add_alert_rule(rule)
    
    logger.info(f"添加了 {len(custom_rules)} 个自定义告警规则")
    
    # 显示所有规则
    logger.info("\n告警规则列表:")
    for rule_id, rule in service.alert_rules.items():
        logger.info(f"  - {rule.name}: {rule.metric_name} {rule.condition} {rule.threshold}")


# ==================== 示例 3: 记录指标 ====================

def example_record_metrics():
    """记录指标示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 记录指标")
    logger.info("=" * 60)
    
    service = AlertingMonitoringService()
    
    # 记录各种类型的指标
    
    # 1. 计数器（请求数）
    for i in range(10):
        service.increment_counter("requests.total", 1, {"endpoint": "/search"})
        service.increment_counter("requests.total", 1, {"endpoint": "/upload"})
    
    logger.info("记录了请求计数器")
    
    # 2. 仪表盘（延迟）
    latencies = [100, 150, 200, 180, 220, 300, 250, 190, 170, 210]
    for latency in latencies:
        service.set_gauge("query.latency", latency, {"type": "vector_search"})
    
    logger.info("记录了查询延迟指标")
    
    # 3. 直方图（处理时间分布）
    processing_times = [50, 80, 120, 200, 350, 500, 750, 1000]
    for pt in processing_times:
        service.record_metric("processing.time", pt, MetricType.HISTOGRAM)
    
    logger.info("记录了处理时间直方图")
    
    # 获取指标统计
    stats = service.metrics_collector.get_stats("query.latency", {"type": "vector_search"})
    logger.info(f"\n查询延迟统计:")
    logger.info(f"  数量: {stats.get('count', 0)}")
    logger.info(f"  最小值: {stats.get('min', 0):.2f}ms")
    logger.info(f"  最大值: {stats.get('max', 0):.2f}ms")
    logger.info(f"  平均值: {stats.get('avg', 0):.2f}ms")
    
    # 获取计数器值
    counter_value = service.metrics_collector.get_counter("requests.total", {"endpoint": "/search"})
    logger.info(f"\n搜索请求数: {counter_value}")


# ==================== 示例 4: 告警触发和恢复 ====================

def example_alert_triggering():
    """告警触发和恢复示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 告警触发和恢复")
    logger.info("=" * 60)
    
    service = AlertingMonitoringService(check_interval=5)
    
    # 添加告警规则
    rule = AlertRule(
        id="test_high_value",
        name="测试高值告警",
        description="测试值超过阈值",
        metric_name="test.value",
        condition=">",
        threshold=80,
        duration=0,
        level=AlertLevel.WARNING,
        channels=[AlertChannel.LOG, AlertChannel.CONSOLE],
        cooldown=10
    )
    service.add_alert_rule(rule)
    
    # 启动服务
    service.start()
    
    logger.info("\n阶段 1: 正常值（不触发告警）")
    for i in range(3):
        service.set_gauge("test.value", 50)
        time.sleep(2)
    
    logger.info("\n阶段 2: 高值（触发告警）")
    for i in range(3):
        service.set_gauge("test.value", 90)
        time.sleep(2)
    
    # 检查活跃告警
    active_alerts = service.get_active_alerts()
    logger.info(f"\n活跃告警数: {len(active_alerts)}")
    
    logger.info("\n阶段 3: 恢复正常值（告警恢复）")
    for i in range(3):
        service.set_gauge("test.value", 50)
        time.sleep(2)
    
    # 停止服务
    service.stop()


# ==================== 示例 5: 告警确认 ====================

def example_alert_acknowledgment():
    """告警确认示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 告警确认")
    logger.info("=" * 60)
    
    service = AlertingMonitoringService(check_interval=5)
    
    # 添加规则并触发告警
    rule = AlertRule(
        id="ack_test",
        name="确认测试告警",
        description="测试告警确认功能",
        metric_name="ack.test.value",
        condition=">",
        threshold=100,
        duration=0,
        level=AlertLevel.ERROR,
        channels=[AlertChannel.LOG]
    )
    service.add_alert_rule(rule)
    
    service.start()
    
    # 触发告警
    logger.info("触发告警...")
    service.set_gauge("ack.test.value", 150)
    time.sleep(3)
    
    # 获取告警
    alerts = service.get_active_alerts()
    if alerts:
        alert = alerts[0]
        logger.info(f"告警状态: {alert.status.value}")
        
        # 确认告警
        logger.info("确认告警...")
        service.acknowledge_alert(alert.id, "admin")
        
        # 刷新告警状态
        alerts = service.get_active_alerts()
        if alerts:
            logger.info(f"确认后状态: {alerts[0].status.value}")
            logger.info(f"确认人: {alerts[0].acknowledged_by}")
    
    service.stop()


# ==================== 示例 6: 系统指标监控 ====================

def example_system_metrics():
    """系统指标监控示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 系统指标监控")
    logger.info("=" * 60)
    
    service = AlertingMonitoringService()
    
    # 启动服务（会自动采集系统指标）
    service.start()
    
    logger.info("采集系统指标（等待5秒）...")
    time.sleep(5)
    
    # 获取系统指标
    metrics = service.get_system_metrics()
    
    logger.info("\n系统指标:")
    logger.info(f"  CPU使用率: {metrics.cpu_percent}%")
    logger.info(f"  CPU核心数: {metrics.cpu_count}")
    logger.info(f"  内存使用率: {metrics.memory_percent}%")
    logger.info(f"  内存使用: {metrics.memory_used_gb:.2f} GB")
    logger.info(f"  内存可用: {metrics.memory_available_gb:.2f} GB")
    logger.info(f"  磁盘使用率: {metrics.disk_percent}%")
    logger.info(f"  磁盘使用: {metrics.disk_used_gb:.2f} GB")
    logger.info(f"  磁盘空闲: {metrics.disk_free_gb:.2f} GB")
    logger.info(f"  进程数: {metrics.process_count}")
    logger.info(f"  线程数: {metrics.thread_count}")
    
    service.stop()


# ==================== 示例 7: 告警历史查询 ====================

def example_alert_history():
    """告警历史查询示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 7: 告警历史查询")
    logger.info("=" * 60)
    
    service = AlertingMonitoringService(check_interval=3)
    
    # 添加多个规则
    rules = [
        AlertRule(
            id="history_test_1",
            name="历史测试告警1",
            description="测试历史记录1",
            metric_name="history.test.1",
            condition=">",
            threshold=50,
            duration=0,
            level=AlertLevel.WARNING,
            channels=[AlertChannel.LOG]
        ),
        AlertRule(
            id="history_test_2",
            name="历史测试告警2",
            description="测试历史记录2",
            metric_name="history.test.2",
            condition=">",
            threshold=100,
            duration=0,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.LOG]
        )
    ]
    
    for rule in rules:
        service.add_alert_rule(rule)
    
    service.start()
    
    # 触发一些告警
    logger.info("触发告警...")
    service.set_gauge("history.test.1", 60)
    service.set_gauge("history.test.2", 120)
    time.sleep(5)
    
    # 查询告警历史
    history = service.get_alert_history()
    logger.info(f"\n告警历史总数: {len(history)}")
    
    # 按级别过滤
    error_history = service.get_alert_history(level=AlertLevel.ERROR)
    logger.info(f"ERROR级别告警: {len(error_history)}")
    
    # 按时间过滤
    recent_history = service.get_alert_history(since=datetime.now() - timedelta(minutes=1))
    logger.info(f"最近1分钟告警: {len(recent_history)}")
    
    service.stop()


# ==================== 示例 8: 指标摘要 ====================

def example_metrics_summary():
    """指标摘要示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 8: 指标摘要")
    logger.info("=" * 60)
    
    service = AlertingMonitoringService()
    
    # 添加一些规则
    for i in range(5):
        rule = AlertRule(
            id=f"summary_rule_{i}",
            name=f"摘要规则{i}",
            description=f"测试规则{i}",
            metric_name=f"metric.{i}",
            condition=">",
            threshold=i * 10,
            duration=60,
            level=AlertLevel.INFO,
            channels=[AlertChannel.LOG],
            enabled=i % 2 == 0  # 偶数启用
        )
        service.add_alert_rule(rule)
    
    # 记录一些指标
    for i in range(10):
        service.set_gauge(f"metric.{i % 5}", i * 5)
    
    # 获取摘要
    summary = service.get_metrics_summary()
    
    logger.info("\n指标摘要:")
    logger.info(f"  活跃告警: {summary['active_alerts']}")
    logger.info(f"  总规则数: {summary['total_rules']}")
    logger.info(f"  启用规则: {summary['enabled_rules']}")
    logger.info(f"  指标数量: {summary['metrics_count']}")
    logger.info(f"  告警历史: {summary['alert_history_count']}")


# ==================== 示例 9: 实际应用场景 ====================

def example_real_world_scenario():
    """
    实际应用场景：知识库系统监控
    
    展示如何在实际应用中使用监控告警系统。
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 9: 实际应用场景 - 知识库系统监控")
    logger.info("=" * 60)
    
    service = AlertingMonitoringService(check_interval=10)
    
    # 添加业务相关告警规则
    business_rules = [
        AlertRule(
            id="search_latency_high",
            name="搜索延迟过高",
            description="向量搜索平均延迟超过1秒",
            metric_name="search.latency.avg",
            condition=">",
            threshold=1000,
            duration=60,
            level=AlertLevel.WARNING,
            channels=[AlertChannel.LOG, AlertChannel.CONSOLE],
            labels={"component": "search"}
        ),
        AlertRule(
            id="index_build_slow",
            name="索引构建过慢",
            description="索引构建时间超过10分钟",
            metric_name="index.build.time",
            condition=">",
            threshold=600,
            duration=0,
            level=AlertLevel.WARNING,
            channels=[AlertChannel.LOG]
        ),
        AlertRule(
            id="document_processing_failed",
            name="文档处理失败率高",
            description="文档处理失败率超过10%",
            metric_name="document.processing.failure_rate",
            condition=">",
            threshold=0.1,
            duration=120,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.LOG, AlertChannel.CONSOLE]
        ),
        AlertRule(
            id="vector_store_connection_failed",
            name="向量存储连接失败",
            description="无法连接到向量存储",
            metric_name="vector.store.connection.status",
            condition="==",
            threshold=0,
            duration=30,
            level=AlertLevel.CRITICAL,
            channels=[AlertChannel.LOG, AlertChannel.CONSOLE]
        )
    ]
    
    for rule in business_rules:
        service.add_alert_rule(rule)
    
    # 启动监控
    service.start()
    
    logger.info("\n模拟知识库系统运行...")
    
    # 模拟系统运行
    for i in range(20):
        # 模拟搜索延迟
        search_latency = 500 + (i * 50)  # 逐渐增加的延迟
        service.set_gauge("search.latency.avg", search_latency, {"component": "search"})
        
        # 模拟文档处理
        service.increment_counter("documents.processed.total", 5)
        if i % 5 == 0:
            service.increment_counter("documents.processed.failed", 1)
        
        # 计算失败率
        total = service.metrics_collector.get_counter("documents.processed.total")
        failed = service.metrics_collector.get_counter("documents.processed.failed")
        failure_rate = failed / total if total > 0 else 0
        service.set_gauge("document.processing.failure_rate", failure_rate)
        
        # 模拟向量存储连接状态
        connection_status = 1 if i < 15 else 0  # 第15次后断开连接
        service.set_gauge("vector.store.connection.status", connection_status)
        
        time.sleep(1)
    
    # 查看结果
    logger.info("\n监控结果:")
    
    active_alerts = service.get_active_alerts()
    logger.info(f"活跃告警: {len(active_alerts)}")
    
    for alert in active_alerts:
        logger.info(f"  - [{alert.level.value.upper()}] {alert.rule_name}: {alert.message}")
    
    # 指标统计
    search_stats = service.metrics_collector.get_stats("search.latency.avg")
    logger.info(f"\n搜索延迟统计:")
    logger.info(f"  平均: {search_stats.get('avg', 0):.2f}ms")
    logger.info(f"  最大: {search_stats.get('max', 0):.2f}ms")
    
    service.stop()
    
    logger.info("\n监控结束")


# ==================== 示例 10: 性能测试 ====================

def example_performance_test():
    """性能测试示例"""
    
    logger.info("\n" + "=" * 60)
    logger.info("示例 10: 性能测试")
    logger.info("=" * 60)
    
    import random
    
    service = AlertingMonitoringService(check_interval=5)
    
    # 添加大量规则
    logger.info("添加100个告警规则...")
    for i in range(100):
        rule = AlertRule(
            id=f"perf_rule_{i}",
            name=f"性能测试规则{i}",
            description=f"测试规则{i}",
            metric_name=f"perf.metric.{i % 10}",
            condition=random.choice([">", "<"]),
            threshold=random.randint(50, 150),
            duration=0,
            level=random.choice(list(AlertLevel)),
            channels=[AlertChannel.LOG]
        )
        service.add_alert_rule(rule)
    
    service.start()
    
    # 记录大量指标
    logger.info("记录10000个指标...")
    start_time = time.time()
    
    for i in range(10000):
        service.set_gauge(f"perf.metric.{i % 10}", random.randint(0, 200))
    
    elapsed = time.time() - start_time
    logger.info(f"记录完成，耗时: {elapsed:.2f}秒")
    logger.info(f"平均每秒: {10000 / elapsed:.0f} 个指标")
    
    # 等待告警检查
    time.sleep(6)
    
    # 查看结果
    summary = service.get_metrics_summary()
    logger.info(f"\n监控摘要:")
    logger.info(f"  活跃告警: {summary['active_alerts']}")
    logger.info(f"  总规则数: {summary['total_rules']}")
    
    service.stop()


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    
    logger.info("\n" + "=" * 70)
    logger.info("监控告警系统使用示例")
    logger.info("=" * 70)
    
    try:
        # 注意：以下示例中涉及实际监控的示例
        # 在实际运行时需要确保系统资源正常
        
        example_basic_usage()
        example_custom_alert_rules()
        example_record_metrics()
        # example_alert_triggering()  # 需要等待时间
        # example_alert_acknowledgment()  # 需要等待时间
        example_system_metrics()
        # example_alert_history()  # 需要等待时间
        example_metrics_summary()
        # example_real_world_scenario()  # 需要等待时间
        # example_performance_test()  # 需要较长时间
        
        logger.info("\n" + "=" * 70)
        logger.info("示例运行完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
