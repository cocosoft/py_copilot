"""
智能体执行API

提供智能体的消息处理、能力执行和对话管理功能。
"""
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .agent_engine import (
    Message, MessageType, ConversationContext, ExecutionResult,
    agent_engine
)
from .agent_models import agent_manager, AgentStatus, AgentCapability

router = APIRouter(prefix="/api/agents", tags=["智能体执行"])


class MessageRequest(BaseModel):
    """消息请求模型"""
    content: str
    message_type: str = "text"
    metadata: Dict[str, Any] = None


class MessageResponse(BaseModel):
    """消息响应模型"""
    success: bool
    output: str
    error_message: str = ""
    execution_time: float
    metadata: Dict[str, Any]


class ConversationResponse(BaseModel):
    """对话响应模型"""
    context_id: str
    agent_id: str
    user_id: str
    messages: list
    created_at: str
    updated_at: str


class CapabilityExecutionRequest(BaseModel):
    """能力执行请求模型"""
    capability: str
    input_data: Any
    user_id: str = "system"


class CapabilityExecutionResponse(BaseModel):
    """能力执行响应模型"""
    success: bool
    output: str
    error_message: str = ""
    execution_time: float
    metadata: Dict[str, Any]


@router.post("/{agent_id}/messages", response_model=MessageResponse)
async def send_message(agent_id: str, user_id: str, request: MessageRequest):
    """发送消息给智能体
    
    Args:
        agent_id: 智能体ID
        user_id: 用户ID
        request: 消息请求
        
    Returns:
        消息响应
    """
    try:
        # 验证智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
            
        # 检查智能体状态
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(status_code=400, detail=f"智能体 {agent_id} 未激活")
            
        # 解析消息类型
        try:
            message_type = MessageType(request.message_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的消息类型: {request.message_type}")
            
        # 创建消息对象
        message = Message(
            content=request.content,
            message_type=message_type,
            sender="user",
            metadata=request.metadata or {}
        )
        
        # 处理消息
        result = await agent_engine.process_message(agent_id, user_id, message)
        
        return MessageResponse(**result.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")


@router.get("/{agent_id}/conversations/{user_id}", response_model=ConversationResponse)
async def get_conversation(agent_id: str, user_id: str):
    """获取对话上下文
    
    Args:
        agent_id: 智能体ID
        user_id: 用户ID
        
    Returns:
        对话上下文
    """
    try:
        # 验证智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
            
        # 获取对话上下文
        context = agent_engine.get_conversation_context(agent_id, user_id)
        if not context:
            # 创建新的对话上下文
            context = ConversationContext(agent_id=agent_id, user_id=user_id)
            
        return ConversationResponse(**context.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话上下文失败: {str(e)}")


@router.delete("/{agent_id}/conversations/{user_id}")
async def clear_conversation(agent_id: str, user_id: str):
    """清空对话上下文
    
    Args:
        agent_id: 智能体ID
        user_id: 用户ID
        
    Returns:
        清空结果
    """
    try:
        # 验证智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
            
        # 清空对话上下文
        success = agent_engine.clear_conversation_context(agent_id, user_id)
        
        return {
            "status": "success" if success else "no_conversation",
            "message": "对话上下文已清空" if success else "未找到对话上下文",
            "agent_id": agent_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空对话上下文失败: {str(e)}")


@router.post("/{agent_id}/capabilities", response_model=CapabilityExecutionResponse)
async def execute_capability(agent_id: str, request: CapabilityExecutionRequest):
    """执行智能体能力
    
    Args:
        agent_id: 智能体ID
        request: 能力执行请求
        
    Returns:
        执行结果
    """
    try:
        # 验证智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
            
        # 检查智能体状态
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(status_code=400, detail=f"智能体 {agent_id} 未激活")
            
        # 解析能力类型
        try:
            capability = AgentCapability(request.capability)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的能力类型: {request.capability}")
            
        # 执行能力
        result = await agent_engine.execute_capability(
            agent_id, capability, request.input_data, request.user_id
        )
        
        return CapabilityExecutionResponse(**result.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行能力失败: {str(e)}")


@router.get("/{agent_id}/capabilities")
async def get_agent_capabilities(agent_id: str):
    """获取智能体支持的能力
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        能力列表
    """
    try:
        # 验证智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
            
        # 获取支持的能力
        capabilities = [cap.value for cap in agent.config.capabilities]
        
        # 获取已注册的处理器
        registered_capabilities = [cap.value for cap in agent_engine.handlers.keys()]
        
        # 计算可用能力
        available_capabilities = list(set(capabilities) & set(registered_capabilities))
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "supported_capabilities": capabilities,
            "available_capabilities": available_capabilities,
            "registered_capabilities": registered_capabilities,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体能力失败: {str(e)}")


@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """获取智能体状态信息
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        状态信息
    """
    try:
        # 验证智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
            
        # 获取对话统计
        conversations_count = 0
        active_conversations = []
        
        engine_stats = agent_engine.get_engine_stats()
        for conv_key in engine_stats.get("active_conversations", []):
            if conv_key.startswith(f"{agent_id}:"):
                conversations_count += 1
                active_conversations.append(conv_key.split(":", 1)[1])  # 提取用户ID
                
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "status": agent.status.value,
            "conversations_count": conversations_count,
            "active_conversations": active_conversations,
            "capabilities": [cap.value for cap in agent.config.capabilities],
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体状态失败: {str(e)}")


@router.post("/{agent_id}/test")
async def test_agent(agent_id: str, test_message: str = Query("你好")):
    """测试智能体
    
    Args:
        agent_id: 智能体ID
        test_message: 测试消息
        
    Returns:
        测试结果
    """
    try:
        # 验证智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
            
        # 检查智能体状态
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(status_code=400, detail=f"智能体 {agent_id} 未激活")
            
        # 创建测试消息
        message = Message(
            content=test_message,
            message_type=MessageType.TEXT,
            sender="tester"
        )
        
        # 处理消息
        result = await agent_engine.process_message(agent_id, "test_user", message)
        
        return {
            "status": "success" if result.success else "error",
            "test_message": test_message,
            "agent_response": result.output,
            "execution_time": result.execution_time,
            "error_message": result.error_message,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试智能体失败: {str(e)}")


@router.get("/engine/stats")
async def get_engine_stats():
    """获取引擎统计信息
    
    Returns:
        引擎统计
    """
    try:
        stats = agent_engine.get_engine_stats()
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取引擎统计失败: {str(e)}")


@router.post("/{agent_id}/batch-messages")
async def batch_send_messages(agent_id: str, user_id: str, messages: list):
    """批量发送消息
    
    Args:
        agent_id: 智能体ID
        user_id: 用户ID
        messages: 消息列表
        
    Returns:
        批量处理结果
    """
    try:
        # 验证智能体
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 未找到")
            
        # 检查智能体状态
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(status_code=400, detail=f"智能体 {agent_id} 未激活")
            
        results = []
        
        for msg_data in messages:
            try:
                # 解析消息类型
                message_type = MessageType(msg_data.get("message_type", "text"))
                
                # 创建消息对象
                message = Message(
                    content=msg_data.get("content", ""),
                    message_type=message_type,
                    sender="user",
                    metadata=msg_data.get("metadata", {})
                )
                
                # 处理消息
                result = await agent_engine.process_message(agent_id, user_id, message)
                
                results.append({
                    "message_id": message.message_id,
                    "success": result.success,
                    "output": result.output,
                    "error_message": result.error_message,
                    "execution_time": result.execution_time
                })
                
            except Exception as e:
                results.append({
                    "message_id": "unknown",
                    "success": False,
                    "error_message": str(e),
                    "execution_time": 0.0
                })
                
        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        error_count = len(results) - success_count
        
        return {
            "status": "success",
            "total_messages": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
            "agent_id": agent_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量发送消息失败: {str(e)}")