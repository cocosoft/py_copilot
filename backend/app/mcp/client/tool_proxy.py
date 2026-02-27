"""MCP 工具代理

将外部 MCP 工具代理到本地工具注册表。
"""

import logging
from typing import Dict, Any, List, Optional, Callable
import asyncio

from app.mcp.client.connection_manager import connection_manager
from app.mcp.services.config_service import MCPConfigService

logger = logging.getLogger(__name__)


class MCPToolProxy:
    """MCP 工具代理类
    
    将外部 MCP 服务提供的工具代理为本地可调用的工具。
    
    Attributes:
        client_config_id: 客户端配置ID
        tool_name: 工具名称
        original_name: 原始工具名称
        description: 工具描述
        input_schema: 输入参数Schema
    """
    
    def __init__(
        self,
        client_config_id: int,
        tool_name: str,
        original_name: str,
        description: str,
        input_schema: Dict[str, Any]
    ):
        """初始化工具代理
        
        Args:
            client_config_id: 客户端配置ID
            tool_name: 本地工具名称
            original_name: 原始工具名称
            description: 工具描述
            input_schema: 输入参数Schema
        """
        self.client_config_id = client_config_id
        self.tool_name = tool_name
        self.original_name = original_name
        self.description = description
        self.input_schema = input_schema
        
    async def execute(self, **kwargs) -> Any:
        """执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            # 通过连接管理器调用工具
            result = await connection_manager.call_tool(
                self.client_config_id,
                self.original_name,
                kwargs
            )
            
            if result is None:
                return {"error": "工具调用失败"}
            
            # 解析结果
            if "error" in result:
                return {"error": result["error"].get("message", "未知错误")}
            
            response_result = result.get("result", {})
            
            # 提取内容
            content = response_result.get("content", [])
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                return {"result": text_content}
            
            return {"result": response_result}
            
        except Exception as e:
            logger.error(f"工具代理执行失败 {self.tool_name}: {e}", exc_info=True)
            return {"error": str(e)}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            工具信息字典
        """
        return {
            "name": self.tool_name,
            "original_name": self.original_name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "client_config_id": self.client_config_id
        }


class MCPToolProxyRegistry:
    """MCP 工具代理注册表
    
    管理所有外部 MCP 工具代理。
    
    Attributes:
        proxies: 工具代理字典
    """
    
    def __init__(self):
        """初始化注册表"""
        self.proxies: Dict[str, MCPToolProxy] = {}
        
    def register_proxy(self, proxy: MCPToolProxy) -> None:
        """注册工具代理
        
        Args:
            proxy: 工具代理实例
        """
        self.proxies[proxy.tool_name] = proxy
        logger.info(f"注册 MCP 工具代理: {proxy.tool_name}")
        
    def unregister_proxy(self, tool_name: str) -> None:
        """注销工具代理
        
        Args:
            tool_name: 工具名称
        """
        if tool_name in self.proxies:
            del self.proxies[tool_name]
            logger.info(f"注销 MCP 工具代理: {tool_name}")
    
    def unregister_client_proxies(self, client_config_id: int) -> None:
        """注销指定客户端的所有工具代理
        
        Args:
            client_config_id: 客户端配置ID
        """
        to_remove = [
            name for name, proxy in self.proxies.items()
            if proxy.client_config_id == client_config_id
        ]
        
        for name in to_remove:
            self.unregister_proxy(name)
    
    def get_proxy(self, tool_name: str) -> Optional[MCPToolProxy]:
        """获取工具代理
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具代理实例
        """
        return self.proxies.get(tool_name)
    
    def get_all_proxies(self) -> Dict[str, MCPToolProxy]:
        """获取所有工具代理
        
        Returns:
            工具代理字典
        """
        return self.proxies.copy()
    
    def get_client_proxies(self, client_config_id: int) -> List[MCPToolProxy]:
        """获取指定客户端的所有工具代理
        
        Args:
            client_config_id: 客户端配置ID
            
        Returns:
            工具代理列表
        """
        return [
            proxy for proxy in self.proxies.values()
            if proxy.client_config_id == client_config_id
        ]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        proxy = self.proxies.get(tool_name)
        if not proxy:
            raise ValueError(f"工具不存在: {tool_name}")
        
        return await proxy.execute(**kwargs)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具
        
        Returns:
            工具信息列表
        """
        return [proxy.to_dict() for proxy in self.proxies.values()]


# 全局工具代理注册表
tool_proxy_registry = MCPToolProxyRegistry()


async def sync_client_tools(
    client_config_id: int,
    db: Any
) -> int:
    """同步客户端工具
    
    从连接的 MCP 客户端获取工具列表，并创建工具代理。
    
    Args:
        client_config_id: 客户端配置ID
        db: 数据库会话
        
    Returns:
        同步的工具数量
    """
    try:
        # 获取客户端
        client = connection_manager.get_client(client_config_id)
        if not client:
            logger.error(f"客户端 {client_config_id} 不存在")
            return 0
        
        if not client.is_connected:
            logger.error(f"客户端 {client_config_id} 未连接")
            return 0
        
        # 获取工具列表
        tools = client.tools
        
        # 注销旧代理
        tool_proxy_registry.unregister_client_proxies(client_config_id)
        
        # 获取配置服务
        service = MCPConfigService(db)
        config = service.get_client_config(1, client_config_id)  # 简化处理
        
        if not config:
            logger.error(f"配置 {client_config_id} 不存在")
            return 0
        
        # 获取白名单和黑名单
        whitelist = config.tool_whitelist or []
        blacklist = config.tool_blacklist or []
        
        # 创建新代理
        count = 0
        tool_mappings = []
        
        for tool in tools:
            original_name = tool.get('name')
            
            # 检查黑名单
            if original_name in blacklist:
                continue
            
            # 检查白名单（如果设置了白名单）
            if whitelist and original_name not in whitelist:
                continue
            
            # 生成本地工具名
            local_name = f"mcp_{config.name}_{original_name}"
            
            # 创建工具代理
            proxy = MCPToolProxy(
                client_config_id=client_config_id,
                tool_name=local_name,
                original_name=original_name,
                description=tool.get('description', ''),
                input_schema=tool.get('inputSchema', {})
            )
            
            # 注册代理
            tool_proxy_registry.register_proxy(proxy)
            
            # 保存映射信息
            tool_mappings.append({
                'name': original_name,
                'local_name': local_name,
                'description': tool.get('description', ''),
                'inputSchema': tool.get('inputSchema', {})
            })
            
            count += 1
        
        # 保存到数据库
        service.save_tool_mappings(client_config_id, tool_mappings)
        
        logger.info(f"已同步 {count} 个工具从客户端 {client_config_id}")
        return count
        
    except Exception as e:
        logger.error(f"同步客户端工具失败: {e}", exc_info=True)
        return 0


async def execute_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any]
) -> Any:
    """执行 MCP 工具
    
    供外部调用的工具执行接口。
    
    Args:
        tool_name: 工具名称
        arguments: 工具参数
        
    Returns:
        工具执行结果
    """
    try:
        return await tool_proxy_registry.execute_tool(tool_name, **arguments)
    except Exception as e:
        logger.error(f"执行 MCP 工具失败: {e}", exc_info=True)
        return {"error": str(e)}


def get_mcp_tools() -> List[Dict[str, Any]]:
    """获取所有 MCP 工具
    
    Returns:
        工具信息列表
    """
    return tool_proxy_registry.list_tools()
