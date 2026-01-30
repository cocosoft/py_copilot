"""
性能监控中间件

负责监控API请求性能、内存使用情况和错误率统计。
"""
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from enum import Enum

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型枚举"""
    RESPONSE_TIME = "response_time"
    MEMORY_USAGE = "memory_usage"
    ERROR_RATE = "error_rate"
    REQUEST_COUNT = "request_count"


class PerformanceMetric:
    """性能指标类"""
    
    def __init__(self, metric_type: MetricType, value: float, timestamp: datetime, 
                 metadata: Optional[Dict[str, Any]] = None):
        """初始化性能指标
        
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


class PerformanceStats:
    """性能统计类"""
    
    def __init__(self, window_size: int = 100):
        """初始化性能统计
        
        Args:
            window_size: 统计窗口大小
        """
        self.window_size = window_size
        self.metrics: Dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.error_count = 0
        self.total_requests = 0
        self.start_time = datetime.now()
        
    def add_metric(self, metric: PerformanceMetric):
        """添加性能指标
        
        Args:
            metric: 性能指标
        """
        self.metrics[metric.metric_type].append(metric)
        
    def record_request(self, is_error: bool = False):
        """记录请求统计
        
        Args:
            is_error: 是否为错误请求
        """
        self.total_requests += 1
        if is_error:
            self.error_count += 1
            
    def get_response_time_stats(self) -> Dict[str, Any]:
        """获取响应时间统计
        
        Returns:
            响应时间统计信息
        """
        response_times = [m.value for m in self.metrics[MetricType.RESPONSE_TIME]]
        
        if not response_times:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "p95": 0,
                "p99": 0
            }
            
        sorted_times = sorted(response_times)
        count = len(response_times)
        
        return {
            "count": count,
            "avg": sum(response_times) / count,
            "min": min(response_times),
            "max": max(response_times),
            "p95": sorted_times[int(count * 0.95)],
            "p99": sorted_times[int(count * 0.99)]
        }
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存使用统计
        
        Returns:
            内存使用统计信息
        """
        memory_usage = [m.value for m in self.metrics[MetricType.MEMORY_USAGE]]
        
        if not memory_usage:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0
            }
            
        return {
            "count": len(memory_usage),
            "avg": sum(memory_usage) / len(memory_usage),
            "min": min(memory_usage),
            "max": max(memory_usage)
        }
        
    def get_error_rate(self) -> float:
        """获取错误率
        
        Returns:
            错误率（百分比）
        """
        if self.total_requests == 0:
            return 0.0
            
        return (self.error_count / self.total_requests) * 100
        
    def get_request_stats(self) -> Dict[str, Any]:
        """获取请求统计
        
        Returns:
            请求统计信息
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "error_rate": self.get_error_rate(),
            "uptime_seconds": uptime,
            "requests_per_second": self.total_requests / uptime if uptime > 0 else 0
        }
        
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要
        
        Returns:
            性能摘要信息
        """
        return {
            "response_time": self.get_response_time_stats(),
            "memory_usage": self.get_memory_stats(),
            "request_stats": self.get_request_stats(),
            "window_size": self.window_size,
            "start_time": self.start_time.isoformat()
        }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, window_size: int = 100):
        """初始化性能监控器
        
        Args:
            window_size: 统计窗口大小
        """
        self.stats = PerformanceStats(window_size)
        self.process = psutil.Process()
        
    def record_request_start(self, request: Request):
        """记录请求开始
        
        Args:
            request: 请求对象
        """
        # 在请求对象中存储开始时间
        request.state.start_time = time.time()
        
    def record_request_end(self, request: Request, response: Response, is_error: bool = False):
        """记录请求结束
        
        Args:
            request: 请求对象
            response: 响应对象
            is_error: 是否为错误请求
        """
        # 计算响应时间
        if hasattr(request.state, 'start_time'):
            response_time = (time.time() - request.state.start_time) * 1000  # 转换为毫秒
            
            # 记录响应时间指标
            metric = PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                value=response_time,
                timestamp=datetime.now(),
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code
                }
            )
            self.stats.add_metric(metric)
            
        # 记录内存使用指标
        memory_usage = self.process.memory_info().rss / 1024 / 1024  # 转换为MB
        memory_metric = PerformanceMetric(
            metric_type=MetricType.MEMORY_USAGE,
            value=memory_usage,
            timestamp=datetime.now()
        )
        self.stats.add_metric(memory_metric)
        
        # 记录请求统计
        self.stats.record_request(is_error)
        
    def record_error(self, request: Request, error: Exception):
        """记录错误
        
        Args:
            request: 请求对象
            error: 异常对象
        """
        # 记录错误请求
        self.stats.record_request(is_error=True)
        
        # 记录错误详情
        logger.error(f"请求错误: {request.method} {request.url.path} - {error}")
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要
        
        Returns:
            性能摘要信息
        """
        return self.stats.get_summary()
        
    def get_recent_metrics(self, metric_type: MetricType, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的指标数据
        
        Args:
            metric_type: 指标类型
            limit: 限制数量
            
        Returns:
            指标数据列表
        """
        metrics = list(self.stats.metrics[metric_type])
        recent_metrics = metrics[-limit:] if len(metrics) > limit else metrics
        
        return [metric.to_dict() for metric in recent_metrics]


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, monitor: PerformanceMonitor):
        """初始化性能监控中间件
        
        Args:
            app: FastAPI应用
            monitor: 性能监控器
        """
        super().__init__(app)
        self.monitor = monitor
        
    async def dispatch(self, request: Request, call_next):
        """处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            响应对象
        """
        # 记录请求开始
        self.monitor.record_request_start(request)
        
        response = None
        is_error = False
        
        try:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)
            
            # 检查是否为错误响应
            if response.status_code >= 400:
                is_error = True
                
            return response
            
        except Exception as e:
            # 记录异常
            is_error = True
            self.monitor.record_error(request, e)
            
            # 重新抛出异常
            raise
            
        finally:
            # 记录请求结束
            if response is not None:
                self.monitor.record_request_end(request, response, is_error)


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()