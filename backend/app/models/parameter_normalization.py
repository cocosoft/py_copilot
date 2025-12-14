"""参数归一化规则模型"""
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base


class ParameterNormalizationRule(Base):
    """参数归一化规则模型，用于存储不同供应商的参数映射规则"""
    __tablename__ = "parameter_normalization_rules"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)  # 规则ID
    supplier_id = Column(Integer, nullable=True, index=True)  # 供应商ID，可为空表示通用规则
    model_type = Column(String(100), nullable=True, index=True)  # 模型类型，可为空表示适用于所有模型类型
    param_name = Column(String(100), nullable=False)  # 供应商参数名
    standard_name = Column(String(100), nullable=False)  # 标准参数名
    param_type = Column(String(50), nullable=False)  # 参数类型：int、float、string、bool、array、object
    mapped_from = Column(String(100), nullable=True)  # 映射来源参数名，用于支持别名
    default_value = Column(JSON, nullable=True)  # 默认值
    range_min = Column(Integer, nullable=True)  # 最小值（适用于数值类型）
    range_max = Column(Integer, nullable=True)  # 最大值（适用于数值类型）
    regex_pattern = Column(String(200), nullable=True)  # 正则表达式（适用于字符串类型）
    enum_values = Column(JSON, nullable=True)  # 枚举值列表（适用于枚举类型）
    is_active = Column(Boolean, default=True)  # 是否激活
    description = Column(String(500), nullable=True)  # 规则描述
    
    def __repr__(self):
        return f"<ParameterNormalizationRule(id={self.id}, supplier_id={self.supplier_id}, param_name='{self.param_name}', standard_name='{self.standard_name}')>"