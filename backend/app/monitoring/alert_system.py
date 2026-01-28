"""
预警系统模块

实现性能阈值配置、预警通知机制和预警历史记录功能。
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """预警严重程度枚举"""
    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    CRITICAL = "critical"  # 严重


class AlertType(Enum):
    """预警类型枚举"""
    PERFORMANCE = "performance"  # 性能预警
    RESOURCE = "resource"  # 资源预警
    ERROR = "error"  # 错误预警
    AVAILABILITY = "availability"  # 可用性预警
    SECURITY = "security"  # 安全预警


class MetricType(Enum):
    """指标类型枚举"""
    RESPONSE_TIME = "response_time"  # 响应时间
    MEMORY_USAGE = "memory_usage"  # 内存使用
    ERROR_RATE = "error_rate"  # 错误率
    CPU_USAGE = "cpu_usage"  # CPU使用率
    DISK_USAGE = "disk_usage"  # 磁盘使用率
    DATABASE_CONNECTIONS = "database_connections"  # 数据库连接数
    API_THROUGHPUT = "api_throughput"  # API吞吐量


@dataclass
class AlertThreshold:
    """预警阈值配置"""
    metric_type: MetricType
    threshold_value: float
    comparison: str  # "gt" (大于), "lt" (小于), "eq" (等于)
    severity: AlertSeverity
    duration: int  # 持续时间（秒）
    cooldown: int  # 冷却时间（秒）
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class AlertRecord:
    """预警记录"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    metric_type: MetricType
    metric_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_time: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        if self.resolved_time:
            data["resolved_time"] = self.resolved_time.isoformat()
        return data


class NotificationChannel:
    """通知渠道基类"""
    
    def __init__(self, name: str, enabled: bool = True):
        """初始化通知渠道
        
        Args:
            name: 渠道名称
            enabled: 是否启用
        """
        self.name = name
        self.enabled = enabled
        
    def send_alert(self, alert: AlertRecord) -> bool:
        """发送预警通知
        
        Args:
            alert: 预警记录
            
        Returns:
            发送是否成功
        """
        raise NotImplementedError("子类必须实现 send_alert 方法")


class LogNotificationChannel(NotificationChannel):
    """日志通知渠道"""
    
    def send_alert(self, alert: AlertRecord) -> bool:
        """发送预警到日志
        
        Args:
            alert: 预警记录
            
        Returns:
            发送是否成功
        """
        try:
            log_level = {
                AlertSeverity.LOW: logging.INFO,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.WARNING)
            
            logger.log(log_level, f"预警 [{alert.severity.value}]: {alert.message}")
            return True
        except Exception as e:
            logger.error(f"发送日志预警失败: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook通知渠道"""
    
    def __init__(self, name: str, webhook_url: str, enabled: bool = True):
        """初始化Webhook通知渠道
        
        Args:
            name: 渠道名称
            webhook_url: Webhook URL
            enabled: 是否启用
        """
        super().__init__(name, enabled)
        self.webhook_url = webhook_url
        
    def send_alert(self, alert: AlertRecord) -> bool:
        """发送预警到Webhook
        
        Args:
            alert: 预警记录
            
        Returns:
            发送是否成功
        """
        try:
            import requests
            
            payload = {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "metric_type": alert.metric_type.value,
                "metric_value": alert.metric_value,
                "threshold_value": alert.threshold_value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata or {}
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Webhook预警发送成功: {alert.alert_id}")
            return True
        except Exception as e:
            logger.error(f"发送Webhook预警失败: {e}")
            return False


class AlertManager:
    """预警管理器"""
    
    def __init__(self, history_size: int = 1000):
        """初始化预警管理器
        
        Args:
            history_size: 历史记录大小
        """
        self.thresholds: Dict[str, AlertThreshold] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.alert_history: List[AlertRecord] = []
        self.history_size = history_size
        self.active_alerts: Set[str] = set()
        self.last_alert_time: Dict[str, datetime] = {}
        
        # 注册默认通知渠道
        self._register_default_channels()
        
    def _register_default_channels(self):
        """注册默认通知渠道"""
        # 日志渠道
        log_channel = LogNotificationChannel("log")
        self.add_notification_channel(log_channel)
        
    def add_threshold(self, threshold: AlertThreshold) -> str:
        """添加预警阈值
        
        Args:
            threshold: 预警阈值
            
        Returns:
            阈值ID
        """
        threshold_id = f"{threshold.metric_type.value}_{threshold.comparison}_{threshold.threshold_value}"
        self.thresholds[threshold_id] = threshold
        logger.info(f"已添加预警阈值: {threshold_id}")
        return threshold_id
        
    def remove_threshold(self, threshold_id: str):
        """移除预警阈值
        
        Args:
            threshold_id: 阈值ID
        """
        if threshold_id in self.thresholds:
            del self.thresholds[threshold_id]
            logger.info(f"已移除预警阈值: {threshold_id}")
        
    def add_notification_channel(self, channel: NotificationChannel):
        """添加通知渠道
        
        Args:
            channel: 通知渠道
        """
        self.notification_channels[channel.name] = channel
        logger.info(f"已添加通知渠道: {channel.name}")
        
    def remove_notification_channel(self, channel_name: str):
        """移除通知渠道
        
        Args:
            channel_name: 渠道名称
        """
        if channel_name in self.notification_channels:
            del self.notification_channels[channel_name]
            logger.info(f"已移除通知渠道: {channel_name}")
            
    def check_metric(self, metric_type: MetricType, metric_value: float, 
                    metadata: Optional[Dict[str, Any]] = None) -> List[AlertRecord]:
        """检查指标是否触发预警
        
        Args:
            metric_type: 指标类型
            metric_value: 指标值
            metadata: 元数据
            
        Returns:
            触发的预警记录列表
        """
        triggered_alerts = []
        
        for threshold_id, threshold in self.thresholds.items():
            if not threshold.enabled or threshold.metric_type != metric_type:
                continue
                
            # 检查是否满足阈值条件
            is_triggered = False
            if threshold.comparison == "gt" and metric_value > threshold.threshold_value:
                is_triggered = True
            elif threshold.comparison == "lt" and metric_value < threshold.threshold_value:
                is_triggered = True
            elif threshold.comparison == "eq" and metric_value == threshold.threshold_value:
                is_triggered = True
                
            if is_triggered:
                # 检查冷却时间
                current_time = datetime.now()
                last_alert_time = self.last_alert_time.get(threshold_id)
                
                if last_alert_time:
                    time_since_last_alert = (current_time - last_alert_time).total_seconds()
                    if time_since_last_alert < threshold.cooldown:
                        continue  # 仍在冷却期内，跳过
                        
                # 创建预警记录
                alert_id = f"alert_{int(time.time())}_{len(self.alert_history)}"
                alert_type = self._determine_alert_type(metric_type)
                severity = threshold.severity
                
                # 生成预警消息
                comparison_text = {
                    "gt": "超过",
                    "lt": "低于", 
                    "eq": "等于"
                }.get(threshold.comparison, "超过")
                
                message = f"{metric_type.value} {comparison_text}阈值 {threshold.threshold_value}，当前值: {metric_value:.2f}"
                
                alert = AlertRecord(
                    alert_id=alert_id,
                    alert_type=alert_type,
                    severity=severity,
                    metric_type=metric_type,
                    metric_value=metric_value,
                    threshold_value=threshold.threshold_value,
                    message=message,
                    timestamp=current_time,
                    metadata=metadata
                )
                
                # 发送通知
                self._send_notifications(alert)
                
                # 记录预警
                self.alert_history.append(alert)
                self.active_alerts.add(alert_id)
                self.last_alert_time[threshold_id] = current_time
                
                # 限制历史记录大小
                if len(self.alert_history) > self.history_size:
                    self.alert_history = self.alert_history[-self.history_size:]
                    
                triggered_alerts.append(alert)
                
                logger.warning(f"预警触发: {message}")
                
        return triggered_alerts
        
    def _determine_alert_type(self, metric_type: MetricType) -> AlertType:
        """根据指标类型确定预警类型
        
        Args:
            metric_type: 指标类型
            
        Returns:
            预警类型
        """
        if metric_type in [MetricType.RESPONSE_TIME, MetricType.API_THROUGHPUT]:
            return AlertType.PERFORMANCE
        elif metric_type in [MetricType.MEMORY_USAGE, MetricType.CPU_USAGE, MetricType.DISK_USAGE, MetricType.DATABASE_CONNECTIONS]:
            return AlertType.RESOURCE
        elif metric_type == MetricType.ERROR_RATE:
            return AlertType.ERROR
        else:
            return AlertType.PERFORMANCE
            
    def _send_notifications(self, alert: AlertRecord):
        """发送预警通知
        
        Args:
            alert: 预警记录
        """
        for channel_name, channel in self.notification_channels.items():
            if channel.enabled:
                try:
                    success = channel.send_alert(alert)
                    if not success:
                        logger.warning(f"渠道 {channel_name} 发送预警失败")
                except Exception as e:
                    logger.error(f"渠道 {channel_name} 发送预警异常: {e}")
                    
    def resolve_alert(self, alert_id: str):
        """解决预警
        
        Args:
            alert_id: 预警ID
        """
        for alert in self.alert_history:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_time = datetime.now()
                self.active_alerts.discard(alert_id)
                
                logger.info(f"预警已解决: {alert_id}")
                break
                
    def get_active_alerts(self) -> List[AlertRecord]:
        """获取活跃预警
        
        Returns:
            活跃预警列表
        """
        return [alert for alert in self.alert_history if not alert.resolved]
        
    def get_alert_history(self, limit: int = 100, 
                         severity: Optional[AlertSeverity] = None,
                         alert_type: Optional[AlertType] = None) -> List[AlertRecord]:
        """获取预警历史
        
        Args:
            limit: 限制数量
            severity: 严重程度过滤
            alert_type: 预警类型过滤
            
        Returns:
            预警历史列表
        """
        filtered_alerts = self.alert_history
        
        if severity:
            filtered_alerts = [alert for alert in filtered_alerts if alert.severity == severity]
            
        if alert_type:
            filtered_alerts = [alert for alert in filtered_alerts if alert.alert_type == alert_type]
            
        return filtered_alerts[-limit:]
        
    def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取预警统计
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            预警统计信息
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
        
        # 按严重程度统计
        severity_stats = {}
        for severity in AlertSeverity:
            count = len([alert for alert in recent_alerts if alert.severity == severity])
            severity_stats[severity.value] = count
            
        # 按类型统计
        type_stats = {}
        for alert_type in AlertType:
            count = len([alert for alert in recent_alerts if alert.alert_type == alert_type])
            type_stats[alert_type.value] = count
            
        # 活跃预警统计
        active_alerts = self.get_active_alerts()
        
        return {
            "total_alerts": len(recent_alerts),
            "active_alerts": len(active_alerts),
            "resolved_alerts": len(recent_alerts) - len(active_alerts),
            "severity_stats": severity_stats,
            "type_stats": type_stats,
            "time_range_hours": hours
        }
        
    def load_default_thresholds(self):
        """加载默认阈值配置"""
        default_thresholds = [
            # 性能阈值
            AlertThreshold(
                metric_type=MetricType.RESPONSE_TIME,
                threshold_value=5000,  # 5秒
                comparison="gt",
                severity=AlertSeverity.HIGH,
                duration=60,
                cooldown=300
            ),
            AlertThreshold(
                metric_type=MetricType.RESPONSE_TIME,
                threshold_value=2000,  # 2秒
                comparison="gt",
                severity=AlertSeverity.MEDIUM,
                duration=60,
                cooldown=300
            ),
            
            # 错误率阈值
            AlertThreshold(
                metric_type=MetricType.ERROR_RATE,
                threshold_value=10,  # 10%
                comparison="gt",
                severity=AlertSeverity.HIGH,
                duration=60,
                cooldown=300
            ),
            AlertThreshold(
                metric_type=MetricType.ERROR_RATE,
                threshold_value=5,  # 5%
                comparison="gt",
                severity=AlertSeverity.MEDIUM,
                duration=60,
                cooldown=300
            ),
            
            # 内存使用阈值
            AlertThreshold(
                metric_type=MetricType.MEMORY_USAGE,
                threshold_value=1024,  # 1GB
                comparison="gt",
                severity=AlertSeverity.HIGH,
                duration=60,
                cooldown=300
            ),
            AlertThreshold(
                metric_type=MetricType.MEMORY_USAGE,
                threshold_value=512,  # 512MB
                comparison="gt",
                severity=AlertSeverity.MEDIUM,
                duration=60,
                cooldown=300
            ),
            
            # 数据库连接阈值
            AlertThreshold(
                metric_type=MetricType.DATABASE_CONNECTIONS,
                threshold_value=50,  # 50个连接
                comparison="gt",
                severity=AlertSeverity.HIGH,
                duration=60,
                cooldown=300
            )
        ]
        
        for threshold in default_thresholds:
            self.add_threshold(threshold)
            
        logger.info("默认预警阈值配置已加载")


# 全局预警管理器实例
alert_manager = AlertManager()
alert_manager.load_default_thresholds()