"""模型分类相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelCategory(Base):
    """模型分类表模型"""
    __tablename__ = "model_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 分类名称，如 task_type, size
    display_name = Column(String(100), nullable=False)  # 显示名称，如 任务类型, 规模
    description = Column(Text, nullable=True)  # 分类描述
    

    
    # 父分类ID，支持层级分类
    parent_id = Column(Integer, ForeignKey("model_categories.id"), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # LOGO信息
    logo = Column(Text, nullable=True)  # SVG格式的logo数据
    
    # 默认参数配置（JSON格式）
    default_parameters = Column(JSON, nullable=True, default={})
    
    # 分类权重（用于排序和优先级）
    weight = Column(Integer, default=0)
    
    # 分类维度标识（支持多维分类）
    dimension = Column(String(50), nullable=False, default="task_type")  # 设置默认维度
    
    # 添加表约束
    __table_args__ = (
        # 保留原有的全局唯一约束
        UniqueConstraint('name', name='_name_uc'),
        # 新增的联合唯一约束：同一维度下分类名称唯一
        UniqueConstraint('dimension', 'name', name='_dimension_name_uc'),
    )
    
    # 关系定义
    # 自引用关系，用于层级分类
    parent = relationship("ModelCategory", remote_side=[id], backref="children")
    
    # 与模型的关系
    model_db = relationship("ModelDB", back_populates="model_type")
    
    # 与模型的多对多关系
    models = relationship(
        "ModelDB",
        secondary="model_category_associations",
        back_populates="categories"
    )
    
    # 与关联表的关系
    model_associations = relationship("ModelCategoryAssociation", back_populates="category")
    
    # 与旧模型的关系（已废弃，已移除LegacyModel依赖）
    # legacy_models = relationship("LegacyModel", back_populates="model_type")
    
    def __repr__(self):
        return f"<ModelCategory(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


# 创建模型和分类之间的多对多关联表
class ModelCategoryAssociation(Base):
    """模型和分类的多对多关联表"""
    __tablename__ = "model_category_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("model_categories.id", ondelete="CASCADE"), nullable=False)
    
    # 关联权重（用于多维分类中的优先级）
    weight = Column(Integer, default=0)
    
    # 关联类型（主要关联、次要关联等）
    association_type = Column(String(20), default="primary")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系定义
    model = relationship("ModelDB", back_populates="category_associations")
    category = relationship("ModelCategory", back_populates="model_associations")
    
    def __repr__(self):
        return f"<ModelCategoryAssociation(id={self.id}, model_id={self.model_id}, category_id={self.category_id})>"