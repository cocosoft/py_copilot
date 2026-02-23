"""Function Calling工具模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Tool(Base):
    """工具表"""
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, comment="工具名称，全局唯一")
    display_name = Column(String(255), nullable=False, comment="工具显示名称")
    description = Column(Text, nullable=False, comment="工具描述")
    category = Column(String(100), nullable=False, comment="工具分类")
    version = Column(String(50), default="1.0.0", comment="工具版本")
    author = Column(String(255), comment="工具作者")
    icon = Column(String(50), default="🔧", comment="工具图标")
    tags = Column(JSON, comment="工具标签")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系
    executions = relationship("ToolExecution", back_populates="tool", cascade="all, delete-orphan")
    usage_stats = relationship("ToolUsageStats", back_populates="tool", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', category='{self.category}')>"


class ToolExecution(Base):
    """工具执行记录表"""
    __tablename__ = "tool_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, comment="工具ID")
    user_id = Column(Integer, comment="用户ID")
    conversation_id = Column(Integer, comment="对话ID")
    parameters = Column(JSON, comment="执行参数")
    result = Column(JSON, comment="执行结果")
    error = Column(Text, comment="错误信息")
    execution_time = Column(Float, comment="执行时间（秒）")
    status = Column(String(50), default="pending", comment="执行状态")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关系
    tool = relationship("Tool", back_populates="executions")

    def __repr__(self):
        return f"<ToolExecution(id={self.id}, tool_id={self.tool_id}, status='{self.status}')>"


class ToolUsageStats(Base):
    """工具使用统计表"""
    __tablename__ = "tool_usage_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, comment="工具ID")
    date = Column(String(10), nullable=False, comment="日期（YYYY-MM-DD）")
    call_count = Column(Integer, default=0, comment="调用次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    failure_count = Column(Integer, default=0, comment="失败次数")
    avg_execution_time = Column(Float, comment="平均执行时间（秒）")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系
    tool = relationship("Tool", back_populates="usage_stats")

    def __repr__(self):
        return f"<ToolUsageStats(id={self.id}, tool_id={self.tool_id}, date='{self.date}')>"
