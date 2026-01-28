"""
错误监控API

提供错误数据的查询接口。
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .error_monitor import error_monitor, ErrorType, ErrorSeverity

router = APIRouter(prefix="/api/monitoring/errors", tags=["错误监控"])


class ErrorSummaryResponse(BaseModel):
    """错误摘要响应模型"""
    error_distribution: Dict[str, Any]
    error_rate_1h: float
    error_rate_24h: float
    recent_errors: List[Dict[str, Any]]
    window_size: int
    start_time: str


class ErrorHealthResponse(BaseModel):
    """错误健康状态响应模型"""
    status: str
    timestamp: str
    error_rate_1h: float
    error_rate_24h: float
    total_errors: int
    warnings: List[str]
    is_healthy: bool


class ErrorTrendResponse(BaseModel):
    """错误趋势响应模型"""
    data_points: List[Dict[str, Any]]
    count: int
    time_range_hours: int


class RecentErrorsResponse(BaseModel):
    """最近错误响应模型"""
    errors: List[Dict[str, Any]]
    count: int


@router.get("/summary", response_model=ErrorSummaryResponse)
async def get_error_summary():
    """获取错误摘要
    
    Returns:
        错误摘要信息
    """
    try:
        summary = error_monitor.get_error_summary()
        return ErrorSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误摘要失败: {str(e)}")


@router.get("/health", response_model=ErrorHealthResponse)
async def get_error_health():
    """获取错误健康状态
    
    Returns:
        错误健康状态信息
    """
    try:
        health_status = error_monitor.check_error_health()
        return ErrorHealthResponse(**health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误健康状态失败: {str(e)}")


@router.get("/trend", response_model=ErrorTrendResponse)
async def get_error_trend(hours: int = 24):
    """获取错误趋势数据
    
    Args:
        hours: 时间范围（小时，最大168）
        
    Returns:
        错误趋势数据
    """
    # 限制时间范围
    if hours > 168:  # 最大1周
        hours = 168
    elif hours < 1:
        hours = 1
        
    try:
        trend_data = error_monitor.stats.get_error_trend(hours)
        
        return ErrorTrendResponse(
            data_points=trend_data,
            count=len(trend_data),
            time_range_hours=hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误趋势数据失败: {str(e)}")


@router.get("/recent", response_model=RecentErrorsResponse)
async def get_recent_errors(limit: int = 10):
    """获取最近的错误记录
    
    Args:
        limit: 限制数量（最大50）
        
    Returns:
        最近的错误记录
    """
    # 限制查询数量
    if limit > 50:
        limit = 50
    elif limit < 1:
        limit = 1
        
    try:
        recent_errors = error_monitor.stats.get_recent_errors(limit)
        
        return RecentErrorsResponse(
            errors=recent_errors,
            count=len(recent_errors)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近错误记录失败: {str(e)}")


@router.get("/distribution/type")
async def get_error_distribution_by_type():
    """按类型获取错误分布
    
    Returns:
        按类型分类的错误分布
    """
    try:
        summary = error_monitor.get_error_summary()
        return summary["error_distribution"]["by_type"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误类型分布失败: {str(e)}")


@router.get("/distribution/severity")
async def get_error_distribution_by_severity():
    """按严重程度获取错误分布
    
    Returns:
        按严重程度分类的错误分布
    """
    try:
        summary = error_monitor.get_error_summary()
        return summary["error_distribution"]["by_severity"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误严重程度分布失败: {str(e)}")


@router.get("/rate")
async def get_error_rates():
    """获取错误率数据
    
    Returns:
        不同时间窗口的错误率
    """
    try:
        summary = error_monitor.get_error_summary()
        
        return {
            "error_rate_1h": summary["error_rate_1h"],
            "error_rate_6h": error_monitor.stats.get_error_rate(360),
            "error_rate_12h": error_monitor.stats.get_error_rate(720),
            "error_rate_24h": summary["error_rate_24h"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误率数据失败: {str(e)}")


@router.get("/types")
async def get_error_types():
    """获取支持的错误类型
    
    Returns:
        支持的错误类型列表
    """
    return {
        "error_types": [error_type.value for error_type in ErrorType],
        "descriptions": {
            "validation_error": "验证错误",
            "authentication_error": "认证错误",
            "authorization_error": "授权错误",
            "database_error": "数据库错误",
            "external_service_error": "外部服务错误",
            "internal_server_error": "内部服务器错误",
            "timeout_error": "超时错误",
            "unknown_error": "未知错误"
        }
    }


@router.get("/severities")
async def get_error_severities():
    """获取支持的严重程度
    
    Returns:
        支持的严重程度列表
    """
    return {
        "error_severities": [severity.value for severity in ErrorSeverity],
        "descriptions": {
            "low": "低严重度",
            "medium": "中等严重度",
            "high": "高严重度",
            "critical": "严重"
        }
    }