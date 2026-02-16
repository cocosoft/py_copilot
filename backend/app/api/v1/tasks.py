"""
任务处理API模块（优化版）
支持单文本翻译等任务，以及任务管理功能
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.services.llm_tasks import LLMTasks
from app.models.task import Task, TaskSkill

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

# 任务创建请求模型
class TaskCreateRequest(BaseModel):
    """任务创建请求"""
    title: str = Field(..., description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    priority: str = Field("medium", description="任务优先级")
    working_directory: Optional[str] = Field(None, description="工作目录")
    execute_command: bool = Field(False, description="是否执行系统命令")
    command: Optional[str] = Field(None, description="系统命令")

# 任务更新请求模型
class TaskUpdateRequest(BaseModel):
    """任务更新请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

# 任务响应模型
class TaskResponse(BaseModel):
    """任务响应"""
    id: int
    title: str
    description: Optional[str]
    task_type: Optional[str]
    complexity: Optional[str]
    status: str
    priority: str
    execution_time_ms: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

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


@router.post("", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建任务
    
    Args:
        request: 任务创建请求
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        任务响应
    """
    task = Task(
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        priority=request.priority,
        working_directory=request.working_directory,
        execute_command=request.execute_command,
        command=request.command,
        status="analyzing"
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 自动执行任务分析和技能匹配
    try:
        from app.services.task_service import TaskService
        task_service = TaskService(db)
        
        # 分析任务
        await task_service.analyze_task(task)
        
        # 匹配技能
        await task_service.match_skills(task)
        
        # 更新任务状态为待处理
        task.status = "pending"
        db.commit()
        db.refresh(task)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"任务分析和匹配失败: {e}")
        # 即使分析失败，也将任务状态设为pending，允许用户手动执行
        task.status = "pending"
        db.commit()
        db.refresh(task)
    
    return task


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = Query(None, description="任务状态"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务列表
    
    Args:
        status: 任务状态
        skip: 跳过数量
        limit: 返回数量
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        任务列表
    """
    query = db.query(Task).filter(Task.user_id == current_user.id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务详情
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        任务详情
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新任务
    
    Args:
        task_id: 任务ID
        request: 任务更新请求
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        更新后的任务
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除任务
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        删除结果
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "任务删除成功"}


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    执行任务
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        执行结果
    """
    from app.services.task_service import TaskService
    
    task_service = TaskService(db)
    
    try:
        result = await task_service.execute_task(task_id, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务执行失败: {str(e)}"
        )


@router.get("/{task_id}/progress")
async def get_task_progress(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务进度
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        任务进度
    """
    from app.services.task_service import TaskService
    
    task_service = TaskService(db)
    
    progress = task_service.get_task_progress(task_id, current_user.id)
    
    return progress


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    取消任务
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        取消结果
    """
    from app.services.task_service import TaskService
    
    task_service = TaskService(db)
    
    result = task_service.cancel_task(task_id, current_user.id)
    
    return result