"""能力维度相关数据库模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class CapabilityDimension(Base):
    """能力维度数据库模型"""
    __tablename__ = "capability_dimensions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)  # 维度名称，如：comprehension, generation
    display_name = Column(String(100), nullable=False)  # 显示名称，如：理解能力，生成能力
    description = Column(Text, nullable=True)  # 维度描述
    
    # 状态信息
    is_active = Column(Boolean, default=True)  # 是否激活
    is_system = Column(Boolean, default=False)  # 是否系统内置维度
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    subdimensions = relationship("CapabilitySubdimension", back_populates="dimension")
    # capabilities = relationship("ModelCapability", back_populates="dimension_rel", foreign_keys="ModelCapability.dimension_id")
    
    def __repr__(self):
        return f"<CapabilityDimension(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class CapabilitySubdimension(Base):
    """能力子维度数据库模型"""
    __tablename__ = "capability_subdimensions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)  # 子维度名称
    display_name = Column(String(100), nullable=False)  # 显示名称
    description = Column(Text, nullable=True)  # 子维度描述
    
    # 外键
    dimension_id = Column(Integer, ForeignKey("capability_dimensions.id"), nullable=False)
    
    # 状态信息
    is_active = Column(Boolean, default=True)  # 是否激活
    is_system = Column(Boolean, default=False)  # 是否系统内置子维度
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    dimension = relationship("CapabilityDimension", back_populates="subdimensions")
    # capabilities = relationship("ModelCapability", back_populates="subdimension_rel", foreign_keys="ModelCapability.subdimension_id")
    
    def __repr__(self):
        return f"<CapabilitySubdimension(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"
