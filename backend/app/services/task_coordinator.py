"""任务执行协调器（优化版）"""
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.task import Task, TaskSkill
from app.services.skill_execution_engine import SkillExecutionEngine

logger = logging.getLogger(__name__)


class TaskCoordinator:
    """任务执行协调器"""
    
    def __init__(self, db: Session):
        """
        初始化任务执行协调器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.skill_engine = SkillExecutionEngine(db)
    
    async def coordinate_execution(self, task: Task) -> Dict[str, Any]:
        """
        协调任务执行
        
        Args:
            task: 任务对象
            
        Returns:
            执行结果
        """
        try:
            # 更新任务状态为执行中
            task.status = "running"
            task.started_at = datetime.utcnow()
            self.db.commit()
            
            # 检查是否需要执行系统命令
            if task.execute_command and task.command:
                command_result = await self._execute_command(task)
                if not command_result["success"]:
                    # 命令执行失败，更新任务状态
                    task.status = "failed"
                    task.error_message = command_result["stderr"]
                    task.completed_at = datetime.utcnow()
                    self.db.commit()
                    raise Exception(f"命令执行失败: {command_result['stderr']}")
                
                # 将命令执行结果添加到任务输出
                task.output_data = f"=== 命令执行结果 ===\n{command_result['stdout']}\n"
                if command_result["stderr"]:
                    task.output_data += f"=== 命令执行错误 ===\n{command_result['stderr']}\n"
            
            # 获取任务技能
            task_skills = self.db.query(TaskSkill).filter(
                TaskSkill.task_id == task.id
            ).order_by(TaskSkill.execution_order).all()
            
            if not task_skills:
                # 如果没有技能，但有命令执行，直接返回命令执行结果
                if task.execute_command and task.command:
                    task.status = "completed"
                    task.completed_at = datetime.utcnow()
                    task.execution_summary = "命令执行完成"
                    
                    if task.started_at:
                        execution_time = (task.completed_at - task.started_at).total_seconds()
                        task.execution_time_ms = int(execution_time * 1000)
                    
                    self.db.commit()
                    return {"success": True, "output": task.output_data}
                else:
                    raise ValueError(f"任务 {task.id} 没有关联的技能")
            
            # 执行技能链
            results = []
            for task_skill in task_skills:
                result = await self._execute_skill(task, task_skill)
                results.append(result)
            
            # 导入结果整合服务
            from app.services.task_result_integrator import TaskResultIntegrator
            
            # 整合结果
            integrator = TaskResultIntegrator(self.db)
            integrated_result = await integrator.integrate_results(task, results)
            
            # 更新任务状态为完成
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            
            # 合并命令执行结果和技能执行结果
            if task.output_data:
                task.output_data += f"\n=== 技能执行结果 ===\n{str(integrated_result)}"
            else:
                task.output_data = str(integrated_result)
            
            task.execution_summary = f"任务执行完成"
            if task.execute_command and task.command:
                task.execution_summary += f"，包含命令执行和 {len(results)} 个技能"
            else:
                task.execution_summary += f"，共执行 {len(results)} 个技能"
            
            if task.started_at:
                execution_time = (task.completed_at - task.started_at).total_seconds()
                task.execution_time_ms = int(execution_time * 1000)
            
            self.db.commit()
            
            logger.info(f"任务 {task.id} 执行完成")
            
            return integrated_result
            
        except Exception as e:
            logger.error(f"任务 {task.id} 执行失败: {e}")
            
            # 更新任务状态为失败
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            self.db.commit()
            
            raise
    
    async def _execute_skill(self, task: Task, task_skill: TaskSkill) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            task: 任务对象
            task_skill: 任务技能对象
            
        Returns:
            执行结果
        """
        try:
            # 更新技能状态为执行中
            task_skill.status = "running"
            self.db.commit()
            
            # 执行技能
            execution_log = await self.skill_engine.execute_skill(
                skill_id=task_skill.skill_id,
                user_id=task.user_id,
                params=task_skill.config or {},
                context={
                    "task_id": task.id,
                    "task_description": task.description
                }
            )
            
            # 更新技能状态
            if execution_log.status == "completed":
                task_skill.status = "completed"
                task_skill.result_data = execution_log.output_result
            else:
                task_skill.status = "failed"
                task_skill.error_message = execution_log.error_message
            
            self.db.commit()
            
            logger.info(f"任务 {task.id} 技能 {task_skill.skill_name} 执行完成")
            
            return {
                "skill_name": task_skill.skill_name,
                "status": task_skill.status,
                "result": execution_log.output_result,
                "error": task_skill.error_message
            }
            
        except Exception as e:
            logger.error(f"任务 {task.id} 技能 {task_skill.skill_name} 执行失败: {e}")
            
            # 更新技能状态为失败
            task_skill.status = "failed"
            task_skill.error_message = str(e)
            self.db.commit()
            
            raise
    
    async def _execute_command(self, task: Task) -> Dict[str, Any]:
        """
        执行系统命令
        
        Args:
            task: 任务对象
            
        Returns:
            执行结果
        """
        try:
            from app.services.command_execution_service import CommandExecutionService
            
            command_service = CommandExecutionService()
            
            # 验证命令安全性
            if not command_service.validate_command(task.command):
                raise ValueError("命令包含危险操作，已被拒绝执行")
            
            # 执行命令
            result = await command_service.execute_command(
                command=task.command,
                working_directory=task.working_directory,
                timeout=300  # 5分钟超时
            )
            
            logger.info(f"任务 {task.id} 命令执行完成: {task.command}")
            
            return result
            
        except Exception as e:
            logger.error(f"任务 {task.id} 命令执行失败: {e}")
            raise
