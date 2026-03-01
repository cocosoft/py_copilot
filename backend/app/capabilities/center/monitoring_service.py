"""
能力监控服务

本模块提供能力执行的监控、日志记录和性能分析功能
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

from sqlalchemy.orm import Session

from app.capabilities.types import CapabilityResult, ExecutionContext
from app.capabilities.center.unified_center import UnifiedCapabilityCenter
from app.models.capability_orchestration import (
    CapabilityExecutionLog,
    CapabilityUsageStats
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """执行指标"""
    total_calls: int = 0
    success_calls: int = 0
    failed_calls: int = 0
    total_execution_time_ms: int = 0
    average_execution_time_ms: float = 0.0
    min_execution_time_ms: int = 0
    max_execution_time_ms: int = 0
    error_rate: float = 0.0
    last_called_at: Optional[datetime] = None


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: Callable[[ExecutionMetrics], bool]
    message: str
    severity: str = "warning"  # info, warning, error, critical


class MonitoringService:
    """
    能力监控服务

    提供以下功能：
    - 执行日志记录
    - 性能指标收集
    - 实时监控
    - 告警通知
    - 统计分析

    Attributes:
        _center: 统一能力中心
        _db: 数据库会话
        _metrics: 指标缓存
        _alert_rules: 告警规则
        _alert_handlers: 告警处理器
    """

    def __init__(self, center: UnifiedCapabilityCenter, db: Session):
        """
        初始化监控服务

        Args:
            center: 统一能力中心
            db: 数据库会话
        """
        self._center = center
        self._db = db
        self._metrics: Dict[str, ExecutionMetrics] = defaultdict(ExecutionMetrics)
        self._alert_rules: List[AlertRule] = []
        self._alert_handlers: List[Callable] = []

        # 注册默认告警规则
        self._register_default_alerts()

        logger.info("监控服务已创建")

    def _register_default_alerts(self):
        """注册默认告警规则"""
        # 错误率过高告警
        self.add_alert_rule(AlertRule(
            name="high_error_rate",
            condition=lambda m: m.error_rate > 0.5 and m.total_calls > 10,
            message="错误率超过50%",
            severity="error"
        ))

        # 执行时间过长告警
        self.add_alert_rule(AlertRule(
            name="slow_execution",
            condition=lambda m: m.average_execution_time_ms > 30000,
            message="平均执行时间超过30秒",
            severity="warning"
        ))

        # 频繁失败告警
        self.add_alert_rule(AlertRule(
            name="frequent_failures",
            condition=lambda m: m.failed_calls > 10,
            message="失败次数过多",
            severity="error"
        ))

    def add_alert_rule(self, rule: AlertRule):
        """
        添加告警规则

        Args:
            rule: 告警规则
        """
        self._alert_rules.append(rule)
        logger.info(f"告警规则已添加: {rule.name}")

    def add_alert_handler(self, handler: Callable):
        """
        添加告警处理器

        Args:
            handler: 处理函数
        """
        self._alert_handlers.append(handler)

    async def record_execution(self,
                               capability_name: str,
                               input_data: Dict[str, Any],
                               result: CapabilityResult,
                               context: ExecutionContext):
        """
        记录执行

        Args:
            capability_name: 能力名称
            input_data: 输入数据
            result: 执行结果
            context: 执行上下文
        """
        try:
            # 更新内存中的指标
            self._update_metrics(capability_name, result)

            # 检查告警
            self._check_alerts(capability_name)

            # 记录到数据库
            await self._save_execution_log(
                capability_name, input_data, result, context
            )

            # 更新统计信息
            await self._update_usage_stats(capability_name, result)

        except Exception as e:
            logger.error(f"记录执行失败: {e}", exc_info=True)

    def _update_metrics(self, capability_name: str, result: CapabilityResult):
        """
        更新指标

        Args:
            capability_name: 能力名称
            result: 执行结果
        """
        metrics = self._metrics[capability_name]

        metrics.total_calls += 1
        metrics.last_called_at = datetime.now()

        if result.success:
            metrics.success_calls += 1
        else:
            metrics.failed_calls += 1

        if result.execution_time_ms:
            metrics.total_execution_time_ms += result.execution_time_ms

            if metrics.total_calls == 1:
                metrics.min_execution_time_ms = result.execution_time_ms
                metrics.max_execution_time_ms = result.execution_time_ms
            else:
                metrics.min_execution_time_ms = min(
                    metrics.min_execution_time_ms,
                    result.execution_time_ms
                )
                metrics.max_execution_time_ms = max(
                    metrics.max_execution_time_ms,
                    result.execution_time_ms
                )

            metrics.average_execution_time_ms = (
                metrics.total_execution_time_ms / metrics.total_calls
            )

        if metrics.total_calls > 0:
            metrics.error_rate = metrics.failed_calls / metrics.total_calls

    def _check_alerts(self, capability_name: str):
        """
        检查告警

        Args:
            capability_name: 能力名称
        """
        metrics = self._metrics[capability_name]

        for rule in self._alert_rules:
            try:
                if rule.condition(metrics):
                    alert = {
                        "rule_name": rule.name,
                        "capability_name": capability_name,
                        "message": rule.message,
                        "severity": rule.severity,
                        "timestamp": datetime.now().isoformat(),
                        "metrics": {
                            "total_calls": metrics.total_calls,
                            "error_rate": metrics.error_rate,
                            "avg_time": metrics.average_execution_time_ms
                        }
                    }

                    self._trigger_alert(alert)

            except Exception as e:
                logger.error(f"告警检查失败: {rule.name}, error={e}")

    def _trigger_alert(self, alert: Dict[str, Any]):
        """
        触发告警

        Args:
            alert: 告警信息
        """
        logger.warning(f"触发告警: {alert['rule_name']} - {alert['message']}")

        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")

    async def _save_execution_log(self,
                                  capability_name: str,
                                  input_data: Dict[str, Any],
                                  result: CapabilityResult,
                                  context: ExecutionContext):
        """
        保存执行日志

        Args:
            capability_name: 能力名称
            input_data: 输入数据
            result: 执行结果
            context: 执行上下文
        """
        try:
            log = CapabilityExecutionLog(
                capability_name=capability_name,
                capability_type=self._get_capability_type(capability_name),
                input_data=input_data,
                output_data={"output": result.output} if result.output else None,
                execution_time_ms=result.execution_time_ms,
                success=result.success,
                error_message=result.error,
                retry_count=getattr(result, 'retry_count', 0)
            )

            self._db.add(log)
            self._db.commit()

        except Exception as e:
            logger.error(f"保存执行日志失败: {e}")
            self._db.rollback()

    async def _update_usage_stats(self,
                                  capability_name: str,
                                  result: CapabilityResult):
        """
        更新使用统计

        Args:
            capability_name: 能力名称
            result: 执行结果
        """
        try:
            # 查询现有统计
            stats = self._db.query(CapabilityUsageStats).filter(
                CapabilityUsageStats.capability_name == capability_name
            ).first()

            if not stats:
                stats = CapabilityUsageStats(
                    capability_name=capability_name,
                    capability_type=self._get_capability_type(capability_name)
                )
                self._db.add(stats)

            # 更新统计
            stats.total_calls += 1

            if result.success:
                stats.success_calls += 1
            else:
                stats.failed_calls += 1

            if result.execution_time_ms:
                stats.total_execution_time_ms += result.execution_time_ms
                stats.average_execution_time_ms = (
                    stats.total_execution_time_ms / stats.total_calls
                )

            stats.last_called_at = datetime.now()

            self._db.commit()

        except Exception as e:
            logger.error(f"更新使用统计失败: {e}")
            self._db.rollback()

    def _get_capability_type(self, capability_name: str) -> str:
        """
        获取能力类型

        Args:
            capability_name: 能力名称

        Returns:
            str: 能力类型
        """
        metadata = self._center.get_capability_metadata(capability_name)
        return metadata.capability_type.value if metadata else "unknown"

    def get_metrics(self, capability_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指标

        Args:
            capability_name: 能力名称，None则返回所有

        Returns:
            Dict[str, Any]: 指标信息
        """
        if capability_name:
            metrics = self._metrics.get(capability_name)
            if metrics:
                return {
                    "capability_name": capability_name,
                    "total_calls": metrics.total_calls,
                    "success_calls": metrics.success_calls,
                    "failed_calls": metrics.failed_calls,
                    "success_rate": (
                        metrics.success_calls / metrics.total_calls * 100
                        if metrics.total_calls > 0 else 0
                    ),
                    "error_rate": metrics.error_rate * 100,
                    "average_execution_time_ms": metrics.average_execution_time_ms,
                    "min_execution_time_ms": metrics.min_execution_time_ms,
                    "max_execution_time_ms": metrics.max_execution_time_ms,
                    "last_called_at": metrics.last_called_at.isoformat() if metrics.last_called_at else None
                }
            return {}

        # 返回所有指标
        return {
            name: self.get_metrics(name)
            for name in self._metrics.keys()
        }

    def get_top_capabilities(self,
                            limit: int = 10,
                            metric: str = "total_calls") -> List[Dict[str, Any]]:
        """
        获取热门能力

        Args:
            limit: 返回数量
            metric: 排序指标

        Returns:
            List[Dict[str, Any]]: 热门能力列表
        """
        items = []

        for name, metrics in self._metrics.items():
            items.append({
                "name": name,
                "total_calls": metrics.total_calls,
                "success_rate": (
                    metrics.success_calls / metrics.total_calls * 100
                    if metrics.total_calls > 0 else 0
                ),
                "average_time": metrics.average_execution_time_ms
            })

        # 排序
        items.sort(key=lambda x: x.get(metric, 0), reverse=True)

        return items[:limit]

    def get_error_summary(self,
                         hours: int = 24) -> Dict[str, Any]:
        """
        获取错误汇总

        Args:
            hours: 时间范围（小时）

        Returns:
            Dict[str, Any]: 错误汇总
        """
        since = datetime.now() - timedelta(hours=hours)

        errors = []
        total_errors = 0

        for name, metrics in self._metrics.items():
            if metrics.failed_calls > 0:
                total_errors += metrics.failed_calls
                errors.append({
                    "capability_name": name,
                    "failed_calls": metrics.failed_calls,
                    "error_rate": metrics.error_rate * 100
                })

        errors.sort(key=lambda x: x["failed_calls"], reverse=True)

        return {
            "period_hours": hours,
            "total_errors": total_errors,
            "top_errors": errors[:10]
        }

    def get_health_report(self) -> Dict[str, Any]:
        """
        获取健康报告

        Returns:
            Dict[str, Any]: 健康报告
        """
        total_capabilities = len(self._metrics)
        total_calls = sum(m.total_calls for m in self._metrics.values())
        total_errors = sum(m.failed_calls for m in self._metrics.values())

        overall_error_rate = (
            total_errors / total_calls * 100 if total_calls > 0 else 0
        )

        # 确定健康状态
        if overall_error_rate < 5:
            health_status = "healthy"
        elif overall_error_rate < 20:
            health_status = "warning"
        else:
            health_status = "critical"

        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_capabilities": total_capabilities,
                "total_calls": total_calls,
                "total_errors": total_errors,
                "overall_error_rate": overall_error_rate
            },
            "center_health": self._center.get_health_status()
        }

    def reset_metrics(self, capability_name: Optional[str] = None):
        """
        重置指标

        Args:
            capability_name: 能力名称，None则重置所有
        """
        if capability_name:
            if capability_name in self._metrics:
                del self._metrics[capability_name]
                logger.info(f"指标已重置: {capability_name}")
        else:
            self._metrics.clear()
            logger.info("所有指标已重置")

    def export_metrics(self, format: str = "json") -> str:
        """
        导出指标

        Args:
            format: 导出格式

        Returns:
            str: 导出的数据
        """
        metrics = self.get_metrics()

        if format == "json":
            return json.dumps(metrics, indent=2, default=str)

        # 简化CSV格式
        lines = ["capability_name,total_calls,success_rate,error_rate,avg_time_ms"]
        for name, data in metrics.items():
            lines.append(
                f"{name},{data.get('total_calls',0)},"
                f"{data.get('success_rate',0):.2f},"
                f"{data.get('error_rate',0):.2f},"
                f"{data.get('average_execution_time_ms',0):.2f}"
            )

        return "\n".join(lines)
