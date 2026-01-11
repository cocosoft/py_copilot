"""文件处理微服务"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import uuid
import asyncio
from pathlib import Path

from app.core.microservices import MicroserviceConfig, get_service_registry
from app.core.config import settings


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: int
    filename: str
    file_size: int
    file_type: str
    upload_path: str
    processing_status: str
    metadata: Optional[Dict[str, Any]] = None


class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: int
    filename: str
    file_size: int
    file_type: str
    upload_time: str
    processing_status: str
    metadata: Optional[Dict[str, Any]] = None


class FileService:
    """文件服务管理器"""
    
    def __init__(self):
        self.service_registry = get_service_registry()
        self.upload_dir = Path(settings.UPLOAD_DIR) if hasattr(settings, 'UPLOAD_DIR') else Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
    
    async def upload_file(self, file: UploadFile, conversation_id: int, 
                         user_id: int) -> FileUploadResponse:
        """上传文件"""
        try:
            # 生成唯一文件名
            file_extension = Path(file.filename).suffix if file.filename else ".bin"
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = self.upload_dir / unique_filename
            
            # 保存文件
            file_content = await file.read()
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 获取文件信息
            file_size = len(file_content)
            file_type = self._detect_file_type(file.filename, file_content)
            
            # 处理文件（异步）
            asyncio.create_task(self._process_file_async(
                file_path, unique_filename, file_type, conversation_id, user_id
            ))
            
            # 创建文件记录（这里简化处理，实际应该保存到数据库）
            from app.models.chat_enhancements import UploadedFile
            from app.core.database import get_db
            
            db = next(get_db())
            try:
                uploaded_file = UploadedFile(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    filename=file.filename or "unknown",
                    file_path=str(file_path),
                    file_size=file_size,
                    file_type=file_type,
                    processing_status="uploaded"
                )
                db.add(uploaded_file)
                db.commit()
                db.refresh(uploaded_file)
                
                return FileUploadResponse(
                    file_id=uploaded_file.id,
                    filename=uploaded_file.filename,
                    file_size=uploaded_file.file_size,
                    file_type=uploaded_file.file_type,
                    upload_path=uploaded_file.file_path,
                    processing_status=uploaded_file.processing_status
                )
            finally:
                db.close()
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    async def _process_file_async(self, file_path: Path, filename: str, 
                                file_type: str, conversation_id: int, user_id: int):
        """异步处理文件"""
        try:
            # 更新处理状态
            await self._update_file_processing_status(filename, "processing")
            
            # 根据文件类型进行处理
            if file_type.startswith("image"):
                await self._process_image_file(file_path)
            elif file_type.startswith("text"):
                await self._process_text_file(file_path)
            elif file_type == "application/pdf":
                await self._process_pdf_file(file_path)
            elif file_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                await self._process_word_file(file_path)
            else:
                # 通用文件处理
                await self._process_generic_file(file_path)
            
            # 更新处理状态为完成
            await self._update_file_processing_status(filename, "completed")
            
            # 发布文件处理完成消息
            await self._publish_file_processed_event(
                filename, file_type, conversation_id, user_id
            )
            
        except Exception as e:
            print(f"文件处理错误: {e}")
            await self._update_file_processing_status(filename, "error")
    
    async def _process_image_file(self, file_path: Path):
        """处理图像文件"""
        # 这里可以实现图像分析、OCR等功能
        print(f"处理图像文件: {file_path}")
        
        # 模拟处理时间
        await asyncio.sleep(2)
    
    async def _process_text_file(self, file_path: Path):
        """处理文本文件"""
        # 这里可以实现文本分析、内容提取等功能
        print(f"处理文本文件: {file_path}")
        
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 模拟处理时间
        await asyncio.sleep(1)
    
    async def _process_pdf_file(self, file_path: Path):
        """处理PDF文件"""
        # 这里可以实现PDF文本提取、分析等功能
        print(f"处理PDF文件: {file_path}")
        
        # 模拟处理时间
        await asyncio.sleep(3)
    
    async def _process_word_file(self, file_path: Path):
        """处理Word文档"""
        # 这里可以实现Word文档解析等功能
        print(f"处理Word文档: {file_path}")
        
        # 模拟处理时间
        await asyncio.sleep(2)
    
    async def _process_generic_file(self, file_path: Path):
        """处理通用文件"""
        # 通用文件处理逻辑
        print(f"处理通用文件: {file_path}")
        
        # 模拟处理时间
        await asyncio.sleep(1)
    
    async def _update_file_processing_status(self, filename: str, status: str):
        """更新文件处理状态"""
        # 这里应该更新数据库中的文件状态
        from app.models.chat_enhancements import UploadedFile
        from app.core.database import get_db
        
        db = next(get_db())
        try:
            file_record = db.query(UploadedFile).filter(
                UploadedFile.file_path.like(f"%{filename}%")
            ).first()
            
            if file_record:
                file_record.processing_status = status
                db.commit()
        finally:
            db.close()
    
    async def _publish_file_processed_event(self, filename: str, file_type: str, 
                                          conversation_id: int, user_id: int):
        """发布文件处理完成事件"""
        from app.core.microservices import get_message_queue
        
        message_queue = get_message_queue()
        
        event_data = {
            "event_type": "file_processed",
            "filename": filename,
            "file_type": file_type,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await message_queue.publish_message("file_events", event_data)
    
    def _detect_file_type(self, filename: str, content: bytes) -> str:
        """检测文件类型"""
        # 基于文件名后缀和内容检测文件类型
        if filename:
            filename_lower = filename.lower()
            
            # 图像文件
            if any(ext in filename_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                return "image/jpeg" if '.jpg' in filename_lower or '.jpeg' in filename_lower else "image/png"
            
            # 文本文件
            if any(ext in filename_lower for ext in ['.txt', '.md', '.csv', '.json', '.xml']):
                return "text/plain"
            
            # PDF文件
            if '.pdf' in filename_lower:
                return "application/pdf"
            
            # Word文档
            if '.doc' in filename_lower or '.docx' in filename_lower:
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            # Excel文件
            if '.xls' in filename_lower or '.xlsx' in filename_lower:
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # 基于内容检测（简化版本）
        if content.startswith(b'%PDF'):
            return "application/pdf"
        
        # 默认类型
        return "application/octet-stream"
    
    async def get_file_info(self, file_id: int) -> Optional[FileInfo]:
        """获取文件信息"""
        from app.models.chat_enhancements import UploadedFile
        from app.core.database import get_db
        
        db = next(get_db())
        try:
            file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            
            if file_record:
                return FileInfo(
                    file_id=file_record.id,
                    filename=file_record.filename,
                    file_size=file_record.file_size,
                    file_type=file_record.file_type,
                    upload_time=file_record.created_at.isoformat() if file_record.created_at else "",
                    processing_status=file_record.processing_status
                )
        finally:
            db.close()
        
        return None
    
    async def download_file(self, file_id: int) -> Optional[FileResponse]:
        """下载文件"""
        from app.models.chat_enhancements import UploadedFile
        from app.core.database import get_db
        
        db = next(get_db())
        try:
            file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            
            if file_record and os.path.exists(file_record.file_path):
                return FileResponse(
                    path=file_record.file_path,
                    filename=file_record.filename,
                    media_type=file_record.file_type
                )
        finally:
            db.close()
        
        return None


# 创建文件服务实例
file_service = FileService()


# 创建文件微服务应用
file_app = FastAPI(
    title="Py Copilot File Service",
    version="1.0.0",
    description="文件处理微服务"
)


@file_app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "file"}


@file_app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: int = 0,
    user_id: int = 0
):
    """文件上传接口"""
    response = await file_service.upload_file(file, conversation_id, user_id)
    return response


@file_app.get("/files/{file_id}")
async def get_file(file_id: int):
    """获取文件信息接口"""
    file_info = await file_service.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件未找到")
    return file_info


@file_app.get("/files/{file_id}/download")
async def download_file(file_id: int):
    """下载文件接口"""
    file_response = await file_service.download_file(file_id)
    if not file_response:
        raise HTTPException(status_code=404, detail="文件未找到")
    return file_response


@file_app.get("/statistics")
async def get_statistics():
    """获取文件统计信息"""
    # 这里可以返回文件服务的统计信息
    return {
        "total_uploads": 0,
        "total_file_size": 0,
        "file_types": {}
    }


@file_app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    # 注册服务到服务注册中心
    config = MicroserviceConfig(
        name="file-service",
        host="localhost",
        port=8003,
        description="文件处理微服务"
    )
    
    await file_service.service_registry.register_service(config)
    print("文件微服务启动完成")


@file_app.on_event("shutdown")
async def shutdown_event():
    """服务关闭事件"""
    print("文件微服务已关闭")