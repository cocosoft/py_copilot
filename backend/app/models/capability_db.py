"""能力相关数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text
from app.models.base import Base

class CapabilityDB(Base):
    """能力数据库模型"""
    __tablename__ = "capabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    display_name = Column(String(200))
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)