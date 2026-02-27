"""MCP 数据库模型定义"""

from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base


class MCPServerConfigModel(Base):
    """MCP 服务端配置模型
    
    存储 MCP 服务端配置信息，用于对外提供 MCP 服务。
    """
    
    __tablename__ = 'mcp_server_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    transport = Column(String(50), default='sse')
    host = Column(String(255), default='127.0.0.1')
    port = Column(Integer, default=8008)
    enabled = Column(Boolean, default=True, index=True)
    auth_type = Column(String(50), default='none')
    auth_config = Column(JSON, nullable=True)
    exposed_modules = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    def __repr__(self):
        return f"<MCPServerConfig(id={self.id}, name='{self.name}', enabled={self.enabled})>"


class MCPClientConfigModel(Base):
    """MCP 客户端连接配置模型
    
    存储外部 MCP 服务连接配置，用于连接第三方 MCP 服务。
    """
    
    __tablename__ = 'mcp_client_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    transport = Column(String(50), default='sse')
    connection_url = Column(String(500), nullable=True)
    command = Column(String(500), nullable=True)
    enabled = Column(Boolean, default=True, index=True)
    auto_connect = Column(Boolean, default=True)
    auth_config = Column(JSON, nullable=True)
    tool_whitelist = Column(JSON, nullable=True)
    tool_blacklist = Column(JSON, nullable=True)
    last_connected_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default='disconnected', index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    def __repr__(self):
        return f"<MCPClientConfig(id={self.id}, name='{self.name}', status='{self.status}')>"


class MCPToolMappingModel(Base):
    """MCP 工具映射模型
    
    缓存外部 MCP 服务的工具信息，建立原始工具名与本地工具名的映射关系。
    """
    
    __tablename__ = 'mcp_tool_mappings'
    
    id = Column(Integer, primary_key=True, index=True)
    client_config_id = Column(Integer, ForeignKey('mcp_client_configs.id', ondelete='CASCADE'), nullable=False)
    original_name = Column(String(255), nullable=False)
    local_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    input_schema = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True, index=True)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 唯一约束：每个客户端配置下，原始工具名必须唯一
    __table_args__ = (
        UniqueConstraint('client_config_id', 'original_name', name='uq_client_tool_name'),
    )
    
    def __repr__(self):
        return f"<MCPToolMapping(id={self.id}, original='{self.original_name}', local='{self.local_name}')>"


class MCPCallLogModel(Base):
    """MCP 调用日志模型
    
    记录所有 MCP 工具调用日志，包括内部调用和外部调用。
    """
    
    __tablename__ = 'mcp_call_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    direction = Column(String(20), nullable=False, index=True)
    connection_name = Column(String(255), nullable=True)
    tool_name = Column(String(255), nullable=True)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    status = Column(String(50), nullable=True, index=True)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<MCPCallLog(id={self.id}, direction='{self.direction}', tool='{self.tool_name}', status='{self.status}')>"
