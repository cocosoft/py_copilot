"""参数模板数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func, JSON, ForeignKey
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
    level = Column(String(50), nullable=False, default="system")  # 模板层级：system|model_type|model|agent
    
    # 与能力维度的关联
    # dimension_id = Column(Integer, ForeignKey("capability_dimensions.id"), nullable=True)
    # subdimension_id = Column(Integer, ForeignKey("capability_subdimensions.id"), nullable=True)
    # capability_id = Column(Integer, ForeignKey("model_capabilities.id"), nullable=True)
    
    # 版本管理
    version = Column(String(20), nullable=False, default="1.0.0")
    level_id = Column(Integer, nullable=True)  # 层级特定ID
    parent_id = Column(Integer, ForeignKey("parameter_templates.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    models = relationship("ModelDB", back_populates="parameter_template", lazy='select')
    
    # 能力维度关系
    # dimension = relationship("CapabilityDimension", backref="parameter_templates")
    # subdimension = relationship("CapabilitySubdimension", backref="parameter_templates")
    # capability = relationship("ModelCapability", backref="parameter_templates")  # 已注释，因为没有对应的外键
    
    # 模板继承关系
    parent = relationship("ParameterTemplate", remote_side=[id], backref="children")
