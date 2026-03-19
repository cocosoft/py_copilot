"""
智能搜索API模块

提供智能搜索相关的API端点
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.knowledge.intelligent_search_service import (
    intelligent_search_service,
    SearchContext,
    SearchIntent
)

router = APIRouter(prefix="/intelligent-search", tags=["智能搜索"])


# ============ 请求/响应模型 ============

class SearchContextRequest(BaseModel):
    """搜索上下文请求模型"""
    user_id: Optional[str] = Field(None, description="用户ID")
    knowledge_base_id: Optional[int] = Field(None, description="知识库ID")
    previous_queries: List[str] = Field(default_factory=list, description="历史查询")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")


class IntelligentSearchRequest(BaseModel):
    """智能搜索请求模型"""
    query: str = Field(..., description="搜索查询", min_length=1, max_length=500)
    context: Optional[SearchContextRequest] = Field(None, description="搜索上下文")
    n_results: int = Field(10, description="返回结果数量", ge=1, le=50)
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class SearchResultItem(BaseModel):
    """搜索结果项模型"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容摘要")
    score: float = Field(..., description="相关性分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")


class QueryUnderstanding(BaseModel):
    """查询理解模型"""
    original_query: str = Field(..., description="原始查询")
    normalized_query: str = Field(..., description="规范化查询")
    query_type: str = Field(..., description="查询类型")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="提取的实体")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    concepts: List[str] = Field(default_factory=list, description="概念")


class IntelligentSearchResponse(BaseModel):
    """智能搜索响应模型"""
    success: bool = Field(True, description="是否成功")
    query: str = Field(..., description="搜索查询")
    search_intent: str = Field(..., description="搜索意图")
    query_understanding: QueryUnderstanding = Field(..., description="查询理解")
    results: List[SearchResultItem] = Field(default_factory=list, description="搜索结果")
    related_queries: List[str] = Field(default_factory=list, description="相关查询")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="推荐内容")
    facets: Dict[str, List[str]] = Field(default_factory=dict, description="分面信息")
    search_stats: Dict[str, Any] = Field(default_factory=dict, description="搜索统计")


class SearchAnalyticsResponse(BaseModel):
    """搜索分析响应模型"""
    success: bool = Field(True, description="是否成功")
    query_analysis: Dict[str, Any] = Field(..., description="查询分析")
    search_performance: Dict[str, Any] = Field(..., description="搜索性能")
    result_quality: Dict[str, Any] = Field(..., description="结果质量")
    user_engagement: Dict[str, Any] = Field(..., description="用户参与度")


# ============ API端点 ============

@router.post("/search", response_model=IntelligentSearchResponse)
async def intelligent_search(request: IntelligentSearchRequest):
    """
    执行智能搜索
    
    提供基于语义理解和意图识别的智能搜索功能
    
    Args:
        request: 智能搜索请求
        
    Returns:
        智能搜索结果，包括查询理解、搜索意图、推荐内容等
        
    Example:
        ```json
        {
            "query": "人工智能技术应用",
            "n_results": 10,
            "context": {
                "user_id": "user_123",
                "knowledge_base_id": 1
            }
        }
        ```
    """
    try:
        # 构建搜索上下文
        context = None
        if request.context:
            context = SearchContext(
                user_id=request.context.user_id,
                knowledge_base_id=request.context.knowledge_base_id,
                previous_queries=request.context.previous_queries,
                user_preferences=request.context.user_preferences
            )
        
        # 执行智能搜索
        result = intelligent_search_service.intelligent_search(
            query=request.query,
            context=context,
            n_results=request.n_results,
            filters=request.filters
        )
        
        # 构建响应
        return IntelligentSearchResponse(
            success=True,
            query=request.query,
            search_intent=result.search_intent.value,
            query_understanding=QueryUnderstanding(
                original_query=result.query_understanding.get("original_query", ""),
                normalized_query=result.query_understanding.get("normalized_query", ""),
                query_type=result.query_understanding.get("query_type", ""),
                entities=result.query_understanding.get("entities", []),
                keywords=result.query_understanding.get("keywords", []),
                concepts=result.query_understanding.get("concepts", [])
            ),
            results=[
                SearchResultItem(
                    id=r.get("id", ""),
                    title=r.get("metadata", {}).get("title", "") or r.get("title", ""),
                    content=r.get("content", "")[:500],  # 限制内容长度
                    score=r.get("score", 0.0),
                    metadata=r.get("metadata", {})
                )
                for r in result.results
            ],
            related_queries=result.related_queries,
            recommendations=result.recommendations,
            facets=result.facets,
            search_stats=result.search_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能搜索失败: {str(e)}")


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="搜索查询前缀", min_length=1),
    limit: int = Query(5, description="建议数量", ge=1, le=10)
):
    """
    获取搜索建议
    
    基于查询前缀提供智能搜索建议
    
    Args:
        query: 搜索查询前缀
        limit: 返回建议数量
        
    Returns:
        搜索建议列表
    """
    try:
        suggestions = intelligent_search_service.semantic_search_service.get_search_suggestions(
            query=query,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")


@router.post("/analyze", response_model=SearchAnalyticsResponse)
async def analyze_search(request: IntelligentSearchRequest):
    """
    分析搜索查询
    
    提供搜索查询的深度分析，包括查询理解、性能分析等
    
    Args:
        request: 搜索请求
        
    Returns:
        搜索分析结果
    """
    try:
        # 构建搜索上下文
        context = None
        if request.context:
            context = SearchContext(
                user_id=request.context.user_id,
                knowledge_base_id=request.context.knowledge_base_id,
                previous_queries=request.context.previous_queries,
                user_preferences=request.context.user_preferences
            )
        
        # 执行智能搜索
        result = intelligent_search_service.intelligent_search(
            query=request.query,
            context=context,
            n_results=request.n_results,
            filters=request.filters
        )
        
        # 获取分析数据
        analytics = intelligent_search_service.get_search_analytics(
            query=request.query,
            results=result
        )
        
        return SearchAnalyticsResponse(
            success=True,
            **analytics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索分析失败: {str(e)}")


@router.get("/intents")
async def get_search_intents():
    """
    获取支持的搜索意图类型
    
    Returns:
        搜索意图类型列表
    """
    intents = [
        {"value": intent.value, "label": intent.name, "description": _get_intent_description(intent)}
        for intent in SearchIntent
    ]
    
    return {
        "success": True,
        "intents": intents
    }


def _get_intent_description(intent: SearchIntent) -> str:
    """获取搜索意图描述"""
    descriptions = {
        SearchIntent.INFORMATIONAL: "信息查询意图，用户想要获取特定信息",
        SearchIntent.NAVIGATIONAL: "导航意图，用户想要找到特定页面或文档",
        SearchIntent.TRANSACTIONAL: "事务意图，用户想要执行某个操作",
        SearchIntent.EXPLORATORY: "探索意图，用户想要浏览和发现内容",
        SearchIntent.COMPARATIVE: "比较意图，用户想要比较不同选项"
    }
    return descriptions.get(intent, "未知意图")
