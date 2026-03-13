"""
一体化检索服务 - 向量化管理模块优化

整合向量、实体、图谱三种检索方式，实现统一的检索接口。
支持RRF融合算法和加权融合算法。

任务编号: BE-011
阶段: Phase 3 - 一体化建设期
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np

from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.core.database import get_db_pool
from app.modules.knowledge.models.unified_knowledge_unit import (
    UnifiedKnowledgeUnit,
    KnowledgeUnitAssociation,
    KnowledgeUnitType,
    AssociationType
)
from app.modules.knowledge.models.knowledge_document import (
    DocumentEntity,
    EntityRelationship,
    DocumentChunk
)
from app.services.knowledge.vectorization.chroma_service import ChromaService
from app.services.knowledge.retrieval.cached_retrieval_service import CachedRetrievalService

logger = logging.getLogger(__name__)


class RetrievalType(Enum):
    """检索类型"""
    VECTOR = "vector"           # 向量检索
    ENTITY = "entity"           # 实体检索
    GRAPH = "graph"             # 图谱检索
    HYBRID = "hybrid"           # 混合检索


class FusionAlgorithm(Enum):
    """融合算法"""
    RRF = "rrf"                 # Reciprocal Rank Fusion
    WEIGHTED = "weighted"       # 加权融合
    LINEAR = "linear"           # 线性融合


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    content: str
    score: float
    source_type: RetrievalType
    metadata: Dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    knowledge_base_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "source_type": self.source_type.value,
            "metadata": self.metadata,
            "title": self.title,
            "knowledge_base_id": self.knowledge_base_id
        }


@dataclass
class UnifiedSearchRequest:
    """统一搜索请求"""
    query: str
    retrieval_types: List[RetrievalType] = field(default_factory=lambda: [RetrievalType.VECTOR])
    fusion_algorithm: FusionAlgorithm = FusionAlgorithm.RRF
    top_k: int = 10
    knowledge_base_id: Optional[int] = None
    
    # 权重配置（用于加权融合）
    vector_weight: float = 0.5
    entity_weight: float = 0.3
    graph_weight: float = 0.2
    
    # RRF参数
    rrf_k: int = 60
    
    # 过滤条件
    filters: Dict[str, Any] = field(default_factory=dict)
    entity_types: Optional[List[str]] = None
    relationship_types: Optional[List[str]] = None
    
    def __post_init__(self):
        """验证权重"""
        total_weight = self.vector_weight + self.entity_weight + self.graph_weight
        if abs(total_weight - 1.0) > 0.001:
            # 归一化权重
            self.vector_weight /= total_weight
            self.entity_weight /= total_weight
            self.graph_weight /= total_weight


@dataclass
class UnifiedSearchResponse:
    """统一搜索响应"""
    query: str
    results: List[SearchResult]
    total_results: int
    fusion_algorithm: FusionAlgorithm
    retrieval_types: List[RetrievalType]
    
    # 各检索类型的原始结果数
    source_stats: Dict[str, int] = field(default_factory=dict)
    
    # 处理时间
    processing_time_ms: int = 0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total_results": self.total_results,
            "fusion_algorithm": self.fusion_algorithm.value,
            "retrieval_types": [t.value for t in self.retrieval_types],
            "source_stats": self.source_stats,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata
        }


class VectorRetrievalEngine:
    """向量检索引擎"""
    
    def __init__(self):
        self.chroma_service = ChromaService()
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        knowledge_base_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        执行向量检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            knowledge_base_id: 知识库ID过滤
            filters: 其他过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            # 构建过滤条件
            where_filter = {}
            if knowledge_base_id:
                where_filter["knowledge_base_id"] = knowledge_base_id
            if filters:
                where_filter.update(filters)
            
            # 执行向量搜索
            results = self.chroma_service.search_similar(
                query=query,
                n_results=top_k * 2,  # 获取更多用于融合
                where_filter=where_filter if where_filter else None
            )
            
            # 格式化结果
            search_results = []
            if results and results.get('ids') and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    score = 1 - results['distances'][0][i] if 'distances' in results else 0.5
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    
                    search_results.append(SearchResult(
                        id=str(doc_id),
                        content=results['documents'][0][i] if results.get('documents') else "",
                        score=score,
                        source_type=RetrievalType.VECTOR,
                        metadata=metadata,
                        title=metadata.get('title', '无标题'),
                        knowledge_base_id=metadata.get('knowledge_base_id')
                    ))
            
            logger.info(f"向量检索完成: {len(search_results)} 个结果")
            return search_results
            
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []


class EntityRetrievalEngine:
    """实体检索引擎"""
    
    def __init__(self):
        self.db_pool = get_db_pool()
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        knowledge_base_id: Optional[int] = None,
        entity_types: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        执行实体检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            knowledge_base_id: 知识库ID过滤
            entity_types: 实体类型过滤
            
        Returns:
            搜索结果列表
        """
        try:
            with self.db_pool.get_db_session() as db:
                # 构建查询
                query_filter = or_(
                    DocumentEntity.entity_text.ilike(f"%{query}%"),
                    DocumentEntity.entity_type.ilike(f"%{query}%")
                )
                
                # 添加知识库过滤
                if knowledge_base_id:
                    query_filter = and_(
                        query_filter,
                        DocumentEntity.document.has(knowledge_base_id=knowledge_base_id)
                    )
                
                # 添加实体类型过滤
                if entity_types:
                    query_filter = and_(
                        query_filter,
                        DocumentEntity.entity_type.in_(entity_types)
                    )
                
                # 执行查询
                entities = db.query(DocumentEntity).filter(query_filter).limit(top_k * 2).all()
                
                # 格式化结果
                search_results = []
                for entity in entities:
                    # 计算相似度分数（简单匹配）
                    score = self._calculate_entity_score(query, entity)
                    
                    search_results.append(SearchResult(
                        id=f"entity_{entity.id}",
                        content=entity.entity_text,
                        score=score,
                        source_type=RetrievalType.ENTITY,
                        metadata={
                            "entity_type": entity.entity_type,
                            "confidence": entity.confidence,
                            "document_id": entity.document_id,
                            "start_pos": entity.start_pos,
                            "end_pos": entity.end_pos
                        },
                        title=f"实体: {entity.entity_text}",
                        knowledge_base_id=knowledge_base_id
                    ))
                
                # 按分数排序
                search_results.sort(key=lambda x: x.score, reverse=True)
                
                logger.info(f"实体检索完成: {len(search_results)} 个结果")
                return search_results[:top_k]
                
        except Exception as e:
            logger.error(f"实体检索失败: {e}")
            return []
    
    def _calculate_entity_score(self, query: str, entity: DocumentEntity) -> float:
        """计算实体匹配分数"""
        query_lower = query.lower()
        entity_text_lower = entity.entity_text.lower()
        
        # 精确匹配
        if query_lower == entity_text_lower:
            return 1.0
        
        # 包含匹配
        if query_lower in entity_text_lower:
            return 0.8
        
        # 部分匹配
        query_words = set(query_lower.split())
        entity_words = set(entity_text_lower.split())
        if query_words & entity_words:
            overlap = len(query_words & entity_words) / len(query_words)
            return 0.5 + overlap * 0.3
        
        # 基础分数（基于置信度）
        return entity.confidence * 0.3


class GraphRetrievalEngine:
    """图谱检索引擎"""
    
    def __init__(self):
        self.db_pool = get_db_pool()
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        knowledge_base_id: Optional[int] = None,
        relationship_types: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        执行图谱检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            knowledge_base_id: 知识库ID过滤
            relationship_types: 关系类型过滤
            
        Returns:
            搜索结果列表
        """
        try:
            with self.db_pool.get_db_session() as db:
                # 1. 先找到匹配的实体
                entity_filter = or_(
                    DocumentEntity.entity_text.ilike(f"%{query}%"),
                    DocumentEntity.entity_type.ilike(f"%{query}%")
                )
                
                if knowledge_base_id:
                    entity_filter = and_(
                        entity_filter,
                        DocumentEntity.document.has(knowledge_base_id=knowledge_base_id)
                    )
                
                matching_entities = db.query(DocumentEntity).filter(entity_filter).all()
                entity_ids = [e.id for e in matching_entities]
                
                if not entity_ids:
                    logger.info("图谱检索: 未找到匹配实体")
                    return []
                
                # 2. 查找与这些实体相关的关系
                rel_filter = or_(
                    EntityRelationship.source_id.in_(entity_ids),
                    EntityRelationship.target_id.in_(entity_ids)
                )
                
                if relationship_types:
                    rel_filter = and_(
                        rel_filter,
                        EntityRelationship.relationship_type.in_(relationship_types)
                    )
                
                relationships = db.query(EntityRelationship).filter(rel_filter).limit(top_k * 2).all()
                
                # 3. 格式化结果
                search_results = []
                for rel in relationships:
                    # 获取源实体和目标实体
                    source = db.query(DocumentEntity).get(rel.source_id)
                    target = db.query(DocumentEntity).get(rel.target_id)
                    
                    if source and target:
                        # 构建关系描述
                        content = f"{source.entity_text} --[{rel.relationship_type}]--> {target.entity_text}"
                        
                        # 计算分数
                        score = rel.confidence * 0.8
                        
                        search_results.append(SearchResult(
                            id=f"rel_{rel.id}",
                            content=content,
                            score=score,
                            source_type=RetrievalType.GRAPH,
                            metadata={
                                "relationship_type": rel.relationship_type,
                                "confidence": rel.confidence,
                                "source_entity": source.entity_text,
                                "target_entity": target.entity_text,
                                "source_type": source.entity_type,
                                "target_type": target.entity_type,
                                "document_id": rel.document_id
                            },
                            title=f"关系: {rel.relationship_type}",
                            knowledge_base_id=knowledge_base_id
                        ))
                
                # 按分数排序
                search_results.sort(key=lambda x: x.score, reverse=True)
                
                logger.info(f"图谱检索完成: {len(search_results)} 个结果")
                return search_results[:top_k]
                
        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []
    
    def search_by_entity(
        self,
        entity_id: int,
        depth: int = 1,
        knowledge_base_id: Optional[int] = None
    ) -> List[SearchResult]:
        """
        基于实体的图谱搜索
        
        Args:
            entity_id: 实体ID
            depth: 搜索深度
            knowledge_base_id: 知识库ID过滤
            
        Returns:
            搜索结果列表
        """
        try:
            with self.db_pool.get_db_session() as db:
                # 获取直接关联的关系
                relationships = db.query(EntityRelationship).filter(
                    or_(
                        EntityRelationship.source_id == entity_id,
                        EntityRelationship.target_id == entity_id
                    )
                ).all()
                
                search_results = []
                for rel in relationships:
                    source = db.query(DocumentEntity).get(rel.source_id)
                    target = db.query(DocumentEntity).get(rel.target_id)
                    
                    if source and target:
                        content = f"{source.entity_text} --[{rel.relationship_type}]--> {target.entity_text}"
                        
                        search_results.append(SearchResult(
                            id=f"rel_{rel.id}",
                            content=content,
                            score=rel.confidence,
                            source_type=RetrievalType.GRAPH,
                            metadata={
                                "relationship_type": rel.relationship_type,
                                "source_entity": source.entity_text,
                                "target_entity": target.entity_text,
                                "is_source": rel.source_id == entity_id
                            },
                            title=f"关系: {rel.relationship_type}"
                        ))
                
                return search_results
                
        except Exception as e:
            logger.error(f"实体图谱检索失败: {e}")
            return []


class ResultFusionEngine:
    """结果融合引擎"""
    
    @staticmethod
    def rrf_fusion(
        results_lists: List[List[SearchResult]],
        k: int = 60,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        RRF (Reciprocal Rank Fusion) 融合算法
        
        公式: score = Σ(1 / (k + rank))
        
        Args:
            results_lists: 多个检索结果列表
            k: RRF常数，控制低排名项的权重
            top_k: 返回结果数量
            
        Returns:
            融合后的结果列表
        """
        # 收集所有结果及其排名
        rrf_scores: Dict[str, float] = {}
        result_map: Dict[str, SearchResult] = {}
        
        for results in results_lists:
            for rank, result in enumerate(results, start=1):
                result_id = result.id
                
                # 计算RRF分数
                rrf_score = 1.0 / (k + rank)
                
                if result_id in rrf_scores:
                    rrf_scores[result_id] += rrf_score
                else:
                    rrf_scores[result_id] = rrf_score
                    result_map[result_id] = result
        
        # 按RRF分数排序
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 构建最终结果
        fused_results = []
        for result_id, score in sorted_results[:top_k]:
            result = result_map[result_id]
            result.score = score  # 更新分数为RRF分数
            fused_results.append(result)
        
        logger.info(f"RRF融合完成: {len(fused_results)} 个结果")
        return fused_results
    
    @staticmethod
    def weighted_fusion(
        results_lists: List[List[SearchResult]],
        weights: List[float],
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        加权融合算法
        
        Args:
            results_lists: 多个检索结果列表
            weights: 各结果列表的权重
            top_k: 返回结果数量
            
        Returns:
            融合后的结果列表
        """
        if len(results_lists) != len(weights):
            raise ValueError("结果列表数量与权重数量不匹配")
        
        # 归一化权重
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # 收集所有结果
        weighted_scores: Dict[str, float] = {}
        result_map: Dict[str, SearchResult] = {}
        
        for results, weight in zip(results_lists, normalized_weights):
            for result in results:
                result_id = result.id
                weighted_score = result.score * weight
                
                if result_id in weighted_scores:
                    weighted_scores[result_id] += weighted_score
                else:
                    weighted_scores[result_id] = weighted_score
                    result_map[result_id] = result
        
        # 按加权分数排序
        sorted_results = sorted(
            weighted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 构建最终结果
        fused_results = []
        for result_id, score in sorted_results[:top_k]:
            result = result_map[result_id]
            result.score = score  # 更新分数
            fused_results.append(result)
        
        logger.info(f"加权融合完成: {len(fused_results)} 个结果")
        return fused_results
    
    @staticmethod
    def linear_fusion(
        results_lists: List[List[SearchResult]],
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        线性融合算法（简单取并集后排序）
        
        Args:
            results_lists: 多个检索结果列表
            top_k: 返回结果数量
            
        Returns:
            融合后的结果列表
        """
        # 合并所有结果
        all_results: Dict[str, SearchResult] = {}
        
        for results in results_lists:
            for result in results:
                result_id = result.id
                
                if result_id in all_results:
                    # 保留分数较高的结果
                    if result.score > all_results[result_id].score:
                        all_results[result_id] = result
                else:
                    all_results[result_id] = result
        
        # 按分数排序
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        logger.info(f"线性融合完成: {len(sorted_results)} 个结果")
        return sorted_results[:top_k]


class UnifiedRetrievalService:
    """
    一体化检索服务
    
    整合向量、实体、图谱三种检索方式，提供统一的检索接口。
    支持多种融合算法：RRF、加权融合、线性融合。
    
    特性：
    - 统一检索接口
    - 多源结果融合
    - 灵活的权重配置
    - 异步并行检索
    """
    
    def __init__(self):
        """初始化一体化检索服务"""
        self.vector_engine = VectorRetrievalEngine()
        self.entity_engine = EntityRetrievalEngine()
        self.graph_engine = GraphRetrievalEngine()
        self.fusion_engine = ResultFusionEngine()
        
        logger.info("一体化检索服务初始化完成")
    
    def search(self, request: UnifiedSearchRequest) -> UnifiedSearchResponse:
        """
        执行统一检索
        
        Args:
            request: 搜索请求
            
        Returns:
            搜索响应
        """
        start_time = datetime.now()
        
        # 执行各类型检索
        results_by_type: Dict[RetrievalType, List[SearchResult]] = {}
        
        for retrieval_type in request.retrieval_types:
            if retrieval_type == RetrievalType.VECTOR:
                results = self.vector_engine.search(
                    query=request.query,
                    top_k=request.top_k,
                    knowledge_base_id=request.knowledge_base_id,
                    filters=request.filters
                )
                results_by_type[RetrievalType.VECTOR] = results
                
            elif retrieval_type == RetrievalType.ENTITY:
                results = self.entity_engine.search(
                    query=request.query,
                    top_k=request.top_k,
                    knowledge_base_id=request.knowledge_base_id,
                    entity_types=request.entity_types
                )
                results_by_type[RetrievalType.ENTITY] = results
                
            elif retrieval_type == RetrievalType.GRAPH:
                results = self.graph_engine.search(
                    query=request.query,
                    top_k=request.top_k,
                    knowledge_base_id=request.knowledge_base_id,
                    relationship_types=request.relationship_types
                )
                results_by_type[RetrievalType.GRAPH] = results
        
        # 融合结果
        fused_results = self._fuse_results(request, results_by_type)
        
        # 计算处理时间
        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        # 统计各源结果数
        source_stats = {
            rt.value: len(results) for rt, results in results_by_type.items()
        }
        
        return UnifiedSearchResponse(
            query=request.query,
            results=fused_results[:request.top_k],
            total_results=len(fused_results),
            fusion_algorithm=request.fusion_algorithm,
            retrieval_types=request.retrieval_types,
            source_stats=source_stats,
            processing_time_ms=processing_time,
            metadata={
                "fusion_params": {
                    "rrf_k": request.rrf_k if request.fusion_algorithm == FusionAlgorithm.RRF else None,
                    "weights": {
                        "vector": request.vector_weight,
                        "entity": request.entity_weight,
                        "graph": request.graph_weight
                    } if request.fusion_algorithm == FusionAlgorithm.WEIGHTED else None
                }
            }
        )
    
    async def search_async(self, request: UnifiedSearchRequest) -> UnifiedSearchResponse:
        """
        异步执行统一检索
        
        Args:
            request: 搜索请求
            
        Returns:
            搜索响应
        """
        start_time = datetime.now()
        
        # 并行执行各类型检索
        tasks = []
        retrieval_types = []
        
        for retrieval_type in request.retrieval_types:
            if retrieval_type == RetrievalType.VECTOR:
                task = asyncio.to_thread(
                    self.vector_engine.search,
                    request.query,
                    request.top_k,
                    request.knowledge_base_id,
                    request.filters
                )
                tasks.append(task)
                retrieval_types.append(RetrievalType.VECTOR)
                
            elif retrieval_type == RetrievalType.ENTITY:
                task = asyncio.to_thread(
                    self.entity_engine.search,
                    request.query,
                    request.top_k,
                    request.knowledge_base_id,
                    request.entity_types
                )
                tasks.append(task)
                retrieval_types.append(RetrievalType.ENTITY)
                
            elif retrieval_type == RetrievalType.GRAPH:
                task = asyncio.to_thread(
                    self.graph_engine.search,
                    request.query,
                    request.top_k,
                    request.knowledge_base_id,
                    request.relationship_types
                )
                tasks.append(task)
                retrieval_types.append(RetrievalType.GRAPH)
        
        # 等待所有任务完成
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集结果
        results_by_type: Dict[RetrievalType, List[SearchResult]] = {}
        for rt, results in zip(retrieval_types, results_list):
            if isinstance(results, Exception):
                logger.error(f"{rt.value} 检索失败: {results}")
                results_by_type[rt] = []
            else:
                results_by_type[rt] = results
        
        # 融合结果
        fused_results = self._fuse_results(request, results_by_type)
        
        # 计算处理时间
        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        # 统计各源结果数
        source_stats = {
            rt.value: len(results) for rt, results in results_by_type.items()
        }
        
        return UnifiedSearchResponse(
            query=request.query,
            results=fused_results[:request.top_k],
            total_results=len(fused_results),
            fusion_algorithm=request.fusion_algorithm,
            retrieval_types=request.retrieval_types,
            source_stats=source_stats,
            processing_time_ms=processing_time
        )
    
    def _fuse_results(
        self,
        request: UnifiedSearchRequest,
        results_by_type: Dict[RetrievalType, List[SearchResult]]
    ) -> List[SearchResult]:
        """
        融合各类型检索结果
        
        Args:
            request: 搜索请求
            results_by_type: 各类型检索结果
            
        Returns:
            融合后的结果列表
        """
        results_lists = list(results_by_type.values())
        
        if len(results_lists) == 0:
            return []
        
        if len(results_lists) == 1:
            return results_lists[0]
        
        # 根据融合算法选择融合方法
        if request.fusion_algorithm == FusionAlgorithm.RRF:
            return self.fusion_engine.rrf_fusion(
                results_lists,
                k=request.rrf_k,
                top_k=request.top_k
            )
        
        elif request.fusion_algorithm == FusionAlgorithm.WEIGHTED:
            # 构建权重列表
            weights = []
            for rt in results_by_type.keys():
                if rt == RetrievalType.VECTOR:
                    weights.append(request.vector_weight)
                elif rt == RetrievalType.ENTITY:
                    weights.append(request.entity_weight)
                elif rt == RetrievalType.GRAPH:
                    weights.append(request.graph_weight)
            
            return self.fusion_engine.weighted_fusion(
                results_lists,
                weights=weights,
                top_k=request.top_k
            )
        
        elif request.fusion_algorithm == FusionAlgorithm.LINEAR:
            return self.fusion_engine.linear_fusion(
                results_lists,
                top_k=request.top_k
            )
        
        else:
            # 默认使用RRF
            return self.fusion_engine.rrf_fusion(results_lists, top_k=request.top_k)
    
    def vector_search(
        self,
        query: str,
        top_k: int = 10,
        knowledge_base_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量检索便捷方法"""
        return self.vector_engine.search(query, top_k, knowledge_base_id, filters)
    
    def entity_search(
        self,
        query: str,
        top_k: int = 10,
        knowledge_base_id: Optional[int] = None,
        entity_types: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """实体检索便捷方法"""
        return self.entity_engine.search(query, top_k, knowledge_base_id, entity_types)
    
    def graph_search(
        self,
        query: str,
        top_k: int = 10,
        knowledge_base_id: Optional[int] = None,
        relationship_types: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """图谱检索便捷方法"""
        return self.graph_engine.search(query, top_k, knowledge_base_id, relationship_types)
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        knowledge_base_id: Optional[int] = None,
        use_rrf: bool = True
    ) -> UnifiedSearchResponse:
        """
        混合检索便捷方法（向量+实体+图谱）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            knowledge_base_id: 知识库ID
            use_rrf: 是否使用RRF融合
            
        Returns:
            搜索响应
        """
        request = UnifiedSearchRequest(
            query=query,
            retrieval_types=[
                RetrievalType.VECTOR,
                RetrievalType.ENTITY,
                RetrievalType.GRAPH
            ],
            fusion_algorithm=FusionAlgorithm.RRF if use_rrf else FusionAlgorithm.WEIGHTED,
            top_k=top_k,
            knowledge_base_id=knowledge_base_id
        )
        
        return self.search(request)


# 便捷函数

def unified_search(
    query: str,
    retrieval_types: List[str] = None,
    top_k: int = 10,
    knowledge_base_id: Optional[int] = None,
    fusion_algorithm: str = "rrf"
) -> Dict[str, Any]:
    """
    统一检索便捷函数
    
    Args:
        query: 查询文本
        retrieval_types: 检索类型列表 ["vector", "entity", "graph"]
        top_k: 返回结果数量
        knowledge_base_id: 知识库ID
        fusion_algorithm: 融合算法 ["rrf", "weighted", "linear"]
        
    Returns:
        搜索结果字典
    """
    # 解析检索类型
    r_types = []
    if retrieval_types:
        for rt in retrieval_types:
            try:
                r_types.append(RetrievalType(rt))
            except ValueError:
                logger.warning(f"未知的检索类型: {rt}")
    else:
        r_types = [RetrievalType.VECTOR]
    
    # 解析融合算法
    try:
        fusion = FusionAlgorithm(fusion_algorithm)
    except ValueError:
        fusion = FusionAlgorithm.RRF
    
    # 构建请求
    request = UnifiedSearchRequest(
        query=query,
        retrieval_types=r_types,
        fusion_algorithm=fusion,
        top_k=top_k,
        knowledge_base_id=knowledge_base_id
    )
    
    # 执行搜索
    service = UnifiedRetrievalService()
    response = service.search(request)
    
    return response.to_dict()


# 全局服务实例
unified_retrieval_service = UnifiedRetrievalService()
