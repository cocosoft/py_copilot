"""知识图谱API路由"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService

# 创建Pydantic模型用于API请求和响应
from pydantic import BaseModel, validator, model_validator
from typing import List, Dict, Any, Optional


class EntityExtractionRequest(BaseModel):
    document_id: Optional[int] = None
    text: Optional[str] = None
    
    class Config:
        extra = "forbid"  # 禁止额外的字段


class EntityExtractionResponse(BaseModel):
    success: bool
    entities_count: int = 0
    relationships_count: int = 0
    error: Optional[str] = None


class EntityExtractionResponseFixed(BaseModel):
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    success: bool


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


class GraphBuildRequest(BaseModel):
    document_id: Optional[int] = None
    knowledge_base_id: Optional[int] = None
    rebuild: bool = False
    
    class Config:
        extra = "forbid"  # 禁止额外的字段


class GraphBuildResponse(BaseModel):
    success: bool
    graph_id: Optional[str] = None
    nodes_count: int = 0
    edges_count: int = 0
    communities_count: int = 0
    statistics: Dict[str, Any] = {}
    error: Optional[str] = None


class GraphAnalysisResponse(BaseModel):
    graph_id: str
    analysis: Dict[str, Any]
    communities: List[Dict[str, Any]]
    central_nodes: List[Dict[str, Any]]


class DocumentSemanticsResponse(BaseModel):
    text_length: int
    word_count: int
    entity_count: int
    entity_density: float
    top_keywords: List[Dict[str, Any]]
    semantic_richness: float


router = APIRouter(tags=["knowledge-graph"])
knowledge_graph_service = KnowledgeGraphService()


@router.post("/extract-entities", response_model=EntityExtractionResponseFixed)
async def extract_entities(
    request: EntityExtractionRequest,
    db: Session = Depends(get_db)
):
    """从文档或文本中提取实体和关系"""
    try:
        # 验证必须提供document_id或text参数
        if not request.document_id and not request.text:
            raise HTTPException(status_code=400, detail="必须提供document_id或text参数")
            
        if request.document_id:
            # 从文档中提取实体和关系
            document = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == request.document_id
            ).first()
            
            if not document:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            # 提取实体和关系并存储
            result = knowledge_graph_service.extract_and_store_entities(db, document)
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result.get("error", "提取失败"))
            
            # 获取存储的实体和关系
            entities = knowledge_graph_service.get_document_entities(db, request.document_id)
            relationships = knowledge_graph_service.get_document_relationships(db, request.document_id)
            
            return {
                "entities": entities,
                "relationships": relationships,
                "success": True
            }
        elif request.text:
            # 从文本内容直接提取实体和关系（不存储到数据库）
            if not request.text.strip():
                raise HTTPException(status_code=400, detail="文本内容不能为空")
            
            # 直接从文本提取实体和关系
            entities, relationships = knowledge_graph_service.text_processor.extract_entities_relationships(request.text)
            
            # 转换实体格式以匹配前端预期
            formatted_entities = []
            for i, entity in enumerate(entities):
                formatted_entities.append({
                    "id": i + 1,
                    "text": entity["text"],
                    "type": entity["type"],
                    "start_pos": entity.get("start_pos", 0),
                    "end_pos": entity.get("end_pos", len(entity["text"])),
                    "confidence": entity.get("confidence", 0.7)
                })
            
            # 转换关系格式以匹配前端预期
            formatted_relationships = []
            for i, rel in enumerate(relationships):
                # 查找对应的实体索引
                source_idx = next((idx for idx, ent in enumerate(formatted_entities) if ent["text"] == rel["subject"]), None)
                target_idx = next((idx for idx, ent in enumerate(formatted_entities) if ent["text"] == rel["object"]), None)
                
                if source_idx is not None and target_idx is not None:
                    formatted_relationships.append({
                        "id": i + 1,
                        "subject": rel["subject"],
                        "object": rel["object"],
                        "relation": rel["relation"],
                        "source": {
                            "id": source_idx + 1,
                            "text": rel["subject"]
                        },
                        "target": {
                            "id": target_idx + 1,
                            "text": rel["object"]
                        },
                        "confidence": rel.get("confidence", 0.7)
                    })
            
            return {
                "entities": formatted_entities,
                "relationships": formatted_relationships,
                "success": True
            }
        
        # 这种情况理论上不会发生，因为validator已经检查过
        raise HTTPException(status_code=400, detail="必须提供document_id或text参数")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实体提取失败: {str(e)}")


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


@router.post("/build-graph", response_model=GraphBuildResponse)
async def build_knowledge_graph(
    request: GraphBuildRequest,
    db: Session = Depends(get_db)
):
    """构建知识图谱"""
    try:
        # 验证参数
        if not request.document_id and not request.knowledge_base_id:
            raise HTTPException(status_code=400, detail="必须提供document_id或knowledge_base_id参数")
        
        if request.document_id:
            # 构建单个文档的知识图谱
            result = knowledge_graph_service.build_document_graph(request.document_id, db)
        else:
            # 构建整个知识库的知识图谱
            result = knowledge_graph_service.build_knowledge_base_graph(request.knowledge_base_id, db)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return GraphBuildResponse(
            success=True,
            graph_id=result.get("graph_id"),
            nodes_count=result.get("nodes_count", 0),
            edges_count=result.get("edges_count", 0),
            communities_count=result.get("communities_count", 0),
            statistics=result.get("statistics", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建知识图谱失败: {str(e)}")


@router.get("/documents/{document_id}/graph")
async def get_document_graph(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的知识图谱数据"""
    try:
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        graph_data = knowledge_graph_service.get_document_graph_data(db, document_id)
        
        if "error" in graph_data:
            raise HTTPException(status_code=500, detail=graph_data["error"])
        
        return KnowledgeGraphDataResponse(**graph_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档图谱数据失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/graph")
async def get_knowledge_base_graph(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """获取知识库的知识图谱数据"""
    try:
        graph_data = knowledge_graph_service.get_knowledge_base_graph_data(db, knowledge_base_id)
        
        if "error" in graph_data:
            raise HTTPException(status_code=500, detail=graph_data["error"])
        
        return KnowledgeGraphDataResponse(**graph_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库图谱数据失败: {str(e)}")


@router.get("/graphs/{graph_id}/analyze", response_model=GraphAnalysisResponse)
async def analyze_graph(
    graph_id: str,
    db: Session = Depends(get_db)
):
    """分析知识图谱"""
    try:
        analysis_result = knowledge_graph_service.analyze_graph(graph_id, db)
        
        if "error" in analysis_result:
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        return GraphAnalysisResponse(**analysis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析知识图谱失败: {str(e)}")


@router.get("/graphs/{graph_id}/similar-nodes")
async def find_similar_nodes(
    graph_id: str,
    node_id: str,
    max_results: int = Query(10, ge=1, le=50, description="最大返回结果数量"),
    db: Session = Depends(get_db)
):
    """查找相似节点"""
    try:
        similar_nodes = knowledge_graph_service.find_similar_nodes(graph_id, node_id, max_results, db)
        
        if "error" in similar_nodes:
            raise HTTPException(status_code=500, detail=similar_nodes["error"])
        
        return {"similar_nodes": similar_nodes}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找相似节点失败: {str(e)}")


@router.get("/graphs/{graph_id}/path")
async def find_path_between_nodes(
    graph_id: str,
    source_node: str,
    target_node: str,
    max_path_length: int = Query(5, ge=1, le=10, description="最大路径长度"),
    db: Session = Depends(get_db)
):
    """查找两个节点之间的路径"""
    try:
        path_result = knowledge_graph_service.find_path_between_nodes(
            graph_id, source_node, target_node, max_path_length, db
        )
        
        if "error" in path_result:
            raise HTTPException(status_code=500, detail=path_result["error"])
        
        return {"path": path_result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找路径失败: {str(e)}")


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