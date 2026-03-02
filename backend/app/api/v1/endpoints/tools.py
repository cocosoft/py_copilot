"""
工具API端点

提供工具相关的RESTful API接口
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.function_calling.tool_manager import tool_manager
from app.modules.function_calling.tool_schemas import ToolInfo, ToolExecutionResult

router = APIRouter()


# 请求模型
class ToolExecuteRequest(BaseModel):
    """工具执行请求"""
    tool_name: str = Field(..., description="工具名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class ToolExecuteBatchRequest(BaseModel):
    """批量工具执行请求"""
    calls: List[ToolExecuteRequest] = Field(..., description="工具调用列表")


class ToolEnableRequest(BaseModel):
    """工具启用/禁用请求"""
    tool_name: str = Field(..., description="工具名称")
    enable: bool = Field(..., description="是否启用")


# 响应模型
class ToolListResponse(BaseModel):
    """工具列表响应"""
    tools: List[ToolInfo]
    total: int


class ToolExecuteResponse(BaseModel):
    """工具执行响应"""
    success: bool
    result: Any
    execution_time: float
    error: Optional[str] = None
    error_code: Optional[str] = None


class ToolStatisticsResponse(BaseModel):
    """工具统计响应"""
    total_tools: int
    active_tools: int
    inactive_tools: int
    category_distribution: Dict[str, int]
    execution_statistics: Dict[str, Any]


@router.get("/tools", response_model=ToolListResponse)
async def list_tools(
    category: Optional[str] = Query(None, description="按类别过滤"),
    active_only: bool = Query(False, description="仅返回激活的工具")
):
    """
    获取工具列表
    
    Args:
        category: 工具类别过滤
        active_only: 是否仅返回激活的工具
        
    Returns:
        ToolListResponse: 工具列表
    """
    if category:
        tools = tool_manager.get_tools_by_category(category)
    elif active_only:
        tools = tool_manager.get_active_tools()
    else:
        tools = tool_manager.get_all_tools()
    
    tools_info = [
        ToolInfo(
            metadata=tool.get_metadata(),
            parameters=tool.get_parameters(),
            schema=tool.get_schema()
        )
        for tool in tools
    ]
    
    return ToolListResponse(
        tools=tools_info,
        total=len(tools_info)
    )


@router.get("/tools/{tool_name}", response_model=ToolInfo)
async def get_tool(tool_name: str):
    """
    获取工具详细信息
    
    Args:
        tool_name: 工具名称
        
    Returns:
        ToolInfo: 工具信息
        
    Raises:
        HTTPException: 工具不存在时返回404
    """
    tool_info = tool_manager.get_tool_info(tool_name)
    
    if not tool_info:
        raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 不存在")
    
    return tool_info


@router.post("/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest):
    """
    执行工具
    
    Args:
        request: 工具执行请求
        
    Returns:
        ToolExecuteResponse: 执行结果
    """
    result = await tool_manager.execute_tool(
        tool_name=request.tool_name,
        **request.params
    )
    
    return ToolExecuteResponse(
        success=result.success,
        result=result.result if result.success else None,
        execution_time=result.execution_time,
        error=result.error if not result.success else None,
        error_code=result.error_code if not result.success else None
    )


@router.post("/tools/execute/batch", response_model=List[ToolExecuteResponse])
async def execute_tools_batch(request: ToolExecuteBatchRequest):
    """
    批量执行工具
    
    Args:
        request: 批量工具执行请求
        
    Returns:
        List[ToolExecuteResponse]: 执行结果列表
    """
    tool_calls = [
        {"tool_name": call.tool_name, "params": call.params}
        for call in request.calls
    ]
    
    results = await tool_manager.execute_tools_parallel(tool_calls)
    
    return [
        ToolExecuteResponse(
            success=result.success,
            result=result.result if result.success else None,
            execution_time=result.execution_time,
            error=result.error if not result.success else None,
            error_code=result.error_code if not result.success else None
        )
        for result in results
    ]


@router.get("/tools/categories")
async def list_categories():
    """
    获取工具类别列表
    
    Returns:
        Dict[str, List[str]]: 类别列表
    """
    from app.modules.function_calling.tool_schemas import ToolCategory
    
    categories = [
        ToolCategory.SEARCH.value,
        ToolCategory.KNOWLEDGE.value,
        ToolCategory.MEMORY.value,
        ToolCategory.FILE.value,
        ToolCategory.TEXT.value,
        ToolCategory.IMAGE.value,
        ToolCategory.CALCULATION.value,
        ToolCategory.DATA.value,
        ToolCategory.CODE.value,
        ToolCategory.API.value,
        ToolCategory.UTILITY.value
    ]
    
    return {"categories": categories}


@router.get("/tools/statistics", response_model=ToolStatisticsResponse)
async def get_statistics():
    """
    获取工具统计信息
    
    Returns:
        ToolStatisticsResponse: 统计信息
    """
    stats = tool_manager.get_tool_statistics()
    return ToolStatisticsResponse(**stats)


@router.post("/tools/{tool_name}/enable")
async def enable_tool(tool_name: str, enable: bool = True):
    """
    启用或禁用工具
    
    Args:
        tool_name: 工具名称
        enable: 是否启用
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    if enable:
        success = tool_manager.enable_tool(tool_name)
    else:
        success = tool_manager.disable_tool(tool_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 不存在")
    
    return {
        "success": True,
        "tool_name": tool_name,
        "enabled": enable
    }


@router.get("/tools/history")
async def get_execution_history(
    tool_name: Optional[str] = Query(None, description="工具名称过滤"),
    limit: int = Query(100, description="返回记录数量限制")
):
    """
    获取工具执行历史
    
    Args:
        tool_name: 工具名称过滤
        limit: 返回记录数量限制
        
    Returns:
        Dict[str, Any]: 执行历史
    """
    history = tool_manager.get_execution_history(tool_name, limit)
    
    return {
        "history": history,
        "count": len(history)
    }


@router.post("/tools/history/clear")
async def clear_execution_history():
    """
    清空执行历史
    
    Returns:
        Dict[str, Any]: 操作结果
    """
    tool_manager.clear_history()
    
    return {
        "success": True,
        "message": "执行历史已清空"
    }
