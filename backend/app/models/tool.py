"""工具数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tool(Base):
    """工具数据库模型"""
    __tablename__ = "tools"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), default='general', index=True)
    version = Column(String(50), default='1.0.0')
    icon = Column(String(50), default='🔧')
    tags = Column(JSON, default=list)
    
    # 官方能力标识
    source = Column(String(50), default='user')
    is_official = Column(Boolean, default=False, index=True)
    is_builtin = Column(Boolean, default=False, index=True)
    official_badge = Column(String(50), nullable=True)
    is_system = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False, index=True)
    allow_disable = Column(Boolean, default=True)
    allow_edit = Column(Boolean, default=True)
    
    # 版本管理
    min_app_version = Column(String(50), nullable=True)
    update_mode = Column(String(20), default='manual')
    
    # 工具配置
    tool_type = Column(String(50), default='local', index=True)  # local/mcp/official
    handler_module = Column(String(200), nullable=True)
    handler_class = Column(String(100), nullable=True)
    parameters_schema = Column(JSON, nullable=True)
    config = Column(JSON, default=dict)
    
    # MCP关联
    mcp_client_config_id = Column(Integer, ForeignKey("mcp_client_configs.id", ondelete="SET NULL"), nullable=True, index=True)
    mcp_tool_name = Column(String(255), nullable=True)
    
    # 状态
    status = Column(String(20), default='disabled', index=True)
    is_active = Column(Boolean, default=True)
    
    # 元数据
    author = Column(String(200), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    
    # 关系
    # mcp_client关系暂时注释掉，避免循环导入问题
    # mcp_client = relationship("MCPClientConfig", back_populates="tools")
    agent_associations = relationship("AgentToolAssociation", back_populates="tool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', type='{self.tool_type}')>"


class ToolExecutionLog(Base):
    """工具执行日志模型"""
    __tablename__ = "tool_execution_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    input_params = Column(JSON, default=dict)
    output_result = Column(Text, nullable=True)
    status = Column(String(20), default="pending", index=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    tool = relationship("Tool")
    
    def __repr__(self):
        return f"<ToolExecutionLog(id={self.id}, tool_id={self.tool_id}, status='{self.status}')>"
