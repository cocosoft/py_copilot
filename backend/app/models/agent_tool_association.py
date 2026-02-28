"""智能体与工具关联模型"""
from sqlalchemy import Column, Integer, ForeignKey, Boolean, JSON, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AgentToolAssociation(Base):
    """智能体与工具的关联表"""
    __tablename__ = "agent_tool_associations"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="SET NULL"), nullable=True, index=True)
    priority = Column(Integer, default=0)  # 工具调用优先级
    enabled = Column(Boolean, default=True)  # 是否启用该工具
    config = Column(JSON, default=dict)  # 工具调用配置
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)
    
    # 关系
    agent = relationship("Agent", back_populates="tool_associations")
    tool = relationship("Tool", back_populates="agent_associations")
    
    __table_args__ = (
        UniqueConstraint('agent_id', 'tool_id', name='uq_agent_tool'),
    )
    
    def __repr__(self):
        return f"<AgentToolAssociation(id={self.id}, agent_id={self.agent_id}, tool_id={self.tool_id})>"
