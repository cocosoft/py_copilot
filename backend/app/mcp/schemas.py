"""MCP Pydantic 模型定义

定义 MCP 相关的数据验证和序列化模型。
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TransportType(str, Enum):
    """传输类型枚举
    
    定义 MCP 连接支持的传输协议类型。
    """
    SSE = "sse"
    STDIO = "stdio"
    WEBSOCKET = "websocket"


class AuthType(str, Enum):
    """认证类型枚举
    
    定义 MCP 服务支持的认证方式。
    """
    NONE = "none"
    API_KEY = "api_key"
    JWT = "jwt"


class MCPModule(str, Enum):
    """可暴露的模块枚举
    
    定义可以通过 MCP 协议暴露的功能模块。
    """
    TOOLS = "tools"
    SKILLS = "skills"
    KNOWLEDGE = "knowledge"
    WORKFLOWS = "workflows"
    AGENTS = "agents"
    MEMORY = "memory"


class ConnectionStatus(str, Enum):
    """连接状态枚举
    
    定义 MCP 客户端连接的状态。
    """
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


class CallDirection(str, Enum):
    """调用方向枚举
    
    定义 MCP 调用的方向。
    """
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class CallStatus(str, Enum):
    """调用状态枚举
    
    定义 MCP 工具调用的执行状态。
    """
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    PENDING = "pending"


# ==================== Server Config Schemas ====================

class MCPServerConfigBase(BaseModel):
    """MCP 服务配置基础模型
    
    定义 MCP 服务端配置的基本字段。
    
    Attributes:
        name: 配置名称，用于标识
        description: 配置描述
        transport: 传输类型，支持 sse/stdio/websocket
        host: 监听地址
        port: 监听端口
        enabled: 是否启用
        auth_type: 认证类型
        auth_config: 认证配置详情
        exposed_modules: 要暴露的模块列表
    """
    name: str = Field(..., description="配置名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="配置描述")
    transport: TransportType = Field(default=TransportType.SSE, description="传输类型")
    host: str = Field(default="127.0.0.1", description="监听地址")
    port: int = Field(default=8008, description="监听端口", ge=1, le=65535)
    enabled: bool = Field(default=True, description="是否启用")
    auth_type: AuthType = Field(default=AuthType.NONE, description="认证类型")
    auth_config: Optional[Dict[str, Any]] = Field(default=None, description="认证配置")
    exposed_modules: List[MCPModule] = Field(
        default=[MCPModule.TOOLS, MCPModule.SKILLS],
        description="暴露的模块列表"
    )


class MCPServerConfigCreate(MCPServerConfigBase):
    """创建 MCP 服务配置请求模型"""
    pass


class MCPServerConfigUpdate(BaseModel):
    """更新 MCP 服务配置请求模型
    
    所有字段均为可选，只更新提供的字段。
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    transport: Optional[TransportType] = None
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    enabled: Optional[bool] = None
    auth_type: Optional[AuthType] = None
    auth_config: Optional[Dict[str, Any]] = None
    exposed_modules: Optional[List[MCPModule]] = None


class MCPServerConfig(MCPServerConfigBase):
    """MCP 服务配置完整模型
    
    包含数据库字段的完整配置信息。
    """
    id: int = Field(..., description="配置ID")
    user_id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ==================== Client Config Schemas ====================

class MCPClientConfigBase(BaseModel):
    """MCP 客户端配置基础模型
    
    定义 MCP 客户端连接配置的基本字段。
    
    Attributes:
        name: 连接名称
        description: 连接描述
        transport: 传输类型
        connection_url: 连接URL（SSE/WebSocket模式）
        command: 启动命令（stdio模式）
        enabled: 是否启用
        auto_connect: 是否自动连接
        auth_config: 认证配置
        tool_whitelist: 工具白名单
        tool_blacklist: 工具黑名单
    """
    name: str = Field(..., description="连接名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="连接描述")
    transport: TransportType = Field(default=TransportType.SSE, description="传输类型")
    connection_url: Optional[str] = Field(None, description="连接URL", max_length=500)
    command: Optional[str] = Field(None, description="启动命令", max_length=500)
    enabled: bool = Field(default=True, description="是否启用")
    auto_connect: bool = Field(default=True, description="是否自动连接")
    auth_config: Optional[Dict[str, Any]] = Field(default=None, description="认证配置")
    tool_whitelist: Optional[List[str]] = Field(default=None, description="工具白名单")
    tool_blacklist: Optional[List[str]] = Field(default=None, description="工具黑名单")


class MCPClientConfigCreate(MCPClientConfigBase):
    """创建 MCP 客户端配置请求模型"""
    pass


class MCPClientConfigUpdate(BaseModel):
    """更新 MCP 客户端配置请求模型
    
    所有字段均为可选，只更新提供的字段。
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    transport: Optional[TransportType] = None
    connection_url: Optional[str] = Field(None, max_length=500)
    command: Optional[str] = Field(None, max_length=500)
    enabled: Optional[bool] = None
    auto_connect: Optional[bool] = None
    auth_config: Optional[Dict[str, Any]] = None
    tool_whitelist: Optional[List[str]] = None
    tool_blacklist: Optional[List[str]] = None


class MCPClientConfig(MCPClientConfigBase):
    """MCP 客户端配置完整模型
    
    包含数据库字段的完整配置信息，包括连接状态。
    """
    id: int = Field(..., description="配置ID")
    user_id: int = Field(..., description="用户ID")
    status: ConnectionStatus = Field(default=ConnectionStatus.DISCONNECTED, description="连接状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    last_connected_at: Optional[datetime] = Field(None, description="最后连接时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ==================== Tool Mapping Schemas ====================

class MCPToolMappingBase(BaseModel):
    """MCP 工具映射基础模型"""
    original_name: str = Field(..., description="原始工具名")
    local_name: str = Field(..., description="本地映射名")
    description: Optional[str] = Field(None, description="工具描述")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="输入参数Schema")
    enabled: bool = Field(default=True, description="是否启用")


class MCPToolMapping(MCPToolMappingBase):
    """MCP 工具映射完整模型"""
    id: int = Field(..., description="映射ID")
    client_config_id: int = Field(..., description="客户端配置ID")
    cached_at: datetime = Field(..., description="缓存时间")

    class Config:
        from_attributes = True


# ==================== Call Log Schemas ====================

class MCPCallLogBase(BaseModel):
    """MCP 调用日志基础模型"""
    direction: CallDirection = Field(..., description="调用方向")
    connection_name: Optional[str] = Field(None, description="连接名称")
    tool_name: Optional[str] = Field(None, description="工具名称")
    request_data: Optional[Dict[str, Any]] = Field(None, description="请求数据")
    response_data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    status: Optional[CallStatus] = Field(None, description="调用状态")
    execution_time_ms: Optional[int] = Field(None, description="执行时间（毫秒）")


class MCPCallLog(MCPCallLogBase):
    """MCP 调用日志完整模型"""
    id: int = Field(..., description="日志ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


# ==================== Settings Integration ====================

class MCPSettingsData(BaseModel):
    """MCP 设置数据模型
    
    用于 SettingService 的集成，统一管理 MCP 相关设置。
    """
    server_configs: List[MCPServerConfig] = Field(default_factory=list, description="服务端配置列表")
    client_configs: List[MCPClientConfig] = Field(default_factory=list, description="客户端配置列表")
    global_enabled: bool = Field(default=True, description="全局启用 MCP")
    default_timeout: int = Field(default=30, description="默认超时时间（秒）", ge=1, le=300)
    max_concurrent_calls: int = Field(default=10, description="最大并发调用数", ge=1, le=100)
    log_enabled: bool = Field(default=True, description="启用调用日志")


# ==================== API Response Schemas ====================

class MCPStatusResponse(BaseModel):
    """MCP 状态响应模型"""
    server_enabled: bool = Field(..., description="服务端是否启用")
    server_count: int = Field(..., description="服务端配置数量")
    client_count: int = Field(..., description="客户端配置数量")
    connected_clients: int = Field(..., description="已连接客户端数量")
    servers: List[Dict[str, Any]] = Field(default_factory=list, description="服务端列表")
    clients: List[Dict[str, Any]] = Field(default_factory=list, description="客户端列表")


class MCPToolInfo(BaseModel):
    """MCP 工具信息模型"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    source: str = Field(..., description="工具来源：local/skill/external")
    inputSchema: Dict[str, Any] = Field(..., description="输入参数Schema")
    enabled: bool = Field(default=True, description="是否启用")


class MCPConnectResult(BaseModel):
    """MCP 连接结果模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    tools_discovered: int = Field(default=0, description="发现的工具数量")
