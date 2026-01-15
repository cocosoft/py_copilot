"""文档翻译API路由"""
from typing import Any, Dict, List, Optional
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.llm_tasks import llm_tasks

router = APIRouter()


@router.post("/translate/document")
async def translate_document(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    source_language: str = Form("auto"),
    model_id: Optional[str] = Form(None),
    agent_id: Optional[str] = Form(None),
    preserve_formatting: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    文档翻译API
    
    支持的文件格式：TXT, DOCX, PDF
    
    Args:
        file: 上传的文件
        target_language: 目标语言
        source_language: 源语言（默认自动检测）
        model_id: 模型ID（可选）
        agent_id: 智能体ID（可选）
        preserve_formatting: 是否保持格式
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        翻译结果
    """
    # 验证文件格式
    allowed_extensions = {'.txt', '.docx', '.pdf'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式: {file_extension}。支持格式: {', '.join(allowed_extensions)}"
        )
    
    # 验证文件大小（最大10MB）
    max_file_size = 10 * 1024 * 1024  # 10MB
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置文件指针
    
    if file_size > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制: {file_size}字节。最大支持: {max_file_size}字节"
        )
    
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # 保存上传的文件到临时文件
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 根据文件类型提取内容
        if file_extension == '.txt':
            # 读取TXT文件
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        
        elif file_extension == '.docx':
            # 读取DOCX文件
            try:
                from docx import Document
                doc = Document(temp_file_path)
                original_content = '\n'.join([para.text for para in doc.paragraphs])
            except ImportError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="DOCX处理功能不可用，请安装python-docx库"
                )
        
        elif file_extension == '.pdf':
            # 读取PDF文件
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(temp_file_path)
                original_content = '\n'.join([page.extract_text() for page in reader.pages])
            except ImportError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="PDF处理功能不可用，请安装PyPDF2库"
                )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式: {file_extension}"
            )
        
        # 验证内容不为空
        if not original_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容为空或无法提取文本"
            )
        
        # 构建翻译参数
        translation_params = {
            "text": original_content,
            "target_language": target_language,
            "source_language": source_language,
        }
        
        # 添加可选参数
        if model_id:
            translation_params["model_name"] = model_id
        
        if agent_id:
            translation_params["agent_id"] = agent_id
        
        # 添加用户ID和数据库会话到翻译参数
        translation_params["user_id"] = current_user.id
        translation_params["db"] = db
        
        # 调用翻译服务
        translation_result = llm_tasks.translate_text(**translation_params)
        
        if not translation_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"翻译失败: {translation_result.get('error', '未知错误')}"
            )
        
        # 返回结果
        return {
            "success": True,
            "translated_content": translation_result.get("result", ""),
            "original_content": original_content,
            "file_type": file_extension,
            "file_name": file.filename,
            "translation_metadata": {
                "model": translation_result.get("model", "unknown"),
                "agent": agent_id,
                "execution_time": translation_result.get("execution_time_ms", 0)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        try:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        except Exception:
            pass  # 忽略清理错误


@router.get("/translate/supported-formats")
async def get_supported_formats() -> Dict[str, Any]:
    """
    获取支持的文档格式列表
    
    Returns:
        支持的格式信息
    """
    return {
        "success": True,
        "supported_formats": [
            {
                "extension": ".txt",
                "name": "纯文本文件",
                "description": "支持UTF-8编码的文本文件"
            },
            {
                "extension": ".docx",
                "name": "Microsoft Word文档",
                "description": "支持DOCX格式的Word文档"
            },
            {
                "extension": ".pdf",
                "name": "PDF文档",
                "description": "支持文本提取的PDF文档"
            }
        ],
        "max_file_size": "10MB"
    }