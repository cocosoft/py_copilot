"""
工具模块

包含所有工具的实现
"""

from app.modules.function_calling.tools.web_search_tool_new import WebSearchTool
from app.modules.function_calling.tools.knowledge_search_tool_new import KnowledgeSearchTool
from app.modules.function_calling.tools.memory_tool_new import MemoryTool
from app.modules.function_calling.tools.file_operation_tool_new import FileOperationTool
from app.modules.function_calling.tools.text_processing_tool_new import TextProcessingTool
from app.modules.function_calling.tools.image_processing_tool_new import ImageProcessingTool
from app.modules.function_calling.tools.calculator_tool_new import CalculatorTool
from app.modules.function_calling.tools.data_processing_tool_new import DataProcessingTool
from app.modules.function_calling.tools.code_execution_tool_new import CodeExecutionTool
from app.modules.function_calling.tools.api_call_tool_new import APICallTool
from app.modules.function_calling.tools.datetime_tool_new import DateTimeTool
from app.modules.function_calling.tools.random_generator_tool_new import RandomGeneratorTool

__all__ = [
    "WebSearchTool",
    "KnowledgeSearchTool",
    "MemoryTool",
    "FileOperationTool",
    "TextProcessingTool",
    "ImageProcessingTool",
    "CalculatorTool",
    "DataProcessingTool",
    "CodeExecutionTool",
    "APICallTool",
    "DateTimeTool",
    "RandomGeneratorTool"
]


def get_all_tools():
    """
    获取所有工具实例
    
    Returns:
        List[BaseTool]: 所有工具实例列表
    """
    return [
        WebSearchTool(),
        KnowledgeSearchTool(),
        MemoryTool(),
        FileOperationTool(),
        TextProcessingTool(),
        ImageProcessingTool(),
        CalculatorTool(),
        DataProcessingTool(),
        CodeExecutionTool(),
        APICallTool(),
        DateTimeTool(),
        RandomGeneratorTool()
    ]


def initialize_tools():
    """
    初始化并注册所有工具
    
    Returns:
        ToolManager: 配置好的工具管理器
    """
    from app.modules.function_calling.tool_manager import tool_manager
    
    tools = get_all_tools()
    tool_manager.register_tools(tools)
    
    return tool_manager
