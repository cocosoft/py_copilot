"""MCP 适配器模块

提供 MCP 协议与现有系统的适配器。
"""

from .base import BaseAdapter
from .tool_adapter import ToolAdapter
from .skill_adapter import SkillAdapter
from .knowledge_adapter import KnowledgeAdapter

__all__ = [
    'BaseAdapter',
    'ToolAdapter',
    'SkillAdapter',
    'KnowledgeAdapter'
]
