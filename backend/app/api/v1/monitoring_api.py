#!/usr/bin/env python3
"""
监控告警API

提供系统监控和告警的HTTP接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.services.knowledge.monitoring_service import (
    get_monitoring_service,
    Alert,
    AlertLevel,
    AlertType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["监控告警"])


# ============== 数据模型 ==============

class AlertLevelEnum(str, Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertTypeEnum(str, Enum):
    """告警类型枚举"""
    TASK_FAILED = "task_failed"
    TASK_TIMEOUT = "task_timeout"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    LOW_SUCCESS_RATE = "low_success_rate"
    RESOURCE_HIGH = "resource_high"
    SYSTEM_ERROR = "system_error"


class AlertResponse(BaseModel):
    """告警响应模型"""
    id: str = Field(..., description="告警ID")
    type: AlertTypeEnum = Field(..., description="告警类型")
    level: AlertLevelEnum = Field(..., description="告警级别")
    message: str = Field(..., description="告警消息")
    timestamp: str = Field(..., description="告警时间")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    acknowledged: bool = Field(default=False, description="是否已确认")
    acknowledged_by: Optional[str] = Field(default=None, description="确认人")
    acknowledged_at: Optional[str] = Field(default=None, description="确认时间")


class AlertListResponse(BaseModel):
    """告警列表响应"""
    alerts: List[AlertResponse] = Field(..., description="告警列表")
    total: int = Field(..., description="总数")
    unacknowledged: int = Field(..., description="未确认数")


class AcknowledgeAlertRequest(BaseModel):
    """确认告警请求"""
    user: str = Field(..., description="确认用户")


class MetricData(BaseModel):
    """指标数据"""
    name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    timestamp: str = Field(..., description="时间戳")
    labels: Dict[str, str] = Field(default_factory=dict, description="标签")


class MetricQueryResponse(BaseModel):
    """指标查询响应"""
    name: str = Field(..., description="指标名称")
    data: List[MetricData] = Field(..., description="指标数据")


class MonitoringStats(BaseModel):
    """监控统计"""
    alerts: Dict[str, Any] = Field(..., description="告警统计")
    metrics: Dict[str, int] = Field(..., description="指标统计")
    tasks: Dict[str, Any] = Field(..., description="任务统计")


class CreateAlertRequest(BaseModel):
    """创建告警请求"""
    type: AlertTypeEnum = Field(..., description="告警类型")
    level: AlertLevelEnum = Field(..., description="告警级别")
    message: str = Field(..., description="告警消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")


# ============== API端点 ==============

@router.get("/alerts", response_model=AlertListResponse)
async def get_alerts(
    level: Optional[AlertLevelEnum] = Query(None, description="告警级别过滤"),
    alert_type: Optional[AlertTypeEnum] = Query(None, description="告警类型过滤"),
    acknowledged: Optional[bool] = Query(None, description="确认状态过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取告警列表
    
    支持按级别、类型、确认状态过滤
    """
    try:
        service = get_monitoring_service()
        
        # 转换枚举
        level_filter = AlertLevel(level.value) if level else None
        type_filter = AlertType(alert_type.value) if alert_type else None
        
        alerts = service.get_alerts(
            level=level_filter,
            alert_type=type_filter,
            acknowledged=acknowledged,
            limit=limit + offset
        )
        
        # 应用偏移量
        alerts = alerts[offset:offset + limit]
        
        # 转换为响应模型
        alert_responses = [
            AlertResponse(
                id=a.id,
                type=AlertTypeEnum(a.type.value),
                level=AlertLevelEnum(a.level.value),
                message=a.message,
                timestamp=a.timestamp.isoformat(),
                details=a.details,
                acknowledged=a.acknowledged,
                acknowledged_by=a.acknowledged_by,
                acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            )
            for a in alerts
        ]
        
        # 获取统计
        all_alerts = service.get_alerts()
        unacknowledged_count = len([a for a in all_alerts if not a.acknowledged])
        
        return AlertListResponse(
            alerts=alert_responses,
            total=len(all_alerts),
            unacknowledged=unacknowledged_count
        )
        
    except Exception as e:
        logger.error(f"获取告警列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_alert(alert_id: str, request: AcknowledgeAlertRequest):
    """
    确认告警
    
    将告警标记为已确认状态
    """
    try:
        service = get_monitoring_service()
        success = service.acknowledge_alert(alert_id, request.user)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"告警不存在: {alert_id}")
        
        return {
            "success": True,
            "message": "告警已确认",
            "alert_id": alert_id,
            "acknowledged_by": request.user,
            "acknowledged_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认告警失败: {e}")
        raise HTTPException(status_code=500, detail=f"确认告警失败: {str(e)}")


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(request: CreateAlertRequest):
    """
    创建告警
    
    手动创建系统告警
    """
    try:
        service = get_monitoring_service()
        
        alert = service.create_alert(
            type=AlertType(request.type.value),
            level=AlertLevel(request.level.value),
            message=request.message,
            details=request.details or {}
        )
        
        return AlertResponse(
            id=alert.id,
            type=AlertTypeEnum(alert.type.value),
            level=AlertLevelEnum(alert.level.value),
            message=alert.message,
            timestamp=alert.timestamp.isoformat(),
            details=alert.details,
            acknowledged=alert.acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        )
        
    except Exception as e:
        logger.error(f"创建告警失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建告警失败: {str(e)}")


@router.get("/metrics/{metric_name}", response_model=MetricQueryResponse)
async def get_metrics(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168, description="查询最近几小时的数据"),
):
    """
    获取指标数据
    
    查询指定指标的历史数据
    """
    try:
        service = get_monitoring_service()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = service.get_metrics(metric_name, start_time, end_time)
        
        metric_data = [
            MetricData(
                name=m.name,
                value=m.value,
                timestamp=m.timestamp.isoformat(),
                labels=m.labels
            )
            for m in metrics
        ]
        
        return MetricQueryResponse(
            name=metric_name,
            data=metric_data
        )
        
    except Exception as e:
        logger.error(f"获取指标数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取指标数据失败: {str(e)}")


@router.get("/stats", response_model=MonitoringStats)
async def get_monitoring_stats():
    """
    获取监控统计
    
    返回系统监控的整体统计信息
    """
    try:
        service = get_monitoring_service()
        stats = service.get_stats()
        
        return MonitoringStats(
            alerts=stats['alerts'],
            metrics=stats['metrics'],
            tasks=stats['tasks']
        )
        
    except Exception as e:
        logger.error(f"获取监控统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取监控统计失败: {str(e)}")


@router.post("/alerts/export")
async def export_alerts(filepath: str = Query(..., description="导出文件路径")):
    """
    导出告警
    
    将所有告警导出到JSON文件
    """
    try:
        service = get_monitoring_service()
        service.export_alerts(filepath)
        
        return {
            "success": True,
            "message": "告警已导出",
            "filepath": filepath
        }
        
    except Exception as e:
        logger.error(f"导出告警失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出告警失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查
    
    检查监控服务状态
    """
    try:
        service = get_monitoring_service()
        stats = service.get_stats()
        
        # 检查是否有严重告警
        critical_alerts = [
            a for a in service.get_alerts() 
            if a.level == AlertLevel.CRITICAL and not a.acknowledged
        ]
        
        status = "healthy"
        if critical_alerts:
            status = "warning"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "alerts": {
                "total": stats['alerts']['total'],
                "unacknowledged": stats['alerts']['unacknowledged'],
                "critical": len(critical_alerts)
            },
            "metrics_count": len(stats['metrics']),
            "tasks_count": stats['tasks']['total']
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.delete("/alerts/cleanup")
async def cleanup_old_alerts(days: int = Query(7, ge=1, le=30, description="清理几天前的告警")):
    """
    清理旧告警
    
    删除指定天数前的已确认告警
    """
    try:
        service = get_monitoring_service()
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # 获取要删除的告警
        old_alerts = [
            a for a in service.alerts 
            if a.timestamp < cutoff_time and a.acknowledged
        ]
        
        # 删除
        service.alerts = [
            a for a in service.alerts 
            if not (a.timestamp < cutoff_time and a.acknowledged)
        ]
        
        return {
            "success": True,
            "message": f"已清理 {len(old_alerts)} 条旧告警",
            "deleted_count": len(old_alerts),
            "cutoff_date": cutoff_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理旧告警失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理旧告警失败: {str(e)}")
