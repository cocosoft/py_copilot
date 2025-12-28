"""能力版本管理相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelCapabilityVersion(Base):
    """模型能力版本表模型"""
    __tablename__ = "model_capability_versions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    capability_id = Column(Integer, ForeignKey("model_capabilities.id", ondelete="CASCADE"), nullable=False)
    
    # 版本号（如：1.0.0, 1.1.0）
    version = Column(String(20), nullable=False)
    
    # 版本描述（记录版本变更内容）
    version_description = Column(Text, nullable=True)
    
    # 以下字段与ModelCapability保持一致，用于完整记录每个版本的状态
    name = Column(String(100), nullable=False)  # 能力名称
    display_name = Column(String(100), nullable=False)  # 显示名称
    description = Column(Text, nullable=True)  # 能力描述
    
    # 能力维度
    capability_dimension = Column(String(50), nullable=False, default="generation")
    capability_subdimension = Column(String(50), nullable=True)
    
    # 能力强度量化
    base_strength = Column(Integer, default=3)
    max_strength = Column(Integer, default=5)
    
    # 能力评估指标
    assessment_metrics = Column(JSON, nullable=True)
    benchmark_datasets = Column(JSON, nullable=True)
    
    # 能力依赖关系
    dependencies = Column(JSON, nullable=True)
    
    # 能力类型
    capability_type = Column(String(50), default="standard", nullable=False)
    
    # 支持的输入输出类型
    input_types = Column(JSON, nullable=True)
    output_types = Column(JSON, nullable=True)
    
    # 能力领域
    domain = Column(String(50), nullable=False, default="nlp")
    
    # 是否为当前活跃版本
    is_current = Column(Boolean, default=False)
    
    # 是否为稳定版本
    is_stable = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 创建人（可以扩展为用户外键）
    created_by = Column(String(100), nullable=True)
    
    # 关系定义
    capability = relationship("ModelCapability", back_populates="versions")
    
    def __repr__(self):
        return f"<ModelCapabilityVersion(id={self.id}, capability_id={self.capability_id}, version='{self.version}', is_current={self.is_current})>"
