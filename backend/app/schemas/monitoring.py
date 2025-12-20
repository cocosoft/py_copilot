"""监控模式定义"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class AlertRuleBase(BaseModel):
    """告警规则基础模式"""
    name: str = Field(..., description="规则名称")
    metric_name: str = Field(..., description="指标名称")
    threshold: float = Field(..., description="阈值")
    comparison: str = Field(..., description="比较操作符", pattern="^(>|>=|<|<=|==)$")
    duration: int = Field(..., description="持续时间（秒）", ge=1)
    level: str = Field(..., description="告警级别", pattern="^(info|warning|error|critical)$")
    type: str = Field(..., description="告警类型", pattern="^(performance|error_rate|resource|business|security)$")
    message_template: str = Field(..., description="消息模板")
    enabled: bool = Field(True, description="是否启用")

class AlertRuleCreate(AlertRuleBase):
    """告警规则创建模式"""
    pass

class AlertRuleUpdate(BaseModel):
    """告警规则更新模式"""
    metric_name: Optional[str] = None
    threshold: Optional[float] = None
    comparison: Optional[str] = None
    duration: Optional[int] = None
    level: Optional[str] = None
    type: Optional[str] = None
    message_template: Optional[str] = None
    enabled: Optional[bool] = None

class AlertRule(AlertRuleBase):
    """告警规则响应模式"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    """告警基础模式"""
    rule_name: str = Field(..., description="规则名称")
    level: str = Field(..., description="告警级别")
    type: str = Field(..., description="告警类型")
    message: str = Field(..., description="告警消息")
    metric_value: float = Field(..., description="指标值")
    threshold: float = Field(..., description="阈值")

class AlertCreate(AlertBase):
    """告警创建模式"""
    pass

class Alert(AlertBase):
    """告警响应模式"""
    id: int
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    resolved: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class MetricDataBase(BaseModel):
    """指标数据基础模式"""
    metric_name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    tags: Optional[Dict[str, str]] = Field(None, description="标签")

class MetricDataCreate(MetricDataBase):
    """指标数据创建模式"""
    pass

class MetricData(MetricDataBase):
    """指标数据响应模式"""
    id: int
    timestamp: datetime
    source: Optional[str] = None
    
    class Config:
        from_attributes = True

class SystemMetricsBase(BaseModel):
    """系统指标基础模式"""
    cpu_usage: float = Field(..., description="CPU使用率", ge=0, le=100)
    memory_usage: float = Field(..., description="内存使用率", ge=0, le=100)
    disk_usage: float = Field(..., description="磁盘使用率", ge=0, le=100)
    network_in: Optional[float] = Field(None, description="网络流入")
    network_out: Optional[float] = Field(None, description="网络流出")
    db_connections: Optional[int] = Field(None, description="数据库连接数")

class SystemMetricsCreate(SystemMetricsBase):
    """系统指标创建模式"""
    pass

class SystemMetrics(SystemMetricsBase):
    """系统指标响应模式"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class PerformanceMetricsBase(BaseModel):
    """性能指标基础模式"""
    endpoint: str = Field(..., description="API端点")
    method: str = Field(..., description="HTTP方法")
    response_time: float = Field(..., description="响应时间（毫秒）", ge=0)
    status_code: int = Field(..., description="状态码")
    user_agent: Optional[str] = Field(None, description="用户代理")
    client_ip: Optional[str] = Field(None, description="客户端IP")

class PerformanceMetricsCreate(PerformanceMetricsBase):
    """性能指标创建模式"""
    pass

class PerformanceMetrics(PerformanceMetricsBase):
    """性能指标响应模式"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class MetricSummary(BaseModel):
    """指标摘要"""
    count: int = Field(..., description="数据点数量")
    avg: float = Field(..., description="平均值")
    min: float = Field(..., description="最小值")
    max: float = Field(..., description="最大值")
    p95: float = Field(..., description="95分位数")

class AlertStatistics(BaseModel):
    """告警统计"""
    total_alerts: int = Field(..., description="总告警数")
    active_alerts: int = Field(..., description="活跃告警数")
    alerts_by_level: Dict[str, int] = Field(..., description="按级别统计")
    alerts_by_type: Dict[str, int] = Field(..., description="按类型统计")

class MonitoringStatistics(BaseModel):
    """监控统计"""
    alert_statistics: AlertStatistics = Field(..., description="告警统计")
    key_metrics: Dict[str, MetricSummary] = Field(..., description="关键指标")
    duration_seconds: int = Field(..., description="时间范围（秒）")

class AlertResponse(BaseModel):
    """告警响应"""
    id: str = Field(..., description="告警ID")
    rule_name: str = Field(..., description="规则名称")
    level: str = Field(..., description="告警级别")
    type: str = Field(..., description="告警类型")
    message: str = Field(..., description="告警消息")
    metric_value: float = Field(..., description="指标值")
    threshold: float = Field(..., description="阈值")
    timestamp: datetime = Field(..., description="触发时间")
    resolved: bool = Field(..., description="是否已解决")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")

class AlertListResponse(BaseModel):
    """告警列表响应"""
    alerts: List[AlertResponse] = Field(..., description="告警列表")
    count: int = Field(..., description="告警数量")

class AlertRuleResponse(BaseModel):
    """告警规则响应"""
    name: str = Field(..., description="规则名称")
    metric_name: str = Field(..., description="指标名称")
    threshold: float = Field(..., description="阈值")
    comparison: str = Field(..., description="比较操作符")
    duration: int = Field(..., description="持续时间（秒）")
    level: str = Field(..., description="告警级别")
    type: str = Field(..., description="告警类型")
    message_template: str = Field(..., description="消息模板")
    enabled: bool = Field(..., description="是否启用")

class AlertRuleListResponse(BaseModel):
    """告警规则列表响应"""
    rules: List[AlertRuleResponse] = Field(..., description="规则列表")

class MetricRecordRequest(BaseModel):
    """指标记录请求"""
    metric_name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    tags: Optional[Dict[str, str]] = Field(None, description="标签")

class MetricDataResponse(BaseModel):
    """指标数据响应"""
    metric_name: str = Field(..., description="指标名称")
    duration_seconds: int = Field(..., description="时间范围（秒）")
    summary: MetricSummary = Field(..., description="指标摘要")

class AlertRuleCreateRequest(BaseModel):
    """告警规则创建请求"""
    name: str = Field(..., description="规则名称")
    metric_name: str = Field(..., description="指标名称")
    threshold: float = Field(..., description="阈值")
    comparison: str = Field(..., description="比较操作符")
    duration: int = Field(..., description="持续时间（秒）")
    level: str = Field(..., description="告警级别")
    type: str = Field(..., description="告警类型")
    message_template: Optional[str] = Field(None, description="消息模板")

class AlertRuleUpdateRequest(BaseModel):
    """告警规则更新请求"""
    metric_name: Optional[str] = None
    threshold: Optional[float] = None
    comparison: Optional[str] = None
    duration: Optional[int] = None
    level: Optional[str] = None
    type: Optional[str] = None
    message_template: Optional[str] = None
    enabled: Optional[bool] = None