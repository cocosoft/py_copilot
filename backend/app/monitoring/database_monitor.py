"""
数据库连接监控模块

监控数据库连接池状态、查询性能和连接健康状态。
"""
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseMetricType(Enum):
    """数据库指标类型枚举"""
    CONNECTION_COUNT = "connection_count"  # 连接数量
    QUERY_EXECUTION_TIME = "query_execution_time"  # 查询执行时间
    QUERY_COUNT = "query_count"  # 查询计数
    ERROR_COUNT = "error_count"  # 错误计数
    CONNECTION_POOL_SIZE = "connection_pool_size"  # 连接池大小


class DatabaseMetric:
    """数据库指标类"""
    
    def __init__(self, metric_type: DatabaseMetricType, value: float, timestamp: datetime, 
                 metadata: Optional[Dict[str, Any]] = None):
        """初始化数据库指标
        
        Args:
            metric_type: 指标类型
            value: 指标值
            timestamp: 时间戳
            metadata: 元数据
        """
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class DatabaseStats:
    """数据库统计类"""
    
    def __init__(self, window_size: int = 100):
        """初始化数据库统计
        
        Args:
            window_size: 统计窗口大小
        """
        self.window_size = window_size
        self.metrics: Dict[DatabaseMetricType, deque] = {}
        for metric_type in DatabaseMetricType:
            self.metrics[metric_type] = deque(maxlen=window_size)
        self.start_time = datetime.now()
        self.total_queries = 0
        self.total_errors = 0
        
    def add_metric(self, metric: DatabaseMetric):
        """添加数据库指标
        
        Args:
            metric: 数据库指标
        """
        self.metrics[metric.metric_type].append(metric)
        
        # 更新统计计数
        if metric.metric_type == DatabaseMetricType.QUERY_COUNT:
            self.total_queries += int(metric.value)
        elif metric.metric_type == DatabaseMetricType.ERROR_COUNT:
            self.total_errors += int(metric.value)
            
    def get_database_stats(self, metric_type: DatabaseMetricType) -> Dict[str, Any]:
        """获取指定指标类型的统计
        
        Args:
            metric_type: 指标类型
            
        Returns:
            指标统计信息
        """
        metrics = list(self.metrics[metric_type])
        
        if not metrics:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "current": 0
            }
            
        values = [m.value for m in metrics]
        current_value = metrics[-1].value if metrics else 0
        
        return {
            "count": len(values),
            "avg": sum(values) / len(values) if values else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "current": current_value
        }
        
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有数据库统计
        
        Returns:
            所有数据库统计信息
        """
        stats = {}
        for metric_type in DatabaseMetricType:
            stats[metric_type.value] = self.get_database_stats(metric_type)
            
        stats["window_size"] = self.window_size
        stats["start_time"] = self.start_time.isoformat()
        stats["total_queries"] = self.total_queries
        stats["total_errors"] = self.total_errors
        stats["error_rate"] = (self.total_errors / self.total_queries * 100) if self.total_queries > 0 else 0
        
        return stats


class DatabaseMonitor:
    """数据库监控器"""
    
    def __init__(self, database_path: str, window_size: int = 100, interval: float = 60.0):
        """初始化数据库监控器
        
        Args:
            database_path: 数据库文件路径
            window_size: 统计窗口大小
            interval: 监控间隔（秒）
        """
        self.database_path = database_path
        self.stats = DatabaseStats(window_size)
        self.interval = interval
        self.last_monitor_time = 0
        self.connection_pool_size = 10  # 默认连接池大小
        
    def collect_database_metrics(self):
        """收集数据库指标"""
        current_time = time.time()
        
        # 检查是否达到监控间隔
        if current_time - self.last_monitor_time < self.interval:
            return
            
        self.last_monitor_time = current_time
        timestamp = datetime.now()
        
        try:
            # 连接数据库并收集指标
            connection = sqlite3.connect(self.database_path)
            cursor = connection.cursor()
            
            # 收集数据库统计信息
            self._collect_connection_stats(cursor, timestamp)
            self._collect_query_stats(cursor, timestamp)
            self._collect_database_info(cursor, timestamp)
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"收集数据库指标失败: {e}")
            
    def _collect_connection_stats(self, cursor, timestamp: datetime):
        """收集连接统计信息
        
        Args:
            cursor: 数据库游标
            timestamp: 时间戳
        """
        try:
            # 获取当前连接数（估算）
            # SQLite没有直接的连接数查询，这里使用近似方法
            connection_count = self.connection_pool_size  # 使用配置的连接池大小
            
            metric = DatabaseMetric(
                metric_type=DatabaseMetricType.CONNECTION_COUNT,
                value=connection_count,
                timestamp=timestamp,
                metadata={"type": "estimated"}
            )
            self.stats.add_metric(metric)
            
            # 连接池大小
            pool_metric = DatabaseMetric(
                metric_type=DatabaseMetricType.CONNECTION_POOL_SIZE,
                value=self.connection_pool_size,
                timestamp=timestamp
            )
            self.stats.add_metric(pool_metric)
            
        except Exception as e:
            logger.error(f"收集连接统计信息失败: {e}")
            
    def _collect_query_stats(self, cursor, timestamp: datetime):
        """收集查询统计信息
        
        Args:
            cursor: 数据库游标
            timestamp: 时间戳
        """
        try:
            # 执行一个简单的查询来测量性能
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            result = cursor.fetchone()
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 查询执行时间
            time_metric = DatabaseMetric(
                metric_type=DatabaseMetricType.QUERY_EXECUTION_TIME,
                value=execution_time,
                timestamp=timestamp,
                metadata={"query_type": "system_table_count"}
            )
            self.stats.add_metric(time_metric)
            
            # 查询计数（每次监控增加1）
            count_metric = DatabaseMetric(
                metric_type=DatabaseMetricType.QUERY_COUNT,
                value=1,
                timestamp=timestamp
            )
            self.stats.add_metric(count_metric)
            
        except Exception as e:
            logger.error(f"收集查询统计信息失败: {e}")
            
            # 记录错误
            error_metric = DatabaseMetric(
                metric_type=DatabaseMetricType.ERROR_COUNT,
                value=1,
                timestamp=timestamp,
                metadata={"error_type": "query_execution", "message": str(e)}
            )
            self.stats.add_metric(error_metric)
            
    def _collect_database_info(self, cursor, timestamp: datetime):
        """收集数据库信息
        
        Args:
            cursor: 数据库游标
            timestamp: 时间戳
        """
        try:
            # 获取表数量
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # 获取数据库大小（文件大小）
            import os
            db_size = os.path.getsize(self.database_path) / 1024 / 1024  # MB
            
            # 这里可以添加更多数据库信息收集
            
        except Exception as e:
            logger.error(f"收集数据库信息失败: {e}")
            
    def get_database_summary(self) -> Dict[str, Any]:
        """获取数据库摘要
        
        Returns:
            数据库摘要信息
        """
        # 确保收集最新指标
        self.collect_database_metrics()
        
        return self.stats.get_all_stats()
        
    def check_database_health(self) -> Dict[str, Any]:
        """检查数据库健康状态
        
        Returns:
            数据库健康状态信息
        """
        summary = self.get_database_summary()
        
        # 获取关键指标
        query_time_avg = summary[DatabaseMetricType.QUERY_EXECUTION_TIME.value]["avg"]
        error_rate = summary["error_rate"]
        
        # 健康状态判断
        is_healthy = True
        warnings = []
        
        # 查询时间检查（超过100ms为警告）
        if query_time_avg > 100:
            warnings.append(f"平均查询时间过高: {query_time_avg:.2f}ms")
            is_healthy = False
            
        # 错误率检查（超过5%为警告）
        if error_rate > 5.0:
            warnings.append(f"数据库错误率过高: {error_rate:.2f}%")
            is_healthy = False
            
        # 数据库文件检查
        try:
            import os
            if not os.path.exists(self.database_path):
                warnings.append("数据库文件不存在")
                is_healthy = False
            else:
                # 检查文件大小（超过1GB为警告）
                db_size = os.path.getsize(self.database_path) / 1024 / 1024 / 1024  # GB
                if db_size > 1:
                    warnings.append(f"数据库文件过大: {db_size:.2f}GB")
                    is_healthy = False
        except Exception as e:
            warnings.append(f"数据库文件检查失败: {str(e)}")
            is_healthy = False
            
        return {
            "status": "healthy" if is_healthy else "warning",
            "timestamp": datetime.now().isoformat(),
            "query_time_avg_ms": query_time_avg,
            "error_rate": error_rate,
            "total_queries": summary["total_queries"],
            "warnings": warnings,
            "is_healthy": is_healthy,
            "database_path": self.database_path
        }
        
    def get_database_trend(self, metric_type: DatabaseMetricType, hours: int = 24) -> List[Dict[str, Any]]:
        """获取数据库趋势数据
        
        Args:
            metric_type: 指标类型
            hours: 时间范围（小时）
            
        Returns:
            数据库趋势数据
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指定时间范围内的指标
        recent_metrics = [
            m for m in self.stats.metrics[metric_type]
            if m.timestamp >= cutoff_time
        ]
        
        return [metric.to_dict() for metric in recent_metrics]
        
    def set_connection_pool_size(self, size: int):
        """设置连接池大小
        
        Args:
            size: 连接池大小
        """
        self.connection_pool_size = size
        logger.info(f"数据库连接池大小设置为: {size}")


# 全局数据库监控器实例
database_monitor = DatabaseMonitor("backend/py_copilot.db")