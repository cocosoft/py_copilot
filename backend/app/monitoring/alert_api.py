"""
预警系统API

提供预警配置、预警查询和预警管理的API接口。
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .alert_system import alert_manager, AlertThreshold, AlertSeverity, AlertType, MetricType, NotificationChannel, WebhookNotificationChannel

router = APIRouter(prefix="/api/monitoring/alerts", tags=["预警管理"])


class AlertThresholdRequest(BaseModel):
    """预警阈值请求模型"""
    metric_type: str
    threshold_value: float
    comparison: str
    severity: str
    duration: int
    cooldown: int
    enabled: bool = True


class AlertThresholdResponse(BaseModel):
    """预警阈值响应模型"""
    threshold_id: str
    metric_type: str
    threshold_value: float
    comparison: str
    severity: str
    duration: int
    cooldown: int
    enabled: bool


class AlertRecordResponse(BaseModel):
    """预警记录响应模型"""
    alert_id: str
    alert_type: str
    severity: str
    metric_type: str
    metric_value: float
    threshold_value: float
    message: str
    timestamp: str
    resolved: bool
    resolved_time: Optional[str]
    metadata: Optional[Dict[str, Any]]


class AlertStatsResponse(BaseModel):
    """预警统计响应模型"""
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    severity_stats: Dict[str, int]
    type_stats: Dict[str, int]
    time_range_hours: int


class NotificationChannelRequest(BaseModel):
    """通知渠道请求模型"""
    name: str
    channel_type: str
    config: Dict[str, Any]
    enabled: bool = True


class NotificationChannelResponse(BaseModel):
    """通知渠道响应模型"""
    name: str
    channel_type: str
    enabled: bool
    config: Dict[str, Any]


class CheckMetricRequest(BaseModel):
    """检查指标请求模型"""
    metric_type: str
    metric_value: float
    metadata: Optional[Dict[str, Any]] = None


class CheckMetricResponse(BaseModel):
    """检查指标响应模型"""
    triggered_alerts: List[AlertRecordResponse]
    metric_value: float
    threshold_count: int


@router.post("/thresholds", response_model=AlertThresholdResponse)
async def add_threshold(request: AlertThresholdRequest):
    """添加预警阈值
    
    Args:
        request: 预警阈值请求
        
    Returns:
        添加的预警阈值
    """
    # 验证参数
    try:
        metric_enum = MetricType(request.metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的指标类型: {request.metric_type}")
    
    try:
        severity_enum = AlertSeverity(request.severity)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的严重程度: {request.severity}")
    
    if request.comparison not in ["gt", "lt", "eq"]:
        raise HTTPException(status_code=400, detail="比较操作必须是 gt, lt 或 eq")
    
    if request.duration < 1:
        raise HTTPException(status_code=400, detail="持续时间必须大于0")
    
    if request.cooldown < 0:
        raise HTTPException(status_code=400, detail="冷却时间不能为负数")
    
    try:
        threshold = AlertThreshold(
            metric_type=metric_enum,
            threshold_value=request.threshold_value,
            comparison=request.comparison,
            severity=severity_enum,
            duration=request.duration,
            cooldown=request.cooldown,
            enabled=request.enabled
        )
        
        threshold_id = alert_manager.add_threshold(threshold)
        
        return AlertThresholdResponse(
            threshold_id=threshold_id,
            metric_type=request.metric_type,
            threshold_value=request.threshold_value,
            comparison=request.comparison,
            severity=request.severity,
            duration=request.duration,
            cooldown=request.cooldown,
            enabled=request.enabled
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加预警阈值失败: {str(e)}")


@router.get("/thresholds", response_model=List[AlertThresholdResponse])
async def get_thresholds():
    """获取所有预警阈值
    
    Returns:
        预警阈值列表
    """
    try:
        thresholds = []
        for threshold_id, threshold in alert_manager.thresholds.items():
            thresholds.append(AlertThresholdResponse(
                threshold_id=threshold_id,
                metric_type=threshold.metric_type.value,
                threshold_value=threshold.threshold_value,
                comparison=threshold.comparison,
                severity=threshold.severity.value,
                duration=threshold.duration,
                cooldown=threshold.cooldown,
                enabled=threshold.enabled
            ))
        
        return thresholds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警阈值失败: {str(e)}")


@router.delete("/thresholds/{threshold_id}")
async def remove_threshold(threshold_id: str):
    """移除预警阈值
    
    Args:
        threshold_id: 阈值ID
        
    Returns:
        移除结果
    """
    if threshold_id not in alert_manager.thresholds:
        raise HTTPException(status_code=404, detail=f"预警阈值 {threshold_id} 未找到")
    
    try:
        alert_manager.remove_threshold(threshold_id)
        
        return {
            "status": "success",
            "message": f"预警阈值 {threshold_id} 已移除",
            "threshold_id": threshold_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除预警阈值失败: {str(e)}")


@router.post("/check-metric", response_model=CheckMetricResponse)
async def check_metric(request: CheckMetricRequest):
    """检查指标是否触发预警
    
    Args:
        request: 检查指标请求
        
    Returns:
        检查结果
    """
    # 验证指标类型
    try:
        metric_enum = MetricType(request.metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的指标类型: {request.metric_type}")
    
    try:
        triggered_alerts = alert_manager.check_metric(
            metric_type=metric_enum,
            metric_value=request.metric_value,
            metadata=request.metadata
        )
        
        # 转换为响应模型
        alert_responses = []
        for alert in triggered_alerts:
            alert_responses.append(AlertRecordResponse(
                alert_id=alert.alert_id,
                alert_type=alert.alert_type.value,
                severity=alert.severity.value,
                metric_type=alert.metric_type.value,
                metric_value=alert.metric_value,
                threshold_value=alert.threshold_value,
                message=alert.message,
                timestamp=alert.timestamp.isoformat(),
                resolved=alert.resolved,
                resolved_time=alert.resolved_time.isoformat() if alert.resolved_time else None,
                metadata=alert.metadata
            ))
        
        return CheckMetricResponse(
            triggered_alerts=alert_responses,
            metric_value=request.metric_value,
            threshold_count=len(alert_manager.thresholds)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查指标失败: {str(e)}")


@router.get("/alerts/active", response_model=List[AlertRecordResponse])
async def get_active_alerts():
    """获取活跃预警
    
    Returns:
        活跃预警列表
    """
    try:
        active_alerts = alert_manager.get_active_alerts()
        
        alert_responses = []
        for alert in active_alerts:
            alert_responses.append(AlertRecordResponse(
                alert_id=alert.alert_id,
                alert_type=alert.alert_type.value,
                severity=alert.severity.value,
                metric_type=alert.metric_type.value,
                metric_value=alert.metric_value,
                threshold_value=alert.threshold_value,
                message=alert.message,
                timestamp=alert.timestamp.isoformat(),
                resolved=alert.resolved,
                resolved_time=alert.resolved_time.isoformat() if alert.resolved_time else None,
                metadata=alert.metadata
            ))
        
        return alert_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃预警失败: {str(e)}")


@router.get("/alerts/history", response_model=List[AlertRecordResponse])
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None)
):
    """获取预警历史
    
    Args:
        limit: 限制数量
        severity: 严重程度过滤
        alert_type: 预警类型过滤
        
    Returns:
        预警历史列表
    """
    # 验证参数
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的严重程度: {severity}")
    
    type_enum = None
    if alert_type:
        try:
            type_enum = AlertType(alert_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的预警类型: {alert_type}")
    
    try:
        alerts = alert_manager.get_alert_history(
            limit=limit,
            severity=severity_enum,
            alert_type=type_enum
        )
        
        alert_responses = []
        for alert in alerts:
            alert_responses.append(AlertRecordResponse(
                alert_id=alert.alert_id,
                alert_type=alert.alert_type.value,
                severity=alert.severity.value,
                metric_type=alert.metric_type.value,
                metric_value=alert.metric_value,
                threshold_value=alert.threshold_value,
                message=alert.message,
                timestamp=alert.timestamp.isoformat(),
                resolved=alert.resolved,
                resolved_time=alert.resolved_time.isoformat() if alert.resolved_time else None,
                metadata=alert.metadata
            ))
        
        return alert_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警历史失败: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """解决预警
    
    Args:
        alert_id: 预警ID
        
    Returns:
        解决结果
    """
    try:
        alert_manager.resolve_alert(alert_id)
        
        return {
            "status": "success",
            "message": f"预警 {alert_id} 已解决",
            "alert_id": alert_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决预警失败: {str(e)}")


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(hours: int = Query(24, ge=1, le=168)):
    """获取预警统计
    
    Args:
        hours: 时间范围（小时）
        
    Returns:
        预警统计信息
    """
    try:
        stats = alert_manager.get_alert_stats(hours)
        
        return AlertStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警统计失败: {str(e)}")


@router.post("/channels")
async def add_notification_channel(request: NotificationChannelRequest):
    """添加通知渠道
    
    Args:
        request: 通知渠道请求
        
    Returns:
        添加结果
    """
    if request.name in alert_manager.notification_channels:
        raise HTTPException(status_code=400, detail=f"通知渠道 {request.name} 已存在")
    
    try:
        if request.channel_type == "webhook":
            webhook_url = request.config.get("webhook_url")
            if not webhook_url:
                raise HTTPException(status_code=400, detail="Webhook渠道需要配置 webhook_url")
            
            channel = WebhookNotificationChannel(
                name=request.name,
                webhook_url=webhook_url,
                enabled=request.enabled
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的通知渠道类型: {request.channel_type}")
        
        alert_manager.add_notification_channel(channel)
        
        return {
            "status": "success",
            "message": f"通知渠道 {request.name} 已添加",
            "channel_name": request.name,
            "channel_type": request.channel_type,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加通知渠道失败: {str(e)}")


@router.get("/channels", response_model=List[NotificationChannelResponse])
async def get_notification_channels():
    """获取所有通知渠道
    
    Returns:
        通知渠道列表
    """
    try:
        channels = []
        for channel_name, channel in alert_manager.notification_channels.items():
            channel_type = "log" if isinstance(channel, WebhookNotificationChannel) else "webhook"
            config = {}
            
            if isinstance(channel, WebhookNotificationChannel):
                config = {"webhook_url": channel.webhook_url}
            
            channels.append(NotificationChannelResponse(
                name=channel_name,
                channel_type=channel_type,
                enabled=channel.enabled,
                config=config
            ))
        
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取通知渠道失败: {str(e)}")


@router.delete("/channels/{channel_name}")
async def remove_notification_channel(channel_name: str):
    """移除通知渠道
    
    Args:
        channel_name: 渠道名称
        
    Returns:
        移除结果
    """
    if channel_name not in alert_manager.notification_channels:
        raise HTTPException(status_code=404, detail=f"通知渠道 {channel_name} 未找到")
    
    try:
        alert_manager.remove_notification_channel(channel_name)
        
        return {
            "status": "success",
            "message": f"通知渠道 {channel_name} 已移除",
            "channel_name": channel_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除通知渠道失败: {str(e)}")


@router.get("/types/metrics")
async def get_metric_types():
    """获取支持的指标类型
    
    Returns:
        支持的指标类型列表
    """
    return {
        "metric_types": [metric_type.value for metric_type in MetricType],
        "descriptions": {
            "response_time": "响应时间（毫秒）",
            "memory_usage": "内存使用（MB）",
            "error_rate": "错误率（百分比）",
            "cpu_usage": "CPU使用率（百分比）",
            "disk_usage": "磁盘使用率（百分比）",
            "database_connections": "数据库连接数",
            "api_throughput": "API吞吐量（请求/秒）"
        }
    }


@router.get("/types/severities")
async def get_severity_types():
    """获取支持的严重程度类型
    
    Returns:
        支持的严重程度类型列表
    """
    return {
        "severity_types": [severity.value for severity in AlertSeverity],
        "descriptions": {
            "low": "低 - 信息级别",
            "medium": "中 - 警告级别",
            "high": "高 - 错误级别",
            "critical": "严重 - 紧急级别"
        }
    }


@router.get("/types/alert-types")
async def get_alert_types():
    """获取支持的预警类型
    
    Returns:
        支持的预警类型列表
    """
    return {
        "alert_types": [alert_type.value for alert_type in AlertType],
        "descriptions": {
            "performance": "性能预警",
            "resource": "资源预警",
            "error": "错误预警",
            "availability": "可用性预警",
            "security": "安全预警"
        }
    }


@router.get("/types/channel-types")
async def get_channel_types():
    """获取支持的通知渠道类型
    
    Returns:
        支持的通知渠道类型列表
    """
    return {
        "channel_types": ["log", "webhook"],
        "descriptions": {
            "log": "日志渠道 - 将预警记录到日志文件",
            "webhook": "Webhook渠道 - 发送预警到指定的Webhook URL"
        }
    }


@router.post("/test-alert")
async def test_alert():
    """测试预警功能
    
    Returns:
        测试结果
    """
    try:
        # 模拟一个高响应时间的预警
        test_alerts = alert_manager.check_metric(
            metric_type=MetricType.RESPONSE_TIME,
            metric_value=6000,  # 6秒，超过5秒阈值
            metadata={"test": True, "endpoint": "/api/test"}
        )
        
        return {
            "status": "success",
            "message": f"测试预警已触发 {len(test_alerts)} 个预警",
            "triggered_alerts": len(test_alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试预警失败: {str(e)}")


@router.get("/health")
async def get_alert_system_health():
    """获取预警系统健康状态
    
    Returns:
        预警系统健康状态
    """
    try:
        stats = alert_manager.get_alert_stats(hours=24)
        
        # 检查系统状态
        is_healthy = True
        warnings = []
        
        if stats["active_alerts"] > 0:
            warnings.append(f"有 {stats['active_alerts']} 个活跃预警")
            
        if stats["total_alerts"] > 100:
            warnings.append(f"过去24小时预警数量较多: {stats['total_alerts']}")
            
        if stats["severity_stats"].get("critical", 0) > 0:
            warnings.append("存在严重级别预警")
            is_healthy = False
            
        return {
            "status": "healthy" if is_healthy else "warning",
            "is_healthy": is_healthy,
            "warnings": warnings,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警系统健康状态失败: {str(e)}")