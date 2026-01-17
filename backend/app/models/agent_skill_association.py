"""智能体与技能关联模型"""
from sqlalchemy import Column, Integer, ForeignKey, Boolean, JSON, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AgentSkillAssociation(Base):
    """智能体与技能的关联表"""
    __tablename__ = "agent_skill_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    priority = Column(Integer, default=0)  # 技能调用优先级
    enabled = Column(Boolean, default=True)  # 是否启用该技能
    config = Column(JSON, default=dict)  # 技能调用配置
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)
    
    agent = relationship("Agent", backref="skill_associations")
    skill = relationship("Skill", backref="agent_associations")
    
    __table_args__ = (
        UniqueConstraint('agent_id', 'skill_id', name='uq_agent_skill'),
    )
    
    def __repr__(self):
        return f"<AgentSkillAssociation(id={self.id}, agent_id={self.agent_id}, skill_id={self.skill_id})>"
