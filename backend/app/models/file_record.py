"""
统一文件记录模型

用于替代现有的分散文件记录表（uploaded_files, voice_inputs等）
实现统一的文件管理和用户隔离
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    BigInteger, JSON, Enum, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class FileCategory(str, enum.Enum):
    """文件分类枚举"""
    CONVERSATION_ATTACHMENT = "conversation_attachment"  # 聊天附件
    VOICE_MESSAGE = "voice_message"                      # 语音消息
    KNOWLEDGE_DOCUMENT = "knowledge_document"            # 知识库文档
    KNOWLEDGE_EXTRACT = "knowledge_extract"              # 知识库提取内容
    TRANSLATION_INPUT = "translation_input"              # 翻译输入
    TRANSLATION_OUTPUT = "translation_output"            # 翻译输出
    USER_AVATAR = "user_avatar"                          # 用户头像
    USER_EXPORT = "user_export"                          # 用户导出
    TEMP_FILE = "temp_file"                              # 临时文件
    MODEL_LOGO = "model_logo"                            # 模型Logo
    SUPPLIER_LOGO = "supplier_logo"                      # 供应商Logo
    IMAGE_ANALYSIS = "image_analysis"                    # 图像分析


class FileStatus(str, enum.Enum):
    """文件状态枚举"""
    PENDING = "pending"           # 待处理
    UPLOADING = "uploading"       # 上传中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    PROCESSING = "processing"     # 处理中
    EXPIRED = "expired"           # 已过期


class StorageType(str, enum.Enum):
    """存储类型枚举"""
    LOCAL = "local"       # 本地存储
    PUBLIC = "public"     # 公开目录
    TEMP = "temp"         # 临时存储
    DATABASE = "database" # 数据库存储


class FileRecord(Base):
    """
    统一文件记录表
    
    替代原有的 uploaded_files, voice_inputs, analyzed_images 等分散表
    实现统一的文件管理和用户隔离
    """
    __tablename__ = "file_records"
    
    # 主键
    id = Column(String(36), primary_key=True, index=True, comment="文件唯一标识(UUID)")
    
    # 用户隔离
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True,
        comment="上传用户ID"
    )
    
    # 文件基本信息
    original_name = Column(String(500), nullable=False, comment="原始文件名")
    stored_name = Column(String(500), nullable=False, comment="存储文件名")
    
    # 存储路径
    relative_path = Column(String(1000), nullable=False, comment="相对存储路径")
    absolute_path = Column(String(1000), nullable=False, comment="绝对存储路径")
    
    # 文件属性
    file_size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    mime_type = Column(String(200), nullable=True, comment="MIME类型")
    extension = Column(String(20), nullable=False, comment="文件扩展名")
    checksum = Column(String(32), nullable=True, comment="MD5校验和")
    
    # 分类和关联
    category = Column(
        Enum(FileCategory), 
        nullable=False, 
        index=True,
        comment="文件分类"
    )
    storage_type = Column(
        Enum(StorageType), 
        default=StorageType.LOCAL,
        comment="存储类型"
    )
    
    # 关联ID（根据分类不同含义不同）
    conversation_id = Column(
        Integer, 
        ForeignKey("conversations.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True,
        comment="关联对话ID"
    )
    knowledge_base_id = Column(
        Integer, 
        nullable=True, 
        index=True,
        comment="关联知识库ID"
    )
    related_id = Column(
        Integer, 
        nullable=True, 
        index=True,
        comment="通用关联ID"
    )
    
    # 状态
    status = Column(
        Enum(FileStatus), 
        default=FileStatus.PENDING,
        index=True,
        comment="文件状态"
    )
    
    # 处理结果
    processing_result = Column(JSON, nullable=True, comment="处理结果")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 元数据
    extra_metadata = Column(JSON, nullable=True, comment="额外元数据")
    
    # 过期时间（用于临时文件）
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True, comment="过期时间")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        index=True,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        comment="更新时间"
    )
    
    # 索引优化
    __table_args__ = (
        # 复合索引：用户+分类
        Index('idx_user_category', 'user_id', 'category'),
        # 复合索引：用户+分类+关联ID
        Index('idx_user_related', 'user_id', 'category', 'related_id'),
        # 复合索引：分类+状态
        Index('idx_category_status', 'category', 'status'),
        # 复合索引：过期时间（用于清理）
        Index('idx_expires_at', 'expires_at'),
    )
    
    # 关系定义
    user = relationship("User", back_populates="file_records")
    conversation = relationship("Conversation", back_populates="file_records")
    blob = relationship("FileBlob", back_populates="file_record", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FileRecord(id={self.id}, name='{self.original_name}', category='{self.category}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'original_name': self.original_name,
            'stored_name': self.stored_name,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'extension': self.extension,
            'category': self.category.value if self.category else None,
            'storage_type': self.storage_type.value if self.storage_type else None,
            'status': self.status.value if self.status else None,
            'relative_path': self.relative_path,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'knowledge_base_id': self.knowledge_base_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.extra_metadata
        }


class FileBlob(Base):
    """
    文件BLOB存储表
    
    用于小文件直接存储在数据库中
    """
    __tablename__ = "file_blobs"
    
    file_id = Column(
        String(36), 
        ForeignKey("file_records.id", ondelete="CASCADE"), 
        primary_key=True,
        comment="关联文件ID"
    )
    data = Column(
        # 使用LargeBinary存储二进制数据
        # 注意：实际使用时需要根据数据库类型调整
        Text,  # 临时使用Text，实际应使用LargeBinary
        nullable=False,
        comment="文件二进制数据"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 关系定义
    file_record = relationship("FileRecord", back_populates="blob")
    
    def __repr__(self):
        return f"<FileBlob(file_id={self.file_id}, size={len(self.data) if self.data else 0})>"


# 在User模型中添加反向关系
# 需要在 user.py 中添加：
# file_records = relationship("FileRecord", back_populates="user", cascade="all, delete-orphan")

# 在Conversation模型中添加反向关系
# 需要在 conversation.py 中添加：
# file_records = relationship("FileRecord", back_populates="conversation")
