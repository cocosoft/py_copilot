"""分层知识图谱API路由模块"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import (
    KnowledgeDocument, KnowledgeBase,
    DocumentEntity, EntityRelationship,
    KBEntity, KBRelationship,
    GlobalEntity, GlobalRelationship
)
from app.services.knowledge.hierarchical_build_service import HierarchicalBuildService

router = APIRouter()


# ============ 请求/响应模型 ============

class GraphQueryParams(BaseModel):
    include_documents: bool = False
    include_kbs: bool = False
    entity_types: Optional[List[str]] = None
    max_nodes: int = 1000


class HierarchyNavigationResponse(BaseModel):
    level: str
    entity: Dict[str, Any]
    parent: Optional[Dict[str, Any]] = None
    children: List[Dict[str, Any]] = []


class EntitySearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_count: int


# ============ 文档级图谱API ============

@router.get("/documents/{document_id}/graph")
async def get_document_graph(
    document_id: int,
    include_documents: bool = Query(False),
    entity_types: Optional[List[str]] = Query(None),
    max_nodes: int = Query(1000),
    db: Session = Depends(get_db)
):
    """
    获取文档级知识图谱

    返回文档内的所有实体和关系
    """
    try:
        # 验证文档存在
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 查询实体
        entities_query = db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document_id
        )

        if entity_types:
            entities_query = entities_query.filter(
                DocumentEntity.entity_type.in_(entity_types)
            )

        entities = entities_query.limit(max_nodes).all()

        # 查询关系
        entity_ids = [e.id for e in entities]
        relationships = db.query(EntityRelationship).filter(
            EntityRelationship.document_id == document_id,
            EntityRelationship.source_id.in_(entity_ids),
            EntityRelationship.target_id.in_(entity_ids)
        ).all()

        # 构建响应
        nodes = []
        for entity in entities:
            nodes.append({
                "id": f"doc_ent_{entity.id}",
                "entity_id": entity.id,
                "text": entity.entity_text,
                "type": entity.entity_type,
                "level": "document",
                "confidence": entity.confidence,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos
            })

        edges = []
        for rel in relationships:
            edges.append({
                "id": f"doc_rel_{rel.id}",
                "source": f"doc_ent_{rel.source_id}",
                "target": f"doc_ent_{rel.target_id}",
                "type": rel.relationship_type,
                "level": "document",
                "confidence": rel.confidence
            })

        return {
            "level": "document",
            "document_id": document_id,
            "document_title": document.title,
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "entity_types": list(set(e.entity_type for e in entities))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档图谱失败: {str(e)}")


# ============ 知识库级图谱API ============

@router.get("/knowledge-bases/{kb_id}/graph")
async def get_knowledge_base_graph(
    kb_id: int,
    include_documents: bool = Query(False, description="是否包含下层文档节点"),
    entity_types: Optional[List[str]] = Query(None, description="筛选实体类型"),
    max_nodes: int = Query(1000, description="最大节点数"),
    db: Session = Depends(get_db)
):
    """
    获取知识库级知识图谱

    返回知识库内的KB级实体和关系
    可选包含下层文档级实体
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        nodes = []
        edges = []

        # 查询KB级实体
        kb_entities_query = db.query(KBEntity).filter(
            KBEntity.knowledge_base_id == kb_id
        )

        if entity_types:
            kb_entities_query = kb_entities_query.filter(
                KBEntity.entity_type.in_(entity_types)
            )

        kb_entities = kb_entities_query.limit(max_nodes).all()

        # 添加KB级节点
        for entity in kb_entities:
            nodes.append({
                "id": f"kb_ent_{entity.id}",
                "entity_id": entity.id,
                "text": entity.canonical_name,
                "type": entity.entity_type,
                "level": "knowledge_base",
                "aliases": entity.aliases,
                "document_count": entity.document_count,
                "occurrence_count": entity.occurrence_count
            })

        # 查询KB级关系
        kb_entity_ids = [e.id for e in kb_entities]
        kb_relationships = db.query(KBRelationship).filter(
            KBRelationship.knowledge_base_id == kb_id,
            KBRelationship.source_kb_entity_id.in_(kb_entity_ids),
            KBRelationship.target_kb_entity_id.in_(kb_entity_ids)
        ).all()

        for rel in kb_relationships:
            edges.append({
                "id": f"kb_rel_{rel.id}",
                "source": f"kb_ent_{rel.source_kb_entity_id}",
                "target": f"kb_ent_{rel.target_kb_entity_id}",
                "type": rel.relationship_type,
                "level": "knowledge_base",
                "aggregated_count": rel.aggregated_count
            })

        # 如果需要，包含文档级实体
        if include_documents:
            for kb_entity in kb_entities:
                doc_entities = db.query(DocumentEntity).filter(
                    DocumentEntity.kb_entity_id == kb_entity.id
                ).all()

                for doc_entity in doc_entities:
                    nodes.append({
                        "id": f"doc_ent_{doc_entity.id}",
                        "entity_id": doc_entity.id,
                        "text": doc_entity.entity_text,
                        "type": doc_entity.entity_type,
                        "level": "document",
                        "confidence": doc_entity.confidence,
                        "document_id": doc_entity.document_id
                    })

                    # 添加层级边
                    edges.append({
                        "id": f"hierarchy_{kb_entity.id}_{doc_entity.id}",
                        "source": f"kb_ent_{kb_entity.id}",
                        "target": f"doc_ent_{doc_entity.id}",
                        "type": "belongs_to",
                        "level": "hierarchy"
                    })

        return {
            "level": "knowledge_base",
            "knowledge_base_id": kb_id,
            "knowledge_base_name": kb.name,
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "kb_entity_count": len(kb_entities),
                "entity_types": list(set(e.entity_type for e in kb_entities))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库图谱失败: {str(e)}")


# ============ 全局级图谱API ============

@router.get("/graph/global")
async def get_global_graph(
    include_kbs: bool = Query(False, description="是否包含知识库节点"),
    include_documents: bool = Query(False, description="是否包含文档节点"),
    entity_types: Optional[List[str]] = Query(None, description="筛选实体类型"),
    max_nodes: int = Query(500, description="最大节点数"),
    db: Session = Depends(get_db)
):
    """
    获取全局级知识图谱

    返回跨知识库的全局实体和关系
    可选包含下层知识库和文档级实体
    """
    try:
        nodes = []
        edges = []

        # 查询全局实体
        global_entities_query = db.query(GlobalEntity)

        if entity_types:
            global_entities_query = global_entities_query.filter(
                GlobalEntity.entity_type.in_(entity_types)
            )

        global_entities = global_entities_query.limit(max_nodes).all()

        # 添加全局节点
        for entity in global_entities:
            nodes.append({
                "id": f"global_ent_{entity.id}",
                "entity_id": entity.id,
                "text": entity.global_name,
                "type": entity.entity_type,
                "level": "global",
                "aliases": entity.all_aliases,
                "kb_count": entity.kb_count,
                "document_count": entity.document_count
            })

        # 查询全局关系
        global_entity_ids = [e.id for e in global_entities]
        global_relationships = db.query(GlobalRelationship).filter(
            GlobalRelationship.source_global_entity_id.in_(global_entity_ids),
            GlobalRelationship.target_global_entity_id.in_(global_entity_ids)
        ).all()

        for rel in global_relationships:
            edges.append({
                "id": f"global_rel_{rel.id}",
                "source": f"global_ent_{rel.source_global_entity_id}",
                "target": f"global_ent_{rel.target_global_entity_id}",
                "type": rel.relationship_type,
                "level": "global",
                "aggregated_count": rel.aggregated_count,
                "source_kbs": rel.source_kbs
            })

        # 如果需要，包含下层实体
        if include_kbs or include_documents:
            for global_entity in global_entities:
                kb_entities = db.query(KBEntity).filter(
                    KBEntity.global_entity_id == global_entity.id
                ).all()

                for kb_entity in kb_entities:
                    if include_kbs:
                        nodes.append({
                            "id": f"kb_ent_{kb_entity.id}",
                            "entity_id": kb_entity.id,
                            "text": kb_entity.canonical_name,
                            "type": kb_entity.entity_type,
                            "level": "knowledge_base",
                            "knowledge_base_id": kb_entity.knowledge_base_id
                        })

                        edges.append({
                            "id": f"hierarchy_global_kb_{global_entity.id}_{kb_entity.id}",
                            "source": f"global_ent_{global_entity.id}",
                            "target": f"kb_ent_{kb_entity.id}",
                            "type": "belongs_to",
                            "level": "hierarchy"
                        })

                    if include_documents:
                        doc_entities = db.query(DocumentEntity).filter(
                            DocumentEntity.kb_entity_id == kb_entity.id
                        ).all()

                        for doc_entity in doc_entities:
                            nodes.append({
                                "id": f"doc_ent_{doc_entity.id}",
                                "entity_id": doc_entity.id,
                                "text": doc_entity.entity_text,
                                "type": doc_entity.entity_type,
                                "level": "document",
                                "document_id": doc_entity.document_id
                            })

                            parent_id = f"kb_ent_{kb_entity.id}" if include_kbs else f"global_ent_{global_entity.id}"
                            edges.append({
                                "id": f"hierarchy_{parent_id}_{doc_entity.id}",
                                "source": parent_id,
                                "target": f"doc_ent_{doc_entity.id}",
                                "type": "belongs_to",
                                "level": "hierarchy"
                            })

        return {
            "level": "global",
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "global_entity_count": len(global_entities),
                "entity_types": list(set(e.entity_type for e in global_entities))
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取全局图谱失败: {str(e)}")


# ============ 跨层导航API ============

@router.get("/entities/{entity_id}/hierarchy")
async def get_entity_hierarchy(
    entity_id: int,
    level: str = Query("document", description="实体层级: document|kb|global"),
    db: Session = Depends(get_db)
):
    """
    获取实体的层级结构

    向上导航：文档实体 -> KB实体 -> 全局实体
    """
    try:
        result = {
            "query": {"entity_id": entity_id, "level": level},
            "hierarchy": []
        }

        if level == "document":
            # 从文档实体开始
            doc_entity = db.query(DocumentEntity).filter(
                DocumentEntity.id == entity_id
            ).first()

            if not doc_entity:
                raise HTTPException(status_code=404, detail="文档实体不存在")

            result["hierarchy"].append({
                "level": "document",
                "entity": {
                    "id": doc_entity.id,
                    "text": doc_entity.entity_text,
                    "type": doc_entity.entity_type,
                    "document_id": doc_entity.document_id
                }
            })

            # 向上到KB实体
            if doc_entity.kb_entity_id:
                kb_entity = db.query(KBEntity).filter(
                    KBEntity.id == doc_entity.kb_entity_id
                ).first()

                if kb_entity:
                    result["hierarchy"].append({
                        "level": "knowledge_base",
                        "entity": {
                            "id": kb_entity.id,
                            "text": kb_entity.canonical_name,
                            "type": kb_entity.entity_type,
                            "knowledge_base_id": kb_entity.knowledge_base_id
                        }
                    })

                    # 向上到全局实体
                    if kb_entity.global_entity_id:
                        global_entity = db.query(GlobalEntity).filter(
                            GlobalEntity.id == kb_entity.global_entity_id
                        ).first()

                        if global_entity:
                            result["hierarchy"].append({
                                "level": "global",
                                "entity": {
                                    "id": global_entity.id,
                                    "text": global_entity.global_name,
                                    "type": global_entity.entity_type,
                                    "kb_count": global_entity.kb_count,
                                    "document_count": global_entity.document_count
                                }
                            })

        elif level == "kb":
            # 从KB实体开始
            kb_entity = db.query(KBEntity).filter(KBEntity.id == entity_id).first()

            if not kb_entity:
                raise HTTPException(status_code=404, detail="KB实体不存在")

            result["hierarchy"].append({
                "level": "knowledge_base",
                "entity": {
                    "id": kb_entity.id,
                    "text": kb_entity.canonical_name,
                    "type": kb_entity.entity_type,
                    "knowledge_base_id": kb_entity.knowledge_base_id
                }
            })

            # 向上到全局实体
            if kb_entity.global_entity_id:
                global_entity = db.query(GlobalEntity).filter(
                    GlobalEntity.id == kb_entity.global_entity_id
                ).first()

                if global_entity:
                    result["hierarchy"].append({
                        "level": "global",
                        "entity": {
                            "id": global_entity.id,
                            "text": global_entity.global_name,
                            "type": global_entity.entity_type,
                            "kb_count": global_entity.kb_count,
                            "document_count": global_entity.document_count
                        }
                    })

            # 向下到文档实体
            doc_entities = db.query(DocumentEntity).filter(
                DocumentEntity.kb_entity_id == entity_id
            ).all()

            result["children"] = [
                {
                    "level": "document",
                    "entity": {
                        "id": e.id,
                        "text": e.entity_text,
                        "type": e.entity_type,
                        "document_id": e.document_id
                    }
                }
                for e in doc_entities
            ]

        elif level == "global":
            # 从全局实体开始
            global_entity = db.query(GlobalEntity).filter(
                GlobalEntity.id == entity_id
            ).first()

            if not global_entity:
                raise HTTPException(status_code=404, detail="全局实体不存在")

            result["hierarchy"].append({
                "level": "global",
                "entity": {
                    "id": global_entity.id,
                    "text": global_entity.global_name,
                    "type": global_entity.entity_type,
                    "kb_count": global_entity.kb_count,
                    "document_count": global_entity.document_count
                }
            })

            # 向下到KB实体
            kb_entities = db.query(KBEntity).filter(
                KBEntity.global_entity_id == entity_id
            ).all()

            result["children"] = [
                {
                    "level": "knowledge_base",
                    "entity": {
                        "id": e.id,
                        "text": e.canonical_name,
                        "type": e.entity_type,
                        "knowledge_base_id": e.knowledge_base_id
                    }
                }
                for e in kb_entities
            ]

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取层级结构失败: {str(e)}")


# ============ 实体搜索API ============

@router.get("/entities/search")
async def search_entities(
    q: str = Query(..., description="搜索关键词"),
    level: str = Query("all", description="搜索层级: document|kb|global|all"),
    kb_id: Optional[int] = Query(None, description="限制知识库"),
    limit: int = Query(20, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    跨层实体搜索

    在指定层级或所有层级搜索实体
    """
    try:
        results = []

        # 搜索文档级实体
        if level in ["all", "document"]:
            doc_query = db.query(DocumentEntity).filter(
                DocumentEntity.entity_text.ilike(f"%{q}%")
            )

            if kb_id:
                doc_query = doc_query.join(KnowledgeDocument).filter(
                    KnowledgeDocument.knowledge_base_id == kb_id
                )

            doc_entities = doc_query.limit(limit).all()

            for entity in doc_entities:
                results.append({
                    "level": "document",
                    "entity": {
                        "id": entity.id,
                        "text": entity.entity_text,
                        "type": entity.entity_type,
                        "document_id": entity.document_id,
                        "confidence": entity.confidence
                    }
                })

        # 搜索知识库级实体
        if level in ["all", "kb"]:
            kb_query = db.query(KBEntity).filter(
                KBEntity.canonical_name.ilike(f"%{q}%")
            )

            if kb_id:
                kb_query = kb_query.filter(KBEntity.knowledge_base_id == kb_id)

            kb_entities = kb_query.limit(limit).all()

            for entity in kb_entities:
                results.append({
                    "level": "knowledge_base",
                    "entity": {
                        "id": entity.id,
                        "text": entity.canonical_name,
                        "type": entity.entity_type,
                        "knowledge_base_id": entity.knowledge_base_id,
                        "aliases": entity.aliases
                    }
                })

        # 搜索全局级实体
        if level in ["all", "global"]:
            global_entities = db.query(GlobalEntity).filter(
                GlobalEntity.global_name.ilike(f"%{q}%")
            ).limit(limit).all()

            for entity in global_entities:
                results.append({
                    "level": "global",
                    "entity": {
                        "id": entity.id,
                        "text": entity.global_name,
                        "type": entity.entity_type,
                        "kb_count": entity.kb_count,
                        "aliases": entity.all_aliases
                    }
                })

        return {
            "query": q,
            "level": level,
            "results": results[:limit],
            "total_count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索实体失败: {str(e)}")


# ============ 构建触发API ============

@router.post("/build/knowledge-base/{kb_id}")
async def build_knowledge_base_graph(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """
    触发知识库级图谱构建

    异步构建指定知识库的图谱
    """
    try:
        build_service = HierarchicalBuildService(db)
        result = build_service.build_knowledge_base_level(kb_id)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "构建失败"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.post("/build/global")
async def build_global_graph(
    db: Session = Depends(get_db)
):
    """
    触发全局级图谱构建

    异步构建全局图谱
    """
    try:
        build_service = HierarchicalBuildService(db)
        result = build_service.build_global_level()

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "构建失败"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.post("/build/all")
async def build_all_graphs(
    kb_id: Optional[int] = Query(None, description="指定知识库ID，不指定则构建所有"),
    db: Session = Depends(get_db)
):
    """
    触发全量构建

    构建所有层级的图谱
    """
    try:
        build_service = HierarchicalBuildService(db)
        result = build_service.build_all(kb_id)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "构建失败"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.get("/build/status")
async def get_build_status(
    kb_id: Optional[int] = Query(None, description="指定知识库ID"),
    db: Session = Depends(get_db)
):
    """
    获取构建状态统计
    """
    try:
        build_service = HierarchicalBuildService(db)
        status = build_service.get_build_status(kb_id)

        return {
            "success": True,
            "status": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
