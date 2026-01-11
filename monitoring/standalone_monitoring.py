"""独立监控服务（避免复杂的模块依赖）"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time

# 创建独立的监控应用
monitoring_app = FastAPI(title="Py Copilot 监控服务", version="1.0.0")

# 添加CORS中间件
monitoring_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 简单的内存存储（替代数据库）
metrics_store = {
    "response_time": [],
    "request_count": [],
    "error_count": [],
    "alerts": []
}

def record_metric(metric_type: str, value: float):
    """记录指标数据"""
    timestamp = datetime.now()
    metrics_store[metric_type].append({
        "timestamp": timestamp,
        "value": value
    })
    
    # 保持最近1000个数据点
    if len(metrics_store[metric_type]) > 1000:
        metrics_store[metric_type] = metrics_store[metric_type][-1000:]

def get_metrics_summary(metric_type: str, duration_seconds: int = 300) -> Dict[str, Any]:
    """获取指标摘要"""
    cutoff_time = datetime.now() - timedelta(seconds=duration_seconds)
    
    # 过滤指定时间范围内的数据
    recent_data = [
        item for item in metrics_store[metric_type]
        if item["timestamp"] >= cutoff_time
    ]
    
    if not recent_data:
        return {
            "count": 0,
            "avg": 0,
            "min": 0,
            "max": 0,
            "p95": 0
        }
    
    values = [item["value"] for item in recent_data]
    values.sort()
    
    return {
        "count": len(values),
        "avg": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "p95": values[int(len(values) * 0.95)] if len(values) > 0 else 0
    }

def add_alert(alert_type: str, message: str, severity: str = "warning"):
    """添加告警"""
    alert = {
        "id": len(metrics_store["alerts"]) + 1,
        "type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.now(),
        "resolved": False
    }
    metrics_store["alerts"].append(alert)
    
    # 保持最近100个告警
    if len(metrics_store["alerts"]) > 100:
        metrics_store["alerts"] = metrics_store["alerts"][-100:]

# 模拟一些初始数据
record_metric("response_time", 150.5)
record_metric("response_time", 120.3)
record_metric("response_time", 180.7)
record_metric("request_count", 1)
record_metric("request_count", 1)
record_metric("error_count", 0)

# API路由
@monitoring_app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Py Copilot 监控服务",
        "version": "1.0.0",
        "status": "running"
    }

@monitoring_app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": datetime.now().isoformat()
    }

@monitoring_app.get("/api/monitoring/metrics/summary")
async def get_metrics_summary_endpoint(
    duration: int = Query(300, description="时间范围（秒）")
):
    """获取性能指标摘要"""
    try:
        # 获取基础性能指标
        response_time_summary = get_metrics_summary("response_time", duration)
        request_summary = get_metrics_summary("request_count", duration)
        error_summary = get_metrics_summary("error_count", duration)
        
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

@monitoring_app.get("/api/monitoring/system/info")
async def get_system_info():
    """获取系统信息"""
    try:
        # 获取系统信息
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        # 获取网络信息
        net_io = psutil.net_io_counters()
        
        return {
            "system": {
                "boot_time": boot_time.isoformat(),
                "uptime_seconds": uptime.total_seconds(),
                "uptime_human": str(uptime).split('.')[0],
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")

@monitoring_app.get("/api/monitoring/alerts")
async def get_active_alerts():
    """获取活跃告警"""
    try:
        active_alerts = [
            alert for alert in metrics_store["alerts"]
            if not alert["resolved"]
        ]
        
        return {
            "alerts": active_alerts,
            "count": len(active_alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警失败: {str(e)}")

@monitoring_app.post("/api/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """解决告警"""
    try:
        for alert in metrics_store["alerts"]:
            if alert["id"] == alert_id:
                alert["resolved"] = True
                alert["resolved_at"] = datetime.now()
                return {"message": "告警已解决", "alert_id": alert_id}
        
        raise HTTPException(status_code=404, detail="告警不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")

@monitoring_app.post("/api/monitoring/metrics/record")
async def record_metric_endpoint(
    metric_type: str,
    value: float
):
    """记录指标数据（供其他服务调用）"""
    try:
        if metric_type not in ["response_time", "request_count", "error_count"]:
            raise HTTPException(status_code=400, detail="不支持的指标类型")
        
        record_metric(metric_type, value)
        
        # 如果响应时间过高，添加告警
        if metric_type == "response_time" and value > 5000:  # 5秒阈值
            add_alert("slow_response", f"响应时间过高: {value}ms", "warning")
        
        # 如果错误率过高，添加告警
        if metric_type == "error_count" and value > 10:
            add_alert("high_error_rate", f"错误计数过高: {value}", "error")
        
        return {"message": "指标记录成功", "metric_type": metric_type, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录指标失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import sys
    
    print("=" * 50)
    print("Py Copilot 独立监控服务启动")
    print("=" * 50)
    print("访问地址: http://localhost:8005")
    print("健康检查: http://localhost:8005/health")
    print("性能指标: http://localhost:8005/api/monitoring/metrics/summary")
    print("=" * 50)
    
    uvicorn.run(
        monitoring_app,
        host="localhost",
        port=8005,
        log_level="info"
    )