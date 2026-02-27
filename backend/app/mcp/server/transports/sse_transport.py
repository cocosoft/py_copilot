"""MCP SSE 传输层实现

基于 Server-Sent Events 的 MCP 传输层实现。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from fastapi import Request
from sse_starlette.sse import EventSourceResponse

from .base import BaseTransport

logger = logging.getLogger(__name__)


class SSETransport(BaseTransport):
    """SSE 传输层实现
    
    使用 Server-Sent Events 协议实现 MCP 通信。
    
    Attributes:
        host: 监听地址
        port: 监听端口
        clients: 连接的客户端集合
        message_queue: 消息队列
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化 SSE 传输层
        
        Args:
            config: 配置字典，包含 host, port 等
        """
        super().__init__(config)
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('port', 8008)
        self.clients: Set[asyncio.Queue] = set()
        self.message_queue: Optional[asyncio.Queue] = None
        self.server = None
        
    async def start(self) -> bool:
        """启动 SSE 传输层
        
        Returns:
            是否启动成功
        """
        try:
            self.message_queue = asyncio.Queue()
            self.is_running = True
            logger.info(f"SSE 传输层已启动: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"SSE 传输层启动失败: {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """停止 SSE 传输层
        
        Returns:
            是否停止成功
        """
        try:
            self.is_running = False
            
            # 关闭所有客户端连接
            for client_queue in list(self.clients):
                try:
                    await client_queue.put(None)  # 发送关闭信号
                except Exception:
                    pass
            
            self.clients.clear()
            logger.info("SSE 传输层已停止")
            return True
        except Exception as e:
            logger.error(f"SSE 传输层停止失败: {e}", exc_info=True)
            return False
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息到所有连接的客户端
        
        Args:
            message: 要发送的消息
            
        Returns:
            是否发送成功
        """
        if not self.is_running:
            logger.warning("SSE 传输层未运行，无法发送消息")
            return False
        
        try:
            message_str = json.dumps(message)
            
            # 发送到所有连接的客户端
            disconnected_clients = set()
            for client_queue in self.clients:
                try:
                    await client_queue.put(message_str)
                except Exception as e:
                    logger.error(f"发送消息到客户端失败: {e}")
                    disconnected_clients.add(client_queue)
            
            # 清理断开的客户端
            self.clients -= disconnected_clients
            
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            return False
    
    async def handle_client(self, request: Request):
        """处理客户端 SSE 连接
        
        供 FastAPI 路由调用。
        
        Args:
            request: FastAPI 请求对象
            
        Returns:
            EventSourceResponse 对象
        """
        client_queue = asyncio.Queue()
        self.clients.add(client_queue)
        
        logger.info(f"新的 SSE 客户端连接: {request.client}")
        
        async def event_generator():
            try:
                # 发送初始连接确认
                yield {
                    "event": "connected",
                    "data": json.dumps({"status": "connected", "transport": "sse"})
                }
                
                while self.is_running:
                    try:
                        # 等待消息，设置超时以便检查运行状态
                        message = await asyncio.wait_for(
                            client_queue.get(),
                            timeout=1.0
                        )
                        
                        if message is None:  # 关闭信号
                            break
                        
                        yield {
                            "event": "message",
                            "data": message
                        }
                    except asyncio.TimeoutError:
                        # 发送心跳保持连接
                        yield {
                            "event": "ping",
                            "data": ""
                        }
                    except Exception as e:
                        logger.error(f"SSE 事件生成错误: {e}")
                        break
            finally:
                self.clients.discard(client_queue)
                logger.info(f"SSE 客户端断开连接: {request.client}")
        
        return EventSourceResponse(event_generator())
    
    async def handle_post_message(self, request: Request) -> Dict[str, Any]:
        """处理客户端 POST 消息
        
        客户端通过 POST 发送消息到服务端。
        
        Args:
            request: FastAPI 请求对象
            
        Returns:
            响应字典
        """
        try:
            body = await request.body()
            message_str = body.decode('utf-8')
            message = self._parse_message(message_str)
            
            if message is None:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    },
                    "id": None
                }
            
            # 处理消息（异步）
            if self.message_handler:
                # 创建任务异步处理，避免阻塞
                asyncio.create_task(self._process_message_async(message))
            
            # 立即返回接受确认
            return {
                "jsonrpc": "2.0",
                "result": {"status": "accepted"},
                "id": message.get('id')
            }
            
        except Exception as e:
            logger.error(f"处理 POST 消息失败: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": None
            }
    
    async def _process_message_async(self, message: Dict[str, Any]) -> None:
        """异步处理消息
        
        Args:
            message: 要处理的消息
        """
        try:
            self._handle_incoming_message(message)
        except Exception as e:
            logger.error(f"异步处理消息失败: {e}", exc_info=True)
    
    def get_endpoint_url(self) -> str:
        """获取端点 URL
        
        Returns:
            SSE 端点 URL
        """
        return f"http://{self.host}:{self.port}/mcp/sse"
