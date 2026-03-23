from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field
  
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.services.knowledge.document.document_processing_service import DocumentProcessingService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["knowledge_document_processing"]
)


class ChunkRequest(BaseModel):
    """
    文档切片请求模型
    """
    knowledge_base_id: int = Field(..., description="知识库ID")
    max_chunk_size: int = Field(1000, description="最大切片大小")
    min_chunk_size: int = Field(200, description="最小切片大小")
    overlap: int = Field(50, description="切片重叠大小")


@router.get("/documents/{document_id}/status")
async def get_document_processing_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取文档的处理状态
    
    返回文档的当前处理状态和详细的阶段信息
    """
    processing_service = DocumentProcessingService(db)
    status_info = processing_service.get_document_status(document_id)
    
    if status_info.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {
        "success": True,
        "data": status_info
    }


@router.post("/documents/{document_id}/vectorize")
async def vectorize_document(
    document_id: int,
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    执行文档向量化
    
    流程：文档解析 → 文本清理 → 智能分块 → 向量化处理
    """
    processing_service = DocumentProcessingService(db)
    result = processing_service.process_vectorization(
        document_id=document_id,
        knowledge_base_id=knowledge_base_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "success": True,
        "data": result
    }


@router.post("/documents/{document_id}/extract-entities")
async def extract_document_entities(
    document_id: int,
    max_workers: int = 4,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    执行片段级实体识别
    
    对文档的所有片段进行并行实体识别
    """
    processing_service = DocumentProcessingService(db)
    result = processing_service.process_entity_extraction(
        document_id=document_id,
        max_workers=max_workers
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "success": True,
        "data": result
    }


@router.post("/documents/{document_id}/aggregate-entities")
async def aggregate_document_entities(
    document_id: int,
    similarity_threshold: float = 0.85,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    执行文档级实体聚合
    
    将片段级实体聚合为文档级实体
    """
    processing_service = DocumentProcessingService(db)
    result = processing_service.process_entity_aggregation(
        document_id=document_id,
        similarity_threshold=similarity_threshold
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "success": True,
        "data": result
    }


@router.get("/knowledge-bases/{knowledge_base_id}/processing-summary")
async def get_knowledge_base_processing_summary(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取知识库的处理状态摘要
    
    返回知识库中所有文档的处理状态统计
    """
    processing_service = DocumentProcessingService(db)
    summary = processing_service.get_processing_summary(knowledge_base_id)
    
    return {
        "success": True,
        "data": summary
    }


@router.post("/documents/{document_id}/validate-preconditions")
async def validate_document_preconditions(
    document_id: int,
    target_stage: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    验证文档处理的前置条件
    
    检查文档是否满足目标处理阶段的前置条件
    """
    processing_service = DocumentProcessingService(db)
    validation = processing_service.validate_preconditions(
        document_id=document_id,
        target_stage=target_stage
    )
    
    return {
        "success": True,
        "data": validation
    }


@router.post("/documents/{document_id}/extract-text")
async def extract_document_text(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    执行文档文本提取
    
    从文档文件中提取纯文本内容
    """
    from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
    from app.services.knowledge.core.document_processor import DocumentProcessor
    
    # 查找文档
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 更新状态为处理中
        if not document.document_metadata:
            document.document_metadata = {}
        document.document_metadata["processing_status"] = "processing"
        db.commit()
        
        # 执行文本提取
        processor = DocumentProcessor()
        raw_text = processor.parser.parse_document(document.file_path)
        
        if not raw_text:
            raise ValueError("无法提取文档文本")
        
        # 更新文档内容
        document.content = raw_text
        document.document_metadata["processing_status"] = "text_extracted"
        document.document_metadata["text_length"] = len(raw_text)
        document.document_metadata["text_extracted_at"] = datetime.now().isoformat()
        
        from sqlalchemy.orm import attributes
        attributes.flag_modified(document, "document_metadata")
        db.commit()
        
        return {
            "success": True,
            "message": "文本提取完成",
            "document_id": document_id,
            "text_length": len(raw_text),
            "status": "text_extracted"
        }
        
    except Exception as e:
        logger.error(f"文本提取失败: {e}")
        if document.document_metadata:
            document.document_metadata["processing_status"] = "text_extraction_failed"
            db.commit()
        
        raise HTTPException(status_code=500, detail=f"文本提取失败: {str(e)}")


@router.post("/documents/{document_id}/chunk")
async def chunk_document(
    document_id: int,
    request_data: ChunkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    执行文档切片处理
    
    将文档内容分割成适合向量化的片段
    """
    from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
    from app.services.knowledge.core.document_processor import DocumentProcessor
    
    # 查找文档
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 验证前置条件
    if not document.content:
        raise HTTPException(status_code=400, detail="文档内容为空，请先提取文本")
    
    try:
        # 更新状态为处理中
        if not document.document_metadata:
            document.document_metadata = {}
        document.document_metadata["processing_status"] = "processing"
        db.commit()
        
        # 执行切片处理
        processor = DocumentProcessor()
        chunks = processor._simple_chunking(
            document.content,
            max_chunk_size=request_data.max_chunk_size,
            min_chunk_size=request_data.min_chunk_size,
            overlap=request_data.overlap
        )
        
        if not chunks:
            raise ValueError("切片失败，无法生成有效片段")
        
        # 保存切片到数据库
        from app.modules.knowledge.models.knowledge_document import DocumentChunk
        
        # 删除旧的切片
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        
        # 创建新切片
        total_chunks = len(chunks)
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_text=chunk_text,
                chunk_index=i,
                start_pos=0,
                end_pos=len(chunk_text),
                total_chunks=total_chunks,
                is_vectorized=False,
                created_at=datetime.now()
            )
            chunk_objects.append(chunk)
        
        db.bulk_save_objects(chunk_objects)
        db.commit()
        
        # 更新文档状态
        document.document_metadata["processing_status"] = "chunked"
        document.document_metadata["chunks_count"] = len(chunks)
        document.document_metadata["chunked_at"] = datetime.now().isoformat()
        
        from sqlalchemy.orm import attributes
        attributes.flag_modified(document, "document_metadata")
        db.commit()
        
        return {
            "success": True,
            "message": "切片完成",
            "document_id": document_id,
            "chunks_count": len(chunks),
            "status": "chunked"
        }
        
    except Exception as e:
        logger.error(f"切片处理失败: {e}")
        if document.document_metadata:
            document.document_metadata["processing_status"] = "chunking_failed"
            db.commit()
        
        raise HTTPException(status_code=500, detail=f"切片处理失败: {str(e)}")


@router.post("/documents/{document_id}/build-graph")
async def build_document_graph(
    document_id: int,
    knowledge_base_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    执行文档知识图谱构建
    
    基于文档实体和关系构建知识图谱
    """
    from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
    from app.services.knowledge.graph.knowledge_graph_service import KnowledgeGraphService
    
    # 查找文档
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 更新状态为处理中
        if not document.document_metadata:
            document.document_metadata = {}
        document.document_metadata["processing_status"] = "processing"
        db.commit()
        
        # 执行图谱构建
        graph_service = KnowledgeGraphService(db)
        
        # 获取文档实体
        from app.modules.knowledge.models.knowledge_document import DocumentEntity
        entities = db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document_id
        ).all()
        
        if not entities:
            raise ValueError("文档没有实体，请先进行实体提取")
        
        # 构建图谱
        result = graph_service.build_document_graph(
            document_id=document_id,
            knowledge_base_id=knowledge_base_id
        )
        
        # 更新文档状态
        document.document_metadata["processing_status"] = "graph_built"
        document.document_metadata["graph_nodes"] = result.get("nodes_count", 0)
        document.document_metadata["graph_edges"] = result.get("edges_count", 0)
        document.document_metadata["graph_built_at"] = datetime.now().isoformat()
        
        from sqlalchemy.orm import attributes
        attributes.flag_modified(document, "document_metadata")
        db.commit()
        
        return {
            "success": True,
            "message": "知识图谱构建完成",
            "document_id": document_id,
            "nodes_count": result.get("nodes_count", 0),
            "edges_count": result.get("edges_count", 0),
            "status": "graph_built"
        }
        
    except Exception as e:
        logger.error(f"知识图谱构建失败: {e}")
        if document.document_metadata:
            document.document_metadata["processing_status"] = "graph_building_failed"
            db.commit()
        
        raise HTTPException(status_code=500, detail=f"知识图谱构建失败: {str(e)}")
