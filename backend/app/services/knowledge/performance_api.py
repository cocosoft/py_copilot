"""
知识库性能监控API

提供知识库系统性能监控的RESTful API接口。
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from .optimized_retrieval_service import get_optimized_retrieval_service

router = APIRouter()


@router.get("/performance/stats")
async def get_performance_stats() -> Dict[str, Any]:
    """获取性能统计信息
    
    Returns:
        性能统计信息
    """
    try:
        retrieval_service = get_optimized_retrieval_service()
        stats = retrieval_service.get_performance_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")


@router.post("/performance/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """清空检索缓存
    
    Returns:
        清空结果
    """
    try:
        retrieval_service = get_optimized_retrieval_service()
        retrieval_service.clear_cache()
        
        return {
            "success": True,
            "message": "检索缓存已清空"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空缓存失败: {str(e)}")


@router.get("/performance/health")
async def get_system_health() -> Dict[str, Any]:
    """获取系统健康状态
    
    Returns:
        系统健康状态
    """
    try:
        retrieval_service = get_optimized_retrieval_service()
        
        # 检查基本功能
        document_count = retrieval_service.get_document_count()
        performance_stats = retrieval_service.get_performance_stats()
        
        # 评估健康状态
        cache_hit_rate = performance_stats.get("cache", {}).get("hit_rate", 0)
        avg_search_latency = performance_stats.get("performance", {}).get("search_latency", {}).get("avg", 0)
        
        health_status = "healthy"
        issues = []
        
        # 检查缓存命中率
        if cache_hit_rate < 0.1:  # 低于10%的命中率
            issues.append("缓存命中率较低")
            health_status = "degraded"
        
        # 检查搜索延迟
        if avg_search_latency > 2.0:  # 平均延迟超过2秒
            issues.append("搜索延迟较高")
            health_status = "degraded"
        
        # 检查文档数量
        if document_count == 0:
            issues.append("知识库为空")
            health_status = "warning"
        
        return {
            "success": True,
            "health": {
                "status": health_status,
                "issues": issues,
                "document_count": document_count,
                "cache_hit_rate": cache_hit_rate,
                "avg_search_latency": avg_search_latency
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统健康状态失败: {str(e)}")


@router.post("/performance/optimize/document")
async def optimize_document_processing(
    content: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """优化文档处理
    
    Args:
        content: 文档内容
        metadata: 文档元数据
        
    Returns:
        优化结果
    """
    try:
        retrieval_service = get_optimized_retrieval_service()
        optimized_chunks = retrieval_service.optimize_document_processing(content, metadata)
        
        return {
            "success": True,
            "optimization": {
                "original_size": len(content),
                "chunk_count": len(optimized_chunks),
                "avg_chunk_size": sum(len(chunk['content']) for chunk in optimized_chunks) / len(optimized_chunks) if optimized_chunks else 0,
                "chunks": optimized_chunks
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档优化失败: {str(e)}")


@router.get("/performance/metrics")
async def get_detailed_metrics() -> Dict[str, Any]:
    """获取详细性能指标
    
    Returns:
        详细性能指标
    """
    try:
        retrieval_service = get_optimized_retrieval_service()
        stats = retrieval_service.get_performance_stats()
        
        # 提取关键指标
        metrics = {
            "cache": {
                "hits": stats.get("cache", {}).get("hits", 0),
                "misses": stats.get("cache", {}).get("misses", 0),
                "hit_rate": stats.get("cache", {}).get("hit_rate", 0),
                "size": stats.get("cache", {}).get("cache_size", 0),
                "max_size": stats.get("cache", {}).get("max_size", 0)
            },
            "latency": {
                "search": stats.get("performance", {}).get("search_latency", {}),
                "cached_search": stats.get("performance", {}).get("search_latency_cached", {})
            },
            "throughput": {
                "total_searches": stats.get("cache", {}).get("hits", 0) + stats.get("cache", {}).get("misses", 0)
            }
        }
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取详细指标失败: {str(e)}")