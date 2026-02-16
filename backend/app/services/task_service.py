"""任务管理服务（优化版）"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.task import Task, TaskSkill
from app.services.agent_task_planner import AgentTaskPlanner
from app.services.skill_matching_service import SkillMatchingService

logger = logging.getLogger(__name__)


class TaskService:
    """任务管理服务"""
    
    def __init__(self, db: Session):
        """
        初始化任务管理服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.task_planner = AgentTaskPlanner(db)
        self.skill_matcher = SkillMatchingService(db)
    
    async def analyze_task(self, task: Task) -> Dict[str, Any]:
        """
        分析任务（复用AgentTaskPlanner）
        
        Args:
            task: 任务对象
            
        Returns:
            任务分析结果
        """
        try:
            # 使用AgentTaskPlanner分析任务
            task_plan = self.task_planner.analyze_task(
                task.description,
                task_context={"task_id": task.id}
            )
            
            # 更新任务信息
            task.task_type = task_plan.task_type.value
            task.complexity = task_plan.complexity.value
            task.config = {
                "task_plan": task_plan.dict(),
                "required_capabilities": task_plan.required_capabilities
            }
            
            self.db.commit()
            
            logger.info(f"任务 {task.id} 分析完成: {task.task_type}")
            
            return task_plan.dict()
            
        except Exception as e:
            logger.error(f"任务 {task.id} 分析失败: {e}")
            raise
    
    async def decompose_task(self, task: Task) -> Dict[str, Any]:
        """
        分解任务（暂不实现，待工作流系统完善后集成）
        
        Args:
            task: 任务对象
            
        Returns:
            任务分解结果
        """
        # 如果任务复杂度不是复杂，不需要分解
        if task.complexity != "complex":
            return {
                "subtasks": [],
                "requires_decomposition": False
            }
        
        # TODO: 待工作流系统完善后，集成WorkflowAutoComposer
        logger.info(f"任务 {task.id} 分解功能待实现")
        
        return {
            "subtasks": [],
            "requires_decomposition": True,
            "message": "任务分解功能待工作流系统完善后实现"
        }
    
    async def match_skills(self, task: Task) -> List[Dict[str, Any]]:
        """
        匹配技能（复用SkillMatchingService）
        
        Args:
            task: 任务对象
            
        Returns:
            技能匹配结果
        """
        try:
            # 使用SkillMatchingService匹配技能
            matched_skills = self.skill_matcher.match_skills(
                task.description,
                limit=10
            )
            
            # 创建任务技能关联
            task_skills = []
            for index, skill in enumerate(matched_skills, start=1):
                # 自动设置技能配置参数
                config = {}
                
                # 根据技能类型设置不同的参数
                if skill.name == "translate":
                    # 翻译技能：使用任务描述作为输入文本
                    config = {
                        "text": task.description,
                        "target_language": "English"  # 默认翻译为英语
                    }
                elif skill.name == "summarize":
                    # 摘要技能：使用任务描述作为输入文本
                    config = {
                        "text": task.description,
                        "max_length": 200
                    }
                elif skill.name == "analyze":
                    # 分析技能：使用任务描述作为输入文本
                    config = {
                        "text": task.description
                    }
                else:
                    # 通用技能：使用任务描述作为上下文
                    config = {
                        "user_input": task.description
                    }
                
                task_skill = TaskSkill(
                    task_id=task.id,
                    skill_id=skill.id,
                    skill_name=skill.name,
                    execution_order=index,
                    status="pending",
                    config=config
                )
                self.db.add(task_skill)
                task_skills.append({
                    "skill_id": skill.id,
                    "skill_name": skill.name,
                    "execution_order": index,
                    "config": config
                })
            
            self.db.commit()
            
            logger.info(f"任务 {task.id} 匹配到 {len(matched_skills)} 个技能")
            
            return task_skills
            
        except Exception as e:
            logger.error(f"任务 {task.id} 技能匹配失败: {e}")
            raise
    
    async def execute_task(self, task_id: int, user_id: int) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            执行结果
        """
        # 导入任务协调器
        from app.services.task_coordinator import TaskCoordinator
        
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 创建任务协调器
        coordinator = TaskCoordinator(self.db)
        
        # 执行任务
        result = await coordinator.coordinate_execution(task)
        
        return result
    
    def get_task_progress(self, task_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取任务进度
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            任务进度
        """
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 获取任务技能执行状态
        task_skills = self.db.query(TaskSkill).filter(
            TaskSkill.task_id == task_id
        ).all()
        
        # 计算进度
        total_skills = len(task_skills)
        completed_skills = sum(1 for ts in task_skills if ts.status == "completed")
        progress = int((completed_skills / total_skills) * 100) if total_skills > 0 else 0
        
        return {
            "task_id": task_id,
            "status": task.status,
            "progress": progress,
            "total_skills": total_skills,
            "completed_skills": completed_skills,
            "started_at": task.started_at,
            "completed_at": task.completed_at
        }
    
    def cancel_task(self, task_id: int, user_id: int) -> Dict[str, Any]:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            取消结果
        """
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 更新任务状态
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()
        
        # 更新任务技能状态
        self.db.query(TaskSkill).filter(
            TaskSkill.task_id == task_id,
            TaskSkill.status == "pending"
        ).update({"status": "cancelled"})
        
        self.db.commit()
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "任务已取消"
        }
