"""MCP 客户端实现

提供 MCP 协议客户端功能。
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from app.mcp.schemas import MCPClientConfig, ConnectionStatus

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP 客户端类
    
    管理与外部 MCP 服务的连接和通信。
    
    Attributes:
        config: 客户端配置
        status: 连接状态
        tools: 可用工具列表
        message_handlers: 消息处理器列表
        pending_requests: 待处理的请求
    """
    
    def __init__(self, config: MCPClientConfig):
        """初始化 MCP 客户端
        
        Args:
            config: 客户端配置
        """
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.error_message: Optional[str] = None
        
        # 连接相关
        self._transport = None
        self._reader = None
        self._writer = None
        self._process = None
        
        # 协议相关
        self._initialized = False
        self._server_capabilities: Optional[Dict[str, Any]] = None
        self._tools: List[Dict[str, Any]] = []
        self._resources: List[Dict[str, Any]] = []
        self._prompts: List[Dict[str, Any]] = []
        
        # 请求管理
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._message_handlers: List[Callable[[Dict[str, Any]], None]] = []
        self._request_counter = 0
        
        # 任务
        self._read_task: Optional[asyncio.Task] = None
        
    @property
    def tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return self._tools.copy()
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.status == ConnectionStatus.CONNECTED and self._initialized
    
    async def connect(self) -> bool:
        """连接到 MCP 服务
        
        Returns:
            是否连接成功
        """
        if self.status == ConnectionStatus.CONNECTED:
            return True
        
        if not self.config.enabled:
            logger.info(f"客户端 {self.config.name} 已禁用")
            return False
        
        try:
            self.status = ConnectionStatus.CONNECTING
            self.error_message = None
            
            # 根据传输类型建立连接
            if self.config.transport.value == 'sse':
                success = await self._connect_sse()
            elif self.config.transport.value == 'stdio':
                success = await self._connect_stdio()
            else:
                raise ValueError(f"不支持的传输类型: {self.config.transport}")
            
            if not success:
                return False
            
            # 执行初始化握手
            if not await self._initialize():
                await self.disconnect()
                return False
            
            # 获取工具列表
            await self._fetch_tools()
            
            self.status = ConnectionStatus.CONNECTED
            logger.info(f"MCP 客户端已连接: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"连接 MCP 服务失败: {e}", exc_info=True)
            self.status = ConnectionStatus.ERROR
            self.error_message = str(e)
            return False
    
    async def disconnect(self) -> bool:
        """断开连接
        
        Returns:
            是否断开成功
        """
        try:
            # 取消读取任务
            if self._read_task and not self._read_task.done():
                self._read_task.cancel()
                try:
                    await self._read_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭连接
            if self.config.transport.value == 'sse':
                await self._disconnect_sse()
            elif self.config.transport.value == 'stdio':
                await self._disconnect_stdio()
            
            # 清理状态
            self._initialized = False
            self._server_capabilities = None
            self._tools = []
            self._pending_requests.clear()
            
            self.status = ConnectionStatus.DISCONNECTED
            logger.info(f"MCP 客户端已断开: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}", exc_info=True)
            return False
    
    async def _connect_sse(self) -> bool:
        """建立 SSE 连接
        
        Returns:
            是否连接成功
        """
        try:
            import aiohttp
            
            url = self.config.connection_url
            if not url:
                raise ValueError("SSE 连接需要 connection_url")
            
            # 创建 aiohttp 会话
            self._transport = aiohttp.ClientSession()
            
            # 建立 SSE 连接
            # 注意：这里简化处理，实际实现需要处理 SSE 协议
            logger.info(f"SSE 连接已建立: {url}")
            return True
            
        except Exception as e:
            logger.error(f"SSE 连接失败: {e}")
            return False
    
    async def _disconnect_sse(self) -> None:
        """断开 SSE 连接"""
        if self._transport:
            await self._transport.close()
            self._transport = None
    
    async def _connect_stdio(self) -> bool:
        """建立 Stdio 连接
        
        Returns:
            是否连接成功
        """
        try:
            import asyncio.subprocess
            
            command = self.config.command
            if not command:
                raise ValueError("Stdio 连接需要 command")
            
            # 解析命令
            args = command.split()
            
            # 启动子进程
            self._process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 启动读取循环
            self._read_task = asyncio.create_task(self._stdio_read_loop())
            
            logger.info(f"Stdio 连接已建立: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Stdio 连接失败: {e}")
            return False
    
    async def _disconnect_stdio(self) -> None:
        """断开 Stdio 连接"""
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            self._process = None
    
    async def _stdio_read_loop(self) -> None:
        """Stdio 读取循环"""
        try:
            while True:
                if not self._process or self._process.stdout.at_eof():
                    break
                
                # 读取一行
                line = await self._process.stdout.readline()
                if not line:
                    break
                
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                
                # 解析消息
                try:
                    message = json.loads(line)
                    await self._handle_message(message)
                except json.JSONDecodeError:
                    logger.error(f"无效的 JSON: {line}")
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"读取循环错误: {e}")
    
    async def _initialize(self) -> bool:
        """执行初始化握手
        
        Returns:
            是否初始化成功
        """
        try:
            # 发送初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        }
                    },
                    "clientInfo": {
                        "name": "py-copilot-mcp-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_request(init_request)
            
            if "error" in response:
                logger.error(f"初始化失败: {response['error']}")
                return False
            
            result = response.get("result", {})
            self._server_capabilities = result.get("capabilities", {})
            
            # 发送初始化确认通知
            await self._send_notification("notifications/initialized", {})
            
            self._initialized = True
            logger.info("MCP 客户端初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}", exc_info=True)
            return False
    
    async def _fetch_tools(self) -> None:
        """获取工具列表"""
        try:
            if not self._server_capabilities or "tools" not in self._server_capabilities:
                return
            
            request = {
                "jsonrpc": "2.0",
                "id": self._get_next_request_id(),
                "method": "tools/list",
                "params": {}
            }
            
            response = await self._send_request(request)
            
            if "error" not in response:
                result = response.get("result", {})
                self._tools = result.get("tools", [])
                logger.info(f"获取到 {len(self._tools)} 个工具")
                
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具调用结果
        """
        if not self.is_connected:
            raise RuntimeError("客户端未连接")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        return await self._send_request(request)
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求并等待响应
        
        Args:
            request: 请求数据
            
        Returns:
            响应数据
        """
        request_id = str(request.get("id"))
        
        # 创建 Future 等待响应
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # 发送消息
            await self._send_message(request)
            
            # 等待响应（设置超时）
            response = await asyncio.wait_for(future, timeout=30.0)
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {request_id}")
            return {"error": {"code": -32000, "message": "Request timeout"}}
        finally:
            self._pending_requests.pop(request_id, None)
    
    async def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """发送通知（无需响应）
        
        Args:
            method: 通知方法
            params: 通知参数
        """
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        await self._send_message(notification)
    
    async def _send_message(self, message: Dict[str, Any]) -> None:
        """发送消息
        
        Args:
            message: 消息数据
        """
        message_str = json.dumps(message)
        
        if self.config.transport.value == 'stdio':
            if self._process and self._process.stdin:
                self._process.stdin.write((message_str + '\n').encode())
                await self._process.stdin.drain()
        elif self.config.transport.value == 'sse':
            # SSE 发送逻辑
            pass
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """处理接收到的消息
        
        Args:
            message: 接收到的消息
        """
        # 检查是否是响应
        msg_id = message.get("id")
        if msg_id is not None:
            request_id = str(msg_id)
            future = self._pending_requests.get(request_id)
            if future and not future.done():
                future.set_result(message)
        
        # 检查是否是通知
        if "method" in message and "id" not in message:
            await self._handle_notification(message)
        
        # 调用外部处理器
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"消息处理器错误: {e}")
    
    async def _handle_notification(self, message: Dict[str, Any]) -> None:
        """处理通知消息
        
        Args:
            message: 通知消息
        """
        method = message.get("method")
        params = message.get("params", {})
        
        if method == "notifications/tools/list_changed":
            # 工具列表变更，重新获取
            await self._fetch_tools()
    
    def _get_next_request_id(self) -> int:
        """获取下一个请求ID
        
        Returns:
            请求ID
        """
        self._request_counter += 1
        return self._request_counter
    
    def add_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """添加消息处理器
        
        Args:
            handler: 消息处理函数
        """
        self._message_handlers.append(handler)
    
    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态
        
        Returns:
            状态信息字典
        """
        return {
            "id": self.config.id,
            "name": self.config.name,
            "status": self.status.value,
            "error_message": self.error_message,
            "initialized": self._initialized,
            "tools_count": len(self._tools),
            "capabilities": self._server_capabilities
        }
