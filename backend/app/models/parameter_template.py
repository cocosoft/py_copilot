"""参数模板数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.supplier_db import ModelDB


class ParameterTemplate(Base):
    """参数模板数据库模型，用于支持分层参数管理"""
    __tablename__ = "parameter_templates"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # 模板名称
    description = Column(Text, nullable=True)  # 模板描述
    level = Column(String(50), nullable=False)  # 层级：system|supplier|model_type|model_capability|model|agent
    parent_id = Column(Integer, ForeignKey("parameter_templates.id", ondelete="SET NULL"), nullable=True)  # 父模板ID
    level_id = Column(Integer, nullable=True)  # 层级特定ID（如供应商ID、模型类型ID等）
    parameters = Column(JSON, nullable=False)  # 参数列表，使用JSON类型存储
    version = Column(String(50), default="1.0.0")  # 模板版本
    is_active = Column(Boolean, default=True)  # 是否激活
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    parent = relationship("ParameterTemplate", remote_side=[id], backref="children")
    
    # 与模型的关系，一个模板可以应用于多个模型
    models = relationship("ModelDB", back_populates="parameter_template")
