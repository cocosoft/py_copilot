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

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import (
    KnowledgeDocument, KnowledgeBase, DocumentEntity, EntityRelationship, 
    DocumentChunk, ChunkEntity, EntityExtractionTask, ChunkExtractionStatus
)
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

    统计知识库内所有片段的实体数量（最细粒度）
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

        # 统计片段级实体（ChunkEntity）
        total_chunks = 0
        total_entities = 0
        entity_types = {}
        document_stats = []

        for doc in documents:
            # 获取文档的片段
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc.id
            ).all()

            doc_chunk_count = len(chunks)
            doc_entity_count = 0

            for chunk in chunks:
                # 统计片段中的实体
                chunk_entities = db.query(ChunkEntity).filter(
                    ChunkEntity.chunk_id == chunk.id
                ).all()

                doc_entity_count += len(chunk_entities)

                # 统计实体类型
                for entity in chunk_entities:
                    entity_type = entity.entity_type or "未知"
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            total_chunks += doc_chunk_count
            total_entities += doc_entity_count

            document_stats.append({
                "docId": doc.id,
                "title": doc.title,
                "chunkCount": doc_chunk_count,
                "entityCount": doc_entity_count
            })

        return {
            "documentCount": len(documents),
            "chunkCount": total_chunks,
            "entityCount": total_entities,
            "avgEntitiesPerChunk": round(total_entities / total_chunks, 2) if total_chunks else 0,
            "entityTypes": [
                {"type": type_name, "count": count}
                for type_name, count in entity_types.items()
            ],
            "documentStats": document_stats
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

    统计知识库内所有文档的实体数量（文档级去重）
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

        # 统计文档级实体（DocumentEntity）
        total_entities = 0
        total_relationships = 0
        entity_types = {}
        document_stats = []

        for doc in documents:
            # 统计文档中的实体
            entities = db.query(DocumentEntity).filter(
                DocumentEntity.document_id == doc.id
            ).all()

            # 统计文档中的关系
            relationships = db.query(EntityRelationship).filter(
                EntityRelationship.document_id == doc.id
            ).count()

            doc_entity_count = len(entities)

            # 统计实体类型
            for entity in entities:
                entity_type = entity.entity_type or "未知"
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            total_entities += doc_entity_count
            total_relationships += relationships

            document_stats.append({
                "docId": doc.id,
                "title": doc.title,
                "entityCount": doc_entity_count,
                "relationCount": relationships
            })

        return {
            "documentCount": len(documents),
            "entityCount": total_entities,
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

        if "error" in graph_data:
            raise HTTPException(status_code=500, detail=graph_data["error"])

        return {
            "code": 200,
            "message": "success",
            "data": graph_data
        }
        
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


# ============================================================================
# 层级视图逻辑修复 - 新增API接口
# 任务编号: Phase3-Week10
# 说明: 为支持各层级正确的数据筛选，新增以下4个API接口
# ============================================================================

@router.get("/knowledge-bases/{knowledge_base_id}/documents")
async def get_documents_list(
    knowledge_base_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取知识库的文档列表

    返回文档基本信息及实体数量统计，用于文档选择器
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 构建查询
        query = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        )

        # 搜索过滤
        if search:
            query = query.filter(KnowledgeDocument.title.ilike(f"%{search}%"))

        # 获取总数
        total = query.count()

        # 分页
        documents = query.order_by(KnowledgeDocument.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        # 构建响应数据
        document_list = []
        for doc in documents:
            # 统计文档的实体数量
            entity_count = db.query(DocumentEntity).filter(
                DocumentEntity.document_id == doc.id
            ).count()

            # 统计文档的关系数量
            relation_count = db.query(EntityRelationship).filter(
                EntityRelationship.document_id == doc.id
            ).count()

            # 数据一致性检查：如果实体数为0，关系数也应该为0
            # 因为关系是连接两个实体的，没有实体就不可能有关系
            if entity_count == 0:
                relation_count = 0
            else:
                # 关系数不应该超过理论最大值（完全图）
                max_relations = entity_count * (entity_count - 1) // 2
                if relation_count > max_relations:
                    logger.warning(f"文档 {doc.id} 关系数({relation_count})超过理论最大值({max_relations})，可能存在数据异常")
                    # 重新计算有效关系数（只统计两端实体都存在的关系）
                    valid_relations = db.query(EntityRelationship).filter(
                        EntityRelationship.document_id == doc.id,
                        EntityRelationship.source_id.in_(
                            db.query(DocumentEntity.id).filter(DocumentEntity.document_id == doc.id)
                        ),
                        EntityRelationship.target_id.in_(
                            db.query(DocumentEntity.id).filter(DocumentEntity.document_id == doc.id)
                        )
                    ).count()
                    relation_count = valid_relations

            # 统计文档的片段数量
            chunk_count = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc.id
            ).count()

            document_list.append({
                "id": doc.id,
                "title": doc.title,
                "file_type": doc.file_type,
                "entity_count": entity_count,
                "relation_count": relation_count,
                "chunk_count": chunk_count,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "list": document_list,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/documents/{document_id}/chunks")
async def get_document_chunks_list(
    knowledge_base_id: int,
    document_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取文档的片段列表

    返回片段基本信息及实体数量统计，用于片段选择器
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

        # 获取片段列表
        query = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        )

        # 获取总数
        total = query.count()

        # 分页
        chunks = query.order_by(DocumentChunk.chunk_index.asc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        # 构建响应数据
        chunk_list = []
        for chunk in chunks:
            # 统计片段的实体数量
            entity_count = db.query(ChunkEntity).filter(
                ChunkEntity.chunk_id == chunk.id
            ).count()

            chunk_list.append({
                "id": chunk.id,
                "text": chunk.chunk_text,  # 返回完整文本
                "text_preview": chunk.chunk_text[:200] + "..." if len(chunk.chunk_text) > 200 else chunk.chunk_text,
                "start_position": chunk.start_pos,
                "end_position": chunk.end_pos,
                "entity_count": entity_count,
                "index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "list": chunk_list,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取片段列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取片段列表失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/chunks/{chunk_id}/entities")
async def get_chunk_entities_detail(
    knowledge_base_id: int,
    chunk_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取指定片段的实体列表

    返回片段中包含的所有实体，用于片段级视图
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 验证片段存在
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="片段不存在")

        # 验证片段所属文档属于该知识库
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == chunk.document_id,
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="片段不属于该知识库")

        # 获取片段的实体列表
        query = db.query(ChunkEntity).filter(ChunkEntity.chunk_id == chunk_id)

        # 获取总数
        total = query.count()

        # 分页
        entities = query.order_by(ChunkEntity.start_pos.asc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        # 构建响应数据
        entity_list = []
        for entity in entities:
            entity_list.append({
                "id": entity.id,
                "text": entity.entity_text,
                "type": entity.entity_type,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos,
                "confidence": entity.confidence,
                "context": entity.context
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "list": entity_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "chunk_id": chunk_id,
                "chunk_index": chunk.chunk_index
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取片段实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取片段实体失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/documents/{document_id}/entities")
async def get_document_entities_detail(
    knowledge_base_id: int,
    document_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    db: Session = Depends(get_db)
):
    """
    获取指定文档的实体列表

    返回文档中包含的所有实体（去重），用于文档级视图
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

        # 构建查询
        query = db.query(DocumentEntity).filter(DocumentEntity.document_id == document_id)

        # 实体类型过滤
        if entity_type:
            query = query.filter(DocumentEntity.entity_type == entity_type)

        # 获取总数
        total = query.count()

        # 分页
        entities = query.order_by(DocumentEntity.start_pos.asc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        # 构建响应数据
        entity_list = []
        for entity in entities:
            entity_list.append({
                "id": entity.id,
                "text": entity.entity_text,
                "type": entity.entity_type,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos,
                "confidence": entity.confidence,
                "status": entity.status,
                "kb_entity_id": entity.kb_entity_id,
                "global_entity_id": entity.global_entity_id
            })

        # 获取实体类型分布
        type_distribution = db.query(
            DocumentEntity.entity_type,
            func.count(DocumentEntity.id).label("count")
        ).filter(DocumentEntity.document_id == document_id).group_by(
            DocumentEntity.entity_type
        ).all()

        return {
            "code": 200,
            "message": "success",
            "data": {
                "list": entity_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "document_id": document_id,
                "entity_types": [
                    {"type": t[0], "count": t[1]} for t in type_distribution
                ]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档实体失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/documents/{document_id}/relations")
async def get_document_relations_detail(
    knowledge_base_id: int,
    document_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    relation_type: Optional[str] = Query(None, description="关系类型过滤"),
    db: Session = Depends(get_db)
):
    """
    获取指定文档的关系列表

    返回文档中包含的所有实体关系，用于文档级关系管理
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

        # 获取文档的所有关系
        knowledge_graph_service = KnowledgeGraphService()
        relationships = knowledge_graph_service.get_document_relationships(db, document_id)

        # 关系类型过滤
        if relation_type:
            relationships = [r for r in relationships if r.get("relation_type") == relation_type]

        # 计算总数
        total = len(relationships)

        # 分页
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paged_relationships = relationships[start_index:end_index]

        # 构建响应数据
        relation_list = []
        for rel in paged_relationships:
            # 获取源实体和目标实体的文本
            source = rel.get("source", {})
            target = rel.get("target", {})
            relation_list.append({
                "id": rel.get("id"),
                "source_entity": source.get("text", "未知"),
                "target_entity": target.get("text", "未知"),
                "relation_type": rel.get("relationship_type", "未知"),
                "confidence": rel.get("confidence", 0),
                "properties": rel.get("properties", {})
            })

        # 获取关系类型分布
        type_counts = {}
        for rel in relationships:
            rel_type = rel.get("relationship_type", "未知")
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

        return {
            "code": 200,
            "message": "success",
            "data": {
                "list": relation_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "document_id": document_id,
                "relation_types": [
                    {"type": t, "count": c} for t, c in type_counts.items()
                ]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档关系失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档关系失败: {str(e)}")


@router.delete("/knowledge-bases/{knowledge_base_id}/relations/{relation_id}")
async def delete_relation(
    knowledge_base_id: int,
    relation_id: int,
    db: Session = Depends(get_db)
):
    """
    删除关系

    删除指定的实体关系
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 查找关系
        relation = db.query(EntityRelationship).filter(
            EntityRelationship.id == relation_id
        ).first()

        if not relation:
            raise HTTPException(status_code=404, detail="关系不存在")

        # 验证关系所属的文档是否在该知识库中
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == relation.document_id,
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).first()

        if not doc:
            raise HTTPException(status_code=403, detail="无权操作该关系")

        # 删除关系
        db.delete(relation)
        db.commit()

        return {
            "code": 200,
            "message": "关系删除成功",
            "data": {"id": relation_id}
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除关系失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除关系失败: {str(e)}")


# ============================================================================
# 大文件实体识别改造 - 新增API接口
# 任务编号: 大文件实体识别改造方案
# 说明: 支持片段级实体重新识别和文档级实体聚合
# ============================================================================

@router.post("/knowledge-bases/{knowledge_base_id}/chunks/{chunk_id}/extract-entities")
async def extract_chunk_entities(
    knowledge_base_id: int,
    chunk_id: int,
    db: Session = Depends(get_db)
):
    """
    对指定片段进行实体识别（重新识别）

    适用于：
    1. 大文件初次导入时部分片段识别失败
    2. 用户需要重新识别某个片段
    3. 增量更新片段实体

    Args:
        knowledge_base_id: 知识库ID
        chunk_id: 片段ID

    Returns:
        识别结果和统计信息
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 验证片段存在
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="片段不存在")

        # 验证片段所属文档属于该知识库
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == chunk.document_id,
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="片段不属于该知识库")

        # 获取文档的所有片段数
        total_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == chunk.document_id
        ).count()

        # 查找或创建任务记录
        # 优先查找最近24小时内创建的任务，避免重复创建
        from datetime import datetime, timedelta
        time_threshold = datetime.utcnow() - timedelta(hours=24)

        task = db.query(EntityExtractionTask).filter(
            EntityExtractionTask.document_id == chunk.document_id,
            EntityExtractionTask.created_at >= time_threshold
        ).order_by(EntityExtractionTask.created_at.desc()).first()

        if not task or task.status == 'completed':
            # 创建新任务
            task = EntityExtractionTask(
                knowledge_base_id=knowledge_base_id,
                document_id=chunk.document_id,
                status='processing',
                task_type='retry',
                total_chunks=total_chunks,
                processed_chunks=0,
                started_at=func.now()
            )
            db.add(task)
            db.flush()

        # 查找或创建片段状态记录
        chunk_status = db.query(ChunkExtractionStatus).filter(
            ChunkExtractionStatus.chunk_id == chunk_id
        ).first()

        if not chunk_status:
            chunk_status = ChunkExtractionStatus(
                task_id=task.id,
                chunk_id=chunk_id,
                document_id=chunk.document_id,
                status='processing'
            )
            db.add(chunk_status)
        else:
            chunk_status.status = 'processing'
            chunk_status.retry_count += 1

        db.commit()

        # 导入并调用ChunkEntityService进行实体识别
        from app.services.knowledge.chunk.chunk_entity_service import ChunkEntityService

        service = ChunkEntityService(db)
        result = service.extract_chunk_entities(chunk_id, knowledge_base_id)

        # 更新片段状态
        if "error" in result:
            chunk_status.status = 'failed'
            chunk_status.error_message = result["error"]
            task.failed_chunks += 1
        else:
            chunk_status.status = 'completed'
            chunk_status.entity_count = result.get("entity_count", 0)
            chunk_status.processed_at = func.now()
            task.successful_chunks += 1
            task.chunk_entity_count += result.get("entity_count", 0)

        # 更新任务进度
        task.processed_chunks += 1
        is_task_completed = task.processed_chunks >= task.total_chunks

        if is_task_completed:
            task.status = 'completed'
            task.completed_at = func.now()

        db.commit()

        # 如果任务完成，触发实体聚合
        if is_task_completed and "error" not in result:
            try:
                from app.services.knowledge.document.document_entity_service import DocumentEntityService
                doc_entity_service = DocumentEntityService(db)

                # 直接执行实体聚合，不检查文档状态
                agg_result = doc_entity_service.aggregate_chunk_entities(document_id=chunk.document_id)

                if agg_result.get("entities_created", 0) > 0:
                    task.document_entity_count = agg_result.get("entities_created", 0)
                    db.commit()
                    logger.info(f"任务 {task.id} 实体聚合完成，文档级实体: {task.document_entity_count}")
            except Exception as e:
                logger.warning(f"实体聚合失败: {e}")

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "code": 200,
            "message": "实体识别成功",
            "data": {
                "chunk_id": chunk_id,
                "document_id": chunk.document_id,
                "entity_count": result.get("entity_count", 0),
                "entities": result.get("entities", []),
                "processing_time": result.get("processing_time", 0)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"片段实体识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"片段实体识别失败: {str(e)}")


@router.post("/knowledge-bases/{knowledge_base_id}/documents/{document_id}/aggregate-entities")
async def aggregate_document_entities(
    knowledge_base_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    聚合文档所有片段的实体到文档级

    聚合逻辑：
    1. 收集所有片段的实体（从ChunkEntity表）
    2. 按entity_text + entity_type去重
    3. 统计每个实体在文档中的出现次数
    4. 生成DocumentEntity记录
    5. 支持增量更新（只处理未聚合的实体）

    Args:
        knowledge_base_id: 知识库ID
        document_id: 文档ID

    Returns:
        聚合结果和统计信息
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

        # 导入并调用DocumentProcessingService进行实体聚合
        from app.services.knowledge.document.document_processing_service import DocumentProcessingService

        service = DocumentProcessingService(db)
        result = service.process_entity_aggregation(document_id)

        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("message", "实体聚合失败"))

        return {
            "code": 200,
            "message": "实体聚合成功",
            "data": {
                "document_id": document_id,
                "chunk_entity_count": result.get("chunk_entity_count", 0),
                "document_entity_count": result.get("document_entity_count", 0),
                "merged_groups": result.get("merged_groups", 0),
                "status": result.get("status", "unknown")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档实体聚合失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档实体聚合失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/documents/{document_id}/extraction-status")
async def get_document_extraction_status(
    knowledge_base_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档的实体识别状态

    返回文档实体识别的整体状态，包括：
    - 总片段数
    - 已处理片段数
    - 失败片段数
    - 实体统计

    Args:
        knowledge_base_id: 知识库ID
        document_id: 文档ID

    Returns:
        识别状态信息
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

        # 获取文档的片段统计
        total_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).count()

        # 首先尝试从任务表获取状态
        task = db.query(EntityExtractionTask).filter(
            EntityExtractionTask.document_id == document_id
        ).order_by(EntityExtractionTask.created_at.desc()).first()

        if task:
            # 使用任务表的数据
            progress = (task.processed_chunks / task.total_chunks * 100) if task.total_chunks > 0 else 0
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "document_id": document_id,
                    "status": task.status,
                    "progress": round(progress, 2),
                    "total_chunks": task.total_chunks,
                    "processed_chunks": task.processed_chunks,
                    "successful_chunks": task.successful_chunks,
                    "failed_chunks": task.failed_chunks,
                    "chunk_entity_count": task.chunk_entity_count,
                    "document_entity_count": task.document_entity_count,
                    "task_type": task.task_type,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "error_message": task.error_message
                }
            }

        # 如果没有任务记录，从实体表统计
        from sqlalchemy import distinct
        processed_chunks = db.query(distinct(ChunkEntity.chunk_id)).filter(
            ChunkEntity.document_id == document_id
        ).count()

        # 获取实体统计
        chunk_entity_count = db.query(ChunkEntity).filter(
            ChunkEntity.document_id == document_id
        ).count()

        document_entity_count = db.query(DocumentEntity).filter(
            DocumentEntity.document_id == document_id
        ).count()

        # 计算进度
        progress = (processed_chunks / total_chunks * 100) if total_chunks > 0 else 0

        # 确定状态
        if processed_chunks == 0:
            status = "pending"
        elif processed_chunks < total_chunks:
            status = "processing"
        else:
            status = "completed"

        return {
            "code": 200,
            "message": "success",
            "data": {
                "document_id": document_id,
                "status": status,
                "progress": round(progress, 2),
                "total_chunks": total_chunks,
                "processed_chunks": processed_chunks,
                "successful_chunks": processed_chunks,
                "failed_chunks": total_chunks - processed_chunks,
                "chunk_entity_count": chunk_entity_count,
                "document_entity_count": document_entity_count,
                "task_type": None,
                "created_at": None,
                "started_at": None,
                "completed_at": None,
                "error_message": None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档识别状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档识别状态失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/extraction-tasks")
async def get_extraction_tasks(
    knowledge_base_id: int,
    status: Optional[str] = Query(None, description="任务状态过滤: pending, processing, completed, failed"),
    task_type: Optional[str] = Query(None, description="任务类型过滤: full, incremental, retry"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取实体识别任务列表

    用于实体识别管理页面，显示所有识别任务

    Args:
        knowledge_base_id: 知识库ID
        status: 状态过滤
        task_type: 任务类型过滤
        page: 页码
        page_size: 每页数量

    Returns:
        任务列表和分页信息
    """
    try:
        # 验证知识库存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 构建查询
        query = db.query(EntityExtractionTask).filter(
            EntityExtractionTask.knowledge_base_id == knowledge_base_id
        )

        # 应用过滤
        if status:
            query = query.filter(EntityExtractionTask.status == status)
        if task_type:
            query = query.filter(EntityExtractionTask.task_type == task_type)

        # 排序（最新的在前）
        query = query.order_by(EntityExtractionTask.created_at.desc())

        # 分页
        total = query.count()
        tasks = query.offset((page - 1) * page_size).limit(page_size).all()

        # 获取文档标题
        document_ids = [task.document_id for task in tasks]
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id.in_(document_ids)
        ).all()
        doc_map = {doc.id: doc.title for doc in documents}

        # 格式化结果
        task_list = []
        for task in tasks:
            progress = (task.processed_chunks / task.total_chunks * 100) if task.total_chunks > 0 else 0
            task_list.append({
                "id": task.id,
                "document_id": task.document_id,
                "document_title": doc_map.get(task.document_id, "未知文档"),
                "status": task.status,
                "task_type": task.task_type,
                "progress": round(progress, 2),
                "total_chunks": task.total_chunks,
                "processed_chunks": task.processed_chunks,
                "successful_chunks": task.successful_chunks,
                "failed_chunks": task.failed_chunks,
                "chunk_entity_count": task.chunk_entity_count,
                "document_entity_count": task.document_entity_count,
                "error_message": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "list": task_list,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/knowledge-bases/{knowledge_base_id}/documents/{document_id}/re-extract-all")
async def re_extract_all_chunks(
    knowledge_base_id: int,
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    重新识别文档的所有片段

    用于批量重新识别整个文档的所有片段

    Args:
        knowledge_base_id: 知识库ID
        document_id: 文档ID

    Returns:
        任务创建结果
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

        # 获取文档的所有片段
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()

        if not chunks:
            raise HTTPException(status_code=400, detail="文档没有片段")

        # 检查是否已有进行中的任务
        existing_task = db.query(EntityExtractionTask).filter(
            EntityExtractionTask.document_id == document_id,
            EntityExtractionTask.status.in_(['pending', 'processing'])
        ).first()

        if existing_task:
            raise HTTPException(status_code=400, detail="该文档已有进行中的识别任务")

        # 创建新任务
        task = EntityExtractionTask(
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            status='pending',
            task_type='full',
            total_chunks=len(chunks),
            processed_chunks=0,
            successful_chunks=0,
            failed_chunks=0
        )
        db.add(task)
        db.flush()

        # 为每个片段创建状态记录
        for chunk in chunks:
            chunk_status = ChunkExtractionStatus(
                task_id=task.id,
                chunk_id=chunk.id,
                document_id=document_id,
                status='pending'
            )
            db.add(chunk_status)

        db.commit()

        # 启动后台任务执行识别
        background_tasks.add_task(
            _process_extraction_task,
            task.id,
            knowledge_base_id,
            document_id
        )

        return {
            "code": 200,
            "message": "任务创建成功，正在后台执行",
            "data": {
                "task_id": task.id,
                "document_id": document_id,
                "total_chunks": len(chunks),
                "status": "processing"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建重新识别任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建重新识别任务失败: {str(e)}")


# ============================================================================
# 后台任务处理函数
# ============================================================================

def _process_extraction_task(task_id: int, knowledge_base_id: int, document_id: int):
    """
    后台处理实体识别任务

    Args:
        task_id: 任务ID
        knowledge_base_id: 知识库ID
        document_id: 文档ID
    """
    from app.core.database import SessionLocal
    from app.services.knowledge.chunk.chunk_entity_service import ChunkEntityService

    db = SessionLocal()
    try:
        # 获取任务
        task = db.query(EntityExtractionTask).filter(EntityExtractionTask.id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return

        # 更新任务状态为处理中
        task.status = 'processing'
        task.started_at = func.now()
        db.commit()

        logger.info(f"开始处理任务 {task_id}, 文档 {document_id}, 共 {task.total_chunks} 个片段")

        # 获取所有待处理的片段状态
        chunk_statuses = db.query(ChunkExtractionStatus).filter(
            ChunkExtractionStatus.task_id == task_id,
            ChunkExtractionStatus.status == 'pending'
        ).all()

        service = ChunkEntityService(db)
        total_entities = 0

        # 逐个处理片段
        for i, chunk_status in enumerate(chunk_statuses):
            try:
                # 检查任务是否被暂停或取消
                db.refresh(task)
                if task.status == 'paused':
                    logger.info(f"任务 {task_id} 已暂停，当前进度: {task.processed_chunks}/{task.total_chunks}")
                    return  # 退出处理，保留当前进度

                if task.status == 'failed':
                    logger.info(f"任务 {task_id} 已被取消，停止处理")
                    return  # 任务被取消

                # 更新片段状态为处理中
                chunk_status.status = 'processing'
                db.commit()

                # 执行实体识别
                result = service.extract_chunk_entities(chunk_status.chunk_id, knowledge_base_id)

                if "error" in result:
                    chunk_status.status = 'failed'
                    chunk_status.error_message = result["error"]
                    task.failed_chunks += 1
                    logger.warning(f"片段 {chunk_status.chunk_id} 识别失败: {result['error']}")
                else:
                    chunk_status.status = 'completed'
                    chunk_status.entity_count = result.get("entity_count", 0)
                    chunk_status.processed_at = func.now()
                    task.successful_chunks += 1
                    task.chunk_entity_count += result.get("entity_count", 0)
                    total_entities += result.get("entity_count", 0)
                    logger.debug(f"片段 {chunk_status.chunk_id} 识别完成，提取 {result.get('entity_count', 0)} 个实体")

            except Exception as e:
                logger.error(f"处理片段 {chunk_status.chunk_id} 时出错: {e}")
                chunk_status.status = 'failed'
                chunk_status.error_message = str(e)
                task.failed_chunks += 1

            # 更新任务进度
            task.processed_chunks += 1
            db.commit()

        # 任务完成，执行实体聚合
        try:
            from app.services.knowledge.document.document_entity_service import DocumentEntityService
            doc_entity_service = DocumentEntityService(db)

            # 直接执行实体聚合，不检查文档状态
            agg_result = doc_entity_service.aggregate_chunk_entities(document_id=document_id)

            if agg_result.get("entities_created", 0) > 0:
                task.document_entity_count = agg_result.get("entities_created", 0)
                logger.info(f"任务 {task_id} 实体聚合完成，文档级实体: {task.document_entity_count}")
            else:
                logger.warning(f"任务 {task_id} 没有可聚合的实体: {agg_result.get('message')}")
        except Exception as e:
            logger.error(f"任务 {task_id} 实体聚合时出错: {e}")

        # 更新任务状态为完成
        task.status = 'completed'
        task.completed_at = func.now()
        db.commit()

        logger.info(f"任务 {task_id} 处理完成，成功: {task.successful_chunks}, 失败: {task.failed_chunks}, 实体: {task.chunk_entity_count}")

    except Exception as e:
        logger.error(f"处理任务 {task_id} 时出错: {e}")
        # 更新任务状态为失败
        if task:
            task.status = 'failed'
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()
