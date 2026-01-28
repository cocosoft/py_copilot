"""
API调用统计模块

监控API端点的调用情况、响应时间和错误率。
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)


class APIMetricType(Enum):
    """API指标类型枚举"""
    RESPONSE_TIME = "response_time"  # 响应时间
    CALL_COUNT = "call_count"  # 调用计数
    ERROR_COUNT = "error_count"  # 错误计数
    SUCCESS_RATE = "success_rate"  # 成功率
    THROUGHPUT = "throughput"  # 吞吐量


class APIEndpoint:
    """API端点类"""
    
    def __init__(self, path: str, method: str):
        """初始化API端点
        
        Args:
            path: API路径
            method: HTTP方法
        """
        self.path = path
        self.method = method
        self.endpoint_key = f"{method}:{path}"
        self.call_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.last_call_time = None
        self.response_times: deque = deque(maxlen=100)  # 保留最近100次响应时间
        
    def record_call(self, response_time: float, is_error: bool = False):
        """记录API调用
        
        Args:
            response_time: 响应时间（秒）
            is_error: 是否错误
        """
        self.call_count += 1
        self.total_response_time += response_time
        self.response_times.append(response_time)
        self.last_call_time = datetime.now()
        
        if is_error:
            self.error_count += 1
            
    def get_stats(self) -> Dict[str, Any]:
        """获取端点统计
        
        Returns:
            端点统计信息
        """
        avg_response_time = (self.total_response_time / self.call_count) if self.call_count > 0 else 0
        success_rate = ((self.call_count - self.error_count) / self.call_count * 100) if self.call_count > 0 else 100
        
        return {
            "path": self.path,
            "method": self.method,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "last_call_time": self.last_call_time.isoformat() if self.last_call_time else None,
            "recent_response_times": list(self.response_times)
        }


class APIMetric:
    """API指标类"""
    
    def __init__(self, metric_type: APIMetricType, value: float, timestamp: datetime, 
                 metadata: Optional[Dict[str, Any]] = None):
        """初始化API指标
        
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


class APIStats:
    """API统计类"""
    
    def __init__(self, window_size: int = 100):
        """初始化API统计
        
        Args:
            window_size: 统计窗口大小
        """
        self.window_size = window_size
        self.metrics: Dict[APIMetricType, deque] = {}
        for metric_type in APIMetricType:
            self.metrics[metric_type] = deque(maxlen=window_size)
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.start_time = datetime.now()
        self.total_calls = 0
        self.total_errors = 0
        
    def add_metric(self, metric: APIMetric):
        """添加API指标
        
        Args:
            metric: API指标
        """
        self.metrics[metric.metric_type].append(metric)
        
    def record_api_call(self, path: str, method: str, response_time: float, is_error: bool = False):
        """记录API调用
        
        Args:
            path: API路径
            method: HTTP方法
            response_time: 响应时间（秒）
            is_error: 是否错误
        """
        endpoint_key = f"{method}:{path}"
        
        if endpoint_key not in self.endpoints:
            self.endpoints[endpoint_key] = APIEndpoint(path, method)
            
        endpoint = self.endpoints[endpoint_key]
        endpoint.record_call(response_time, is_error)
        
        self.total_calls += 1
        if is_error:
            self.total_errors += 1
            
        # 记录全局指标
        timestamp = datetime.now()
        
        # 响应时间指标
        response_time_metric = APIMetric(
            metric_type=APIMetricType.RESPONSE_TIME,
            value=response_time * 1000,  # 转换为毫秒
            timestamp=timestamp,
            metadata={"path": path, "method": method}
        )
        self.add_metric(response_time_metric)
        
        # 调用计数指标
        call_count_metric = APIMetric(
            metric_type=APIMetricType.CALL_COUNT,
            value=1,
            timestamp=timestamp
        )
        self.add_metric(call_count_metric)
        
        if is_error:
            # 错误计数指标
            error_metric = APIMetric(
                metric_type=APIMetricType.ERROR_COUNT,
                value=1,
                timestamp=timestamp
            )
            self.add_metric(error_metric)
            
    def get_api_stats(self, metric_type: APIMetricType) -> Dict[str, Any]:
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
        """获取所有API统计
        
        Returns:
            所有API统计信息
        """
        stats = {}
        for metric_type in APIMetricType:
            stats[metric_type.value] = self.get_api_stats(metric_type)
            
        # 端点统计
        endpoint_stats = {}
        for endpoint_key, endpoint in self.endpoints.items():
            endpoint_stats[endpoint_key] = endpoint.get_stats()
            
        stats["endpoints"] = endpoint_stats
        stats["total_calls"] = self.total_calls
        stats["total_errors"] = self.total_errors
        stats["overall_success_rate"] = ((self.total_calls - self.total_errors) / self.total_calls * 100) if self.total_calls > 0 else 100
        stats["window_size"] = self.window_size
        stats["start_time"] = self.start_time.isoformat()
        
        return stats
        
    def get_endpoint_stats(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """获取指定端点的统计
        
        Args:
            path: API路径
            method: HTTP方法
            
        Returns:
            端点统计信息，如果不存在返回None
        """
        endpoint_key = f"{method}:{path}"
        if endpoint_key in self.endpoints:
            return self.endpoints[endpoint_key].get_stats()
        return None
        
    def get_top_endpoints(self, limit: int = 10, sort_by: str = "call_count") -> List[Dict[str, Any]]:
        """获取排名靠前的端点
        
        Args:
            limit: 限制数量
            sort_by: 排序字段（call_count, error_count, avg_response_time）
            
        Returns:
            端点统计列表
        """
        endpoints_list = []
        for endpoint in self.endpoints.values():
            stats = endpoint.get_stats()
            endpoints_list.append(stats)
            
        # 排序
        if sort_by == "call_count":
            endpoints_list.sort(key=lambda x: x["call_count"], reverse=True)
        elif sort_by == "error_count":
            endpoints_list.sort(key=lambda x: x["error_count"], reverse=True)
        elif sort_by == "avg_response_time":
            endpoints_list.sort(key=lambda x: x["avg_response_time"], reverse=True)
            
        return endpoints_list[:limit]


class APIMonitor:
    """API监控器"""
    
    def __init__(self, window_size: int = 100):
        """初始化API监控器
        
        Args:
            window_size: 统计窗口大小
        """
        self.stats = APIStats(window_size)
        
    def record_api_call(self, path: str, method: str, response_time: float, is_error: bool = False):
        """记录API调用
        
        Args:
            path: API路径
            method: HTTP方法
            response_time: 响应时间（秒）
            is_error: 是否错误
        """
        self.stats.record_api_call(path, method, response_time, is_error)
        
        # 记录日志
        if is_error:
            logger.warning(f"API调用错误: {method} {path}, 响应时间: {response_time:.3f}s")
        else:
            logger.debug(f"API调用: {method} {path}, 响应时间: {response_time:.3f}s")
            
    def get_api_summary(self) -> Dict[str, Any]:
        """获取API摘要
        
        Returns:
            API摘要信息
        """
        return self.stats.get_all_stats()
        
    def check_api_health(self, response_time_threshold: float = 5.0, error_rate_threshold: float = 5.0) -> Dict[str, Any]:
        """检查API健康状态
        
        Args:
            response_time_threshold: 响应时间阈值（秒）
            error_rate_threshold: 错误率阈值（百分比）
            
        Returns:
            API健康状态信息
        """
        summary = self.get_api_summary()
        
        # 获取关键指标
        response_time_avg = summary[APIMetricType.RESPONSE_TIME.value]["avg"] / 1000  # 转换为秒
        overall_error_rate = summary["overall_success_rate"]
        
        # 健康状态判断
        is_healthy = True
        warnings = []
        problematic_endpoints = []
        
        # 响应时间检查
        if response_time_avg > response_time_threshold:
            warnings.append(f"平均响应时间过高: {response_time_avg:.2f}s")
            is_healthy = False
            
        # 错误率检查
        if overall_error_rate < (100 - error_rate_threshold):
            warnings.append(f"总体错误率过高: {100 - overall_error_rate:.2f}%")
            is_healthy = False
            
        # 检查各个端点的健康状态
        for endpoint_key, endpoint_stats in summary["endpoints"].items():
            endpoint_response_time = endpoint_stats["avg_response_time"] / 1000  # 转换为秒
            endpoint_error_rate = 100 - endpoint_stats["success_rate"]
            
            if endpoint_response_time > response_time_threshold or endpoint_error_rate > error_rate_threshold:
                problematic_endpoints.append({
                    "endpoint": endpoint_key,
                    "response_time": endpoint_response_time,
                    "error_rate": endpoint_error_rate
                })
                
        if problematic_endpoints:
            warnings.append(f"发现 {len(problematic_endpoints)} 个有问题的端点")
            is_healthy = False
            
        return {
            "status": "healthy" if is_healthy else "warning",
            "timestamp": datetime.now().isoformat(),
            "response_time_avg_s": response_time_avg,
            "overall_error_rate": 100 - overall_error_rate,
            "total_calls": summary["total_calls"],
            "total_endpoints": len(summary["endpoints"]),
            "warnings": warnings,
            "problematic_endpoints": problematic_endpoints,
            "is_healthy": is_healthy
        }
        
    def get_api_trend(self, metric_type: APIMetricType, hours: int = 24) -> List[Dict[str, Any]]:
        """获取API趋势数据
        
        Args:
            metric_type: 指标类型
            hours: 时间范围（小时）
            
        Returns:
            API趋势数据
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指定时间范围内的指标
        recent_metrics = [
            m for m in self.stats.metrics[metric_type]
            if m.timestamp >= cutoff_time
        ]
        
        return [metric.to_dict() for metric in recent_metrics]
        
    def get_endpoint_analysis(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """获取端点分析
        
        Args:
            path: API路径
            method: HTTP方法
            
        Returns:
            端点分析信息，如果不存在返回None
        """
        return self.stats.get_endpoint_stats(path, method)
        
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告
        
        Returns:
            性能报告
        """
        summary = self.get_api_summary()
        
        # 获取最活跃的端点
        top_called = self.stats.get_top_endpoints(5, "call_count")
        top_errors = self.stats.get_top_endpoints(5, "error_count")
        top_slow = self.stats.get_top_endpoints(5, "avg_response_time")
        
        return {
            "summary": {
                "total_calls": summary["total_calls"],
                "total_errors": summary["total_errors"],
                "success_rate": summary["overall_success_rate"],
                "avg_response_time_ms": summary[APIMetricType.RESPONSE_TIME.value]["avg"]
            },
            "top_called_endpoints": top_called,
            "top_error_endpoints": top_errors,
            "top_slow_endpoints": top_slow,
            "timestamp": datetime.now().isoformat()
        }


# 全局API监控器实例
api_monitor = APIMonitor()