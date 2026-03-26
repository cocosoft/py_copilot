"""
层级结构API

提供层次化实体管理的API端点，支持四个层级：
- 片段级
- 文档级
- 知识库级
- 全局级

任务编号: Phase3-Week10
阶段: 第三阶段 - 功能不完善问题优化
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import KnowledgeDocument, KnowledgeBase, DocumentEntity, EntityRelationship
from app.services.knowledge.graph.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["层级结构"])

knowledge_graph_service = KnowledgeGraphService()


# 片段级API
@router.get("/knowledge-bases/{knowledge_base_id}/chunks")
async def get_chunk_entities(
    knowledge_base_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("index"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db)
):
    """
    获取片段级实体列表
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取知识库中的文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 获取所有文档的实体
        all_entities = []
        for doc in documents:
            entities = knowledge_graph_service.get_document_entities(db, doc.id, distinct=False)
            all_entities.extend(entities)
        
        # 排序
        if sort_by == "index":
            all_entities.sort(key=lambda x: x.get("start_pos", 0), reverse=sort_order == "desc")
        elif sort_by == "name":
            all_entities.sort(key=lambda x: x.get("text", ""), reverse=sort_order == "desc")
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entities = all_entities[start_idx:end_idx]
        
        return {
            "data": paginated_entities,
            "total": len(all_entities),
            "page": page,
            "page_size": page_size,
            "knowledge_base_id": knowledge_base_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取片段级实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取片段级实体失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/chunks/{chunk_id}/graph")
async def get_chunk_graph(
    knowledge_base_id: int,
    chunk_id: int,
    db: Session = Depends(get_db)
):
    """
    获取片段级图谱数据
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 这里简化处理，返回文档级图谱数据
        # 实际项目中应该根据chunk_id获取具体片段的图谱
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).first()
        
        if not documents:
            return {
                "nodes": [],
                "edges": [],
                "statistics": {
                    "total_entities": 0,
                    "total_relationships": 0
                }
            }
        
        graph_data = knowledge_graph_service.get_document_graph_data(db, documents.id)
        return graph_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取片段级图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取片段级图谱失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/stats/fragment")
async def get_fragment_level_stats(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取片段级统计数据
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取知识库中的文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 统计实体和关系
        total_entities = 0
        total_relationships = 0
        entity_types = {}
        
        for doc in documents:
            entities = knowledge_graph_service.get_document_entities(db, doc.id, distinct=False)
            relationships = knowledge_graph_service.get_document_relationships(db, doc.id)
            
            total_entities += len(entities)
            total_relationships += len(relationships)
            
            # 统计实体类型
            for entity in entities:
                entity_type = entity.get("type", "未知")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        return {
            "documentCount": len(documents),
            "entityCount": total_entities,
            "relationCount": total_relationships,
            "avgEntitiesPerDoc": round(total_entities / len(documents), 2) if documents else 0,
            "entityTypes": [
                {"type": type_name, "count": count}
                for type_name, count in entity_types.items()
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取片段级统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取片段级统计失败: {str(e)}")


# 文档级API
@router.get("/knowledge-bases/{knowledge_base_id}/documents/entities")
async def get_document_entities(
    knowledge_base_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db)
):
    """
    获取文档级实体列表
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取知识库中的文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 构建文档实体列表
        document_entities = []
        for doc in documents:
            entities = knowledge_graph_service.get_document_entities(db, doc.id)
            document_entities.append({
                "id": doc.id,
                "title": doc.title,
                "entityCount": len(entities),
                "relationCount": len(knowledge_graph_service.get_document_relationships(db, doc.id)),
                "entities": entities
            })
        
        # 排序
        if sort_by == "name":
            document_entities.sort(key=lambda x: x.get("title", ""), reverse=sort_order == "desc")
        elif sort_by == "entityCount":
            document_entities.sort(key=lambda x: x.get("entityCount", 0), reverse=sort_order == "desc")
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_documents = document_entities[start_idx:end_idx]
        
        return {
            "data": paginated_documents,
            "total": len(document_entities),
            "page": page,
            "page_size": page_size,
            "knowledge_base_id": knowledge_base_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档级实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档级实体失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/documents/{document_id}/graph")
async def get_document_graph(
    knowledge_base_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档级图谱数据
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 验证文档存在且属于该知识库
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).first()
        
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在或不属于该知识库")
        
        graph_data = knowledge_graph_service.get_document_graph_data(db, document_id)
        return graph_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档级图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档级图谱失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/stats/document")
async def get_document_level_stats(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档级统计数据
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取知识库中的文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 统计实体和关系
        total_entities = 0
        total_relationships = 0
        entity_types = {}
        
        for doc in documents:
            entities = knowledge_graph_service.get_document_entities(db, doc.id)
            relationships = knowledge_graph_service.get_document_relationships(db, doc.id)
            
            total_entities += len(entities)
            total_relationships += len(relationships)
            
            # 统计实体类型
            for entity in entities:
                entity_type = entity.get("type", "未知")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        return {
            "documentCount": len(documents),
            "entityCount": total_entities,
            "relationCount": total_relationships,
            "avgEntitiesPerDoc": round(total_entities / len(documents), 2) if documents else 0,
            "entityTypes": [
                {"type": type_name, "count": count}
                for type_name, count in entity_types.items()
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档级统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档级统计失败: {str(e)}")


# 知识库级API
@router.get("/knowledge-bases/{knowledge_base_id}/graph")
async def get_knowledge_base_graph(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识库级图谱数据
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        graph_data = knowledge_graph_service.get_knowledge_base_graph_data(db, knowledge_base_id)
        return graph_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库级图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库级图谱失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/stats")
async def get_knowledge_base_level_stats(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识库级统计数据
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取知识库中的文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 统计实体和关系
        total_entities = 0
        unique_entities = set()
        total_relationships = 0
        entity_types = {}
        document_stats = []
        
        for doc in documents:
            entities = knowledge_graph_service.get_document_entities(db, doc.id)
            relationships = knowledge_graph_service.get_document_relationships(db, doc.id)
            
            doc_entity_count = len(entities)
            doc_relation_count = len(relationships)
            
            total_entities += doc_entity_count
            total_relationships += doc_relation_count
            
            # 统计唯一实体
            for entity in entities:
                entity_key = (entity.get("text"), entity.get("type"))
                unique_entities.add(entity_key)
                
                # 统计实体类型
                entity_type = entity.get("type", "未知")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            # 文档统计
            document_stats.append({
                "docId": doc.id,
                "title": doc.title,
                "entityCount": doc_entity_count,
                "relationCount": doc_relation_count
            })
        
        return {
            "documentCount": len(documents),
            "entityCount": total_entities,
            "uniqueEntityCount": len(unique_entities),
            "relationCount": total_relationships,
            "avgEntitiesPerDoc": round(total_entities / len(documents), 2) if documents else 0,
            "entityTypes": [
                {"type": type_name, "count": count}
                for type_name, count in entity_types.items()
            ],
            "documentStats": document_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库级统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库级统计失败: {str(e)}")


# 全局级API
@router.get("/graph/global")
async def get_global_graph(
    db: Session = Depends(get_db)
):
    """
    获取全局级图谱数据
    """
    try:
        # 获取所有知识库
        knowledge_bases = db.query(KnowledgeBase).all()
        
        # 构建全局图谱数据
        all_nodes = []
        all_edges = []
        
        for kb in knowledge_bases:
            graph_data = knowledge_graph_service.get_knowledge_base_graph_data(db, kb.id)
            if "error" not in graph_data:
                all_nodes.extend(graph_data.get("nodes", []))
                all_edges.extend(graph_data.get("edges", []))
        
        return {
            "nodes": all_nodes,
            "edges": all_edges,
            "statistics": {
                "total_entities": len(all_nodes),
                "total_relationships": len(all_edges),
                "knowledge_base_count": len(knowledge_bases)
            }
        }
        
    except Exception as e:
        logger.error(f"获取全局级图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取全局级图谱失败: {str(e)}")


@router.get("/stats/global")
async def get_global_level_stats(
    db: Session = Depends(get_db)
):
    """
    获取全局级统计数据
    """
    try:
        # 获取所有知识库
        knowledge_bases = db.query(KnowledgeBase).all()
        
        # 统计实体和关系
        total_documents = 0
        total_entities = 0
        unique_entities = set()
        total_relationships = 0
        entity_types = {}
        knowledge_base_stats = []
        
        for kb in knowledge_bases:
            documents = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == kb.id
            ).all()
            
            kb_doc_count = len(documents)
            kb_entity_count = 0
            kb_relation_count = 0
            
            for doc in documents:
                entities = knowledge_graph_service.get_document_entities(db, doc.id)
                relationships = knowledge_graph_service.get_document_relationships(db, doc.id)
                
                doc_entity_count = len(entities)
                doc_relation_count = len(relationships)
                
                kb_entity_count += doc_entity_count
                kb_relation_count += doc_relation_count
                
                # 统计唯一实体
                for entity in entities:
                    entity_key = (entity.get("text"), entity.get("type"))
                    unique_entities.add(entity_key)
                    
                    # 统计实体类型
                    entity_type = entity.get("type", "未知")
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            total_documents += kb_doc_count
            total_entities += kb_entity_count
            total_relationships += kb_relation_count
            
            # 知识库统计
            knowledge_base_stats.append({
                "kbId": kb.id,
                "name": kb.name,
                "documentCount": kb_doc_count,
                "entityCount": kb_entity_count,
                "relationCount": kb_relation_count
            })
        
        return {
            "knowledgeBaseCount": len(knowledge_bases),
            "documentCount": total_documents,
            "entityCount": total_entities,
            "uniqueEntityCount": len(unique_entities),
            "relationCount": total_relationships,
            "avgEntitiesPerDoc": round(total_entities / total_documents, 2) if total_documents else 0,
            "entityTypes": [
                {"type": type_name, "count": count}
                for type_name, count in entity_types.items()
            ],
            "knowledgeBaseStats": knowledge_base_stats
        }
        
    except Exception as e:
        logger.error(f"获取全局级统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取全局级统计失败: {str(e)}")


# 跨层级查询
@router.get("/entities/{entity_id}/hierarchy")
async def get_entity_hierarchy(
    entity_id: int,
    level: str = Query(..., description="层级: fragment, document, knowledge_base, global"),
    db: Session = Depends(get_db)
):
    """
    获取实体的层级关系
    """
    try:
        # 获取实体
        entity = db.query(DocumentEntity).filter(DocumentEntity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        # 获取文档
        document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == entity.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取知识库
        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == document.knowledge_base_id
        ).first()
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 根据层级返回不同的数据
        if level == "fragment":
            # 片段级：返回实体所在的片段信息
            return {
                "entity": {
                    "id": entity.id,
                    "text": entity.entity_text,
                    "type": entity.entity_type,
                    "start_pos": entity.start_pos,
                    "end_pos": entity.end_pos
                },
                "document": {
                    "id": document.id,
                    "title": document.title
                },
                "knowledge_base": {
                    "id": knowledge_base.id,
                    "name": knowledge_base.name
                }
            }
        elif level == "document":
            # 文档级：返回实体所在文档的所有实体
            document_entities = knowledge_graph_service.get_document_entities(db, document.id)
            return {
                "document": {
                    "id": document.id,
                    "title": document.title
                },
                "entities": document_entities,
                "knowledge_base": {
                    "id": knowledge_base.id,
                    "name": knowledge_base.name
                }
            }
        elif level == "knowledge_base":
            # 知识库级：返回实体所在知识库的统计信息
            kb_stats = get_knowledge_base_level_stats(knowledge_base.id, db)
            return {
                "knowledge_base": {
                    "id": knowledge_base.id,
                    "name": knowledge_base.name
                },
                "statistics": kb_stats,
                "entity": {
                    "id": entity.id,
                    "text": entity.entity_text,
                    "type": entity.entity_type
                }
            }
        elif level == "global":
            # 全局级：返回全局统计信息
            global_stats = get_global_level_stats(db)
            return {
                "global_statistics": global_stats,
                "entity": {
                    "id": entity.id,
                    "text": entity.entity_text,
                    "type": entity.entity_type
                },
                "document": {
                    "id": document.id,
                    "title": document.title
                },
                "knowledge_base": {
                    "id": knowledge_base.id,
                    "name": knowledge_base.name
                }
            }
        else:
            raise HTTPException(status_code=400, detail="无效的层级参数")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体层级失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实体层级失败: {str(e)}")


# 层级导航API
@router.get("/knowledge-bases/{knowledge_base_id}/hierarchy/levels")
async def get_hierarchy_levels(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取层级导航信息
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取知识库中的文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 统计各层级的实体数量
        fragment_count = 0
        document_count = len(documents)
        kb_entity_count = 0
        
        for doc in documents:
            entities = knowledge_graph_service.get_document_entities(db, doc.id, distinct=False)
            fragment_count += len(entities)
            kb_entity_count += len(knowledge_graph_service.get_document_entities(db, doc.id))
        
        return {
            "knowledge_base_id": knowledge_base_id,
            "knowledge_base_name": kb.name,
            "levels": [
                {
                    "level": "fragment",
                    "name": "片段级",
                    "count": fragment_count,
                    "description": "查看文本片段内的实体标注"
                },
                {
                    "level": "document",
                    "name": "文档级",
                    "count": document_count,
                    "description": "查看文档内的实体关系"
                },
                {
                    "level": "knowledge_base",
                    "name": "知识库级",
                    "count": kb_entity_count,
                    "description": "查看跨文档的实体聚合"
                },
                {
                    "level": "global",
                    "name": "全局级",
                    "count": 0,  # 全局级需要统计所有知识库
                    "description": "查看跨知识库的全局关系"
                }
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取层级导航信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取层级导航信息失败: {str(e)}")


# 搜索API
@router.get("/search/fragment")
async def search_fragment_entities(
    query: str = Query(..., description="搜索关键词"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    db: Session = Depends(get_db)
):
    """
    搜索片段级实体
    """
    try:
        results = knowledge_graph_service.search_entities(db, query, knowledge_base_id=knowledge_base_id)
        return {
            "data": results,
            "total": len(results),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"搜索片段级实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索片段级实体失败: {str(e)}")


@router.get("/search/document")
async def search_document_entities(
    query: str = Query(..., description="搜索关键词"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    db: Session = Depends(get_db)
):
    """
    搜索文档级实体
    """
    try:
        results = knowledge_graph_service.search_entities(db, query, knowledge_base_id=knowledge_base_id)
        return {
            "data": results,
            "total": len(results),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"搜索文档级实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索文档级实体失败: {str(e)}")


@router.get("/search/knowledge-base")
async def search_knowledge_base_entities(
    query: str = Query(..., description="搜索关键词"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    db: Session = Depends(get_db)
):
    """
    搜索知识库级实体
    """
    try:
        results = knowledge_graph_service.search_entities(db, query, knowledge_base_id=knowledge_base_id)
        return {
            "data": results,
            "total": len(results),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"搜索知识库级实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索知识库级实体失败: {str(e)}")


@router.get("/search/global")
async def search_global_entities(
    query: str = Query(..., description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    搜索全局级实体
    """
    try:
        results = knowledge_graph_service.search_entities(db, query)
        return {
            "data": results,
            "total": len(results),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"搜索全局级实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索全局级实体失败: {str(e)}")
