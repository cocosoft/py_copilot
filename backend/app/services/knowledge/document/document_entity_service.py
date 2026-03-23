"""
文档级实体服务

复用EntityAlignmentService的对齐逻辑，实现片段级实体聚合为文档级实体
"""

import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_document import (
    DocumentChunk, ChunkEntity, DocumentEntity
)

logger = logging.getLogger(__name__)


class DocumentEntityService:
    """文档级实体服务

    复用EntityAlignmentService的对齐逻辑，实现片段级实体聚合为文档级实体
    """

    def __init__(self, db: Session):
        self.db = db
        self.text_similarity_threshold = 0.85

    def aggregate_chunk_entities(self, document_id: int) -> Dict[str, Any]:
        """
        将文档的所有片段级实体聚合成文档级实体

        复用：EntityAlignmentService的对齐逻辑（简化版）

        Args:
            document_id: 文档ID

        Returns:
            {"document_id": int, "entities_created": int, "entities": List}
        """
        try:
            # 1. 获取文档的所有片段级实体
            chunk_entities = self.db.query(ChunkEntity).filter(
                ChunkEntity.document_id == document_id
            ).all()

            if not chunk_entities:
                return {
                    "document_id": document_id,
                    "entities_created": 0,
                    "message": "文档中没有片段级实体"
                }

            # 2. 按实体类型分组
            entity_groups = self._group_by_type(chunk_entities)

            total_created = 0
            created_entities = []

            # 3. 对每个类型组进行聚合
            for entity_type, type_entities in entity_groups.items():
                entities = self._aggregate_entity_group(
                    document_id, entity_type, type_entities
                )
                total_created += len(entities)
                created_entities.extend(entities)

            self.db.commit()

            logger.info(f"文档 {document_id} 实体聚合完成: {total_created} 个文档级实体")

            return {
                "document_id": document_id,
                "entities_created": total_created,
                "entities": [
                    {
                        "id": e.id,
                        "entity_text": e.entity_text,
                        "entity_type": e.entity_type,
                        "confidence": e.confidence
                    }
                    for e in created_entities
                ]
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"文档 {document_id} 实体聚合失败: {e}")
            return {"document_id": document_id, "entities_created": 0, "error": str(e)}

    def _group_by_type(self, entities: List[ChunkEntity]) -> Dict[str, List[ChunkEntity]]:
        """按实体类型分组"""
        groups = defaultdict(list)
        for entity in entities:
            groups[entity.entity_type].append(entity)
        return dict(groups)

    def _aggregate_entity_group(
        self,
        document_id: int,
        entity_type: str,
        chunk_entities: List[ChunkEntity]
    ) -> List[DocumentEntity]:
        """
        聚合同一类型的片段级实体

        复用：EntityAlignmentService._align_entity_group()的聚类逻辑

        Args:
            document_id: 文档ID
            entity_type: 实体类型
            chunk_entities: 片段级实体列表

        Returns:
            创建的文档级实体列表
        """
        if len(chunk_entities) == 0:
            return []

        if len(chunk_entities) == 1:
            # 只有一个实体，直接创建文档级实体
            entity = self._create_document_entity(document_id, entity_type, chunk_entities)
            return [entity] if entity else []

        # 1. 计算相似度矩阵
        similarity_matrix = self._compute_similarity_matrix(chunk_entities)

        # 2. 层次聚类
        clusters = self._hierarchical_clustering(chunk_entities, similarity_matrix)

        # 3. 为每个聚类创建文档级实体
        document_entities = []
        for cluster in clusters:
            entity = self._create_document_entity(document_id, entity_type, cluster)
            if entity:
                document_entities.append(entity)

        return document_entities

    def _compute_similarity_matrix(
        self,
        entities: List[ChunkEntity]
    ) -> List[List[float]]:
        """
        计算实体间的相似度矩阵

        复用：EntityAlignmentService._compute_similarity_matrix()的简化版
        """
        n = len(entities)
        similarity = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                # 文本相似度
                text_sim = self._text_similarity(
                    entities[i].entity_text,
                    entities[j].entity_text
                )

                similarity[i][j] = similarity[j][i] = text_sim

        return similarity

    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _hierarchical_clustering(
        self,
        entities: List[ChunkEntity],
        similarity_matrix: List[List[float]]
    ) -> List[List[ChunkEntity]]:
        """
        层次聚类

        复用：EntityAlignmentService._hierarchical_clustering()的简化版
        """
        n = len(entities)
        if n == 0:
            return []

        # 初始化：每个实体为一个簇
        clusters = [[i] for i in range(n)]

        # 合并相似度高的簇
        merged = True
        while merged and len(clusters) > 1:
            merged = False
            best_sim = 0
            best_pair = (0, 1)

            # 找到最相似的一对簇
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    sim = self._cluster_similarity(
                        clusters[i], clusters[j], similarity_matrix
                    )
                    if sim > best_sim:
                        best_sim = sim
                        best_pair = (i, j)

            # 如果最相似的簇相似度超过阈值，合并它们
            if best_sim >= self.text_similarity_threshold:
                i, j = best_pair
                clusters[i] = clusters[i] + clusters[j]
                clusters.pop(j)
                merged = True

        # 将索引转换为实体
        return [[entities[i] for i in cluster] for cluster in clusters]

    def _cluster_similarity(
        self,
        cluster1: List[int],
        cluster2: List[int],
        similarity_matrix: List[List[float]]
    ) -> float:
        """计算两个簇之间的平均相似度"""
        total_sim = 0
        count = 0
        for i in cluster1:
            for j in cluster2:
                total_sim += similarity_matrix[i][j]
                count += 1
        return total_sim / count if count > 0 else 0

    def _create_document_entity(
        self,
        document_id: int,
        entity_type: str,
        chunk_entities: List[ChunkEntity]
    ) -> DocumentEntity:
        """
        从片段级实体创建文档级实体

        Args:
            document_id: 文档ID
            entity_type: 实体类型
            chunk_entities: 片段级实体列表（同一聚类）

        Returns:
            创建的文档级实体
        """
        if not chunk_entities:
            return None

        # 选择最频繁的实体文本作为规范名称
        text_counts = defaultdict(int)
        for ce in chunk_entities:
            text_counts[ce.entity_text] += 1

        canonical_text = max(text_counts.keys(), key=lambda x: text_counts[x])

        # 计算平均置信度
        avg_confidence = sum(ce.confidence for ce in chunk_entities) / len(chunk_entities)

        # 获取第一个片段的位置信息
        first_chunk = min(chunk_entities, key=lambda x: x.start_pos)

        # 创建文档级实体
        document_entity = DocumentEntity(
            document_id=document_id,
            entity_text=canonical_text,
            entity_type=entity_type,
            start_pos=first_chunk.start_pos,
            end_pos=first_chunk.end_pos,
            confidence=avg_confidence
        )

        self.db.add(document_entity)
        self.db.flush()  # 获取ID

        # 更新片段级实体的关联
        for ce in chunk_entities:
            ce.document_entity_id = document_entity.id

        return document_entity

    def get_document_entities(self, document_id: int) -> List[Dict[str, Any]]:
        """
        获取文档的所有文档级实体

        Args:
            document_id: 文档ID

        Returns:
            实体列表
        """
        entities = self.db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document_id
        ).all()

        return [
            {
                "id": e.id,
                "entity_text": e.entity_text,
                "entity_type": e.entity_type,
                "confidence": e.confidence,
                "status": e.status
            }
            for e in entities
        ]
