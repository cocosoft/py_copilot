"""
批量翻译API模块
支持同时翻译多个文本或文档
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
import uuid

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.services import llm_tasks

router = APIRouter()

# 批量翻译请求模型
class BatchTranslationRequest(BaseModel):
    """批量翻译请求"""
    texts: List[str]
    target_language: str
    source_language: Optional[str] = "auto"
    model_id: Optional[str] = None
    agent_id: Optional[str] = None
    preserve_formatting: bool = True
    
# 批量翻译响应模型
class BatchTranslationResponse(BaseModel):
    """批量翻译响应"""
    batch_id: str
    status: str  # pending, processing, completed, failed
    total_items: int
    processed_items: int
    results: List[Dict[str, Any]]
    
# 单个翻译结果模型
class TranslationResult(BaseModel):
    """单个翻译结果"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    status: str  # success, failed
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    model: Optional[str] = None
    
# 存储批量翻译任务状态
batch_tasks = {}

@router.post("/translate/batch", response_model=BatchTranslationResponse)
async def batch_translate_texts(
    request: BatchTranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    批量翻译文本
    
    Args:
        request: 批量翻译请求
        background_tasks: 后台任务管理器
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        批量翻译响应，包含任务ID和初始状态
    """
    if not request.texts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="翻译文本列表不能为空"
        )
    
    if len(request.texts) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="单次批量翻译最多支持100个文本"
        )
    
    # 生成批量任务ID
    batch_id = str(uuid.uuid4())
    
    # 初始化任务状态
    batch_tasks[batch_id] = {
        "status": "pending",
        "total_items": len(request.texts),
        "processed_items": 0,
        "results": [],
        "user_id": current_user.id
    }
    
    # 启动后台处理任务
    background_tasks.add_task(
        process_batch_translation,
        batch_id,
        request.texts,
        request.target_language,
        request.source_language,
        request.model_id,
        request.agent_id,
        request.preserve_formatting,
        db
    )
    
    return BatchTranslationResponse(
        batch_id=batch_id,
        status="pending",
        total_items=len(request.texts),
        processed_items=0,
        results=[]
    )

@router.get("/translate/batch/{batch_id}", response_model=BatchTranslationResponse)
async def get_batch_translation_status(
    batch_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取批量翻译任务状态
    
    Args:
        batch_id: 批量任务ID
        current_user: 当前用户
    
    Returns:
        批量翻译任务状态
    """
    if batch_id not in batch_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批量翻译任务不存在"
        )
    
    task = batch_tasks[batch_id]
    
    # 验证用户权限
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此批量翻译任务"
        )
    
    return BatchTranslationResponse(
        batch_id=batch_id,
        status=task["status"],
        total_items=task["total_items"],
        processed_items=task["processed_items"],
        results=task["results"]
    )

async def process_batch_translation(
    batch_id: str,
    texts: List[str],
    target_language: str,
    source_language: str,
    model_id: Optional[str],
    agent_id: Optional[str],
    preserve_formatting: bool,
    db: Session
):
    """
    处理批量翻译任务
    
    Args:
        batch_id: 批量任务ID
        texts: 待翻译文本列表
        target_language: 目标语言
        source_language: 源语言
        model_id: 模型ID
        agent_id: 智能体ID
        preserve_formatting: 是否保持格式
        db: 数据库会话
    """
    # 更新任务状态为处理中
    batch_tasks[batch_id]["status"] = "processing"
    
    results = []
    
    for i, text in enumerate(texts):
        try:
            # 跳过空文本
            if not text or not text.strip():
                results.append({
                    "original_text": text,
                    "translated_text": "",
                    "source_language": source_language,
                    "target_language": target_language,
                    "status": "failed",
                    "error_message": "文本内容为空"
                })
                continue
            
            # 构建翻译参数
            translation_params = {
                "text": text.strip(),
                "target_language": target_language,
                "source_language": source_language if source_language != "auto" else None,
            }
            
            # 添加可选参数
            if model_id:
                translation_params["model_name"] = model_id
            
            if agent_id:
                translation_params["agent_id"] = agent_id
            
            # 调用翻译服务
            start_time = asyncio.get_event_loop().time()
            translation_result = llm_tasks.translate_text(**translation_params)
            end_time = asyncio.get_event_loop().time()
            
            execution_time_ms = int((end_time - start_time) * 1000)
            
            # 处理翻译结果
            if translation_result and "result" in translation_result:
                results.append({
                    "original_text": text,
                    "translated_text": translation_result["result"],
                    "source_language": source_language,
                    "target_language": target_language,
                    "status": "success",
                    "execution_time_ms": execution_time_ms,
                    "model": translation_result.get("model", "unknown")
                })
            else:
                results.append({
                    "original_text": text,
                    "translated_text": "",
                    "source_language": source_language,
                    "target_language": target_language,
                    "status": "failed",
                    "error_message": "翻译服务返回空结果"
                })
            
        except Exception as e:
            # 记录翻译失败
            results.append({
                "original_text": text,
                "translated_text": "",
                "source_language": source_language,
                "target_language": target_language,
                "status": "failed",
                "error_message": str(e)
            })
        
        # 更新处理进度
        batch_tasks[batch_id]["processed_items"] = i + 1
        batch_tasks[batch_id]["results"] = results
        
        # 添加小延迟，避免过快请求
        await asyncio.sleep(0.1)
    
    # 更新任务状态为完成
    batch_tasks[batch_id]["status"] = "completed"
    
    # 清理过期的任务（24小时后）
    # 在实际项目中，应该使用数据库存储任务状态
    # 这里使用内存存储，需要定期清理

@router.post("/translate/batch/cancel/{batch_id}")
async def cancel_batch_translation(
    batch_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    取消批量翻译任务
    
    Args:
        batch_id: 批量任务ID
        current_user: 当前用户
    
    Returns:
        取消结果
    """
    if batch_id not in batch_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批量翻译任务不存在"
        )
    
    task = batch_tasks[batch_id]
    
    # 验证用户权限
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权取消此批量翻译任务"
        )
    
    # 只能取消处理中的任务
    if task["status"] not in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能取消待处理或处理中的任务"
        )
    
    # 标记任务为已取消
    task["status"] = "cancelled"
    
    return {"message": "批量翻译任务已取消", "batch_id": batch_id}