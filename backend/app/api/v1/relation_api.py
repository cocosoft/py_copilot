"""
关系管理增强API

提供关系权重计算、自动发现、可视化数据生成接口

任务编号: Phase3-Week11
阶段: 第三阶段 - 功能不完善问题优化
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.services.knowledge.relation_management_service import (
    RelationManagementService,
    EntityNode,
    RelationEdge,
    WeightConfig,
    get_relation_management_service
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/relations", tags=["关系管理"])


class EntityNodeRequest(BaseModel):
    """实体节点请求"""
    id: str
    name: str
    entity_type: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    attributes: Optional[Dict[str, Any]] = Field(default=None)


class RelationEdgeRequest(BaseModel):
    """关系边请求"""
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    evidence: Optional[List[str]] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class WeightConfigRequest(BaseModel):
    """权重配置请求"""
    frequency_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    confidence_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    recency_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    source_quality_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    context_relevance_weight: float = Field(default=0.15, ge=0.0, le=1.0)


class AnalyzeRequest(BaseModel):
    """分析请求"""
    entities: List[EntityNodeRequest]
    relations: List[RelationEdgeRequest]
    context: Optional[Dict[str, Any]] = Field(default=None)


class DiscoverRequest(BaseModel):
    """发现请求"""
    text: str = Field(..., description="待分析文本")
    existing_entities: Optional[List[EntityNodeRequest]] = Field(default=None)


class VisualizeRequest(BaseModel):
    """可视化请求"""
    entities: List[EntityNodeRequest]
    relations: List[RelationEdgeRequest]
    viz_type: str = Field(default="graph", description="可视化类型: graph, tree, matrix")
    options: Optional[Dict[str, Any]] = Field(default=None)


class EntityResponse(BaseModel):
    """实体响应"""
    id: str
    name: str
    entity_type: str
    weight: float
    attributes: Dict[str, Any]


class RelationResponse(BaseModel):
    """关系响应"""
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: float
    confidence: float
    evidence: List[str]
    metadata: Dict[str, Any]


class AnalysisResponse(BaseModel):
    """分析响应"""
    weights: Dict[str, float]
    statistics: Dict[str, Any]
    top_relations: List[Dict[str, Any]]


class DiscoverResponse(BaseModel):
    """发现响应"""
    entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    entity_count: int
    relation_count: int


class VisualizeResponse(BaseModel):
    """可视化响应"""
    viz_type: str
    data: Dict[str, Any]


def get_service() -> RelationManagementService:
    """获取关系管理服务依赖"""
    return get_relation_management_service()


def convert_to_entity_node(req: EntityNodeRequest) -> EntityNode:
    """转换请求为实体节点"""
    return EntityNode(
        id=req.id,
        name=req.name,
        entity_type=req.entity_type,
        weight=req.weight,
        attributes=req.attributes or {}
    )


def convert_to_relation_edge(req: RelationEdgeRequest) -> RelationEdge:
    """转换请求为关系边"""
    return RelationEdge(
        id=req.id,
        source_id=req.source_id,
        target_id=req.target_id,
        relation_type=req.relation_type,
        weight=req.weight,
        confidence=req.confidence,
        evidence=req.evidence or [],
        metadata=req.metadata or {}
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_relations(
    request: AnalyzeRequest,
    service: RelationManagementService = Depends(get_service)
):
    """
    分析关系
    
    计算关系权重并生成统计信息
    """
    try:
        entities = [convert_to_entity_node(e) for e in request.entities]
        relations = [convert_to_relation_edge(r) for r in request.relations]
        
        result = service.analyze_relations(entities, relations, request.context)
        
        return AnalysisResponse(**result)
    except Exception as e:
        logger.error(f"分析关系失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/discover", response_model=DiscoverResponse)
async def discover_relations(
    request: DiscoverRequest,
    service: RelationManagementService = Depends(get_service)
):
    """
    发现实体和关系
    
    从文本中自动发现实体和关系
    """
    try:
        existing_entities = None
        if request.existing_entities:
            existing_entities = [convert_to_entity_node(e) for e in request.existing_entities]
        
        result = service.discover_from_text(request.text, existing_entities)
        
        return DiscoverResponse(**result)
    except Exception as e:
        logger.error(f"发现关系失败: {e}")
        raise HTTPException(status_code=500, detail=f"发现失败: {str(e)}")


@router.post("/visualize", response_model=VisualizeResponse)
async def generate_visualization(
    request: VisualizeRequest,
    service: RelationManagementService = Depends(get_service)
):
    """
    生成可视化数据
    
    生成图、树或矩阵可视化数据
    """
    try:
        entities = [convert_to_entity_node(e) for e in request.entities]
        relations = [convert_to_relation_edge(r) for r in request.relations]
        
        data = service.generate_visualization(
            entities, relations, 
            request.viz_type, 
            request.options
        )
        
        return VisualizeResponse(
            viz_type=request.viz_type,
            data=data
        )
    except Exception as e:
        logger.error(f"生成可视化数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/weight/calculate")
async def calculate_weight(
    relation: RelationEdgeRequest,
    context: Optional[Dict[str, Any]] = None,
    service: RelationManagementService = Depends(get_service)
):
    """
    计算单个关系权重
    
    根据多个因子计算关系权重
    """
    try:
        rel = convert_to_relation_edge(relation)
        weight = service.weight_calculator.calculate_weight(rel, context)
        
        return {
            "relation_id": relation.id,
            "weight": weight,
            "factors": {
                "frequency": service.weight_calculator._calculate_frequency_score(rel),
                "confidence": rel.confidence,
                "recency": service.weight_calculator._calculate_recency_score(rel),
                "source_quality": service.weight_calculator._calculate_source_quality_score(rel)
            }
        }
    except Exception as e:
        logger.error(f"计算权重失败: {e}")
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/weight/batch")
async def batch_calculate_weights(
    relations: List[RelationEdgeRequest],
    context: Optional[Dict[str, Any]] = None,
    service: RelationManagementService = Depends(get_service)
):
    """
    批量计算关系权重
    
    批量计算多个关系的权重
    """
    try:
        rels = [convert_to_relation_edge(r) for r in relations]
        weights = service.weight_calculator.batch_calculate_weights(rels, context)
        
        return {
            "weights": weights,
            "count": len(weights)
        }
    except Exception as e:
        logger.error(f"批量计算权重失败: {e}")
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/patterns")
async def get_relation_patterns(
    service: RelationManagementService = Depends(get_service)
):
    """
    获取关系模式
    
    返回所有可用的关系发现模式
    """
    return {
        "patterns": service.discovery.patterns,
        "entity_patterns": service.discovery.entity_patterns
    }


@router.get("/statistics")
async def get_statistics_info():
    """
    获取统计信息说明
    
    返回统计指标的含义说明
    """
    return {
        "metrics": {
            "entity_count": "实体数量",
            "relation_count": "关系数量",
            "average_degree": "平均度（每个实体平均连接的关系数）",
            "average_weight": "平均权重",
            "relation_types": "各类型关系数量分布",
            "max_degree": "最大度（最活跃实体）",
            "min_degree": "最小度"
        },
        "weight_factors": {
            "frequency": "频率因子 - 基于证据数量",
            "confidence": "置信度因子 - 提取时的置信度",
            "recency": "时效性因子 - 基于创建时间",
            "source_quality": "来源质量因子 - 基于数据来源",
            "context_relevance": "上下文相关性因子 - 基于查询上下文"
        }
    }
