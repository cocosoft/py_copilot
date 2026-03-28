#!/usr/bin/env python3
"""
实体识别任务暂停/恢复/取消功能

为处理大文档（如90万字文档）提供暂停和恢复功能
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import logging

from app.core.database import get_db
from app.modules.knowledge.models.knowledge_document import EntityExtractionTask

logger = logging.getLogger(__name__)

router = APIRouter(tags=["任务管理"])


@router.post("/knowledge-bases/{knowledge_base_id}/extraction-tasks/{task_id}/pause")
async def pause_extraction_task(
    knowledge_base_id: int,
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    暂停实体识别任务

    将正在处理中的任务暂停，已处理的片段结果会被保留
    用户可以在需要时恢复任务

    Args:
        knowledge_base_id: 知识库ID
        task_id: 任务ID

    Returns:
        暂停结果
    """
    try:
        # 查询任务
        task = db.query(EntityExtractionTask).filter(
            EntityExtractionTask.id == task_id,
            EntityExtractionTask.knowledge_base_id == knowledge_base_id
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 只能暂停处理中的任务
        if task.status != 'processing':
            raise HTTPException(
                status_code=400,
                detail=f"只能暂停处理中的任务，当前状态: {task.status}"
            )

        # 更新任务状态为暂停
        task.status = 'paused'
        task.paused_at = func.now()
        task.pause_count = (task.pause_count or 0) + 1
        db.commit()

        logger.info(f"任务 {task_id} 已暂停，当前进度: {task.processed_chunks}/{task.total_chunks}")

        return {
            "code": 200,
            "message": "任务已暂停",
            "data": {
                "task_id": task_id,
                "status": "paused",
                "progress": {
                    "processed": task.processed_chunks,
                    "total": task.total_chunks,
                    "percentage": round(task.processed_chunks / task.total_chunks * 100, 2) if task.total_chunks > 0 else 0
                },
                "paused_at": task.paused_at.isoformat() if task.paused_at else None,
                "pause_count": task.pause_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务 {task_id} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"暂停任务失败: {str(e)}")


@router.post("/knowledge-bases/{knowledge_base_id}/extraction-tasks/{task_id}/resume")
async def resume_extraction_task(
    knowledge_base_id: int,
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    恢复实体识别任务

    将已暂停的任务恢复执行，从上次暂停的位置继续处理

    Args:
        knowledge_base_id: 知识库ID
        task_id: 任务ID

    Returns:
        恢复结果
    """
    try:
        # 查询任务
        task = db.query(EntityExtractionTask).filter(
            EntityExtractionTask.id == task_id,
            EntityExtractionTask.knowledge_base_id == knowledge_base_id
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 只能恢复已暂停的任务
        if task.status != 'paused':
            raise HTTPException(
                status_code=400,
                detail=f"只能恢复已暂停的任务，当前状态: {task.status}"
            )

        # 更新任务状态为处理中
        task.status = 'processing'
        task.resumed_at = func.now()
        db.commit()

        # 重新启动后台任务处理
        from app.api.v1.endpoints.hierarchy_api import _process_extraction_task
        background_tasks.add_task(
            _process_extraction_task,
            task_id=task.id,
            knowledge_base_id=knowledge_base_id,
            document_id=task.document_id
        )

        logger.info(f"任务 {task_id} 已恢复，继续处理")

        return {
            "code": 200,
            "message": "任务已恢复",
            "data": {
                "task_id": task_id,
                "status": "processing",
                "progress": {
                    "processed": task.processed_chunks,
                    "total": task.total_chunks,
                    "percentage": round(task.processed_chunks / task.total_chunks * 100, 2) if task.total_chunks > 0 else 0
                },
                "resumed_at": task.resumed_at.isoformat() if task.resumed_at else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务 {task_id} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复任务失败: {str(e)}")


@router.post("/knowledge-bases/{knowledge_base_id}/extraction-tasks/{task_id}/cancel")
async def cancel_extraction_task(
    knowledge_base_id: int,
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    取消实体识别任务

    终止正在处理或已暂停的任务，保留已处理的结果

    Args:
        knowledge_base_id: 知识库ID
        task_id: 任务ID

    Returns:
        取消结果
    """
    try:
        # 查询任务
        task = db.query(EntityExtractionTask).filter(
            EntityExtractionTask.id == task_id,
            EntityExtractionTask.knowledge_base_id == knowledge_base_id
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 只能取消处理中或已暂停的任务
        if task.status not in ['processing', 'paused', 'pending']:
            raise HTTPException(
                status_code=400,
                detail=f"只能取消处理中、已暂停或待处理的任务，当前状态: {task.status}"
            )

        # 记录取消前的状态
        previous_status = task.status

        # 更新任务状态为失败（表示被取消）
        task.status = 'failed'
        task.error_message = f"任务被用户取消（原状态: {previous_status}）"
        task.completed_at = func.now()
        db.commit()

        logger.info(f"任务 {task_id} 已取消，原状态: {previous_status}")

        return {
            "code": 200,
            "message": "任务已取消",
            "data": {
                "task_id": task_id,
                "previous_status": previous_status,
                "final_status": "failed",
                "progress": {
                    "processed": task.processed_chunks,
                    "total": task.total_chunks,
                    "percentage": round(task.processed_chunks / task.total_chunks * 100, 2) if task.total_chunks > 0 else 0
                },
                "preserved_entities": {
                    "chunk_entities": task.chunk_entity_count,
                    "document_entities": task.document_entity_count
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务 {task_id} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


# 导入 BackgroundTasks
from fastapi import BackgroundTasks
