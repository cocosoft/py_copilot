"""
重排序服务

实现多阶段重排序策略，包括语义、时效性、权威性、个性化重排序

@task DB-001
@phase 重排序功能实现
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import math


class SemanticReranker:
    """
    语义重排序器
    """
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        基于语义相似度进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            user_context: 用户上下文
            
        Returns:
            重排序后的文档列表
        """
        # 计算语义相似度分数
        for doc in documents:
            semantic_score = self._calculate_semantic_similarity(query, doc)
            doc['semantic_score'] = semantic_score
        
        # 按语义相似度排序
        return sorted(documents, key=lambda x: x.get('semantic_score', 0), reverse=True)
    
    def _calculate_semantic_similarity(self, query: str, document: Dict[str, Any]) -> float:
        """
        计算查询与文档的语义相似度
        """
        # 这里应该实现真实的语义相似度计算
        # 例如使用向量相似度
        return 0.5


class EntityAwareReranker:
    """
    基于实体匹配的重排序器
    """
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        基于实体匹配进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            user_context: 用户上下文
            
        Returns:
            重排序后的文档列表
        """
        # 提取查询中的实体
        query_entities = self._extract_entities(query)
        
        # 计算文档实体与查询实体的匹配度
        for doc in documents:
            doc_entities = self._get_document_entities(doc)
            entity_score = self._calculate_entity_match(query_entities, doc_entities)
            doc['entity_match_score'] = entity_score
        
        # 综合排序
        return sorted(documents, key=lambda x: x.get('entity_match_score', 0), reverse=True)
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        从文本中提取实体
        """
        # 实现实体提取逻辑
        return []
    
    def _get_document_entities(self, document: Dict[str, Any]) -> List[str]:
        """
        获取文档中的实体
        """
        return document.get('entities', [])
    
    def _calculate_entity_match(self, query_entities: List[str], doc_entities: List[str]) -> float:
        """
        计算实体匹配度
        """
        if not query_entities:
            return 0.5
        
        matched = set(query_entities) & set(doc_entities)
        return len(matched) / len(query_entities)


class KnowledgeGraphReranker:
    """
    基于知识图谱的重排序器
    """
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        基于知识图谱进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            user_context: 用户上下文
            
        Returns:
            重排序后的文档列表
        """
        # 查询知识图谱获取相关实体
        related_entities = self._expand_query(query)
        
        # 计算文档与扩展实体的相关性
        for doc in documents:
            graph_score = self._calculate_graph_relevance(doc, related_entities)
            doc['graph_relevance_score'] = graph_score
        
        return sorted(documents, key=lambda x: x.get('graph_relevance_score', 0), reverse=True)
    
    def _expand_query(self, query: str) -> List[str]:
        """
        基于知识图谱扩展查询
        """
        # 实现知识图谱查询扩展逻辑
        return []
    
    def _calculate_graph_relevance(self, document: Dict[str, Any], related_entities: List[str]) -> float:
        """
        计算文档与扩展实体的相关性
        """
        doc_entities = document.get('entities', [])
        matched = set(related_entities) & set(doc_entities)
        return len(matched) / len(related_entities) if related_entities else 0.5


class TemporalReranker:
    """
    时效性重排序器
    """
    
    def __init__(self, time_decay_factor: float = 0.1):
        """
        初始化时效性重排序器
        
        Args:
            time_decay_factor: 时间衰减因子
        """
        self.time_decay_factor = time_decay_factor
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        基于时效性进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            user_context: 用户上下文
            
        Returns:
            重排序后的文档列表
        """
        current_time = datetime.now()
        
        for doc in documents:
            # 计算时间衰减分数
            doc_time = doc.get('created_at', current_time)
            if isinstance(doc_time, str):
                doc_time = datetime.fromisoformat(doc_time)
            
            time_diff = (current_time - doc_time).days
            time_score = math.exp(-self.time_decay_factor * time_diff)
            
            doc['temporal_score'] = time_score
        
        return sorted(documents, key=lambda x: x.get('temporal_score', 0), reverse=True)


class AuthorityReranker:
    """
    权威性重排序器
    """
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        基于权威性进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            user_context: 用户上下文
            
        Returns:
            重排序后的文档列表
        """
        for doc in documents:
            # 基于来源权威性评分
            source_authority = self._get_source_authority(doc.get('source'))
            
            # 基于作者权威性评分
            author_authority = self._get_author_authority(doc.get('author'))
            
            # 基于引用次数评分
            citation_score = self._get_citation_score(doc.get('citations', 0))
            
            authority_score = (source_authority + author_authority + citation_score) / 3
            doc['authority_score'] = authority_score
        
        return sorted(documents, key=lambda x: x.get('authority_score', 0), reverse=True)
    
    def _get_source_authority(self, source: Optional[str]) -> float:
        """
        获取来源权威性
        """
        # 实现来源权威性评估逻辑
        return 0.5
    
    def _get_author_authority(self, author: Optional[str]) -> float:
        """
        获取作者权威性
        """
        # 实现作者权威性评估逻辑
        return 0.5
    
    def _get_citation_score(self, citations: int) -> float:
        """
        获取引用次数评分
        """
        # 实现引用次数评分逻辑
        return min(1.0, citations / 100)  # 假设100次引用是满分


class PersonalReranker:
    """
    个性化重排序器
    """
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        基于用户个性化偏好进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            user_context: 用户上下文
            
        Returns:
            重排序后的文档列表
        """
        if not user_context:
            # 没有用户上下文，返回原始顺序
            return documents
        
        user_preferences = user_context.get('preferences', {})
        
        for doc in documents:
            personal_score = self._calculate_personal_relevance(doc, user_preferences)
            doc['personal_score'] = personal_score
        
        return sorted(documents, key=lambda x: x.get('personal_score', 0), reverse=True)
    
    def _calculate_personal_relevance(self, document: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """
        计算文档与用户偏好的相关性
        """
        # 实现个性化相关性计算逻辑
        return 0.5


class MultiStageReranker:
    """
    多阶段重排序器
    """
    
    def __init__(self):
        """
        初始化多阶段重排序器
        """
        self.stages = [
            ('semantic', SemanticReranker()),      # 语义重排序
            ('entity', EntityAwareReranker()),      # 实体匹配重排序
            ('graph', KnowledgeGraphReranker()),    # 知识图谱重排序
            ('temporal', TemporalReranker()),      # 时效性重排序
            ('authority', AuthorityReranker()),    # 权威性重排序
            ('personal', PersonalReranker()),      # 个性化重排序
        ]
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        多阶段重排序流程
        
        Args:
            query: 查询文本
            documents: 文档列表
            user_context: 用户上下文
            
        Returns:
            重排序后的文档列表
        """
        results = documents.copy()
        
        for stage_name, reranker in self.stages:
            results = reranker.rerank(query, results, user_context)
        
        # 综合所有分数
        for doc in results:
            scores = [
                doc.get('semantic_score', 0),
                doc.get('entity_match_score', 0),
                doc.get('graph_relevance_score', 0),
                doc.get('temporal_score', 0),
                doc.get('authority_score', 0),
                doc.get('personal_score', 0)
            ]
            doc['final_score'] = sum(scores) / len(scores)
        
        # 按最终分数排序
        return sorted(results, key=lambda x: x.get('final_score', 0), reverse=True)
    
    def get_ranking_explanation(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取排序解释
        
        Args:
            document: 文档对象
            
        Returns:
            排序解释
        """
        return {
            'semantic_score': document.get('semantic_score', 0),
            'entity_match_score': document.get('entity_match_score', 0),
            'graph_relevance_score': document.get('graph_relevance_score', 0),
            'temporal_score': document.get('temporal_score', 0),
            'authority_score': document.get('authority_score', 0),
            'personal_score': document.get('personal_score', 0),
            'final_score': document.get('final_score', 0)
        }


class RerankingService:
    """
    重排序服务
    """
    
    def __init__(self):
        """
        初始化重排序服务
        """
        self.multi_stage_reranker = MultiStageReranker()
    
    def rerank_documents(self, query: str, documents: List[Dict[str, Any]], 
                        user_context: Optional[Dict[str, Any]] = None, 
                        top_k: int = 10) -> List[Dict[str, Any]]:
        """
        重排序文档
        
        Args:
            query: 查询文本
            documents: 文档列表
            user_context: 用户上下文
            top_k: 返回前k个结果
            
        Returns:
            重排序后的文档列表
        """
        # 执行多阶段重排序
        reranked_docs = self.multi_stage_reranker.rerank(query, documents, user_context)
        
        # 返回前k个结果
        return reranked_docs[:top_k]
    
    def evaluate_ranking(self, query: str, documents: List[Dict[str, Any]], 
                        ground_truth: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        评估排序效果
        
        Args:
            query: 查询文本
            documents: 待排序文档
            ground_truth: 真实排序结果
            
        Returns:
            评估指标
        """
        # 执行重排序
        reranked_docs = self.multi_stage_reranker.rerank(query, documents)
        
        # 计算评估指标
        metrics = {
            'precision@1': self._calculate_precision(reranked_docs, ground_truth, 1),
            'precision@3': self._calculate_precision(reranked_docs, ground_truth, 3),
            'precision@5': self._calculate_precision(reranked_docs, ground_truth, 5),
            'recall@5': self._calculate_recall(reranked_docs, ground_truth, 5),
            'ndcg@5': self._calculate_ndcg(reranked_docs, ground_truth, 5)
        }
        
        return metrics
    
    def _calculate_precision(self, ranked_docs: List[Dict[str, Any]], 
                            ground_truth: List[Dict[str, Any]], k: int) -> float:
        """
        计算precision@k
        """
        ground_truth_ids = {doc['id'] for doc in ground_truth[:k]}
        ranked_ids = {doc['id'] for doc in ranked_docs[:k]}
        
        if not ranked_ids:
            return 0.0
        
        return len(ranked_ids & ground_truth_ids) / k
    
    def _calculate_recall(self, ranked_docs: List[Dict[str, Any]], 
                         ground_truth: List[Dict[str, Any]], k: int) -> float:
        """
        计算recall@k
        """
        ground_truth_ids = {doc['id'] for doc in ground_truth}
        ranked_ids = {doc['id'] for doc in ranked_docs[:k]}
        
        if not ground_truth_ids:
            return 0.0
        
        return len(ranked_ids & ground_truth_ids) / len(ground_truth_ids)
    
    def _calculate_ndcg(self, ranked_docs: List[Dict[str, Any]], 
                       ground_truth: List[Dict[str, Any]], k: int) -> float:
        """
        计算NDCG@k
        """
        # 构建真实相关性分数映射
        relevance_map = {doc['id']: i + 1 for i, doc in enumerate(ground_truth)}
        
        # 计算DCG
        dcg = 0.0
        for i, doc in enumerate(ranked_docs[:k]):
            rel = relevance_map.get(doc['id'], 0)
            dcg += rel / math.log2(i + 2)  # 位置从1开始
        
        # 计算理想DCG
        ideal_dcg = 0.0
        for i in range(min(k, len(ground_truth))):
            ideal_dcg += (i + 1) / math.log2(i + 2)
        
        if ideal_dcg == 0:
            return 0.0
        
        return dcg / ideal_dcg