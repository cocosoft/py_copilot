"""
API监控API

提供API调用统计和性能数据的查询接口。
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .api_monitor import api_monitor, APIMetricType

router = APIRouter(prefix="/api/monitoring/api", tags=["API监控"])


class APISummaryResponse(BaseModel):
    """API摘要响应模型"""
    response_time: Dict[str, Any]
    call_count: Dict[str, Any]
    error_count: Dict[str, Any]
    success_rate: Dict[str, Any]
    throughput: Dict[str, Any]
    endpoints: Dict[str, Any]
    total_calls: int
    total_errors: int
    overall_success_rate: float
    window_size: int
    start_time: str


class APIHealthResponse(BaseModel):
    """API健康状态响应模型"""
    status: str
    timestamp: str
    response_time_avg_s: float
    overall_error_rate: float
    total_calls: int
    total_endpoints: int
    warnings: List[str]
    problematic_endpoints: List[Dict[str, Any]]
    is_healthy: bool


class APITrendResponse(BaseModel):
    """API趋势响应模型"""
    metric_type: str
    data_points: List[Dict[str, Any]]
    count: int
    time_range_hours: int


class EndpointAnalysisResponse(BaseModel):
    """端点分析响应模型"""
    path: str
    method: str
    call_count: int
    error_count: int
    success_rate: float
    avg_response_time: float
    last_call_time: Optional[str]
    recent_response_times: List[float]


class PerformanceReportResponse(BaseModel):
    """性能报告响应模型"""
    summary: Dict[str, Any]
    top_called_endpoints: List[Dict[str, Any]]
    top_error_endpoints: List[Dict[str, Any]]
    top_slow_endpoints: List[Dict[str, Any]]
    timestamp: str


@router.get("/summary", response_model=APISummaryResponse)
async def get_api_summary():
    """获取API摘要
    
    Returns:
        API摘要信息
    """
    try:
        summary = api_monitor.get_api_summary()
        return APISummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取API摘要失败: {str(e)}")


@router.get("/health", response_model=APIHealthResponse)
async def get_api_health():
    """获取API健康状态
    
    Returns:
        API健康状态信息
    """
    try:
        health_status = api_monitor.check_api_health()
        return APIHealthResponse(**health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取API健康状态失败: {str(e)}")


@router.get("/trend/{metric_type}", response_model=APITrendResponse)
async def get_api_trend(metric_type: str, hours: int = 24):
    """获取API趋势数据
    
    Args:
        metric_type: 指标类型
        hours: 时间范围（小时，最大168）
        
    Returns:
        API趋势数据
    """
    # 验证指标类型
    try:
        metric_enum = APIMetricType(metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的指标类型: {metric_type}")
    
    # 限制时间范围
    if hours > 168:  # 最大1周
        hours = 168
    elif hours < 1:
        hours = 1
        
    try:
        trend_data = api_monitor.get_api_trend(metric_enum, hours)
        
        return APITrendResponse(
            metric_type=metric_type,
            data_points=trend_data,
            count=len(trend_data),
            time_range_hours=hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取API趋势数据失败: {str(e)}")


@router.get("/endpoints/{path:path}")
async def get_endpoint_analysis(path: str, method: str = "GET"):
    """获取端点分析
    
    Args:
        path: API路径
        method: HTTP方法
        
    Returns:
        端点分析信息
    """
    try:
        analysis = api_monitor.get_endpoint_analysis(path, method)
        if analysis is None:
            raise HTTPException(status_code=404, detail=f"端点 {method} {path} 未找到")
            
        return EndpointAnalysisResponse(**analysis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取端点分析失败: {str(e)}")


@router.get("/performance-report", response_model=PerformanceReportResponse)
async def get_performance_report():
    """获取性能报告
    
    Returns:
        性能报告
    """
    try:
        report = api_monitor.get_performance_report()
        return PerformanceReportResponse(**report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能报告失败: {str(e)}")


@router.get("/stats/endpoints")
async def get_endpoints_stats():
    """获取所有端点统计
    
    Returns:
        所有端点统计信息
    """
    try:
        summary = api_monitor.get_api_summary()
        return summary["endpoints"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取端点统计失败: {str(e)}")


@router.get("/stats/top-endpoints")
async def get_top_endpoints(limit: int = 10, sort_by: str = "call_count"):
    """获取排名靠前的端点
    
    Args:
        limit: 限制数量（最大50）
        sort_by: 排序字段（call_count, error_count, avg_response_time）
        
    Returns:
        排名靠前的端点列表
    """
    # 验证参数
    if limit > 50:
        limit = 50
    elif limit < 1:
        limit = 1
        
    if sort_by not in ["call_count", "error_count", "avg_response_time"]:
        raise HTTPException(status_code=400, detail="排序字段必须是 call_count, error_count 或 avg_response_time")
        
    try:
        top_endpoints = api_monitor.stats.get_top_endpoints(limit, sort_by)
        return {
            "top_endpoints": top_endpoints,
            "limit": limit,
            "sort_by": sort_by,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排名靠前的端点失败: {str(e)}")


@router.get("/stats/overall")
async def get_overall_stats():
    """获取总体统计
    
    Returns:
        总体统计信息
    """
    try:
        summary = api_monitor.get_api_summary()
        
        return {
            "total_calls": summary["total_calls"],
            "total_errors": summary["total_errors"],
            "overall_success_rate": summary["overall_success_rate"],
            "total_endpoints": len(summary["endpoints"]),
            "avg_response_time_ms": summary[APIMetricType.RESPONSE_TIME.value]["avg"],
            "start_time": summary["start_time"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取总体统计失败: {str(e)}")


@router.post("/record-call")
async def record_api_call(path: str, method: str, response_time: float, is_error: bool = False):
    """记录API调用（用于测试或手动记录）
    
    Args:
        path: API路径
        method: HTTP方法
        response_time: 响应时间（秒）
        is_error: 是否错误
        
    Returns:
        记录结果
    """
    if response_time < 0:
        raise HTTPException(status_code=400, detail="响应时间不能为负数")
        
    try:
        api_monitor.record_api_call(path, method, response_time, is_error)
        
        return {
            "status": "success",
            "message": "API调用已记录",
            "path": path,
            "method": method,
            "response_time": response_time,
            "is_error": is_error,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录API调用失败: {str(e)}")


@router.get("/types")
async def get_api_metric_types():
    """获取支持的API指标类型
    
    Returns:
        支持的API指标类型列表
    """
    return {
        "metric_types": [metric_type.value for metric_type in APIMetricType],
        "descriptions": {
            "response_time": "响应时间（毫秒）",
            "call_count": "调用计数",
            "error_count": "错误计数",
            "success_rate": "成功率（百分比）",
            "throughput": "吞吐量（调用/秒）"
        }
    }


@router.get("/endpoints")
async def get_all_endpoints():
    """获取所有监控的端点列表
    
    Returns:
        所有端点列表
    """
    try:
        summary = api_monitor.get_api_summary()
        
        endpoints_list = []
        for endpoint_key, endpoint_stats in summary["endpoints"].items():
            endpoints_list.append({
                "endpoint": endpoint_key,
                "path": endpoint_stats["path"],
                "method": endpoint_stats["method"],
                "call_count": endpoint_stats["call_count"],
                "success_rate": endpoint_stats["success_rate"]
            })
            
        return {
            "endpoints": endpoints_list,
            "count": len(endpoints_list),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取端点列表失败: {str(e)}")