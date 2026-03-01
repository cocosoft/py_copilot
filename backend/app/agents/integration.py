"""
Agent系统集成模块

本模块负责将新的Agent系统与现有Agent管理系统集成
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session

from app.agents.registry import agent_registry
from app.agents.base import BaseAgent, AgentConfig, AgentResult, AgentContext
from app.models.agent import Agent

logger = logging.getLogger(__name__)


class AgentSystemIntegration:
    """
    Agent系统集成器

    负责新旧Agent系统之间的桥接和集成
    """

    def __init__(self, db: Session):
        """
        初始化集成器

        Args:
            db: 数据库会话
        """
        self.db = db
        self._initialized = False

    async def initialize(self):
        """初始化集成"""
        if self._initialized:
            return

        logger.info("初始化Agent系统集成...")

        # 同步数据库中的Agent到注册中心
        await self._sync_from_database()

        self._initialized = True
        logger.info("Agent系统集成完成")

    async def _sync_from_database(self):
        """从数据库同步Agent到注册中心"""
        try:
            # 获取数据库中所有官方Agent
            db_agents = self.db.query(Agent).filter(
                Agent.is_official == True
            ).all()

            logger.info(f"从数据库找到 {len(db_agents)} 个官方Agent")

            for db_agent in db_agents:
                # 检查是否已在注册中心
                if agent_registry.get_agent_config(db_agent.name):
                    logger.debug(f"Agent '{db_agent.name}' 已在注册中心")
                    continue

                # 创建配置
                config = self._create_config_from_db(db_agent)

                # 尝试找到对应的Agent类
                agent_class = self._find_agent_class(db_agent.name)

                if agent_class:
                    # 注册到注册中心
                    agent_registry.register(
                        agent_class=agent_class,
                        config=config,
                        create_instance=False
                    )
                    logger.info(f"从数据库同步Agent: {db_agent.name}")
                else:
                    logger.warning(f"未找到Agent类: {db_agent.name}")

        except Exception as e:
            logger.error(f"同步数据库Agent失败: {e}", exc_info=True)

    def _create_config_from_db(self, db_agent: Agent) -> AgentConfig:
        """
        从数据库Agent创建配置

        Args:
            db_agent: 数据库Agent模型

        Returns:
            AgentConfig: Agent配置
        """
        # 解析标签
        tags = []
        if db_agent.tags:
            tags = [tag.strip() for tag in db_agent.tags.split(",")]

        # 解析元数据
        metadata = {}
        if db_agent.metadata_:
            try:
                import json
                metadata = json.loads(db_agent.metadata_)
            except:
                pass

        return AgentConfig(
            name=db_agent.name,
            description=db_agent.description or "",
            version=db_agent.version or "1.0.0",
            author=db_agent.author or "System",
            tags=tags,
            metadata=metadata,
            max_retries=3,
            timeout=30.0
        )

    def _find_agent_class(self, name: str) -> Optional[type]:
        """
        根据名称查找Agent类

        Args:
            name: Agent名称

        Returns:
            Optional[type]: Agent类或None
        """
        from app.agents.official import OFFICIAL_AGENTS

        name_mapping = {
            "聊天助手": "ChatAgent",
            "翻译专家": "TranslateAgent",
            "语音识别助手": "SpeechRecognitionAgent",
            "知识库搜索": "KnowledgeSearchAgent",
            "Web搜索助手": "WebSearchAgent",
            "图片生成器": "ImageGenerationAgent",
            "图像识别专家": "ImageRecognitionAgent",
            "视频生成器": "VideoGenerationAgent",
            "视频分析专家": "VideoAnalysisAgent",
            "文字转语音": "TTSAgent",
            "语音转文字": "STTAgent",
        }

        class_name = name_mapping.get(name)
        if not class_name:
            return None

        for agent_class in OFFICIAL_AGENTS:
            if agent_class.__name__ == class_name:
                return agent_class

        return None

    async def execute_agent(
        self,
        agent_name: str,
        input_data: Any,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        执行Agent

        Args:
            agent_name: Agent名称
            input_data: 输入数据
            user_id: 用户ID
            session_id: 会话ID
            parameters: 执行参数

        Returns:
            AgentResult: 执行结果
        """
        # 获取Agent实例
        agent = agent_registry.get_agent(agent_name)

        if not agent:
            return AgentResult(
                success=False,
                error=f"Agent '{agent_name}' 未找到"
            )

        # 创建执行上下文
        context = AgentContext(
            session_id=session_id or f"session_{datetime.now().timestamp()}",
            user_id=user_id,
            parameters=parameters or {}
        )

        # 执行
        try:
            result = await agent.run(input_data, context)

            # 记录执行日志到数据库
            await self._log_execution(agent_name, input_data, result, user_id)

            return result

        except Exception as e:
            logger.error(f"执行Agent '{agent_name}' 失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                error=str(e)
            )

    async def _log_execution(
        self,
        agent_name: str,
        input_data: Any,
        result: AgentResult,
        user_id: Optional[str] = None
    ):
        """
        记录执行日志

        Args:
            agent_name: Agent名称
            input_data: 输入数据
            result: 执行结果
            user_id: 用户ID
        """
        try:
            # 这里可以扩展为写入数据库
            # 暂时只记录日志
            logger.info(
                f"Agent执行记录: {agent_name}, "
                f"成功: {result.success}, "
                f"耗时: {result.execution_time_ms}ms"
            )
        except Exception as e:
            logger.error(f"记录执行日志失败: {e}")

    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        获取Agent信息

        Args:
            agent_name: Agent名称

        Returns:
            Optional[Dict]: Agent信息
        """
        # 从注册中心获取
        agent = agent_registry.get_agent(agent_name)
        config = agent_registry.get_agent_config(agent_name)

        if not config:
            return None

        info = {
            "name": config.name,
            "description": config.description,
            "version": config.version,
            "author": config.author,
            "tags": config.tags,
            "status": agent.status.value if agent else "unknown",
            "required_capabilities": config.required_capabilities,
            "optional_capabilities": config.optional_capabilities,
        }

        # 从数据库获取额外信息
        try:
            db_agent = self.db.query(Agent).filter(
                Agent.name == agent_name
            ).first()

            if db_agent:
                info.update({
                    "id": db_agent.id,
                    "is_official": db_agent.is_official,
                    "icon": db_agent.icon,
                    "template_category": db_agent.template_category,
                })
        except Exception as e:
            logger.error(f"获取数据库Agent信息失败: {e}")

        return info

    def list_agents(
        self,
        tags: Optional[List[str]] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        列出所有Agent

        Args:
            tags: 标签过滤
            active_only: 仅返回激活的

        Returns:
            List[Dict]: Agent信息列表
        """
        agent_names = agent_registry.list_agents(
            tags=tags,
            active_only=active_only
        )

        agents = []
        for name in agent_names:
            info = self.get_agent_info(name)
            if info:
                agents.append(info)

        return agents

    def find_agents_for_task(
        self,
        task_description: str,
        required_capabilities: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        为任务查找合适的Agent

        Args:
            task_description: 任务描述
            required_capabilities: 必需的能力

        Returns:
            List[Dict]: 匹配的Agent列表
        """
        candidates = []

        # 获取所有Agent
        all_agents = self.list_agents(active_only=True)

        for agent_info in all_agents:
            score = 0.0

            # 基于能力匹配
            if required_capabilities:
                agent_caps = set(agent_info.get("required_capabilities", []))
                task_caps = set(required_capabilities)

                if task_caps.issubset(agent_caps):
                    score += 0.5

            # 基于描述匹配（简单关键词匹配）
            agent_desc = agent_info.get("description", "").lower()
            task_lower = task_description.lower()

            # 提取关键词
            keywords = task_lower.split()
            matches = sum(1 for kw in keywords if kw in agent_desc)
            if keywords:
                score += (matches / len(keywords)) * 0.3

            # 基于标签匹配
            tags = agent_info.get("tags", [])
            for tag in tags:
                if tag.lower() in task_lower:
                    score += 0.1
                    break

            if score > 0.3:
                candidates.append({
                    **agent_info,
                    "match_score": score
                })

        # 按匹配分数排序
        candidates.sort(key=lambda x: x["match_score"], reverse=True)

        return candidates[:5]  # 返回前5个


# 全局集成器实例
_integration_instance: Optional[AgentSystemIntegration] = None


def get_integration(db: Session) -> AgentSystemIntegration:
    """
    获取集成器实例

    Args:
        db: 数据库会话

    Returns:
        AgentSystemIntegration: 集成器实例
    """
    global _integration_instance

    if _integration_instance is None:
        _integration_instance = AgentSystemIntegration(db)

    return _integration_instance


async def initialize_agent_system(db: Session):
    """
    初始化Agent系统

    Args:
        db: 数据库会话
    """
    integration = get_integration(db)
    await integration.initialize()
