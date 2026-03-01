"""
编排API路由

本模块提供智能编排相关的RESTful API接口
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.services.orchestration_service import OrchestrationService
from app.capabilities.center.unified_center import UnifiedCapabilityCenter

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 请求/响应模型 ============

class ProcessRequest(BaseModel):
    """处理请求"""
    user_input: str = Field(..., description="用户输入", min_length=1, max_length=4000)
    conversation_id: Optional[str] = Field(None, description="对话ID")


class ProcessResponse(BaseModel):
    """处理响应"""
    type: str = Field(..., description="响应类型")
    conversation_id: str = Field(..., description="对话ID")
    message: str = Field(..., description="响应消息")
    intent: Optional[dict] = Field(None, description="意图信息")
    plan: Optional[dict] = Field(None, description="计划信息")
    execution_time_ms: Optional[int] = Field(None, description="执行时间")


class ConversationHistoryResponse(BaseModel):
    """对话历史响应"""
    conversation_id: str = Field(..., description="对话ID")
    messages: list = Field(..., description="消息列表")


class ExecutionStatusResponse(BaseModel):
    """执行状态响应"""
    status: str = Field(..., description="执行状态")
    is_running: bool = Field(..., description="是否运行中")
    progress: Optional[dict] = Field(None, description="进度信息")
    current_plan_id: Optional[str] = Field(None, description="当前计划ID")


class ServiceStatsResponse(BaseModel):
    """服务统计响应"""
    context_manager: dict = Field(..., description="上下文管理器统计")
    orchestrator: dict = Field(..., description="编排器统计")


# ============ 依赖注入 ============

def get_capability_center(db: Session = Depends(get_db)) -> UnifiedCapabilityCenter:
    """获取能力中心实例"""
    center = UnifiedCapabilityCenter(db)
    # 注意：实际应用中应该使用单例模式或依赖注入容器
    return center


def get_orchestration_service(
    center: UnifiedCapabilityCenter = Depends(get_capability_center),
    db: Session = Depends(get_db)
) -> OrchestrationService:
    """获取编排服务实例"""
    return OrchestrationService(center, db)


# ============ API路由 ============

@router.post("/process", response_model=ProcessResponse)
async def process_request(
    request: ProcessRequest,
    service: OrchestrationService = Depends(get_orchestration_service),
    current_user: dict = Depends(get_current_user)
):
    """
    处理用户请求

    接收用户输入，进行意图理解、任务规划和执行
    """
    try:
        result = await service.process_request(
            user_input=request.user_input,
            conversation_id=request.conversation_id,
            user_id=current_user.get("id") if current_user else None
        )

        return ProcessResponse(**result)

    except Exception as e:
        logger.error(f"处理请求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/process/stream")
async def process_request_stream(
    request: ProcessRequest,
    service: OrchestrationService = Depends(get_orchestration_service),
    current_user: dict = Depends(get_current_user)
):
    """
    流式处理用户请求

    使用SSE(Server-Sent Events)返回流式响应
    """
    async def event_generator():
        async for event in service.process_request_stream(
            user_input=request.user_input,
            conversation_id=request.conversation_id,
            user_id=current_user.get("id") if current_user else None
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/conversations/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50,
    service: OrchestrationService = Depends(get_orchestration_service),
    current_user: dict = Depends(get_current_user)
):
    """
    获取对话历史
    """
    try:
        messages = service.get_conversation_history(conversation_id, limit)

        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=messages
        )

    except Exception as e:
        logger.error(f"获取对话历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    service: OrchestrationService = Depends(get_orchestration_service),
    current_user: dict = Depends(get_current_user)
):
    """
    清空对话
    """
    try:
        success = service.clear_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=404, detail="对话不存在")

        return {"message": "对话已清空", "conversation_id": conversation_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


@router.get("/status", response_model=ExecutionStatusResponse)
async def get_execution_status(
    service: OrchestrationService = Depends(get_orchestration_service),
    current_user: dict = Depends(get_current_user)
):
    """
    获取执行状态
    """
    try:
        status = service.get_execution_status()
        return ExecutionStatusResponse(**status)

    except Exception as e:
        logger.error(f"获取执行状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/cancel")
async def cancel_execution(
    service: OrchestrationService = Depends(get_orchestration_service),
    current_user: dict = Depends(get_current_user)
):
    """
    取消当前执行
    """
    try:
        success = service.cancel_execution()

        if success:
            return {"message": "执行已取消"}
        else:
            return {"message": "没有正在执行的任务"}

    except Exception as e:
        logger.error(f"取消执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取消失败: {str(e)}")


@router.get("/stats", response_model=ServiceStatsResponse)
async def get_service_stats(
    service: OrchestrationService = Depends(get_orchestration_service),
    current_user: dict = Depends(get_current_user)
):
    """
    获取服务统计信息
    """
    try:
        stats = service.get_service_stats()
        return ServiceStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ============ 健康检查 ============

@router.get("/health")
async def health_check(
    service: OrchestrationService = Depends(get_orchestration_service)
):
    """
    健康检查
    """
    try:
        status = service.get_execution_status()

        return {
            "status": "healthy",
            "orchestrator_status": status["status"],
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="服务不健康")
