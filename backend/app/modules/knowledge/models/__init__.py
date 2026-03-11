"""知识库模型

向量化管理模块优化 - Phase 3

任务编号: BE-009
任务名称: 统一数据模型
"""

# 导出原有模型
from app.modules.knowledge.models.knowledge_document import (
    KnowledgeBase,
    KnowledgeDocument,
    KnowledgeTag,
    DocumentEntity,
    EntityRelationship,
    DocumentChunk,
    KBEntity,
    GlobalEntity,
    document_tag_association
)

# 导出统一知识单元模型
from app.modules.knowledge.models.unified_knowledge_unit import (
    UnifiedKnowledgeUnit,
    KnowledgeUnitAssociation,
    ProcessingPipelineRun,
    KnowledgeUnitIndex,
    KnowledgeUnitType,
    KnowledgeUnitStatus,
    AssociationType
)

__all__ = [
    # 原有模型
    "KnowledgeBase",
    "KnowledgeDocument",
    "KnowledgeTag",
    "DocumentEntity",
    "EntityRelationship",
    "DocumentChunk",
    "KBEntity",
    "GlobalEntity",
    "document_tag_association",
    # 统一知识单元模型
    "UnifiedKnowledgeUnit",
    "KnowledgeUnitAssociation",
    "ProcessingPipelineRun",
    "KnowledgeUnitIndex",
    "KnowledgeUnitType",
    "KnowledgeUnitStatus",
    "AssociationType",
]