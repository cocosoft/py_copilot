"""实体对齐服务模块"""

import numpy as np
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
import logging

from sqlalchemy.orm import Session
from app.modules.knowledge.models.knowledge_document import (
    DocumentEntity, KBEntity, KnowledgeDocument
)
from app.services.knowledge.alignment.bert_entity_aligner import (
    BERTEntityAligner, get_bert_aligner
)

logger = logging.getLogger(__name__)


class EntityAlignmentService:
    """
    实体对齐服务

    用于将文档级实体对齐到知识库级实体
    核心功能：实体聚类、相似度计算、别名发现

    增强功能：集成BERT语义理解
    """

    def __init__(self, db: Session, use_bert: bool = True):
        self.db = db
        self.text_similarity_threshold = 0.75
        self.semantic_similarity_threshold = 0.70

        # 初始化BERT对齐器
        self.bert_aligner = None
        if use_bert:
            try:
                self.bert_aligner = get_bert_aligner()
                logger.info("BERT实体对齐器初始化成功")
            except Exception as e:
                logger.warning(f"BERT实体对齐器初始化失败: {e}，将使用传统方法")

    def align_entities_for_kb(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        对指定知识库的所有文档实体进行对齐

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            {
                "success": bool,
                "kb_entities_created": int,
                "entities_aligned": int,
                "error": str (optional)
            }
        """
        try:
            # 1. 获取知识库内所有文档实体
            entities = self.db.query(DocumentEntity).join(
                KnowledgeDocument
            ).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).all()

            if not entities:
                return {
                    "success": True,
                    "kb_entities_created": 0,
                    "entities_aligned": 0,
                    "message": "知识库中没有文档实体"
                }

            # 2. 按实体类型分组
            entity_groups = self._group_by_type(entities)

            total_kb_entities = 0
            total_aligned = 0

            # 3. 对每个类型组进行对齐
            for entity_type, type_entities in entity_groups.items():
                kb_entities, aligned_count = self._align_entity_group(
                    knowledge_base_id, entity_type, type_entities
                )
                total_kb_entities += len(kb_entities)
                total_aligned += aligned_count

            return {
                "success": True,
                "kb_entities_created": total_kb_entities,
                "entities_aligned": total_aligned
            }

        except Exception as e:
            logger.error(f"实体对齐失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _group_by_type(self, entities: List[DocumentEntity]) -> Dict[str, List[DocumentEntity]]:
        """按实体类型分组"""
        groups = defaultdict(list)
        for entity in entities:
            groups[entity.entity_type].append(entity)
        return dict(groups)

    def _align_entity_group(
        self,
        knowledge_base_id: int,
        entity_type: str,
        entities: List[DocumentEntity]
    ) -> Tuple[List[KBEntity], int]:
        """
        对齐同一类型的实体组

        Args:
            knowledge_base_id: 知识库ID
            entity_type: 实体类型
            entities: 实体列表

        Returns:
            (KBEntity列表, 对齐的实体数量)
        """
        if len(entities) == 0:
            return [], 0

        if len(entities) == 1:
            # 只有一个实体，直接创建KB实体
            kb_entity = self._create_kb_entity(knowledge_base_id, entity_type, entities)
            return [kb_entity], 1

        # 1. 计算相似度矩阵
        similarity_matrix = self._compute_similarity_matrix(entities)

        # 2. 层次聚类
        clusters = self._hierarchical_clustering(entities, similarity_matrix)

        # 3. 为每个聚类创建KB实体
        kb_entities = []
        aligned_count = 0

        for cluster in clusters:
            kb_entity = self._create_kb_entity(knowledge_base_id, entity_type, cluster)
            kb_entities.append(kb_entity)
            aligned_count += len(cluster)

        return kb_entities, aligned_count

    def _compute_similarity_matrix(
        self,
        entities: List[DocumentEntity]
    ) -> np.ndarray:
        """
        计算实体间的相似度矩阵

        使用多维度相似度：
        - 文本相似度 (30%): Jaro-Winkler
        - BERT语义相似度 (40%): 基于BERT的语义理解
        - 传统语义相似度 (10%): 基于词重叠
        - 上下文相似度 (20%): 文档相关性
        """
        n = len(entities)
        similarity = np.zeros((n, n))

        # 如果BERT对齐器可用，计算BERT语义相似度
        bert_similarity = None
        if self.bert_aligner:
            try:
                bert_similarity = self._compute_bert_similarity_matrix(entities)
            except Exception as e:
                logger.warning(f"BERT相似度计算失败: {e}")

        for i in range(n):
            for j in range(i + 1, n):
                # 文本相似度
                text_sim = self._text_similarity(
                    entities[i].entity_text,
                    entities[j].entity_text
                )

                # BERT语义相似度（优先使用）
                if bert_similarity is not None:
                    bert_sim = bert_similarity[i][j]
                else:
                    bert_sim = 0.0

                # 传统语义相似度（作为补充）
                semantic_sim = self._semantic_similarity(
                    entities[i].entity_text,
                    entities[j].entity_text
                )

                # 上下文相似度
                context_sim = self._context_similarity(
                    entities[i].document_id,
                    entities[j].document_id
                )

                # 加权组合
                if bert_similarity is not None:
                    # 使用BERT语义相似度
                    similarity[i][j] = similarity[j][i] = (
                        0.30 * text_sim +
                        0.40 * bert_sim +
                        0.10 * semantic_sim +
                        0.20 * context_sim
                    )
                else:
                    # 回退到传统方法
                    similarity[i][j] = similarity[j][i] = (
                        0.40 * text_sim +
                        0.40 * semantic_sim +
                        0.20 * context_sim
                    )

        return similarity

    def _compute_bert_similarity_matrix(
        self,
        entities: List[DocumentEntity]
    ) -> np.ndarray:
        """
        使用BERT计算实体间的语义相似度矩阵
        """
        if not self.bert_aligner:
            return None

        # 准备实体数据
        entity_dicts = []
        for entity in entities:
            entity_dicts.append({
                'id': entity.id,
                'text': entity.entity_text,
                'type': entity.entity_type,
                'context': entity.context or ''
            })

        # 编码实体
        embeddings = self.bert_aligner.encode_entities(entity_dicts)

        # 计算相似度矩阵
        return self.bert_aligner.compute_similarity_matrix(embeddings)

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度

        使用 SequenceMatcher 计算 Jaro-Winkler 风格的相似度
        """
        if not text1 or not text2:
            return 0.0

        # 标准化文本
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        # 完全匹配
        if t1 == t2:
            return 1.0

        # 包含关系
        if t1 in t2 or t2 in t1:
            return 0.9

        # 序列相似度
        return SequenceMatcher(None, t1, t2).ratio()

    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """
        计算语义相似度

        简化实现：基于词重叠和词序
        可扩展为使用预训练词向量（如 Word2Vec、BERT）
        """
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Jaccard 相似度
        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _context_similarity(self, doc_id1: int, doc_id2: int) -> float:
        """
        计算上下文相似度

        基于文档是否相同或相关
        """
        if doc_id1 == doc_id2:
            return 1.0

        # 可扩展：检查文档标签、知识库等
        return 0.5

    def _hierarchical_clustering(
        self,
        entities: List[DocumentEntity],
        similarity_matrix: np.ndarray
    ) -> List[List[DocumentEntity]]:
        """
        层次聚类

        使用自底向上的聚合聚类，将相似实体分到同一组
        """
        n = len(entities)
        if n == 0:
            return []

        if n == 1:
            return [[entities[0]]]

        # 初始化：每个实体为一个簇
        clusters = [[i] for i in range(n)]

        # 自底向上合并
        merged = True
        while merged and len(clusters) > 1:
            merged = False
            best_merge = None
            best_similarity = self.text_similarity_threshold

            # 找到最相似的簇对
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    sim = self._cluster_similarity(
                        clusters[i], clusters[j], similarity_matrix
                    )
                    if sim > best_similarity:
                        best_similarity = sim
                        best_merge = (i, j)

            # 合并最相似的簇
            if best_merge:
                i, j = best_merge
                clusters[i] = clusters[i] + clusters[j]
                clusters.pop(j)
                merged = True

        # 转换索引为实体
        return [[entities[idx] for idx in cluster] for cluster in clusters]

    def _cluster_similarity(
        self,
        cluster1: List[int],
        cluster2: List[int],
        similarity_matrix: np.ndarray
    ) -> float:
        """计算两个簇的相似度（平均链接）"""
        total_sim = 0.0
        count = 0

        for i in cluster1:
            for j in cluster2:
                total_sim += similarity_matrix[i][j]
                count += 1

        return total_sim / count if count > 0 else 0.0

    def _create_kb_entity(
        self,
        knowledge_base_id: int,
        entity_type: str,
        entity_cluster: List[DocumentEntity]
    ) -> KBEntity:
        """
        从实体聚类创建KB级实体
        """
        # 选择规范名称（出现次数最多的）
        name_counts = defaultdict(int)
        for entity in entity_cluster:
            name_counts[entity.entity_text] += 1

        canonical_name = max(name_counts.keys(), key=lambda x: name_counts[x])

        # 收集别名
        aliases = list(set([
            entity.entity_text
            for entity in entity_cluster
            if entity.entity_text != canonical_name
        ]))

        # 统计信息
        document_ids = set(entity.document_id for entity in entity_cluster)

        # 创建KB实体
        kb_entity = KBEntity(
            knowledge_base_id=knowledge_base_id,
            canonical_name=canonical_name,
            entity_type=entity_type,
            aliases=aliases,
            document_count=len(document_ids),
            occurrence_count=len(entity_cluster)
        )

        self.db.add(kb_entity)
        self.db.flush()  # 获取ID

        # 更新文档实体的关联
        for entity in entity_cluster:
            entity.kb_entity_id = kb_entity.id

        return kb_entity
