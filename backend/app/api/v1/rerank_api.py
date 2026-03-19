"""
重排序配置API

提供重排序功能的配置和管理接口

任务编号: Phase3-Week9
阶段: 第三阶段 - 功能不完善问题优化
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.services.knowledge.intelligent_rerank_service import (
    IntelligentRerankService,
    RerankConfig,
    RerankStrategy,
    get_intelligent_rerank_service
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rerank", tags=["重排序管理"])


class RerankConfigRequest(BaseModel):
    """重排序配置请求"""
    strategy: str = Field(default="hybrid", description="重排序策略: semantic, keyword, hybrid, ml_model, multi_dimension, adaptive")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="分数阈值")
    multi_dimension_weights: Optional[Dict[str, float]] = Field(default=None, description="多维度权重")
    hybrid_weights: Optional[Dict[str, float]] = Field(default=None, description="混合权重")
    diversity_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="多样性阈值")
    enable_diversity_rerank: bool = Field(default=True, description="启用多样性重排序")
    model_name: str = Field(default="BAAI/bge-reranker-large", description="模型名称")


class RerankRequest(BaseModel):
    """重排序请求"""
    query: str = Field(..., description="查询文本")
    documents: List[Dict[str, Any]] = Field(..., description="待重排序的文档列表")
    config: Optional[RerankConfigRequest] = Field(default=None, description="重排序配置")


class RerankResponse(BaseModel):
    """重排序响应"""
    success: bool
    results: List[Dict[str, Any]]
    total: int
    strategy: str
    elapsed_ms: float


class RerankConfigResponse(BaseModel):
    """重排序配置响应"""
    strategy: str
    top_k: int
    threshold: float
    multi_dimension_weights: Dict[str, float]
    hybrid_weights: Dict[str, float]
    diversity_threshold: float
    enable_diversity_rerank: bool
    model_name: str


class ModelInfoResponse(BaseModel):
    """模型信息响应"""
    model_name: str
    available: bool
    device: Optional[str]
    strategy: str


class StrategyInfo(BaseModel):
    """策略信息"""
    name: str
    description: str
    use_case: str


def get_rerank_service() -> IntelligentRerankService:
    """获取重排序服务依赖"""
    return get_intelligent_rerank_service()


@router.get("/config", response_model=RerankConfigResponse)
async def get_rerank_config(
    service: IntelligentRerankService = Depends(get_rerank_service)
):
    """
    获取当前重排序配置
    
    返回当前的重排序策略和参数配置
    """
    try:
        config = service.get_config()
        return RerankConfigResponse(
            strategy=config.strategy.value,
            top_k=config.top_k,
            threshold=config.threshold,
            multi_dimension_weights=config.multi_dimension_weights,
            hybrid_weights=config.hybrid_weights,
            diversity_threshold=config.diversity_threshold,
            enable_diversity_rerank=config.enable_diversity_rerank,
            model_name=config.model_name
        )
    except Exception as e:
        logger.error(f"获取重排序配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/config", response_model=RerankConfigResponse)
async def update_rerank_config(
    request: RerankConfigRequest,
    service: IntelligentRerankService = Depends(get_rerank_service)
):
    """
    更新重排序配置
    
    更新重排序策略和参数配置
    """
    try:
        strategy_map = {
            "semantic": RerankStrategy.SEMANTIC,
            "keyword": RerankStrategy.KEYWORD,
            "hybrid": RerankStrategy.HYBRID,
            "ml_model": RerankStrategy.ML_MODEL,
            "multi_dimension": RerankStrategy.MULTI_DIMENSION,
            "adaptive": RerankStrategy.ADAPTIVE
        }
        
        strategy = strategy_map.get(request.strategy.lower())
        if not strategy:
            raise HTTPException(status_code=400, detail=f"无效的策略: {request.strategy}")
        
        config = RerankConfig(
            strategy=strategy,
            top_k=request.top_k,
            threshold=request.threshold,
            multi_dimension_weights=request.multi_dimension_weights or {
                "relevance": 0.5,
                "recency": 0.2,
                "popularity": 0.15,
                "authority": 0.15
            },
            hybrid_weights=request.hybrid_weights or {
                "semantic": 0.6,
                "keyword": 0.4
            },
            diversity_threshold=request.diversity_threshold,
            enable_diversity_rerank=request.enable_diversity_rerank,
            model_name=request.model_name
        )
        
        service.update_config(config)
        
        return RerankConfigResponse(
            strategy=config.strategy.value,
            top_k=config.top_k,
            threshold=config.threshold,
            multi_dimension_weights=config.multi_dimension_weights,
            hybrid_weights=config.hybrid_weights,
            diversity_threshold=config.diversity_threshold,
            enable_diversity_rerank=config.enable_diversity_rerank,
            model_name=config.model_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新重排序配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.post("/execute", response_model=RerankResponse)
async def execute_rerank(
    request: RerankRequest,
    service: IntelligentRerankService = Depends(get_rerank_service)
):
    """
    执行重排序
    
    对给定的文档列表进行重排序
    """
    import time
    
    try:
        start_time = time.time()
        
        config = None
        if request.config:
            strategy_map = {
                "semantic": RerankStrategy.SEMANTIC,
                "keyword": RerankStrategy.KEYWORD,
                "hybrid": RerankStrategy.HYBRID,
                "ml_model": RerankStrategy.ML_MODEL,
                "multi_dimension": RerankStrategy.MULTI_DIMENSION,
                "adaptive": RerankStrategy.ADAPTIVE
            }
            
            strategy = strategy_map.get(request.config.strategy.lower(), RerankStrategy.HYBRID)
            
            config = RerankConfig(
                strategy=strategy,
                top_k=request.config.top_k,
                threshold=request.config.threshold,
                multi_dimension_weights=request.config.multi_dimension_weights or {
                    "relevance": 0.5,
                    "recency": 0.2,
                    "popularity": 0.15,
                    "authority": 0.15
                },
                hybrid_weights=request.config.hybrid_weights or {
                    "semantic": 0.6,
                    "keyword": 0.4
                },
                diversity_threshold=request.config.diversity_threshold,
                enable_diversity_rerank=request.config.enable_diversity_rerank,
                model_name=request.config.model_name
            )
        
        results = service.rerank(request.query, request.documents, config)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return RerankResponse(
            success=True,
            results=[r.to_dict() for r in results],
            total=len(results),
            strategy=config.strategy.value if config else service.get_config().strategy.value,
            elapsed_ms=elapsed_ms
        )
    except Exception as e:
        logger.error(f"执行重排序失败: {e}")
        raise HTTPException(status_code=500, detail=f"重排序失败: {str(e)}")


@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info(
    service: IntelligentRerankService = Depends(get_rerank_service)
):
    """
    获取模型信息
    
    返回当前使用的重排序模型信息
    """
    try:
        info = service.get_model_info()
        return ModelInfoResponse(**info)
    except Exception as e:
        logger.error(f"获取模型信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")


@router.get("/strategies", response_model=List[StrategyInfo])
async def get_available_strategies():
    """
    获取可用的重排序策略
    
    返回所有可用的重排序策略及其说明
    """
    strategies = [
        StrategyInfo(
            name="semantic",
            description="语义重排序",
            use_case="基于语义相似度进行排序，适合精确匹配场景"
        ),
        StrategyInfo(
            name="keyword",
            description="关键词重排序",
            use_case="基于关键词匹配进行排序，适合快速检索场景"
        ),
        StrategyInfo(
            name="hybrid",
            description="混合重排序",
            use_case="结合语义和关键词进行排序，平衡精度和速度"
        ),
        StrategyInfo(
            name="ml_model",
            description="机器学习模型重排序",
            use_case="使用预训练模型进行重排序，精度最高但速度较慢"
        ),
        StrategyInfo(
            name="multi_dimension",
            description="多维度重排序",
            use_case="综合考虑相关性、时效性、流行度、权威性等多个维度"
        ),
        StrategyInfo(
            name="adaptive",
            description="自适应重排序",
            use_case="根据查询特征自动选择最优策略"
        )
    ]
    
    return strategies


@router.post("/compare")
async def compare_strategies(
    request: RerankRequest,
    service: IntelligentRerankService = Depends(get_rerank_service)
):
    """
    比较不同策略的重排序结果
    
    对同一组文档使用不同策略进行重排序，便于对比分析
    """
    import time
    
    try:
        strategies = ["semantic", "keyword", "hybrid", "multi_dimension"]
        comparison_results = {}
        
        for strategy_name in strategies:
            strategy_map = {
                "semantic": RerankStrategy.SEMANTIC,
                "keyword": RerankStrategy.KEYWORD,
                "hybrid": RerankStrategy.HYBRID,
                "multi_dimension": RerankStrategy.MULTI_DIMENSION
            }
            
            config = RerankConfig(
                strategy=strategy_map[strategy_name],
                top_k=request.config.top_k if request.config else 10,
                threshold=request.config.threshold if request.config else 0.0
            )
            
            start_time = time.time()
            results = service.rerank(request.query, request.documents, config)
            elapsed_ms = (time.time() - start_time) * 1000
            
            comparison_results[strategy_name] = {
                "results": [r.to_dict() for r in results[:5]],
                "total": len(results),
                "elapsed_ms": elapsed_ms
            }
        
        return {
            "success": True,
            "query": request.query,
            "document_count": len(request.documents),
            "comparison": comparison_results
        }
    except Exception as e:
        logger.error(f"策略比较失败: {e}")
        raise HTTPException(status_code=500, detail=f"策略比较失败: {str(e)}")
