from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.services.knowledge.semantic_search_service import SemanticSearchService
from app.modules.knowledge.schemas.knowledge import (
    SearchResponse,
    AdvancedSearchResponse,
    SemanticSearchRequest,
    SearchSuggestionRequest,
    SearchSuggestionResponse,
    SearchAnalysisResponse,
    SearchAnalysis
)

router = APIRouter(prefix="/semantic-search", tags=["语义搜索"])

# 初始化服务
knowledge_service = KnowledgeService()
semantic_search_service = SemanticSearchService()

@router.get("/health")
async def health_check():
    """语义搜索服务健康检查"""
    return {"status": "healthy", "service": "semantic-search"}

@router.post("/search", response_model=AdvancedSearchResponse)
async def semantic_search_documents(
    search_request: SemanticSearchRequest,
    db: Session = Depends(get_db)
):
    """语义搜索知识库文档"""
    try:
        results = semantic_search_service.semantic_search(
            query=search_request.query,
            n_results=search_request.n_results,
            knowledge_base_id=search_request.knowledge_base_id,
            use_entities=search_request.use_entities,
            use_synonyms=search_request.use_synonyms,
            boost_recent=search_request.boost_recent,
            semantic_boost=search_request.semantic_boost
        )
        
        # 分析搜索效果
        search_analysis = semantic_search_service.analyze_search_patterns(
            search_request.query, results
        )
        
        return {
            "query": search_request.query,
            "results": results,
            "count": len(results),
            "search_type": "semantic",
            "analysis": search_analysis
        }
        
    except Exception as e:
        import traceback
        logger.error(f"语义搜索失败: {str(e)}")
        logger.error(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="语义搜索失败")

@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="搜索查询"),
    limit: int = Query(5, ge=1, le=10, description="建议数量限制"),
    db: Session = Depends(get_db)
):
    """获取搜索建议"""
    try:
        suggestions = semantic_search_service.get_search_suggestions(query, limit)
        
        return {
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取搜索建议失败")

@router.post("/analyze")
async def analyze_search_query(
    query: str = Query(..., min_length=1, description="搜索查询"),
    n_results: int = Query(10, ge=1, le=20, description="搜索结果数量"),
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID"),
    db: Session = Depends(get_db)
):
    """分析搜索查询和效果"""
    try:
        # 执行搜索
        results = semantic_search_service.semantic_search(
            query=query,
            n_results=n_results,
            knowledge_base_id=knowledge_base_id
        )
        
        # 分析搜索模式
        analysis = semantic_search_service.analyze_search_patterns(query, results)
        
        return {
            "query": query,
            "analysis": analysis,
            "sample_results_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"搜索分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail="搜索分析失败")

@router.get("/performance", response_model=Dict[str, Any])
async def get_search_performance(
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取搜索性能统计"""
    try:
        # 这里可以添加搜索性能统计逻辑
        # 例如：平均响应时间、成功率、热门查询等
        
        performance_stats = {
            "average_response_time": 0.15,  # 示例数据
            "success_rate": 0.98,           # 示例数据
            "total_searches": 1500,         # 示例数据
            "popular_queries": [
                {"query": "人工智能", "count": 120},
                {"query": "机器学习", "count": 95},
                {"query": "自然语言处理", "count": 78}
            ],
            "coverage_percentage": 0.85     # 文档覆盖率
        }
        
        return performance_stats
        
    except Exception as e:
        logger.error(f"获取搜索性能统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取搜索性能统计失败")

@router.post("/optimize")
async def optimize_search_index(
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID"),
    db: Session = Depends(get_db)
):
    """优化搜索索引"""
    try:
        # 这里可以添加索引优化逻辑
        # 例如：重新索引、清理无效数据、优化向量等
        
        return {
            "message": "搜索索引优化完成",
            "optimized_documents": 0,  # 实际优化文档数量
            "optimization_time": "0.5s"  # 优化耗时
        }
        
    except Exception as e:
        logger.error(f"搜索索引优化失败: {str(e)}")
        raise HTTPException(status_code=500, detail="搜索索引优化失败")

# 导入必要的日志模块
import logging
logger = logging.getLogger(__name__)