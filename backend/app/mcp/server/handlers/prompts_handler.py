"""MCP Prompts 处理器

处理 MCP 协议中的提示模板相关请求。
"""

import logging
from typing import Dict, Any, List, Optional

from .base import BaseHandler

logger = logging.getLogger(__name__)


class PromptsHandler(BaseHandler):
    """提示模板处理器
    
    处理 prompts/list 和 prompts/get 请求。
    
    Attributes:
        prompts: 提示模板注册表
        adapters: 提示模板适配器列表
    """
    
    def __init__(self):
        """初始化提示模板处理器"""
        super().__init__("prompts")
        self.prompts: Dict[str, Dict[str, Any]] = {}
        self.adapters: List[Any] = []
        self.capabilities = {
            "listChanged": True
        }
        
    def _get_supported_methods(self) -> List[str]:
        """获取支持的方法列表
        
        Returns:
            方法名列表
        """
        return [
            "prompts/list",
            "prompts/get"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取处理器能力
        
        Returns:
            能力描述字典
        """
        return self.capabilities
    
    def register_adapter(self, adapter: Any) -> None:
        """注册提示模板适配器
        
        Args:
            adapter: 提示模板适配器实例
        """
        self.adapters.append(adapter)
        logger.info(f"注册提示模板适配器: {adapter.__class__.__name__}")
    
    async def refresh_prompts(self) -> None:
        """刷新提示模板列表
        
        从所有适配器收集提示模板信息。
        """
        self.prompts = {}
        
        for adapter in self.adapters:
            try:
                adapter_prompts = await adapter.get_prompts()
                for prompt in adapter_prompts:
                    name = prompt.get('name')
                    if name:
                        self.prompts[name] = {
                            **prompt,
                            '_adapter': adapter
                        }
            except Exception as e:
                logger.error(f"从适配器获取提示模板失败: {e}", exc_info=True)
        
        logger.info(f"提示模板列表已刷新，共 {len(self.prompts)} 个模板")
    
    async def handle(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理提示模板请求
        
        Args:
            method: 请求方法名
            params: 请求参数
            
        Returns:
            处理结果
        """
        try:
            if method == "prompts/list":
                return await self._handle_list(params)
            elif method == "prompts/get":
                return await self._handle_get(params)
            else:
                return self._create_error(
                    -32601,
                    f"Method not found: {method}"
                )
        except Exception as e:
            logger.error(f"处理提示模板请求失败: {e}", exc_info=True)
            return self._create_error(
                -32603,
                f"Internal error: {str(e)}"
            )
    
    async def _handle_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 prompts/list 请求
        
        返回所有可用提示模板列表。
        
        Args:
            params: 请求参数
            
        Returns:
            提示模板列表
        """
        await self.refresh_prompts()
        
        prompts_list = []
        for name, prompt in self.prompts.items():
            prompts_list.append({
                "name": name,
                "description": prompt.get("description", ""),
                "arguments": prompt.get("arguments", [])
            })
        
        return {
            "prompts": prompts_list
        }
    
    async def _handle_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 prompts/get 请求
        
        获取指定提示模板内容。
        
        Args:
            params: 请求参数，包含 name 和 arguments
            
        Returns:
            提示模板内容
        """
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            return self._create_error(
                -32602,
                "Invalid params: missing 'name'"
            )
        
        prompt = self.prompts.get(name)
        if not prompt:
            return self._create_error(
                -32602,
                f"Prompt not found: {name}"
            )
        
        adapter = prompt.get('_adapter')
        if not adapter:
            return self._create_error(
                -32603,
                f"Prompt adapter not found: {name}"
            )
        
        try:
            # 获取提示模板内容
            content = await adapter.get_prompt_content(name, arguments)
            
            return {
                "description": prompt.get("description", ""),
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": content
                        }
                    }
                ]
            }
        except Exception as e:
            logger.error(f"获取提示模板失败 {name}: {e}", exc_info=True)
            return self._create_error(
                -32603,
                f"Failed to get prompt: {str(e)}"
            )
