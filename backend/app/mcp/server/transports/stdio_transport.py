"""MCP Stdio 传输层实现

基于标准输入输出的 MCP 传输层实现。
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from .base import BaseTransport

logger = logging.getLogger(__name__)


class StdioTransport(BaseTransport):
    """Stdio 传输层实现
    
    使用标准输入输出实现 MCP 通信。
    适用于本地进程间通信。
    
    Attributes:
        input_stream: 输入流
        output_stream: 输出流
        read_task: 读取任务
        executor: 线程池执行器
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化 Stdio 传输层
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.input_stream = config.get('input_stream', sys.stdin)
        self.output_stream = config.get('output_stream', sys.stdout)
        self.read_task: Optional[asyncio.Task] = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    async def start(self) -> bool:
        """启动 Stdio 传输层
        
        Returns:
            是否启动成功
        """
        try:
            self.is_running = True
            
            # 启动读取循环
            self.read_task = asyncio.create_task(self._read_loop())
            
            logger.info("Stdio 传输层已启动")
            return True
        except Exception as e:
            logger.error(f"Stdio 传输层启动失败: {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """停止 Stdio 传输层
        
        Returns:
            是否停止成功
        """
        try:
            self.is_running = False
            
            # 取消读取任务
            if self.read_task and not self.read_task.done():
                self.read_task.cancel()
                try:
                    await self.read_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭线程池
            self.executor.shutdown(wait=False)
            
            logger.info("Stdio 传输层已停止")
            return True
        except Exception as e:
            logger.error(f"Stdio 传输层停止失败: {e}", exc_info=True)
            return False
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息
        
        将消息写入标准输出。
        
        Args:
            message: 要发送的消息
            
        Returns:
            是否发送成功
        """
        if not self.is_running:
            logger.warning("Stdio 传输层未运行，无法发送消息")
            return False
        
        try:
            # 序列化消息
            message_str = json.dumps(message)
            
            # 使用线程池执行阻塞的写操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._write_message,
                message_str
            )
            
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            return False
    
    def _write_message(self, message_str: str) -> None:
        """写入消息（同步方法）
        
        Args:
            message_str: 消息字符串
        """
        try:
            # MCP 协议使用换行符分隔消息
            self.output_stream.write(message_str + '\n')
            self.output_stream.flush()
        except Exception as e:
            logger.error(f"写入消息失败: {e}")
            raise
    
    async def _read_loop(self) -> None:
        """读取循环
        
        持续从标准输入读取消息。
        """
        logger.info("Stdio 读取循环已启动")
        
        try:
            loop = asyncio.get_event_loop()
            
            while self.is_running:
                try:
                    # 在线程池中执行阻塞的读取操作
                    line = await loop.run_in_executor(
                        self.executor,
                        self._read_line
                    )
                    
                    if line is None:
                        # 输入流结束
                        logger.info("Stdio 输入流结束")
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析消息
                    message = self._parse_message(line)
                    if message:
                        # 处理消息
                        self._handle_incoming_message(message)
                    else:
                        # 发送解析错误响应
                        error_response = self._create_error_response(
                            None, -32700, "Parse error"
                        )
                        await self.send_message(error_response)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"读取消息失败: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"读取循环错误: {e}", exc_info=True)
        finally:
            logger.info("Stdio 读取循环已结束")
    
    def _read_line(self) -> Optional[str]:
        """读取一行（同步方法）
        
        Returns:
            读取的行，如果输入结束返回 None
        """
        try:
            line = self.input_stream.readline()
            if not line:
                return None
            return line
        except Exception as e:
            logger.error(f"读取行失败: {e}")
            raise
    
    async def send_initialize_response(self, request_id: Any, protocol_version: str) -> bool:
        """发送初始化响应
        
        Args:
            request_id: 请求ID
            protocol_version: 协议版本
            
        Returns:
            是否发送成功
        """
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": {
                    "logging": {},
                    "prompts": {
                        "listChanged": True
                    },
                    "resources": {
                        "subscribe": True,
                        "listChanged": True
                    },
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "py-copilot-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
        
        return await self.send_message(response)
