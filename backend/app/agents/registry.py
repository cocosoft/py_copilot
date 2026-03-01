"""
Agent注册中心

本模块提供Agent的注册、发现和管理功能
"""

import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field

from app.agents.base import BaseAgent, AgentConfig, AgentStatus

logger = logging.getLogger(__name__)


@dataclass
class AgentRegistration:
    """
    Agent注册信息

    Attributes:
        agent_class: Agent类
        config: Agent配置
        instance: Agent实例（可选）
        is_active: 是否激活
        register_time: 注册时间
    """
    agent_class: Type[BaseAgent]
    config: AgentConfig
    instance: Optional[BaseAgent] = None
    is_active: bool = True
    register_time: str = field(default_factory=lambda: __import__('datetime').datetime.now().isoformat())


class AgentRegistry:
    """
    Agent注册中心

    管理所有Agent的注册、发现和生命周期。

    Attributes:
        _agents: Agent注册表
        _singleton: 单例模式
    """

    _singleton = None

    def __new__(cls):
        """单例模式"""
        if cls._singleton is None:
            cls._singleton = super().__new__(cls)
            cls._singleton._initialized = False
        return cls._singleton

    def __init__(self):
        """初始化注册中心"""
        if self._initialized:
            return

        self._agents: Dict[str, AgentRegistration] = {}
        self._initialized = True

        logger.info("Agent注册中心已创建")

    def register(self,
                agent_class: Type[BaseAgent],
                config: AgentConfig,
                create_instance: bool = False) -> bool:
        """
        注册Agent

        Args:
            agent_class: Agent类
            config: Agent配置
            create_instance: 是否立即创建实例

        Returns:
            bool: 是否成功
        """
        agent_name = config.name

        if agent_name in self._agents:
            logger.warning(f"Agent '{agent_name}' 已存在，将覆盖")

        try:
            instance = None
            if create_instance:
                instance = agent_class(config)

            self._agents[agent_name] = AgentRegistration(
                agent_class=agent_class,
                config=config,
                instance=instance
            )

            logger.info(f"Agent '{agent_name}' 已注册")
            return True

        except Exception as e:
            logger.error(f"注册Agent '{agent_name}' 失败: {e}")
            return False

    def unregister(self, agent_name: str) -> bool:
        """
        注销Agent

        Args:
            agent_name: Agent名称

        Returns:
            bool: 是否成功
        """
        if agent_name not in self._agents:
            logger.warning(f"Agent '{agent_name}' 不存在")
            return False

        del self._agents[agent_name]
        logger.info(f"Agent '{agent_name}' 已注销")
        return True

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        获取Agent实例

        Args:
            agent_name: Agent名称

        Returns:
            Optional[BaseAgent]: Agent实例
        """
        registration = self._agents.get(agent_name)
        if not registration:
            return None

        # 如果实例不存在，创建实例
        if registration.instance is None:
            try:
                registration.instance = registration.agent_class(registration.config)
            except Exception as e:
                logger.error(f"创建Agent '{agent_name}' 实例失败: {e}")
                return None

        return registration.instance

    def get_agent_class(self, agent_name: str) -> Optional[Type[BaseAgent]]:
        """
        获取Agent类

        Args:
            agent_name: Agent名称

        Returns:
            Optional[Type[BaseAgent]]: Agent类
        """
        registration = self._agents.get(agent_name)
        return registration.agent_class if registration else None

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """
        获取Agent配置

        Args:
            agent_name: Agent名称

        Returns:
            Optional[AgentConfig]: Agent配置
        """
        registration = self._agents.get(agent_name)
        return registration.config if registration else None

    def list_agents(self,
                   tags: Optional[List[str]] = None,
                   active_only: bool = True) -> List[str]:
        """
        列出所有Agent

        Args:
            tags: 标签过滤
            active_only: 仅返回激活的Agent

        Returns:
            List[str]: Agent名称列表
        """
        result = []

        for name, registration in self._agents.items():
            # 检查是否激活
            if active_only and not registration.is_active:
                continue

            # 检查标签
            if tags:
                if not any(tag in registration.config.tags for tag in tags):
                    continue

            result.append(name)

        return result

    def get_all_agents_info(self) -> List[Dict[str, Any]]:
        """
        获取所有Agent信息

        Returns:
            List[Dict[str, Any]]: Agent信息列表
        """
        result = []

        for name, registration in self._agents.items():
            info = {
                "name": name,
                "description": registration.config.description,
                "version": registration.config.version,
                "tags": registration.config.tags,
                "priority": registration.config.priority.value,
                "is_active": registration.is_active,
                "has_instance": registration.instance is not None,
                "register_time": registration.register_time
            }
            result.append(info)

        # 按优先级排序
        result.sort(key=lambda x: x["priority"], reverse=True)

        return result

    def find_agents_by_capability(self, capability: str) -> List[str]:
        """
        根据能力查找Agent

        Args:
            capability: 能力名称

        Returns:
            List[str]: Agent名称列表
        """
        result = []

        for name, registration in self._agents.items():
            if capability in registration.config.required_capabilities:
                result.append(name)
            elif capability in registration.config.optional_capabilities:
                result.append(name)

        return result

    def activate_agent(self, agent_name: str) -> bool:
        """
        激活Agent

        Args:
            agent_name: Agent名称

        Returns:
            bool: 是否成功
        """
        registration = self._agents.get(agent_name)
        if not registration:
            logger.warning(f"Agent '{agent_name}' 不存在")
            return False

        registration.is_active = True
        logger.info(f"Agent '{agent_name}' 已激活")
        return True

    def deactivate_agent(self, agent_name: str) -> bool:
        """
        停用Agent

        Args:
            agent_name: Agent名称

        Returns:
            bool: 是否成功
        """
        registration = self._agents.get(agent_name)
        if not registration:
            logger.warning(f"Agent '{agent_name}' 不存在")
            return False

        registration.is_active = False
        logger.info(f"Agent '{agent_name}' 已停用")
        return True

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        获取注册中心统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        total = len(self._agents)
        active = sum(1 for r in self._agents.values() if r.is_active)
        with_instance = sum(1 for r in self._agents.values() if r.instance is not None)

        # 按标签统计
        tag_counts: Dict[str, int] = {}
        for registration in self._agents.values():
            for tag in registration.config.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_agents": total,
            "active_agents": active,
            "inactive_agents": total - active,
            "instanced_agents": with_instance,
            "tag_distribution": tag_counts
        }

    def clear(self):
        """清空所有注册"""
        self._agents.clear()
        logger.info("Agent注册中心已清空")


# 全局注册中心实例
agent_registry = AgentRegistry()
