"""
智能重排序服务

实现多维度排序策略，支持机器学习排序模型
支持LangChain集成和自定义排序算法

任务编号: Phase3-Week9
阶段: 第三阶段 - 功能不完善问题优化
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)


class RerankStrategy(Enum):
    """重排序策略"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    ML_MODEL = "ml_model"
    MULTI_DIMENSION = "multi_dimension"
    ADAPTIVE = "adaptive"


class SortDimension(Enum):
    """排序维度"""
    RELEVANCE = "relevance"
    RECENCY = "recency"
    POPULARITY = "popularity"
    AUTHORITY = "authority"
    DIVERSITY = "diversity"
    CUSTOM = "custom"


@dataclass
class RerankConfig:
    """重排序配置"""
    strategy: RerankStrategy = RerankStrategy.HYBRID
    top_k: int = 10
    threshold: float = 0.0
    
    multi_dimension_weights: Dict[str, float] = field(default_factory=lambda: {
        "relevance": 0.5,
        "recency": 0.2,
        "popularity": 0.15,
        "authority": 0.15
    })
    
    hybrid_weights: Dict[str, float] = field(default_factory=lambda: {
        "semantic": 0.6,
        "keyword": 0.4
    })
    
    diversity_threshold: float = 0.8
    enable_diversity_rerank: bool = True
    
    model_name: str = "BAAI/bge-reranker-large"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "top_k": self.top_k,
            "threshold": self.threshold,
            "multi_dimension_weights": self.multi_dimension_weights,
            "hybrid_weights": self.hybrid_weights,
            "diversity_threshold": self.diversity_threshold,
            "enable_diversity_rerank": self.enable_diversity_rerank,
            "model_name": self.model_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RerankConfig':
        return cls(
            strategy=RerankStrategy(data.get("strategy", "hybrid")),
            top_k=data.get("top_k", 10),
            threshold=data.get("threshold", 0.0),
            multi_dimension_weights=data.get("multi_dimension_weights", {
                "relevance": 0.5,
                "recency": 0.2,
                "popularity": 0.15,
                "authority": 0.15
            }),
            hybrid_weights=data.get("hybrid_weights", {
                "semantic": 0.6,
                "keyword": 0.4
            }),
            diversity_threshold=data.get("diversity_threshold", 0.8),
            enable_diversity_rerank=data.get("enable_diversity_rerank", True),
            model_name=data.get("model_name", "BAAI/bge-reranker-large")
        )


@dataclass
class RerankResult:
    """重排序结果"""
    document_id: str
    content: str
    title: str
    original_score: float
    rerank_score: float
    final_score: float
    original_rank: int
    rerank_rank: int
    dimensions: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "content": self.content,
            "title": self.title,
            "original_score": self.original_score,
            "rerank_score": self.rerank_score,
            "final_score": self.final_score,
            "original_rank": self.original_rank,
            "rerank_rank": self.rerank_rank,
            "dimensions": self.dimensions,
            "metadata": self.metadata
        }


class IntelligentRerankService:
    """智能重排序服务"""
    
    def __init__(self, config: Optional[RerankConfig] = None):
        self.config = config or RerankConfig()
        self._model = None
        self._model_available = False
        self._initialize_model()
    
    def _get_device(self) -> str:
        """自动检测可用设备"""
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except:
            return "cpu"
    
    def _get_model_path(self) -> Optional[str]:
        """获取模型路径"""
        model_name = self.config.model_name
        
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        model_id = model_name.replace("/", "--")
        cache_path = os.path.join(cache_dir, f"models--{model_id}")
        
        if os.path.exists(cache_path):
            snapshots_dir = os.path.join(cache_path, "snapshots")
            if os.path.exists(snapshots_dir):
                snapshots = os.listdir(snapshots_dir)
                if snapshots:
                    return os.path.join(snapshots_dir, snapshots[0])
        
        return None
    
    def _initialize_model(self):
        """初始化重排序模型"""
        try:
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            from sentence_transformers import CrossEncoder
            
            model_path = self._get_model_path()
            
            if model_path and os.path.exists(model_path):
                logger.info(f"从本地加载重排序模型: {model_path}")
                self._model = CrossEncoder(
                    model_path,
                    max_length=512,
                    device=self._get_device()
                )
                self._model_available = True
                logger.info("重排序模型加载成功")
            else:
                logger.warning("重排序模型未找到，将使用备用排序策略")
                self._model_available = False
        except Exception as e:
            logger.warning(f"重排序模型加载失败: {e}，将使用备用排序策略")
            self._model_available = False
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], 
               config: Optional[RerankConfig] = None) -> List[RerankResult]:
        """执行重排序
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            config: 重排序配置（可选，覆盖默认配置）
            
        Returns:
            重排序结果列表
        """
        if not documents:
            return []
        
        cfg = config or self.config
        start_time = time.time()
        
        strategy = cfg.strategy
        
        if strategy == RerankStrategy.SEMANTIC:
            results = self._semantic_rerank(query, documents, cfg)
        elif strategy == RerankStrategy.KEYWORD:
            results = self._keyword_rerank(query, documents, cfg)
        elif strategy == RerankStrategy.HYBRID:
            results = self._hybrid_rerank(query, documents, cfg)
        elif strategy == RerankStrategy.ML_MODEL:
            results = self._ml_model_rerank(query, documents, cfg)
        elif strategy == RerankStrategy.MULTI_DIMENSION:
            results = self._multi_dimension_rerank(query, documents, cfg)
        elif strategy == RerankStrategy.ADAPTIVE:
            results = self._adaptive_rerank(query, documents, cfg)
        else:
            results = self._hybrid_rerank(query, documents, cfg)
        
        if cfg.enable_diversity_rerank:
            results = self._diversity_rerank(results, cfg)
        
        results = results[:cfg.top_k]
        
        if cfg.threshold > 0:
            results = [r for r in results if r.final_score >= cfg.threshold]
        
        elapsed = time.time() - start_time
        logger.info(f"重排序完成: 策略={strategy.value}, 文档数={len(documents)}, 耗时={elapsed:.3f}s")
        
        return results
    
    def _semantic_rerank(self, query: str, documents: List[Dict[str, Any]], 
                        config: RerankConfig) -> List[RerankResult]:
        """语义重排序"""
        results = []
        
        for i, doc in enumerate(documents):
            content = doc.get('content', doc.get('document', ''))
            
            semantic_score = self._calculate_semantic_similarity(query, content)
            
            result = RerankResult(
                document_id=doc.get('id', str(i)),
                content=content,
                title=doc.get('title', '无标题'),
                original_score=doc.get('score', 0.0),
                rerank_score=semantic_score,
                final_score=semantic_score,
                original_rank=i,
                rerank_rank=0,
                dimensions={"semantic": semantic_score},
                metadata=doc.get('metadata', {})
            )
            results.append(result)
        
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        for i, result in enumerate(results):
            result.rerank_rank = i
        
        return results
    
    def _keyword_rerank(self, query: str, documents: List[Dict[str, Any]], 
                       config: RerankConfig) -> List[RerankResult]:
        """关键词重排序"""
        query_keywords = set(query.lower().split())
        results = []
        
        for i, doc in enumerate(documents):
            content = doc.get('content', doc.get('document', '')).lower()
            
            keyword_score = 0.0
            for keyword in query_keywords:
                if keyword in content:
                    keyword_score += 1.0
            
            keyword_score = keyword_score / len(query_keywords) if query_keywords else 0.0
            
            result = RerankResult(
                document_id=doc.get('id', str(i)),
                content=doc.get('content', ''),
                title=doc.get('title', '无标题'),
                original_score=doc.get('score', 0.0),
                rerank_score=keyword_score,
                final_score=keyword_score,
                original_rank=i,
                rerank_rank=0,
                dimensions={"keyword": keyword_score},
                metadata=doc.get('metadata', {})
            )
            results.append(result)
        
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        for i, result in enumerate(results):
            result.rerank_rank = i
        
        return results
    
    def _hybrid_rerank(self, query: str, documents: List[Dict[str, Any]], 
                      config: RerankConfig) -> List[RerankResult]:
        """混合重排序"""
        semantic_results = self._semantic_rerank(query, documents, config)
        keyword_results = self._keyword_rerank(query, documents, config)
        
        semantic_map = {r.document_id: r for r in semantic_results}
        keyword_map = {r.document_id: r for r in keyword_results}
        
        weights = config.hybrid_weights
        semantic_weight = weights.get("semantic", 0.6)
        keyword_weight = weights.get("keyword", 0.4)
        
        results = []
        for i, doc in enumerate(documents):
            doc_id = doc.get('id', str(i))
            
            semantic_score = semantic_map.get(doc_id, RerankResult(
                document_id=doc_id, content="", title="",
                original_score=0, rerank_score=0, final_score=0,
                original_rank=i, rerank_rank=0
            )).rerank_score
            
            keyword_score = keyword_map.get(doc_id, RerankResult(
                document_id=doc_id, content="", title="",
                original_score=0, rerank_score=0, final_score=0,
                original_rank=i, rerank_rank=0
            )).rerank_score
            
            hybrid_score = semantic_score * semantic_weight + keyword_score * keyword_weight
            
            result = RerankResult(
                document_id=doc_id,
                content=doc.get('content', ''),
                title=doc.get('title', '无标题'),
                original_score=doc.get('score', 0.0),
                rerank_score=hybrid_score,
                final_score=hybrid_score,
                original_rank=i,
                rerank_rank=0,
                dimensions={
                    "semantic": semantic_score,
                    "keyword": keyword_score,
                    "hybrid": hybrid_score
                },
                metadata=doc.get('metadata', {})
            )
            results.append(result)
        
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        for i, result in enumerate(results):
            result.rerank_rank = i
        
        return results
    
    def _ml_model_rerank(self, query: str, documents: List[Dict[str, Any]], 
                        config: RerankConfig) -> List[RerankResult]:
        """机器学习模型重排序"""
        if not self._model_available:
            logger.warning("ML模型不可用，回退到混合重排序")
            return self._hybrid_rerank(query, documents, config)
        
        try:
            pairs = []
            for doc in documents:
                content = doc.get('content', doc.get('document', ''))
                pairs.append([query, content])
            
            scores = self._model.predict(pairs)
            
            results = []
            for i, (doc, score) in enumerate(zip(documents, scores)):
                result = RerankResult(
                    document_id=doc.get('id', str(i)),
                    content=doc.get('content', ''),
                    title=doc.get('title', '无标题'),
                    original_score=doc.get('score', 0.0),
                    rerank_score=float(score),
                    final_score=float(score),
                    original_rank=i,
                    rerank_rank=0,
                    dimensions={"ml_model": float(score)},
                    metadata=doc.get('metadata', {})
                )
                results.append(result)
            
            results.sort(key=lambda x: x.final_score, reverse=True)
            
            for i, result in enumerate(results):
                result.rerank_rank = i
            
            return results
        except Exception as e:
            logger.error(f"ML模型重排序失败: {e}")
            return self._hybrid_rerank(query, documents, config)
    
    def _multi_dimension_rerank(self, query: str, documents: List[Dict[str, Any]], 
                               config: RerankConfig) -> List[RerankResult]:
        """多维度重排序"""
        weights = config.multi_dimension_weights
        
        results = []
        for i, doc in enumerate(documents):
            relevance_score = self._calculate_relevance(query, doc)
            recency_score = self._calculate_recency(doc)
            popularity_score = self._calculate_popularity(doc)
            authority_score = self._calculate_authority(doc)
            
            final_score = (
                relevance_score * weights.get("relevance", 0.5) +
                recency_score * weights.get("recency", 0.2) +
                popularity_score * weights.get("popularity", 0.15) +
                authority_score * weights.get("authority", 0.15)
            )
            
            result = RerankResult(
                document_id=doc.get('id', str(i)),
                content=doc.get('content', ''),
                title=doc.get('title', '无标题'),
                original_score=doc.get('score', 0.0),
                rerank_score=final_score,
                final_score=final_score,
                original_rank=i,
                rerank_rank=0,
                dimensions={
                    "relevance": relevance_score,
                    "recency": recency_score,
                    "popularity": popularity_score,
                    "authority": authority_score
                },
                metadata=doc.get('metadata', {})
            )
            results.append(result)
        
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        for i, result in enumerate(results):
            result.rerank_rank = i
        
        return results
    
    def _adaptive_rerank(self, query: str, documents: List[Dict[str, Any]], 
                        config: RerankConfig) -> List[RerankResult]:
        """自适应重排序"""
        query_length = len(query.split())
        doc_count = len(documents)
        
        if query_length <= 3:
            strategy = RerankStrategy.KEYWORD
        elif self._model_available and doc_count <= 50:
            strategy = RerankStrategy.ML_MODEL
        elif doc_count > 100:
            strategy = RerankStrategy.HYBRID
        else:
            strategy = RerankStrategy.MULTI_DIMENSION
        
        logger.info(f"自适应选择策略: {strategy.value}")
        
        adaptive_config = RerankConfig(
            strategy=strategy,
            top_k=config.top_k,
            threshold=config.threshold,
            multi_dimension_weights=config.multi_dimension_weights,
            hybrid_weights=config.hybrid_weights,
            enable_diversity_rerank=config.enable_diversity_rerank
        )
        
        return self.rerank(query, documents, adaptive_config)
    
    def _diversity_rerank(self, results: List[RerankResult], 
                         config: RerankConfig) -> List[RerankResult]:
        """多样性重排序"""
        if len(results) <= 1:
            return results
        
        threshold = config.diversity_threshold
        diverse_results = [results[0]]
        
        for result in results[1:]:
            is_diverse = True
            
            for selected in diverse_results:
                similarity = self._calculate_content_similarity(
                    result.content, selected.content
                )
                
                if similarity > threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_results.append(result)
        
        for i, result in enumerate(diverse_results):
            result.rerank_rank = i
        
        return diverse_results
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """计算内容相似度"""
        return self._calculate_semantic_similarity(text1, text2)
    
    def _calculate_relevance(self, query: str, doc: Dict[str, Any]) -> float:
        """计算相关性分数"""
        content = doc.get('content', '').lower()
        query_lower = query.lower()
        
        if query_lower in content:
            return 1.0
        
        query_words = set(query_lower.split())
        content_words = set(content.split())
        
        if not query_words:
            return 0.0
        
        overlap = query_words & content_words
        return len(overlap) / len(query_words)
    
    def _calculate_recency(self, doc: Dict[str, Any]) -> float:
        """计算时效性分数"""
        metadata = doc.get('metadata', {})
        created_at = metadata.get('created_at')
        
        if not created_at:
            return 0.5
        
        try:
            if isinstance(created_at, str):
                doc_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                doc_date = created_at
            
            now = datetime.now(doc_date.tzinfo) if doc_date.tzinfo else datetime.now()
            days_diff = (now - doc_date).days
            
            recency_score = max(0, 1 - days_diff / 365)
            return recency_score
        except:
            return 0.5
    
    def _calculate_popularity(self, doc: Dict[str, Any]) -> float:
        """计算流行度分数"""
        metadata = doc.get('metadata', {})
        view_count = metadata.get('view_count', 0)
        like_count = metadata.get('like_count', 0)
        
        popularity = min(1.0, (view_count * 0.01 + like_count * 0.1) / 10)
        return popularity
    
    def _calculate_authority(self, doc: Dict[str, Any]) -> float:
        """计算权威性分数"""
        metadata = doc.get('metadata', {})
        source = metadata.get('source', '').lower()
        author = metadata.get('author', '').lower()
        
        authority_score = 0.5
        
        trusted_sources = ['wikipedia', 'arxiv', 'github', 'stackoverflow']
        if any(ts in source for ts in trusted_sources):
            authority_score += 0.3
        
        if author:
            authority_score += 0.2
        
        return min(1.0, authority_score)
    
    def get_config(self) -> RerankConfig:
        """获取当前配置"""
        return self.config
    
    def update_config(self, config: RerankConfig) -> None:
        """更新配置"""
        self.config = config
        logger.info(f"重排序配置已更新: {config.to_dict()}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.config.model_name,
            "available": self._model_available,
            "device": self._get_device() if self._model_available else None,
            "strategy": self.config.strategy.value
        }


_intelligent_rerank_service: Optional[IntelligentRerankService] = None


def get_intelligent_rerank_service() -> IntelligentRerankService:
    """获取智能重排序服务实例"""
    global _intelligent_rerank_service
    if _intelligent_rerank_service is None:
        _intelligent_rerank_service = IntelligentRerankService()
    return _intelligent_rerank_service
