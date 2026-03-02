"""
技能市场模块

支持 ClawHub 技能系统的适配器
提供技能安装、管理和执行功能
"""

from app.modules.skills.skill_manager import skill_manager
from app.modules.skills.clawhub_adapter import ClawHubSkillAdapter

__all__ = ["skill_manager", "ClawHubSkillAdapter"]
