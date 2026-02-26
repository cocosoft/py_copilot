from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class UserSetting(Base):
    """用户设置模型"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    # 不使用 ForeignKey，避免 SQLAlchemy 的循环导入问题
    # 数据库层面已通过迁移脚本创建外键约束
    user_id = Column(Integer, nullable=False)
    setting_type = Column(String(50), nullable=False)  # general, personalization, emotion, learning, relationship
    setting_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())