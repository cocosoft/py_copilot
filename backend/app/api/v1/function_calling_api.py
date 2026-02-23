"""Function Calling API路由"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.modules.function_calling.function_calling_service import FunctionCallingService
from app.modules.function_calling.tool_registry import ToolRegistry
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/function-calling", tags=["Function Calling"])


def get_function_calling_service() -> FunctionCallingService:
    """
    获取Function Calling服务实例
    
    Returns:
        Function Calling服务实例
    """
    return FunctionCallingService()


def get_tool_registry() -> ToolRegistry:
    """
    获取工具注册中心实例
    
    Returns:
        工具注册中心实例
    """
    return ToolRegistry()


@router.post("/chat", summary="Function Calling聊天")
async def function_calling_chat(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    fc_service: FunctionCallingService = Depends(get_function_calling_service)
) -> Any:
    """
    使用Function Calling进行聊天
    
    Args:
        request: 聊天请求参数
        db: 数据库会话
        current_user: 当前活跃用户
        fc_service: Function Calling服务
        
    Returns:
        聊天结果
    """
    try:
        messages = request.get("messages", [])
        model_name = request.get("model_name")
        tools = request.get("tools")
        max_iterations = request.get("max_iterations", 5)
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="messages参数不能为空"
            )
        
        if not model_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="model_name参数不能为空"
            )
        
        # 调用Function Calling服务
        result = await fc_service.process_with_function_calling(
            messages=messages,
            model_name=model_name,
            tools=tools,
            max_iterations=max_iterations
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Function Calling处理失败")
            )
        
        return {
            "success": True,
            "data": {
                "response": result.get("response"),
                "tool_calls": result.get("tool_calls", []),
                "iterations": result.get("iterations")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Function Calling聊天失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Function Calling聊天失败: {str(e)}"
        )


@router.get("/stats", summary="获取Function Calling统计信息")
async def get_function_calling_stats(
    fc_service: FunctionCallingService = Depends(get_function_calling_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取Function Calling执行统计信息
    
    Args:
        fc_service: Function Calling服务
        current_user: 当前活跃用户
        
    Returns:
        统计信息
    """
    try:
        stats = fc_service.get_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取Function Calling统计信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.post("/stats/reset", summary="重置Function Calling统计信息")
async def reset_function_calling_stats(
    fc_service: FunctionCallingService = Depends(get_function_calling_service),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    重置Function Calling执行统计信息
    
    Args:
        fc_service: Function Calling服务
        current_user: 当前活跃用户
        
    Returns:
        操作结果
    """
    try:
        fc_service.reset_stats()
        
        return {
            "success": True,
            "message": "统计信息已重置"
        }
        
    except Exception as e:
        logger.error(f"重置Function Calling统计信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置统计信息失败: {str(e)}"
        )
