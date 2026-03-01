"""
Agent编排服务

提供Agent编排的高级接口，整合能力中心和Agent系统
"""

import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime

from sqlalchemy.orm import Session

from app.agents.integration import AgentSystemIntegration, get_integration
from app.agents.base import AgentResult, AgentContext
from app.capabilities.center.unified_center import UnifiedCapabilityCenter

# 全局能力中心实例
capability_center = UnifiedCapabilityCenter()
from app.orchestration.engine import orchestration_engine
from app.orchestration.models import (
    UserRequest, Intent, TaskPlan, ExecutionResult
)

logger = logging.getLogger(__name__)


class AgentOrchestrationService:
    """
    Agent编排服务

    整合Agent系统、能力中心和编排引擎，提供统一的编排接口
    """

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.agent_integration = get_integration(db)

    async def initialize(self):
        """初始化服务"""
        await self.agent_integration.initialize()
        logger.info("Agent编排服务初始化完成")

    async def process_request(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理用户请求

        Args:
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID
            context: 上下文信息

        Returns:
            Dict: 处理结果
        """
        try:
            # 1. 理解用户意图
            intent = await self._understand_intent(user_input, context)
            logger.info(f"识别意图: {intent.intent_type}, 置信度: {intent.confidence}")

            # 2. 根据意图选择处理方式
            if intent.intent_type == "agent_execution":
                # 直接执行Agent
                return await self._execute_agent_directly(
                    intent, user_input, user_id, session_id
                )
            elif intent.intent_type == "capability_execution":
                # 执行能力
                return await self._execute_capability(
                    intent, user_input, user_id
                )
            else:
                # 3. 复杂任务：使用编排引擎
                return await self._orchestrate_complex_task(
                    user_input, intent, user_id, session_id, context
                )

        except Exception as e:
            logger.error(f"处理请求失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "处理请求时发生错误，请稍后重试"
            }

    async def _understand_intent(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Intent:
        """
        理解用户意图

        Args:
            user_input: 用户输入
            context: 上下文

        Returns:
            Intent: 识别到的意图
        """
        # 使用编排引擎的意图理解
        request = UserRequest(
            raw_input=user_input,
            user_id=context.get("user_id") if context else None,
            session_id=context.get("session_id") if context else None,
            context=context or {}
        )

        intent = await orchestration_engine.understand_intent(request)
        return intent

    async def _execute_agent_directly(
        self,
        intent: Intent,
        user_input: str,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        直接执行Agent

        Args:
            intent: 意图
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            Dict: 执行结果
        """
        # 从意图中提取Agent名称
        agent_name = intent.parameters.get("agent_name")

        if not agent_name:
            # 尝试从实体中提取
            for entity in intent.entities:
                if entity["type"] == "agent":
                    agent_name = entity["value"]
                    break

        if not agent_name:
            return {
                "success": False,
                "error": "未指定Agent名称",
                "response": "请指定要使用的智能体"
            }

        # 执行Agent
        result = await self.agent_integration.execute_agent(
            agent_name=agent_name,
            input_data=user_input,
            user_id=user_id,
            session_id=session_id,
            parameters=intent.parameters
        )

        return {
            "success": result.success,
            "response": result.output if result.success else result.error,
            "metadata": result.metadata,
            "execution_time_ms": result.execution_time_ms
        }

    async def _execute_capability(
        self,
        intent: Intent,
        user_input: str,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        执行能力

        Args:
            intent: 意图
            user_input: 用户输入
            user_id: 用户ID

        Returns:
            Dict: 执行结果
        """
        capability_name = intent.parameters.get("capability_name")

        if not capability_name:
            return {
                "success": False,
                "error": "未指定能力名称",
                "response": "请指定要执行的能力"
            }

        # 使用能力中心执行
        result = await capability_center.execute_capability(
            name=capability_name,
            input_data=intent.parameters.get("input", user_input),
            user_id=user_id,
            parameters=intent.parameters
        )

        return {
            "success": result.success,
            "response": result.data if result.success else result.error,
            "metadata": {
                "capability_name": capability_name,
                "execution_time_ms": result.execution_time_ms
            }
        }

    async def _orchestrate_complex_task(
        self,
        user_input: str,
        intent: Intent,
        user_id: Optional[str],
        session_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        编排复杂任务

        Args:
            user_input: 用户输入
            intent: 意图
            user_id: 用户ID
            session_id: 会话ID
            context: 上下文

        Returns:
            Dict: 执行结果
        """
        # 创建用户请求
        request = UserRequest(
            raw_input=user_input,
            user_id=user_id,
            session_id=session_id,
            context=context or {}
        )

        # 使用编排引擎处理
        result = await orchestration_engine.orchestrate(request)

        if result.status == "completed":
            return {
                "success": True,
                "response": result.output,
                "metadata": {
                    "execution_time_ms": result.execution_time_ms,
                    "steps_executed": len(result.step_results)
                }
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "response": f"任务执行失败: {result.error}"
            }

    async def stream_process_request(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式处理用户请求

        Args:
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID
            context: 上下文

        Yields:
            str: 流式响应片段
        """
        try:
            # 发送开始标记
            yield "[START]"

            # 理解意图
            yield "正在理解您的意图...\n"
            intent = await self._understand_intent(user_input, context)
            yield f"识别到意图: {intent.intent_type}\n"

            # 根据意图处理
            if intent.intent_type == "agent_execution":
                yield "正在调用智能体...\n"
                result = await self._execute_agent_directly(
                    intent, user_input, user_id, session_id
                )
            elif intent.intent_type == "capability_execution":
                yield "正在执行能力...\n"
                result = await self._execute_capability(
                    intent, user_input, user_id
                )
            else:
                yield "正在编排任务...\n"
                result = await self._orchestrate_complex_task(
                    user_input, intent, user_id, session_id, context
                )

            # 发送结果
            if result["success"]:
                yield f"\n[RESULT]{result['response']}[/RESULT]"
            else:
                yield f"\n[ERROR]{result.get('error', '未知错误')}[/ERROR]"

            # 发送结束标记
            yield "[END]"

        except Exception as e:
            logger.error(f"流式处理失败: {e}", exc_info=True)
            yield f"[ERROR]{str(e)}[/ERROR]"
            yield "[END]"

    def list_available_agents(
        self,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        列出可用的Agent

        Args:
            tags: 标签过滤

        Returns:
            List[Dict]: Agent列表
        """
        return self.agent_integration.list_agents(tags=tags, active_only=True)

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
        return self.agent_integration.find_agents_for_task(
            task_description,
            required_capabilities
        )

    def get_agent_details(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        获取Agent详情

        Args:
            agent_name: Agent名称

        Returns:
            Optional[Dict]: Agent详情
        """
        return self.agent_integration.get_agent_info(agent_name)

    async def execute_agent_directly(
        self,
        agent_name: str,
        input_data: Any,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        直接执行Agent（绕过编排）

        Args:
            agent_name: Agent名称
            input_data: 输入数据
            user_id: 用户ID
            session_id: 会话ID
            parameters: 参数

        Returns:
            AgentResult: 执行结果
        """
        return await self.agent_integration.execute_agent(
            agent_name=agent_name,
            input_data=input_data,
            user_id=user_id,
            session_id=session_id,
            parameters=parameters
        )

    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态

        Returns:
            Dict: 系统状态
        """
        from app.agents.registry import agent_registry

        return {
            "agents": agent_registry.get_registry_stats(),
            "capabilities": capability_center.get_stats(),
            "timestamp": datetime.now().isoformat()
        }


# 服务实例管理
_service_instance: Optional[AgentOrchestrationService] = None


def get_orchestration_service(db: Session) -> AgentOrchestrationService:
    """
    获取编排服务实例

    Args:
        db: 数据库会话

    Returns:
        AgentOrchestrationService: 服务实例
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = AgentOrchestrationService(db)

    return _service_instance
