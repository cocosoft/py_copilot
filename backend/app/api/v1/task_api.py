#!/usr/bin/env python3
"""
任务管理API

提供异步任务的提交、查询、管理功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging

from app.tasks.knowledge_graph_tasks import (
    build_knowledge_graph_task,
    build_document_layer_task,
    build_knowledge_base_layer_task,
    build_global_layer_task,
    incremental_update_task,
    get_task_status,
)
from app.tasks.entity_extraction_tasks import (
    extract_entities_task,
    batch_extract_entities_task,
)
from app.tasks.entity_alignment_tasks import (
    align_entities_task,
    cross_kb_link_task,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["任务管理"])


# ============== 数据模型 ==============

class TaskType(str, Enum):
    """任务类型"""
    BUILD_KNOWLEDGE_GRAPH = "build_knowledge_graph"
    BUILD_DOCUMENT_LAYER = "build_document_layer"
    BUILD_KB_LAYER = "build_kb_layer"
    BUILD_GLOBAL_LAYER = "build_global_layer"
    INCREMENTAL_UPDATE = "incremental_update"
    EXTRACT_ENTITIES = "extract_entities"
    BATCH_EXTRACT = "batch_extract"
    ALIGN_ENTITIES = "align_entities"
    CROSS_KB_LINK = "cross_kb_link"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    STARTED = "started"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class BuildKnowledgeGraphRequest(BaseModel):
    """构建知识图谱请求"""
    knowledge_base_id: str = Field(..., description="知识库ID")
    document_ids: List[str] = Field(..., description="文档ID列表")
    build_options: Optional[Dict[str, Any]] = Field(default=None, description="构建选项")


class ExtractEntitiesRequest(BaseModel):
    """实体提取请求"""
    document_id: str = Field(..., description="文档ID")
    knowledge_base_id: str = Field(..., description="知识库ID")
    extraction_options: Optional[Dict[str, Any]] = Field(default=None, description="提取选项")


class BatchExtractRequest(BaseModel):
    """批量提取请求"""
    document_ids: List[str] = Field(..., description="文档ID列表")
    knowledge_base_id: str = Field(..., description="知识库ID")
    batch_options: Optional[Dict[str, Any]] = Field(default=None, description="批量选项")


class AlignEntitiesRequest(BaseModel):
    """实体对齐请求"""
    knowledge_base_id: str = Field(..., description="知识库ID")
    entity_ids: List[str] = Field(..., description="实体ID列表")
    alignment_options: Optional[Dict[str, Any]] = Field(default=None, description="对齐选项")


class CrossKBLinkRequest(BaseModel):
    """跨知识库链接请求"""
    source_kb_id: str = Field(..., description="源知识库ID")
    target_kb_id: str = Field(..., description="目标知识库ID")
    link_options: Optional[Dict[str, Any]] = Field(default=None, description="链接选项")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str = Field(..., description="任务ID")
    task_type: TaskType = Field(..., description="任务类型")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field(default="", description="状态消息")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    message: str = Field(default="", description="状态消息")
    result: Optional[Dict[str, Any]] = Field(default=None, description="任务结果")
    updated_at: str = Field(..., description="更新时间")


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskStatusResponse] = Field(..., description="任务列表")
    total: int = Field(..., description="总数")


# ============== API端点 ==============

@router.post("/build-knowledge-graph", response_model=TaskResponse)
async def submit_build_knowledge_graph_task(request: BuildKnowledgeGraphRequest):
    """
    提交知识图谱构建任务
    
    启动完整的分层构建流程
    """
    try:
        # 提交异步任务
        task = build_knowledge_graph_task.delay(
            knowledge_base_id=request.knowledge_base_id,
            document_ids=request.document_ids,
            build_options=request.build_options
        )
        
        return TaskResponse(
            task_id=task.id,
            task_type=TaskType.BUILD_KNOWLEDGE_GRAPH,
            status=TaskStatus.PENDING,
            message="知识图谱构建任务已提交"
        )
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.post("/build-document-layer", response_model=TaskResponse)
async def submit_build_document_layer_task(request: BuildKnowledgeGraphRequest):
    """提交文档层构建任务"""
    try:
        task = build_document_layer_task.delay(
            knowledge_base_id=request.knowledge_base_id,
            document_ids=request.document_ids,
            options=request.build_options
        )
        
        return TaskResponse(
            task_id=task.id,
            task_type=TaskType.BUILD_DOCUMENT_LAYER,
            status=TaskStatus.PENDING,
            message="文档层构建任务已提交"
        )
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.post("/extract-entities", response_model=TaskResponse)
async def submit_extract_entities_task(request: ExtractEntitiesRequest):
    """提交实体提取任务"""
    try:
        task = extract_entities_task.delay(
            document_id=request.document_id,
            knowledge_base_id=request.knowledge_base_id,
            extraction_options=request.extraction_options
        )
        
        return TaskResponse(
            task_id=task.id,
            task_type=TaskType.EXTRACT_ENTITIES,
            status=TaskStatus.PENDING,
            message="实体提取任务已提交"
        )
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.post("/batch-extract", response_model=TaskResponse)
async def submit_batch_extract_task(request: BatchExtractRequest):
    """提交批量实体提取任务"""
    try:
        task = batch_extract_entities_task.delay(
            document_ids=request.document_ids,
            knowledge_base_id=request.knowledge_base_id,
            batch_options=request.batch_options
        )
        
        return TaskResponse(
            task_id=task.id,
            task_type=TaskType.BATCH_EXTRACT,
            status=TaskStatus.PENDING,
            message="批量实体提取任务已提交"
        )
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.post("/align-entities", response_model=TaskResponse)
async def submit_align_entities_task(request: AlignEntitiesRequest):
    """提交实体对齐任务"""
    try:
        task = align_entities_task.delay(
            knowledge_base_id=request.knowledge_base_id,
            entity_ids=request.entity_ids,
            alignment_options=request.alignment_options
        )
        
        return TaskResponse(
            task_id=task.id,
            task_type=TaskType.ALIGN_ENTITIES,
            status=TaskStatus.PENDING,
            message="实体对齐任务已提交"
        )
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.post("/cross-kb-link", response_model=TaskResponse)
async def submit_cross_kb_link_task(request: CrossKBLinkRequest):
    """提交跨知识库链接任务"""
    try:
        task = cross_kb_link_task.delay(
            source_kb_id=request.source_kb_id,
            target_kb_id=request.target_kb_id,
            link_options=request.link_options
        )
        
        return TaskResponse(
            task_id=task.id,
            task_type=TaskType.CROSS_KB_LINK,
            status=TaskStatus.PENDING,
            message="跨知识库链接任务已提交"
        )
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status_endpoint(task_id: str):
    """
    获取任务状态
    
    查询任务的当前状态、进度和结果
    """
    try:
        status_info = get_task_status(task_id)
        
        if not status_info:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        return TaskStatusResponse(
            task_id=status_info.get('task_id', task_id),
            status=TaskStatus(status_info.get('status', 'pending')),
            progress=status_info.get('progress', 0),
            message=status_info.get('message', ''),
            result=status_info.get('result'),
            updated_at=status_info.get('updated_at', datetime.now().isoformat())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")


@router.get("/list", response_model=TaskListResponse)
async def list_tasks(
    task_type: Optional[TaskType] = Query(None, description="任务类型过滤"),
    status: Optional[TaskStatus] = Query(None, description="状态过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取任务列表
    
    支持按任务类型和状态过滤
    """
    try:
        # 实际项目中应该从Redis或数据库查询
        # 这里返回模拟数据
        tasks = []
        
        return TaskListResponse(
            tasks=tasks,
            total=len(tasks)
        )
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/{task_id}/revoke")
async def revoke_task(task_id: str):
    """
    取消任务
    
    终止正在执行的任务
    """
    try:
        from celery.result import AsyncResult
        from app.core.celery_config import get_celery_app
        
        celery_app = get_celery_app()
        result = AsyncResult(task_id, app=celery_app)
        
        if result.state in ['PENDING', 'STARTED', 'PROGRESS']:
            result.revoke(terminate=True)
            return {
                "task_id": task_id,
                "status": "revoked",
                "message": "任务已取消"
            }
        else:
            return {
                "task_id": task_id,
                "status": result.state.lower(),
                "message": f"任务状态为{result.state}，无法取消"
            }
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.get("/{task_id}/result")
async def get_task_result(task_id: str):
    """
    获取任务结果
    
    获取已完成任务的结果数据
    """
    try:
        from celery.result import AsyncResult
        from app.core.celery_config import get_celery_app
        
        celery_app = get_celery_app()
        result = AsyncResult(task_id, app=celery_app)
        
        if not result.ready():
            return {
                "task_id": task_id,
                "ready": False,
                "status": result.state.lower(),
                "message": "任务尚未完成"
            }
        
        if result.successful():
            return {
                "task_id": task_id,
                "ready": True,
                "status": "success",
                "result": result.result
            }
        else:
            return {
                "task_id": task_id,
                "ready": True,
                "status": "failure",
                "error": str(result.result) if result.result else "未知错误"
            }
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务结果失败: {str(e)}")
