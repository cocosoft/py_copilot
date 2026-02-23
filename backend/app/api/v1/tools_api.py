"""工具管理API路由"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from app.modules.function_calling.tool_registry import ToolRegistry
from app.modules.function_calling.base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tools", tags=["工具管理"])


def get_tool_registry() -> ToolRegistry:
    """
    获取工具注册中心实例
    
    Returns:
        工具注册中心实例
    """
    return ToolRegistry()


@router.get("", summary="获取所有工具列表")
async def list_tools(
    category: Optional[str] = None,
    registry: ToolRegistry = Depends(get_tool_registry)
):
    """
    获取所有可用工具列表
    
    Args:
        category: 工具分类，不指定则返回所有工具
        
    Returns:
        工具列表
    """
    try:
        tools = registry.list_tools(category)
        
        return {
            "success": True,
            "data": [
                {
                    "name": tool.get_metadata().name,
                    "display_name": tool.get_metadata().display_name,
                    "description": tool.get_metadata().description,
                    "category": tool.get_metadata().category,
                    "version": tool.get_metadata().version,
                    "author": tool.get_metadata().author,
                    "icon": tool.get_metadata().icon,
                    "tags": tool.get_metadata().tags,
                    "is_active": tool.get_metadata().is_active
                }
                for tool in tools
            ],
            "total": len(tools)
        }
        
    except Exception as e:
        logger.error(f"获取工具列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tool_name}", summary="获取工具详情")
async def get_tool_detail(
    tool_name: str,
    registry: ToolRegistry = Depends(get_tool_registry)
):
    """
    获取指定工具的详细信息
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具详情
    """
    try:
        tool = registry.get_tool(tool_name)
        
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 不存在")
        
        metadata = tool.get_metadata()
        parameters = tool._get_parameters()
        
        return {
            "success": True,
            "data": {
                "name": metadata.name,
                "display_name": metadata.display_name,
                "description": metadata.description,
                "category": metadata.category,
                "version": metadata.version,
                "author": metadata.author,
                "icon": metadata.icon,
                "tags": metadata.tags,
                "is_active": metadata.is_active,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type,
                        "description": param.description,
                        "required": param.required,
                        "default": param.default,
                        "enum": param.enum
                    }
                    for param in parameters
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", summary="获取所有工具分类")
async def get_categories(
    registry: ToolRegistry = Depends(get_tool_registry)
):
    """
    获取所有工具分类
    
    Returns:
        分类列表
    """
    try:
        categories = registry.get_categories()
        
        return {
            "success": True,
            "data": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        logger.error(f"获取工具分类失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/definitions", summary="获取工具定义列表")
async def get_tool_definitions(
    category: Optional[str] = None,
    registry: ToolRegistry = Depends(get_tool_registry)
):
    """
    获取工具定义列表（用于Function Calling）
    
    Args:
        category: 工具分类，不指定则返回所有工具定义
        
    Returns:
        工具定义列表
    """
    try:
        definitions = registry.get_tool_definitions(category)
        
        return {
            "success": True,
            "data": definitions,
            "total": len(definitions)
        }
        
    except Exception as e:
        logger.error(f"获取工具定义失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tool_name}/execute", summary="执行工具")
async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    registry: ToolRegistry = Depends(get_tool_registry)
):
    """
    执行指定工具
    
    Args:
        tool_name: 工具名称
        parameters: 工具参数
        
    Returns:
        执行结果
    """
    try:
        tool = registry.get_tool(tool_name)
        
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 不存在")
        
        result = await tool.execute(**parameters)
        
        return {
            "success": result.success,
            "data": result.result,
            "error": result.error,
            "error_code": result.error_code,
            "execution_time": result.execution_time,
            "tool_name": result.tool_name,
            "metadata": result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工具失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="搜索工具")
async def search_tools(
    keyword: str,
    registry: ToolRegistry = Depends(get_tool_registry)
):
    """
    根据关键词搜索工具
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的工具列表
    """
    try:
        tools = registry.search_tools(keyword)
        
        return {
            "success": True,
            "data": [
                {
                    "name": tool.get_metadata().name,
                    "display_name": tool.get_metadata().display_name,
                    "description": tool.get_metadata().description,
                    "category": tool.get_metadata().category,
                    "icon": tool.get_metadata().icon
                }
                for tool in tools
            ],
            "total": len(tools)
        }
        
    except Exception as e:
        logger.error(f"搜索工具失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
