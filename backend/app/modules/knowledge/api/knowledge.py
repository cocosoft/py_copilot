import os
import logging
import time
import asyncio
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, text
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# 简单的内存缓存机制
_processing_status_cache: Dict[int, Dict[str, Any]] = {}
_processing_status_cache_time: Dict[int, float] = {}
_document_progress_cache: Dict[str, Dict[str, Any]] = {}
_document_progress_cache_time: Dict[str, float] = {}
CACHE_TTL = 5.0  # 缓存有效期5秒

# 并发控制锁
_processing_status_locks: Dict[int, asyncio.Lock] = {}
_processing_status_pending: Dict[int, asyncio.Future] = {}

from app.core.database import get_db
from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.modules.knowledge.models.knowledge_document import (
    KnowledgeBase as KnowledgeBaseModel, 
    KnowledgeDocument as KnowledgeDocumentModel,
    KnowledgeBasePermission as KnowledgeBasePermissionModel
)
from app.services.knowledge.retrieval.retrieval_service import AdvancedRetrievalService
from app.services.knowledge.document_processing_queue import document_processing_queue
from app.modules.knowledge.schemas.knowledge import (
    KnowledgeDocument, SearchResponse, DocumentListResponse,
    KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate,
    KnowledgeTag, DocumentTagRequest, DocumentTagsResponse, TagListResponse,
    KnowledgeDocumentChunk, AdvancedSearchRequest, HybridSearchRequest,
    AdvancedSearchResponse,
    KnowledgeBasePermission, KnowledgeBasePermissionCreate,
    KnowledgeBasePermissionListResponse, KnowledgeBasePermissionsUpdateRequest
)

router = APIRouter()
knowledge_service = KnowledgeService()

# Knowledge Base API Endpoints
@router.post("/knowledge-bases", response_model=KnowledgeBase)
async def create_knowledge_base(
    knowledge_base: KnowledgeBaseCreate,
    db: Session = Depends(get_db)
):
    """创建新的知识库"""
    try:
        # 检查知识库名称是否已存在
        existing_kb = db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.name == knowledge_base.name).first()
        if existing_kb:
            raise HTTPException(status_code=400, detail="知识库名称已存在")
        
        result = knowledge_service.create_knowledge_base(
            name=knowledge_base.name,
            description=knowledge_base.description,
            db=db
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建知识库失败")

@router.get("/knowledge-bases", response_model=List[KnowledgeBase])
async def list_knowledge_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取知识库列表"""
    try:
        return knowledge_service.list_knowledge_bases(db, skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取知识库列表失败")

@router.get("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBase)
async def get_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """获取知识库详情"""
    try:
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        return knowledge_base
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取知识库详情失败")

@router.put("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBase)
async def update_knowledge_base(
    knowledge_base_id: int,
    knowledge_base: KnowledgeBaseUpdate,
    db: Session = Depends(get_db)
):
    """更新知识库信息"""
    try:
        result = knowledge_service.update_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            name=knowledge_base.name,
            description=knowledge_base.description,
            db=db
        )
        if not result:
            raise HTTPException(status_code=404, detail="知识库不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新知识库失败")

@router.delete("/knowledge-bases/{knowledge_base_id}")
async def delete_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """删除知识库"""
    try:
        success = knowledge_service.delete_knowledge_base(knowledge_base_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在")
        return {"message": "知识库删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除知识库失败")

# 初始化文档处理队列
from app.services.knowledge.document_processing_queue import document_processing_queue

# 设置文档处理器并启动队列
async def init_document_processing_queue():
    """初始化文档处理队列"""
    document_processing_queue.set_processor(knowledge_service.process_document_async)
    await document_processing_queue.start()

# 在应用启动时初始化队列
# 注意：这需要在应用启动时调用

# Knowledge Document API Endpoints
@router.post("/documents", response_model=dict)
@router.post("/documents/upload")
async def upload_document(
    knowledge_base_id: int = Query(..., description="目标知识库ID"),
    file: UploadFile = File(...),
    auto_process: bool = Query(False, description="是否自动处理文档（向量化、图谱化）"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    上传文档到指定知识库

    分离上传与处理：
    1. 文件上传后立即返回响应，仅保存文件和创建记录
    2. 向量化、图谱化等耗时操作需要前端手动触发
    3. 如需自动处理，设置 auto_process=true（向后兼容）
    """
    try:
        # 检查文件格式支持
        if not knowledge_service.is_supported_format(file.filename):
            raise HTTPException(status_code=400, detail="不支持的文件格式")

        # 检查文件大小（限制50MB）
        if file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小超过50MB限制")

        # 检查知识库是否存在
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 保存文件并创建文档记录（同步执行，快速返回）
        save_result = await knowledge_service.save_document(file, knowledge_base_id, db)

        # 检查是否是重复文件
        if save_result.get("duplicate"):
            existing_doc = save_result.get("document")
            existing_metadata = existing_doc.document_metadata or {}
            return {
                "message": save_result.get("message", "该文件已存在于知识库中"),
                "document_id": existing_doc.id,
                "status": "duplicate",
                "processing_status": existing_metadata.get("processing_status", "unknown"),
                "warning": "系统检测到您上传的文件与知识库中现有文件内容完全相同"
            }

        document = save_result.get("document")

        # 如果不自动处理，直接返回上传成功
        if not auto_process:
            return {
                "message": "文档上传成功，请手动启动处理",
                "document_id": document.id,
                "status": "uploaded",
                "processing_status": "idle"
            }

        # 以下代码仅在 auto_process=true 时执行（向后兼容）
        # 将文档添加到处理队列
        queue_status = document_processing_queue.get_queue_status()

        # 如果队列已满（处理中+队列中超过5个），提示用户稍后再试
        if queue_status["queue_size"] + queue_status["processing_count"] >= 5:
            document.document_metadata["processing_status"] = "queued"
            db.commit()

            return {
                "message": "文档上传成功，但处理队列已满，请稍后再试",
                "document_id": document.id,
                "status": "queue_full",
                "queue_status": queue_status
            }

        # 添加到处理队列
        added = await document_processing_queue.add_document(
            document_id=document.id,
            knowledge_base_id=knowledge_base_id,
            document_name=document.title,
            priority=0
        )

        if added:
            document.document_metadata["processing_status"] = "queued"
            db.commit()

            return {
                "message": "文档上传成功，已加入处理队列",
                "document_id": document.id,
                "status": "queued",
                "queue_position": queue_status["queue_size"] + 1
            }
        else:
            if background_tasks:
                background_tasks.add_task(
                    knowledge_service.process_document_async,
                    document.id,
                    knowledge_base_id
                )
            else:
                import asyncio
                asyncio.create_task(
                    knowledge_service.process_document_async(document.id, knowledge_base_id)
                )

            return {
                "message": "文档上传成功，正在后台处理中",
                "document_id": document.id,
                "status": "processing"
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")

@router.get("/search", response_model=SearchResponse)
async def search_documents(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID进行搜索"),
    db: Session = Depends(get_db)
):
    """搜索知识库文档"""
    try:
        results = knowledge_service.search_documents(query, limit, knowledge_base_id, db)
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="搜索失败")

@router.post("/search/advanced", response_model=AdvancedSearchResponse)
async def advanced_search_documents(
    search_request: AdvancedSearchRequest,
    db: Session = Depends(get_db)
):
    """高级搜索知识库文档"""
    try:
        advanced_service = AdvancedRetrievalService()
        
        results = advanced_service.advanced_search(
            query=search_request.query,
            n_results=search_request.n_results,
            knowledge_base_id=search_request.knowledge_base_id,
            tags=search_request.tags,
            filters=search_request.filters,
            sort_by=search_request.sort_by,
            entity_filter=search_request.entity_filter
        )
        
        return {
            "query": search_request.query,
            "results": results,
            "count": len(results),
            "search_type": "advanced"
        }
    except Exception as e:
        import traceback
        print(f"高级搜索失败: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="高级搜索失败")

@router.post("/search/hybrid", response_model=AdvancedSearchResponse)
async def hybrid_search_documents(
    search_request: HybridSearchRequest,
    db: Session = Depends(get_db)
):
    """混合搜索知识库文档（关键词+向量）"""
    try:
        advanced_service = AdvancedRetrievalService()
        
        results = advanced_service.hybrid_search(
            query=search_request.query,
            n_results=search_request.n_results,
            keyword_weight=search_request.keyword_weight,
            vector_weight=search_request.vector_weight,
            knowledge_base_id=search_request.knowledge_base_id,
            tags=search_request.tags,
            filters=search_request.filters,
            sort_by=search_request.sort_by
        )
        
        return {
            "query": search_request.query,
            "results": results,
            "count": len(results),
            "search_type": "hybrid"
        }
    except Exception as e:
        import traceback
        print(f"混合搜索失败: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="混合搜索失败")

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID"),
    # is_vectorized 参数已废弃，使用 processing_status 替代
    # is_vectorized: Optional[int] = Query(None, description="筛选向量化状态: 1=已向量化, 0=未向量化"),
    processing_status: Optional[str] = Query(None, description="筛选处理状态: idle=待处理, processing=处理中, queued=排队中, failed=失败, completed=已完成")
    , db: Session = Depends(get_db)
):
    """获取知识库文档列表 - 自动修复状态不一致的文档"""
    try:
        # 使用 processing_status 单字段进行筛选
        documents = knowledge_service.list_documents(db, skip, limit, knowledge_base_id, processing_status)
        total = knowledge_service.get_document_count(db, knowledge_base_id, processing_status)

        # 获取队列状态（同步方法，不需要await）
        queue_status = document_processing_queue.get_queue_status()
        processing_ids = {task["document_id"] for task in queue_status.get("processing_documents", [])}
        # 注意：queued_documents 不在返回结果中，只检查 processing_documents
        all_active_ids = processing_ids

        # 转换为Pydantic模型，并修复状态不一致的文档
        document_models = []
        for doc in documents:
            # 检查文档状态是否与队列状态一致
            doc_metadata = doc.document_metadata or {}
            doc_status = doc_metadata.get("processing_status")

            # 如果文档标记为processing或queued，但不在队列中，重置状态
            if doc_status in ["processing", "queued"] and doc.id not in all_active_ids:
                print(f"修复文档状态不一致: 文档 {doc.id} ({doc.title}) 标记为 {doc_status} 但不在队列中，重置为空闲状态")
                doc_metadata["processing_status"] = "idle"
                doc_metadata["processing_error"] = "服务重启，处理中断"
                doc.document_metadata = doc_metadata
                db.commit()

            document_models.append(
                KnowledgeDocument(
                    id=doc.id,
                    uuid=doc.uuid,
                    title=doc.title,
                    knowledge_base_id=doc.knowledge_base_id,
                    file_path=doc.file_path,
                    file_type=doc.file_type,
                    content=doc.content,
                    document_metadata=doc.document_metadata,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    vector_id=doc.vector_id,
                    file_hash=doc.file_hash
                )
            )

        return {
            "documents": document_models,
            "skip": skip,
            "limit": limit,
            "total": total
        }
    except Exception as e:
        import traceback
        print(f"获取文档列表错误: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.get("/documents/unprocessed")
async def get_unprocessed_documents_list(
    knowledge_base_id: int = Query(..., description="知识库ID"),
    db: Session = Depends(get_db)
):
    """
    获取未处理文档列表（简化版）

    用于前端获取指定知识库中所有未处理的文档
    """
    try:
        # 检查知识库是否存在
        knowledge_base = await run_in_threadpool(
            lambda: db.query(KnowledgeBaseModel).filter(
                KnowledgeBaseModel.id == knowledge_base_id
            ).first()
        )

        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 获取所有文档
        all_docs = await run_in_threadpool(
            lambda: db.query(KnowledgeDocumentModel).filter(
                KnowledgeDocumentModel.knowledge_base_id == knowledge_base_id
            ).all()
        )

        # 过滤未处理的文档
        unprocessed_docs = []
        for doc in all_docs:
            metadata = doc.document_metadata or {}
            status = metadata.get('processing_status')
            if status != 'completed':
                unprocessed_docs.append({
                    "id": doc.id,
                    "title": doc.title,
                    "file_type": doc.file_type,
                    "processing_status": status or 'unknown',
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                })

        return {
            "success": True,
            "knowledge_base_id": knowledge_base_id,
            "total_unprocessed": len(unprocessed_docs),
            "documents": unprocessed_docs
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取未处理文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取未处理文档列表失败: {str(e)}")


@router.get("/documents/{document_id}", response_model=KnowledgeDocument)
async def get_document_detail(
    document_id: str,
    db: Session = Depends(get_db)
):
    """获取文档详情（支持ID或UUID）"""
    try:
        document = knowledge_service.get_document_by_id_or_uuid(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        return KnowledgeDocument(
            id=document.id,
            uuid=document.uuid,
            title=document.title,
            knowledge_base_id=document.knowledge_base_id,
            file_path=document.file_path,
            file_type=document.file_type,
            content=None,  # 不返回完整内容，避免大数据传输
            document_metadata=document.document_metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            vector_id=document.vector_id,
            file_hash=document.file_hash
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取文档详情失败")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """删除文档（支持ID或UUID）"""
    try:
        # 根据ID或UUID获取文档
        document = knowledge_service.get_document_by_id_or_uuid(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        success = knowledge_service.delete_document(db, document.id)
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除失败")


class BatchDeleteRequest(BaseModel):
    """批量删除请求模型"""
    document_ids: List[str]


class BatchDeleteResponse(BaseModel):
    """批量删除响应模型"""
    success_count: int
    failed_count: int
    total_count: int
    failed_documents: List[Dict[str, Any]]


@router.post("/documents/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_documents(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """批量删除文档"""
    try:
        result = knowledge_service.batch_delete_documents(db, request.document_ids)
        return BatchDeleteResponse(
            success_count=result["success_count"],
            failed_count=result["failed_count"],
            total_count=result["total_count"],
            failed_documents=result["failed_documents"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")


class BatchDownloadRequest(BaseModel):
    """批量下载请求模型"""
    document_ids: List[str]


@router.post("/documents/batch-download")
async def batch_download_documents(
    request: BatchDownloadRequest,
    db: Session = Depends(get_db)
):
    """批量下载文档（打包为ZIP）"""
    try:
        result = knowledge_service.batch_download_documents(db, request.document_ids)

        if result["success_count"] == 0:
            raise HTTPException(status_code=404, detail="没有可下载的文档")

        # 返回ZIP文件
        from starlette.responses import StreamingResponse

        zip_buffer = result["zip_buffer"]

        def iterfile():
            yield from zip_buffer

        return StreamingResponse(
            iterfile(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={result['zip_filename']}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量下载失败: {str(e)}")


@router.get("/documents/{document_id}/progress")
async def get_document_processing_progress(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档处理进度

    用于前端轮询查询文档处理状态
    使用缓存机制避免频繁查询数据库
    """
    global _document_progress_cache, _document_progress_cache_time

    cache_key = str(document_id)
    current_time = time.time()

    # 检查缓存是否有效
    if cache_key in _document_progress_cache:
        cache_age = current_time - _document_progress_cache_time.get(cache_key, 0)
        if cache_age < CACHE_TTL:
            # 缓存有效，直接返回
            logger.debug(f"[文档进度] 使用缓存: document_id={document_id}, age={cache_age:.2f}s")
            return _document_progress_cache[cache_key]

    try:
        from app.services.knowledge.processing_progress_service import processing_progress_service

        # 首先检查文档是否存在（使用轻量级查询）
        document = await run_in_threadpool(
            lambda: db.query(KnowledgeDocumentModel).filter(
                KnowledgeDocumentModel.id == document_id
            ).with_entities(
                KnowledgeDocumentModel.id,
                KnowledgeDocumentModel.document_metadata
            ).first()
        )

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 如果文档已向量化（processing_status = 'completed'），直接返回完成状态
        doc_metadata = document.document_metadata or {}
        if doc_metadata.get('processing_status') == 'completed':
            result = {
                "document_id": document_id,
                "status": "completed",
                "progress_percent": 100,
                "step_name": "完成",
                "message": "文档处理已完成"
            }
            # 更新缓存
            _document_progress_cache[cache_key] = result
            _document_progress_cache_time[cache_key] = current_time
            return result

        # 获取处理进度（从内存服务，不查询数据库）
        progress = processing_progress_service.get_progress(str(document_id))

        if progress:
            # 更新缓存
            _document_progress_cache[cache_key] = progress
            _document_progress_cache_time[cache_key] = current_time
            return progress

        # 如果没有进度记录，根据文档状态返回
        doc_metadata = document.document_metadata or {}
        doc_status = doc_metadata.get("processing_status")

        if doc_status == "processing":
            result = {
                "document_id": document_id,
                "status": "processing",
                "progress_percent": 0,
                "step_name": "初始化",
                "message": "文档处理初始化中..."
            }
        elif doc_status == "queued":
            result = {
                "document_id": document_id,
                "status": "queued",
                "progress_percent": 0,
                "step_name": "排队中",
                "message": "文档在队列中等待处理"
            }
        else:
            result = {
                "document_id": document_id,
                "status": "pending",
                "progress_percent": 0,
                "step_name": "等待处理",
                "message": "文档等待处理，请手动启动"
            }

        # 更新缓存
        _document_progress_cache[cache_key] = result
        _document_progress_cache_time[cache_key] = current_time
        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"获取处理进度错误: {str(e)}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取处理进度失败: {str(e)}")


@router.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档处理状态（简化版）

    用于前端查询文档当前处理状态
    """
    try:
        document = await run_in_threadpool(
            lambda: db.query(KnowledgeDocumentModel).filter(
                KnowledgeDocumentModel.id == document_id
            ).first()
        )

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        metadata = document.document_metadata or {}
        processing_status = metadata.get('processing_status', 'unknown')

        return {
            "document_id": document_id,
            "status": processing_status,
            "progress": 100 if processing_status == 'completed' else 0,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档状态失败: {str(e)}")


@router.get("/processing-queue/status")
async def get_processing_queue_status():
    """
    获取文档处理队列状态

    用于前端查看当前处理队列的情况
    """
    try:
        queue_status = document_processing_queue.get_queue_status()
        return queue_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """下载文档（支持ID或UUID）"""
    try:
        # 根据ID或UUID获取文档
        document = knowledge_service.get_document_by_id_or_uuid(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        file_path, filename = knowledge_service.download_document(db, document.id)
        if not file_path:
            raise HTTPException(status_code=404, detail="文档不存在或文件已丢失")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

@router.get("/documents/{document_id}/preview")
async def preview_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """预览文档（支持ID或UUID）"""
    try:
        # 根据ID或UUID获取文档
        document = knowledge_service.get_document_by_id_or_uuid(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        file_path, filename = knowledge_service.download_document(db, document.id)
        if not file_path:
            raise HTTPException(status_code=404, detail="文档不存在或文件已丢失")

        # 根据文件类型设置不同的媒体类型
        file_type = document.file_type.lower() if document.file_type else ""
        media_type = "application/octet-stream"

        if file_type == "pdf":
            media_type = "application/pdf"
        elif file_type in ["jpg", "jpeg"]:
            media_type = "image/jpeg"
        elif file_type == "png":
            media_type = "image/png"
        elif file_type == "gif":
            media_type = "image/gif"
        elif file_type == "txt":
            media_type = "text/plain"
        elif file_type == "md":
            media_type = "text/markdown"

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@router.get("/documents/{document_id}/chunks", response_model=List[KnowledgeDocumentChunk])
async def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db)
):
    """获取文档的向量片段列表（支持ID或UUID）"""
    try:
        # 根据ID或UUID获取文档
        document = knowledge_service.get_document_by_id_or_uuid(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        chunks = knowledge_service.get_document_chunks(document.id, db)
        return chunks
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档向量片段失败: {str(e)}")
        # 出错时返回空列表，避免500错误
        return []

@router.get("/stats")
async def get_knowledge_stats(db: Session = Depends(get_db)):
    """获取知识库统计信息"""
    try:
        # 查询文档总数
        total_documents = db.query(KnowledgeDocumentModel).count()

        # 查询已向量化文档数（使用 processing_status = 'completed'）
        # 注意：SQLite不支持.astext，需要在Python中过滤
        all_docs = db.query(KnowledgeDocumentModel).all()
        vector_documents = 0
        for doc in all_docs:
            metadata = doc.document_metadata or {}
            if metadata.get('processing_status') == 'completed':
                vector_documents += 1

        # 查询知识库数量
        knowledge_bases_count = db.query(KnowledgeBaseModel).count()

        return {
            "total_documents": total_documents,
            "vector_documents": vector_documents,
            "knowledge_bases_count": knowledge_bases_count,
            "supported_formats": [".pdf", ".docx", ".doc", ".txt"]
        }
    except Exception as e:
        import traceback
        print(f"获取统计信息错误: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# Knowledge Tag API Endpoints
@router.get("/tags", response_model=TagListResponse)
async def get_all_tags(
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID过滤标签"),
    db: Session = Depends(get_db)
):
    """获取所有标签，可选按知识库过滤"""
    try:
        tags = knowledge_service.get_all_tags(db, knowledge_base_id)
        return {"tags": tags, "total": len(tags)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取标签失败")

@router.get("/documents/{document_id}/tags", response_model=DocumentTagsResponse)
async def get_document_tags(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有标签"""
    try:
        tags = knowledge_service.get_document_tags(document_id, db)
        return {"document_id": document_id, "tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取文档标签失败")

@router.post("/documents/{document_id}/process")
async def process_document(
    document_id: str,
    force: bool = Query(False, description="强制重新处理，即使文档已完成处理"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    手动启动文档处理（向量化、图谱化）

    上传文档后，调用此接口启动后续处理流程

    参数:
        force: 设置为true可强制重新处理已完成的文档
    """
    logger.info(f"[process_document] 收到文档处理请求: {document_id}, force={force}")
    try:
        # 检查文档是否存在（支持ID或UUID）
        document = knowledge_service.get_document_by_id_or_uuid(document_id, db)
        logger.info(f"[process_document] 文档查询结果: {document}")
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查文档是否已向量化（使用 processing_status = 'completed'）
        current_status = document.document_metadata.get("processing_status") if document.document_metadata else None

        # 如果强制重新处理，重置状态
        if force and current_status == "completed":
            logger.info(f"[process_document] 强制重新处理文档: {document_id}")
            document.document_metadata["processing_status"] = "pending"
            document.document_metadata["vectorization_rate"] = 0
            document.document_metadata["success_count"] = 0
            from sqlalchemy.orm import attributes
            attributes.flag_modified(document, "document_metadata")
            db.commit()
            current_status = "pending"

        if current_status == "completed":
            return {
                "message": "文档已处理完成",
                "document_id": document_id,
                "status": "completed"
            }

        # 检查是否已经在处理中
        if current_status == "processing":
            return {
                "message": "文档正在处理中",
                "document_id": document_id,
                "status": "processing"
            }

        if current_status == "queued":
            return {
                "message": "文档已在队列中等待处理",
                "document_id": document_id,
                "status": "queued"
            }

        # 检查处理队列状态
        queue_status = document_processing_queue.get_queue_status()

        # 如果队列已满，提示用户稍后再试
        if queue_status["queue_size"] + queue_status["processing_count"] >= 5:
            document.document_metadata["processing_status"] = "queued"
            db.commit()

            return {
                "message": "处理队列已满，请稍后再试",
                "document_id": document_id,
                "status": "queue_full",
                "queue_status": queue_status
            }

        # 添加到处理队列
        logger.info(f"[process_document] 尝试添加文档到队列: {document.id}")
        added = await document_processing_queue.add_document(
            document_id=document.id,
            knowledge_base_id=document.knowledge_base_id,
            document_name=document.title,
            priority=0
        )
        logger.info(f"[process_document] 文档添加到队列结果: {added}")

        if added:
            # 更新文档状态为排队中
            document.document_metadata["processing_status"] = "queued"
            db.commit()

            return {
                "message": "文档已加入处理队列",
                "document_id": document.id,
                "status": "queued",
                "queue_position": queue_status["queue_size"] + 1
            }
        else:
            # 如果添加失败，使用后台任务处理
            logger.info(f"[process_document] 队列添加失败，使用后台任务处理: {document.id}")
            if background_tasks:
                background_tasks.add_task(
                    knowledge_service.process_document_async,
                    document.id,
                    document.knowledge_base_id
                )
            else:
                import asyncio
                asyncio.create_task(
                    knowledge_service.process_document_async(document.id, document.knowledge_base_id)
                )

            return {
                "message": "文档处理已启动",
                "document_id": document.id,
                "status": "processing"
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理启动失败: {str(e)}")

@router.post("/documents/{document_id}/vectorize")
async def vectorize_document(
    document_id: int,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """启动文档向量化处理 - 异步后台执行（兼容旧接口）"""
    # 直接调用新的处理接口
    return await process_document(document_id, background_tasks, db)

@router.post("/documents/{document_id}/tags", response_model=KnowledgeTag)
async def add_document_tag(
    document_id: int,
    tag_request: DocumentTagRequest,
    db: Session = Depends(get_db)
):
    """为文档添加标签"""
    try:
        tag = knowledge_service.add_document_tag(document_id, tag_request.tag_name, db)
        return tag
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="添加标签失败")

@router.delete("/documents/{document_id}/tags/{tag_id}")
async def remove_document_tag(
    document_id: int,
    tag_id: int,
    db: Session = Depends(get_db)
):
    """从文档中移除标签"""
    try:
        success = knowledge_service.remove_document_tag(document_id, tag_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="标签或文档不存在")
        return {"message": "标签移除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="移除标签失败")

@router.get("/tags/{tag_id}/documents", response_model=DocumentListResponse)
async def search_documents_by_tag(
    tag_id: int,
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID过滤文档"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """根据标签搜索文档"""
    try:
        documents = knowledge_service.search_documents_by_tag(tag_id, db, knowledge_base_id)
        
        # 应用分页
        paginated_documents = documents[skip:skip+limit]
        
        # 转换为Pydantic模型
        document_models = [
            KnowledgeDocument(
                id=doc.id,
                title=doc.title,
                knowledge_base_id=doc.knowledge_base_id,
                file_path=doc.file_path,
                file_type=doc.file_type,
                content=doc.content,
                document_metadata=doc.document_metadata,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                vector_id=doc.vector_id
            ) for doc in paginated_documents
        ]
        
        return {
            "documents": document_models,
            "skip": skip,
            "limit": limit,
            "total": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="按标签搜索文档失败")

# Document Version Control API Endpoints
from pydantic import BaseModel
from typing import List, Optional

class DocumentVersion(BaseModel):
    id: int
    title: str
    version: int
    is_current: bool
    created_at: str
    updated_at: Optional[str]
    content_preview: Optional[str]

class DocumentVersionsResponse(BaseModel):
    document_id: int
    current_version: DocumentVersion
    versions: List[DocumentVersion]
    total_versions: int

class UpdateDocumentRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class UpdateProcessingStatusRequest(BaseModel):
    processing_status: str



# Document Version Control API Endpoints
@router.get("/documents/{document_id}/versions", response_model=DocumentVersionsResponse)
async def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有版本"""
    try:
        versions = knowledge_service.get_document_versions(document_id, db)
        if not versions:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取当前版本
        current_version = next((v for v in versions if v.is_current), versions[0])
        
        # 转换为响应模型
        version_models = []
        for version in versions:
            version_models.append(DocumentVersion(
                id=version.id,
                title=version.title,
                version=version.version,
                is_current=version.is_current,
                created_at=version.created_at.isoformat() if version.created_at else None,
                updated_at=version.updated_at.isoformat() if version.updated_at else None,
                content_preview=version.content[:200] + "..." if version.content and len(version.content) > 200 else version.content
            ))
        
        current_version_model = DocumentVersion(
            id=current_version.id,
            title=current_version.title,
            version=current_version.version,
            is_current=current_version.is_current,
            created_at=current_version.created_at.isoformat() if current_version.created_at else None,
            updated_at=current_version.updated_at.isoformat() if current_version.updated_at else None,
            content_preview=current_version.content[:200] + "..." if current_version.content and len(current_version.content) > 200 else current_version.content
        )
        
        return DocumentVersionsResponse(
            document_id=document_id,
            current_version=current_version_model,
            versions=version_models,
            total_versions=len(versions)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档版本失败: {str(e)}")

@router.put("/documents/{document_id}", response_model=KnowledgeDocument)
async def update_document_with_version(
    document_id: int,
    update_request: UpdateDocumentRequest,
    db: Session = Depends(get_db)
):
    """更新文档并创建新版本"""
    try:
        update_data = {}
        if update_request.title is not None:
            update_data["title"] = update_request.title
        if update_request.content is not None:
            update_data["content"] = update_request.content
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        updated_document = knowledge_service.update_document_with_version(document_id, update_data, db)
        if not updated_document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return KnowledgeDocument(
            id=updated_document.id,
            title=updated_document.title,
            knowledge_base_id=updated_document.knowledge_base_id,
            file_path=updated_document.file_path,
            file_type=updated_document.file_type,
            content=updated_document.content,
            document_metadata=updated_document.document_metadata,
            created_at=updated_document.created_at,
            updated_at=updated_document.updated_at,
            vector_id=updated_document.vector_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文档失败: {str(e)}")

@router.put("/documents/{document_id}/processing-status", response_model=KnowledgeDocument)
async def update_document_processing_status(
    document_id: int,
    request: UpdateProcessingStatusRequest,
    db: Session = Depends(get_db)
):
    """更新文档处理状态

    支持的状态值：
    - idle, pending: 待向量化
    - queued: 排队中
    - processing: 向量化中
    - completed: 已向量化
    - entity_processing: 实体识别中
    - entity_aggregating: 实体聚合中
    - entity_aligning: 实体对齐中
    - entity_completed: 已实体识别
    - failed: 处理失败
    - entity_failed: 实体识别失败
    """
    try:
        # 获取文档
        document = knowledge_service.get_document_by_id(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 更新document_metadata中的processing_status
        metadata = document.document_metadata or {}
        metadata['processing_status'] = request.processing_status
        document.document_metadata = metadata

        db.commit()
        db.refresh(document)

        return KnowledgeDocument(
            id=document.id,
            title=document.title,
            knowledge_base_id=document.knowledge_base_id,
            file_path=document.file_path,
            file_type=document.file_type,
            content=document.content,
            document_metadata=document.document_metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            vector_id=document.vector_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文档处理状态失败: {str(e)}")

@router.get("/documents/{document_id}/versions/{version_id}", response_model=KnowledgeDocument)
async def get_document_version(
    document_id: int,
    version_id: int,
    db: Session = Depends(get_db)
):
    """获取特定版本的文档"""
    try:
        document = knowledge_service.get_document_version(document_id, version_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档或版本不存在")
        
        return KnowledgeDocument(
            id=document.id,
            title=document.title,
            knowledge_base_id=document.knowledge_base_id,
            file_path=document.file_path,
            file_type=document.file_type,
            content=document.content,
            document_metadata=document.document_metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            vector_id=document.vector_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档版本失败: {str(e)}")

@router.post("/documents/{document_id}/versions/{version_id}/restore", response_model=KnowledgeDocument)
async def restore_document_version(
    document_id: int,
    version_id: int,
    db: Session = Depends(get_db)
):
    """恢复文档到指定版本"""
    try:
        restored_document = knowledge_service.restore_document_version(document_id, version_id, db)
        if not restored_document:
            raise HTTPException(status_code=404, detail="文档或版本不存在")

        return KnowledgeDocument(
            id=restored_document.id,
            title=restored_document.title,
            knowledge_base_id=restored_document.knowledge_base_id,
            file_path=restored_document.file_path,
            file_type=restored_document.file_type,
            content=restored_document.content,
            document_metadata=restored_document.document_metadata,
            created_at=restored_document.created_at,
            updated_at=restored_document.updated_at,
            vector_id=restored_document.vector_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复文档版本失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/export")
async def export_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    导出知识库

    导出知识库的所有文档、标签和元数据为JSON格式
    """
    try:
        # 检查知识库是否存在
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 获取知识库的所有文档
        documents = knowledge_service.list_documents(db, skip=0, limit=10000, knowledge_base_id=knowledge_base_id)

        # 获取知识库的所有标签
        tags = knowledge_service.get_all_tags(db, knowledge_base_id)

        # 构建导出数据
        export_data = {
            "knowledge_base": {
                "id": knowledge_base.id,
                "name": knowledge_base.name,
                "description": knowledge_base.description,
                "created_at": knowledge_base.created_at.isoformat() if knowledge_base.created_at else None,
                "updated_at": knowledge_base.updated_at.isoformat() if knowledge_base.updated_at else None
            },
            "documents": [],
            "tags": []
        }

        # 添加文档数据
        for doc in documents:
            doc_data = {
                "id": doc.id,
                "title": doc.title,
                "file_type": doc.file_type,
                "content": doc.content,
                "file_path": doc.file_path,
                "processing_status": doc.document_metadata.get("processing_status", "unknown") if doc.document_metadata else "unknown",
                "vector_id": doc.vector_id,
                "document_metadata": doc.document_metadata,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            }
            export_data["documents"].append(doc_data)

        # 添加标签数据
        for tag in tags:
            tag_data = {
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "created_at": tag.created_at.isoformat() if tag.created_at else None
            }
            export_data["tags"].append(tag_data)

        return export_data

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"导出知识库失败: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出知识库失败: {str(e)}")


@router.post("/knowledge-bases/import")
async def import_knowledge_base(
    import_data: dict,
    db: Session = Depends(get_db)
):
    """
    导入知识库

    从JSON数据导入知识库，包括文档、标签和元数据
    """
    try:
        # 验证导入数据
        if "knowledge_base" not in import_data:
            raise HTTPException(status_code=400, detail="导入数据格式错误：缺少知识库信息")

        kb_data = import_data["knowledge_base"]

        # 检查知识库名称是否已存在
        existing_kb = db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.name == kb_data.get("name")).first()
        if existing_kb:
            raise HTTPException(status_code=400, detail="知识库名称已存在")

        # 创建新知诀库
        new_kb = knowledge_service.create_knowledge_base(
            name=kb_data.get("name"),
            description=kb_data.get("description"),
            db=db
        )

        # 导入标签
        tag_mapping = {}  # 旧标签ID映射到新标签ID
        if "tags" in import_data:
            for tag_data in import_data["tags"]:
                # 创建新标签
                from app.modules.knowledge.models.knowledge_document import KnowledgeTag
                new_tag = KnowledgeTag(
                    name=tag_data.get("name"),
                    color=tag_data.get("color", "#1890ff")
                )
                db.add(new_tag)
                db.commit()
                db.refresh(new_tag)
                tag_mapping[tag_data.get("id")] = new_tag.id

        # 导入文档
        imported_count = 0
        if "documents" in import_data:
            for doc_data in import_data["documents"]:
                # 创建文档记录
                # 准备文档元数据，设置处理状态为 pending
                doc_metadata = doc_data.get("document_metadata", {}) or {}
                doc_metadata["processing_status"] = "pending"
                doc_metadata["imported_from"] = kb_data.get("id")

                new_doc = KnowledgeDocumentModel(
                    title=doc_data.get("title"),
                    knowledge_base_id=new_kb.id,
                    file_path=doc_data.get("file_path"),
                    file_type=doc_data.get("file_type"),
                    content=doc_data.get("content", ""),
                    vector_id=None,
                    document_metadata=doc_metadata
                )

                db.add(new_doc)
                db.commit()
                db.refresh(new_doc)
                imported_count += 1

        return {
            "message": "知识库导入成功",
            "knowledge_base_id": new_kb.id,
            "knowledge_base_name": new_kb.name,
            "imported_documents": imported_count,
            "imported_tags": len(tag_mapping)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"导入知识库失败: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导入知识库失败: {str(e)}")


# Knowledge Base Permission API Endpoints

@router.get("/knowledge-bases/{knowledge_base_id}/permissions", response_model=KnowledgeBasePermissionListResponse)
async def get_knowledge_base_permissions(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识库的权限列表
    
    返回指定知识库的所有用户权限
    """
    try:
        # 检查知识库是否存在
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 查询权限列表
        permissions = db.query(KnowledgeBasePermissionModel).filter(
            KnowledgeBasePermissionModel.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 转换为响应模型
        permission_list = []
        for perm in permissions:
            permission_list.append(KnowledgeBasePermission(
                id=perm.id,
                knowledge_base_id=perm.knowledge_base_id,
                user_id=perm.user_id,
                role=perm.role,
                created_at=perm.created_at,
                updated_at=perm.updated_at
            ))
        
        return {
            "permissions": permission_list,
            "total": len(permission_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"获取知识库权限失败: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取知识库权限失败: {str(e)}")


@router.post("/knowledge-bases/{knowledge_base_id}/permissions", response_model=KnowledgeBasePermission)
async def add_knowledge_base_permission(
    knowledge_base_id: int,
    permission_data: KnowledgeBasePermissionCreate,
    db: Session = Depends(get_db)
):
    """
    为知识库添加用户权限
    
    支持的角色: admin(管理员), editor(编辑者), viewer(查看者)
    """
    try:
        # 检查知识库是否存在
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 验证角色有效性
        valid_roles = ["admin", "editor", "viewer"]
        if permission_data.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"无效的角色，必须是以下之一: {', '.join(valid_roles)}")
        
        # 检查用户是否已有权限
        existing_perm = db.query(KnowledgeBasePermissionModel).filter(
            KnowledgeBasePermissionModel.knowledge_base_id == knowledge_base_id,
            KnowledgeBasePermissionModel.user_id == permission_data.user_id
        ).first()
        
        if existing_perm:
            # 更新现有权限
            existing_perm.role = permission_data.role
            existing_perm.updated_at = func.now()
            db.commit()
            db.refresh(existing_perm)
            
            return KnowledgeBasePermission(
                id=existing_perm.id,
                knowledge_base_id=existing_perm.knowledge_base_id,
                user_id=existing_perm.user_id,
                role=existing_perm.role,
                created_at=existing_perm.created_at,
                updated_at=existing_perm.updated_at
            )
        
        # 创建新权限
        new_permission = KnowledgeBasePermissionModel(
            knowledge_base_id=knowledge_base_id,
            user_id=permission_data.user_id,
            role=permission_data.role
        )
        db.add(new_permission)
        db.commit()
        db.refresh(new_permission)
        
        return KnowledgeBasePermission(
            id=new_permission.id,
            knowledge_base_id=new_permission.knowledge_base_id,
            user_id=new_permission.user_id,
            role=new_permission.role,
            created_at=new_permission.created_at,
            updated_at=new_permission.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"添加知识库权限失败: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"添加知识库权限失败: {str(e)}")


@router.put("/knowledge-bases/{knowledge_base_id}/permissions")
async def update_knowledge_base_permissions(
    knowledge_base_id: int,
    update_data: KnowledgeBasePermissionsUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    批量更新知识库权限
    
    替换知识库的所有权限设置
    """
    try:
        # 检查知识库是否存在
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 验证所有角色
        valid_roles = ["admin", "editor", "viewer"]
        for perm in update_data.permissions:
            if perm.role not in valid_roles:
                raise HTTPException(status_code=400, detail=f"无效的角色 '{perm.role}'，必须是以下之一: {', '.join(valid_roles)}")
        
        # 删除现有权限
        db.query(KnowledgeBasePermissionModel).filter(
            KnowledgeBasePermissionModel.knowledge_base_id == knowledge_base_id
        ).delete()
        
        # 创建新权限
        new_permissions = []
        for perm_data in update_data.permissions:
            new_perm = KnowledgeBasePermissionModel(
                knowledge_base_id=knowledge_base_id,
                user_id=perm_data.user_id,
                role=perm_data.role
            )
            db.add(new_perm)
            new_permissions.append(new_perm)
        
        db.commit()
        
        # 刷新所有新权限以获取ID
        for perm in new_permissions:
            db.refresh(perm)
        
        # 转换为响应模型
        permission_list = [
            KnowledgeBasePermission(
                id=perm.id,
                knowledge_base_id=perm.knowledge_base_id,
                user_id=perm.user_id,
                role=perm.role,
                created_at=perm.created_at,
                updated_at=perm.updated_at
            ) for perm in new_permissions
        ]
        
        return {
            "permissions": permission_list,
            "total": len(permission_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"更新知识库权限失败: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"更新知识库权限失败: {str(e)}")


@router.delete("/knowledge-bases/{knowledge_base_id}/permissions/{permission_id}")
async def remove_knowledge_base_permission(
    knowledge_base_id: int,
    permission_id: int,
    db: Session = Depends(get_db)
):
    """
    删除知识库的指定权限
    """
    try:
        # 检查知识库是否存在
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 查询权限
        permission = db.query(KnowledgeBasePermissionModel).filter(
            KnowledgeBasePermissionModel.id == permission_id,
            KnowledgeBasePermissionModel.knowledge_base_id == knowledge_base_id
        ).first()
        
        if not permission:
            raise HTTPException(status_code=404, detail="权限记录不存在")
        
        # 删除权限
        db.delete(permission)
        db.commit()
        
        return {"message": "权限删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"删除知识库权限失败: {str(e)}")
        print(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"删除知识库权限失败: {str(e)}")


@router.post("/knowledge-bases/{knowledge_base_id}/batch-process")
async def batch_process_documents(
    knowledge_base_id: int,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    批量处理知识库中所有未处理的文档

    该接口会将知识库中所有尚未向量化的文档（content为空或未向量化的文档）
    添加到处理队列中进行解析、向量化、实体提取和知识图谱构建。

    Args:
        knowledge_base_id: 知识库ID
        background_tasks: 后台任务

    Returns:
        处理结果统计信息
    """
    try:
        # 检查知识库是否存在
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 获取知识库中所有文档，然后在Python中过滤未处理的
        # 条件：processing_status != 'completed' 或 content为空
        all_docs = db.query(KnowledgeDocumentModel).filter(
            KnowledgeDocumentModel.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 在Python中过滤未处理的文档
        unprocessed_docs = []
        for doc in all_docs:
            metadata = doc.document_metadata or {}
            status = metadata.get('processing_status')
            if status != 'completed' or not doc.content:
                unprocessed_docs.append(doc)

        if not unprocessed_docs:
            return {
                "success": True,
                "message": "知识库中没有需要处理的文档",
                "total_documents": 0,
                "queued_documents": 0,
                "skipped_documents": 0
            }

        total_count = len(unprocessed_docs)
        queued_count = 0
        skipped_count = 0
        failed_count = 0
        document_ids = []

        # 获取队列状态
        queue_status = document_processing_queue.get_queue_status()
        current_queue_size = queue_status["queue_size"] + queue_status["processing_count"]

        for document in unprocessed_docs:
            try:
                # 确保 document_metadata 不为 None
                if document.document_metadata is None:
                    document.document_metadata = {}

                # 检查文件是否存在
                if not document.file_path or not os.path.exists(document.file_path):
                    logger.warning(f"文档 {document.id} 的文件不存在，跳过处理")
                    document.document_metadata["processing_status"] = "failed"
                    document.document_metadata["processing_error"] = "文件不存在"
                    db.commit()
                    skipped_count += 1
                    continue

                # 添加到处理队列
                added = await document_processing_queue.add_document(
                    document_id=document.id,
                    knowledge_base_id=knowledge_base_id,
                    document_name=document.title,
                    priority=0
                )

                if added:
                    queued_count += 1
                    document_ids.append(document.id)
                    # 更新文档状态为排队中
                    document.document_metadata["processing_status"] = "queued"
                    db.commit()
                else:
                    # 如果队列添加失败，使用后台任务处理
                    if background_tasks:
                        background_tasks.add_task(
                            knowledge_service.process_document_async,
                            document.id,
                            knowledge_base_id
                        )
                    else:
                        import asyncio
                        asyncio.create_task(
                            knowledge_service.process_document_async(document.id, knowledge_base_id)
                        )
                    queued_count += 1
                    document_ids.append(document.id)

            except Exception as e:
                logger.error(f"添加文档 {document.id} 到处理队列失败: {e}")
                failed_count += 1
                # 确保 document_metadata 不为 None
                if document.document_metadata is None:
                    document.document_metadata = {}
                document.document_metadata["processing_status"] = "failed"
                document.document_metadata["processing_error"] = str(e)
                db.commit()

        return {
            "success": True,
            "message": f"批量处理已启动，共 {total_count} 个文档，成功加入队列 {queued_count} 个",
            "knowledge_base_id": knowledge_base_id,
            "knowledge_base_name": knowledge_base.name,
            "total_documents": total_count,
            "queued_documents": queued_count,
            "skipped_documents": skipped_count,
            "failed_documents": failed_count,
            "document_ids": document_ids,
            "queue_status": document_processing_queue.get_queue_status()
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"批量处理文档失败: {str(e)}")
        logger.error(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"批量处理文档失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}/unprocessed-documents")
async def get_unprocessed_documents(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识库中所有未处理的文档列表

    Args:
        knowledge_base_id: 知识库ID

    Returns:
        未处理文档列表
    """
    try:
        # 检查知识库是否存在
        knowledge_base = knowledge_service.get_knowledge_base(knowledge_base_id, db)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 获取所有文档，然后在Python中过滤未处理的
        all_docs = db.query(KnowledgeDocumentModel).filter(
            KnowledgeDocumentModel.knowledge_base_id == knowledge_base_id
        ).all()
        
        # 在Python中过滤未处理的文档
        unprocessed_docs = []
        for doc in all_docs:
            metadata = doc.document_metadata or {}
            status = metadata.get('processing_status')
            if status != 'completed' or not doc.content:
                unprocessed_docs.append(doc)

        documents_list = []
        for doc in unprocessed_docs:
            # 安全获取 document_metadata
            metadata = doc.document_metadata or {}
            doc_info = {
                "id": doc.id,
                "title": doc.title,
                "file_type": doc.file_type,
                "has_content": bool(doc.content and doc.content.strip()),
                "content_length": len(doc.content) if doc.content else 0,
                "processing_status": metadata.get("processing_status", "unknown"),
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }
            documents_list.append(doc_info)

        return {
            "success": True,
            "knowledge_base_id": knowledge_base_id,
            "knowledge_base_name": knowledge_base.name,
            "total_unprocessed": len(documents_list),
            "documents": documents_list
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"获取未处理文档列表失败: {str(e)}")
        logger.error(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取未处理文档列表失败: {str(e)}")


def _get_processing_status_sync(knowledge_base_id: int, db: Session):
    """
    同步获取处理状态的辅助函数
    
    在线程池中执行数据库查询，避免阻塞事件循环
    使用轻量级查询优化性能 - 只查询需要的字段
    """
    # 检查知识库是否存在（只查询需要的字段）
    knowledge_base = db.query(KnowledgeBaseModel).filter(
        KnowledgeBaseModel.id == knowledge_base_id
    ).with_entities(KnowledgeBaseModel.id, KnowledgeBaseModel.name).first()

    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 使用数据库级别的统计查询，避免加载所有文档
    # 首先获取总数
    total = db.query(KnowledgeDocumentModel).filter(
        KnowledgeDocumentModel.knowledge_base_id == knowledge_base_id
    ).count()
    
    # 使用SQLite的json_extract函数在数据库层面统计
    # completed状态的文档数
    completed_result = db.execute(
        text("""SELECT COUNT(*) FROM knowledge_documents 
           WHERE knowledge_base_id = :kb_id 
           AND json_extract(document_metadata, '$.processing_status') = 'completed'"""),
        {"kb_id": knowledge_base_id}
    ).scalar()
    vectorized = completed_result or 0
    
    # 未处理的文档数 = 总数 - 已完成的
    unprocessed = total - vectorized

    # 创建轻量级对象
    kb_result = type('KBResult', (), {'name': knowledge_base.name})()

    return {
        "knowledge_base": kb_result,
        "total_docs": total,
        "vectorized_docs": vectorized,
        "unprocessed_docs": unprocessed
    }


@router.get("/knowledge-bases/{knowledge_base_id}/processing-status")
async def get_processing_status(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识库文档处理状态

    返回当前处理队列的状态，包括：
    - 队列中等待处理的文档数
    - 正在处理的文档数
    - 已完成的文档数
    - 处理失败的文档数
    - 正在处理的具体文档列表

    使用缓存机制和并发控制避免频繁查询数据库

    Args:
        knowledge_base_id: 知识库ID

    Returns:
        处理状态信息
    """
    global _processing_status_cache, _processing_status_cache_time
    global _processing_status_locks, _processing_status_pending

    current_time = time.time()

    # 检查缓存是否有效
    if knowledge_base_id in _processing_status_cache:
        cache_age = current_time - _processing_status_cache_time.get(knowledge_base_id, 0)
        if cache_age < CACHE_TTL:
            # 缓存有效，直接返回（但队列状态需要实时更新）
            logger.debug(f"[处理状态] 使用缓存: knowledge_base_id={knowledge_base_id}, age={cache_age:.2f}s")
            cached_result = _processing_status_cache[knowledge_base_id].copy()
            # 队列状态实时获取
            queue_status = document_processing_queue.get_queue_status()
            cached_result["queue_status"] = {
                "queue_size": queue_status["queue_size"],
                "processing_count": queue_status["processing_count"],
                "completed_count": queue_status["completed_count"],
                "failed_count": queue_status["failed_count"],
                "max_concurrent": queue_status["max_concurrent"]
            }
            cached_result["processing_documents"] = queue_status["processing_documents"]
            return cached_result

    # 并发控制：如果有其他请求正在查询同一知识库，等待其结果
    if knowledge_base_id in _processing_status_pending:
        logger.debug(f"[处理状态] 等待其他请求结果: knowledge_base_id={knowledge_base_id}")
        try:
            result = await asyncio.wait_for(
                _processing_status_pending[knowledge_base_id],
                timeout=30.0
            )
            # 获取最新的队列状态
            queue_status = document_processing_queue.get_queue_status()
            result["queue_status"] = {
                "queue_size": queue_status["queue_size"],
                "processing_count": queue_status["processing_count"],
                "completed_count": queue_status["completed_count"],
                "failed_count": queue_status["failed_count"],
                "max_concurrent": queue_status["max_concurrent"]
            }
            result["processing_documents"] = queue_status["processing_documents"]
            return result
        except asyncio.TimeoutError:
            logger.warning(f"[处理状态] 等待其他请求超时: knowledge_base_id={knowledge_base_id}")

    # 创建锁和Future
    if knowledge_base_id not in _processing_status_locks:
        _processing_status_locks[knowledge_base_id] = asyncio.Lock()

    lock = _processing_status_locks[knowledge_base_id]

    async with lock:
        # 再次检查缓存（可能在等待锁的过程中其他请求已更新缓存）
        if knowledge_base_id in _processing_status_cache:
            cache_age = current_time - _processing_status_cache_time.get(knowledge_base_id, 0)
            if cache_age < CACHE_TTL:
                logger.debug(f"[处理状态] 锁内使用缓存: knowledge_base_id={knowledge_base_id}, age={cache_age:.2f}s")
                cached_result = _processing_status_cache[knowledge_base_id].copy()
                queue_status = document_processing_queue.get_queue_status()
                cached_result["queue_status"] = {
                    "queue_size": queue_status["queue_size"],
                    "processing_count": queue_status["processing_count"],
                    "completed_count": queue_status["completed_count"],
                    "failed_count": queue_status["failed_count"],
                    "max_concurrent": queue_status["max_concurrent"]
                }
                cached_result["processing_documents"] = queue_status["processing_documents"]
                return cached_result

        # 创建Future，让其他并发请求可以等待
        future = asyncio.Future()
        _processing_status_pending[knowledge_base_id] = future

    # 在锁外执行数据库查询，减少锁持有时间
    try:
        logger.info(f"[处理状态] 开始查询数据库: knowledge_base_id={knowledge_base_id}")
        start_time = time.time()

        # 获取队列状态（非阻塞操作）
        queue_status = document_processing_queue.get_queue_status()

        # 在线程池中执行数据库查询，避免阻塞事件循环
        result = await run_in_threadpool(_get_processing_status_sync, knowledge_base_id, db)

        response_data = {
            "success": True,
            "knowledge_base_id": knowledge_base_id,
            "knowledge_base_name": result["knowledge_base"].name,
            "statistics": {
                "total_documents": result["total_docs"],
                "vectorized_documents": result["vectorized_docs"],
                "unprocessed_documents": result["unprocessed_docs"],
                "vectorization_rate": round(result["vectorized_docs"] / result["total_docs"] * 100, 2) if result["total_docs"] > 0 else 0
            },
            "queue_status": {
                "queue_size": queue_status["queue_size"],
                "processing_count": queue_status["processing_count"],
                "completed_count": queue_status["completed_count"],
                "failed_count": queue_status["failed_count"],
                "max_concurrent": queue_status["max_concurrent"]
            },
            "processing_documents": queue_status["processing_documents"]
        }

        query_time = time.time() - start_time
        logger.info(f"[处理状态] 查询完成: knowledge_base_id={knowledge_base_id}, 耗时={query_time:.2f}s")

        # 通知等待的请求
        if not future.done():
            future.set_result(response_data.copy())

        # 更新缓存（在锁内）
        async with lock:
            _processing_status_cache[knowledge_base_id] = response_data
            _processing_status_cache_time[knowledge_base_id] = time.time()

        return response_data

    except HTTPException:
        # 通知等待的请求出错
        if not future.done():
            future.set_exception(HTTPException(status_code=500, detail="查询失败"))
        raise
    except Exception as e:
        # 通知等待的请求出错
        if not future.done():
            future.set_exception(e)
        import traceback
        logger.error(f"获取处理状态失败: {str(e)}")
        logger.error(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取处理状态失败: {str(e)}")
    finally:
        # 清理pending
        if knowledge_base_id in _processing_status_pending:
            del _processing_status_pending[knowledge_base_id]


@router.post("/knowledge-bases/{knowledge_base_id}/sync-status")
async def sync_knowledge_base_status(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    同步知识库的向量化状态
    
    查询ChromaDB中已向量化的文档，并同步更新数据库中的状态
    用于修复服务重启后状态不一致的问题
    
    Args:
        knowledge_base_id: 知识库ID
        
    Returns:
        同步结果统计
    """
    try:
        # 检查知识库是否存在
        knowledge_base = db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == knowledge_base_id
        ).first()
        
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 执行状态同步
        result = await knowledge_service.sync_vectorization_status(knowledge_base_id, db)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "状态同步完成",
                "knowledge_base_id": knowledge_base_id,
                "statistics": result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "同步失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步知识库状态失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


# ==================== 异步文档加载任务状态管理 ====================

# 内存中的文档加载任务状态存储
_document_load_tasks: Dict[str, Dict[str, Any]] = {}


def _update_document_load_progress(task_id: str, current: int, total: int,
                                    message: str = "", loaded_count: int = 0):
    """
    更新文档加载任务进度
    
    Args:
        task_id: 任务ID
        current: 当前加载的文档索引
        total: 总文档数
        message: 进度消息
        loaded_count: 已加载的文档数量
    """
    if task_id in _document_load_tasks:
        progress = (current / total * 100) if total > 0 else 0
        _document_load_tasks[task_id].update({
            "progress": round(progress, 2),
            "loaded_documents": current,
            "total_documents": total,
            "current_message": message,
            "updated_at": datetime.now().isoformat()
        })
        
        # 通过WebSocket广播进度
        _broadcast_document_load_progress(task_id)


def _broadcast_document_load_progress(task_id: str):
    """
    通过WebSocket广播文档加载进度
    
    Args:
        task_id: 任务ID
    """
    if task_id not in _document_load_tasks:
        return
        
    task = _document_load_tasks[task_id]
    try:
        from app.websocket.message_handler import message_handler
        import asyncio
        
        # 获取知识库ID作为订阅组
        knowledge_base_id = task.get("knowledge_base_id")
        if knowledge_base_id:
            # 广播到知识库文档加载进度组
            progress_msg = {
                "type": "document_load_progress",
                "task_id": task_id,
                "knowledge_base_id": knowledge_base_id,
                "status": task.get("status", "loading"),
                "progress": task.get("progress", 0),
                "loaded_documents": task.get("loaded_documents", 0),
                "total_documents": task.get("total_documents", 0),
                "current_message": task.get("current_message", ""),
                "updated_at": task.get("updated_at", "")
            }
            
            # 尝试在当前事件循环中广播
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(
                    message_handler.connection_manager.send_to_group(
                        f"kb_{knowledge_base_id}_document_load",
                        progress_msg
                    )
                )
            except RuntimeError:
                # 没有运行的事件循环，启动新线程
                import threading
                def run_broadcast():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        message_handler.connection_manager.send_to_group(
                            f"kb_{knowledge_base_id}_document_load",
                            progress_msg
                        )
                    )
                    loop.close()
                    
                thread = threading.Thread(target=run_broadcast, daemon=True)
                thread.start()
                
    except Exception as e:
        logger.debug(f"广播文档加载进度失败: {e}")


def _run_document_load_task(
    task_id: str,
    knowledge_base_id: int,
    skip: int = 0,
    limit: int = 100,
    processing_status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """
    后台执行文档加载任务（同步版本）

    Args:
        task_id: 任务ID
        knowledge_base_id: 知识库ID
        skip: 跳过的文档数
        limit: 返回的文档数限制
        processing_status: 处理状态筛选 (completed=已向量化, idle=待处理, processing=处理中, failed=失败)
        sort_by: 排序字段
        sort_order: 排序方向
    """
    from app.core.database import SessionLocal
    from datetime import datetime
    
    logger.info(f"[后台任务] 开始执行文档加载任务: task_id={task_id}, "
               f"knowledge_base_id={knowledge_base_id}, skip={skip}, limit={limit}, "
               f"processing_status={processing_status}")
    
    db = None
    try:
        db = SessionLocal()
        
        logger.info(f"[后台任务] 数据库连接成功，开始更新任务状态")
        
        # 更新任务状态为处理中
        _document_load_tasks[task_id].update({
            "status": "loading",
            "started_at": datetime.now().isoformat()
        })
        _broadcast_document_load_progress(task_id)
        
        logger.info(f"[后台任务] 任务状态已更新为loading")
        
        # 获取文档总数
        total_count = knowledge_service.get_document_count(db, knowledge_base_id, processing_status)
        logger.info(f"[后台任务] 文档总数: {total_count}")
        
        # 更新总文档数
        _document_load_tasks[task_id]["total_documents"] = total_count
        
        # 获取文档列表
        documents = knowledge_service.list_documents(db, skip, limit, knowledge_base_id, processing_status)
        logger.info(f"[后台任务] 获取到 {len(documents)} 个文档")
        
        # 获取队列状态
        queue_status = document_processing_queue.get_queue_status()
        processing_ids = {task["document_id"] for task in queue_status.get("processing_documents", [])}
        
        # 转换文档数据
        document_models = []
        has_updates = False  # 标记是否有需要更新的文档
        
        for i, doc in enumerate(documents):
            # 更新进度
            _update_document_load_progress(
                task_id, i + 1, len(documents),
                f"加载文档 {i + 1}/{len(documents)}"
            )
            
            # 检查文档状态是否与队列状态一致
            doc_metadata = doc.document_metadata or {}
            doc_status = doc_metadata.get("processing_status")

            # 如果文档标记为processing或queued，但不在队列中，重置状态
            if doc_status in ["processing", "queued"] and doc.id not in processing_ids:
                doc_metadata["processing_status"] = "idle"
                doc_metadata["processing_error"] = "服务重启，处理中断"
                doc.document_metadata = doc_metadata
                has_updates = True

            document_models.append({
                "id": doc.id,
                "uuid": doc.uuid,
                "title": doc.title,
                "knowledge_base_id": doc.knowledge_base_id,
                "file_path": doc.file_path,
                "file_type": doc.file_type,
                "content": None,  # 不返回完整内容
                "document_metadata": doc.document_metadata,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "vector_id": doc.vector_id,
                "file_hash": doc.file_hash
            })
        
        # 批量提交数据库更新，减少数据库操作次数
        if has_updates:
            db.commit()
            logger.info(f"[后台任务] 批量更新了文档状态")
        
        # 更新任务状态为完成
        _document_load_tasks[task_id].update({
            "status": "completed",
            "progress": 100.0,
            "loaded_documents": len(document_models),
            "documents": document_models,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "completed_at": datetime.now().isoformat()
        })
        _broadcast_document_load_progress(task_id)
        
        logger.info(f"[后台任务] 文档加载任务完成: task_id={task_id}, "
                   f"loaded={len(document_models)}, total={total_count}")
        
    except Exception as e:
        logger.error(f"[后台任务] 文档加载任务失败: {e}", exc_info=True)
        _document_load_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })
        _broadcast_document_load_progress(task_id)
    finally:
        if db:
            db.close()
        logger.info(f"[后台任务] 任务执行结束: task_id={task_id}")


# ==================== 异步文档加载API端点 ====================

class AsyncDocumentLoadRequest(BaseModel):
    """异步文档加载请求"""
    knowledge_base_id: int
    skip: int = 0
    limit: int = 100
    # is_vectorized 已移除，使用 processing_status 替代
    processing_status: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class AsyncDocumentLoadResponse(BaseModel):
    """异步文档加载响应"""
    success: bool
    task_id: str
    status: str
    message: str
    total_documents: int = 0


class DocumentLoadTaskStatus(BaseModel):
    """文档加载任务状态"""
    task_id: str
    status: str  # pending, loading, completed, failed
    progress: float
    total_documents: int
    loaded_documents: int
    current_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    documents: Optional[List[Dict[str, Any]]] = None
    total: Optional[int] = None
    skip: Optional[int] = None
    limit: Optional[int] = None


@router.post("/documents/load-async", response_model=AsyncDocumentLoadResponse)
async def load_documents_async(
    request: AsyncDocumentLoadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    异步加载文档列表
    
    启动后台任务进行文档加载，立即返回任务ID，
    前端可通过WebSocket订阅进度或轮询查询任务状态
    
    Args:
        request: 异步文档加载请求
        background_tasks: FastAPI后台任务
        db: 数据库会话
        
    Returns:
        任务信息，包含task_id用于查询进度
    """
    import uuid
    
    try:
        logger.info(f"[load_documents_async] 收到异步文档加载请求: "
                   f"knowledge_base_id={request.knowledge_base_id}, "
                   f"skip={request.skip}, limit={request.limit}")
        
        # 验证知识库是否存在
        kb = knowledge_service.get_knowledge_base(request.knowledge_base_id, db)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取文档总数
        total_count = knowledge_service.get_document_count(db, request.knowledge_base_id, request.processing_status)
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        _document_load_tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0.0,
            "total_documents": total_count,
            "loaded_documents": 0,
            "knowledge_base_id": request.knowledge_base_id,
            "created_at": datetime.now().isoformat()
        }
        
        # 启动后台任务
        background_tasks.add_task(
            _run_document_load_task,
            task_id=task_id,
            knowledge_base_id=request.knowledge_base_id,
            skip=request.skip,
            limit=request.limit,
            processing_status=request.processing_status,
            sort_by=request.sort_by,
            sort_order=request.sort_order
        )
        
        logger.info(f"[load_documents_async] 已启动后台任务: task_id={task_id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "pending",
            "message": f"已启动文档加载任务，共 {total_count} 个文档",
            "total_documents": total_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[load_documents_async] 启动任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动文档加载任务失败: {str(e)}")


@router.post("/documents/async", response_model=AsyncDocumentLoadResponse)
async def load_documents_async_alias(
    request: AsyncDocumentLoadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    异步加载文档列表（别名端点）

    与 /documents/load-async 功能相同，为前端提供兼容的 API 路径
    """
    return await load_documents_async(request, background_tasks, db)


@router.get("/documents/load-status/{task_id}", response_model=DocumentLoadTaskStatus)
async def get_document_load_status(task_id: str):
    """
    获取文档加载任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    if task_id not in _document_load_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = _document_load_tasks[task_id]
    
    return DocumentLoadTaskStatus(
        task_id=task["task_id"],
        status=task.get("status", "pending"),
        progress=task.get("progress", 0.0),
        total_documents=task.get("total_documents", 0),
        loaded_documents=task.get("loaded_documents", 0),
        current_message=task.get("current_message"),
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        error=task.get("error"),
        documents=task.get("documents"),
        total=task.get("total"),
        skip=task.get("skip"),
        limit=task.get("limit")
    )


@router.get("/documents/async/status/{task_id}", response_model=DocumentLoadTaskStatus)
async def get_document_load_status_alias(task_id: str):
    """
    获取文档加载任务状态（别名端点）

    与 /documents/load-status/{task_id} 功能相同，为前端提供兼容的 API 路径
    """
    return await get_document_load_status(task_id)


@router.post("/documents/subscribe-load/{knowledge_base_id}")
async def subscribe_document_load_progress(
    knowledge_base_id: int,
    connection_id: str = Query(..., description="WebSocket连接ID"),
    db: Session = Depends(get_db)
):
    """
    订阅知识库的文档加载进度
    
    将WebSocket连接加入到知识库的文档加载进度广播组
    
    Args:
        knowledge_base_id: 知识库ID
        connection_id: WebSocket连接ID
        db: 数据库会话
        
    Returns:
        订阅结果
    """
    try:
        from app.websocket.connection_manager import connection_manager
        
        # 加入知识库的文档加载进度组
        group_name = f"kb_{knowledge_base_id}_document_load"
        await connection_manager.join_group(connection_id, group_name)
        
        logger.info(f"连接 {connection_id} 已订阅知识库 {knowledge_base_id} 的文档加载进度")

        return {
            "success": True,
            "message": f"已订阅知识库 {knowledge_base_id} 的文档加载进度",
            "group_name": group_name
        }

    except Exception as e:
        logger.error(f"订阅文档加载进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"订阅失败: {str(e)}")


# ==================== 片段级实体识别 API (异步) ====================

@router.post("/documents/{document_id}/extract-chunk-entities")
async def extract_document_chunk_entities(
    document_id: int,
    max_workers: int = Query(4, ge=1, le=10, description="并行工作线程数"),
    db: Session = Depends(get_db)
):
    """
    对文档的所有片段进行并行实体识别（异步）

    - 复用现有LLMEntityExtractor
    - 支持多线程并行处理
    - 适用于大文件（70万字）
    - 异步处理，立即返回任务ID
    """
    try:
        from app.services.knowledge.chunk.chunk_entity_task_service import ChunkEntityTaskService

        service = ChunkEntityTaskService(db)
        task_id = service.create_task(document_id=document_id, max_workers=max_workers)

        return {
            "document_id": document_id,
            "task_id": task_id,
            "status": "accepted",
            "message": "实体提取任务已创建，请使用任务ID查询进度"
        }
    except Exception as e:
        logger.error(f"创建实体提取任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/documents/{document_id}/extract-chunk-entities/status/{task_id}")
async def get_extract_task_status(
    document_id: int,
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取实体提取任务状态

    - 查询异步任务的进度和状态
    - 返回任务详细信息
    """
    try:
        from app.services.knowledge.chunk.chunk_entity_task_service import ChunkEntityTaskService

        service = ChunkEntityTaskService(db)
        status = service.get_task_status(task_id)

        if not status:
            raise HTTPException(status_code=404, detail="任务不存在")

        if status["document_id"] != document_id:
            raise HTTPException(status_code=400, detail="任务ID与文档ID不匹配")

        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.get("/documents/{document_id}/extract-chunk-entities/tasks")
async def list_extract_tasks(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    列出文档的所有实体提取任务

    - 返回文档的所有任务列表
    - 按创建时间倒序排列
    """
    try:
        from app.services.knowledge.chunk.chunk_entity_task_service import ChunkEntityTaskService

        service = ChunkEntityTaskService(db)
        tasks = service.list_tasks(document_id=document_id)

        return {
            "document_id": document_id,
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/chunks/{chunk_id}/entities")
async def get_chunk_entities(
    chunk_id: int,
    db: Session = Depends(get_db)
):
    """获取片段级实体列表"""
    try:
        from app.services.knowledge.chunk.chunk_entity_service import ChunkEntityService

        service = ChunkEntityService(db)
        entities = service.get_chunk_entities(chunk_id)

        return {
            "chunk_id": chunk_id,
            "entities": entities,
            "total": len(entities)
        }
    except Exception as e:
        logger.error(f"获取片段实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/documents/{document_id}/chunk-entities")
async def get_document_chunk_entities(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有片段级实体"""
    try:
        from app.services.knowledge.chunk.chunk_entity_service import ChunkEntityService

        service = ChunkEntityService(db)
        result = service.get_document_chunk_entities(document_id)

        return result
    except Exception as e:
        logger.error(f"获取文档片段实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ==================== 文档级实体聚合 API ====================

@router.post("/documents/{document_id}/aggregate-entities")
async def aggregate_document_entities(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    将文档的片段级实体聚合成文档级实体

    - 复用EntityAlignmentService的对齐逻辑
    - 按实体类型分组聚类
    - 自动合并相似实体
    """
    try:
        from app.services.knowledge.document.document_entity_service import DocumentEntityService

        service = DocumentEntityService(db)
        result = service.aggregate_chunk_entities(document_id)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "document_id": document_id,
            "status": "completed",
            "entities_created": result["entities_created"],
            "entities": result.get("entities", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档实体聚合失败: {e}")
        raise HTTPException(status_code=500, detail=f"聚合失败: {str(e)}")


@router.get("/documents/{document_id}/entities")
async def get_document_entities(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的文档级实体列表"""
    try:
        from app.services.knowledge.document.document_entity_service import DocumentEntityService

        service = DocumentEntityService(db)
        entities = service.get_document_entities(document_id)

        return {
            "document_id": document_id,
            "entities": entities,
            "total": len(entities)
        }
    except Exception as e:
        logger.error(f"获取文档实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ==================== 知识库级实体对齐 API ====================

@router.post("/knowledge-bases/{knowledge_base_id}/align-entities")
async def align_kb_entities(
    knowledge_base_id: int,
    use_bert: bool = Query(False, description="是否使用BERT语义对齐"),
    db: Session = Depends(get_db)
):
    """
    对知识库的所有文档实体进行对齐，生成KB级实体

    - 复用EntityAlignmentService
    - 将文档级实体对齐到知识库级
    - 自动发现别名和聚类
    """
    try:
        from app.services.knowledge.alignment.entity_alignment_service import EntityAlignmentService

        service = EntityAlignmentService(db, use_bert=use_bert)
        result = service.align_entities_for_kb(knowledge_base_id)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "对齐失败"))

        return {
            "knowledge_base_id": knowledge_base_id,
            "status": "completed",
            "kb_entities_created": result.get("kb_entities_created", 0),
            "entities_aligned": result.get("entities_aligned", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"知识库实体对齐失败: {e}")
        raise HTTPException(status_code=500, detail=f"对齐失败: {str(e)}")


# ==================== 文档重新切片 API ====================

class RechunkRequest(BaseModel):
    """重新切片请求参数"""
    max_chunk_size: int = 1500
    min_chunk_size: int = 300
    overlap: int = 100


@router.post("/documents/{document_id}/rechunk")
async def rechunk_document(
    document_id: int,
    request: RechunkRequest,
    db: Session = Depends(get_db)
):
    """
    重新切片文档

    - 删除旧切片和实体
    - 使用新参数重新切片
    - 返回新切片统计信息
    """
    try:
        from app.services.knowledge.chunk.chunk_service import ChunkService

        service = ChunkService(db)
        result = service.rechunk_document(
            document_id=document_id,
            max_chunk_size=request.max_chunk_size,
            min_chunk_size=request.min_chunk_size,
            overlap=request.overlap
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "document_id": document_id,
            "status": "completed",
            "old_chunks": result.get("old_chunks", 0),
            "new_chunks": result.get("new_chunks", 0),
            "old_entities_deleted": result.get("old_entities_deleted", 0),
            "avg_chunk_size": result.get("avg_chunk_size", 0),
            "min_chunk_size": result.get("min_chunk_size", 0),
            "max_chunk_size": result.get("max_chunk_size", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新切片失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新切片失败: {str(e)}")


@router.get("/documents/{document_id}/chunk-stats")
async def get_document_chunk_stats(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档切片统计信息

    - 返回切片数量和大小分布
    - 用于判断是否需要重新切片
    """
    try:
        from sqlalchemy import text

        # 获取文档信息
        document = knowledge_service.get_document_by_id_or_uuid(str(document_id), db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 获取切片统计
        result = db.execute(text("""
            SELECT
                COUNT(*) as count,
                AVG(LENGTH(chunk_text)) as avg_length,
                MAX(LENGTH(chunk_text)) as max_length,
                MIN(LENGTH(chunk_text)) as min_length,
                SUM(LENGTH(chunk_text)) as total_length
            FROM document_chunks
            WHERE document_id = :doc_id
        """), {"doc_id": document_id})

        stats = result.fetchone()

        # 获取实体数量
        entity_result = db.execute(text("""
            SELECT COUNT(*) as count
            FROM chunk_entities
            WHERE document_id = :doc_id
        """), {"doc_id": document_id})
        entity_count = entity_result.fetchone().count

        return {
            "document_id": document_id,
            "document_title": document.title,
            "content_length": len(document.content) if document.content else 0,
            "chunk_count": stats.count if stats else 0,
            "avg_chunk_length": round(stats.avg_length, 0) if stats and stats.avg_length else 0,
            "max_chunk_length": stats.max_length if stats else 0,
            "min_chunk_length": stats.min_length if stats else 0,
            "total_chunk_length": stats.total_length if stats else 0,
            "entity_count": entity_count,
            "needs_rechunking": stats.max_length > 5000 if stats and stats.max_length else False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取切片统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")