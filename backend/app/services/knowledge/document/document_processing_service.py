import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_document import KnowledgeDocument, DocumentChunk
from app.modules.knowledge.schemas.knowledge import DocumentProcessingStatus
from app.services.knowledge.core.document_processor import DocumentProcessor
from app.services.knowledge.chunk.chunk_entity_service import ChunkEntityService
from app.services.knowledge.document.document_entity_service import DocumentEntityService
from app.services.knowledge.processing_progress_service import processing_progress_service

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """文档处理流程管理服务
    
    统一管理文档处理的完整流程，包括：
    1. 向量化（文档解析、分块、向量化）
    2. 片段级实体识别
    3. 文档级实体聚合
    4. 知识库级实体对齐
    5. 知识图谱构建
    
    提供流程验证、状态管理和统一接口
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.document_processor = DocumentProcessor()
        self.chunk_entity_service = ChunkEntityService(db)
        self.document_entity_service = DocumentEntityService(db)
    
    def get_document_status(self, document_id: int) -> Dict[str, Any]:
        """
        获取文档的处理状态
        
        Args:
            document_id: 文档ID
            
        Returns:
            包含处理状态的字典
        """
        document = self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            return {
                "document_id": document_id,
                "status": "not_found",
                "message": "文档不存在"
            }
        
        metadata = document.document_metadata or {}
        processing_status = metadata.get('processing_status', DocumentProcessingStatus.IDLE.value)
        
        # 构建详细状态信息
        status_info = {
            "document_id": document_id,
            "processing_status": processing_status,
            "stages": {
                "text_extracted": processing_status in [
                    DocumentProcessingStatus.TEXT_EXTRACTED.value,
                    DocumentProcessingStatus.CHUNKED.value,
                    DocumentProcessingStatus.ENTITY_EXTRACTED.value,
                    DocumentProcessingStatus.VECTORIZED.value,
                    DocumentProcessingStatus.GRAPH_BUILT.value,
                    DocumentProcessingStatus.COMPLETED.value
                ],
                "chunked": processing_status in [
                    DocumentProcessingStatus.CHUNKED.value,
                    DocumentProcessingStatus.ENTITY_EXTRACTED.value,
                    DocumentProcessingStatus.VECTORIZED.value,
                    DocumentProcessingStatus.GRAPH_BUILT.value,
                    DocumentProcessingStatus.COMPLETED.value
                ],
                "entity_extracted": processing_status in [
                    DocumentProcessingStatus.ENTITY_EXTRACTED.value,
                    DocumentProcessingStatus.VECTORIZED.value,
                    DocumentProcessingStatus.GRAPH_BUILT.value,
                    DocumentProcessingStatus.COMPLETED.value
                ],
                "vectorized": processing_status in [
                    DocumentProcessingStatus.VECTORIZED.value,
                    DocumentProcessingStatus.GRAPH_BUILT.value,
                    DocumentProcessingStatus.COMPLETED.value
                ],
                "graph_built": processing_status in [
                    DocumentProcessingStatus.GRAPH_BUILT.value,
                    DocumentProcessingStatus.COMPLETED.value
                ]
            },
            "stats": {
                "chunks_count": metadata.get('chunks_count', 0),
                "entities_count": metadata.get('entities_count', 0),
                "relationships_count": metadata.get('relationships_count', 0),
                "vectorization_rate": metadata.get('vectorization_rate', 0.0),
                "graph_nodes": metadata.get('graph_nodes', 0),
                "graph_edges": metadata.get('graph_edges', 0)
            },
            "timestamps": metadata.get('processing_timestamps', {})
        }
        
        return status_info
    
    def validate_preconditions(self, document_id: int, target_stage: str) -> Dict[str, Any]:
        """
        验证处理阶段的前置条件
        
        Args:
            document_id: 文档ID
            target_stage: 目标处理阶段
            
        Returns:
            验证结果，包含是否通过和错误信息
        """
        document = self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            return {
                "valid": False,
                "message": "文档不存在"
            }
        
        metadata = document.document_metadata or {}
        current_status = metadata.get('processing_status', DocumentProcessingStatus.IDLE.value)
        
        # 定义前置条件映射
        preconditions = {
            DocumentProcessingStatus.TEXT_EXTRACTED.value: [
                DocumentProcessingStatus.IDLE.value,
                DocumentProcessingStatus.FAILED.value
            ],
            DocumentProcessingStatus.CHUNKED.value: [
                DocumentProcessingStatus.TEXT_EXTRACTED.value,
                DocumentProcessingStatus.CHUNKING_FAILED.value
            ],
            DocumentProcessingStatus.ENTITY_EXTRACTED.value: [
                DocumentProcessingStatus.CHUNKED.value,
                DocumentProcessingStatus.ENTITY_EXTRACTION_FAILED.value
            ],
            DocumentProcessingStatus.VECTORIZED.value: [
                DocumentProcessingStatus.CHUNKED.value,
                DocumentProcessingStatus.VECTORIZATION_FAILED.value
            ],
            DocumentProcessingStatus.GRAPH_BUILT.value: [
                DocumentProcessingStatus.ENTITY_EXTRACTED.value,
                DocumentProcessingStatus.GRAPH_BUILDING_FAILED.value
            ],
            DocumentProcessingStatus.COMPLETED.value: [
                DocumentProcessingStatus.GRAPH_BUILT.value
            ]
        }
        
        # 检查前置条件
        required_statuses = preconditions.get(target_stage, [])
        if current_status not in required_statuses:
            return {
                "valid": False,
                "message": f"当前状态 '{current_status}' 不满足阶段 '{target_stage}' 的前置条件",
                "required_statuses": required_statuses
            }
        
        # 额外检查：对于需要分块的阶段，确保有足够的片段
        if target_stage in [
            DocumentProcessingStatus.ENTITY_EXTRACTED.value,
            DocumentProcessingStatus.VECTORIZED.value
        ]:
            chunk_count = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).count()
            
            if chunk_count == 0:
                return {
                    "valid": False,
                    "message": "文档尚未分块，无法执行此操作"
                }
        
        return {
            "valid": True,
            "message": "前置条件满足"
        }
    
    def update_document_status(self, document_id: int, status: DocumentProcessingStatus, 
                             stats: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新文档的处理状态
        
        Args:
            document_id: 文档ID
            status: 新的处理状态
            stats: 统计信息（可选）
            
        Returns:
            是否更新成功
        """
        try:
            document = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()
            
            if not document:
                return False
            
            metadata = document.document_metadata or {}
            
            # 更新处理状态
            metadata['processing_status'] = status.value
            
            # 更新时间戳
            timestamps = metadata.get('processing_timestamps', {})
            timestamp_key = status.value.replace('_', '_at')
            timestamps[timestamp_key] = datetime.now().isoformat()
            metadata['processing_timestamps'] = timestamps
            
            # 更新统计信息
            if stats:
                metadata.update(stats)
            
            # 保存更新
            document.document_metadata = metadata
            self.db.commit()
            
            logger.info(f"文档 {document_id} 状态更新为: {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档状态失败: {e}")
            self.db.rollback()
            return False
    
    def process_vectorization(self, document_id: int, knowledge_base_id: int) -> Dict[str, Any]:
        """
        执行文档向量化流程
        
        流程：文档解析 → 文本清理 → 智能分块 → 向量化处理
        
        Args:
            document_id: 文档ID
            knowledge_base_id: 知识库ID
            
        Returns:
            处理结果
        """
        # 验证前置条件
        validation = self.validate_preconditions(
            document_id, 
            DocumentProcessingStatus.TEXT_EXTRACTED.value
        )
        
        if not validation['valid']:
            return {
                "success": False,
                "message": validation['message'],
                "document_id": document_id
            }
        
        document = self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            return {
                "success": False,
                "message": "文档不存在",
                "document_id": document_id
            }
        
        try:
            # 更新状态为处理中
            self.update_document_status(
                document_id, 
                DocumentProcessingStatus.PROCESSING
            )
            
            # 执行向量化处理
            result = self.document_processor.process_document(
                file_path=document.file_path,
                file_type=document.file_type,
                document_id=document_id,
                knowledge_base_id=knowledge_base_id,
                db=self.db,
                document_name=document.title
            )
            
            if result.get('success'):
                # 更新状态为分块完成
                self.update_document_status(
                    document_id, 
                    DocumentProcessingStatus.CHUNKED,
                    {
                        "chunks_count": len(result.get('chunks', [])),
                        "vectorization_rate": 1.0
                    }
                )
                
                return {
                    "success": True,
                    "message": "向量化完成",
                    "document_id": document_id,
                    "chunks_count": len(result.get('chunks', [])),
                    "status": DocumentProcessingStatus.CHUNKED.value
                }
            else:
                # 更新状态为失败
                self.update_document_status(
                    document_id, 
                    DocumentProcessingStatus.FAILED
                )
                
                return {
                    "success": False,
                    "message": result.get('error', '向量化失败'),
                    "document_id": document_id
                }
                
        except Exception as e:
            logger.error(f"向量化处理失败: {e}")
            self.update_document_status(
                document_id, 
                DocumentProcessingStatus.FAILED
            )
            return {
                "success": False,
                "message": str(e),
                "document_id": document_id
            }
    
    def process_entity_extraction(self, document_id: int, max_workers: int = 4) -> Dict[str, Any]:
        """
        执行片段级实体识别
        
        Args:
            document_id: 文档ID
            max_workers: 并行工作线程数
            
        Returns:
            处理结果
        """
        # 验证前置条件
        validation = self.validate_preconditions(
            document_id, 
            DocumentProcessingStatus.ENTITY_EXTRACTED.value
        )
        
        if not validation['valid']:
            return {
                "success": False,
                "message": validation['message'],
                "document_id": document_id
            }
        
        try:
            # 更新状态为处理中
            self.update_document_status(
                document_id, 
                DocumentProcessingStatus.PROCESSING
            )
            
            # 执行片段级实体识别
            result = self.chunk_entity_service.extract_document_entities_parallel(
                document_id=document_id,
                max_workers=max_workers
            )
            
            if result['total_chunks'] > 0:
                # 更新状态为实体提取完成
                self.update_document_status(
                    document_id, 
                    DocumentProcessingStatus.ENTITY_EXTRACTED,
                    {
                        "entities_count": result.get('completed', 0),
                        "failed_chunks": result.get('failed', 0)
                    }
                )
                
                return {
                    "success": True,
                    "message": "实体识别完成",
                    "document_id": document_id,
                    "total_chunks": result['total_chunks'],
                    "completed": result['completed'],
                    "failed": result['failed'],
                    "status": DocumentProcessingStatus.ENTITY_EXTRACTED.value
                }
            else:
                # 更新状态为失败
                self.update_document_status(
                    document_id, 
                    DocumentProcessingStatus.ENTITY_EXTRACTION_FAILED
                )
                
                return {
                    "success": False,
                    "message": "没有可处理的片段",
                    "document_id": document_id
                }
                
        except Exception as e:
            logger.error(f"实体识别失败: {e}")
            self.update_document_status(
                document_id, 
                DocumentProcessingStatus.ENTITY_EXTRACTION_FAILED
            )
            return {
                "success": False,
                "message": str(e),
                "document_id": document_id
            }
    
    def process_entity_aggregation(self, document_id: int, similarity_threshold: float = 0.85) -> Dict[str, Any]:
        """
        执行文档级实体聚合
        
        Args:
            document_id: 文档ID
            similarity_threshold: 相似度阈值
            
        Returns:
            处理结果
        """
        # 验证前置条件
        validation = self.validate_preconditions(
            document_id, 
            DocumentProcessingStatus.ENTITY_EXTRACTED.value
        )
        
        if not validation['valid']:
            return {
                "success": False,
                "message": validation['message'],
                "document_id": document_id
            }
        
        try:
            # 更新状态为处理中
            self.update_document_status(
                document_id, 
                DocumentProcessingStatus.PROCESSING
            )
            
            # 执行文档级实体聚合
            result = self.document_entity_service.aggregate_entities(
                document_id=document_id,
                similarity_threshold=similarity_threshold
            )
            
            if result['document_entity_count'] > 0:
                # 更新状态为实体提取完成（聚合是实体提取的一部分）
                self.update_document_status(
                    document_id, 
                    DocumentProcessingStatus.ENTITY_EXTRACTED,
                    {
                        "entities_count": result['document_entity_count'],
                        "chunk_entity_count": result['chunk_entity_count'],
                        "merged_groups": result['merged_groups']
                    }
                )
                
                return {
                    "success": True,
                    "message": "实体聚合完成",
                    "document_id": document_id,
                    "chunk_entity_count": result['chunk_entity_count'],
                    "document_entity_count": result['document_entity_count'],
                    "merged_groups": result['merged_groups'],
                    "status": DocumentProcessingStatus.ENTITY_EXTRACTED.value
                }
            else:
                # 更新状态为失败
                self.update_document_status(
                    document_id, 
                    DocumentProcessingStatus.ENTITY_EXTRACTION_FAILED
                )
                
                return {
                    "success": False,
                    "message": "没有可聚合的实体",
                    "document_id": document_id
                }
                
        except Exception as e:
            logger.error(f"实体聚合失败: {e}")
            self.update_document_status(
                document_id, 
                DocumentProcessingStatus.ENTITY_EXTRACTION_FAILED
            )
            return {
                "success": False,
                "message": str(e),
                "document_id": document_id
            }
    
    def get_processing_summary(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        获取知识库的处理状态摘要
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            处理状态摘要
        """
        documents = self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        status_counts = {}
        total_documents = len(documents)
        
        for document in documents:
            metadata = document.document_metadata or {}
            status = metadata.get('processing_status', DocumentProcessingStatus.IDLE.value)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        summary = {
            "knowledge_base_id": knowledge_base_id,
            "total_documents": total_documents,
            "status_counts": status_counts,
            "processing_rate": {
                "text_extracted": sum(1 for doc in documents if doc.document_metadata and doc.document_metadata.get('processing_status') in [
                    DocumentProcessingStatus.TEXT_EXTRACTED.value,
                    DocumentProcessingStatus.CHUNKED.value,
                    DocumentProcessingStatus.ENTITY_EXTRACTED.value,
                    DocumentProcessingStatus.VECTORIZED.value,
                    DocumentProcessingStatus.GRAPH_BUILT.value,
                    DocumentProcessingStatus.COMPLETED.value
                ]) / total_documents if total_documents > 0 else 0,
                "chunked": sum(1 for doc in documents if doc.document_metadata and doc.document_metadata.get('processing_status') in [
                    DocumentProcessingStatus.CHUNKED.value,
                    DocumentProcessingStatus.ENTITY_EXTRACTED.value,
                    DocumentProcessingStatus.VECTORIZED.value,
                    DocumentProcessingStatus.GRAPH_BUILT.value,
                    DocumentProcessingStatus.COMPLETED.value
                ]) / total_documents if total_documents > 0 else 0,
                "entity_extracted": sum(1 for doc in documents if doc.document_metadata and doc.document_metadata.get('processing_status') in [
                    DocumentProcessingStatus.ENTITY_EXTRACTED.value,
                    DocumentProcessingStatus.VECTORIZED.value,
                    DocumentProcessingStatus.GRAPH_BUILT.value,
                    DocumentProcessingStatus.COMPLETED.value
                ]) / total_documents if total_documents > 0 else 0,
                "completed": sum(1 for doc in documents if doc.document_metadata and doc.document_metadata.get('processing_status') == DocumentProcessingStatus.COMPLETED.value) / total_documents if total_documents > 0 else 0
            }
        }
        
        return summary
