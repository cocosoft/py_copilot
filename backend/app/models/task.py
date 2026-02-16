"""任务数据模型（优化版）"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Task(Base):
    """任务表模型（简化版）"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 任务分析结果（复用AgentTaskPlanner）
    task_type = Column(String(50))
    complexity = Column(String(20))
    
    # 任务状态
    status = Column(String(20), nullable=False, default="pending")
    priority = Column(String(20), default="medium")
    
    # 任务配置
    config = Column(JSON)
    
    # 任务输入
    input_data = Column(Text)
    
    # 工作目录
    working_directory = Column(String(500))
    
    # 系统命令执行
    execute_command = Column(Boolean, default=False)
    command = Column(Text)
    
    # 任务输出
    output_data = Column(Text)
    execution_summary = Column(Text)
    
    # 执行信息
    execution_time_ms = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 错误信息
    error_message = Column(Text)
    
    # 关联信息
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    workflow_id = Column(Integer)  # 工作流ID（暂不使用外键，待workflows表创建后再关联）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系定义
    user = relationship("User", backref="tasks")
    conversation = relationship("Conversation", backref="tasks")
    agent = relationship("Agent", backref="tasks")
    task_skills = relationship("TaskSkill", back_populates="task", cascade="all, delete-orphan")


class TaskSkill(Base):
    """任务技能关联表模型"""
    __tablename__ = "task_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    skill_id = Column(Integer)
    skill_name = Column(String(100), nullable=False)
    
    # 调用配置
    execution_order = Column(Integer, nullable=False)
    config = Column(JSON)
    
    # 执行状态
    status = Column(String(20), default="pending")
    
    # 执行结果
    result_data = Column(Text)
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系定义
    task = relationship("Task", back_populates="task_skills")
