"""
数据库监控API

提供数据库连接和性能数据的查询接口。
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database_monitor import database_monitor, DatabaseMetricType

router = APIRouter(prefix="/api/monitoring/database", tags=["数据库监控"])


class DatabaseSummaryResponse(BaseModel):
    """数据库摘要响应模型"""
    connection_count: Dict[str, Any]
    query_execution_time: Dict[str, Any]
    query_count: Dict[str, Any]
    error_count: Dict[str, Any]
    connection_pool_size: Dict[str, Any]
    total_queries: int
    total_errors: int
    error_rate: float
    window_size: int
    start_time: str


class DatabaseHealthResponse(BaseModel):
    """数据库健康状态响应模型"""
    status: str
    timestamp: str
    query_time_avg_ms: float
    error_rate: float
    total_queries: int
    warnings: List[str]
    is_healthy: bool
    database_path: str


class DatabaseTrendResponse(BaseModel):
    """数据库趋势响应模型"""
    metric_type: str
    data_points: List[Dict[str, Any]]
    count: int
    time_range_hours: int


@router.get("/summary", response_model=DatabaseSummaryResponse)
async def get_database_summary():
    """获取数据库摘要
    
    Returns:
        数据库摘要信息
    """
    try:
        summary = database_monitor.get_database_summary()
        return DatabaseSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库摘要失败: {str(e)}")


@router.get("/health", response_model=DatabaseHealthResponse)
async def get_database_health():
    """获取数据库健康状态
    
    Returns:
        数据库健康状态信息
    """
    try:
        health_status = database_monitor.check_database_health()
        return DatabaseHealthResponse(**health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库健康状态失败: {str(e)}")


@router.get("/trend/{metric_type}", response_model=DatabaseTrendResponse)
async def get_database_trend(metric_type: str, hours: int = 24):
    """获取数据库趋势数据
    
    Args:
        metric_type: 指标类型
        hours: 时间范围（小时，最大168）
        
    Returns:
        数据库趋势数据
    """
    # 验证指标类型
    try:
        metric_enum = DatabaseMetricType(metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的指标类型: {metric_type}")
    
    # 限制时间范围
    if hours > 168:  # 最大1周
        hours = 168
    elif hours < 1:
        hours = 1
        
    try:
        trend_data = database_monitor.get_database_trend(metric_enum, hours)
        
        return DatabaseTrendResponse(
            metric_type=metric_type,
            data_points=trend_data,
            count=len(trend_data),
            time_range_hours=hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库趋势数据失败: {str(e)}")


@router.get("/stats/connections")
async def get_connection_stats():
    """获取连接统计
    
    Returns:
        连接统计信息
    """
    try:
        summary = database_monitor.get_database_summary()
        
        return {
            "connection_count": summary[DatabaseMetricType.CONNECTION_COUNT.value],
            "connection_pool_size": summary[DatabaseMetricType.CONNECTION_POOL_SIZE.value]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取连接统计失败: {str(e)}")


@router.get("/stats/queries")
async def get_query_stats():
    """获取查询统计
    
    Returns:
        查询统计信息
    """
    try:
        summary = database_monitor.get_database_summary()
        
        return {
            "query_execution_time": summary[DatabaseMetricType.QUERY_EXECUTION_TIME.value],
            "query_count": summary[DatabaseMetricType.QUERY_COUNT.value],
            "error_count": summary[DatabaseMetricType.ERROR_COUNT.value],
            "total_queries": summary["total_queries"],
            "total_errors": summary["total_errors"],
            "error_rate": summary["error_rate"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询统计失败: {str(e)}")


@router.get("/info")
async def get_database_info():
    """获取数据库信息
    
    Returns:
        数据库基本信息
    """
    try:
        import os
        import sqlite3
        
        db_path = database_monitor.database_path
        
        # 检查数据库文件
        if not os.path.exists(db_path):
            return {
                "exists": False,
                "path": db_path,
                "error": "数据库文件不存在"
            }
        
        # 获取数据库文件信息
        file_size = os.path.getsize(db_path)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
        
        # 连接数据库获取表信息
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # 获取表数量
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        # 获取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return {
            "exists": True,
            "path": db_path,
            "file_size_bytes": file_size,
            "file_size_mb": file_size / 1024 / 1024,
            "last_modified": file_mtime.isoformat(),
            "table_count": table_count,
            "tables": tables
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库信息失败: {str(e)}")


@router.post("/connection-pool/size")
async def set_connection_pool_size(size: int):
    """设置连接池大小
    
    Args:
        size: 连接池大小
        
    Returns:
        设置结果
    """
    if size < 1 or size > 100:
        raise HTTPException(status_code=400, detail="连接池大小必须在1-100之间")
        
    try:
        database_monitor.set_connection_pool_size(size)
        return {
            "status": "success",
            "message": f"连接池大小已设置为 {size}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置连接池大小失败: {str(e)}")


@router.get("/types")
async def get_database_metric_types():
    """获取支持的数据库指标类型
    
    Returns:
        支持的数据库指标类型列表
    """
    return {
        "metric_types": [metric_type.value for metric_type in DatabaseMetricType],
        "descriptions": {
            "connection_count": "连接数量",
            "query_execution_time": "查询执行时间（毫秒）",
            "query_count": "查询计数",
            "error_count": "错误计数",
            "connection_pool_size": "连接池大小"
        }
    }