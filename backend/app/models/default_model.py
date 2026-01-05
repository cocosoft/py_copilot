"""默认模型管理数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class DefaultModel(Base):
    """默认模型配置"""
    __tablename__ = "default_models"
    
    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(50), nullable=False, default="global")  # 默认作用域：global（全局）、scene（场景）
    scene = Column(String(100), nullable=True)  # 场景名称，当scope为scene时使用
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)  # 默认模型ID
    priority = Column(Integer, nullable=False, default=1)  # 模型优先级，数字越小优先级越高
    fallback_model_id = Column(Integer, ForeignKey("models.id", ondelete="SET NULL"), nullable=True)  # 备选模型ID
    parameter_template_id = Column(Integer, ForeignKey("parameter_templates.id", ondelete="SET NULL"), nullable=True)  # 参数模板ID
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    model = relationship("ModelDB", foreign_keys=[model_id], back_populates="default_models")
    fallback_model = relationship("ModelDB", foreign_keys=[fallback_model_id])
    parameter_template = relationship("ParameterTemplate", back_populates="default_models")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('scope', 'scene', name='uq_scope_scene'),
    )


class ModelFeedback(Base):
    """模型反馈表，用于存储用户对模型的反馈"""
    __tablename__ = "model_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    scene = Column(String(100), nullable=False)
    user_id = Column(String(100), nullable=True)
    rating = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=True)
    usage_context = Column(Text, nullable=True)  # JSON字符串
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    model = relationship("ModelDB", back_populates="model_feedback")


class ModelPerformance(Base):
    """模型性能表，用于存储模型在不同场景下的性能数据"""
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    scene = Column(String(100), nullable=False)
    avg_response_time = Column(DECIMAL(10,3), nullable=True)  # 平均响应时间（秒）
    success_rate = Column(DECIMAL(5,2), nullable=True)  # 成功率（百分比）
    quality_score = Column(Integer, nullable=True)  # 质量评分（1-5）
    usage_count = Column(Integer, nullable=False, default=0)  # 使用次数
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系定义
    model = relationship("ModelDB", back_populates="model_performance")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('model_id', 'scene', name='uq_model_scene'),
    )