"""工具注册中心"""
from typing import Dict, List, Optional, Type, Any
from app.modules.function_calling.base_tool import BaseTool, ToolMetadata
from app.modules.function_calling.tool_integration_adapter import ToolIntegrationAdapter
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册中心，管理所有可用的工具"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化工具注册中心"""
        if self._initialized:
            return
        
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._settings: Dict[str, Any] = {
            "enable_auto_execution": True,
            "show_tool_calls": True,
            "enable_tool_logging": True,
            "execution_timeout": 30,
            "max_concurrent_calls": 5
        }
        self._initialized = True
        logger.info("工具注册中心初始化完成")
    
    def register(self, tool: BaseTool) -> bool:
        """
        注册工具
        
        Args:
            tool: 工具实例
            
        Returns:
            是否注册成功
        """
        try:
            metadata = tool.get_metadata()
            
            # 检查工具名称是否已存在
            if metadata.name in self._tools:
                logger.warning(f"工具 '{metadata.name}' 已存在，将更新")
            
            # 注册工具
            self._tools[metadata.name] = tool
            
            # 更新分类索引
            category = metadata.category
            if category not in self._categories:
                self._categories[category] = []
            
            if metadata.name not in self._categories[category]:
                self._categories[category].append(metadata.name)
            
            logger.info(f"工具 '{metadata.name}' 注册成功，分类: {category}")
            return True
            
        except Exception as e:
            logger.error(f"注册工具失败: {str(e)}")
            return False
    
    def register_from_adapter(self, adapter: ToolIntegrationAdapter) -> int:
        """
        从适配器注册所有工具
        
        Args:
            adapter: 工具集成适配器
            
        Returns:
            成功注册的工具数量
        """
        adapted_tools = adapter.adapt_all_tools()
        count = 0
        
        for tool in adapted_tools:
            if self.register(tool):
                count += 1
        
        logger.info(f"从适配器注册了 {count} 个工具")
        return count
    
    def unregister(self, tool_name: str) -> bool:
        """
        注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否注销成功
        """
        if tool_name not in self._tools:
            logger.warning(f"工具 '{tool_name}' 不存在")
            return False
        
        tool = self._tools[tool_name]
        category = tool.get_metadata().category
        
        # 从分类索引中移除
        if category in self._categories and tool_name in self._categories[category]:
            self._categories[category].remove(tool_name)
            if not self._categories[category]:
                del self._categories[category]
        
        # 移除工具
        del self._tools[tool_name]
        
        logger.info(f"工具 '{tool_name}' 注销成功")
        return True
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例，不存在则返回None
        """
        return self._tools.get(tool_name)
    
    def list_tools(self, category: Optional[str] = None) -> List[BaseTool]:
        """
        列出工具
        
        Args:
            category: 分类名称，None表示列出所有工具
            
        Returns:
            工具列表
        """
        if category:
            if category not in self._categories:
                return []
            return [
                self._tools[name]
                for name in self._categories[category]
                if name in self._tools
            ]
        
        return list(self._tools.values())
    
    def get_categories(self) -> Dict[str, List[str]]:
        """
        获取所有分类
        
        Returns:
            分类字典，键为分类名称，值为该分类下的工具名称列表
        """
        return self._categories.copy()
    
    def get_tool_definitions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取工具定义列表（用于Function Calling）
        
        Args:
            category: 分类名称，None表示获取所有工具定义
            
        Returns:
            工具定义列表
        """
        tools = self.list_tools(category)
        return [tool.get_tool_definition() for tool in tools]
    
    def search_tools(self, keyword: str) -> List[BaseTool]:
        """
        搜索工具
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的工具列表
        """
        keyword = keyword.lower()
        results = []
        
        for tool in self._tools.values():
            metadata = tool.get_metadata()
            
            # 在名称、描述、标签中搜索
            if (
                keyword in metadata.name.lower() or
                keyword in metadata.display_name.lower() or
                keyword in metadata.description.lower() or
                any(keyword in tag.lower() for tag in metadata.tags)
            ):
                results.append(tool)
        
        return results
    
    def get_tool_count(self) -> int:
        """获取工具总数"""
        return len(self._tools)
    
    def clear(self):
        """清空所有工具"""
        self._tools.clear()
        self._categories.clear()
        logger.info("工具注册中心已清空")
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        获取所有工具
        
        Returns:
            工具字典
        """
        return self._tools.copy()
    
    def get_tools_by_category(self, category: str) -> Dict[str, BaseTool]:
        """
        根据分类获取工具
        
        Args:
            category: 分类名称
            
        Returns:
            工具字典
        """
        if category not in self._categories:
            return {}
        
        return {
            name: self._tools[name]
            for name in self._categories[category]
            if name in self._tools
        }
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Args:
            limit: 返回的历史记录数量
            
        Returns:
            执行历史列表
        """
        return self._execution_history[-limit:]
    
    def add_execution_history(self, tool_name: str, display_name: str, execution_time: float, success: bool):
        """
        添加执行历史记录
        
        Args:
            tool_name: 工具名称
            display_name: 工具显示名称
            execution_time: 执行时间（秒）
            success: 是否成功
        """
        from datetime import datetime
        
        history_item = {
            "tool_name": tool_name,
            "display_name": display_name,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "success": success
        }
        
        self._execution_history.append(history_item)
        
        # 限制历史记录数量
        max_history = 1000
        if len(self._execution_history) > max_history:
            self._execution_history = self._execution_history[-max_history:]
    
    def clear_execution_history(self):
        """清空执行历史"""
        self._execution_history.clear()
        logger.info("执行历史已清空")
    
    def get_settings(self) -> Dict[str, Any]:
        """
        获取工具设置
        
        Returns:
            工具设置字典
        """
        return self._settings.copy()
    
    def update_settings(self, settings: Dict[str, Any]):
        """
        更新工具设置
        
        Args:
            settings: 工具设置字典
        """
        self._settings.update(settings)
        logger.info(f"工具设置已更新: {settings}")
    
    def update_tool_status(self, tool_name: str, is_active: bool) -> bool:
        """
        更新工具激活状态
        
        Args:
            tool_name: 工具名称
            is_active: 是否激活
            
        Returns:
            是否更新成功
        """
        tool = self.get_tool(tool_name)
        if not tool:
            logger.warning(f"工具 '{tool_name}' 不存在")
            return False
        
        metadata = tool.get_metadata()
        metadata.is_active = is_active
        logger.info(f"工具 '{tool_name}' 状态已更新为 {'激活' if is_active else '禁用'}")
        return True
