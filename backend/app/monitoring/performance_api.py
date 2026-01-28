"""
性能监控API

提供性能数据的查询接口。
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .performance_middleware import performance_monitor, MetricType

router = APIRouter(prefix="/api/monitoring", tags=["性能监控"])


class PerformanceSummaryResponse(BaseModel):
    """性能摘要响应模型"""
    response_time: Dict[str, Any]
    memory_usage: Dict[str, Any]
    request_stats: Dict[str, Any]
    window_size: int
    start_time: str


class MetricDataResponse(BaseModel):
    """指标数据响应模型"""
    metric_type: str
    value: float
    timestamp: str
    metadata: Dict[str, Any]


class RecentMetricsResponse(BaseModel):
    """最近指标响应模型"""
    metrics: List[MetricDataResponse]
    count: int


@router.get("/summary", response_model=PerformanceSummaryResponse)
async def get_performance_summary():
    """获取性能摘要
    
    Returns:
        性能摘要信息
    """
    try:
        summary = performance_monitor.get_performance_summary()
        return PerformanceSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能摘要失败: {str(e)}")


@router.get("/metrics/{metric_type}", response_model=RecentMetricsResponse)
async def get_recent_metrics(metric_type: str, limit: int = 10):
    """获取最近的指标数据
    
    Args:
        metric_type: 指标类型
        limit: 限制数量（最大100）
        
    Returns:
        最近的指标数据
    """
    # 验证指标类型
    try:
        metric_enum = MetricType(metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的指标类型: {metric_type}")
    
    # 限制查询数量
    if limit > 100:
        limit = 100
    elif limit < 1:
        limit = 1
        
    try:
        metrics_data = performance_monitor.get_recent_metrics(metric_enum, limit)
        
        # 转换为响应模型
        metrics = []
        for data in metrics_data:
            metrics.append(MetricDataResponse(**data))
            
        return RecentMetricsResponse(
            metrics=metrics,
            count=len(metrics)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标数据失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查接口
    
    Returns:
        健康状态信息
    """
    try:
        # 获取性能摘要
        summary = performance_monitor.get_performance_summary()
        
        # 检查关键指标
        response_time_avg = summary["response_time"]["avg"]
        error_rate = summary["request_stats"]["error_rate"]
        memory_avg = summary["memory_usage"]["avg"]
        
        # 健康状态判断
        is_healthy = True
        issues = []
        
        # 响应时间检查（超过1秒为警告）
        if response_time_avg > 1000:
            is_healthy = False
            issues.append(f"平均响应时间过高: {response_time_avg:.2f}ms")
            
        # 错误率检查（超过5%为警告）
        if error_rate > 5.0:
            is_healthy = False
            issues.append(f"错误率过高: {error_rate:.2f}%")
            
        # 内存使用检查（超过1GB为警告）
        if memory_avg > 1024:
            is_healthy = False
            issues.append(f"内存使用过高: {memory_avg:.2f}MB")
            
        status = "healthy" if is_healthy else "unhealthy"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "response_time_avg": response_time_avg,
            "error_rate": error_rate,
            "memory_usage_avg": memory_avg,
            "issues": issues,
            "uptime": summary["request_stats"]["uptime_seconds"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/stats/response-time")
async def get_response_time_stats():
    """获取响应时间统计
    
    Returns:
        响应时间统计信息
    """
    try:
        summary = performance_monitor.get_performance_summary()
        return summary["response_time"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取响应时间统计失败: {str(e)}")


@router.get("/stats/memory-usage")
async def get_memory_usage_stats():
    """获取内存使用统计
    
    Returns:
        内存使用统计信息
    """
    try:
        summary = performance_monitor.get_performance_summary()
        return summary["memory_usage"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内存使用统计失败: {str(e)}")


@router.get("/stats/request")
async def get_request_stats():
    """获取请求统计
    
    Returns:
        请求统计信息
    """
    try:
        summary = performance_monitor.get_performance_summary()
        return summary["request_stats"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取请求统计失败: {str(e)}")


@router.get("/metrics/types")
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
            "request_count": "请求计数"
        }
    }