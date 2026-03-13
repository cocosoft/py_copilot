"""分层构建调度服务模块"""

from typing import Dict, Any, Optional
from enum import Enum
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.knowledge.models.knowledge_document import (
    KnowledgeDocument, KnowledgeBase,
    DocumentEntity, KBEntity, GlobalEntity
)
from app.services.knowledge.alignment.entity_alignment_service import EntityAlignmentService
from app.services.knowledge.alignment.cross_kb_linking_service import CrossKBEntityLinkingService
from app.services.knowledge.relationship_aggregation_service import RelationshipAggregationService

logger = logging.getLogger(__name__)


class BuildLevel(Enum):
    """构建层级"""
    DOCUMENT = "document"
    KNOWLEDGE_BASE = "knowledge_base"
    GLOBAL = "global"


class HierarchicalBuildService:
    """
    分层构建调度服务

    协调三层知识图谱的构建流程
    """

    def __init__(self, db: Session):
        self.db = db
        self.alignment_service = EntityAlignmentService(db)
        self.linking_service = CrossKBEntityLinkingService(db)
        self.relationship_service = RelationshipAggregationService(db)

    def build_document_level(self, document_id: int) -> Dict[str, Any]:
        """
        构建文档级图谱

        在文档上传/更新时触发，实时构建
        """
        try:
            from app.services.knowledge.graph.knowledge_graph_service import KnowledgeGraphService

            service = KnowledgeGraphService()
            document = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()

            if not document:
                return {"success": False, "error": "文档不存在"}

            # 使用现有服务提取实体和关系
            result = service.extract_and_store_entities(self.db, document)

            return result

        except Exception as e:
            logger.error(f"文档级构建失败: {e}")
            return {"success": False, "error": str(e)}

    def build_knowledge_base_level(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        构建知识库级图谱

        包括：
        1. 实体对齐
        2. 关系聚合
        """
        try:
            logger.info(f"开始构建知识库 {knowledge_base_id} 的图谱")

            # 1. 实体对齐
            alignment_result = self.alignment_service.align_entities_for_kb(knowledge_base_id)
            if not alignment_result["success"]:
                return alignment_result

            # 2. 关系聚合
            relationship_result = self.relationship_service.aggregate_relationships_for_kb(knowledge_base_id)
            if not relationship_result["success"]:
                return relationship_result

            self.db.commit()

            return {
                "success": True,
                "level": BuildLevel.KNOWLEDGE_BASE.value,
                "knowledge_base_id": knowledge_base_id,
                "kb_entities_created": alignment_result.get("kb_entities_created", 0),
                "entities_aligned": alignment_result.get("entities_aligned", 0),
                "kb_relationships_created": relationship_result.get("kb_relationships_created", 0)
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"知识库级构建失败: {e}")
            return {"success": False, "error": str(e)}

    def build_global_level(self) -> Dict[str, Any]:
        """
        构建全局级图谱

        包括：
        1. 跨库实体链接
        2. 全局关系聚合
        """
        try:
            logger.info("开始构建全局级图谱")

            # 1. 跨库实体链接
            linking_result = self.linking_service.link_entities_global()
            if not linking_result["success"]:
                return linking_result

            # 2. 全局关系聚合
            relationship_result = self.relationship_service.aggregate_relationships_global()
            if not relationship_result["success"]:
                return relationship_result

            self.db.commit()

            return {
                "success": True,
                "level": BuildLevel.GLOBAL.value,
                "global_entities_created": linking_result.get("global_entities_created", 0),
                "kb_entities_linked": linking_result.get("kb_entities_linked", 0),
                "global_relationships_created": relationship_result.get("global_relationships_created", 0)
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"全局级构建失败: {e}")
            return {"success": False, "error": str(e)}

    def build_all(self, knowledge_base_id: Optional[int] = None) -> Dict[str, Any]:
        """
        构建所有层级

        Args:
            knowledge_base_id: 如果指定，只构建该知识库；否则构建所有
        """
        results = {
            "success": True,
            "document_level": [],
            "knowledge_base_level": [],
            "global_level": None
        }

        try:
            if knowledge_base_id:
                # 构建指定知识库
                kb_result = self.build_knowledge_base_level(knowledge_base_id)
                results["knowledge_base_level"].append(kb_result)
            else:
                # 构建所有知识库
                knowledge_bases = self.db.query(KnowledgeBase).all()
                for kb in knowledge_bases:
                    kb_result = self.build_knowledge_base_level(kb.id)
                    results["knowledge_base_level"].append(kb_result)

            # 构建全局级
            global_result = self.build_global_level()
            results["global_level"] = global_result

            return results

        except Exception as e:
            logger.error(f"全量构建失败: {e}")
            return {"success": False, "error": str(e)}

    def get_build_status(self, knowledge_base_id: Optional[int] = None) -> Dict[str, Any]:
        """获取构建状态统计"""
        status = {
            "document_level": {},
            "knowledge_base_level": {},
            "global_level": {}
        }

        # 文档级统计
        doc_query = self.db.query(func.count(DocumentEntity.id))
        if knowledge_base_id:
            doc_query = doc_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        status["document_level"]["entity_count"] = doc_query.scalar() or 0

        # 知识库级统计
        kb_query = self.db.query(func.count(KBEntity.id))
        if knowledge_base_id:
            kb_query = kb_query.filter(KBEntity.knowledge_base_id == knowledge_base_id)
        status["knowledge_base_level"]["entity_count"] = kb_query.scalar() or 0

        # 全局级统计
        status["global_level"]["entity_count"] = self.db.query(func.count(GlobalEntity.id)).scalar() or 0

        return status
