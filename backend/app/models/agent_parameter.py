"""智能体参数数据库模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AgentParameter(Base):
    """智能体参数表"""
    __tablename__ = "agent_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    parameter_value = Column(Text, nullable=False)
    parameter_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    parameter_group = Column(String(50), nullable=True)
    
    # 参数来源字段
    source = Column(String(20), default="agent")
    inherited = Column(Boolean, default=False)
    inherited_from = Column(String(100), nullable=True)
    
    # 参数版本字段
    version = Column(String(50), default="1.0.0")
    
    # 参数约束字段
    constraints = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    agent = relationship("Agent", back_populates="parameters")
    
    __table_args__ = (
        UniqueConstraint('agent_id', 'parameter_name', name='uq_agent_parameter_name'),
    )
    
    def __repr__(self):
        return f"<AgentParameter(id={self.id}, agent_id={self.agent_id}, name='{self.parameter_name}')>"
