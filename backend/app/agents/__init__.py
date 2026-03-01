"""
Agent模块

本模块提供智能体（Agent）的实现，包括：
- Agent基础类和接口
- 11个官方Agent的封装
- Agent注册和管理
"""

from app.agents.base import BaseAgent, AgentConfig, AgentResult
from app.agents.registry import AgentRegistry

__all__ = [
    'BaseAgent',
    'AgentConfig',
    'AgentResult',
    'AgentRegistry',
]
