"""
外部服务监控API

提供外部服务状态和健康数据的查询接口。
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .external_service_monitor import external_service_monitor, ServiceMetricType, ServiceType, ServiceStatus

router = APIRouter(prefix="/api/monitoring/external-services", tags=["外部服务监控"])


class ServiceSummaryResponse(BaseModel):
    """服务摘要响应模型"""
    services: Dict[str, Any]
    total_services: int
    healthy_services: int
    overall_availability: float
    is_monitoring: bool


class ServiceHealthResponse(BaseModel):
    """服务健康状态响应模型"""
    status: str
    timestamp: str
    overall_availability: float
    healthy_services: int
    total_services: int
    warnings: List[str]
    problematic_services: List[Dict[str, Any]]
    is_healthy: bool


class ServiceTrendResponse(BaseModel):
    """服务趋势响应模型"""
    metric_type: str
    service_name: str
    data_points: List[Dict[str, Any]]
    count: int
    time_range_hours: int


class CriticalServicesReportResponse(BaseModel):
    """关键服务报告响应模型"""
    problematic_services: List[Dict[str, Any]]
    slow_services: List[Dict[str, Any]]
    overall_health: float
    timestamp: str


class RegisterServiceRequest(BaseModel):
    """注册服务请求模型"""
    name: str
    service_type: str
    endpoint: str
    check_interval: int = 60
    timeout: int = 10


@router.get("/summary", response_model=ServiceSummaryResponse)
async def get_service_summary():
    """获取服务摘要
    
    Returns:
        服务摘要信息
    """
    try:
        summary = external_service_monitor.get_service_summary()
        return ServiceSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务摘要失败: {str(e)}")


@router.get("/health", response_model=ServiceHealthResponse)
async def get_service_health():
    """获取服务健康状态
    
    Returns:
        服务健康状态信息
    """
    try:
        health_status = external_service_monitor.check_services_health()
        return ServiceHealthResponse(**health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务健康状态失败: {str(e)}")


@router.get("/trend/{service_name}/{metric_type}", response_model=ServiceTrendResponse)
async def get_service_trend(service_name: str, metric_type: str, hours: int = 24):
    """获取服务趋势数据
    
    Args:
        service_name: 服务名称
        metric_type: 指标类型
        hours: 时间范围（小时，最大168）
        
    Returns:
        服务趋势数据
    """
    # 验证服务名称
    if service_name not in external_service_monitor.services:
        raise HTTPException(status_code=404, detail=f"服务 {service_name} 未找到")
    
    # 验证指标类型
    try:
        metric_enum = ServiceMetricType(metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的指标类型: {metric_type}")
    
    # 限制时间范围
    if hours > 168:  # 最大1周
        hours = 168
    elif hours < 1:
        hours = 1
        
    try:
        trend_data = external_service_monitor.get_service_trend(metric_enum, service_name, hours)
        
        return ServiceTrendResponse(
            metric_type=metric_type,
            service_name=service_name,
            data_points=trend_data,
            count=len(trend_data),
            time_range_hours=hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务趋势数据失败: {str(e)}")


@router.get("/critical-report", response_model=CriticalServicesReportResponse)
async def get_critical_services_report():
    """获取关键服务报告
    
    Returns:
        关键服务报告
    """
    try:
        report = external_service_monitor.get_critical_services_report()
        return CriticalServicesReportResponse(**report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关键服务报告失败: {str(e)}")


@router.post("/register")
async def register_service(request: RegisterServiceRequest):
    """注册外部服务
    
    Args:
        request: 注册服务请求
        
    Returns:
        注册结果
    """
    # 验证服务类型
    try:
        service_type_enum = ServiceType(request.service_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的服务类型: {request.service_type}")
    
    # 验证参数
    if request.check_interval < 10:
        raise HTTPException(status_code=400, detail="检查间隔不能小于10秒")
    if request.timeout < 1 or request.timeout > 60:
        raise HTTPException(status_code=400, detail="超时时间必须在1-60秒之间")
    
    try:
        external_service_monitor.register_service(
            name=request.name,
            service_type=service_type_enum,
            endpoint=request.endpoint,
            check_interval=request.check_interval,
            timeout=request.timeout
        )
        
        return {
            "status": "success",
            "message": f"服务 {request.name} 已注册",
            "service_name": request.name,
            "service_type": request.service_type,
            "endpoint": request.endpoint,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册服务失败: {str(e)}")


@router.delete("/unregister/{service_name}")
async def unregister_service(service_name: str):
    """取消注册外部服务
    
    Args:
        service_name: 服务名称
        
    Returns:
        取消注册结果
    """
    if service_name not in external_service_monitor.services:
        raise HTTPException(status_code=404, detail=f"服务 {service_name} 未找到")
        
    try:
        external_service_monitor.unregister_service(service_name)
        
        return {
            "status": "success",
            "message": f"服务 {service_name} 已取消注册",
            "service_name": service_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消注册服务失败: {str(e)}")


@router.post("/check-all")
async def check_all_services():
    """手动检查所有服务
    
    Returns:
        检查结果
    """
    try:
        results = external_service_monitor.check_all_services()
        
        return {
            "status": "success",
            "message": "所有服务已检查完成",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查服务失败: {str(e)}")


@router.get("/services")
async def get_all_services():
    """获取所有已注册的服务
    
    Returns:
        所有服务列表
    """
    try:
        services_list = []
        for service_name, service in external_service_monitor.services.items():
            stats = service.get_stats()
            services_list.append({
                "name": service_name,
                "type": stats["type"],
                "endpoint": stats["endpoint"],
                "status": stats["status"],
                "availability": stats["availability"],
                "last_check_time": stats["last_check_time"]
            })
            
        return {
            "services": services_list,
            "count": len(services_list),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务列表失败: {str(e)}")


@router.get("/service/{service_name}")
async def get_service_details(service_name: str):
    """获取服务详细信息
    
    Args:
        service_name: 服务名称
        
    Returns:
        服务详细信息
    """
    if service_name not in external_service_monitor.services:
        raise HTTPException(status_code=404, detail=f"服务 {service_name} 未找到")
        
    try:
        service = external_service_monitor.services[service_name]
        stats = service.get_stats()
        
        return {
            "service": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务详情失败: {str(e)}")


@router.post("/monitoring/start")
async def start_monitoring():
    """开始监控服务
    
    Returns:
        启动结果
    """
    try:
        await external_service_monitor.start_monitoring()
        
        return {
            "status": "success",
            "message": "外部服务监控已启动",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动监控失败: {str(e)}")


@router.post("/monitoring/stop")
async def stop_monitoring():
    """停止监控服务
    
    Returns:
        停止结果
    """
    try:
        await external_service_monitor.stop_monitoring()
        
        return {
            "status": "success",
            "message": "外部服务监控已停止",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止监控失败: {str(e)}")


@router.get("/types")
async def get_service_metric_types():
    """获取支持的服务指标类型
    
    Returns:
        支持的服务指标类型列表
    """
    return {
        "metric_types": [metric_type.value for metric_type in ServiceMetricType],
        "descriptions": {
            "response_time": "响应时间（毫秒）",
            "availability": "可用性（百分比）",
            "error_rate": "错误率（百分比）",
            "throughput": "吞吐量（请求/秒）"
        }
    }


@router.get("/service-types")
async def get_service_types():
    """获取支持的服务类型
    
    Returns:
        支持的服务类型列表
    """
    return {
        "service_types": [service_type.value for service_type in ServiceType],
        "descriptions": {
            "database": "数据库服务",
            "api": "API服务",
            "cache": "缓存服务",
            "message_queue": "消息队列",
            "storage": "存储服务",
            "external_api": "外部API"
        }
    }


@router.get("/status-types")
async def get_status_types():
    """获取支持的状态类型
    
    Returns:
        支持的状态类型列表
    """
    return {
        "status_types": [status_type.value for status_type in ServiceStatus],
        "descriptions": {
            "healthy": "健康",
            "degraded": "降级",
            "unhealthy": "不健康",
            "unknown": "未知",
            "offline": "离线"
        }
    }