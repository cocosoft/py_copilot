"""
指标收集系统 - 向量化管理模块优化

实现系统性能指标和业务指标的收集、存储、分析和可视化。

任务编号: BE-003
阶段: Phase 1 - 基础优化期
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import defaultdict, deque
import json
import statistics
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """指标类别"""
    SYSTEM = "system"           # 系统指标
    BUSINESS = "business"       # 业务指标
    PERFORMANCE = "performance" # 性能指标
    QUALITY = "quality"         # 质量指标
    RESOURCE = "resource"       # 资源指标


class AggregationType(Enum):
    """聚合类型"""
    SUM = "sum"                 # 求和
    AVG = "avg"                 # 平均值
    MIN = "min"                 # 最小值
    MAX = "max"                 # 最大值
    COUNT = "count"             # 计数
    P50 = "p50"                 # 50分位数
    P90 = "p90"                 # 90分位数
    P95 = "p95"                 # 95分位数
    P99 = "p99"                 # 99分位数
    RATE = "rate"               # 速率


@dataclass
class MetricPoint:
    """指标数据点"""
    name: str
    value: float
    timestamp: datetime
    category: MetricCategory
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""              # 单位（ms, bytes, count等）
    description: str = ""       # 描述
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "labels": self.labels,
            "unit": self.unit,
            "description": self.description
        }


@dataclass
class TimeSeries:
    """时间序列数据"""
    name: str
    points: List[MetricPoint] = field(default_factory=list)
    
    def add_point(self, point: MetricPoint):
        """添加数据点"""
        self.points.append(point)
        # 保持有序
        self.points.sort(key=lambda p: p.timestamp)
    
    def get_range(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[MetricPoint]:
        """获取时间范围内的数据点"""
        result = self.points
        if start:
            result = [p for p in result if p.timestamp >= start]
        if end:
            result = [p for p in result if p.timestamp <= end]
        return result
    
    def aggregate(self, agg_type: AggregationType) -> Optional[float]:
        """聚合计算"""
        if not self.points:
            return None
        
        values = [p.value for p in self.points]
        
        if agg_type == AggregationType.SUM:
            return sum(values)
        elif agg_type == AggregationType.AVG:
            return statistics.mean(values)
        elif agg_type == AggregationType.MIN:
            return min(values)
        elif agg_type == AggregationType.MAX:
            return max(values)
        elif agg_type == AggregationType.COUNT:
            return len(values)
        elif agg_type == AggregationType.P50:
            return statistics.median(values)
        elif agg_type == AggregationType.P90:
            return self._percentile(values, 90)
        elif agg_type == AggregationType.P95:
            return self._percentile(values, 95)
        elif agg_type == AggregationType.P99:
            return self._percentile(values, 99)
        
        return None
    
    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """计算百分位数"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]


@dataclass
class MetricDefinition:
    """指标定义"""
    name: str
    category: MetricCategory
    description: str
    unit: str
    aggregation_types: List[AggregationType] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)  # 支持的标签键
    retention_days: int = 30  # 数据保留天数


@dataclass
class MetricReport:
    """指标报告"""
    title: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "metrics": self.metrics,
            "summary": self.summary
        }


class MetricsStorage(ABC):
    """指标存储抽象基类"""
    
    @abstractmethod
    def store(self, point: MetricPoint):
        """存储指标点"""
        pass
    
    @abstractmethod
    def query(
        self,
        name: Optional[str] = None,
        category: Optional[MetricCategory] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricPoint]:
        """查询指标"""
        pass
    
    @abstractmethod
    def cleanup(self, before: datetime):
        """清理过期数据"""
        pass


class InMemoryMetricsStorage(MetricsStorage):
    """内存指标存储"""
    
    def __init__(self, max_points_per_series: int = 10000):
        """
        初始化内存存储
        
        Args:
            max_points_per_series: 每个序列最大数据点数
        """
        self.max_points = max_points_per_series
        self.series: Dict[str, TimeSeries] = {}
        self._lock = threading.Lock()
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """生成序列键"""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name
    
    def store(self, point: MetricPoint):
        """存储指标点"""
        with self._lock:
            key = self._make_key(point.name, point.labels)
            
            if key not in self.series:
                self.series[key] = TimeSeries(name=point.name)
            
            series = self.series[key]
            series.add_point(point)
            
            # 限制数据点数量
            if len(series.points) > self.max_points:
                series.points = series.points[-self.max_points:]
    
    def query(
        self,
        name: Optional[str] = None,
        category: Optional[MetricCategory] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricPoint]:
        """查询指标"""
        with self._lock:
            results = []
            
            for key, series in self.series.items():
                # 名称过滤
                if name and not series.name.startswith(name):
                    continue
                
                # 类别过滤
                if category:
                    points = [p for p in series.points if p.category == category]
                else:
                    points = series.points
                
                # 标签过滤
                if labels:
                    points = [
                        p for p in points
                        if all(p.labels.get(k) == v for k, v in labels.items())
                    ]
                
                # 时间范围过滤
                if start:
                    points = [p for p in points if p.timestamp >= start]
                if end:
                    points = [p for p in points if p.timestamp <= end]
                
                results.extend(points)
            
            return sorted(results, key=lambda p: p.timestamp)
    
    def cleanup(self, before: datetime):
        """清理过期数据"""
        with self._lock:
            for series in self.series.values():
                series.points = [p for p in series.points if p.timestamp >= before]
    
    def get_series(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[TimeSeries]:
        """获取时间序列"""
        key = self._make_key(name, labels or {})
        return self.series.get(key)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, storage: Optional[MetricsStorage] = None):
        """
        初始化指标收集器
        
        Args:
            storage: 指标存储，默认使用内存存储
        """
        self.storage = storage or InMemoryMetricsStorage()
        self.definitions: Dict[str, MetricDefinition] = {}
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        logger.info("指标收集器初始化完成")
    
    def register_metric(self, definition: MetricDefinition):
        """
        注册指标定义
        
        Args:
            definition: 指标定义
        """
        with self._lock:
            self.definitions[definition.name] = definition
            logger.debug(f"注册指标: {definition.name}")
    
    def record(
        self,
        name: str,
        value: float,
        category: MetricCategory,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "",
        description: str = ""
    ):
        """
        记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            category: 指标类别
            labels: 标签
            unit: 单位
            description: 描述
        """
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(),
            category=category,
            labels=labels or {},
            unit=unit,
            description=description
        )
        
        self.storage.store(point)
    
    def increment(
        self,
        name: str,
        value: float = 1,
        category: MetricCategory = MetricCategory.BUSINESS,
        labels: Optional[Dict[str, str]] = None
    ):
        """增加计数器"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
            self.record(name, self._counters[key], category, labels, "count")
    
    def gauge(
        self,
        name: str,
        value: float,
        category: MetricCategory = MetricCategory.SYSTEM,
        labels: Optional[Dict[str, str]] = None,
        unit: str = ""
    ):
        """设置仪表盘值"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
            self.record(name, value, category, labels, unit)
    
    def timing(
        self,
        name: str,
        value_ms: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """记录耗时"""
        self.record(name, value_ms, MetricCategory.PERFORMANCE, labels, "ms")
    
    def histogram(
        self,
        name: str,
        value: float,
        category: MetricCategory = MetricCategory.PERFORMANCE,
        labels: Optional[Dict[str, str]] = None,
        unit: str = ""
    ):
        """记录直方图"""
        self.record(name, value, category, labels, unit)
    
    def query(
        self,
        name: Optional[str] = None,
        category: Optional[MetricCategory] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricPoint]:
        """
        查询指标
        
        Args:
            name: 指标名称
            category: 指标类别
            start: 开始时间
            end: 结束时间
            labels: 标签过滤
            
        Returns:
            指标点列表
        """
        return self.storage.query(name, category, start, end, labels)
    
    def get_time_series(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[TimeSeries]:
        """获取时间序列"""
        if isinstance(self.storage, InMemoryMetricsStorage):
            return self.storage.get_series(name, labels)
        return None
    
    def aggregate(
        self,
        name: str,
        agg_type: AggregationType,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """
        聚合计算
        
        Args:
            name: 指标名称
            agg_type: 聚合类型
            start: 开始时间
            end: 结束时间
            labels: 标签过滤
            
        Returns:
            聚合结果
        """
        series = self.get_time_series(name, labels)
        if series:
            points = series.get_range(start, end)
            if points:
                temp_series = TimeSeries(name=name, points=points)
                return temp_series.aggregate(agg_type)
        return None
    
    def get_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """获取统计信息"""
        series = self.get_time_series(name, labels)
        if not series or not series.points:
            return {}
        
        values = [p.value for p in series.points]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "p90": TimeSeries._percentile(values, 90),
            "p95": TimeSeries._percentile(values, 95),
            "p99": TimeSeries._percentile(values, 99),
            "latest": values[-1] if values else None
        }
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """生成键"""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name


class MetricsReporter:
    """指标报告生成器"""
    
    def __init__(self, collector: MetricsCollector):
        """
        初始化报告生成器
        
        Args:
            collector: 指标收集器
        """
        self.collector = collector
    
    def generate_report(
        self,
        title: str,
        period_hours: int = 24
    ) -> MetricReport:
        """
        生成指标报告
        
        Args:
            title: 报告标题
            period_hours: 统计周期（小时）
            
        Returns:
            指标报告
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=period_hours)
        
        report = MetricReport(
            title=title,
            generated_at=end_time,
            period_start=start_time,
            period_end=end_time
        )
        
        # 按类别统计
        for category in MetricCategory:
            points = self.collector.query(
                category=category,
                start=start_time,
                end=end_time
            )
            
            if points:
                # 按名称分组
                by_name = defaultdict(list)
                for p in points:
                    by_name[p.name].append(p)
                
                report.metrics[category.value] = {
                    name: {
                        "count": len(pts),
                        "avg": statistics.mean([p.value for p in pts]),
                        "latest": pts[-1].value if pts else None
                    }
                    for name, pts in by_name.items()
                }
        
        # 生成摘要
        all_points = self.collector.query(start=start_time, end=end_time)
        report.summary = {
            "total_metrics": len(all_points),
            "unique_names": len(set(p.name for p in all_points)),
            "categories": list(set(p.category.value for p in all_points)),
            "period_hours": period_hours
        }
        
        return report
    
    def generate_performance_report(
        self,
        period_hours: int = 24
    ) -> MetricReport:
        """生成性能报告"""
        return self.generate_report("性能指标报告", period_hours)
    
    def generate_business_report(
        self,
        period_hours: int = 24
    ) -> MetricReport:
        """生成业务报告"""
        return self.generate_report("业务指标报告", period_hours)


class MetricsCollectionService:
    """
    指标收集服务
    
    提供完整的指标收集、存储、分析和报告功能：
    - 多类别指标收集（系统、业务、性能、质量、资源）
    - 灵活的指标定义和注册
    - 时间序列数据存储
    - 多维度聚合计算
    - 自动报告生成
    
    特性：
    - 支持多种聚合类型（SUM, AVG, MIN, MAX, P50, P90, P95, P99）
    - 标签维度支持
    - 自动数据清理
    - 线程安全
    """
    
    def __init__(
        self,
        storage: Optional[MetricsStorage] = None,
        cleanup_interval_hours: int = 24,
        default_retention_days: int = 30
    ):
        """
        初始化指标收集服务
        
        Args:
            storage: 指标存储
            cleanup_interval_hours: 清理间隔（小时）
            default_retention_days: 默认数据保留天数
        """
        self.collector = MetricsCollector(storage)
        self.reporter = MetricsReporter(self.collector)
        self.cleanup_interval = timedelta(hours=cleanup_interval_hours)
        self.retention_days = default_retention_days
        
        # 运行状态
        self._running = False
        self._cleanup_thread = None
        
        # 注册默认指标定义
        self._register_default_metrics()
        
        logger.info(f"指标收集服务初始化完成: retention={default_retention_days}天")
    
    def _register_default_metrics(self):
        """注册默认指标定义"""
        default_metrics = [
            # 系统指标
            MetricDefinition(
                name="system.cpu.percent",
                category=MetricCategory.SYSTEM,
                description="CPU使用率",
                unit="percent",
                aggregation_types=[AggregationType.AVG, AggregationType.MAX]
            ),
            MetricDefinition(
                name="system.memory.percent",
                category=MetricCategory.SYSTEM,
                description="内存使用率",
                unit="percent",
                aggregation_types=[AggregationType.AVG, AggregationType.MAX]
            ),
            # 业务指标
            MetricDefinition(
                name="requests.total",
                category=MetricCategory.BUSINESS,
                description="总请求数",
                unit="count",
                aggregation_types=[AggregationType.SUM, AggregationType.RATE]
            ),
            MetricDefinition(
                name="requests.error",
                category=MetricCategory.BUSINESS,
                description="错误请求数",
                unit="count",
                aggregation_types=[AggregationType.SUM, AggregationType.RATE]
            ),
            # 性能指标
            MetricDefinition(
                name="query.latency",
                category=MetricCategory.PERFORMANCE,
                description="查询延迟",
                unit="ms",
                aggregation_types=[AggregationType.AVG, AggregationType.P50, AggregationType.P95, AggregationType.P99]
            ),
            MetricDefinition(
                name="index.build.time",
                category=MetricCategory.PERFORMANCE,
                description="索引构建时间",
                unit="ms",
                aggregation_types=[AggregationType.AVG, AggregationType.P95]
            ),
            # 资源指标
            MetricDefinition(
                name="documents.total",
                category=MetricCategory.RESOURCE,
                description="文档总数",
                unit="count",
                aggregation_types=[AggregationType.MAX]
            ),
            MetricDefinition(
                name="vectors.total",
                category=MetricCategory.RESOURCE,
                description="向量总数",
                unit="count",
                aggregation_types=[AggregationType.MAX]
            ),
        ]
        
        for metric in default_metrics:
            self.collector.register_metric(metric)
    
    def start(self):
        """启动服务"""
        if self._running:
            return
        
        self._running = True
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self._cleanup_thread.daemon = True
        self._cleanup_thread.start()
        
        logger.info("指标收集服务已启动")
    
    def stop(self):
        """停止服务"""
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        logger.info("指标收集服务已停止")
    
    def _cleanup_loop(self):
        """清理循环"""
        while self._running:
            try:
                time.sleep(self.cleanup_interval.total_seconds())
                self._cleanup_old_data()
            except Exception as e:
                logger.error(f"清理数据出错: {e}")
    
    def _cleanup_old_data(self):
        """清理过期数据"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        self.collector.storage.cleanup(cutoff)
        logger.info(f"已清理 {cutoff} 之前的过期数据")
    
    def record(
        self,
        name: str,
        value: float,
        category: MetricCategory,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "",
        description: str = ""
    ):
        """记录指标"""
        self.collector.record(name, value, category, labels, unit, description)
    
    def increment(
        self,
        name: str,
        value: float = 1,
        category: MetricCategory = MetricCategory.BUSINESS,
        labels: Optional[Dict[str, str]] = None
    ):
        """增加计数器"""
        self.collector.increment(name, value, category, labels)
    
    def gauge(
        self,
        name: str,
        value: float,
        category: MetricCategory = MetricCategory.SYSTEM,
        labels: Optional[Dict[str, str]] = None,
        unit: str = ""
    ):
        """设置仪表盘值"""
        self.collector.gauge(name, value, category, labels, unit)
    
    def timing(
        self,
        name: str,
        value_ms: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """记录耗时"""
        self.collector.timing(name, value_ms, labels)
    
    def query(
        self,
        name: Optional[str] = None,
        category: Optional[MetricCategory] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricPoint]:
        """查询指标"""
        return self.collector.query(name, category, start, end, labels)
    
    def aggregate(
        self,
        name: str,
        agg_type: AggregationType,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """聚合计算"""
        return self.collector.aggregate(name, agg_type, start, end, labels)
    
    def get_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """获取统计信息"""
        return self.collector.get_stats(name, labels)
    
    def generate_report(
        self,
        title: str = "指标报告",
        period_hours: int = 24
    ) -> MetricReport:
        """生成报告"""
        return self.reporter.generate_report(title, period_hours)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取服务摘要"""
        return {
            "running": self._running,
            "retention_days": self.retention_days,
            "registered_metrics": len(self.collector.definitions)
        }


# 便捷函数

def create_default_metrics_service() -> MetricsCollectionService:
    """创建默认指标收集服务"""
    return MetricsCollectionService()


# 全局服务实例
metrics_collection_service = MetricsCollectionService()
