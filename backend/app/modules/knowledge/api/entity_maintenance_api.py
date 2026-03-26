"""
实体维护API

提供用户对实体进行查看、编辑、合并、删除等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import (
    DocumentEntity, KBEntity, GlobalEntity, KnowledgeDocument
)
from app.services.knowledge.graph.knowledge_graph_service import KnowledgeGraphService

router = APIRouter(tags=["实体维护"])


# ============ 请求/响应模型 ============

class EntityUpdateRequest(BaseModel):
    """实体更新请求"""
    entity_text: Optional[str] = None
    entity_type: Optional[str] = None
    aliases: Optional[List[str]] = None


class EntityMergeRequest(BaseModel):
    """实体合并请求"""
    source_entity_ids: List[int]
    target_entity_id: int
    level: str  # 'document', 'kb', 'global'


class EntityFeedbackRequest(BaseModel):
    """实体反馈请求"""
    entity_id: int
    level: str
    issue_type: str  # 'wrong_type', 'wrong_text', 'should_merge', 'should_delete'
    suggestion: Optional[str] = None


class EntityCreateRequest(BaseModel):
    """创建实体请求"""
    entity_text: str
    entity_type: str
    document_id: int
    start_pos: int = 0
    end_pos: int = 0
    confidence: float = 1.0


class EntityStatusUpdateRequest(BaseModel):
    """实体状态更新请求"""
    entity_ids: List[int]
    status: str  # 'pending', 'confirmed', 'rejected', 'modified'


# ============ 实体查询接口 ============

@router.get("/document-entities/{document_id}")
def get_document_entities(
    document_id: int,
    entity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    获取文档的所有实体
    
    Args:
        document_id: 文档ID
        entity_type: 可选的实体类型过滤
        page: 页码
        page_size: 每页数量
    """
    query = db.query(DocumentEntity).filter(DocumentEntity.document_id == document_id)
    
    if entity_type:
        query = query.filter(DocumentEntity.entity_type == entity_type)
    
    total = query.count()
    entities = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "entities": [
            {
                "id": e.id,
                "text": e.entity_text,
                "type": e.entity_type,
                "start_pos": e.start_pos,
                "end_pos": e.end_pos,
                "confidence": e.confidence,
                "status": e.status,
                "kb_entity_id": e.kb_entity_id,
                "global_entity_id": e.global_entity_id
            }
            for e in entities
        ]
    }


@router.get("/kb-entities/{knowledge_base_id}")
def get_kb_entities(
    knowledge_base_id: int,
    entity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取知识库的所有KB级实体"""
    query = db.query(KBEntity).filter(KBEntity.knowledge_base_id == knowledge_base_id)
    
    if entity_type:
        query = query.filter(KBEntity.entity_type == entity_type)
    
    total = query.count()
    entities = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "entities": [
            {
                "id": e.id,
                "canonical_name": e.canonical_name,
                "type": e.entity_type,
                "aliases": e.aliases,
                "document_count": e.document_count,
                "occurrence_count": e.occurrence_count,
                "global_entity_id": e.global_entity_id
            }
            for e in entities
        ]
    }


@router.get("/global-entities")
def get_global_entities(
    entity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取所有全局级实体"""
    query = db.query(GlobalEntity)
    
    if entity_type:
        query = query.filter(GlobalEntity.entity_type == entity_type)
    
    total = query.count()
    entities = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "entities": [
            {
                "id": e.id,
                "global_name": e.global_name,
                "type": e.entity_type,
                "all_aliases": e.all_aliases,
                "kb_count": e.kb_count,
                "document_count": e.document_count
            }
            for e in entities
        ]
    }


@router.get("/entity-detail/{level}/{entity_id}")
def get_entity_detail(
    level: str,  # 'document', 'kb', 'global'
    entity_id: int,
    db: Session = Depends(get_db)
):
    """获取实体详细信息"""
    if level == 'document':
        entity = db.query(DocumentEntity).filter(DocumentEntity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        # 获取关联文档信息
        document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == entity.document_id).first()
        
        return {
            "id": entity.id,
            "level": "document",
            "text": entity.entity_text,
            "type": entity.entity_type,
            "start_pos": entity.start_pos,
            "end_pos": entity.end_pos,
            "confidence": entity.confidence,
            "status": entity.status,
            "document_id": entity.document_id,
            "document_title": document.title if document else None,
            "kb_entity_id": entity.kb_entity_id,
            "global_entity_id": entity.global_entity_id
        }
    
    elif level == 'kb':
        entity = db.query(KBEntity).filter(KBEntity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        # 获取关联的文档实体
        doc_entities = db.query(DocumentEntity).filter(DocumentEntity.kb_entity_id == entity_id).all()
        
        return {
            "id": entity.id,
            "level": "kb",
            "canonical_name": entity.canonical_name,
            "type": entity.entity_type,
            "aliases": entity.aliases,
            "document_count": entity.document_count,
            "occurrence_count": entity.occurrence_count,
            "knowledge_base_id": entity.knowledge_base_id,
            "global_entity_id": entity.global_entity_id,
            "document_entities": [
                {"id": de.id, "text": de.entity_text, "document_id": de.document_id}
                for de in doc_entities[:20]  # 限制返回数量
            ]
        }
    
    elif level == 'global':
        entity = db.query(GlobalEntity).filter(GlobalEntity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        # 获取关联的KB实体
        kb_entities = db.query(KBEntity).filter(KBEntity.global_entity_id == entity_id).all()
        
        return {
            "id": entity.id,
            "level": "global",
            "global_name": entity.global_name,
            "type": entity.entity_type,
            "all_aliases": entity.all_aliases,
            "kb_count": entity.kb_count,
            "document_count": entity.document_count,
            "kb_entities": [
                {"id": ke.id, "canonical_name": ke.canonical_name, "knowledge_base_id": ke.knowledge_base_id}
                for ke in kb_entities[:20]
            ]
        }
    
    else:
        raise HTTPException(status_code=400, detail="无效的层级")


# ============ 实体编辑接口 ============

@router.put("/document-entity/{entity_id}")
def update_document_entity(
    entity_id: int,
    request: EntityUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新文档级实体"""
    entity = db.query(DocumentEntity).filter(DocumentEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    if request.entity_text:
        entity.entity_text = request.entity_text
    if request.entity_type:
        entity.entity_type = request.entity_type
    
    db.commit()
    
    return {
        "success": True,
        "message": "实体已更新",
        "entity": {
            "id": entity.id,
            "text": entity.entity_text,
            "type": entity.entity_type
        }
    }


@router.put("/kb-entity/{entity_id}")
def update_kb_entity(
    entity_id: int,
    request: EntityUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新KB级实体"""
    entity = db.query(KBEntity).filter(KBEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    if request.entity_text:
        entity.canonical_name = request.entity_text
    if request.entity_type:
        entity.entity_type = request.entity_type
    if request.aliases is not None:
        entity.aliases = request.aliases
    
    db.commit()
    
    return {
        "success": True,
        "message": "KB实体已更新",
        "entity": {
            "id": entity.id,
            "canonical_name": entity.canonical_name,
            "type": entity.entity_type,
            "aliases": entity.aliases
        }
    }


# ============ 实体合并接口 ============

@router.post("/merge-document-entities")
def merge_document_entities(
    request: EntityMergeRequest,
    db: Session = Depends(get_db)
):
    """
    合并文档级实体到KB级实体
    
    将多个相似的文档实体合并为一个KB实体
    """
    if request.level != 'document':
        raise HTTPException(status_code=400, detail="此接口仅支持文档级实体合并")
    
    # 获取目标实体
    target = db.query(DocumentEntity).filter(DocumentEntity.id == request.target_entity_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标实体不存在")
    
    # 获取源实体
    sources = db.query(DocumentEntity).filter(
        DocumentEntity.id.in_(request.source_entity_ids)
    ).all()
    
    if len(sources) != len(request.source_entity_ids):
        raise HTTPException(status_code=404, detail="部分源实体不存在")
    
    # 创建或获取KB实体
    kb_entity = db.query(KBEntity).filter(
        KBEntity.knowledge_base_id == target.document.knowledge_base_id,
        KBEntity.canonical_name == target.entity_text
    ).first()
    
    if not kb_entity:
        # 创建新的KB实体
        from app.modules.knowledge.models.knowledge_document import KBEntity
        
        # 收集所有别名
        all_texts = set([target.entity_text] + [s.entity_text for s in sources])
        aliases = list(all_texts - {target.entity_text})
        
        kb_entity = KBEntity(
            knowledge_base_id=target.document.knowledge_base_id,
            canonical_name=target.entity_text,
            entity_type=target.entity_type,
            aliases=aliases,
            document_count=len(sources) + 1,
            occurrence_count=len(sources) + 1
        )
        db.add(kb_entity)
        db.flush()
    
    # 更新所有实体的KB关联
    target.kb_entity_id = kb_entity.id
    for source in sources:
        source.kb_entity_id = kb_entity.id
    
    db.commit()
    
    return {
        "success": True,
        "message": f"成功合并 {len(sources)} 个实体到KB实体",
        "kb_entity_id": kb_entity.id
    }


# ============ 实体删除接口 ============

@router.delete("/document-entity/{entity_id}")
def delete_document_entity(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """删除文档级实体"""
    entity = db.query(DocumentEntity).filter(DocumentEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    # 删除相关的关系
    from app.modules.knowledge.models.knowledge_document import EntityRelationship
    db.query(EntityRelationship).filter(
        (EntityRelationship.source_id == entity_id) |
        (EntityRelationship.target_id == entity_id)
    ).delete()
    
    # 删除实体
    db.delete(entity)
    db.commit()
    
    return {
        "success": True,
        "message": "实体已删除"
    }


@router.post("/batch-delete")
def batch_delete_entities(
    entity_ids: List[int],
    level: str = Query(..., description="实体层级: document, kb, global"),
    db: Session = Depends(get_db)
):
    """批量删除实体"""
    deleted_count = 0
    
    if level == 'document':
        for entity_id in entity_ids:
            entity = db.query(DocumentEntity).filter(DocumentEntity.id == entity_id).first()
            if entity:
                # 删除相关关系
                from app.modules.knowledge.models.knowledge_document import EntityRelationship
                db.query(EntityRelationship).filter(
                    (EntityRelationship.source_id == entity_id) |
                    (EntityRelationship.target_id == entity_id)
                ).delete()
                db.delete(entity)
                deleted_count += 1
    
    elif level == 'kb':
        for entity_id in entity_ids:
            entity = db.query(KBEntity).filter(KBEntity.id == entity_id).first()
            if entity:
                db.delete(entity)
                deleted_count += 1
    
    elif level == 'global':
        for entity_id in entity_ids:
            entity = db.query(GlobalEntity).filter(GlobalEntity.id == entity_id).first()
            if entity:
                db.delete(entity)
                deleted_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"成功删除 {deleted_count} 个实体",
        "deleted_count": deleted_count
    }


# ============ 实体添加接口 ============

@router.post("/add-document-entity")
def add_document_entity(
    request: EntityCreateRequest,
    db: Session = Depends(get_db)
):
    """手动添加文档级实体"""
    # 检查文档是否存在
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == request.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 创建实体
    from app.modules.knowledge.models.knowledge_document import DocumentEntity
    
    entity = DocumentEntity(
        document_id=request.document_id,
        entity_text=request.entity_text,
        entity_type=request.entity_type,
        start_pos=request.start_pos or 0,
        end_pos=request.end_pos or 0,
        confidence=request.confidence or 1.0,
        status="confirmed"
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    
    return {
        "success": True,
        "message": "实体已添加",
        "entity": {
            "id": entity.id,
            "text": entity.entity_text,
            "type": entity.entity_type
        }
    }


# ============ 实体反馈接口 ============

@router.post("/feedback")
def submit_entity_feedback(
    request: EntityFeedbackRequest,
    db: Session = Depends(get_db)
):
    """提交实体反馈"""
    # 这里可以将反馈存储到数据库或发送到分析队列
    # 简化实现：记录到日志
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"实体反馈: level={request.level}, entity_id={request.entity_id}, "
                f"issue_type={request.issue_type}, suggestion={request.suggestion}")
    
    # TODO: 将反馈存储到专门的反馈表
    # TODO: 定期分析反馈，优化实体提取模型
    
    return {
        "success": True,
        "message": "反馈已提交，感谢您的建议！"
    }


# ============ 实体统计接口 ============

@router.get("/statistics/{knowledge_base_id}")
def get_entity_statistics(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """获取实体统计信息"""
    # 文档级统计
    doc_entity_count = db.query(DocumentEntity).join(
        KnowledgeDocument
    ).filter(
        KnowledgeDocument.knowledge_base_id == knowledge_base_id
    ).count()
    
    # KB级统计
    kb_entity_count = db.query(KBEntity).filter(
        KBEntity.knowledge_base_id == knowledge_base_id
    ).count()
    
    # 按类型统计
    from sqlalchemy import func
    type_stats = db.query(
        DocumentEntity.entity_type,
        func.count(DocumentEntity.id)
    ).join(
        KnowledgeDocument
    ).filter(
        KnowledgeDocument.knowledge_base_id == knowledge_base_id
    ).group_by(DocumentEntity.entity_type).all()
    
    return {
        "knowledge_base_id": knowledge_base_id,
        "document_entities": doc_entity_count,
        "kb_entities": kb_entity_count,
        "type_distribution": {
            entity_type: count for entity_type, count in type_stats
        }
    }


@router.post("/batch-update-status")
def batch_update_entity_status(
    request: EntityStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    批量更新文档实体状态

    用于实体识别页面的批量确认、批量拒绝等操作

    Args:
        request: 包含实体ID列表和目标状态

    Returns:
        更新结果统计
    """
    try:
        # 验证状态值
        valid_statuses = ['pending', 'confirmed', 'rejected', 'modified']
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"无效的状态值 '{request.status}'，有效值为: {', '.join(valid_statuses)}"
            )

        if not request.entity_ids:
            return {
                "success": True,
                "updated_count": 0,
                "message": "没有需要更新的实体"
            }

        # 查询存在的实体
        existing_entities = db.query(DocumentEntity).filter(
            DocumentEntity.id.in_(request.entity_ids)
        ).all()

        existing_ids = {e.id for e in existing_entities}
        not_found_ids = set(request.entity_ids) - existing_ids

        # 更新实体状态
        updated_count = db.query(DocumentEntity).filter(
            DocumentEntity.id.in_(request.entity_ids)
        ).update({
            DocumentEntity.status: request.status
        }, synchronize_session=False)

        db.commit()

        result = {
            "success": True,
            "updated_count": updated_count,
            "requested_count": len(request.entity_ids),
            "status": request.status
        }

        if not_found_ids:
            result["not_found_ids"] = list(not_found_ids)
            result["warning"] = f"{len(not_found_ids)} 个实体未找到"

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新实体状态失败: {str(e)}")


@router.put("/document-entity/{entity_id}/status")
def update_entity_status(
    entity_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    更新单个文档实体状态

    Args:
        entity_id: 实体ID
        status: 目标状态 (pending, confirmed, rejected, modified)

    Returns:
        更新结果
    """
    try:
        # 验证状态值
        valid_statuses = ['pending', 'confirmed', 'rejected', 'modified']
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"无效的状态值 '{status}'，有效值为: {', '.join(valid_statuses)}"
            )

        entity = db.query(DocumentEntity).filter(DocumentEntity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")

        entity.status = status
        db.commit()

        return {
            "success": True,
            "message": "实体状态已更新",
            "entity": {
                "id": entity.id,
                "text": entity.entity_text,
                "type": entity.entity_type,
                "status": entity.status
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新实体状态失败: {str(e)}")


# ============ 实体确认工作流接口（修复E13） ============

@router.get("/confirmation-stats/{knowledge_base_id}")
def get_entity_confirmation_stats(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取实体确认工作流统计

    修复E13：提供实体确认工作流的统计信息，支持前端状态展示

    Args:
        knowledge_base_id: 知识库ID

    Returns:
        实体确认统计信息
    """
    try:
        from sqlalchemy import func

        # 获取文档ID列表
        document_ids = db.query(KnowledgeDocument.id).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        document_ids = [d[0] for d in document_ids]

        if not document_ids:
            return {
                "knowledge_base_id": knowledge_base_id,
                "total_entities": 0,
                "status_distribution": {},
                "confirmation_rate": "0.00%",
                "pending_count": 0,
                "confirmed_count": 0,
                "rejected_count": 0,
                "modified_count": 0
            }

        # 按状态统计
        status_counts = db.query(
            DocumentEntity.status,
            func.count(DocumentEntity.id)
        ).filter(
            DocumentEntity.document_id.in_(document_ids)
        ).group_by(DocumentEntity.status).all()

        # 构建统计结果
        status_distribution = {status: count for status, count in status_counts}
        total = sum(status_distribution.values())

        pending_count = status_distribution.get('pending', 0)
        confirmed_count = status_distribution.get('confirmed', 0)
        rejected_count = status_distribution.get('rejected', 0)
        modified_count = status_distribution.get('modified', 0)

        # 计算确认率
        confirmed_rate = (confirmed_count / total * 100) if total > 0 else 0

        return {
            "knowledge_base_id": knowledge_base_id,
            "total_entities": total,
            "status_distribution": status_distribution,
            "confirmation_rate": f"{confirmed_rate:.2f}%",
            "pending_count": pending_count,
            "confirmed_count": confirmed_count,
            "rejected_count": rejected_count,
            "modified_count": modified_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体确认统计失败: {str(e)}")


@router.get("/pending-entities/{knowledge_base_id}")
def get_pending_entities(
    knowledge_base_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    获取待确认的实体列表

    修复E13：支持实体确认工作流

    Args:
        knowledge_base_id: 知识库ID
        page: 页码
        page_size: 每页数量

    Returns:
        待确认实体列表
    """
    try:
        # 获取文档ID列表
        document_ids = db.query(KnowledgeDocument.id).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).all()
        document_ids = [d[0] for d in document_ids]

        if not document_ids:
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "entities": []
            }

        # 查询待确认实体
        query = db.query(DocumentEntity).filter(
            DocumentEntity.document_id.in_(document_ids),
            DocumentEntity.status == 'pending'
        )

        total = query.count()
        entities = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "entities": [
                {
                    "id": e.id,
                    "text": e.entity_text,
                    "type": e.entity_type,
                    "confidence": e.confidence,
                    "document_id": e.document_id,
                    "status": e.status,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in entities
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待确认实体失败: {str(e)}")
