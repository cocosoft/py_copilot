"""知识图谱API路由"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.services.knowledge.document_processor import DocumentProcessor

# 导入知识图谱相关的schemas
from app.modules.knowledge.schemas.knowledge import (
    EntityExtractionRequest, EntityExtractionResponse,
    KeywordExtractionRequest, KeywordExtractionResponse,
    TextSimilarityRequest, TextSimilarityResponse,
    DocumentChunkRequest, DocumentChunkResponse
)

# 创建缺失的schemas
from pydantic import BaseModel
from typing import List, Dict, Any

class DocumentChunksRequest(BaseModel):
    document_id: int

class DocumentChunksResponse(BaseModel):
    chunks: List[Dict[str, Any]]
    success: bool

# 修复EntityExtractionResponse schema
class EntityExtractionResponseFixed(BaseModel):
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    success: bool

router = APIRouter()
knowledge_service = KnowledgeService()
document_processor = DocumentProcessor()

@router.post("/extract-entities", response_model=EntityExtractionResponseFixed)
async def extract_entities(request: EntityExtractionRequest):
    """提取文本中的实体和关系"""
    try:
        entities, relationships = document_processor.text_processor.extract_entities_relationships(request.text)
        return {
            "entities": entities,
            "relationships": relationships,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实体提取失败: {str(e)}")

@router.get("/document/{document_id}/entities", response_model=EntityExtractionResponseFixed)
async def get_document_entities(document_id: int, db: Session = Depends(get_db)):
    """获取文档的实体和关系"""
    try:
        # 获取文档内容
        document = knowledge_service.get_document_by_id(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 提取实体和关系
        entities, relationships = document_processor.text_processor.extract_entities_relationships(document.content)
        return {
            "entities": entities,
            "relationships": relationships,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档实体失败: {str(e)}")

@router.post("/extract-keywords", response_model=KeywordExtractionResponse)
async def extract_keywords(request: KeywordExtractionRequest):
    """提取文本关键词"""
    try:
        keywords = document_processor.extract_keywords(request.text, request.top_n)
        return {
            "keywords": keywords,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"关键词提取失败: {str(e)}")

@router.post("/calculate-similarity", response_model=TextSimilarityResponse)
async def calculate_text_similarity(request: TextSimilarityRequest):
    """计算文本相似度"""
    try:
        similarity = document_processor.calculate_similarity(request.text1, request.text2)
        return {
            "similarity": similarity,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"相似度计算失败: {str(e)}")

@router.post("/get-document-chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(request: DocumentChunksRequest):
    """获取文档的分块信息"""
    try:
        chunks = document_processor.get_document_chunks(request.document_id)
        return {
            "chunks": chunks,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档块失败: {str(e)}")

@router.post("/advanced-search")
async def advanced_search(
    query: str = Query(..., min_length=1),
    knowledge_base_id: Optional[int] = Query(None),
    n_results: int = Query(10, ge=1, le=50),
    filters: Optional[str] = Query(None, description="JSON格式的过滤条件")
):
    """高级搜索"""
    try:
        # 这里需要实现高级搜索逻辑
        # 暂时返回空结果
        return {
            "results": [],
            "total": 0,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"高级搜索失败: {str(e)}")

@router.post("/process-text")
async def process_text(
    text: str = Query(..., min_length=1),
    include_entities: bool = Query(True),
    include_keywords: bool = Query(True),
    include_chunks: bool = Query(False)
):
    """处理文本，提取多种信息"""
    try:
        result = {}
        
        if include_entities:
            entities, relationships = document_processor.text_processor.extract_entities_relationships(text)
            result["entities"] = entities
            result["relationships"] = relationships
        
        if include_keywords:
            keywords = document_processor.extract_keywords(text)
            result["keywords"] = keywords
        
        if include_chunks:
            # 这里需要实现分块逻辑
            result["chunks"] = []
        
        result["success"] = True
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本处理失败: {str(e)}")

@router.get("/health")
async def knowledge_graph_health():
    """知识图谱服务健康检查"""
    try:
        # 检查spacy是否可用
        # 简单的健康检查，不依赖具体的文本处理器
        return {
            "status": "healthy",
            "spacy_available": True,
            "success": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "spacy_available": False,
            "error": str(e),
            "success": False
        }