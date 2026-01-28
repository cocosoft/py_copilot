"""
内存监控API

提供内存使用数据的查询接口。
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .memory_monitor import memory_monitor, MemoryType

router = APIRouter(prefix="/api/monitoring/memory", tags=["内存监控"])


class MemorySummaryResponse(BaseModel):
    """内存摘要响应模型"""
    process_rss: Dict[str, Any]
    process_vms: Dict[str, Any]
    system_total: Dict[str, Any]
    system_available: Dict[str, Any]
    system_used: Dict[str, Any]
    system_percent: Dict[str, Any]
    window_size: int
    start_time: str


class MemoryHealthResponse(BaseModel):
    """内存健康状态响应模型"""
    status: str
    timestamp: str
    process_rss_mb: float
    system_memory_percent: float
    warnings: List[str]
    is_healthy: bool


class MemoryTrendResponse(BaseModel):
    """内存趋势响应模型"""
    memory_type: str
    data_points: List[Dict[str, Any]]
    count: int
    time_range_hours: int


@router.get("/summary", response_model=MemorySummaryResponse)
async def get_memory_summary():
    """获取内存摘要
    
    Returns:
        内存摘要信息
    """
    try:
        summary = memory_monitor.get_memory_summary()
        return MemorySummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内存摘要失败: {str(e)}")


@router.get("/health", response_model=MemoryHealthResponse)
async def get_memory_health():
    """获取内存健康状态
    
    Returns:
        内存健康状态信息
    """
    try:
        health_status = memory_monitor.check_memory_health()
        return MemoryHealthResponse(**health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内存健康状态失败: {str(e)}")


@router.get("/trend/{memory_type}", response_model=MemoryTrendResponse)
async def get_memory_trend(memory_type: str, hours: int = 24):
    """获取内存趋势数据
    
    Args:
        memory_type: 内存类型
        hours: 时间范围（小时，最大168）
        
    Returns:
        内存趋势数据
    """
    # 验证内存类型
    try:
        memory_enum = MemoryType(memory_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的内存类型: {memory_type}")
    
    # 限制时间范围
    if hours > 168:  # 最大1周
        hours = 168
    elif hours < 1:
        hours = 1
        
    try:
        trend_data = memory_monitor.get_memory_trend(memory_enum, hours)
        
        return MemoryTrendResponse(
            memory_type=memory_type,
            data_points=trend_data,
            count=len(trend_data),
            time_range_hours=hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内存趋势数据失败: {str(e)}")


@router.get("/stats/process")
async def get_process_memory_stats():
    """获取进程内存统计
    
    Returns:
        进程内存统计信息
    """
    try:
        summary = memory_monitor.get_memory_summary()
        
        return {
            "process_rss": summary[MemoryType.PROCESS_RSS.value],
            "process_vms": summary[MemoryType.PROCESS_VMS.value]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取进程内存统计失败: {str(e)}")


@router.get("/stats/system")
async def get_system_memory_stats():
    """获取系统内存统计
    
    Returns:
        系统内存统计信息
    """
    try:
        summary = memory_monitor.get_memory_summary()
        
        return {
            "system_total": summary[MemoryType.SYSTEM_TOTAL.value],
            "system_available": summary[MemoryType.SYSTEM_AVAILABLE.value],
            "system_used": summary[MemoryType.SYSTEM_USED.value],
            "system_percent": summary[MemoryType.SYSTEM_PERCENT.value]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统内存统计失败: {str(e)}")


@router.get("/leak-detection")
async def check_memory_leak():
    """检查内存泄漏
    
    Returns:
        内存泄漏检查结果
    """
    try:
        # 检查进程RSS内存泄漏
        rss_leak = memory_monitor.stats.detect_memory_leak(MemoryType.PROCESS_RSS)
        
        # 检查进程VMS内存泄漏
        vms_leak = memory_monitor.stats.detect_memory_leak(MemoryType.PROCESS_VMS)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "process_rss_leak_detected": rss_leak,
            "process_vms_leak_detected": vms_leak,
            "leak_detected": rss_leak or vms_leak,
            "description": "内存泄漏检测基于内存增长速率分析"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内存泄漏检查失败: {str(e)}")


@router.get("/types")
async def get_memory_types():
    """获取支持的内存类型
    
    Returns:
        支持的内存类型列表
    """
    return {
        "memory_types": [memory_type.value for memory_type in MemoryType],
        "descriptions": {
            "process_rss": "进程常驻内存（MB）",
            "process_vms": "进程虚拟内存（MB）",
            "system_total": "系统总内存（GB）",
            "system_available": "系统可用内存（GB）",
            "system_used": "系统已用内存（GB）",
            "system_percent": "系统内存使用百分比"
        }
    }