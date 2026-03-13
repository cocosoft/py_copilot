"""
知识库服务模块

提供文档处理、实体提取、实体对齐、向量化、知识图谱等功能
"""

# 核心处理
from app.services.knowledge.core.document_processor import DocumentProcessor
from app.services.knowledge.core.advanced_text_processor import AdvancedTextProcessor
from app.services.knowledge.core.document_parser import DocumentParser

# 实体提取
from app.services.knowledge.extraction.llm_extractor import LLMEntityExtractor

# 实体对齐
from app.services.knowledge.alignment.entity_alignment_service import EntityAlignmentService
from app.services.knowledge.alignment.bert_entity_aligner import BERTEntityAligner

# 向量化
from app.services.knowledge.vectorization.chroma_service import ChromaService

# 知识图谱
from app.services.knowledge.graph.knowledge_graph_service import KnowledgeGraphService

__all__ = [
    'DocumentProcessor',
    'AdvancedTextProcessor',
    'DocumentParser',
    'LLMEntityExtractor',
    'EntityAlignmentService',
    'BERTEntityAligner',
    'ChromaService',
    'KnowledgeGraphService',
]
