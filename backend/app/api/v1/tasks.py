"""
任务处理API模块
支持单文本翻译等任务
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.services.llm_tasks import LLMTasks

router = APIRouter()

# 任务处理请求模型
class TaskProcessRequest(BaseModel):
    """任务处理请求"""
    task_type: str
    text: str
    options: Optional[Dict[str, Any]] = {}

# 任务处理响应模型
class TaskProcessResponse(BaseModel):
    """任务处理响应"""
    task_type: str
    status: str  # success, failed
    result: Optional[str] = None
    error_message: Optional[str] = None
    model: Optional[str] = None
    execution_time_ms: Optional[int] = None

@router.post("/process", response_model=TaskProcessResponse)
async def process_task(
    request: TaskProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    处理单个任务（如单文本翻译）
    
    Args:
        request: 任务处理请求
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        任务处理响应
    """
    # 验证任务类型
    if request.task_type != "translate":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的任务类型: {request.task_type}"
        )
    
    # 验证文本内容
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="需要处理的文本不能为空"
        )
    
    # 初始化LLM任务服务
    llm_tasks = LLMTasks()
    
    try:
        # 处理翻译任务
        if request.task_type == "translate":
            # 提取翻译参数
            translation_options = request.options or {}
            
            # 调用翻译服务
            translation_result = llm_tasks.translate_text(
                text=request.text,
                **translation_options
            )
            
            # 处理翻译结果
            if translation_result.get("success", False):
                return TaskProcessResponse(
                    task_type="translate",
                    status="success",
                    result=translation_result["result"],
                    model=translation_result.get("model"),
                    execution_time_ms=int(translation_result.get("execution_time_ms", 0))
                )
            else:
                return TaskProcessResponse(
                    task_type="translate",
                    status="failed",
                    error_message=translation_result.get("error", "翻译失败")
                )
    
    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"任务处理失败: {str(e)}")
        
        return TaskProcessResponse(
            task_type=request.task_type,
            status="failed",
            error_message=f"任务处理失败: {str(e)}"
        )