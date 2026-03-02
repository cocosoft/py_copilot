"""
工具管理器

管理所有工具的注册、发现、执行和监控
"""

from typing import Dict, List, Optional, Any, Type
import logging
import asyncio
from datetime import datetime

from app.modules.function_calling.base_tool import BaseTool, ServiceTool
from app.modules.function_calling.tool_schemas import (
    ToolMetadata,
    ToolExecutionResult,
    ToolInfo,
    ToolCategory
)

logger = logging.getLogger(__name__)


class ToolManager:
    """
    工具管理器
    
    负责管理所有工具的注册、发现、执行和监控
    """
    
    _instance = None
    _tools: Dict[str, BaseTool] = {}
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化工具管理器"""
        if ToolManager._initialized:
            return
        
        self._tools = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
        ToolManager._initialized = True
        
        logger.info("工具管理器初始化完成")
    
    def register_tool(self, tool: BaseTool) -> bool:
        """
        注册工具
        
        Args:
            tool: 工具实例
            
        Returns:
            bool: 是否注册成功
        """
        try:
            metadata = tool.get_metadata()
            tool_name = metadata.name
            
            if tool_name in self._tools:
                logger.warning(f"工具 '{tool_name}' 已存在，将被覆盖")
            
            self._tools[tool_name] = tool
            logger.info(f"工具 '{tool_name}' 注册成功")
            return True
            
        except Exception as e:
            logger.error(f"工具注册失败: {str(e)}")
            return False
    
    def register_tools(self, tools: List[BaseTool]) -> Dict[str, bool]:
        """
        批量注册工具
        
        Args:
            tools: 工具实例列表
            
        Returns:
            Dict[str, bool]: 每个工具的注册结果
        """
        results = {}
        for tool in tools:
            metadata = tool.get_metadata()
            results[metadata.name] = self.register_tool(tool)
        return results
    
    def unregister_tool(self, tool_name: str) -> bool:
        """
        注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否注销成功
        """
        if tool_name not in self._tools:
            logger.warning(f"工具 '{tool_name}' 不存在")
            return False
        
        del self._tools[tool_name]
        logger.info(f"工具 '{tool_name}' 已注销")
        return True
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[BaseTool]: 工具实例，不存在则返回None
        """
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        获取所有工具
        
        Returns:
            List[BaseTool]: 工具实例列表
        """
        return list(self._tools.values())
    
    def get_tool_names(self) -> List[str]:
        """
        获取所有工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self._tools.keys())
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """
        按类别获取工具
        
        Args:
            category: 工具类别
            
        Returns:
            List[BaseTool]: 工具实例列表
        """
        return [
            tool for tool in self._tools.values()
            if tool.get_metadata().category == category
        ]
    
    def get_active_tools(self) -> List[BaseTool]:
        """
        获取所有激活的工具
        
        Returns:
            List[BaseTool]: 激活的工具实例列表
        """
        return [
            tool for tool in self._tools.values()
            if tool.get_metadata().is_active
        ]
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[ToolInfo]: 工具信息，不存在则返回None
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return None
        
        return ToolInfo(
            metadata=tool.get_metadata(),
            parameters=tool.get_parameters(),
            schema=tool.get_schema()
        )
    
    def get_all_tools_info(self) -> List[ToolInfo]:
        """
        获取所有工具信息
        
        Returns:
            List[ToolInfo]: 工具信息列表
        """
        return [
            ToolInfo(
                metadata=tool.get_metadata(),
                parameters=tool.get_parameters(),
                schema=tool.get_schema()
            )
            for tool in self._tools.values()
        ]
    
    async def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolExecutionResult:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            ToolExecutionResult: 执行结果
        """
        tool = self._tools.get(tool_name)
        
        if not tool:
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"工具 '{tool_name}' 不存在",
                error_code="TOOL_NOT_FOUND"
            )
        
        metadata = tool.get_metadata()
        
        if not metadata.is_active:
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"工具 '{tool_name}' 未激活",
                error_code="TOOL_INACTIVE"
            )
        
        try:
            # 执行工具
            result = await tool.execute(**kwargs)
            
            # 记录执行历史
            self._record_execution(tool_name, kwargs, result)
            
            return result
            
        except Exception as e:
            logger.error(f"工具 '{tool_name}' 执行异常: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"执行异常: {str(e)}",
                error_code="EXECUTION_EXCEPTION"
            )
    
    async def execute_tools_parallel(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """
        并行执行多个工具
        
        Args:
            tool_calls: 工具调用列表，每个元素包含 'tool_name' 和 'params'
                例如: [{"tool_name": "calculator", "params": {"expression": "1+1"}}]
        
        Returns:
            List[ToolExecutionResult]: 执行结果列表
        """
        tasks = []
        
        for call in tool_calls:
            tool_name = call.get("tool_name")
            params = call.get("params", {})
            
            task = self.execute_tool(tool_name, **params)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tool_name = tool_calls[i].get("tool_name", "unknown")
                processed_results.append(
                    ToolExecutionResult.error_result(
                        tool_name=tool_name,
                        error=f"执行异常: {str(result)}",
                        error_code="PARALLEL_EXECUTION_ERROR"
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _record_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: ToolExecutionResult
    ):
        """
        记录工具执行历史
        
        Args:
            tool_name: 工具名称
            params: 执行参数
            result: 执行结果
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "params": params,
            "success": result.success,
            "execution_time": result.execution_time
        }
        
        self._execution_history.append(record)
        
        # 限制历史记录大小
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]
    
    def get_execution_history(
        self,
        tool_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Args:
            tool_name: 工具名称过滤（可选）
            limit: 返回记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 执行历史记录
        """
        history = self._execution_history
        
        if tool_name:
            history = [h for h in history if h["tool_name"] == tool_name]
        
        return history[-limit:]
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """
        获取工具统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_tools = len(self._tools)
        active_tools = len(self.get_active_tools())
        
        # 按类别统计
        category_counts = {}
        for tool in self._tools.values():
            category = tool.get_metadata().category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 执行统计
        total_executions = len(self._execution_history)
        successful_executions = sum(1 for h in self._execution_history if h["success"])
        failed_executions = total_executions - successful_executions
        
        return {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "inactive_tools": total_tools - active_tools,
            "category_distribution": category_counts,
            "execution_statistics": {
                "total": total_executions,
                "successful": successful_executions,
                "failed": failed_executions,
                "success_rate": round(successful_executions / total_executions * 100, 2) if total_executions > 0 else 0
            }
        }
    
    def enable_tool(self, tool_name: str) -> bool:
        """
        启用工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否成功
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return False
        
        tool.get_metadata().is_active = True
        logger.info(f"工具 '{tool_name}' 已启用")
        return True
    
    def disable_tool(self, tool_name: str) -> bool:
        """
        禁用工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否成功
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return False
        
        tool.get_metadata().is_active = False
        logger.info(f"工具 '{tool_name}' 已禁用")
        return True
    
    def clear_history(self):
        """清空执行历史"""
        self._execution_history.clear()
        logger.info("执行历史已清空")


# 全局工具管理器实例
tool_manager = ToolManager()
