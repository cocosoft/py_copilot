"""监控数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base

class AlertRuleDB(Base):
    """告警规则表"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    metric_name = Column(String(100), nullable=False)
    threshold = Column(Float, nullable=False)
    comparison = Column(String(10), nullable=False)  # '>', '<', '>=', '<=', '=='
    duration = Column(Integer, nullable=False)  # 持续时间（秒）
    level = Column(String(20), nullable=False)  # 'info', 'warning', 'error', 'critical'
    type = Column(String(20), nullable=False)  # 'performance', 'error_rate', 'resource', 'business', 'security'
    message_template = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AlertHistoryDB(Base):
    """告警历史表"""
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    type = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=True)  # 额外元数据

class MetricDataDB(Base):
    """指标数据表"""
    __tablename__ = "metric_data"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), index=True, nullable=False)
    value = Column(Float, nullable=False)
    tags = Column(JSON, nullable=True)  # 标签数据
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(100), nullable=True)  # 数据来源

class SystemMetricsDB(Base):
    """系统指标表"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    cpu_usage = Column(Float, nullable=False)  # CPU使用率
    memory_usage = Column(Float, nullable=False)  # 内存使用率
    disk_usage = Column(Float, nullable=False)  # 磁盘使用率
    network_in = Column(Float, nullable=True)  # 网络流入
    network_out = Column(Float, nullable=True)  # 网络流出
    db_connections = Column(Integer, nullable=True)  # 数据库连接数
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class PerformanceMetricsDB(Base):
    """性能指标表"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(200), index=True, nullable=False)  # API端点
    method = Column(String(10), nullable=False)  # HTTP方法
    response_time = Column(Float, nullable=False)  # 响应时间（毫秒）
    status_code = Column(Integer, nullable=False)  # 状态码
    user_agent = Column(String(500), nullable=True)  # 用户代理
    client_ip = Column(String(50), nullable=True)  # 客户端IP
    timestamp = Column(DateTime(timezone=True), server_default=func.now())