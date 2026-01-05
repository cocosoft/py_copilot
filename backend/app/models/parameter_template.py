"""参数模板管理数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ParameterTemplate(Base):
    """参数模板"""
    __tablename__ = "parameter_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 模板名称
    description = Column(Text, nullable=True)  # 模板描述
    scene = Column(String(100), nullable=False)  # 适用场景
    is_default = Column(Boolean, nullable=False, default=False)  # 是否为该场景的默认模板
    parameters = Column(JSON, nullable=False)  # 参数配置，JSON格式存储
    is_active = Column(Boolean, nullable=False, default=True)  # 是否激活
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    models = relationship("ModelDB", back_populates="parameter_template", lazy='select')
    default_models = relationship("DefaultModel", back_populates="parameter_template")
    versions = relationship("ParameterTemplateVersion", back_populates="template", cascade="all, delete-orphan")
    
    # 唯一约束
    __table_args__ = (
        # 确保每个场景只有一个默认模板
        # 注意：如果使用SQLite，需要特殊处理唯一约束
    )


class ParameterTemplateVersion(Base):
    """参数模板版本"""
    __tablename__ = "parameter_template_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("parameter_templates.id", ondelete="CASCADE"), nullable=False)  # 关联模板ID
    version = Column(Integer, nullable=False)  # 版本号
    parameters = Column(JSON, nullable=False)  # 参数配置，JSON格式存储
    changelog = Column(Text, nullable=True)  # 版本变更说明
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    template = relationship("ParameterTemplate", back_populates="versions")
    
    # 唯一约束
    __table_args__ = (
        # 确保每个模板的版本号唯一
    )