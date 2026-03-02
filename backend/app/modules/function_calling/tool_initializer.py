"""工具初始化模块"""
from app.modules.function_calling.tool_registry import ToolRegistry
from app.modules.function_calling.tool_integration_adapter import ToolIntegrationAdapter
from app.modules.function_calling.tools.web_search_tool import WebSearchTool
from app.modules.function_calling.tools.knowledge_search_tool import KnowledgeSearchTool
from app.modules.function_calling.tools.memory_tool import MemoryTool
from app.modules.function_calling.tools.text_processing_tool import TextProcessingTool
from app.modules.function_calling.tools.data_processing_tool import DataProcessingTool
from app.modules.function_calling.tools.calculator_tool import CalculatorTool
from app.modules.function_calling.tools.mcp_tool import mcp_tool_manager
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


async def initialize_tools():
    """
    初始化所有工具
    
    此函数会在系统启动时调用，自动注册所有工具
    """
    try:
        logger.info("开始初始化Function Calling工具...")
        
        # 获取工具注册中心实例
        registry = ToolRegistry()
        
        # 注册内置工具
        await _register_builtin_tools(registry)
        
        # 适配并注册现有工具
        await _register_legacy_tools(registry)
        
        # 注册 MCP 工具
        await _register_mcp_tools(registry)
        
        # 输出注册统计
        tool_count = registry.get_tool_count()
        categories = registry.get_categories()
        
        logger.info(f"工具初始化完成！共注册 {tool_count} 个工具")
        logger.info(f"工具分类: {', '.join(categories.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"工具初始化失败: {str(e)}", exc_info=True)
        return False


async def _register_builtin_tools(registry: ToolRegistry):
    """
    注册内置工具
    
    Args:
        registry: 工具注册中心
    """
    # 延迟导入 FileReaderTool 避免循环导入
    from app.tools.official.file_reader import FileReaderTool
    
    builtin_tools = [
        WebSearchTool(),
        KnowledgeSearchTool(),
        MemoryTool(),
        TextProcessingTool(),
        DataProcessingTool(),
        CalculatorTool(),
        FileReaderTool()
    ]
    
    for tool in builtin_tools:
        try:
            if registry.register(tool):
                metadata = tool.get_metadata()
                logger.info(f"注册内置工具: {metadata.display_name} ({metadata.name})")
        except Exception as e:
            logger.error(f"注册内置工具失败: {tool.get_metadata().name}, 错误: {str(e)}")


async def _register_legacy_tools(registry: ToolRegistry):
    """
    适配并注册现有工具
    
    Args:
        registry: 工具注册中心
    """
    try:
        # 创建工具适配器
        adapter = ToolIntegrationAdapter()
        
        # 适配并注册所有现有工具
        count = registry.register_from_adapter(adapter)
        
        logger.info(f"适配并注册了 {count} 个现有工具")
        
    except Exception as e:
        logger.error(f"适配现有工具失败: {str(e)}", exc_info=True)


async def _register_mcp_tools(registry: ToolRegistry):
    """
    注册 MCP 工具
    
    Args:
        registry: 工具注册中心
    """
    try:
        # 刷新 MCP 工具列表
        count = mcp_tool_manager.refresh_tools()
        
        # 注册所有 MCP 工具
        for tool_name, tool in mcp_tool_manager.get_all_tools().items():
            try:
                if registry.register(tool):
                    metadata = tool.get_metadata()
                    logger.info(f"注册 MCP 工具: {metadata.display_name} ({metadata.name})")
            except Exception as e:
                logger.error(f"注册 MCP 工具失败: {tool_name}, 错误: {str(e)}")
        
        logger.info(f"注册了 {count} 个 MCP 工具")
        
    except Exception as e:
        logger.error(f"注册 MCP 工具失败: {str(e)}", exc_info=True)


def refresh_mcp_tools() -> int:
    """
    刷新 MCP 工具列表
    
    在 MCP 客户端连接后调用，同步最新的 MCP 工具。
    
    Returns:
        新增的工具数量
    """
    try:
        registry = ToolRegistry()
        
        # 刷新 MCP 工具
        count = mcp_tool_manager.refresh_tools()
        
        # 注册新工具
        for tool_name, tool in mcp_tool_manager.get_all_tools().items():
            if tool_name not in registry.get_all_tools():
                registry.register(tool)
                logger.info(f"新增 MCP 工具: {tool_name}")
        
        logger.info(f"MCP 工具刷新完成，新增 {count} 个工具")
        return count
        
    except Exception as e:
        logger.error(f"刷新 MCP 工具失败: {str(e)}", exc_info=True)
        return 0


def get_tool_registry() -> ToolRegistry:
    """
    获取工具注册中心实例
    
    Returns:
        工具注册中心实例
    """
    return ToolRegistry()
