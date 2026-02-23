"""Function Calling服务"""
from typing import Dict, Any, List, Optional
from app.modules.function_calling.tool_registry import ToolRegistry
from app.modules.function_calling.base_tool import BaseTool, ToolExecutionResult
from app.modules.llm.services.llm_service import LLMService
import logging
import json
import time

logger = logging.getLogger(__name__)


class FunctionCallingService:
    """Function Calling服务，处理大模型的工具调用"""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        初始化Function Calling服务
        
        Args:
            llm_service: LLM服务实例
        """
        self.tool_registry = ToolRegistry()
        self.llm_service = llm_service or LLMService()
        self._execution_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "tool_usage": {}
        }
    
    async def process_with_function_calling(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        tools: Optional[List[str]] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        使用Function Calling处理消息
        
        Args:
            messages: 消息列表
            model_name: 模型名称
            tools: 允许使用的工具列表，None表示使用所有工具
            max_iterations: 最大迭代次数
            
        Returns:
            处理结果
        """
        try:
            # 获取允许使用的工具定义
            available_tools = self._get_available_tools(tools)
            tool_definitions = [
                tool.get_tool_definition() for tool in available_tools
            ]
            
            if not tool_definitions:
                logger.warning("没有可用的工具")
                return await self._generate_response_without_tools(
                    messages, model_name
                )
            
            iteration = 0
            current_messages = messages.copy()
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Function Calling迭代 {iteration}/{max_iterations}")
                
                # 调用模型，包含工具定义
                model_response = await self._call_model_with_tools(
                    current_messages,
                    model_name,
                    tool_definitions
                )
                
                # 检查是否有工具调用
                tool_calls = self._extract_tool_calls(model_response)
                
                if not tool_calls:
                    # 没有工具调用，返回最终响应
                    return {
                        "success": True,
                        "response": model_response.get("content", ""),
                        "tool_calls": [],
                        "iterations": iteration
                    }
                
                # 执行工具调用
                tool_results = await self._execute_tool_calls(tool_calls)
                
                # 将工具调用和结果添加到消息中
                current_messages.extend(self._format_tool_calls(tool_calls, tool_results))
                
                # 继续迭代，让模型基于工具结果生成最终响应
            
            # 达到最大迭代次数
            logger.warning(f"达到最大迭代次数 {max_iterations}")
            return {
                "success": False,
                "error": "达到最大迭代次数，未能完成任务",
                "iterations": iteration
            }
            
        except Exception as e:
            logger.error(f"Function Calling处理失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_available_tools(self, tool_names: Optional[List[str]] = None) -> List[BaseTool]:
        """
        获取可用的工具列表
        
        Args:
            tool_names: 工具名称列表，None表示获取所有工具
            
        Returns:
            工具列表
        """
        if tool_names is None:
            return self.tool_registry.list_tools()
        
        tools = []
        for name in tool_names:
            tool = self.tool_registry.get_tool(name)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"工具 '{name}' 不存在")
        
        return tools
    
    async def _call_model_with_tools(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        tool_definitions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        调用模型，包含工具定义
        
        Args:
            messages: 消息列表
            model_name: 模型名称
            tool_definitions: 工具定义列表
            
        Returns:
            模型响应
        """
        try:
            # 调用LLM服务
            response = self.llm_service.chat(
                messages=messages,
                model_name=model_name,
                tools=tool_definitions
            )
            
            return response
            
        except Exception as e:
            logger.error(f"调用模型失败: {str(e)}")
            raise
    
    def _extract_tool_calls(self, model_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从模型响应中提取工具调用
        
        Args:
            model_response: 模型响应
            
        Returns:
            工具调用列表
        """
        tool_calls = []
        
        # 检查OpenAI格式的工具调用
        if "tool_calls" in model_response:
            tool_calls = model_response["tool_calls"]
        
        # 检查自定义格式的工具调用
        elif "function_call" in model_response:
            tool_calls = [model_response["function_call"]]
        
        # 检查文本中的工具调用（JSON格式）
        elif "content" in model_response:
            content = model_response["content"]
            try:
                # 尝试解析JSON格式的工具调用
                if "{" in content and "}" in content:
                    import re
                    json_pattern = r'\{[^{}]*"type"[^{}]*"tool_call"[^{}]*\}'
                    matches = re.findall(json_pattern, content, re.DOTALL)
                    
                    for match in matches:
                        call_data = json.loads(match)
                        if call_data.get("type") == "tool_call":
                            tool_calls.append(call_data)
            except Exception as e:
                logger.debug(f"解析工具调用失败: {str(e)}")
        
        return tool_calls
    
    async def _execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """
        执行工具调用
        
        Args:
            tool_calls: 工具调用列表
            
        Returns:
            执行结果列表
        """
        results = []
        
        for tool_call in tool_calls:
            try:
                # 解析工具调用
                tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
                arguments = tool_call.get("arguments") or tool_call.get("function", {}).get("arguments", {})
                
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                
                # 获取工具实例
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    results.append(ToolExecutionResult(
                        success=False,
                        error=f"工具 '{tool_name}' 不存在",
                        execution_time=0.0,
                        tool_name=tool_name
                    ))
                    continue
                
                # 执行工具
                start_time = time.time()
                result = await tool.execute(**arguments)
                execution_time = time.time() - start_time
                
                # 更新统计信息
                self._update_stats(tool_name, result.success)
                
                # 设置执行时间
                result.execution_time = execution_time
                results.append(result)
                
            except Exception as e:
                logger.error(f"执行工具调用失败: {str(e)}")
                results.append(ToolExecutionResult(
                    success=False,
                    error=str(e),
                    execution_time=0.0,
                    tool_name=tool_call.get("name", "unknown")
                ))
        
        return results
    
    def _format_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        tool_results: List[ToolExecutionResult]
    ) -> List[Dict[str, str]]:
        """
        格式化工具调用和结果为消息
        
        Args:
            tool_calls: 工具调用列表
            tool_results: 执行结果列表
            
        Returns:
            消息列表
        """
        messages = []
        
        # 添加工具调用消息
        for tool_call in tool_calls:
            tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
            arguments = tool_call.get("arguments") or tool_call.get("function", {}).get("arguments", {})
            
            messages.append({
                "role": "assistant",
                "content": json.dumps({
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "arguments": arguments
                }, ensure_ascii=False)
            })
        
        # 添加工具结果消息
        for result in tool_results:
            if result.success:
                messages.append({
                    "role": "tool",
                    "content": json.dumps({
                        "tool_name": result.tool_name,
                        "result": result.result
                    }, ensure_ascii=False)
                })
            else:
                messages.append({
                    "role": "tool",
                    "content": json.dumps({
                        "tool_name": result.tool_name,
                        "error": result.error
                    }, ensure_ascii=False)
                })
        
        return messages
    
    async def _generate_response_without_tools(
        self,
        messages: List[Dict[str, str]],
        model_name: str
    ) -> Dict[str, Any]:
        """
        不使用工具生成响应
        
        Args:
            messages: 消息列表
            model_name: 模型名称
            
        Returns:
            响应结果
        """
        try:
            response = self.llm_service.chat(
                messages=messages,
                model_name=model_name
            )
            
            return {
                "success": True,
                "response": response.get("content", ""),
                "tool_calls": []
            }
            
        except Exception as e:
            logger.error(f"生成响应失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_stats(self, tool_name: str, success: bool):
        """
        更新执行统计
        
        Args:
            tool_name: 工具名称
            success: 是否成功
        """
        self._execution_stats["total_calls"] += 1
        
        if success:
            self._execution_stats["successful_calls"] += 1
        else:
            self._execution_stats["failed_calls"] += 1
        
        if tool_name not in self._execution_stats["tool_usage"]:
            self._execution_stats["tool_usage"][tool_name] = 0
        
        self._execution_stats["tool_usage"][tool_name] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return self._execution_stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self._execution_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "tool_usage": {}
        }
