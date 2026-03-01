"""
编排服务

本模块提供智能编排的业务逻辑服务
"""

import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import asyncio
import json

from sqlalchemy.orm import Session

from app.capabilities.center.unified_center import UnifiedCapabilityCenter
from app.capabilities.orchestration.intent_understanding import IntentUnderstanding, IntentResult
from app.capabilities.orchestration.task_planner import TaskPlanner, TaskPlan
from app.capabilities.orchestration.orchestrator import Orchestrator, OrchestrationResult
from app.capabilities.orchestration.context_manager import ContextManager
from app.capabilities.types import ExecutionContext

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    编排服务

    提供智能编排的完整业务逻辑，包括：
    - 意图理解和任务规划
    - 任务执行和监控
    - 上下文管理
    - 结果处理

    Attributes:
        _center: 统一能力中心
        _intent_understanding: 意图理解器
        _task_planner: 任务规划器
        _orchestrator: 编排执行器
        _context_manager: 上下文管理器
        _db: 数据库会话
    """

    def __init__(self,
                 center: UnifiedCapabilityCenter,
                 db: Session):
        """
        初始化编排服务

        Args:
            center: 统一能力中心
            db: 数据库会话
        """
        self._center = center
        self._db = db
        self._intent_understanding = IntentUnderstanding(center)
        self._task_planner = TaskPlanner(center)
        self._orchestrator = Orchestrator(center)
        self._context_manager = ContextManager()

        # 注册编排事件处理器
        self._register_event_handlers()

        logger.info("编排服务已创建")

    def _register_event_handlers(self):
        """注册编排事件处理器"""
        self._orchestrator.on('task_started', self._on_task_started)
        self._orchestrator.on('task_completed', self._on_task_completed)
        self._orchestrator.on('task_failed', self._on_task_failed)
        self._orchestrator.on('plan_completed', self._on_plan_completed)
        self._orchestrator.on('plan_failed', self._on_plan_failed)

    def _on_task_started(self, data: Dict[str, Any]):
        """任务开始事件处理器"""
        task = data.get('task')
        if task:
            logger.info(f"任务开始: {task.name}")

    def _on_task_completed(self, data: Dict[str, Any]):
        """任务完成事件处理器"""
        task = data.get('task')
        result = data.get('result')
        if task:
            logger.info(f"任务完成: {task.name}, 输出: {result.output if result else None}")

    def _on_task_failed(self, data: Dict[str, Any]):
        """任务失败事件处理器"""
        task = data.get('task')
        if task:
            logger.warning(f"任务失败: {task.name}, 错误: {task.error}")

    def _on_plan_completed(self, data: Dict[str, Any]):
        """计划完成事件处理器"""
        plan = data.get('plan')
        result = data.get('result')
        if plan:
            logger.info(f"计划完成: {plan.id}, 成功: {result.success if result else False}")

    def _on_plan_failed(self, data: Dict[str, Any]):
        """计划失败事件处理器"""
        plan = data.get('plan')
        result = data.get('result')
        if plan:
            logger.error(f"计划失败: {plan.id}, 错误: {result.error if result else 'Unknown'}")

    async def process_request(self,
                             user_input: str,
                             conversation_id: Optional[str] = None,
                             user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        处理用户请求

        Args:
            user_input: 用户输入
            conversation_id: 对话ID
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"处理请求: {user_input[:50]}...")

        # 1. 获取或创建对话上下文
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        conversation = self._context_manager.get_conversation(conversation_id)
        if not conversation:
            conversation = self._context_manager.create_conversation(
                conversation_id=conversation_id,
                user_id=user_id
            )

        # 2. 添加用户消息
        self._context_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=user_input
        )

        # 3. 理解意图
        intent_result = await self._intent_understanding.understand(
            user_input=user_input,
            conversation_context=conversation.to_dict()
        )

        # 4. 检查是否需要澄清
        if intent_result.clarification_needed:
            response = {
                "type": "clarification",
                "conversation_id": conversation_id,
                "message": "我需要更多信息来理解您的请求",
                "suggested_questions": intent_result.suggested_questions
            }

            # 添加助手消息
            self._context_manager.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response["message"]
            )

            return response

        # 5. 创建任务计划
        task_plan = await self._task_planner.create_plan(intent_result)

        # 6. 优化计划
        task_plan = self._task_planner.optimize_plan(task_plan)

        # 7. 执行计划
        execution_context = ExecutionContext(
            conversation_id=conversation_id,
            user_id=user_id
        )

        orchestration_result = await self._orchestrator.execute(
            plan=task_plan,
            context=execution_context
        )

        # 8. 构建响应
        if orchestration_result.success:
            response_content = self._format_success_response(
                intent_result,
                task_plan,
                orchestration_result
            )
        else:
            response_content = self._format_error_response(
                intent_result,
                task_plan,
                orchestration_result
            )

        # 9. 添加助手消息
        self._context_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_content,
            metadata={
                "plan_id": task_plan.id,
                "intent_type": intent_result.intent_type.value,
                "success": orchestration_result.success
            }
        )

        response = {
            "type": "response",
            "conversation_id": conversation_id,
            "message": response_content,
            "intent": {
                "type": intent_result.intent_type.value,
                "confidence": intent_result.confidence,
                "capabilities": intent_result.capabilities
            },
            "plan": {
                "id": task_plan.id,
                "task_count": len(task_plan.tasks),
                "success": orchestration_result.success
            },
            "execution_time_ms": orchestration_result.total_execution_time_ms
        }

        logger.info(f"请求处理完成: {conversation_id}")

        return response

    async def process_request_stream(self,
                                    user_input: str,
                                    conversation_id: Optional[str] = None,
                                    user_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        流式处理用户请求

        Args:
            user_input: 用户输入
            conversation_id: 对话ID
            user_id: 用户ID

        Yields:
            str: SSE格式的数据
        """
        logger.info(f"流式处理请求: {user_input[:50]}...")

        # 1. 获取或创建对话上下文
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 发送开始事件
        yield self._sse_event("start", {"conversation_id": conversation_id})

        try:
            # 2. 理解意图
            intent_result = await self._intent_understanding.understand(user_input)

            yield self._sse_event("intent", {
                "type": intent_result.intent_type.value,
                "confidence": intent_result.confidence,
                "capabilities": intent_result.capabilities
            })

            # 3. 检查是否需要澄清
            if intent_result.clarification_needed:
                yield self._sse_event("clarification", {
                    "questions": intent_result.suggested_questions
                })
                yield self._sse_event("end", {})
                return

            # 4. 创建任务计划
            task_plan = await self._task_planner.create_plan(intent_result)

            yield self._sse_event("plan", {
                "id": task_plan.id,
                "task_count": len(task_plan.tasks)
            })

            # 5. 执行计划（带进度更新）
            execution_context = ExecutionContext(
                conversation_id=conversation_id,
                user_id=user_id
            )

            # 注册进度回调
            progress_events = []

            def on_progress(data):
                progress_events.append(data)

            self._orchestrator.on('task_started', on_progress)
            self._orchestrator.on('task_completed', on_progress)

            orchestration_result = await self._orchestrator.execute(
                plan=task_plan,
                context=execution_context
            )

            # 发送进度事件
            for event in progress_events:
                yield self._sse_event("progress", event)

            # 6. 发送结果
            if orchestration_result.success:
                yield self._sse_event("result", {
                    "success": True,
                    "output": orchestration_result.output
                })
            else:
                yield self._sse_event("error", {
                    "message": orchestration_result.error or "执行失败"
                })

        except Exception as e:
            logger.error(f"流式处理失败: {e}", exc_info=True)
            yield self._sse_event("error", {"message": str(e)})

        finally:
            yield self._sse_event("end", {})

    def _sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        构建SSE事件

        Args:
            event_type: 事件类型
            data: 事件数据

        Returns:
            str: SSE格式字符串
        """
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _format_success_response(self,
                                intent_result: IntentResult,
                                task_plan: TaskPlan,
                                orchestration_result: OrchestrationResult) -> str:
        """
        格式化成功响应

        Args:
            intent_result: 意图结果
            task_plan: 任务计划
            orchestration_result: 编排结果

        Returns:
            str: 响应内容
        """
        output = orchestration_result.output

        if isinstance(output, str):
            return output
        elif isinstance(output, dict):
            return json.dumps(output, ensure_ascii=False)
        elif output is not None:
            return str(output)
        else:
            return "任务执行完成"

    def _format_error_response(self,
                              intent_result: IntentResult,
                              task_plan: TaskPlan,
                              orchestration_result: OrchestrationResult) -> str:
        """
        格式化错误响应

        Args:
            intent_result: 意图结果
            task_plan: 任务计划
            orchestration_result: 编排结果

        Returns:
            str: 响应内容
        """
        error_msg = orchestration_result.error or "执行过程中发生错误"
        return f"抱歉，{error_msg}"

    def get_conversation_history(self,
                                conversation_id: str,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取对话历史

        Args:
            conversation_id: 对话ID
            limit: 消息数量限制

        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        return self._context_manager.get_conversation_history(conversation_id, limit)

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        清空对话

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 是否成功
        """
        conversation = self._context_manager.get_conversation(conversation_id)
        if conversation:
            conversation.clear_messages()
            return True
        return False

    def get_execution_status(self) -> Dict[str, Any]:
        """
        获取执行状态

        Returns:
            Dict[str, Any]: 状态信息
        """
        progress = self._orchestrator.get_progress()
        current_plan = self._orchestrator.get_current_plan()

        return {
            "status": self._orchestrator.get_status().value,
            "is_running": self._orchestrator.get_status().value == "running",
            "progress": progress,
            "current_plan_id": current_plan.id if current_plan else None
        }

    def cancel_execution(self) -> bool:
        """
        取消当前执行

        Returns:
            bool: 是否成功取消
        """
        if self._orchestrator.get_status().value == "running":
            self._orchestrator.cancel()
            return True
        return False

    def get_service_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "context_manager": self._context_manager.get_stats(),
            "orchestrator": {
                "status": self._orchestrator.get_status().value,
                "max_parallel": self._orchestrator._max_parallel
            }
        }
