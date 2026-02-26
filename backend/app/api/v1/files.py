"""
统一文件管理API路由

提供统一的文件上传、下载、管理接口
替代原有的分散文件上传接口
"""

from fastapi import (
    APIRouter, UploadFile, File, HTTPException, 
    Depends, Query, BackgroundTasks, Request
)
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.file_record import FileRecord, FileCategory, FileStatus
from app.services.file_storage_service import file_storage_service
from app.services.storage_path_manager import FilePrefix


router = APIRouter(prefix="/files", tags=["文件管理"])


# ============ 请求/响应模型 ============

class FileUploadRequest(BaseModel):
    """文件上传请求模型"""
    category: str = Field(..., description="文件分类: conversation_attachment, knowledge_document, temp_file等")
    conversation_id: Optional[int] = Field(None, description="关联对话ID")
    knowledge_base_id: Optional[int] = Field(None, description="关联知识库ID")
    related_id: Optional[int] = Field(None, description="通用关联ID")


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool
    message: str
    file_id: Optional[str] = None
    filename: str
    file_size: int
    file_size_human: str
    mime_type: str
    category: str
    relative_path: str
    created_at: str


class FileInfoResponse(BaseModel):
    """文件信息响应模型"""
    id: str
    original_name: str
    file_size: int
    file_size_human: str
    mime_type: str
    extension: str
    category: str
    status: str
    relative_path: str
    user_id: int
    conversation_id: Optional[int]
    knowledge_base_id: Optional[int]
    created_at: str
    updated_at: Optional[str]


class FileListResponse(BaseModel):
    """文件列表响应模型"""
    total: int
    files: List[FileInfoResponse]


class StorageUsageResponse(BaseModel):
    """存储使用情况响应模型"""
    user_id: int
    total_size: int
    total_size_human: str
    total_files: int
    breakdown: Dict[str, Any]


class DeleteResponse(BaseModel):
    """删除响应模型"""
    success: bool
    message: str
    file_id: str


# ============ 辅助函数 ============

def get_category_enum(category: str) -> FileCategory:
    """获取分类枚举"""
    category_map = {
        'conversation_attachment': FileCategory.CONVERSATION_ATTACHMENT,
        'voice_message': FileCategory.VOICE_MESSAGE,
        'knowledge_document': FileCategory.KNOWLEDGE_DOCUMENT,
        'knowledge_extract': FileCategory.KNOWLEDGE_EXTRACT,
        'translation_input': FileCategory.TRANSLATION_INPUT,
        'translation_output': FileCategory.TRANSLATION_OUTPUT,
        'user_avatar': FileCategory.USER_AVATAR,
        'user_export': FileCategory.USER_EXPORT,
        'temp_file': FileCategory.TEMP_FILE,
        'model_logo': FileCategory.MODEL_LOGO,
        'supplier_logo': FileCategory.SUPPLIER_LOGO,
        'image_analysis': FileCategory.IMAGE_ANALYSIS,
    }
    
    if category not in category_map:
        raise HTTPException(status_code=400, detail=f"无效的文件分类: {category}")
    
    return category_map[category]


def validate_file_extension(filename: str, category: FileCategory) -> bool:
    """验证文件扩展名"""
    ext = os.path.splitext(filename)[1].lower()
    
    # 不同分类的允许扩展名
    allowed_extensions = {
        FileCategory.CONVERSATION_ATTACHMENT: [
            '.txt', '.md', '.json', '.xml', '.csv',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.zip', '.rar', '.7z',
            '.mp3', '.wav', '.ogg',
            '.mp4', '.avi', '.mov', '.wmv'
        ],
        FileCategory.KNOWLEDGE_DOCUMENT: [
            '.txt', '.md', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv'
        ],
        FileCategory.USER_AVATAR: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        FileCategory.VOICE_MESSAGE: ['.mp3', '.wav', '.ogg', '.m4a'],
        FileCategory.TEMP_FILE: ['*'],  # 允许所有
    }
    
    allowed = allowed_extensions.get(category, ['*'])
    return '*' in allowed or ext in allowed


# ============ API路由 ============

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Query(..., description="文件分类"),
    conversation_id: Optional[int] = Query(None, description="关联对话ID"),
    knowledge_base_id: Optional[int] = Query(None, description="关联知识库ID"),
    related_id: Optional[int] = Query(None, description="通用关联ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    统一文件上传接口
    
    支持分类：
    - conversation_attachment: 聊天附件
    - voice_message: 语音消息
    - knowledge_document: 知识库文档
    - translation_input/output: 翻译文件
    - user_avatar: 用户头像
    - user_export: 用户导出
    - temp_file: 临时文件
    """
    try:
        # 验证文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 获取分类枚举
        file_category = get_category_enum(category)
        
        # 验证文件类型
        if not validate_file_extension(file.filename, file_category):
            raise HTTPException(
                status_code=400, 
                detail=f"该分类不允许此文件类型"
            )
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 验证文件大小
        max_sizes = {
            FileCategory.CONVERSATION_ATTACHMENT: 50 * 1024 * 1024,  # 50MB
            FileCategory.KNOWLEDGE_DOCUMENT: 100 * 1024 * 1024,      # 100MB
            FileCategory.USER_AVATAR: 5 * 1024 * 1024,               # 5MB
            FileCategory.VOICE_MESSAGE: 20 * 1024 * 1024,            # 20MB
            FileCategory.TEMP_FILE: 100 * 1024 * 1024,               # 100MB
        }
        max_size = max_sizes.get(file_category, 50 * 1024 * 1024)
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制，最大允许 {max_size // (1024 * 1024)}MB"
            )
        
        # 确定关联ID
        related_id_value = related_id
        if file_category == FileCategory.CONVERSATION_ATTACHMENT and conversation_id:
            related_id_value = conversation_id
        elif file_category == FileCategory.KNOWLEDGE_DOCUMENT and knowledge_base_id:
            related_id_value = knowledge_base_id
        
        # 保存文件
        file_info = await file_storage_service.save_file(
            file_data=content,
            filename=file.filename,
            user_id=current_user.id,
            category=file_category,
            related_id=related_id_value,
            metadata={
                'conversation_id': conversation_id,
                'knowledge_base_id': knowledge_base_id,
                'original_filename': file.filename,
                'upload_time': datetime.now().isoformat()
            }
        )
        
        # 创建数据库记录
        new_record = FileRecord(
            id=file_info['file_id'],
            user_id=current_user.id,
            original_name=file_info['original_name'],
            stored_name=file_info['stored_name'],
            relative_path=file_info['relative_path'],
            absolute_path=file_info['file_path'],
            file_size=file_info['file_size'],
            mime_type=file_info.get('mime_type', 'application/octet-stream'),
            extension=file_info['extension'],
            checksum=file_info['checksum'],
            category=file_category,
            conversation_id=conversation_id,
            knowledge_base_id=knowledge_base_id,
            related_id=related_id_value,
            status=FileStatus.COMPLETED,
            extra_metadata=file_info['metadata']
        )
        
        db.add(new_record)
        db.commit()
        
        return FileUploadResponse(
            success=True,
            message="文件上传成功",
            file_id=file_info['file_id'],
            filename=file_info['original_name'],
            file_size=file_info['file_size'],
            file_size_human=file_info['size_human'],
            mime_type=file_info.get('mime_type', 'application/octet-stream'),
            category=category,
            relative_path=file_info['relative_path'],
            created_at=file_info['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/{file_id}")
async def download_file(
    file_id: str,
    download: bool = Query(False, description="是否作为附件下载"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载文件
    
    Args:
        file_id: 文件ID
        download: 是否作为附件下载（默认在线预览）
    """
    try:
        # 查询文件记录
        file_record = db.query(FileRecord).filter(
            FileRecord.id == file_id,
            FileRecord.user_id == current_user.id
        ).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查文件是否存在
        file_path = file_record.absolute_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件已丢失")
        
        # 返回文件
        if download:
            return FileResponse(
                path=file_path,
                filename=file_record.original_name,
                media_type=file_record.mime_type,
                content_disposition_type="attachment"
            )
        else:
            return FileResponse(
                path=file_path,
                media_type=file_record.mime_type,
                content_disposition_type="inline"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.get("/{file_id}/info", response_model=FileInfoResponse)
async def get_file_info(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件信息"""
    try:
        file_record = db.query(FileRecord).filter(
            FileRecord.id == file_id,
            FileRecord.user_id == current_user.id
        ).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileInfoResponse(
            id=file_record.id,
            original_name=file_record.original_name,
            file_size=file_record.file_size,
            file_size_human=file_storage_service._format_size(file_record.file_size),
            mime_type=file_record.mime_type or 'application/octet-stream',
            extension=file_record.extension,
            category=file_record.category.value,
            status=file_record.status.value,
            relative_path=file_record.relative_path,
            user_id=file_record.user_id,
            conversation_id=file_record.conversation_id,
            knowledge_base_id=file_record.knowledge_base_id,
            created_at=file_record.created_at.isoformat() if file_record.created_at else '',
            updated_at=file_record.updated_at.isoformat() if file_record.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.get("/", response_model=FileListResponse)
async def list_files(
    category: Optional[str] = Query(None, description="文件分类筛选"),
    conversation_id: Optional[int] = Query(None, description="对话ID筛选"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件列表"""
    try:
        # 构建查询
        query = db.query(FileRecord).filter(FileRecord.user_id == current_user.id)
        
        # 应用筛选
        if category:
            try:
                cat_enum = get_category_enum(category)
                query = query.filter(FileRecord.category == cat_enum)
            except HTTPException:
                pass
        
        if conversation_id:
            query = query.filter(FileRecord.conversation_id == conversation_id)
        
        if knowledge_base_id:
            query = query.filter(FileRecord.knowledge_base_id == knowledge_base_id)
        
        if status:
            try:
                status_enum = FileStatus(status)
                query = query.filter(FileRecord.status == status_enum)
            except ValueError:
                pass
        
        # 获取总数
        total = query.count()
        
        # 获取分页数据
        files = query.order_by(FileRecord.created_at.desc()).offset(offset).limit(limit).all()
        
        # 构建响应
        file_list = []
        for f in files:
            file_list.append(FileInfoResponse(
                id=f.id,
                original_name=f.original_name,
                file_size=f.file_size,
                file_size_human=file_storage_service._format_size(f.file_size),
                mime_type=f.mime_type or 'application/octet-stream',
                extension=f.extension,
                category=f.category.value,
                status=f.status.value,
                relative_path=f.relative_path,
                user_id=f.user_id,
                conversation_id=f.conversation_id,
                knowledge_base_id=f.knowledge_base_id,
                created_at=f.created_at.isoformat() if f.created_at else '',
                updated_at=f.updated_at.isoformat() if f.updated_at else None
            ))
        
        return FileListResponse(total=total, files=file_list)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.delete("/{file_id}", response_model=DeleteResponse)
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文件"""
    try:
        # 查询文件记录
        file_record = db.query(FileRecord).filter(
            FileRecord.id == file_id,
            FileRecord.user_id == current_user.id
        ).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除物理文件
        success = await file_storage_service.delete_file(file_record.absolute_path)
        
        # 删除数据库记录
        db.delete(file_record)
        db.commit()
        
        return DeleteResponse(
            success=success,
            message="文件删除成功" if success else "文件记录已删除，但物理文件可能不存在",
            file_id=file_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")


@router.get("/storage/usage", response_model=StorageUsageResponse)
async def get_storage_usage(
    current_user: User = Depends(get_current_user)
):
    """获取用户存储使用情况"""
    try:
        usage = file_storage_service.get_user_storage_info(current_user.id)
        
        return StorageUsageResponse(
            user_id=current_user.id,
            total_size=usage['total']['size'],
            total_size_human=usage['total']['size_human'],
            total_files=usage['total']['files'],
            breakdown={
                k: v for k, v in usage.items() 
                if k != 'total'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取存储使用情况失败: {str(e)}")


@router.post("/cleanup/temp")
async def cleanup_temp_files(
    max_age_hours: int = Query(24, ge=1, description="临时文件最大保留时间（小时）"),
    current_user: User = Depends(get_current_user)
):
    """清理用户临时文件"""
    try:
        deleted_count = file_storage_service.cleanup_user_temp_files(
            current_user.id, 
            max_age_hours
        )
        
        return {
            'success': True,
            'message': f'已清理 {deleted_count} 个临时文件',
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理临时文件失败: {str(e)}")


# ============ 兼容旧接口 ============

@router.post("/upload/legacy")
async def upload_file_legacy(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    兼容旧版上传接口
    
    将请求转发到新的统一上传接口
    """
    return await upload_file(
        file=file,
        category="conversation_attachment",
        conversation_id=conversation_id,
        db=db,
        current_user=current_user
    )
