#!/usr/bin/env python3
"""
监控告警服务

提供系统监控和告警功能，包括：
- 任务执行监控
- 性能指标监控
- 错误告警
- 资源使用监控
"""

import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """告警类型"""
    TASK_FAILED = "task_failed"
    TASK_TIMEOUT = "task_timeout"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    LOW_SUCCESS_RATE = "low_success_rate"
    RESOURCE_HIGH = "resource_high"
    SYSTEM_ERROR = "system_error"


@dataclass
class Alert:
    """告警信息"""
    id: str
    type: AlertType
    level: AlertLevel
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class Metric:
    """指标数据"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


class MonitoringService:
    """
    监控告警服务
    
    单例模式提供系统监控功能
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if self._initialized:
            return
        
        self.config = config or {}
        
        # 告警配置
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alerts: List[Alert] = []
        self.max_alerts = self.config.get('max_alerts', 1000)
        
        # 指标数据
        self.metrics: Dict[str, List[Metric]] = {}
        self.max_metrics_per_type = self.config.get('max_metrics_per_type', 10000)
        
        # 任务统计
        self.task_stats: Dict[str, Dict[str, Any]] = {}
        
        # 性能阈值
        self.thresholds = {
            'task_timeout_seconds': self.config.get('task_timeout_seconds', 3600),
            'high_latency_ms': self.config.get('high_latency_ms', 5000),
            'high_error_rate': self.config.get('high_error_rate', 0.1),
            'low_success_rate': self.config.get('low_success_rate', 0.9),
            'max_memory_percent': self.config.get('max_memory_percent', 90),
            'max_cpu_percent': self.config.get('max_cpu_percent', 80),
        }
        
        # 启动监控线程
        self._monitoring = False
        self._monitor_thread = None
        
        self._initialized = True
        logger.info("监控告警服务初始化完成")
    
    def start_monitoring(self, interval: int = 60):
        """
        启动监控线程
        
        Args:
            interval: 监控间隔（秒）
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        logger.info(f"监控线程已启动，间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控线程"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("监控线程已停止")
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self._monitoring:
            try:
                self._check_system_health()
                self._check_task_health()
                self._cleanup_old_data()
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
            
            time.sleep(interval)
    
    def _check_system_health(self):
        """检查系统健康状态"""
        try:
            import psutil
            
            # 检查内存使用
            memory = psutil.virtual_memory()
            if memory.percent > self.thresholds['max_memory_percent']:
                self.create_alert(
                    AlertType.RESOURCE_HIGH,
                    AlertLevel.WARNING,
                    f"内存使用率过高: {memory.percent}%",
                    {'memory_percent': memory.percent, 'threshold': self.thresholds['max_memory_percent']}
                )
            
            # 检查CPU使用
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.thresholds['max_cpu_percent']:
                self.create_alert(
                    AlertType.RESOURCE_HIGH,
                    AlertLevel.WARNING,
                    f"CPU使用率过高: {cpu_percent}%",
                    {'cpu_percent': cpu_percent, 'threshold': self.thresholds['max_cpu_percent']}
                )
            
            # 记录指标
            self.record_metric('system_memory_percent', memory.percent)
            self.record_metric('system_cpu_percent', cpu_percent)
            
        except ImportError:
            logger.warning("psutil未安装，无法监控系统资源")
    
    def _check_task_health(self):
        """检查任务健康状态"""
        for task_id, stats in self.task_stats.items():
            total = stats.get('total', 0)
            if total == 0:
                continue
            
            success = stats.get('success', 0)
            failed = stats.get('failed', 0)
            
            success_rate = success / total if total > 0 else 0
            error_rate = failed / total if total > 0 else 0
            
            # 检查成功率
            if success_rate < self.thresholds['low_success_rate'] and total > 10:
                self.create_alert(
                    AlertType.LOW_SUCCESS_RATE,
                    AlertLevel.ERROR,
                    f"任务成功率过低: {success_rate:.1%} (任务: {task_id})",
                    {'task_id': task_id, 'success_rate': success_rate, 'total': total}
                )
            
            # 检查错误率
            if error_rate > self.thresholds['high_error_rate'] and total > 10:
                self.create_alert(
                    AlertType.HIGH_ERROR_RATE,
                    AlertLevel.ERROR,
                    f"任务错误率过高: {error_rate:.1%} (任务: {task_id})",
                    {'task_id': task_id, 'error_rate': error_rate, 'total': total}
                )
    
    def _cleanup_old_data(self):
        """清理过期数据"""
        # 清理过期告警
        cutoff_time = datetime.now() - timedelta(days=7)
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
        
        # 限制告警数量
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # 清理过期指标
        cutoff_time = datetime.now() - timedelta(hours=24)
        for metric_name in self.metrics:
            self.metrics[metric_name] = [
                m for m in self.metrics[metric_name] 
                if m.timestamp > cutoff_time
            ]
            
            # 限制指标数量
            if len(self.metrics[metric_name]) > self.max_metrics_per_type:
                self.metrics[metric_name] = self.metrics[metric_name][-self.max_metrics_per_type:]
    
    def create_alert(self, 
                     alert_type: AlertType, 
                     level: AlertLevel, 
                     message: str,
                     details: Optional[Dict[str, Any]] = None) -> Alert:
        """
        创建告警
        
        Args:
            alert_type: 告警类型
            level: 告警级别
            message: 告警消息
            details: 详细信息
        
        Returns:
            告警对象
        """
        import uuid
        
        alert = Alert(
            id=str(uuid.uuid4()),
            type=alert_type,
            level=level,
            message=message,
            timestamp=datetime.now(),
            details=details or {}
        )
        
        self.alerts.append(alert)
        
        # 触发告警处理器
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")
        
        # 记录日志
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical,
        }.get(level, logger.info)
        
        log_func(f"[{level.upper()}] {message}")
        
        return alert
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """
        确认告警
        
        Args:
            alert_id: 告警ID
            user: 确认用户
        
        Returns:
            是否成功
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = user
                alert.acknowledged_at = datetime.now()
                logger.info(f"告警已确认: {alert_id} (用户: {user})")
                return True
        return False
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            labels: 标签
        """
        if name not in self.metrics:
            self.metrics[name] = []
        
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {}
        )
        
        self.metrics[name].append(metric)
    
    def record_task_start(self, task_id: str, task_type: str):
        """记录任务开始"""
        if task_id not in self.task_stats:
            self.task_stats[task_id] = {
                'type': task_type,
                'total': 0,
                'success': 0,
                'failed': 0,
                'start_times': [],
                'durations': [],
            }
        
        self.task_stats[task_id]['start_times'].append(datetime.now())
    
    def record_task_end(self, task_id: str, success: bool, duration_ms: float):
        """记录任务结束"""
        if task_id not in self.task_stats:
            return
        
        stats = self.task_stats[task_id]
        stats['total'] += 1
        
        if success:
            stats['success'] += 1
        else:
            stats['failed'] += 1
        
        stats['durations'].append(duration_ms)
        
        # 记录指标
        self.record_metric('task_duration_ms', duration_ms, {'task_id': task_id})
        self.record_metric('task_success', 1 if success else 0, {'task_id': task_id})
        
        # 检查性能阈值
        if duration_ms > self.thresholds['high_latency_ms']:
            self.create_alert(
                AlertType.HIGH_LATENCY,
                AlertLevel.WARNING,
                f"任务执行时间过长: {duration_ms:.0f}ms (任务: {task_id})",
                {'task_id': task_id, 'duration_ms': duration_ms}
            )
    
    def record_task_error(self, task_id: str, error_message: str):
        """记录任务错误"""
        self.create_alert(
            AlertType.TASK_FAILED,
            AlertLevel.ERROR,
            f"任务执行失败: {error_message} (任务: {task_id})",
            {'task_id': task_id, 'error': error_message}
        )
    
    def get_alerts(self, 
                   level: Optional[AlertLevel] = None,
                   alert_type: Optional[AlertType] = None,
                   acknowledged: Optional[bool] = None,
                   limit: int = 100) -> List[Alert]:
        """
        获取告警列表
        
        Args:
            level: 告警级别过滤
            alert_type: 告警类型过滤
            acknowledged: 确认状态过滤
            limit: 返回数量限制
        
        Returns:
            告警列表
        """
        alerts = self.alerts
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if alert_type:
            alerts = [a for a in alerts if a.type == alert_type]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        # 按时间倒序
        alerts = sorted(alerts, key=lambda a: a.timestamp, reverse=True)
        
        return alerts[:limit]
    
    def get_metrics(self, 
                    name: str,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> List[Metric]:
        """
        获取指标数据
        
        Args:
            name: 指标名称
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            指标列表
        """
        metrics = self.metrics.get(name, [])
        
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        
        return metrics
    
    def get_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        return {
            'alerts': {
                'total': len(self.alerts),
                'unacknowledged': len([a for a in self.alerts if not a.acknowledged]),
                'by_level': {
                    level.value: len([a for a in self.alerts if a.level == level])
                    for level in AlertLevel
                }
            },
            'metrics': {
                name: len(metrics) for name, metrics in self.metrics.items()
            },
            'tasks': {
                'total': len(self.task_stats),
                'stats': self.task_stats
            }
        }
    
    def register_alert_handler(self, handler: Callable[[Alert], None]):
        """注册告警处理器"""
        self.alert_handlers.append(handler)
    
    def export_alerts(self, filepath: str):
        """导出告警到文件"""
        data = [
            {
                'id': a.id,
                'type': a.type.value,
                'level': a.level.value,
                'message': a.message,
                'timestamp': a.timestamp.isoformat(),
                'details': a.details,
                'acknowledged': a.acknowledged,
                'acknowledged_by': a.acknowledged_by,
                'acknowledged_at': a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            }
            for a in self.alerts
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"告警已导出到: {filepath}")


# 便捷函数
def get_monitoring_service(config: Optional[Dict[str, Any]] = None) -> MonitoringService:
    """获取监控服务实例"""
    return MonitoringService(config)


def record_task_metric(task_id: str, task_type: str, success: bool, duration_ms: float):
    """便捷函数：记录任务指标"""
    service = get_monitoring_service()
    service.record_task_end(task_id, success, duration_ms)


def create_system_alert(message: str, level: AlertLevel = AlertLevel.WARNING):
    """便捷函数：创建系统告警"""
    service = get_monitoring_service()
    return service.create_alert(AlertType.SYSTEM_ERROR, level, message)


# 默认告警处理器
def default_alert_handler(alert: Alert):
    """默认告警处理器 - 记录到日志"""
    logger.warning(f"[ALERT] {alert.level.value}: {alert.message}")


if __name__ == '__main__':
    # 测试监控服务
    service = MonitoringService({
        'high_latency_ms': 1000,
        'high_error_rate': 0.2,
    })
    
    # 注册告警处理器
    service.register_alert_handler(default_alert_handler)
    
    # 启动监控
    service.start_monitoring(interval=5)
    
    # 模拟任务
    service.record_task_start('task_1', 'entity_extraction')
    time.sleep(0.5)
    service.record_task_end('task_1', True, 500)
    
    # 创建测试告警
    service.create_alert(
        AlertType.TASK_FAILED,
        AlertLevel.ERROR,
        "测试告警消息",
        {'test': True}
    )
    
    # 打印统计
    print("\n监控统计:")
    print(json.dumps(service.get_stats(), indent=2, default=str))
    
    # 停止监控
    time.sleep(2)
    service.stop_monitoring()
