"""关系聚合服务模块"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from app.modules.knowledge.models.knowledge_document import (
    EntityRelationship, KBRelationship, GlobalRelationship,
    DocumentEntity, KBEntity, GlobalEntity, KnowledgeDocument
)

logger = logging.getLogger(__name__)


class RelationshipAggregationService:
    """
    关系聚合服务

    用于将文档级关系聚合到知识库级和全局级
    """

    def __init__(self, db: Session):
        self.db = db

    def aggregate_relationships_for_kb(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        聚合指定知识库的关系

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            {
                "success": bool,
                "kb_relationships_created": int,
                "error": str (optional)
            }
        """
        try:
            # 1. 获取知识库内所有文档关系
            doc_relationships = self.db.query(EntityRelationship).join(
                DocumentEntity, EntityRelationship.source_id == DocumentEntity.id
            ).join(
                KnowledgeDocument, DocumentEntity.document_id == KnowledgeDocument.id
            ).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).all()

            if not doc_relationships:
                return {
                    "success": True,
                    "kb_relationships_created": 0,
                    "message": "知识库中没有文档关系"
                }

            # 2. 按KB实体对分组
            relationship_groups = self._group_by_kb_entities(doc_relationships)

            # 3. 创建KB级关系
            kb_relationships = []
            for (source_kb_id, target_kb_id, rel_type), rels in relationship_groups.items():
                kb_rel = self._create_kb_relationship(
                    knowledge_base_id, source_kb_id, target_kb_id, rel_type, rels
                )
                kb_relationships.append(kb_rel)

            return {
                "success": True,
                "kb_relationships_created": len(kb_relationships)
            }

        except Exception as e:
            logger.error(f"关系聚合失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _group_by_kb_entities(
        self,
        relationships: List[EntityRelationship]
    ) -> Dict[Tuple[int, int, str], List[EntityRelationship]]:
        """按KB实体对和关系类型分组"""
        groups = defaultdict(list)

        for rel in relationships:
            # 获取源实体和目标实体的KB实体ID
            source_kb_id = rel.source_entity.kb_entity_id if rel.source_entity else None
            target_kb_id = rel.target_entity.kb_entity_id if rel.target_entity else None

            if source_kb_id and target_kb_id:
                key = (source_kb_id, target_kb_id, rel.relationship_type)
                groups[key].append(rel)

        return dict(groups)

    def _create_kb_relationship(
        self,
        knowledge_base_id: int,
        source_kb_id: int,
        target_kb_id: int,
        relationship_type: str,
        doc_relationships: List[EntityRelationship]
    ) -> KBRelationship:
        """创建KB级关系"""
        # 收集来源文档关系ID
        source_rel_ids = [rel.id for rel in doc_relationships]

        # 检查是否已存在
        existing = self.db.query(KBRelationship).filter(
            KBRelationship.knowledge_base_id == knowledge_base_id,
            KBRelationship.source_kb_entity_id == source_kb_id,
            KBRelationship.target_kb_entity_id == target_kb_id,
            KBRelationship.relationship_type == relationship_type
        ).first()

        if existing:
            # 更新现有关系
            existing.aggregated_count = len(doc_relationships)
            existing.source_relationships = source_rel_ids
            return existing

        # 创建新关系
        kb_rel = KBRelationship(
            knowledge_base_id=knowledge_base_id,
            source_kb_entity_id=source_kb_id,
            target_kb_entity_id=target_kb_id,
            relationship_type=relationship_type,
            aggregated_count=len(doc_relationships),
            source_relationships=source_rel_ids
        )

        self.db.add(kb_rel)
        return kb_rel

    def aggregate_relationships_global(self) -> Dict[str, Any]:
        """
        聚合全局关系

        Returns:
            {
                "success": bool,
                "global_relationships_created": int,
                "error": str (optional)
            }
        """
        try:
            # 1. 获取所有KB关系
            kb_relationships = self.db.query(KBRelationship).all()

            if not kb_relationships:
                return {
                    "success": True,
                    "global_relationships_created": 0,
                    "message": "没有KB级关系需要聚合"
                }

            # 2. 按全局实体对分组
            relationship_groups = self._group_by_global_entities(kb_relationships)

            # 3. 创建全局关系
            global_relationships = []
            for (source_global_id, target_global_id, rel_type), rels in relationship_groups.items():
                global_rel = self._create_global_relationship(
                    source_global_id, target_global_id, rel_type, rels
                )
                global_relationships.append(global_rel)

            return {
                "success": True,
                "global_relationships_created": len(global_relationships)
            }

        except Exception as e:
            logger.error(f"全局关系聚合失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _group_by_global_entities(
        self,
        relationships: List[KBRelationship]
    ) -> Dict[Tuple[int, int, str], List[KBRelationship]]:
        """按全局实体对和关系类型分组"""
        groups = defaultdict(list)

        for rel in relationships:
            # 获取源实体和目标实体的全局实体ID
            source_global_id = rel.source_entity.global_entity_id if rel.source_entity else None
            target_global_id = rel.target_entity.global_entity_id if rel.target_entity else None

            if source_global_id and target_global_id:
                key = (source_global_id, target_global_id, rel.relationship_type)
                groups[key].append(rel)

        return dict(groups)

    def _create_global_relationship(
        self,
        source_global_id: int,
        target_global_id: int,
        relationship_type: str,
        kb_relationships: List[KBRelationship]
    ) -> GlobalRelationship:
        """创建全局关系"""
        # 收集来源知识库ID
        source_kb_ids = list(set(rel.knowledge_base_id for rel in kb_relationships))
        total_count = sum(rel.aggregated_count for rel in kb_relationships)

        # 检查是否已存在
        existing = self.db.query(GlobalRelationship).filter(
            GlobalRelationship.source_global_entity_id == source_global_id,
            GlobalRelationship.target_global_entity_id == target_global_id,
            GlobalRelationship.relationship_type == relationship_type
        ).first()

        if existing:
            # 更新现有关系
            existing.aggregated_count = total_count
            existing.source_kbs = source_kb_ids
            return existing

        # 创建新关系
        global_rel = GlobalRelationship(
            source_global_entity_id=source_global_id,
            target_global_entity_id=target_global_id,
            relationship_type=relationship_type,
            aggregated_count=total_count,
            source_kbs=source_kb_ids
        )

        self.db.add(global_rel)
        return global_rel
