"""文件上传API路由"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import uuid
import asyncio
from pathlib import Path
from datetime import datetime

from app.core.database import get_db
from app.models.chat_enhancements import UploadedFile
from sqlalchemy.orm import Session

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    '.txt', '.md', '.json', '.xml', '.csv',
    '.pdf', '.doc', '.docx',
    '.xls', '.xlsx',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.zip', '.rar', '.7z',
    '.mp3', '.wav', '.ogg',
    '.mp4', '.avi', '.mov', '.wmv'
}


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool
    message: str
    file_id: Optional[int] = None
    filename: str
    file_size: int
    file_type: str
    upload_path: str


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    file_extension = Path(original_filename).suffix
    unique_name = f"{uuid.uuid4().hex}{file_extension}"
    return unique_name


def detect_file_type(filename: str) -> str:
    """检测文件类型"""
    file_extension = Path(filename).suffix.lower()
    
    if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        return 'image'
    elif file_extension in ['.txt', '.md', '.json', '.xml', '.csv']:
        return 'text'
    elif file_extension == '.pdf':
        return 'pdf'
    elif file_extension in ['.doc', '.docx']:
        return 'word'
    elif file_extension in ['.xls', '.xlsx']:
        return 'excel'
    elif file_extension in ['.zip', '.rar', '.7z']:
        return 'archive'
    elif file_extension in ['.mp3', '.wav', '.ogg']:
        return 'audio'
    elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
        return 'video'
    else:
        return 'unknown'


def get_mime_type(filename: str) -> str:
    """获取MIME类型"""
    file_extension = Path(filename).suffix.lower()
    
    mime_types = {
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.csv': 'text/csv',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv'
    }
    
    return mime_types.get(file_extension, 'application/octet-stream')


async def process_file_async(file_path: Path, filename: str, 
                         file_type: str, conversation_id: int, user_id: int):
    """异步处理文件"""
    try:
        # 更新处理状态
        await update_file_processing_status(filename, "processing")
        
        # 根据文件类型进行处理
        if file_type.startswith("image"):
            await process_image_file(file_path)
        elif file_type.startswith("text"):
            await process_text_file(file_path)
        elif file_type == "pdf":
            await process_pdf_file(file_path)
        elif file_type in ["word", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            await process_word_file(file_path)
        else:
            # 通用文件处理
            await process_generic_file(file_path)
        
        # 更新处理状态为完成
        await update_file_processing_status(filename, "completed")
        
    except Exception as e:
        print(f"文件处理错误: {e}")
        await update_file_processing_status(filename, "error")


async def process_image_file(file_path: Path):
    """处理图像文件"""
    # 这里可以实现图像分析、OCR等功能
    print(f"处理图像文件: {file_path}")
    
    # 模拟处理时间
    await asyncio.sleep(2)


async def process_text_file(file_path: Path):
    """处理文本文件"""
    # 这里可以实现文本分析、内容提取等功能
    print(f"处理文本文件: {file_path}")
    
    # 读取文件内容
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # 如果不是UTF-8编码，尝试其他编码
        with open(file_path, "r", encoding="gbk") as f:
            content = f.read()
    
    # 模拟处理时间
    await asyncio.sleep(1)


async def process_pdf_file(file_path: Path):
    """处理PDF文件"""
    # 这里可以实现PDF文本提取、分析等功能
    print(f"处理PDF文件: {file_path}")
    
    # 模拟处理时间
    await asyncio.sleep(3)


async def process_word_file(file_path: Path):
    """处理Word文档"""
    # 这里可以实现Word文档解析等功能
    print(f"处理Word文档: {file_path}")
    
    # 模拟处理时间
    await asyncio.sleep(2)


async def process_generic_file(file_path: Path):
    """处理通用文件"""
    # 通用文件处理逻辑
    print(f"处理通用文件: {file_path}")
    
    # 模拟处理时间
    await asyncio.sleep(1)


async def update_file_processing_status(filename: str, status: str):
    """更新文件处理状态"""
    # 这里应该更新数据库中的文件状态
    db: Session = next(get_db())
    try:
        file_record = db.query(UploadedFile).filter(
            UploadedFile.file_path.like(f"%{filename}%")
        ).first()
        
        if file_record:
            file_record.processing_status = status
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = None,
    user_id: Optional[int] = None
):
    """上传文件接口"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_extension}"
            )
        
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制，最大允许 {MAX_FILE_SIZE // (1024 * 1024)}MB"
            )
        
        unique_filename = generate_unique_filename(file.filename)
        file_path = UPLOAD_DIR / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        file_type = detect_file_type(file.filename)
        mime_type = get_mime_type(file.filename)
        
        db: Session = next(get_db())
        try:
            uploaded_file = UploadedFile(
                user_id=user_id or 1,
                conversation_id=conversation_id,
                file_name=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_type=file_type,
                mime_type=mime_type,
                upload_status='completed',
                processing_status='uploaded',
                file_metadata={
                    'original_filename': file.filename,
                    'unique_filename': unique_filename,
                    'upload_time': datetime.now().isoformat()
                }
            )
            db.add(uploaded_file)
            db.commit()
            db.refresh(uploaded_file)
            
            # 异步处理文件
            asyncio.create_task(process_file_async(
                file_path, unique_filename, file_type, 
                conversation_id or 0, user_id or 1
            ))
            
            return FileUploadResponse(
                success=True,
                message="文件上传成功",
                file_id=uploaded_file.id,
                filename=file.filename,
                file_size=file_size,
                file_type=file_type,
                upload_path=str(file_path)
            )
        except Exception as e:
            db.rollback()
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(e)}")
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/files/{file_id}")
async def get_file_info(file_id: int):
    """获取文件信息接口"""
    db: Session = next(get_db())
    try:
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        
        if not uploaded_file:
            raise HTTPException(status_code=404, detail="文件未找到")
        
        return {
            "success": True,
            "file_id": uploaded_file.id,
            "filename": uploaded_file.file_name,
            "file_size": uploaded_file.file_size,
            "file_type": uploaded_file.file_type,
            "mime_type": uploaded_file.mime_type,
            "upload_status": uploaded_file.upload_status,
            "processing_status": uploaded_file.processing_status,
            "created_at": uploaded_file.created_at.isoformat() if uploaded_file.created_at else None,
            "metadata": uploaded_file.file_metadata
        }
    finally:
        db.close()


@router.get("/files/{file_id}/download")
async def download_file(file_id: int):
    """下载文件接口"""
    db: Session = next(get_db())
    try:
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        
        if not uploaded_file:
            raise HTTPException(status_code=404, detail="文件未找到")
        
        file_path = Path(uploaded_file.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=uploaded_file.file_name,
            media_type=uploaded_file.mime_type or 'application/octet-stream'
        )
    finally:
        db.close()


@router.delete("/files/{file_id}")
async def delete_file(file_id: int):
    """删除文件接口"""
    db: Session = next(get_db())
    try:
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        
        if not uploaded_file:
            raise HTTPException(status_code=404, detail="文件未找到")
        
        file_path = Path(uploaded_file.file_path)
        if file_path.exists():
            file_path.unlink()
        
        db.delete(uploaded_file)
        db.commit()
        
        return {
            "success": True,
            "message": "文件删除成功"
        }
    finally:
        db.close()


@router.get("/files")
async def list_files(conversation_id: Optional[int] = None, limit: int = 100):
    """列出文件接口"""
    db: Session = next(get_db())
    try:
        query = db.query(UploadedFile)
        
        if conversation_id is not None:
            query = query.filter(UploadedFile.conversation_id == conversation_id)
        
        files = query.order_by(UploadedFile.created_at.desc()).limit(limit).all()
        
        return {
            "success": True,
            "total": len(files),
            "files": [
                {
                    "file_id": f.id,
                    "filename": f.file_name,
                    "file_size": f.file_size,
                    "file_type": f.file_type,
                    "upload_status": f.upload_status,
                    "processing_status": f.processing_status,
                    "created_at": f.created_at.isoformat() if f.created_at else None
                }
                for f in files
            ]
        }
    finally:
        db.close()


@router.get("/statistics")
async def get_statistics():
    """获取文件统计信息"""
    db: Session = next(get_db())
    try:
        total_uploads = db.query(UploadedFile).count()
        files = db.query(UploadedFile).all()
        
        total_file_size = sum(f.file_size for f in files)
        
        file_types = {}
        for f in files:
            file_type = f.file_type or 'unknown'
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            "success": True,
            "total_uploads": total_uploads,
            "total_file_size": total_file_size,
            "file_types": file_types
        }
    finally:
        db.close()
