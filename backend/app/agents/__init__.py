"""
智能体管理模块

提供智能体的数据模型、管理API和执行引擎功能。
"""

from .agent_models import (
    Agent, AgentConfig, AgentType, AgentStatus, AgentCapability,
    AgentManager, AgentTemplate, agent_manager, agent_template
)

from .agent_api import (
    AgentCreateRequest, AgentUpdateRequest, AgentResponse,
    AgentStatsResponse, AgentTemplateResponse, AgentListResponse,
    router as agent_router
)

from .agent_engine import (
    Message, MessageType, ConversationContext, ExecutionResult,
    AgentEngine, agent_engine
)

from .agent_execution_api import (
    MessageRequest, MessageResponse, ConversationResponse,
    CapabilityExecutionRequest, CapabilityExecutionResponse,
    router as agent_execution_router
)

__all__ = [
    # 数据模型
    "Agent",
    "AgentConfig",
    "AgentType", 
    "AgentStatus",
    "AgentCapability",
    "AgentManager",
    "AgentTemplate",
    "agent_manager",
    "agent_template",
    
    # 管理API
    "AgentCreateRequest",
    "AgentUpdateRequest", 
    "AgentResponse",
    "AgentStatsResponse",
    "AgentTemplateResponse",
    "AgentListResponse",
    "agent_router",
    
    # 执行引擎
    "Message",
    "MessageType",
    "ConversationContext",
    "ExecutionResult",
    "AgentEngine",
    "agent_engine",
    
    # 执行API
    "MessageRequest",
    "MessageResponse",
    "ConversationResponse",
    "CapabilityExecutionRequest",
    "CapabilityExecutionResponse",
    "agent_execution_router"
]