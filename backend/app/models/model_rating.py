"""模型评分相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

from app.core.database import Base


class RatingDimension(Base):
    """评分维度表模型"""
    __tablename__ = "rating_dimensions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 维度名称，如 accuracy, performance, usability
    display_name = Column(String(100), nullable=False)  # 显示名称，如 准确性, 性能, 可用性
    description = Column(Text, nullable=True)  # 维度描述
    category = Column(String(50), default="general", nullable=False)  # 维度分类，如 general, technical, business
    weight = Column(DECIMAL(5,2), default=1.0, nullable=False)  # 权重（用于综合评分计算）
    is_active = Column(Boolean, default=True)  # 是否激活
    is_system = Column(Boolean, default=False)  # 是否为系统维度（不可删除）
    order_index = Column(Integer, default=0)  # 排序索引
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    ratings = relationship("ModelRating", back_populates="dimension")
    
    def __repr__(self):
        return f"<RatingDimension(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class ModelRating(Base):
    """模型评分表模型"""
    __tablename__ = "model_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)  # 关联的模型ID
    dimension_id = Column(Integer, ForeignKey("rating_dimensions.id", ondelete="CASCADE"), nullable=False)  # 关联的评分维度ID
    
    # 评分信息
    score = Column(Integer, nullable=False)  # 评分（1-5）
    score_detail = Column(Text, nullable=True)  # 评分详情（文本形式）
    
    # 评分来源信息
    user_id = Column(String(100), nullable=True)  # 用户ID（可为空，表示系统评分）
    source = Column(String(50), default="system", nullable=False)  # 评分来源（system, user, benchmark）
    reference_id = Column(String(100), nullable=True)  # 参考标识（如基准测试ID等）
    
    # 评分元数据
    metadata = Column(Text, nullable=True)  # 评分元数据（JSON格式）
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    dimension = relationship("RatingDimension", back_populates="ratings")
    
    # 唯一约束 - 确保每个模型在每个维度只有一个评分记录
    __table_args__ = (
        UniqueConstraint('model_id', 'dimension_id', name='uq_model_dimension'),
    )
    
    def __repr__(self):
        return f"<ModelRating(id={self.id}, model_id={self.model_id}, dimension_id={self.dimension_id}, score={self.score})>"