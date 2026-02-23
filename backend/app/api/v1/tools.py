"""工具管理相关API接口"""
from typing import Any, Dict, List, Optional, Generic, TypeVar
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field

from app.modules.function_calling.tool_registry import ToolRegistry
from app.modules.function_calling.base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应模型"""
    success: bool = Field(default=True, description="是否成功")
    data: Optional[T] = Field(default=None, description="响应数据")
    message: Optional[str] = Field(default=None, description="响应消息")


class ToolParameters(BaseModel):
    """工具参数模型"""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


router = APIRouter()


class ToolCategoryResponse(BaseModel):
    """工具分类响应"""
    category: str
    display_name: str
    count: int


class ToolHistoryItem(BaseModel):
    """工具历史记录项"""
    tool_name: str
    display_name: str
    execution_time: float
    timestamp: str
    success: bool


class ToolSettings(BaseModel):
    """工具设置"""
    enable_auto_execution: bool = Field(default=True, description="启用自动执行")
    show_tool_calls: bool = Field(default=True, description="显示工具调用详情")
    enable_tool_logging: bool = Field(default=True, description="启用工具调用日志")
    execution_timeout: int = Field(default=30, description="工具执行超时（秒）")
    max_concurrent_calls: int = Field(default=5, description="最大并发工具调用数")


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    display_name: str
    description: str
    category: str
    version: str
    icon: str
    tags: List[str]
    is_active: bool
    parameters: List[Dict[str, Any]]


@router.get("/categories", response_model=ApiResponse[List[str]])
async def get_tool_categories():
    """
    获取工具分类列表
    
    Returns:
        工具分类列表
    """
    try:
        registry = ToolRegistry()
        categories = registry.get_categories()
        
        return ApiResponse[List[str]](
            success=True,
            data=list(categories.keys())
        )
    except Exception as e:
        logger.error(f"获取工具分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具分类失败: {str(e)}"
        )


@router.get("/history", response_model=ApiResponse[List[ToolHistoryItem]])
async def get_tool_history(limit: int = 50):
    """
    获取工具使用历史
    
    Args:
        limit: 返回的历史记录数量
        
    Returns:
        工具历史记录列表
    """
    try:
        registry = ToolRegistry()
        history = registry.get_execution_history(limit=limit)
        
        history_items = []
        for item in history:
            history_items.append(ToolHistoryItem(
                tool_name=item.get("tool_name", ""),
                display_name=item.get("display_name", ""),
                execution_time=item.get("execution_time", 0.0),
                timestamp=item.get("timestamp", ""),
                success=item.get("success", True)
            ))
        
        return ApiResponse[List[ToolHistoryItem]](
            success=True,
            data=history_items
        )
    except Exception as e:
        logger.error(f"获取工具历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具历史失败: {str(e)}"
        )


@router.get("/settings", response_model=ApiResponse[ToolSettings])
async def get_tool_settings():
    """
    获取工具设置
    
    Returns:
        工具设置
    """
    try:
        registry = ToolRegistry()
        settings = registry.get_settings()
        
        return ApiResponse[ToolSettings](
            success=True,
            data=ToolSettings(
                enable_auto_execution=settings.get("enable_auto_execution", True),
                show_tool_calls=settings.get("show_tool_calls", True),
                enable_tool_logging=settings.get("enable_tool_logging", True),
                execution_timeout=settings.get("execution_timeout", 30),
                max_concurrent_calls=settings.get("max_concurrent_calls", 5)
            )
        )
    except Exception as e:
        logger.error(f"获取工具设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具设置失败: {str(e)}"
        )


@router.put("/settings", response_model=ApiResponse[ToolSettings])
async def update_tool_settings(settings: ToolSettings):
    """
    更新工具设置
    
    Args:
        settings: 工具设置
        
    Returns:
        更新后的工具设置
    """
    try:
        registry = ToolRegistry()
        registry.update_settings({
            "enable_auto_execution": settings.enable_auto_execution,
            "show_tool_calls": settings.show_tool_calls,
            "enable_tool_logging": settings.enable_tool_logging,
            "execution_timeout": settings.execution_timeout,
            "max_concurrent_calls": settings.max_concurrent_calls
        })
        
        return ApiResponse[ToolSettings](
            success=True,
            data=settings
        )
    except Exception as e:
        logger.error(f"更新工具设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新工具设置失败: {str(e)}"
        )


@router.delete("/history", response_model=ApiResponse[Dict[str, str]])
async def clear_tool_history():
    """
    清空工具历史记录
    
    Returns:
        操作结果
    """
    try:
        registry = ToolRegistry()
        registry.clear_execution_history()
        
        return ApiResponse[Dict[str, str]](
            success=True,
            data={"message": "工具历史记录已清空"}
        )
    except Exception as e:
        logger.error(f"清空工具历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空工具历史失败: {str(e)}"
        )


@router.get("", response_model=ApiResponse[List[ToolInfo]])
async def get_tools(category: Optional[str] = None):
    """
    获取工具列表
    
    Args:
        category: 工具分类（可选）
        
    Returns:
        工具列表
    """
    try:
        registry = ToolRegistry()
        
        if category:
            tools = registry.get_tools_by_category(category)
        else:
            tools = registry.get_all_tools()
        
        tool_infos = []
        for tool_name, tool in tools.items():
            metadata = tool.get_metadata()
            parameters = tool.get_parameters()
            
            parameter_list = []
            for param in parameters:
                parameter_list.append({
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default
                })
            
            tool_infos.append(ToolInfo(
                name=metadata.name,
                display_name=metadata.display_name,
                description=metadata.description,
                category=metadata.category,
                version=metadata.version,
                icon=metadata.icon,
                tags=metadata.tags,
                is_active=metadata.is_active,
                parameters=parameter_list
            ))
        
        return ApiResponse[List[ToolInfo]](
            success=True,
            data=tool_infos
        )
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )


@router.post("/{tool_name}/execute", response_model=ApiResponse[Dict[str, Any]])
async def execute_tool(tool_name: str, tool_params: ToolParameters):
    """
    执行工具
    
    Args:
        tool_name: 工具名称
        tool_params: 工具参数
        
    Returns:
        工具执行结果
    """
    try:
        registry = ToolRegistry()
        tool = registry.get_tool(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具 '{tool_name}' 不存在"
            )
        
        result = await tool.execute(tool_params.parameters)
        
        if result.success:
            metadata = tool.get_metadata()
            registry.add_execution_history(
                tool_name=metadata.name,
                display_name=metadata.display_name,
                execution_time=result.execution_time,
                success=True
            )
        else:
            metadata = tool.get_metadata()
            registry.add_execution_history(
                tool_name=metadata.name,
                display_name=metadata.display_name,
                execution_time=result.execution_time,
                success=False
            )
        
        return ApiResponse[Dict[str, Any]](
            success=True,
            data={
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "error_code": result.error_code,
                "execution_time": result.execution_time,
                "metadata": result.metadata
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行工具失败: {str(e)}"
        )


@router.get("/{tool_name}", response_model=ApiResponse[ToolInfo])
async def get_tool_info(tool_name: str):
    """
    获取工具详细信息
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具详细信息
    """
    try:
        registry = ToolRegistry()
        tool = registry.get_tool(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具 '{tool_name}' 不存在"
            )
        
        metadata = tool.get_metadata()
        parameters = tool.get_parameters()
        
        parameter_list = []
        for param in parameters:
            parameter_list.append({
                "name": param.name,
                "type": param.type,
                "description": param.description,
                "required": param.required,
                "default": param.default
            })
        
        return ApiResponse[ToolInfo](
            success=True,
            data=ToolInfo(
                name=metadata.name,
                display_name=metadata.display_name,
                description=metadata.description,
                category=metadata.category,
                version=metadata.version,
                icon=metadata.icon,
                tags=metadata.tags,
                is_active=metadata.is_active,
                parameters=parameter_list
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具信息失败: {str(e)}"
        )


@router.patch("/{tool_name}/status", response_model=ApiResponse[Dict[str, str]])
async def toggle_tool_status(tool_name: str, is_active: bool = Body(..., embed=True)):
    """
    切换工具激活状态
    
    Args:
        tool_name: 工具名称
        is_active: 是否激活
        
    Returns:
        操作结果
    """
    try:
        registry = ToolRegistry()
        success = registry.update_tool_status(tool_name, is_active)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具 '{tool_name}' 不存在"
            )
        
        return ApiResponse[Dict[str, str]](
            success=True,
            data={"message": f"工具状态已更新为 {'激活' if is_active else '禁用'}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换工具状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换工具状态失败: {str(e)}"
        )
