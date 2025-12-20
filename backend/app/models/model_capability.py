"""模型能力相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base

# 导入ModelDB类以避免关系解析错误
from app.models.supplier_db import ModelDB


class ModelCapability(Base):
    """模型能力表模型"""
    __tablename__ = "model_capabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 能力名称，如 text_generation, image_generation, speech_recognition
    display_name = Column(String(100), nullable=False)  # 显示名称，如 文本生成, 图像生成, 语音识别
    description = Column(Text, nullable=True)  # 能力描述
    
    # 能力维度（根据文档定义：理解能力、生成能力、推理能力、记忆能力、交互能力、专业能力）
    capability_dimension = Column(String(50), nullable=False, default="generation")  # 能力维度
    capability_subdimension = Column(String(50), nullable=True)  # 能力子维度
    
    # 能力强度量化（1-5级）
    base_strength = Column(Integer, default=3)  # 基础能力强度（1-5级）
    max_strength = Column(Integer, default=5)   # 最大可达到的能力强度
    
    # 能力评估指标
    assessment_metrics = Column(JSON, nullable=True)  # 评估指标配置
    benchmark_datasets = Column(JSON, nullable=True)  # 基准测试数据集
    
    # 能力依赖关系
    dependencies = Column(JSON, nullable=True)  # 依赖的其他能力
    
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
    
    # 是否为系统能力
    is_system = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # LOGO信息
    logo = Column(Text, nullable=True)  # SVG格式的logo数据
    
    # 关系定义
    # 与模型的多对多关系（使用字符串形式避免导入循环）
    models = relationship("app.models.supplier_db.ModelDB", secondary="model_capability_associations", back_populates="capabilities")
    
    # 与关联表的关系
    model_associations = relationship("ModelCapabilityAssociation", back_populates="capability")
    
    def __repr__(self):
        return f"<ModelCapability(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


# 创建模型和能力之间的多对多关联表
class ModelCapabilityAssociation(Base):
    """模型和能力的多对多关联表"""
    __tablename__ = "model_capability_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(Integer, ForeignKey("model_capabilities.id", ondelete="CASCADE"), nullable=False)
    
    # 模型在该能力上的实际强度评估（1-5级）
    actual_strength = Column(Integer, default=3)  # 实际能力强度
    confidence_score = Column(Integer, default=80)  # 评估置信度（0-100）
    
    # 评估信息
    last_assessment_date = Column(DateTime(timezone=True), nullable=True)  # 最后评估时间
    assessment_method = Column(String(50), nullable=True)  # 评估方法（automated, manual, hybrid）
    assessment_data = Column(JSON, nullable=True)  # 评估数据详情
    
    # 能力配置
    config = Column(String(255), nullable=True)  # 简单配置（兼容旧系统）
    config_json = Column(Text, nullable=True)  # 扩展的JSON配置
    
    # 是否为默认能力配置
    is_default = Column(Boolean, default=False)
    
    # 关联权重（用于能力优先级排序）
    weight = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义
    model = relationship("ModelDB", back_populates="capability_associations")
    capability = relationship("ModelCapability", back_populates="model_associations")
    
    def __repr__(self):
        return f"<ModelCapabilityAssociation(id={self.id}, model_id={self.model_id}, capability_id={self.capability_id})>"