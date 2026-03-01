"""
能力编排数据库模型

本模块定义能力编排相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class CapabilityOrchestrationLog(Base):
    """
    能力编排日志模型

    记录每次能力编排的完整信息
    """

    __tablename__ = 'capability_orchestration_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 输入信息
    input_text = Column(Text, nullable=False)
    intent_type = Column(String(100))
    intent_confidence = Column(Float)
    complexity_level = Column(String(50))

    # 执行计划
    execution_plan = Column(JSON, default=dict)
    used_capabilities = Column(JSON, default=list)
    execution_steps = Column(JSON, default=list)

    # 执行结果
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text)

    # 元数据
    created_at = Column(DateTime, default=func.now())

    # 索引
    __table_args__ = (
        Index('idx_orchestration_user', 'user_id', 'created_at'),
        Index('idx_orchestration_agent', 'agent_id', 'created_at'),
        Index('idx_orchestration_intent', 'intent_type', 'success'),
    )

    def __repr__(self):
        return f"<CapabilityOrchestrationLog(id={self.id}, execution_id='{self.execution_id}', success={self.success})>"


class CapabilityExecutionLog(Base):
    """
    能力执行日志模型

    记录单个能力的执行详情
    """

    __tablename__ = 'capability_execution_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    orchestration_id = Column(Integer, ForeignKey('capability_orchestration_logs.id'), nullable=True)

    # 能力信息
    capability_name = Column(String(100), nullable=False, index=True)
    capability_type = Column(String(50))

    # 输入输出
    input_data = Column(JSON)
    output_data = Column(JSON)

    # 执行信息
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # 元数据
    created_at = Column(DateTime, default=func.now())

    # 关系
    orchestration = relationship("CapabilityOrchestrationLog", backref="execution_logs")

    # 索引
    __table_args__ = (
        Index('idx_execution_capability', 'capability_name', 'created_at'),
        Index('idx_execution_orchestration', 'orchestration_id', 'created_at'),
        Index('idx_execution_success', 'capability_name', 'success'),
    )

    def __repr__(self):
        return f"<CapabilityExecutionLog(id={self.id}, capability_name='{self.capability_name}', success={self.success})>"


class CapabilityUsageStats(Base):
    """
    能力使用统计模型

    记录能力的累计使用统计数据
    """

    __tablename__ = 'capability_usage_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    capability_name = Column(String(100), unique=True, nullable=False, index=True)

    # 调用统计
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)

    # 时间统计
    total_execution_time_ms = Column(Integer, default=0)  # 总执行时间（毫秒）
    average_execution_time_ms = Column(Float, default=0.0)

    # 成功率
    success_rate = Column(Float, default=1.0)

    # 时间戳
    last_used_at = Column(DateTime)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<CapabilityUsageStats(capability_name='{self.capability_name}', total_calls={self.total_calls})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "capability_name": self.capability_name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "average_execution_time_ms": round(self.average_execution_time_ms, 2),
            "success_rate": round(self.success_rate, 4),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class CapabilityDependency(Base):
    """
    能力依赖关系模型

    记录能力之间的依赖关系
    """

    __tablename__ = 'capability_dependencies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    capability_name = Column(String(100), nullable=False, index=True)
    depends_on = Column(String(100), nullable=False, index=True)
    dependency_type = Column(String(50), default='required')  # required/optional

    # 元数据
    created_at = Column(DateTime, default=func.now())

    # 唯一约束
    __table_args__ = (
        Index('idx_dependency_unique', 'capability_name', 'depends_on', unique=True),
        Index('idx_dependency_capability', 'capability_name'),
        Index('idx_dependency_depends_on', 'depends_on'),
    )

    def __repr__(self):
        return f"<CapabilityDependency({self.capability_name} -> {self.depends_on})>"


class CapabilityCacheEntry(Base):
    """
    能力结果缓存模型

    缓存能力执行结果以提高性能
    """

    __tablename__ = 'capability_cache_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    capability_name = Column(String(100), nullable=False, index=True)

    # 缓存内容
    input_hash = Column(String(64))  # 输入数据的哈希值
    output_data = Column(JSON)

    # 过期时间
    expires_at = Column(DateTime, nullable=False)

    # 使用统计
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    last_accessed_at = Column(DateTime)

    # 索引
    __table_args__ = (
        Index('idx_cache_capability', 'capability_name', 'created_at'),
        Index('idx_cache_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<CapabilityCacheEntry(key='{self.cache_key}', capability='{self.capability_name}')>"

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        from datetime import datetime
        return datetime.now() > self.expires_at


class CapabilityIndexEntry(Base):
    """
    能力索引模型

    用于能力发现的全文索引
    """

    __tablename__ = 'capability_index_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    capability_name = Column(String(100), unique=True, nullable=False)

    # 索引内容
    name_index = Column(Text)  # 名称索引
    description_index = Column(Text)  # 描述索引
    tags_index = Column(Text)  # 标签索引

    # 向量表示（用于语义搜索）
    embedding = Column(JSON)  # 向量嵌入

    # 元数据
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<CapabilityIndexEntry(capability_name='{self.capability_name}')>"


class OrchestrationConfig(Base):
    """
    编排配置模型

    存储编排相关的配置参数
    """

    __tablename__ = 'orchestration_configs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(JSON)
    description = Column(Text)

    # 元数据
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<OrchestrationConfig(key='{self.config_key}')>"
