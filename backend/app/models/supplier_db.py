"""供应商和模型数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.encryption import encrypt_string, decrypt_string
from app.models.model_category import ModelCategory
from app.models.parameter_template import ParameterTemplate


class SupplierDB(Base):
    """供应商数据库模型"""
    __tablename__ = "suppliers"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    display_name = Column(String(200))  # 新增display_name字段，与name保持一致
    description = Column(Text, nullable=True)
    api_endpoint = Column(String(255), nullable=True)
    api_key_required = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # 新增字段
    logo = Column(String(255), nullable=True)  # Logo存储路径或URL，现在可选
    category = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    api_docs = Column(String(255), nullable=True)
    _api_key = Column("api_key", String(255), nullable=True)  # 实际存储加密后的API密钥
    is_active = Column(Boolean, default=True)
    
    @property
    def api_key(self):
        """获取解密后的API密钥"""
        if self._api_key is not None:
            try:
                # 尝试解密
                return decrypt_string(str(self._api_key))
            except Exception as e:
                # 如果解密失败，可能是因为这是旧的未加密API密钥
                print(f"Warning: Failed to decrypt API key for supplier {self.name}: {e}")
                # 返回原始值，但不建议这样做，更好的做法是自动加密
                return str(self._api_key)
        return None
    
    @api_key.setter
    def api_key(self, value):
        """设置API密钥，自动加密存储"""
        if value:
            self._api_key = encrypt_string(value)
        else:
            self._api_key = None
    
    # 添加关系定义
    models = relationship("ModelDB", back_populates="supplier")


class ModelDB(Base):
    """模型数据库模型"""
    __tablename__ = "models"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), index=True)
    model_name = Column(String(200))
    description = Column(Text, nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    model_type_id = Column(Integer, ForeignKey("model_categories.id"), nullable=True)  # 模型类型ID，关联到model_categories表
    context_window = Column(Integer, nullable=True)  # 上下文窗口大小
    max_tokens = Column(Integer, nullable=True)  # 最大token数
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    logo = Column(String(255), nullable=True)  # 模型LOGO存储路径或URL
    
    # 添加关系定义，使用lazy='select'避免自动加载
    supplier = relationship("SupplierDB", back_populates="models", lazy='select')
    parameters = relationship("ModelParameter", back_populates="model", cascade="all, delete-orphan", lazy='select')
    model_type = relationship("ModelCategory", back_populates="model_db", lazy='select')
    categories = relationship("ModelCategory", secondary="model_category_associations", back_populates="models", lazy='select')
    category_associations = relationship("ModelCategoryAssociation", back_populates="model", lazy='select')
    capabilities = relationship("app.models.model_capability.ModelCapability", secondary="model_capability_associations", back_populates="models", lazy='select')
    capability_associations = relationship("app.models.model_capability.ModelCapabilityAssociation", back_populates="model", lazy='select')
    
    # 参数模板关联
    parameter_template_id = Column(Integer, ForeignKey("parameter_templates.id", ondelete="SET NULL"), nullable=True)
    parameter_template = relationship("ParameterTemplate", back_populates="models", lazy='select')


class ModelParameter(Base):
    """模型参数表，用于存储不同类型模型的特定参数"""
    __tablename__ = "model_parameters"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=True)  # 模型ID，类型级参数可为空
    parameter_name = Column(String(100), nullable=False)  # 参数名称
    parameter_type = Column(String(50), nullable=False)  # 参数类型: int, float, bool, string, json等
    parameter_value = Column(Text, nullable=False)  # 参数值，以文本形式存储
    is_default = Column(Boolean, default=False)  # 是否为默认参数
    description = Column(Text, nullable=True)  # 参数描述
    parameter_source = Column(String(50), default="model")  # 参数来源：model_type或model
    is_override = Column(Boolean, default=False)  # 是否覆盖父参数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 添加关系定义
    model = relationship("ModelDB", back_populates="parameters")
    parameter_versions = relationship("ParameterVersion", back_populates="parameter", cascade="all, delete-orphan")
    
    # 可以添加复合唯一约束，确保同一个模型不会有同名参数
    # __table_args__ = (UniqueConstraint('model_id', 'parameter_name', name='_model_parameter_uc'),)


class ParameterVersion(Base):
    """参数版本表，用于存储参数的历史版本记录"""
    __tablename__ = "parameter_versions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("model_parameters.id", ondelete="CASCADE"), nullable=False)  # 关联的参数ID
    version_number = Column(Integer, nullable=False)  # 版本号
    parameter_value = Column(Text, nullable=False)  # 该版本的参数值
    updated_at = Column(DateTime(timezone=True), server_default=func.now())  # 更新时间
    updated_by = Column(String(100), nullable=True)  # 更新人，可为空
    
    # 添加关系定义
    parameter = relationship("ModelParameter", back_populates="parameter_versions")


class ModelParameterVersion(Base):
    """模型参数版本表，用于存储整个模型参数的历史版本记录"""
    __tablename__ = "model_parameter_versions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)  # 关联的模型ID
    version_name = Column(String(100), nullable=False)  # 版本名称
    version_description = Column(Text, nullable=True)  # 版本描述
    parameters_snapshot = Column(Text, nullable=False)  # 参数快照（JSON格式）
    created_by = Column(String(100), nullable=True)  # 创建人
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    is_active = Column(Boolean, default=True)  # 是否活跃版本
    
    # 添加关系定义
    model = relationship("ModelDB", backref="parameter_versions")
