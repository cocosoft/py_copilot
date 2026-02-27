"""MCP Resources 处理器

处理 MCP 协议中的资源相关请求。
"""

import logging
from typing import Dict, Any, List, Optional

from .base import BaseHandler

logger = logging.getLogger(__name__)


class ResourcesHandler(BaseHandler):
    """资源处理器
    
    处理 resources/list、resources/read 等请求。
    
    Attributes:
        resources: 资源注册表
        adapters: 资源适配器列表
    """
    
    def __init__(self):
        """初始化资源处理器"""
        super().__init__("resources")
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.adapters: List[Any] = []
        self.capabilities = {
            "subscribe": True,
            "listChanged": True
        }
        
    def _get_supported_methods(self) -> List[str]:
        """获取支持的方法列表
        
        Returns:
            方法名列表
        """
        return [
            "resources/list",
            "resources/read",
            "resources/subscribe",
            "resources/unsubscribe"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取处理器能力
        
        Returns:
            能力描述字典
        """
        return self.capabilities
    
    def register_adapter(self, adapter: Any) -> None:
        """注册资源适配器
        
        Args:
            adapter: 资源适配器实例
        """
        self.adapters.append(adapter)
        logger.info(f"注册资源适配器: {adapter.__class__.__name__}")
    
    async def refresh_resources(self) -> None:
        """刷新资源列表
        
        从所有适配器收集资源信息。
        """
        self.resources = {}
        
        for adapter in self.adapters:
            try:
                adapter_resources = await adapter.get_resources()
                for resource in adapter_resources:
                    uri = resource.get('uri')
                    if uri:
                        self.resources[uri] = {
                            **resource,
                            '_adapter': adapter
                        }
            except Exception as e:
                logger.error(f"从适配器获取资源失败: {e}", exc_info=True)
        
        logger.info(f"资源列表已刷新，共 {len(self.resources)} 个资源")
    
    async def handle(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源请求
        
        Args:
            method: 请求方法名
            params: 请求参数
            
        Returns:
            处理结果
        """
        try:
            if method == "resources/list":
                return await self._handle_list(params)
            elif method == "resources/read":
                return await self._handle_read(params)
            elif method == "resources/subscribe":
                return await self._handle_subscribe(params)
            elif method == "resources/unsubscribe":
                return await self._handle_unsubscribe(params)
            else:
                return self._create_error(
                    -32601,
                    f"Method not found: {method}"
                )
        except Exception as e:
            logger.error(f"处理资源请求失败: {e}", exc_info=True)
            return self._create_error(
                -32603,
                f"Internal error: {str(e)}"
            )
    
    async def _handle_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 resources/list 请求
        
        返回所有可用资源列表。
        
        Args:
            params: 请求参数
            
        Returns:
            资源列表
        """
        await self.refresh_resources()
        
        resources_list = []
        for uri, resource in self.resources.items():
            resources_list.append({
                "uri": uri,
                "name": resource.get("name", ""),
                "description": resource.get("description", ""),
                "mimeType": resource.get("mimeType", "text/plain")
            })
        
        return {
            "resources": resources_list
        }
    
    async def _handle_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 resources/read 请求
        
        读取指定资源内容。
        
        Args:
            params: 请求参数，包含 uri
            
        Returns:
            资源内容
        """
        uri = params.get("uri")
        
        if not uri:
            return self._create_error(
                -32602,
                "Invalid params: missing 'uri'"
            )
        
        resource = self.resources.get(uri)
        if not resource:
            return self._create_error(
                -32602,
                f"Resource not found: {uri}"
            )
        
        adapter = resource.get('_adapter')
        if not adapter:
            return self._create_error(
                -32603,
                f"Resource adapter not found: {uri}"
            )
        
        try:
            content = await adapter.read_resource(uri)
            
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": resource.get("mimeType", "text/plain"),
                        "text": content if isinstance(content, str) else str(content)
                    }
                ]
            }
        except Exception as e:
            logger.error(f"读取资源失败 {uri}: {e}", exc_info=True)
            return self._create_error(
                -32603,
                f"Failed to read resource: {str(e)}"
            )
    
    async def _handle_subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 resources/subscribe 请求
        
        订阅资源变更通知。
        
        Args:
            params: 请求参数，包含 uri
            
        Returns:
            订阅结果
        """
        uri = params.get("uri")
        
        if not uri:
            return self._create_error(
                -32602,
                "Invalid params: missing 'uri'"
            )
        
        # TODO: 实现订阅逻辑
        logger.info(f"资源订阅请求: {uri}")
        
        return {
            "success": True
        }
    
    async def _handle_unsubscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 resources/unsubscribe 请求
        
        取消资源变更订阅。
        
        Args:
            params: 请求参数，包含 uri
            
        Returns:
            取消订阅结果
        """
        uri = params.get("uri")
        
        if not uri:
            return self._create_error(
                -32602,
                "Invalid params: missing 'uri'"
            )
        
        # TODO: 实现取消订阅逻辑
        logger.info(f"资源取消订阅请求: {uri}")
        
        return {
            "success": True
        }
