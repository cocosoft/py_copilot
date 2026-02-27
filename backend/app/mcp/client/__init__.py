"""MCP 客户端模块

提供 MCP 协议客户端功能，用于连接外部 MCP 服务。
"""

from .client import MCPClient
from .connection_manager import MCPConnectionManager
from .tool_proxy import MCPToolProxy

__all__ = [
    'MCPClient',
    'MCPConnectionManager',
    'MCPToolProxy'
]
