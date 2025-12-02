"""模型能力相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelCapability(Base):
    """模型能力表模型"""
    __tablename__ = "model_capabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 能力名称，如 text_generation, image_generation, speech_recognition
    display_name = Column(String(100), nullable=False)  # 显示名称，如 文本生成, 图像生成, 语音识别
    description = Column(Text, nullable=True)  # 能力描述
    
    # 能力类型
    capability_type = Column(String(50), default="standard", nullable=False)
    
    # 支持的输入类型（JSON格式），如 ["text", "image", "audio"]
    input_types = Column(Text, nullable=True)
    
    # 支持的输出类型（JSON格式），如 ["text", "image", "audio"]
    output_types = Column(Text, nullable=True)
    
    # 能力领域（如nlp, cv, audio, multimodal）
    domain = Column(String(50), nullable=False, default="nlp")
    
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
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    capability_id = Column(Integer, ForeignKey("model_capabilities.id"), nullable=False)
    
    # 简单配置（兼容旧系统）
    config = Column(String(255), nullable=True)
    
    # 扩展的JSON配置，支持复杂的能力配置，特别是多模态能力
    config_json = Column(Text, nullable=True)
    
    # 是否为默认能力配置
    is_default = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())