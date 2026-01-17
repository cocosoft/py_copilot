"""智能体编排系统API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.logging_config import log_execution
from ..services.smart_orchestrator import SmartOrchestrator
from ..schemas.orchestration import OrchestrationRequest, OrchestrationResponse

router = APIRouter()

@router.post("/orchestrate", response_model=OrchestrationResponse)
@log_execution
async def orchestrate(
    request: OrchestrationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """智能体编排API"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"收到智能体编排请求: {request.query[:100]}...")
        
        # 构建用户上下文
        user_context = {
            "user_id": current_user["id"],
            "conversation_id": request.conversation_id,
            "user_role": current_user.get("role", "user"),
            "user_language": request.language or "zh-CN"
        }
        
        # 创建SmartOrchestrator实例
        orchestrator = SmartOrchestrator()
        
        # 执行编排
        result = await orchestrator.orchestrate(request.query, user_context)
        
        logger.info(f"智能体编排请求处理完成")
        
        return OrchestrationResponse(
            success=result["success"],
            result=result.get("result", {}),
            intent=result.get("intent"),
            route=result.get("route"),
            error=result.get("error"),
            message=result.get("message")
        )
        
    except Exception as e:
        logger.error(f"智能体编排请求处理失败: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"智能体编排失败: {str(e)}"
        )
