"""
工作空间模型

定义工作空间的数据结构和关联关系，支持多用户独立工作空间功能
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Workspace(Base):
    """
    工作空间模型

    每个用户可以拥有多个工作空间，用于隔离不同项目或场景的数据
    工作空间之间数据完全隔离，包括文件、对话、知识库等
    """
    __tablename__ = "workspaces"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(100), nullable=False, comment="工作空间名称")
    description = Column(Text, nullable=True, comment="工作空间描述")

    # 关联用户
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属用户ID"
    )
    user = relationship(
        "User",
        back_populates="workspaces",
        foreign_keys=[user_id]
    )

    # 工作空间配置
    is_default = Column(
        Boolean,
        default=False,
        comment="是否为默认工作空间"
    )
    is_active = Column(
        Boolean,
        default=True,
        comment="是否激活"
    )

    # 存储配额（字节），默认1GB
    max_storage_bytes = Column(
        Integer,
        default=1073741824,
        comment="最大存储空间（字节）"
    )

    # 时间戳
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    # 关联数据 - 文件记录
    file_records = relationship(
        "FileRecord",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', user_id={self.user_id})>"

    def to_dict(self) -> dict:
        """
        转换为字典

        Returns:
            dict: 工作空间信息字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'max_storage_bytes': self.max_storage_bytes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
