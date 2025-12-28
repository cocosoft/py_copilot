"""能力类型相关数据库模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import Base


class CapabilityType(Base):
    """能力类型数据库模型"""
    __tablename__ = "capability_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)  # 类型名称，如：standard, advanced, specialized
    display_name = Column(String(100), nullable=False)  # 显示名称，如：标准能力，高级能力
    description = Column(Text, nullable=True)  # 类型描述
    
    # 分类和分组信息
    category = Column(String(50), default="general")  # 能力类别，如：general, domain_specific, special
    icon = Column(String(50), nullable=True)  # 图标名称
    
    # 状态信息
    is_active = Column(Boolean, default=True)  # 是否激活
    is_system = Column(Boolean, default=False)  # 是否系统内置类型
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义将在表创建后添加
