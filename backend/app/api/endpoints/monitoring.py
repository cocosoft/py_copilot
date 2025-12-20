"""监控API端点"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.api.deps import get_db
from app.services.monitoring.monitoring_service import (
    MonitoringService, Alert, AlertRule, AlertLevel, AlertType
)
from app.services.monitoring.alert_notifier import NotificationManager

router = APIRouter()

# 全局监控服务实例
_monitoring_service = None
_notification_manager = None

def get_monitoring_service(db: Session = Depends(get_db)):
    """获取监控服务实例"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService(db)
        
        # 添加告警通知处理器
        notification_manager = NotificationManager()
        _monitoring_service.add_alert_handler(notification_manager.send_alert_notification)
    
    return _monitoring_service

def get_notification_manager():
    """获取通知管理器实例"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    
    return _notification_manager

@router.get("/metrics/{metric_name}")
async def get_metric_data(
    metric_name: str,
    duration: int = Query(3600, description="时间范围（秒）"),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """获取指标数据"""
    try:
        summary = monitoring_service.get_metrics_summary(metric_name, duration)
        return {
            "metric_name": metric_name,
            "duration_seconds": duration,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标数据失败: {str(e)}")

@router.get("/alerts/active")
async def get_active_alerts(
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """获取活跃告警"""
    try:
        alerts = monitoring_service.get_active_alerts()
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "level": alert.level.value,
                    "type": alert.type.value,
                    "message": alert.message,
                    "metric_value": alert.metric_value,
                    "threshold": alert.threshold,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved
                }
                for alert in alerts
            ],
            "count": len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃告警失败: {str(e)}")

@router.get("/alerts/history")
async def get_alert_history(
    duration: int = Query(86400, description="时间范围（秒）"),
    level: Optional[str] = Query(None, description="告警级别"),
    type: Optional[str] = Query(None, description="告警类型"),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """获取告警历史"""
    try:
        cutoff_time = datetime.now() - timedelta(seconds=duration)
        
        # 过滤告警
        filtered_alerts = [
            alert for alert in monitoring_service.alerts.values()
            if alert.timestamp > cutoff_time
        ]
        
        if level:
            filtered_alerts = [alert for alert in filtered_alerts if alert.level.value == level]
        
        if type:
            filtered_alerts = [alert for alert in filtered_alerts if alert.type.value == type]
        
        # 按时间倒序排序
        filtered_alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "level": alert.level.value,
                    "type": alert.type.value,
                    "message": alert.message,
                    "metric_value": alert.metric_value,
                    "threshold": alert.threshold,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
                }
                for alert in filtered_alerts
            ],
            "count": len(filtered_alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警历史失败: {str(e)}")

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    notification_manager: NotificationManager = Depends(get_notification_manager)
):
    """解决告警"""
    try:
        if alert_id not in monitoring_service.alerts:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        alert = monitoring_service.alerts[alert_id]
        monitoring_service.resolve_alert(alert_id)
        
        # 发送解决通知
        notification_manager.send_resolution_notification(alert)
        
        return {"message": "告警已解决", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")

@router.get("/alerts/rules")
async def get_alert_rules(
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """获取告警规则"""
    try:
        return {
            "rules": [
                {
                    "name": rule.name,
                    "metric_name": rule.metric_name,
                    "threshold": rule.threshold,
                    "comparison": rule.comparison,
                    "duration": rule.duration,
                    "level": rule.level.value,
                    "type": rule.type.value,
                    "message_template": rule.message_template,
                    "enabled": rule.enabled
                }
                for rule in monitoring_service.alert_rules.values()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警规则失败: {str(e)}")

@router.post("/alerts/rules")
async def create_alert_rule(
    rule_data: Dict[str, Any],
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """创建告警规则"""
    try:
        # 验证必需字段
        required_fields = ['name', 'metric_name', 'threshold', 'comparison', 'duration', 'level', 'type']
        for field in required_fields:
            if field not in rule_data:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        # 创建告警规则
        rule = AlertRule(
            name=rule_data['name'],
            metric_name=rule_data['metric_name'],
            threshold=float(rule_data['threshold']),
            comparison=rule_data['comparison'],
            duration=int(rule_data['duration']),
            level=AlertLevel(rule_data['level']),
            type=AlertType(rule_data['type']),
            message_template=rule_data.get('message_template', '告警: {value} {comparison} {threshold}')
        )
        
        monitoring_service.alert_rules[rule.name] = rule
        
        return {"message": "告警规则创建成功", "rule_name": rule.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数验证失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建告警规则失败: {str(e)}")

@router.put("/alerts/rules/{rule_name}")
async def update_alert_rule(
    rule_name: str,
    rule_data: Dict[str, Any],
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """更新告警规则"""
    try:
        if rule_name not in monitoring_service.alert_rules:
            raise HTTPException(status_code=404, detail="告警规则不存在")
        
        rule = monitoring_service.alert_rules[rule_name]
        
        # 更新规则字段
        if 'metric_name' in rule_data:
            rule.metric_name = rule_data['metric_name']
        if 'threshold' in rule_data:
            rule.threshold = float(rule_data['threshold'])
        if 'comparison' in rule_data:
            rule.comparison = rule_data['comparison']
        if 'duration' in rule_data:
            rule.duration = int(rule_data['duration'])
        if 'level' in rule_data:
            rule.level = AlertLevel(rule_data['level'])
        if 'type' in rule_data:
            rule.type = AlertType(rule_data['type'])
        if 'message_template' in rule_data:
            rule.message_template = rule_data['message_template']
        if 'enabled' in rule_data:
            rule.enabled = bool(rule_data['enabled'])
        
        return {"message": "告警规则更新成功", "rule_name": rule_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数验证失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新告警规则失败: {str(e)}")

@router.delete("/alerts/rules/{rule_name}")
async def delete_alert_rule(
    rule_name: str,
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """删除告警规则"""
    try:
        if rule_name not in monitoring_service.alert_rules:
            raise HTTPException(status_code=404, detail="告警规则不存在")
        
        del monitoring_service.alert_rules[rule_name]
        
        return {"message": "告警规则删除成功", "rule_name": rule_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除告警规则失败: {str(e)}")

@router.get("/statistics")
async def get_monitoring_statistics(
    duration: int = Query(3600, description="时间范围（秒）"),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """获取监控统计信息"""
    try:
        alert_stats = monitoring_service.get_alert_statistics(duration)
        
        # 获取关键指标摘要
        key_metrics = {}
        for metric_name in ['response_time_p95', 'error_rate', 'cpu_usage', 'memory_usage']:
            summary = monitoring_service.get_metrics_summary(metric_name, duration)
            key_metrics[metric_name] = summary
        
        return {
            "alert_statistics": alert_stats,
            "key_metrics": key_metrics,
            "duration_seconds": duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控统计失败: {str(e)}")

@router.post("/metrics/record")
async def record_metric(
    metric_data: Dict[str, Any],
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """记录自定义指标"""
    try:
        required_fields = ['metric_name', 'value']
        for field in required_fields:
            if field not in metric_data:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        monitoring_service.record_metric(
            metric_name=metric_data['metric_name'],
            value=float(metric_data['value']),
            tags=metric_data.get('tags', {})
        )
        
        return {"message": "指标记录成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数验证失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录指标失败: {str(e)}")