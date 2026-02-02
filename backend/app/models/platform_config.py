"""
平台配置模型

存储和管理平台适配器的配置信息
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from app.models.base import Base


class PlatformConfig(Base):
    """平台配置表"""
    
    __tablename__ = "platform_configs"
    
    id = Column(Integer, primary_key=True, index=True, comment="配置ID")
    platform_name = Column(String(100), unique=True, nullable=False, index=True, comment="平台名称")
    config_data = Column(JSON, nullable=False, comment="配置数据")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "platform_name": self.platform_name,
            "config_data": self.config_data,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
