from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.modules.knowledge.models.knowledge_document import KnowledgeBase as KnowledgeBaseModel, KnowledgeDocument as KnowledgeDocumentModel
from app.services.knowledge.retrieval_service import AdvancedRetrievalService
from app.services.knowledge.document_processing_queue import document_processing_queue
from app.modules.knowledge.schemas.knowledge import (
    KnowledgeDocument, SearchResponse, DocumentListResponse,
    KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate,
    KnowledgeTag, DocumentTagRequest, DocumentTagsResponse, TagListResponse,
    KnowledgeDocumentChunk, AdvancedSearchRequest, HybridSearchRequest,
    AdvancedSearchResponse
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
            return {
                "message": save_result.get("message", "该文件已存在于知识库中"),
                "document_id": existing_doc.id,
                "status": "duplicate",
                "is_vectorized": existing_doc.is_vectorized == 1,
                "warning": "系统检测到您上传的文件与知识库中现有文件内容完全相同"
            }

        document = save_result.get("document")

        # 如果不自动处理，直接返回上传成功
        if not auto_process:
            return {
                "message": "文档上传成功，请手动启动处理",
                "document_id": document.id,
                "status": "uploaded",
                "is_vectorized": False
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
    limit: int = Query(10, ge=1, le=50),
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID")
    , db: Session = Depends(get_db)
):
    """获取知识库文档列表 - 自动修复状态不一致的文档"""
    try:
        documents = knowledge_service.list_documents(db, skip, limit, knowledge_base_id)
        total = knowledge_service.get_document_count(db, knowledge_base_id)

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
                    title=doc.title,
                    knowledge_base_id=doc.knowledge_base_id,
                    file_path=doc.file_path,
                    file_type=doc.file_type,
                    content=doc.content,
                    document_metadata=doc.document_metadata,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    vector_id=doc.vector_id,
                    is_vectorized=doc.is_vectorized
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

@router.get("/documents/{document_id}", response_model=KnowledgeDocument)
async def get_document_detail(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档详情"""
    try:
        document = knowledge_service.get_document_by_id(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
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
            vector_id=document.vector_id,
            is_vectorized=document.is_vectorized
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取文档详情失败")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """删除文档"""
    try:
        success = knowledge_service.delete_document(db, document_id)
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除失败")


@router.get("/documents/{document_id}/progress")
async def get_document_processing_progress(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档处理进度

    用于前端轮询查询文档处理状态
    """
    try:
        from app.services.knowledge.processing_progress_service import processing_progress_service

        # 首先检查文档是否存在
        document = knowledge_service.get_document_by_id(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 如果文档已向量化，直接返回完成状态
        if document.is_vectorized:
            return {
                "document_id": document_id,
                "status": "completed",
                "progress_percent": 100,
                "step_name": "完成",
                "message": "文档处理已完成"
            }

        # 获取处理进度
        progress = processing_progress_service.get_progress(str(document_id))

        if progress:
            return progress

        # 如果没有进度记录，根据文档状态返回
        doc_status = document.document_metadata.get("processing_status") if document.document_metadata else None

        if doc_status == "processing":
            return {
                "document_id": document_id,
                "status": "processing",
                "progress_percent": 0,
                "step_name": "初始化",
                "message": "文档处理初始化中..."
            }
        elif doc_status == "queued":
            return {
                "document_id": document_id,
                "status": "queued",
                "progress_percent": 0,
                "step_name": "排队中",
                "message": "文档在队列中等待处理"
            }
        else:
            return {
                "document_id": document_id,
                "status": "pending",
                "progress_percent": 0,
                "step_name": "等待处理",
                "message": "文档等待处理，请手动启动"
            }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"获取处理进度错误: {str(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取处理进度失败: {str(e)}")

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
    document_id: int,
    db: Session = Depends(get_db)
):
    """下载文档"""
    try:
        file_path, filename = knowledge_service.download_document(db, document_id)
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

@router.get("/documents/{document_id}/chunks", response_model=List[KnowledgeDocumentChunk])
async def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的向量片段列表"""
    try:
        chunks = knowledge_service.get_document_chunks(document_id, db)
        return chunks
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取文档向量片段失败")

@router.get("/stats")
async def get_knowledge_stats(db: Session = Depends(get_db)):
    """获取知识库统计信息"""
    try:
        # 查询文档总数
        total_documents = db.query(KnowledgeDocumentModel).count()

        # 查询已向量化文档数
        vector_documents = db.query(KnowledgeDocumentModel).filter(KnowledgeDocumentModel.is_vectorized == 1).count()

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
    document_id: int,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    手动启动文档处理（向量化、图谱化）

    上传文档后，调用此接口启动后续处理流程
    """
    try:
        # 检查文档是否存在
        document = knowledge_service.get_document_by_id(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查文档是否已向量化
        if document.is_vectorized == 1:
            return {
                "message": "文档已处理完成",
                "document_id": document_id,
                "status": "completed",
                "is_vectorized": True
            }

        # 检查是否已经在处理中
        current_status = document.document_metadata.get("processing_status") if document.document_metadata else None
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
        added = await document_processing_queue.add_document(
            document_id=document.id,
            knowledge_base_id=document.knowledge_base_id,
            document_name=document.title,
            priority=0
        )

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
                vector_id=doc.vector_id,
                is_vectorized=doc.is_vectorized
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
            vector_id=updated_document.vector_id,
            is_vectorized=updated_document.is_vectorized
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文档失败: {str(e)}")

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
            vector_id=document.vector_id,
            is_vectorized=document.is_vectorized
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
            vector_id=restored_document.vector_id,
            is_vectorized=restored_document.is_vectorized
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
                "is_vectorized": doc.is_vectorized,
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
                new_doc = KnowledgeDocumentModel(
                    title=doc_data.get("title"),
                    knowledge_base_id=new_kb.id,
                    file_path=doc_data.get("file_path"),
                    file_type=doc_data.get("file_type"),
                    content=doc_data.get("content", ""),
                    is_vectorized=0,  # 导入的文档需要重新向量化
                    vector_id=None,
                    document_metadata=doc_data.get("document_metadata", {})
                )

                # 更新元数据中的处理状态
                if new_doc.document_metadata:
                    new_doc.document_metadata["processing_status"] = "pending"
                    new_doc.document_metadata["imported_from"] = kb_data.get("id")

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