"""模型管理相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, func, Boolean, Table
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelSupplier(Base):
    """模型供应商表模型"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 供应商名称，如 openai, deepseek
    display_name = Column(String(100), nullable=False)  # 显示名称，如 OpenAI, DeepSeek
    description = Column(Text, nullable=True)  # 供应商描述
    
    # API配置
    base_url = Column(String(255), nullable=True)  # API基础URL
    api_url = Column(String(255), nullable=True)  # API完整URL
    api_key = Column(String(255), nullable=True)  # API密钥
    api_key_env_name = Column(String(100), nullable=True)  # 环境变量中的API密钥名称
    
    # 其他信息
    website = Column(String(255), nullable=True)  # 官方网站
    api_docs = Column(String(255), nullable=True)  # API文档地址
    is_domestic = Column(Boolean, default=False)  # 是否为国内供应商
    logo = Column(String(255), nullable=True)  # 供应商logo路径
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系定义 - 使用最简单的配置
    models = relationship("Model", backref="supplier", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ModelSupplier(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class Model(Base):
    """模型表模型，扩展自现有的ModelConfiguration"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    model_id = Column(String(100), nullable=False)  # 供应商提供的模型ID
    name = Column(String(100), nullable=False)  # 显示名称
    description = Column(Text, nullable=True)  # 模型描述
    
    # 模型类型
    type = Column(String(50), nullable=False)  # chat, completion, embedding
    
    # 模型参数
    context_window = Column(Integer, default=8000)  # 上下文窗口大小
    default_temperature = Column(Float, default=0.7)
    default_max_tokens = Column(Integer, default=1000)
    default_top_p = Column(Float, default=1.0)
    default_frequency_penalty = Column(Float, default=0.0)
    default_presence_penalty = Column(Float, default=0.0)
    
    # 自定义参数（存储为JSON）
    custom_params = Column(JSON, nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系通过backref自动定义
    
    # 与模型分类的多对多关系
    categories = relationship(
        "ModelCategory",
        secondary="model_category_associations",
        backref="models"
    )
    
    # 与模型能力的多对多关系
    capabilities = relationship(
        "ModelCapability",
        secondary="model_capability_associations",
        backref="models"
    )
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', model_id='{self.model_id}', supplier_id={self.supplier_id})>"