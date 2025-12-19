"""知识图谱API路由"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService

# 创建Pydantic模型用于API请求和响应
from pydantic import BaseModel
from typing import List, Dict, Any


class EntityExtractionRequest(BaseModel):
    document_id: int


class EntityExtractionResponse(BaseModel):
    success: bool
    entities_count: int = 0
    relationships_count: int = 0
    error: Optional[str] = None


class EntitySearchRequest(BaseModel):
    entity_text: str
    entity_type: Optional[str] = None
    knowledge_base_id: Optional[int] = None


class EntityRelationshipResponse(BaseModel):
    entity: Dict[str, Any]
    outgoing_relationships: List[Dict[str, Any]]
    incoming_relationships: List[Dict[str, Any]]


class KnowledgeGraphDataResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class DocumentSemanticsResponse(BaseModel):
    text_length: int
    word_count: int
    entity_count: int
    entity_density: float
    top_keywords: List[Dict[str, Any]]
    semantic_richness: float


router = APIRouter(tags=["knowledge-graph"])
knowledge_graph_service = KnowledgeGraphService()


@router.post("/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    db: Session = Depends(get_db)
):
    """从文档中提取实体和关系"""
    try:
        # 获取文档
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == request.document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 提取实体和关系
        result = knowledge_graph_service.extract_and_store_entities(db, document)
        
        return EntityExtractionResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取实体失败: {str(e)}")


@router.get("/documents/{document_id}/entities")
async def get_document_entities(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有实体"""
    try:
        entities = knowledge_graph_service.get_document_entities(db, document_id)
        return {"entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体失败: {str(e)}")

# 添加单数形式的路由以兼容前端请求
@router.get("/document/{document_id}/entities")
async def get_document_entities_singular(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有实体（单数形式路由，兼容前端请求）"""
    return await get_document_entities(document_id, db)


@router.get("/documents/{document_id}/relationships")
async def get_document_relationships(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有关系"""
    try:
        relationships = knowledge_graph_service.get_document_relationships(db, document_id)
        return {"relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关系失败: {str(e)}")

# 添加单数形式的路由以兼容前端请求
@router.get("/document/{document_id}/relationships")
async def get_document_relationships_singular(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有关系（单数形式路由，兼容前端请求）"""
    return await get_document_relationships(document_id, db)


@router.get("/search-entities")
async def search_entities(
    entity_text: str = Query(..., description="实体文本"),
    entity_type: Optional[str] = Query(None, description="实体类型"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    db: Session = Depends(get_db)
):
    """搜索实体"""
    try:
        entities = knowledge_graph_service.search_entities(
            db, entity_text, entity_type, knowledge_base_id
        )
        return {"entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索实体失败: {str(e)}")


@router.get("/entities/{entity_id}/relationships")
async def get_entity_relationships(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """获取实体的所有关系"""
    try:
        result = knowledge_graph_service.get_entity_relationships(db, entity_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return EntityRelationshipResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体关系失败: {str(e)}")


@router.get("/graph-data")
async def get_knowledge_graph_data(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    db: Session = Depends(get_db)
):
    """获取知识图谱数据（用于可视化）"""
    try:
        graph_data = knowledge_graph_service.get_knowledge_graph_data(db, knowledge_base_id)
        return KnowledgeGraphDataResponse(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识图谱数据失败: {str(e)}")


@router.get("/documents/{document_id}/keywords")
async def get_document_keywords(
    document_id: int,
    top_n: int = Query(10, ge=1, le=50, description="返回关键词数量"),
    db: Session = Depends(get_db)
):
    """获取文档的关键词"""
    try:
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        keywords = knowledge_graph_service.extract_keywords_from_document(document, top_n)
        return {"keywords": keywords}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取关键词失败: {str(e)}")


@router.get("/documents/{document_id}/semantics")
async def analyze_document_semantics(
    document_id: int,
    db: Session = Depends(get_db)
):
    """分析文档语义特征"""
    try:
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        semantics = knowledge_graph_service.analyze_document_semantics(document)
        if "error" in semantics:
            raise HTTPException(status_code=400, detail=semantics["error"])
        
        return DocumentSemanticsResponse(**semantics)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析文档语义失败: {str(e)}")


@router.get("/statistics")
async def get_knowledge_graph_statistics(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    db: Session = Depends(get_db)
):
    """获取知识图谱统计信息"""
    try:
        from sqlalchemy import func
        from app.modules.knowledge.models.knowledge_document import (
            DocumentEntity, EntityRelationship, KnowledgeDocument
        )
        
        # 构建查询
        entity_query = db.query(DocumentEntity)
        relationship_query = db.query(EntityRelationship)
        
        if knowledge_base_id:
            entity_query = entity_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
            relationship_query = relationship_query.join(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            )
        
        # 统计信息
        total_entities = entity_query.count()
        total_relationships = relationship_query.count()
        
        # 按实体类型统计
        entity_types = entity_query.with_entities(
            DocumentEntity.entity_type, func.count(DocumentEntity.id)
        ).group_by(DocumentEntity.entity_type).all()
        
        # 按关系类型统计
        relationship_types = relationship_query.with_entities(
            EntityRelationship.relationship_type, func.count(EntityRelationship.id)
        ).group_by(EntityRelationship.relationship_type).all()
        
        return {
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "entity_types": dict(entity_types),
            "relationship_types": dict(relationship_types)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")