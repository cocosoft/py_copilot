"""
Skill注册表

本模块管理所有Skill能力的注册和发现
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.capabilities.adapters.skill_adapter import SkillCapability
from app.models.skill import Skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Skill注册表

    管理所有Skill能力的注册、发现和生命周期。
    提供Skill到Capability的统一访问接口。

    Attributes:
        _capabilities: 已注册的Skill能力字典
        _db: 数据库会话
    """

    def __init__(self, db: Session):
        """
        初始化Skill注册表

        Args:
            db: 数据库会话
        """
        self._capabilities: Dict[str, SkillCapability] = {}
        self._db = db

    async def initialize(self):
        """
        初始化注册表

        从数据库加载所有启用的Skill并注册
        """
        logger.info("开始初始化Skill注册表...")

        try:
            # 加载所有启用的Skill
            skills = self._db.query(Skill).filter(
                Skill.status == "enabled"
            ).all()

            for skill in skills:
                await self.register_skill(skill)

            logger.info(f"Skill注册表初始化完成，共注册 {len(self._capabilities)} 个Skill")

        except Exception as e:
            logger.error(f"Skill注册表初始化失败: {e}", exc_info=True)
            raise

    async def register_skill(self, skill: Skill) -> SkillCapability:
        """
        注册单个Skill

        Args:
            skill: Skill模型实例

        Returns:
            SkillCapability: 创建的Skill能力适配器
        """
        try:
            # 创建适配器
            capability = SkillCapability(skill)

            # 初始化
            await capability.initialize()

            # 注册
            self._capabilities[skill.name] = capability

            logger.debug(f"Skill已注册: {skill.name}")

            return capability

        except Exception as e:
            logger.error(f"注册Skill失败: {skill.name}, error={e}")
            raise

    async def unregister_skill(self, skill_name: str):
        """
        注销Skill

        Args:
            skill_name: Skill名称
        """
        if skill_name in self._capabilities:
            capability = self._capabilities[skill_name]
            await capability.cleanup()
            del self._capabilities[skill_name]

            logger.debug(f"Skill已注销: {skill_name}")

    def get_capability(self, skill_name: str) -> Optional[SkillCapability]:
        """
        获取Skill能力

        Args:
            skill_name: Skill名称

        Returns:
            Optional[SkillCapability]: Skill能力适配器，不存在返回None
        """
        return self._capabilities.get(skill_name)

    def has_capability(self, skill_name: str) -> bool:
        """
        检查是否存在指定Skill

        Args:
            skill_name: Skill名称

        Returns:
            bool: 是否存在
        """
        return skill_name in self._capabilities

    def list_capabilities(self) -> List[str]:
        """
        列出所有已注册的Skill名称

        Returns:
            List[str]: Skill名称列表
        """
        return list(self._capabilities.keys())

    def get_all_capabilities(self) -> Dict[str, SkillCapability]:
        """
        获取所有已注册的Skill能力

        Returns:
            Dict[str, SkillCapability]: Skill能力字典
        """
        return self._capabilities.copy()

    def get_capabilities_by_tag(self, tag: str) -> List[SkillCapability]:
        """
        根据标签获取Skill能力

        Args:
            tag: 标签

        Returns:
            List[SkillCapability]: Skill能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if tag in cap.metadata.tags
        ]

    def get_capabilities_by_category(self, category: str) -> List[SkillCapability]:
        """
        根据分类获取Skill能力

        Args:
            category: 分类

        Returns:
            List[SkillCapability]: Skill能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.metadata.category == category
        ]

    def get_official_capabilities(self) -> List[SkillCapability]:
        """
        获取所有官方Skill能力

        Returns:
            List[SkillCapability]: 官方Skill能力列表
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.skill.is_official
        ]

    async def refresh(self):
        """
        刷新注册表

        重新从数据库加载所有Skill
        """
        logger.info("刷新Skill注册表...")

        # 清理现有注册
        for capability in self._capabilities.values():
            await capability.cleanup()

        self._capabilities.clear()

        # 重新初始化
        await self.initialize()

    async def shutdown(self):
        """
        关闭注册表

        清理所有资源
        """
        logger.info("关闭Skill注册表...")

        for capability in self._capabilities.values():
            await capability.cleanup()

        self._capabilities.clear()

        logger.info("Skill注册表已关闭")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取注册表统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total = len(self._capabilities)
        official = sum(1 for cap in self._capabilities.values() if cap.skill.is_official)
        builtin = sum(1 for cap in self._capabilities.values() if cap.skill.is_builtin)

        return {
            "total_skills": total,
            "official_skills": official,
            "builtin_skills": builtin,
            "custom_skills": total - official,
            "registered_names": list(self._capabilities.keys())
        }
