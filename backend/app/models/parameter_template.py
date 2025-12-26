"""参数模板数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ParameterTemplate(Base):
    """参数模板数据库模型，用于系统级默认参数管理
    
    说明：原设计支持多级参数模板（system|supplier|model_type|model_capability|model|agent），
    现简化为仅支持系统级默认参数，模型级和智能体级参数分别通过 ModelParameter 和 AgentParameter 管理。
    """
    __tablename__ = "parameter_templates"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    models = relationship("ModelDB", back_populates="parameter_template", lazy='select')
