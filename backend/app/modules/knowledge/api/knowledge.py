from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.modules.knowledge.models.knowledge_document import KnowledgeBase as KnowledgeBaseModel
from app.modules.knowledge.schemas.knowledge import (
    KnowledgeDocument, SearchResponse, DocumentListResponse,
    KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate,
    KnowledgeTag, DocumentTagRequest, DocumentTagsResponse, TagListResponse
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

# Knowledge Document API Endpoints
@router.post("/documents", response_model=dict)
@router.post("/documents/upload")
async def upload_document(
    knowledge_base_id: int = Query(..., description="目标知识库ID"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传文档到指定知识库"""
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
        
        result = await knowledge_service.process_uploaded_file(file, knowledge_base_id, db)
        return {"message": "文档上传成功", "document_id": result.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="文档处理失败")

@router.get("/search", response_model=SearchResponse)
async def search_documents(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID进行搜索")
):
    """搜索知识库文档"""
    try:
        results = knowledge_service.search_documents(query, limit, knowledge_base_id)
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="搜索失败")

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    knowledge_base_id: Optional[int] = Query(None, description="指定知识库ID")
    , db: Session = Depends(get_db)
):
    """获取知识库文档列表"""
    try:
        documents = knowledge_service.list_documents(db, skip, limit, knowledge_base_id)
        total = knowledge_service.get_document_count(db, knowledge_base_id)
        
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
            ) for doc in documents
        ]
        
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
            vector_id=document.vector_id
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

@router.get("/stats")
async def get_knowledge_stats(db: Session = Depends(get_db)):
    """获取知识库统计信息"""
    try:
        # 获取总文档数
        total_documents = knowledge_service.get_document_count(db)
        vector_documents = knowledge_service.retrieval_service.get_document_count()
        
        # 获取知识库数量
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