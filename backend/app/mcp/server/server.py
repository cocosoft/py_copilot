"""MCP 服务端主类

提供完整的 MCP 服务端实现。
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.mcp.schemas import MCPServerConfig, MCPModule
from app.mcp.server.transports import BaseTransport, SSETransport, StdioTransport
from app.mcp.server.handlers import ToolsHandler, ResourcesHandler, PromptsHandler
from app.mcp.adapters import ToolAdapter, SkillAdapter, KnowledgeAdapter

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP 服务端主类
    
    管理 MCP 协议服务端的所有组件。
    
    Attributes:
        config: 服务端配置
        transport: 传输层实例
        handlers: 处理器字典
        adapters: 适配器列表
        is_running: 是否正在运行
        initialized: 是否已初始化
    """
    
    def __init__(self, config: MCPServerConfig):
        """初始化 MCP 服务端
        
        Args:
            config: 服务端配置
        """
        self.config = config
        self.transport: Optional[BaseTransport] = None
        self.handlers: Dict[str, Any] = {}
        self.adapters: List[Any] = []
        self.is_running = False
        self.initialized = False
        self._client_info: Optional[Dict[str, Any]] = None
        
        # 初始化组件
        self._init_transport()
        self._init_handlers()
        self._init_adapters()
        
    def _init_transport(self) -> None:
        """初始化传输层"""
        transport_config = {
            'host': self.config.host,
            'port': self.config.port
        }
        
        if self.config.transport.value == 'sse':
            self.transport = SSETransport(transport_config)
        elif self.config.transport.value == 'stdio':
            self.transport = StdioTransport(transport_config)
        else:
            raise ValueError(f"不支持的传输类型: {self.config.transport}")
        
        # 设置消息处理器
        self.transport.set_message_handler(self._handle_message)
        
        logger.info(f"传输层已初始化: {self.config.transport.value}")
    
    def _init_handlers(self) -> None:
        """初始化处理器"""
        # 根据暴露的模块初始化处理器
        exposed_modules = self.config.exposed_modules
        
        if MCPModule.TOOLS in exposed_modules or MCPModule.SKILLS in exposed_modules:
            self.handlers['tools'] = ToolsHandler()
        
        if MCPModule.KNOWLEDGE in exposed_modules:
            self.handlers['resources'] = ResourcesHandler()
        
        if MCPModule.AGENTS in exposed_modules:
            self.handlers['prompts'] = PromptsHandler()
        
        logger.info(f"处理器已初始化: {list(self.handlers.keys())}")
    
    def _init_adapters(self) -> None:
        """初始化适配器"""
        exposed_modules = self.config.exposed_modules
        
        # 工具适配器
        if MCPModule.TOOLS in exposed_modules and 'tools' in self.handlers:
            try:
                tool_adapter = ToolAdapter()
                self.adapters.append(tool_adapter)
                self.handlers['tools'].register_adapter(tool_adapter)
                logger.info("工具适配器已注册")
            except Exception as e:
                logger.error(f"注册工具适配器失败: {e}")
        
        # 技能适配器
        if MCPModule.SKILLS in exposed_modules and 'tools' in self.handlers:
            try:
                skill_adapter = SkillAdapter()
                self.adapters.append(skill_adapter)
                self.handlers['tools'].register_adapter(skill_adapter)
                logger.info("技能适配器已注册")
            except Exception as e:
                logger.error(f"注册技能适配器失败: {e}")
        
        # 知识库适配器
        if MCPModule.KNOWLEDGE in exposed_modules:
            try:
                knowledge_adapter = KnowledgeAdapter()
                self.adapters.append(knowledge_adapter)
                
                if 'tools' in self.handlers:
                    self.handlers['tools'].register_adapter(knowledge_adapter)
                if 'resources' in self.handlers:
                    self.handlers['resources'].register_adapter(knowledge_adapter)
                if 'prompts' in self.handlers:
                    self.handlers['prompts'].register_adapter(knowledge_adapter)
                
                logger.info("知识库适配器已注册")
            except Exception as e:
                logger.error(f"注册知识库适配器失败: {e}")
    
    async def start(self) -> bool:
        """启动 MCP 服务端
        
        Returns:
            是否启动成功
        """
        if self.is_running:
            logger.warning("MCP 服务端已经在运行")
            return True
        
        if not self.config.enabled:
            logger.info("MCP 服务端已禁用，跳过启动")
            return False
        
        try:
            # 启动传输层
            success = await self.transport.start()
            if not success:
                logger.error("传输层启动失败")
                return False
            
            self.is_running = True
            logger.info(f"MCP 服务端已启动: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"MCP 服务端启动失败: {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """停止 MCP 服务端
        
        Returns:
            是否停止成功
        """
        if not self.is_running:
            return True
        
        try:
            # 停止传输层
            if self.transport:
                await self.transport.stop()
            
            self.is_running = False
            self.initialized = False
            
            logger.info(f"MCP 服务端已停止: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"MCP 服务端停止失败: {e}", exc_info=True)
            return False
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """处理接收到的消息
        
        Args:
            message: 接收到的消息
        """
        try:
            method = message.get('method')
            params = message.get('params', {})
            msg_id = message.get('id')
            
            logger.debug(f"处理消息: {method}")
            
            # 处理初始化请求
            if method == 'initialize':
                await self._handle_initialize(msg_id, params)
                return
            
            # 处理已初始化后的请求
            if not self.initialized and method != 'initialize':
                await self._send_error(msg_id, -32002, "Server not initialized")
                return
            
            # 处理通知
            if method == 'notifications/initialized':
                logger.info("客户端已确认初始化")
                return
            
            # 分派到相应的处理器
            result = await self._dispatch_request(method, params)
            
            if result is not None and msg_id is not None:
                # 发送响应
                response = {
                    'jsonrpc': '2.0',
                    'id': msg_id,
                    'result': result
                }
                await self.transport.send_message(response)
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
            msg_id = message.get('id')
            if msg_id is not None:
                await self._send_error(msg_id, -32603, f"Internal error: {str(e)}")
    
    async def _handle_initialize(self, msg_id: Any, params: Dict[str, Any]) -> None:
        """处理初始化请求
        
        Args:
            msg_id: 消息ID
            params: 初始化参数
        """
        try:
            # 保存客户端信息
            self._client_info = params.get('clientInfo', {})
            protocol_version = params.get('protocolVersion', '2024-11-05')
            
            logger.info(f"客户端初始化: {self._client_info}")
            
            # 构建能力描述
            capabilities = {}
            
            if 'tools' in self.handlers:
                capabilities['tools'] = self.handlers['tools'].get_capabilities()
            
            if 'resources' in self.handlers:
                capabilities['resources'] = self.handlers['resources'].get_capabilities()
            
            if 'prompts' in self.handlers:
                capabilities['prompts'] = self.handlers['prompts'].get_capabilities()
            
            # 发送初始化响应
            response = {
                'jsonrpc': '2.0',
                'id': msg_id,
                'result': {
                    'protocolVersion': protocol_version,
                    'capabilities': capabilities,
                    'serverInfo': {
                        'name': 'py-copilot-mcp-server',
                        'version': '1.0.0'
                    }
                }
            }
            
            await self.transport.send_message(response)
            self.initialized = True
            
            logger.info("MCP 服务端初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}", exc_info=True)
            await self._send_error(msg_id, -32603, f"Initialize failed: {str(e)}")
    
    async def _dispatch_request(self, method: str, params: Dict[str, Any]) -> Optional[Any]:
        """分派请求到相应的处理器
        
        Args:
            method: 请求方法
            params: 请求参数
            
        Returns:
            处理结果
        """
        # 查找处理器
        handler = None
        
        if method.startswith('tools/'):
            handler = self.handlers.get('tools')
        elif method.startswith('resources/'):
            handler = self.handlers.get('resources')
        elif method.startswith('prompts/'):
            handler = self.handlers.get('prompts')
        
        if handler:
            return await handler.handle(method, params)
        
        # 未知方法
        logger.warning(f"未知方法: {method}")
        return None
    
    async def _send_error(self, msg_id: Any, code: int, message: str) -> None:
        """发送错误响应
        
        Args:
            msg_id: 消息ID
            code: 错误代码
            message: 错误消息
        """
        response = {
            'jsonrpc': '2.0',
            'id': msg_id,
            'error': {
                'code': code,
                'message': message
            }
        }
        
        await self.transport.send_message(response)
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务端状态
        
        Returns:
            状态信息字典
        """
        return {
            'name': self.config.name,
            'enabled': self.config.enabled,
            'running': self.is_running,
            'initialized': self.initialized,
            'transport': self.config.transport.value,
            'endpoint': f"{self.config.host}:{self.config.port}" if self.config.transport.value == 'sse' else 'stdio',
            'exposed_modules': [m.value for m in self.config.exposed_modules],
            'handlers': list(self.handlers.keys()),
            'adapters': [a.name for a in self.adapters]
        }
