"""
任务数据清理服务

定期清理旧的执行追踪数据（保留30天）
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.task import Task
from app.services.task_execution_tracker import TaskExecutionTracker

logger = logging.getLogger(__name__)


class TaskCleanupService:
    """任务数据清理服务"""
    
    def __init__(self, db: Session):
        """
        初始化清理服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.tracker = TaskExecutionTracker(db)
    
    def cleanup_old_execution_traces(self, days: int = 30):
        """
        清理旧的执行追踪数据
        
        Args:
            days: 保留天数，默认30天
        """
        try:
            self.tracker.cleanup_old_traces(days)
            logger.info(f"执行追踪数据清理完成（保留 {days} 天）")
        except Exception as e:
            logger.error(f"执行追踪数据清理失败: {e}")
    
    def cleanup_old_tasks(self, days: int = 90):
        """
        清理旧的任务数据（软删除或归档）
        
        Args:
            days: 保留天数，默认90天
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_tasks = self.db.query(Task).filter(
            Task.status.in_(['completed', 'failed', 'cancelled']),
            Task.completed_at < cutoff_date
        ).all()
        
        # 这里可以实现归档逻辑，暂时只记录日志
        logger.info(f"发现 {len(old_tasks)} 个旧任务需要清理（超过 {days} 天）")
