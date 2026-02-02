"""微服务监控API端点"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from datetime import datetime, timedelta
import psutil
import os

router = APIRouter()

# 全局监控服务实例（从主应用导入）
from app.api.main import get_monitoring_service

@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "monitoring"
    }

@router.get("/metrics/summary")
async def get_metrics_summary(
    duration: int = Query(300, description="时间范围（秒）")
):
    """获取性能指标摘要"""
    try:
        monitoring_service = get_monitoring_service()
        
        # 获取基础性能指标
        response_time_summary = monitoring_service.get_metrics_summary("response_time", duration)
        request_summary = monitoring_service.get_metrics_summary("request_count", duration)
        error_summary = monitoring_service.get_metrics_summary("error_count", duration)
        
        # 计算错误率
        error_rate = 0
        if request_summary["count"] > 0:
            error_rate = (error_summary["count"] / request_summary["count"]) * 100
        
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            "performance": {
                "response_time": response_time_summary,
                "request_count": request_summary,
                "error_count": error_summary,
                "error_rate": error_rate
            },
            "system": {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": memory.available / (1024**3),  # GB
                "disk_usage": disk.percent,
                "disk_free": disk.free / (1024**3)  # GB
            },
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标摘要失败: {str(e)}")

@router.get("/metrics/{metric_name}")
async def get_metric_data(
    metric_name: str,
    duration: int = Query(3600, description="时间范围（秒）")
):
    """获取特定指标数据"""
    try:
        monitoring_service = get_monitoring_service()
        summary = monitoring_service.get_metrics_summary(metric_name, duration)
        
        return {
            "metric_name": metric_name,
            "duration_seconds": duration,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标数据失败: {str(e)}")

@router.get("/alerts")
async def get_active_alerts():
    """获取活跃告警"""
    try:
        monitoring_service = get_monitoring_service()
        active_alerts = monitoring_service.get_active_alerts()
        
        return {
            "active_alerts": [
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
                for alert in active_alerts
            ],
            "count": len(active_alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警信息失败: {str(e)}")

@router.get("/alerts/statistics")
async def get_alert_statistics(
    duration: int = Query(3600, description="时间范围（秒）")
):
    """获取告警统计"""
    try:
        monitoring_service = get_monitoring_service()
        statistics = monitoring_service.get_alert_statistics(duration)
        
        return {
            "statistics": statistics,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警统计失败: {str(e)}")

@router.get("/system/info")
async def get_system_info():
    """获取系统信息"""
    try:
        # 获取系统信息
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        # 获取进程信息
        process = psutil.Process(os.getpid())
        
        return {
            "system": {
                "cpu": {
                    "count": cpu_count,
                    "frequency": cpu_freq.current if cpu_freq else None,
                    "usage": psutil.cpu_percent(interval=1)
                },
                "memory": {
                    "total": memory.total / (1024**3),  # GB
                    "available": memory.available / (1024**3),  # GB
                    "used": memory.used / (1024**3),  # GB
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total / (1024**3),  # GB
                    "used": disk.used / (1024**3),  # GB
                    "free": disk.free / (1024**3),  # GB
                    "percent": disk.percent
                },
                "boot_time": boot_time.isoformat(),
                "uptime": str(datetime.now() - boot_time)
            },
            "process": {
                "pid": process.pid,
                "name": process.name(),
                "memory_usage": process.memory_info().rss / (1024**2),  # MB
                "cpu_percent": process.cpu_percent(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")

@router.get("/services/status")
async def get_services_status():
    """获取微服务状态"""
    try:
        # 这里可以集成服务注册中心的信息
        # 目前返回一个模拟的服务状态
        services = {
            "gateway": {
                "status": "healthy",
                "port": 8000,
                "last_heartbeat": datetime.now().isoformat()
            },
            "chat": {
                "status": "healthy", 
                "port": 8001,
                "last_heartbeat": datetime.now().isoformat()
            },
            "search": {
                "status": "healthy",
                "port": 8002,
                "last_heartbeat": datetime.now().isoformat()
            },
            "file": {
                "status": "healthy",
                "port": 8003,
                "last_heartbeat": datetime.now().isoformat()
            },
            "voice": {
                "status": "healthy",
                "port": 8004,
                "last_heartbeat": datetime.now().isoformat()
            }
        }
        
        return {
            "services": services,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")


@router.get("/database/pool")
async def get_database_pool_status():
    """获取数据库连接池状态"""
    try:
        from app.core.database import get_pool_status
        
        pool_status = get_pool_status()
        
        return {
            "pool_status": pool_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库连接池状态失败: {str(e)}")