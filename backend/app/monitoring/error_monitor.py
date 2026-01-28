"""
错误率统计模块

提供详细的错误监控和统计功能，包括错误分类、错误趋势分析和错误详情记录。
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度枚举"""
    LOW = "low"  # 低严重度
    MEDIUM = "medium"  # 中等严重度
    HIGH = "high"  # 高严重度
    CRITICAL = "critical"  # 严重


class ErrorType(Enum):
    """错误类型枚举"""
    VALIDATION_ERROR = "validation_error"  # 验证错误
    AUTHENTICATION_ERROR = "authentication_error"  # 认证错误
    AUTHORIZATION_ERROR = "authorization_error"  # 授权错误
    DATABASE_ERROR = "database_error"  # 数据库错误
    EXTERNAL_SERVICE_ERROR = "external_service_error"  # 外部服务错误
    INTERNAL_SERVER_ERROR = "internal_server_error"  # 内部服务器错误
    TIMEOUT_ERROR = "timeout_error"  # 超时错误
    UNKNOWN_ERROR = "unknown_error"  # 未知错误


class ErrorRecord:
    """错误记录类"""
    
    def __init__(self, error_type: ErrorType, severity: ErrorSeverity, 
                 message: str, timestamp: datetime, metadata: Optional[Dict[str, Any]] = None):
        """初始化错误记录
        
        Args:
            error_type: 错误类型
            severity: 错误严重程度
            message: 错误消息
            timestamp: 时间戳
            metadata: 元数据
        """
        self.error_type = error_type
        self.severity = severity
        self.message = message
        self.timestamp = timestamp
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class ErrorStats:
    """错误统计类"""
    
    def __init__(self, window_size: int = 1000):
        """初始化错误统计
        
        Args:
            window_size: 统计窗口大小
        """
        self.window_size = window_size
        self.error_records: deque = deque(maxlen=window_size)
        self.error_counts: Dict[ErrorType, int] = defaultdict(int)
        self.severity_counts: Dict[ErrorSeverity, int] = defaultdict(int)
        self.total_errors = 0
        self.start_time = datetime.now()
        
    def add_error(self, error_record: ErrorRecord):
        """添加错误记录
        
        Args:
            error_record: 错误记录
        """
        self.error_records.append(error_record)
        self.error_counts[error_record.error_type] += 1
        self.severity_counts[error_record.severity] += 1
        self.total_errors += 1
        
    def get_error_rate(self, time_window_minutes: int = 60) -> float:
        """获取错误率
        
        Args:
            time_window_minutes: 时间窗口（分钟）
            
        Returns:
            错误率（百分比）
        """
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        # 计算时间窗口内的错误数量
        recent_errors = [
            error for error in self.error_records
            if error.timestamp >= cutoff_time
        ]
        
        # 计算时间窗口内的请求数量（估算）
        # 这里使用平均请求速率来估算
        uptime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        if uptime_minutes == 0:
            return 0.0
            
        avg_requests_per_minute = self.total_errors / uptime_minutes
        estimated_requests = avg_requests_per_minute * time_window_minutes
        
        if estimated_requests == 0:
            return 0.0
            
        return (len(recent_errors) / estimated_requests) * 100
        
    def get_error_distribution(self) -> Dict[str, Any]:
        """获取错误分布
        
        Returns:
            错误分布信息
        """
        return {
            "by_type": {error_type.value: count for error_type, count in self.error_counts.items()},
            "by_severity": {severity.value: count for severity, count in self.severity_counts.items()},
            "total_errors": self.total_errors
        }
        
    def get_error_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取错误趋势
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            错误趋势数据
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 按小时分组统计错误数量
        hourly_counts = defaultdict(int)
        
        for error in self.error_records:
            if error.timestamp >= cutoff_time:
                hour_key = error.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_counts[hour_key] += 1
                
        # 转换为时间序列数据
        trend_data = []
        current_time = cutoff_time.replace(minute=0, second=0, microsecond=0)
        end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        while current_time <= end_time:
            count = hourly_counts.get(current_time, 0)
            trend_data.append({
                "timestamp": current_time.isoformat(),
                "error_count": count
            })
            current_time += timedelta(hours=1)
            
        return trend_data
        
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的错误记录
        
        Args:
            limit: 限制数量
            
        Returns:
            最近的错误记录
        """
        recent_errors = list(self.error_records)[-limit:]
        return [error.to_dict() for error in recent_errors]
        
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要
        
        Returns:
            错误摘要信息
        """
        return {
            "error_distribution": self.get_error_distribution(),
            "error_rate_1h": self.get_error_rate(60),
            "error_rate_24h": self.get_error_rate(1440),
            "recent_errors": self.get_recent_errors(5),
            "window_size": self.window_size,
            "start_time": self.start_time.isoformat()
        }


class ErrorMonitor:
    """错误监控器"""
    
    def __init__(self, window_size: int = 1000):
        """初始化错误监控器
        
        Args:
            window_size: 统计窗口大小
        """
        self.stats = ErrorStats(window_size)
        
    def record_error(self, error_type: ErrorType, severity: ErrorSeverity, 
                    message: str, metadata: Optional[Dict[str, Any]] = None):
        """记录错误
        
        Args:
            error_type: 错误类型
            severity: 错误严重程度
            message: 错误消息
            metadata: 元数据
        """
        error_record = ErrorRecord(
            error_type=error_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.stats.add_error(error_record)
        
        # 根据严重程度记录日志
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"严重错误: {message}")
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"高严重度错误: {message}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"中等严重度错误: {message}")
        else:
            logger.info(f"低严重度错误: {message}")
            
    def record_http_error(self, status_code: int, message: str, 
                         path: str, method: str, metadata: Optional[Dict[str, Any]] = None):
        """记录HTTP错误
        
        Args:
            status_code: HTTP状态码
            message: 错误消息
            path: 请求路径
            method: 请求方法
            metadata: 元数据
        """
        # 根据状态码确定错误类型和严重程度
        error_type, severity = self._classify_http_error(status_code)
        
        # 构建元数据
        error_metadata = {
            "status_code": status_code,
            "path": path,
            "method": method
        }
        if metadata:
            error_metadata.update(metadata)
            
        self.record_error(error_type, severity, message, error_metadata)
        
    def _classify_http_error(self, status_code: int) -> Tuple[ErrorType, ErrorSeverity]:
        """分类HTTP错误
        
        Args:
            status_code: HTTP状态码
            
        Returns:
            (错误类型, 严重程度)
        """
        if 400 <= status_code < 500:
            if status_code == 401:
                return ErrorType.AUTHENTICATION_ERROR, ErrorSeverity.MEDIUM
            elif status_code == 403:
                return ErrorType.AUTHORIZATION_ERROR, ErrorSeverity.MEDIUM
            elif status_code == 404:
                return ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW
            elif status_code == 422:
                return ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW
            else:
                return ErrorType.VALIDATION_ERROR, ErrorSeverity.MEDIUM
        elif status_code >= 500:
            if status_code == 503:
                return ErrorType.EXTERNAL_SERVICE_ERROR, ErrorSeverity.HIGH
            else:
                return ErrorType.INTERNAL_SERVER_ERROR, ErrorSeverity.HIGH
        else:
            return ErrorType.UNKNOWN_ERROR, ErrorSeverity.MEDIUM
            
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要
        
        Returns:
            错误摘要信息
        """
        return self.stats.get_error_summary()
        
    def check_error_health(self, error_rate_threshold: float = 5.0) -> Dict[str, Any]:
        """检查错误健康状态
        
        Args:
            error_rate_threshold: 错误率阈值（百分比）
            
        Returns:
            错误健康状态信息
        """
        summary = self.get_error_summary()
        error_rate_1h = summary["error_rate_1h"]
        error_rate_24h = summary["error_rate_24h"]
        
        # 健康状态判断
        is_healthy = True
        warnings = []
        
        # 1小时错误率检查
        if error_rate_1h > error_rate_threshold:
            warnings.append(f"1小时错误率过高: {error_rate_1h:.2f}%")
            is_healthy = False
            
        # 24小时错误率检查
        if error_rate_24h > error_rate_threshold:
            warnings.append(f"24小时错误率过高: {error_rate_24h:.2f}%")
            is_healthy = False
            
        # 严重错误检查
        critical_errors = summary["error_distribution"]["by_severity"].get("critical", 0)
        if critical_errors > 0:
            warnings.append(f"存在 {critical_errors} 个严重错误")
            is_healthy = False
            
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error_rate_1h": error_rate_1h,
            "error_rate_24h": error_rate_24h,
            "total_errors": summary["error_distribution"]["total_errors"],
            "warnings": warnings,
            "is_healthy": is_healthy
        }


# 全局错误监控器实例
error_monitor = ErrorMonitor()