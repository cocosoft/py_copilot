"""
任务执行追踪服务

复用现有 SkillExecutionLog，不重复存储执行数据
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.task import Task, TaskSkill
from app.models.skill import SkillExecutionLog

logger = logging.getLogger(__name__)


class TaskExecutionTracker:
    """
    任务执行追踪器
    
    设计原则：
    1. 复用现有 SkillExecutionLog，不重复存储
    2. 通过 TaskSkill 关联执行日志
    3. 使用 execution_steps 字段存储执行步骤
    """
    
    def __init__(self, db: Session):
        """
        初始化执行追踪器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def start_trace(self, task_id: int, task_title: str,
                   input_data: Optional[Dict] = None) -> str:
        """
        开始任务执行追踪
        
        Args:
            task_id: 任务ID
            task_title: 任务标题
            input_data: 输入数据
            
        Returns:
            追踪ID
        """
        trace_id = str(uuid.uuid4())
        
        task = self.db.query(Task).filter_by(id=task_id).first()
        if task:
            task.execution_trace_id = trace_id
            self.db.commit()
        
        logger.info(f"任务执行追踪开始: {trace_id} (任务 {task_id})")
        
        return trace_id
    
    def start_node(self, task_skill_id: int) -> None:
        """
        开始执行节点（技能执行）
        
        Args:
            task_skill_id: 任务技能ID
        """
        task_skill = self.db.query(TaskSkill).filter_by(id=task_skill_id).first()
        
        if task_skill:
            task_skill.node_status = "running"
            task_skill.started_at = datetime.utcnow()
            self.db.commit()
            
            logger.debug(f"执行节点开始: 任务技能 {task_skill_id}")
    
    def end_node(self, task_skill_id: int, execution_log_id: int,
                status: str = "completed", error_info: Optional[str] = None):
        """
        结束执行节点
        
        Args:
            task_skill_id: 任务技能ID
            execution_log_id: 关联的执行日志ID
            status: 状态
            error_info: 错误信息
        """
        task_skill = self.db.query(TaskSkill).filter_by(id=task_skill_id).first()
        
        if task_skill:
            task_skill.execution_log_id = execution_log_id
            task_skill.node_status = status
            task_skill.completed_at = datetime.utcnow()
            
            if error_info:
                task_skill.error_message = error_info
            
            self.db.commit()
            
            logger.debug(f"执行节点结束: 任务技能 {task_skill_id} ({status})")
    
    def get_execution_trace(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务执行追踪数据
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行追踪数据
        """
        task = self.db.query(Task).filter_by(id=task_id).first()
        
        if not task or not task.execution_trace_id:
            return None
        
        # 获取任务技能执行信息
        task_skills = self.db.query(TaskSkill).filter_by(
            task_id=task_id
        ).order_by(TaskSkill.execution_order).all()
        
        nodes = []
        for skill in task_skills:
            node_data = {
                'id': skill.id,
                'node_type': 'skill',
                'node_name': skill.skill_name,
                'status': skill.node_status,
                'sequence_number': skill.execution_order,
                'started_at': skill.started_at.isoformat() if skill.started_at else None,
                'completed_at': skill.completed_at.isoformat() if skill.completed_at else None,
                'error_message': skill.error_message,
                'input_data': skill.config or {}
            }
            
            # 如果有关联的执行日志，获取详细信息
            if skill.execution_log_id:
                log = self.db.query(SkillExecutionLog).filter_by(
                    id=skill.execution_log_id
                ).first()
                if log:
                    node_data['execution_log'] = {
                        'id': log.id,
                        'status': log.status,
                        'output_result': log.output_result,
                        'error_message': log.error_message,
                        'execution_time_ms': log.execution_time_ms,
                        'execution_steps': log.execution_steps or [],
                        'artifacts': self._get_artifacts(log)
                    }
                    node_data['output_data'] = log.output_result
            
            nodes.append(node_data)
        
        return {
            'trace_id': task.execution_trace_id,
            'task_id': task.id,
            'task_title': task.title,
            'status': task.status,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'execution_time_ms': task.execution_time_ms,
            'error_message': task.error_message,
            'nodes': nodes
        }
    
    def _get_artifacts(self, log: SkillExecutionLog) -> List[Dict[str, Any]]:
        """
        获取执行日志的产物
        
        Args:
            log: 执行日志对象
            
        Returns:
            产物列表
        """
        artifacts = []
        
        # 检查是否有 artifacts 关系
        if hasattr(log, 'artifacts') and log.artifacts:
            for artifact in log.artifacts:
                artifacts.append({
                    'name': getattr(artifact, 'name', 'unknown'),
                    'type': getattr(artifact, 'type', 'unknown'),
                    'content': getattr(artifact, 'content', None)
                })
        
        return artifacts
    
    def cleanup_old_traces(self, days: int = 30):
        """
        清理旧的执行追踪数据
        
        Args:
            days: 保留天数，默认30天
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 清理旧任务的 execution_trace_id
        old_tasks = self.db.query(Task).filter(
            Task.execution_trace_id.isnot(None),
            Task.completed_at < cutoff_date
        ).all()
        
        for task in old_tasks:
            task.execution_trace_id = None
        
        self.db.commit()
        
        logger.info(f"清理了 {len(old_tasks)} 个旧任务的执行追踪数据")


class TaskExecutionTrackerEventHandler:
    """
    任务执行追踪事件处理器
    
    处理来自 SkillExecutionEngine 的事件
    """
    
    def __init__(self, db: Session):
        self.tracker = TaskExecutionTracker(db)
    
    def on_skill_execution_started(self, task_skill_id: int):
        """技能执行开始事件"""
        self.tracker.start_node(task_skill_id)
    
    def on_skill_execution_completed(self, task_skill_id: int, execution_log_id: int):
        """技能执行完成事件"""
        self.tracker.end_node(task_skill_id, execution_log_id, "completed")
    
    def on_skill_execution_failed(self, task_skill_id: int, execution_log_id: int, error: str):
        """技能执行失败事件"""
        self.tracker.end_node(task_skill_id, execution_log_id, "failed", error)
