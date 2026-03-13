"""
知识库批量处理API

提供知识库文档的批量处理功能
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-bases", tags=["知识库管理"])


# ============ 请求/响应模型 ============

class BatchProcessRequest(BaseModel):
    """批量处理请求模型"""
    document_ids: List[int] = Field(..., description="要处理的文档ID列表")
    options: Optional[Dict[str, Any]] = Field(None, description="处理选项")


class BatchProcessResponse(BaseModel):
    """批量处理响应模型"""
    task_id: str = Field(..., description="任务组ID")
    status: str = Field(..., description="任务状态")
    document_count: int = Field(..., description="文档数量")
    message: str = Field(..., description="状态消息")


class BatchProcessStatusResponse(BaseModel):
    """批量处理状态响应模型"""
    task_id: str = Field(..., description="任务组ID")
    status: str = Field(..., description="任务状态: pending/processing/completed")
    progress: Dict[str, Any] = Field(..., description="进度信息")


class DocumentProcessResult(BaseModel):
    """文档处理结果模型"""
    document_id: int = Field(..., description="文档ID")
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="处理消息")
    entities_count: Optional[int] = Field(None, description="识别实体数")
    chunks_count: Optional[int] = Field(None, description="分块数")


# ============ API端点 ============

@router.post("/{kb_id}/documents/batch-process", response_model=BatchProcessResponse)
async def batch_process_documents(
    kb_id: int,
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量处理知识库文档
    
    对指定知识库中的多个文档执行完整的7步处理流程：
    1. 文档解析
    2. 文本清理
    3. 智能分块
    4. 实体识别与关系提取
    5. 实体对齐
    6. 向量化处理
    7. 知识图谱构建
    
    Args:
        kb_id: 知识库ID
        request: 批量处理请求，包含文档ID列表
        
    Returns:
        批量处理任务信息，包含任务组ID
        
    Raises:
        HTTPException: 知识库不存在或无权限
    """
    try:
        # 验证知识库存在
        from app.modules.knowledge.models.knowledge_document import KnowledgeBase
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 验证文档属于该知识库
        from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
        valid_docs = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id.in_(request.document_ids),
            KnowledgeDocument.knowledge_base_id == kb_id
        ).all()
        
        valid_doc_ids = [doc.id for doc in valid_docs]
        invalid_count = len(request.document_ids) - len(valid_doc_ids)
        
        if invalid_count > 0:
            logger.warning(f"有 {invalid_count} 个文档不属于知识库 {kb_id}")
        
        if not valid_doc_ids:
            raise HTTPException(status_code=400, detail="没有有效的文档需要处理")
        
        # 尝试使用Celery进行批量处理
        try:
            from celery import group
            from app.tasks.knowledge.document_processing import process_document_task
            
            # 创建任务组
            tasks = [
                process_document_task.s(doc_id, kb_id, request.options)
                for doc_id in valid_doc_ids
            ]
            
            # 提交任务组
            job = group(tasks).apply_async()
            
            return BatchProcessResponse(
                task_id=job.id,
                status="pending",
                document_count=len(valid_doc_ids),
                message=f"批量处理任务已创建，共 {len(valid_doc_ids)} 个文档"
            )
            
        except ImportError:
            # Celery不可用，使用同步处理
            logger.warning("Celery不可用，使用同步批量处理")
            
            # 生成任务ID
            import uuid
            task_id = str(uuid.uuid4())
            
            # 在后台执行同步处理
            background_tasks.add_task(
                _sync_batch_process,
                task_id,
                valid_doc_ids,
                kb_id,
                request.options
            )
            
            return BatchProcessResponse(
                task_id=task_id,
                status="processing",
                document_count=len(valid_doc_ids),
                message=f"同步批量处理已开始，共 {len(valid_doc_ids)} 个文档"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建批量处理任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/{kb_id}/documents/batch-status/{task_id}", response_model=BatchProcessStatusResponse)
async def get_batch_process_status(
    kb_id: int,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取批量处理任务状态
    
    Args:
        kb_id: 知识库ID
        task_id: 任务组ID
        
    Returns:
        任务状态和进度信息
        
    Raises:
        HTTPException: 任务不存在
    """
    try:
        # 尝试从Celery获取状态
        try:
            from celery.result import GroupResult
            
            result = GroupResult.restore(task_id)
            if result:
                # 计算进度
                total = len(result.results)
                completed = sum(1 for r in result.results if r.ready())
                successful = sum(1 for r in result.results if r.successful())
                
                return BatchProcessStatusResponse(
                    task_id=task_id,
                    status="completed" if result.ready() else "processing",
                    progress={
                        "total": total,
                        "completed": completed,
                        "successful": successful,
                        "failed": completed - successful,
                        "percentage": int((completed / total) * 100) if total > 0 else 0
                    }
                )
        except ImportError:
            pass
        
        # 检查同步任务状态（简化实现）
        # 实际项目中应该使用Redis或数据库来存储任务状态
        return BatchProcessStatusResponse(
            task_id=task_id,
            status="processing",
            progress={
                "total": 0,
                "completed": 0,
                "successful": 0,
                "failed": 0,
                "percentage": 0,
                "message": "同步任务状态查询暂未实现"
            }
        )
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{kb_id}/documents/progress/{document_id}")
async def get_document_progress(
    kb_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个文档的处理进度
    
    Args:
        kb_id: 知识库ID
        document_id: 文档ID
        
    Returns:
        文档处理进度详情
    """
    try:
        # 验证文档存在
        from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.knowledge_base_id == kb_id
        ).first()
        
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取进度
        from app.services.knowledge.utils.processing_progress_service import processing_progress_service
        
        progress = processing_progress_service.get_progress(str(document_id))
        
        if not progress:
            return {
                "document_id": document_id,
                "status": "unknown",
                "message": "未找到进度信息"
            }
        
        return {
            "document_id": document_id,
            "status": progress.get("status"),
            "current_step": progress.get("current_step"),
            "total_steps": progress.get("total_steps"),
            "step_name": progress.get("step_name"),
            "message": progress.get("message"),
            "progress_percentage": int((progress.get("current_step", 0) / progress.get("total_steps", 7)) * 100),
            "updated_at": progress.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询文档进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ============ 辅助函数 ============

def _sync_batch_process(
    task_id: str,
    document_ids: List[int],
    knowledge_base_id: int,
    options: Optional[Dict[str, Any]]
):
    """
    同步批量处理文档（后台任务）
    
    Args:
        task_id: 任务ID
        document_ids: 文档ID列表
        knowledge_base_id: 知识库ID
        options: 处理选项
    """
    from app.core.database import SessionLocal
    from app.services.knowledge.core.document_processor import DocumentProcessor
    from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
    
    db = SessionLocal()
    processor = DocumentProcessor()
    
    logger.info(f"[任务 {task_id}] 开始批量处理 {len(document_ids)} 个文档")
    
    try:
        for idx, doc_id in enumerate(document_ids, 1):
            try:
                # 获取文档
                doc = db.query(KnowledgeDocument).filter(
                    KnowledgeDocument.id == doc_id
                ).first()
                
                if not doc:
                    logger.warning(f"[任务 {task_id}] 文档不存在: {doc_id}")
                    continue
                
                logger.info(f"[任务 {task_id}] 处理文档 {idx}/{len(document_ids)}: {doc_id}")
                
                # 执行处理
                result = processor.process_document(
                    file_path=doc.file_path,
                    file_type=doc.file_type,
                    document_id=doc_id,
                    knowledge_base_id=knowledge_base_id,
                    db=db
                )
                
                # 更新文档状态
                if result.get("success"):
                    logger.info(f"[任务 {task_id}] 文档 {doc_id} 处理成功")
                else:
                    logger.error(f"[任务 {task_id}] 文档 {doc_id} 处理失败: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"[任务 {task_id}] 处理文档 {doc_id} 异常: {e}")
                continue
        
        logger.info(f"[任务 {task_id}] 批量处理完成")
        
    finally:
        db.close()
