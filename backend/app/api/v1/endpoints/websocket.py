"""
WebSocket处理器

本模块提供智能编排的WebSocket实时通信接口
"""

import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.orchestration_service import OrchestrationService
from app.capabilities.center.unified_center import UnifiedCapabilityCenter

logger = logging.getLogger(__name__)

router = APIRouter()


class WebSocketManager:
    """
    WebSocket连接管理器

    管理所有WebSocket连接，支持按用户和对话分组
    """

    def __init__(self):
        # 所有活跃连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 用户连接映射
        self.user_connections: Dict[str, list] = {}
        # 对话连接映射
        self.conversation_connections: Dict[str, list] = {}

    async def connect(self,
                     websocket: WebSocket,
                     client_id: str,
                     user_id: Optional[str] = None,
                     conversation_id: Optional[str] = None):
        """
        建立WebSocket连接

        Args:
            websocket: WebSocket对象
            client_id: 客户端ID
            user_id: 用户ID
            conversation_id: 对话ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(client_id)

        if conversation_id:
            if conversation_id not in self.conversation_connections:
                self.conversation_connections[conversation_id] = []
            self.conversation_connections[conversation_id].append(client_id)

        logger.info(f"WebSocket连接建立: {client_id}, user={user_id}, conv={conversation_id}")

    def disconnect(self,
                  client_id: str,
                  user_id: Optional[str] = None,
                  conversation_id: Optional[str] = None):
        """
        断开WebSocket连接

        Args:
            client_id: 客户端ID
            user_id: 用户ID
            conversation_id: 对话ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if user_id and user_id in self.user_connections:
            if client_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(client_id)

        if conversation_id and conversation_id in self.conversation_connections:
            if client_id in self.conversation_connections[conversation_id]:
                self.conversation_connections[conversation_id].remove(client_id)

        logger.info(f"WebSocket连接断开: {client_id}")

    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """
        发送消息给指定客户端

        Args:
            client_id: 客户端ID
            message: 消息内容
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"发送消息失败: {client_id}, error={e}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        广播消息给所有客户端

        Args:
            message: 消息内容
        """
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"广播消息失败: {client_id}, error={e}")
                disconnected.append(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            self.disconnect(client_id)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        发送消息给指定用户的所有连接

        Args:
            user_id: 用户ID
            message: 消息内容
        """
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id]:
                await self.send_message(client_id, message)

    async def send_to_conversation(self, conversation_id: str, message: Dict[str, Any]):
        """
        发送消息给指定对话的所有连接

        Args:
            conversation_id: 对话ID
            message: 消息内容
        """
        if conversation_id in self.conversation_connections:
            for client_id in self.conversation_connections[conversation_id]:
                await self.send_message(client_id, message)


# 全局WebSocket管理器实例
ws_manager = WebSocketManager()


# ============ WebSocket路由 ============

@router.websocket("/ws/orchestration")
async def orchestration_websocket(
    websocket: WebSocket,
    client_id: Optional[str] = None,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    编排WebSocket接口

    支持实时双向通信，用于：
    - 发送用户请求
    - 接收流式响应
    - 获取执行进度
    - 控制执行流程
    """
    # 生成客户端ID
    if not client_id:
        import uuid
        client_id = str(uuid.uuid4())

    # 获取服务实例
    center = UnifiedCapabilityCenter(db)
    service = OrchestrationService(center, db)

    # 建立连接
    await ws_manager.connect(websocket, client_id, user_id, conversation_id)

    try:
        # 发送连接成功消息
        await ws_manager.send_message(client_id, {
            "type": "connected",
            "client_id": client_id,
            "conversation_id": conversation_id
        })

        # 处理消息
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "process":
                    # 处理请求
                    await _handle_process_message(
                        client_id=client_id,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        message=message,
                        service=service
                    )

                elif message_type == "stream":
                    # 流式处理请求
                    await _handle_stream_message(
                        client_id=client_id,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        message=message,
                        service=service
                    )

                elif message_type == "cancel":
                    # 取消执行
                    success = service.cancel_execution()
                    await ws_manager.send_message(client_id, {
                        "type": "cancelled",
                        "success": success
                    })

                elif message_type == "status":
                    # 获取状态
                    status = service.get_execution_status()
                    await ws_manager.send_message(client_id, {
                        "type": "status",
                        "data": status
                    })

                elif message_type == "history":
                    # 获取历史
                    conv_id = message.get("conversation_id", conversation_id)
                    limit = message.get("limit", 50)
                    history = service.get_conversation_history(conv_id, limit)
                    await ws_manager.send_message(client_id, {
                        "type": "history",
                        "conversation_id": conv_id,
                        "messages": history
                    })

                elif message_type == "ping":
                    # 心跳响应
                    await ws_manager.send_message(client_id, {
                        "type": "pong",
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    })

                else:
                    # 未知消息类型
                    await ws_manager.send_message(client_id, {
                        "type": "error",
                        "message": f"未知消息类型: {message_type}"
                    })

            except json.JSONDecodeError:
                await ws_manager.send_message(client_id, {
                    "type": "error",
                    "message": "无效的JSON格式"
                })

            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}", exc_info=True)
                await ws_manager.send_message(client_id, {
                    "type": "error",
                    "message": f"处理失败: {str(e)}"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket断开连接: {client_id}")

    finally:
        ws_manager.disconnect(client_id, user_id, conversation_id)


async def _handle_process_message(
    client_id: str,
    user_id: Optional[str],
    conversation_id: Optional[str],
    message: Dict[str, Any],
    service: OrchestrationService
):
    """
    处理process类型消息

    Args:
        client_id: 客户端ID
        user_id: 用户ID
        conversation_id: 对话ID
        message: 消息内容
        service: 编排服务
    """
    user_input = message.get("user_input", "")
    conv_id = message.get("conversation_id", conversation_id)

    if not user_input:
        await ws_manager.send_message(client_id, {
            "type": "error",
            "message": "user_input不能为空"
        })
        return

    # 发送开始处理消息
    await ws_manager.send_message(client_id, {
        "type": "processing",
        "conversation_id": conv_id
    })

    try:
        # 处理请求
        result = await service.process_request(
            user_input=user_input,
            conversation_id=conv_id,
            user_id=user_id
        )

        # 发送结果
        await ws_manager.send_message(client_id, {
            "type": "result",
            "data": result
        })

    except Exception as e:
        logger.error(f"处理请求失败: {e}", exc_info=True)
        await ws_manager.send_message(client_id, {
            "type": "error",
            "message": f"处理失败: {str(e)}"
        })


async def _handle_stream_message(
    client_id: str,
    user_id: Optional[str],
    conversation_id: Optional[str],
    message: Dict[str, Any],
    service: OrchestrationService
):
    """
    处理stream类型消息

    Args:
        client_id: 客户端ID
        user_id: 用户ID
        conversation_id: 对话ID
        message: 消息内容
        service: 编排服务
    """
    user_input = message.get("user_input", "")
    conv_id = message.get("conversation_id", conversation_id)

    if not user_input:
        await ws_manager.send_message(client_id, {
            "type": "error",
            "message": "user_input不能为空"
        })
        return

    try:
        # 流式处理
        async for event in service.process_request_stream(
            user_input=user_input,
            conversation_id=conv_id,
            user_id=user_id
        ):
            # 解析SSE事件
            lines = event.strip().split('\n')
            event_type = None
            event_data = {}

            for line in lines:
                if line.startswith('event: '):
                    event_type = line[7:]
                elif line.startswith('data: '):
                    try:
                        event_data = json.loads(line[6:])
                    except:
                        event_data = {"message": line[6:]}

            if event_type:
                await ws_manager.send_message(client_id, {
                    "type": event_type,
                    "data": event_data
                })

    except Exception as e:
        logger.error(f"流式处理失败: {e}", exc_info=True)
        await ws_manager.send_message(client_id, {
            "type": "error",
            "message": f"流式处理失败: {str(e)}"
        })


# ============ 广播接口 ============

@router.post("/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """
    广播消息给所有WebSocket客户端

    仅用于管理用途
    """
    await ws_manager.broadcast(message)
    return {"message": "广播已发送"}


@router.get("/connections")
async def get_connections():
    """
    获取连接统计信息

    仅用于监控用途
    """
    return {
        "total_connections": len(ws_manager.active_connections),
        "user_connections": {
            user_id: len(connections)
            for user_id, connections in ws_manager.user_connections.items()
        },
        "conversation_connections": {
            conv_id: len(connections)
            for conv_id, connections in ws_manager.conversation_connections.items()
        }
    }
