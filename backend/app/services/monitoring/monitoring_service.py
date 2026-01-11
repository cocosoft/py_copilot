"""监控服务模块"""
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import logging
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.core.logging_config import performance_logger

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """告警类型"""
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    RESOURCE = "resource"
    BUSINESS = "business"
    SECURITY = "security"

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric_name: str
    threshold: float
    comparison: str  # '>', '<', '>=', '<=', '=='
    duration: int  # 持续时间（秒）
    level: AlertLevel
    type: AlertType
    message_template: str
    enabled: bool = True

@dataclass
class Alert:
    """告警实例"""
    id: str
    rule_name: str
    level: AlertLevel
    type: AlertType
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class MonitoringService:
    """监控服务"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_handlers: List[Callable] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """设置默认告警规则"""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                metric_name="error_rate",
                threshold=0.1,  # 10%
                comparison=">",
                duration=300,  # 5分钟
                level=AlertLevel.ERROR,
                type=AlertType.ERROR_RATE,
                message_template="错误率超过阈值: {value:.1%} > {threshold:.1%}"
            ),
            AlertRule(
                name="slow_response",
                metric_name="response_time_p95",
                threshold=5000,  # 5秒
                comparison=">",
                duration=60,  # 1分钟
                level=AlertLevel.WARNING,
                type=AlertType.PERFORMANCE,
                message_template="响应时间P95超过阈值: {value:.0f}ms > {threshold:.0f}ms"
            ),
            AlertRule(
                name="high_cpu_usage",
                metric_name="cpu_usage",
                threshold=80.0,  # 80%
                comparison=">",
                duration=300,  # 5分钟
                level=AlertLevel.WARNING,
                type=AlertType.RESOURCE,
                message_template="CPU使用率超过阈值: {value:.1f}% > {threshold:.1f}%"
            ),
            AlertRule(
                name="low_available_memory",
                metric_name="available_memory_percent",
                threshold=10.0,  # 10%
                comparison="<",
                duration=300,  # 5分钟
                level=AlertLevel.ERROR,
                type=AlertType.RESOURCE,
                message_template="可用内存低于阈值: {value:.1f}% < {threshold:.1f}%"
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule
    
    def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录指标"""
        timestamp = datetime.now()
        metric_data = {
            "timestamp": timestamp,
            "value": value,
            "tags": tags or {}
        }
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append(metric_data)
        
        # 保持最近1小时的数据
        cutoff_time = timestamp - timedelta(hours=1)
        self.metrics[metric_name] = [
            m for m in self.metrics[metric_name] 
            if m["timestamp"] > cutoff_time
        ]
        
        # 检查是否需要触发告警
        self._check_alerts(metric_name, value, timestamp)
    
    def _check_alerts(self, metric_name: str, value: float, timestamp: datetime):
        """检查告警规则"""
        for rule_name, rule in self.alert_rules.items():
            if rule.metric_name == metric_name and rule.enabled:
                # 检查是否满足告警条件
                if self._evaluate_rule(rule, value, timestamp):
                    self._trigger_alert(rule, value, timestamp)
    
    def _evaluate_rule(self, rule: AlertRule, value: float, timestamp: datetime) -> bool:
        """评估告警规则"""
        # 获取指定时间段内的指标数据
        cutoff_time = timestamp - timedelta(seconds=rule.duration)
        relevant_metrics = [
            m for m in self.metrics.get(rule.metric_name, [])
            if m["timestamp"] > cutoff_time
        ]
        
        if not relevant_metrics:
            return False
        
        # 计算平均值
        avg_value = sum(m["value"] for m in relevant_metrics) / len(relevant_metrics)
        
        # 根据比较操作符评估条件
        if rule.comparison == ">":
            return avg_value > rule.threshold
        elif rule.comparison == "<":
            return avg_value < rule.threshold
        elif rule.comparison == ">=":
            return avg_value >= rule.threshold
        elif rule.comparison == "<=":
            return avg_value <= rule.threshold
        elif rule.comparison == "==":
            return abs(avg_value - rule.threshold) < 0.001
        
        return False
    
    def _trigger_alert(self, rule: AlertRule, value: float, timestamp: datetime):
        """触发告警"""
        alert_id = f"{rule.name}_{int(timestamp.timestamp())}"
        
        # 检查是否已经存在相同规则的活跃告警
        existing_alert = next((a for a in self.alerts.values() 
                             if a.rule_name == rule.name and not a.resolved), None)
        
        if existing_alert:
            # 更新现有告警
            existing_alert.metric_value = value
            existing_alert.timestamp = timestamp
            return
        
        # 创建新告警
        message = rule.message_template.format(value=value, threshold=rule.threshold)
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            level=rule.level,
            type=rule.type,
            message=message,
            metric_value=value,
            threshold=rule.threshold,
            timestamp=timestamp
        )
        
        self.alerts[alert_id] = alert
        
        # 记录告警日志
        logger.warning(f"告警触发: {rule.level.value.upper()} - {message}")
        
        # 调用告警处理器
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {str(e)}")
    
    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            logger.info(f"告警解决: {alert_id}")
    
    def add_alert_handler(self, handler: Callable):
        """添加告警处理器"""
        self.alert_handlers.append(handler)
    
    def get_metrics_summary(self, metric_name: str, duration: int = 3600) -> Dict[str, Any]:
        """获取指标摘要"""
        cutoff_time = datetime.now() - timedelta(seconds=duration)
        relevant_metrics = [
            m for m in self.metrics.get(metric_name, [])
            if m["timestamp"] > cutoff_time
        ]
        
        if not relevant_metrics:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "p95": 0}
        
        values = [m["value"] for m in relevant_metrics]
        values_sorted = sorted(values)
        
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "p95": values_sorted[int(len(values_sorted) * 0.95)] if len(values_sorted) > 0 else 0
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_statistics(self, duration: int = 3600) -> Dict[str, Any]:
        """获取告警统计"""
        cutoff_time = datetime.now() - timedelta(seconds=duration)
        
        recent_alerts = [
            alert for alert in self.alerts.values()
            if alert.timestamp > cutoff_time
        ]
        
        active_alerts = [alert for alert in recent_alerts if not alert.resolved]
        
        return {
            "total_alerts": len(recent_alerts),
            "active_alerts": len(active_alerts),
            "alerts_by_level": {
                level.value: len([a for a in recent_alerts if a.level == level])
                for level in AlertLevel
            },
            "alerts_by_type": {
                type.value: len([a for a in recent_alerts if a.type == type])
                for type in AlertType
            }
        }

class SystemMetricsCollector:
    """系统指标收集器"""
    
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
    
    async def collect_system_metrics(self):
        """收集系统指标"""
        while True:
            try:
                # 收集CPU使用率
                cpu_usage = self._get_cpu_usage()
                self.monitoring_service.record_metric("cpu_usage", cpu_usage)
                
                # 收集内存使用率
                memory_info = self._get_memory_info()
                self.monitoring_service.record_metric("memory_usage", memory_info["usage_percent"])
                self.monitoring_service.record_metric("available_memory_percent", memory_info["available_percent"])
                
                # 收集磁盘使用率
                disk_usage = self._get_disk_usage()
                self.monitoring_service.record_metric("disk_usage", disk_usage)
                
                # 收集数据库连接数
                db_connections = self._get_db_connections()
                self.monitoring_service.record_metric("db_connections", db_connections)
                
            except Exception as e:
                logger.error(f"收集系统指标失败: {str(e)}")
            
            await asyncio.sleep(60)  # 每分钟收集一次
    
    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            logger.warning("psutil未安装，无法获取CPU使用率")
            return 0.0
    
    def _get_memory_info(self) -> Dict[str, float]:
        """获取内存信息"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "usage_percent": memory.percent,
                "available_percent": (memory.available / memory.total) * 100
            }
        except ImportError:
            logger.warning("psutil未安装，无法获取内存信息")
            return {"usage_percent": 0.0, "available_percent": 100.0}
    
    def _get_disk_usage(self) -> float:
        """获取磁盘使用率"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return (disk.used / disk.total) * 100
        except ImportError:
            logger.warning("psutil未安装，无法获取磁盘使用率")
            return 0.0
    
    def _get_db_connections(self) -> int:
        """获取数据库连接数"""
        try:
            # 执行SQL查询获取连接数
            result = self.monitoring_service.db.execute(text("SELECT COUNT(*) FROM sqlite_master"))
            return 1  # SQLite简化处理
        except Exception:
            return 0