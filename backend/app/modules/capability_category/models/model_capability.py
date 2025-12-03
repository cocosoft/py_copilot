"""模型能力相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelCapability(Base):
    """模型能力表模型"""
    __tablename__ = "model_capabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 能力名称，如 text_generation, translation
    display_name = Column(String(100), nullable=False)  # 显示名称，如 文本生成, 翻译
    description = Column(Text, nullable=True)  # 能力描述
    
    # 能力类型
    capability_type = Column(String(50), default="standard", nullable=False)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    # 与模型的多对多关系将通过关联表定义
    
    def __repr__(self):
        return f"<ModelCapability(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


# 创建模型和能力之间的多对多关联表
class ModelCapabilityAssociation(Base):
    """模型和能力的多对多关联表"""
    __tablename__ = "model_capability_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(Integer, ForeignKey("model_capabilities.id", ondelete="CASCADE"), nullable=False)
    
    # 可以添加额外的关联属性，如能力的具体配置、限制等
    config = Column(String(255), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())