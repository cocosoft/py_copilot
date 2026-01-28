"""
WebSocket路由和API端点

提供WebSocket连接端点和管理API。
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

from .connection_manager import ConnectionManager, ConnectionStatus, ClientType, connection_manager
from .message_handler import MessageHandler, message_handler
from .session_manager import SessionManager, SessionStatus, SessionType, session_manager
from .message_router import MessageRouter, RoutingStrategy, MessagePriority, message_router

router = APIRouter(prefix="/websocket", tags=["websocket"])


@router.websocket("/connect/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket连接端点
    
    Args:
        websocket: WebSocket连接对象
        client_id: 客户端ID
    """
    connection = None
    
    try:
        # 建立连接
        connection = await connection_manager.connect(
            websocket=websocket,
            client_id=client_id,
            client_type=ClientType.WEB,
            metadata={
                "user_agent": websocket.headers.get("user-agent", "unknown"),
                "remote_addr": websocket.client.host if websocket.client else "unknown"
            }
        )
        
        # 启动清理任务（如果未启动）
        await connection_manager.start_cleanup_task()
        
        # 主消息循环
        while True:
            # 接收消息
            raw_message = await websocket.receive_text()
            
            # 处理消息
            await message_handler.handle_message(connection.connection_id, raw_message)
            
    except WebSocketDisconnect:
        # 客户端主动断开连接
        if connection:
            await connection_manager.disconnect(connection.connection_id, 1000)
    except Exception as e:
        # 其他异常
        if connection:
            await connection_manager.disconnect(connection.connection_id, 1011)  # 1011: Internal Error
        raise


@router.websocket("/connect/{client_id}/{client_type}")
async def websocket_endpoint_with_type(websocket: WebSocket, client_id: str, client_type: str):
    """带客户端类型的WebSocket连接端点
    
    Args:
        websocket: WebSocket连接对象
        client_id: 客户端ID
        client_type: 客户端类型
    """
    # 验证客户端类型
    try:
        client_type_enum = ClientType(client_type.lower())
    except ValueError:
        await websocket.close(code=1008, reason="Invalid client type")  # 1008: Policy Violation
        return
    
    connection = None
    
    try:
        # 建立连接
        connection = await connection_manager.connect(
            websocket=websocket,
            client_id=client_id,
            client_type=client_type_enum,
            metadata={
                "user_agent": websocket.headers.get("user-agent", "unknown"),
                "remote_addr": websocket.client.host if websocket.client else "unknown"
            }
        )
        
        # 启动清理任务（如果未启动）
        await connection_manager.start_cleanup_task()
        
        # 主消息循环
        while True:
            # 接收消息
            raw_message = await websocket.receive_text()
            
            # 处理消息
            await message_handler.handle_message(connection.connection_id, raw_message)
            
    except WebSocketDisconnect:
        # 客户端主动断开连接
        if connection:
            await connection_manager.disconnect(connection.connection_id, 1000)
    except Exception as e:
        # 其他异常
        if connection:
            await connection_manager.disconnect(connection.connection_id, 1011)  # 1011: Internal Error
        raise


@router.get("/stats")
async def get_websocket_stats():
    """获取WebSocket连接统计信息
    
    Returns:
        连接统计信息
    """
    return {
        "success": True,
        "data": connection_manager.get_connection_stats()
    }


@router.get("/connections")
async def get_active_connections():
    """获取活跃连接列表
    
    Returns:
        活跃连接列表
    """
    connections = []
    for connection_id, connection in connection_manager.active_connections.items():
        connections.append(connection.to_dict())
    
    return {
        "success": True,
        "data": {
            "connections": connections,
            "total": len(connections)
        }
    }


@router.get("/connections/{connection_id}")
async def get_connection_details(connection_id: str):
    """获取连接详情
    
    Args:
        connection_id: 连接ID
        
    Returns:
        连接详情
    """
    details = connection_manager.get_connection_details(connection_id)
    
    if not details:
        raise HTTPException(status_code=404, detail="连接不存在")
    
    return {
        "success": True,
        "data": details
    }


@router.post("/connections/{connection_id}/disconnect")
async def disconnect_connection(connection_id: str):
    """断开指定连接
    
    Args:
        connection_id: 连接ID
        
    Returns:
        断开结果
    """
    details = connection_manager.get_connection_details(connection_id)
    
    if not details:
        raise HTTPException(status_code=404, detail="连接不存在")
    
    await connection_manager.disconnect(connection_id, 1000)
    
    return {
        "success": True,
        "message": f"连接 {connection_id} 已断开"
    }


@router.post("/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """广播消息到所有连接
    
    Args:
        message: 消息内容
        
    Returns:
        广播结果
    """
    success_count = await connection_manager.broadcast(message)
    
    return {
        "success": True,
        "data": {
            "sent_count": success_count,
            "total_connections": len(connection_manager.active_connections)
        }
    }


@router.post("/groups/{group_name}/broadcast")
async def broadcast_to_group(group_name: str, message: Dict[str, Any]):
    """广播消息到指定组
    
    Args:
        group_name: 组名
        message: 消息内容
        
    Returns:
        广播结果
    """
    success_count = await connection_manager.send_to_group(group_name, message)
    
    return {
        "success": True,
        "data": {
            "group_name": group_name,
            "sent_count": success_count,
            "total_members": len(connection_manager.connection_groups.get(group_name, []))
        }
    }


@router.post("/connections/{connection_id}/send")
async def send_to_connection(connection_id: str, message: Dict[str, Any]):
    """发送消息到指定连接
    
    Args:
        connection_id: 连接ID
        message: 消息内容
        
    Returns:
        发送结果
    """
    success = await connection_manager.send_to_client(connection_id, message)
    
    if not success:
        raise HTTPException(status_code=404, detail="连接不存在或发送失败")
    
    return {
        "success": True,
        "message": "消息发送成功"
    }


@router.post("/connections/{connection_id}/subscribe")
async def subscribe_to_group(connection_id: str, group_name: str):
    """将连接加入指定组
    
    Args:
        connection_id: 连接ID
        group_name: 组名
        
    Returns:
        订阅结果
    """
    details = connection_manager.get_connection_details(connection_id)
    
    if not details:
        raise HTTPException(status_code=404, detail="连接不存在")
    
    await connection_manager.join_group(connection_id, group_name)
    
    return {
        "success": True,
        "message": f"连接 {connection_id} 已加入组 {group_name}"
    }


@router.post("/connections/{connection_id}/unsubscribe")
async def unsubscribe_from_group(connection_id: str, group_name: str):
    """将连接移出指定组
    
    Args:
        connection_id: 连接ID
        group_name: 组名
        
    Returns:
        取消订阅结果
    """
    details = connection_manager.get_connection_details(connection_id)
    
    if not details:
        raise HTTPException(status_code=404, detail="连接不存在")
    
    await connection_manager.leave_group(connection_id, group_name)
    
    return {
        "success": True,
        "message": f"连接 {connection_id} 已移出组 {group_name}"
    }


@router.get("/groups")
async def get_groups():
    """获取所有组信息
    
    Returns:
        组信息
    """
    groups = {}
    for group_name, connection_ids in connection_manager.connection_groups.items():
        groups[group_name] = {
            "member_count": len(connection_ids),
            "connections": list(connection_ids)
        }
    
    return {
        "success": True,
        "data": {
            "groups": groups,
            "total_groups": len(groups)
        }
    }


@router.get("/groups/{group_name}")
async def get_group_details(group_name: str):
    """获取组详情
    
    Args:
        group_name: 组名
        
    Returns:
        组详情
    """
    if group_name not in connection_manager.connection_groups:
        raise HTTPException(status_code=404, detail="组不存在")
    
    connections = []
    for connection_id in connection_manager.connection_groups[group_name]:
        details = connection_manager.get_connection_details(connection_id)
        if details:
            connections.append(details)
    
    return {
        "success": True,
        "data": {
            "group_name": group_name,
            "member_count": len(connections),
            "connections": connections
        }
    }


@router.get("/sessions/stats")
async def get_session_stats():
    """获取会话统计信息
    
    Returns:
        会话统计信息
    """
    return {
        "success": True,
        "data": session_manager.get_session_stats()
    }


@router.get("/sessions")
async def get_sessions(user_id: Optional[int] = None):
    """获取会话列表
    
    Args:
        user_id: 用户ID，如果提供则获取指定用户的会话
        
    Returns:
        会话列表
    """
    if user_id:
        sessions = await session_manager.get_user_sessions(user_id)
    else:
        sessions = list(session_manager.sessions.values())
    
    return {
        "success": True,
        "data": {
            "sessions": [session.to_dict() for session in sessions],
            "total": len(sessions)
        }
    }


@router.get("/sessions/active")
async def get_active_sessions(user_id: Optional[int] = None):
    """获取活跃会话列表
    
    Args:
        user_id: 用户ID，如果提供则获取指定用户的活跃会话
        
    Returns:
        活跃会话列表
    """
    active_sessions = await session_manager.get_active_sessions(user_id)
    
    return {
        "success": True,
        "data": {
            "sessions": [session.to_dict() for session in active_sessions],
            "total": len(active_sessions)
        }
    }


@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str):
    """获取会话详情
    
    Args:
        session_id: 会话ID
        
    Returns:
        会话详情
    """
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = session_manager.sessions[session_id]
    
    return {
        "success": True,
        "data": session.to_dict()
    }


@router.post("/sessions/create")
async def create_session(user_id: int, session_type: str = SessionType.CHAT.value, 
                        metadata: Optional[Dict[str, Any]] = None):
    """创建新会话
    
    Args:
        user_id: 用户ID
        session_type: 会话类型
        metadata: 会话元数据
        
    Returns:
        创建的会话信息
    """
    try:
        session_type_enum = SessionType(session_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的会话类型")
    
    session = await session_manager.create_session(user_id, session_type_enum, metadata)
    
    return {
        "success": True,
        "data": session.to_dict()
    }


@router.post("/sessions/{session_id}/close")
async def close_session(session_id: str):
    """关闭会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        关闭结果
    """
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    await session_manager.close_session(session_id)
    
    return {
        "success": True,
        "message": f"会话 {session_id} 已关闭"
    }


@router.post("/sessions/{session_id}/send")
async def send_to_session(session_id: str, message: Dict[str, Any]):
    """发送消息到会话的所有连接
    
    Args:
        session_id: 会话ID
        message: 消息内容
        
    Returns:
        发送结果
    """
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    success_count = await session_manager.send_to_session(session_id, message)
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "sent_count": success_count,
            "total_connections": len(session_manager.sessions[session_id].associated_connections)
        }
    }


@router.get("/connections/{connection_id}/session")
async def get_session_by_connection(connection_id: str):
    """根据连接ID获取关联的会话
    
    Args:
        connection_id: 连接ID
        
    Returns:
        关联的会话信息
    """
    session = await session_manager.get_session_by_connection(connection_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="连接未关联到任何会话")
    
    return {
        "success": True,
        "data": session.to_dict()
    }


@router.get("/routing/queue/stats")
async def get_message_queue_stats():
    """获取消息队列统计信息
    
    Returns:
        消息队列统计信息
    """
    return {
        "success": True,
        "data": message_router.get_queue_stats()
    }


@router.post("/routing/route")
async def route_message(message: Dict[str, Any], routing_strategy: str, 
                       target: Optional[str] = None, priority: str = MessagePriority.NORMAL.value):
    """路由消息
    
    Args:
        message: 消息内容
        routing_strategy: 路由策略
        target: 目标标识
        priority: 消息优先级
        
    Returns:
        路由结果
    """
    try:
        routing_strategy_enum = RoutingStrategy(routing_strategy)
        priority_enum = MessagePriority(priority)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的路由策略或优先级: {e}")
    
    try:
        message_id = await message_router.route_message(
            message, routing_strategy_enum, target, priority_enum
        )
        
        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "routing_strategy": routing_strategy,
                "target": target,
                "priority": priority
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"消息路由失败: {str(e)}")


@router.post("/routing/broadcast")
async def broadcast_message(message: Dict[str, Any], priority: str = MessagePriority.NORMAL.value):
    """广播消息到所有连接
    
    Args:
        message: 消息内容
        priority: 消息优先级
        
    Returns:
        广播结果
    """
    try:
        priority_enum = MessagePriority(priority)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的优先级")
    
    try:
        message_id = await message_router.broadcast_to_all(message, priority_enum)
        
        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "routing_strategy": "broadcast",
                "priority": priority
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"消息广播失败: {str(e)}")


@router.post("/routing/sessions/{session_id}/send")
async def send_to_session(session_id: str, message: Dict[str, Any], 
                         priority: str = MessagePriority.NORMAL.value):
    """发送消息到指定会话
    
    Args:
        session_id: 会话ID
        message: 消息内容
        priority: 消息优先级
        
    Returns:
        发送结果
    """
    try:
        priority_enum = MessagePriority(priority)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的优先级")
    
    try:
        message_id = await message_router.send_to_session(session_id, message, priority_enum)
        
        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "session_id": session_id,
                "routing_strategy": "session",
                "priority": priority
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息到会话失败: {str(e)}")


@router.post("/routing/groups/{group_name}/send")
async def send_to_group(group_name: str, message: Dict[str, Any], 
                       priority: str = MessagePriority.NORMAL.value):
    """发送消息到指定组
    
    Args:
        group_name: 组名
        message: 消息内容
        priority: 消息优先级
        
    Returns:
        发送结果
    """
    try:
        priority_enum = MessagePriority(priority)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的优先级")
    
    try:
        message_id = await message_router.send_to_group(group_name, message, priority_enum)
        
        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "group_name": group_name,
                "routing_strategy": "group",
                "priority": priority
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息到组失败: {str(e)}")


@router.post("/routing/users/{user_id}/send")
async def send_to_user(user_id: int, message: Dict[str, Any], 
                      priority: str = MessagePriority.NORMAL.value):
    """发送消息到指定用户
    
    Args:
        user_id: 用户ID
        message: 消息内容
        priority: 消息优先级
        
    Returns:
        发送结果
    """
    try:
        priority_enum = MessagePriority(priority)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的优先级")
    
    try:
        message_id = await message_router.send_to_user(user_id, message, priority_enum)
        
        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "user_id": user_id,
                "routing_strategy": "user",
                "priority": priority
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息到用户失败: {str(e)}")


@router.post("/routing/connections/{connection_id}/send")
async def send_direct(connection_id: str, message: Dict[str, Any], 
                     priority: str = MessagePriority.NORMAL.value):
    """直接发送消息到指定连接
    
    Args:
        connection_id: 连接ID
        message: 消息内容
        priority: 消息优先级
        
    Returns:
        发送结果
    """
    try:
        priority_enum = MessagePriority(priority)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的优先级")
    
    try:
        message_id = await message_router.send_direct(connection_id, message, priority_enum)
        
        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "connection_id": connection_id,
                "routing_strategy": "direct",
                "priority": priority
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"直接发送消息失败: {str(e)}")


@router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理WebSocket连接"""
    # 停止清理任务
    await connection_manager.stop_cleanup_task()
    
    # 断开所有连接
    for connection_id in list(connection_manager.active_connections.keys()):
        await connection_manager.disconnect(connection_id, 1001)  # 1001: Going Away