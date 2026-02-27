# Py Copilot MCP 集成设计方案（优化版）

## 1. 概述

### 1.1 什么是 MCP

Model Context Protocol (MCP) 是一个开放协议，用于实现 LLM 应用程序与外部数据源和工具之间的无缝集成。MCP 提供了一种标准化的方式来连接 LLM 与其所需的上下文信息。

### 1.2 设计目标

- **MCP 服务管理**: 与项目现有设置功能集成，提供前端管理页面
- **双向集成**: 既作为 MCP 服务端对外提供能力，也作为 MCP 客户端连接外部服务
- **模块兼容**: 与工作流、知识库、工具、技能等现有模块无缝集成
- **统一体验**: 保持与现有 Py Copilot 架构风格一致

### 1.3 与现有系统集成点

| 现有模块 | 集成方式 | 说明 |
|---------|---------|------|
| **设置管理** | 新增 `mcp` 设置类型 | 通过 `SettingService` 管理 MCP 配置 |
| **工作流** | 新增 MCP 节点类型 | 工作流中可调用 MCP 工具 |
| **知识库** | 作为 MCP Resource 暴露 | 外部客户端可读取知识库内容 |
| **工具系统** | 自动转换为 MCP Tool | `ToolRegistry` 工具自动暴露 |
| **技能系统** | 技能作为 MCP Tool | `SkillRegistry` 技能自动暴露 |
| **Agent 系统** | Agent 作为 MCP 服务 | 智能体能力通过 MCP 对外提供 |

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Py Copilot                                         │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         前端管理界面                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │  MCP服务配置  │  │  连接管理     │  │  工具授权     │  │  使用统计     │  │   │
│  │  │   页面       │  │   页面       │  │   页面       │  │   页面       │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      API 层 (FastAPI)                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ /api/v1/mcp/ │  │ /api/v1/mcp/ │  │ /api/v1/mcp/ │  │ /api/v1/mcp/ │  │   │
│  │  │   servers    │  │   clients    │  │   tools      │  │   settings   │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      MCP 服务管理层                                       │   │
│  │  ┌──────────────────────────────┐      ┌──────────────────────────────┐  │   │
│  │  │      MCP Server (服务端)      │      │      MCP Client (客户端)      │  │   │
│  │  │  ┌──────────┐  ┌──────────┐  │      │  ┌──────────┐  ┌──────────┐  │  │   │
│  │  │  │  SSE     │  │  Stdio   │  │      │  │ 连接管理  │  │ 工具发现  │  │  │   │
│  │  │  │ Transport│  │ Transport│  │      │  │ 连接池   │  │  缓存     │  │  │   │
│  │  │  └──────────┘  └──────────┘  │      │  └──────────┘  └──────────┘  │  │   │
│  │  │  ┌──────────┐  ┌──────────┐  │      │  ┌──────────┐  ┌──────────┐  │  │   │
│  │  │  │  Tool    │  │ Resource │  │      │  │ 工具调用  │  │ 资源读取  │  │  │   │
│  │  │  │ Handler  │  │ Handler  │  │      │  │ 代理     │  │  代理     │  │  │   │
│  │  │  └──────────┘  └──────────┘  │      │  └──────────┘  └──────────┘  │  │   │
│  │  └──────────────────────────────┘      └──────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      现有模块集成层                                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │ ToolRegistry│ SkillRegistry│ Workflow │ Knowledge│  Agent   │      │   │
│  │  │  工具系统  │  技能系统   │  工作流   │  知识库   │  智能体   │      │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      数据存储层                                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │ user_settings│ mcp_servers│ mcp_clients│ mcp_tools│ mcp_logs │      │   │
│  │  │  用户设置  │ MCP服务配置 │ MCP客户端  │ MCP工具   │ MCP日志   │      │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│      外部 MCP 客户端             │   │      外部 MCP 服务端             │
│  ┌──────────┐  ┌──────────┐    │   │  ┌──────────┐  ┌──────────┐    │
│  │  Claude  │  │  Cursor  │    │   │  │  FileSys │  │  GitHub  │    │
│  │ Desktop  │  │   IDE    │    │   │  │  Server  │  │  Server  │    │
│  └──────────┘  └──────────┘    │   │  └──────────┘  └──────────┘    │
└─────────────────────────────────┘   └─────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 MCP Server（服务端）

对外提供 Py Copilot 的能力：

- **自动暴露现有能力**: ToolRegistry、SkillRegistry 自动转换为 MCP Tools
- **知识库作为 Resource**: 知识库文档通过 MCP Resource 协议暴露
- **工作流作为 Tool**: 工作流可作为复合工具被外部调用

#### 2.2.2 MCP Client（客户端）

连接外部 MCP 服务，扩展 Py Copilot 能力：

- **连接管理**: 管理多个外部 MCP 服务连接
- **工具代理**: 将外部 MCP Tools 代理到内部 ToolRegistry
- **服务发现**: 自动发现和缓存外部服务提供的工具

#### 2.2.3 设置集成

与现有设置系统无缝集成：

- **设置类型**: 新增 `mcp` 设置类型
- **前端页面**: 在设置页面下新增 MCP 管理子页面
- **权限控制**: 复用现有用户权限体系

## 3. 数据模型设计

### 3.1 数据库表结构

```sql
-- MCP 服务配置表（作为服务端）
CREATE TABLE mcp_server_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    transport VARCHAR(50) DEFAULT 'sse',  -- sse, stdio, websocket
    host VARCHAR(255) DEFAULT '127.0.0.1',
    port INTEGER DEFAULT 8008,
    enabled BOOLEAN DEFAULT TRUE,
    auth_type VARCHAR(50) DEFAULT 'none',  -- none, api_key, jwt
    auth_config JSON,  -- 认证配置
    exposed_modules JSON,  -- 暴露的模块: ["tools", "skills", "knowledge", "workflows"]
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- MCP 客户端连接配置表
CREATE TABLE mcp_client_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    transport VARCHAR(50) DEFAULT 'sse',
    connection_url VARCHAR(500),
    command VARCHAR(500),  -- stdio 模式下的命令
    enabled BOOLEAN DEFAULT TRUE,
    auto_connect BOOLEAN DEFAULT TRUE,
    auth_config JSON,
    tool_whitelist JSON,  -- 允许使用的工具列表
    tool_blacklist JSON,  -- 禁止使用的工具列表
    last_connected_at DATETIME,
    status VARCHAR(50) DEFAULT 'disconnected',  -- connected, disconnected, error
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- MCP 工具映射表（缓存外部工具信息）
CREATE TABLE mcp_tool_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_config_id INTEGER NOT NULL,
    original_name VARCHAR(255) NOT NULL,  -- 原始工具名
    local_name VARCHAR(255) NOT NULL,     -- 本地映射名（避免冲突）
    description TEXT,
    input_schema JSON,
    enabled BOOLEAN DEFAULT TRUE,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- MCP 调用日志表
CREATE TABLE mcp_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    direction VARCHAR(20) NOT NULL,  -- incoming, outgoing
    connection_name VARCHAR(255),
    tool_name VARCHAR(255),
    request_data JSON,
    response_data JSON,
    status VARCHAR(50),  -- success, error, timeout
    execution_time_ms INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Pydantic 模型

```python
# backend/app/mcp/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TransportType(str, Enum):
    """传输类型"""
    SSE = "sse"
    STDIO = "stdio"
    WEBSOCKET = "websocket"


class AuthType(str, Enum):
    """认证类型"""
    NONE = "none"
    API_KEY = "api_key"
    JWT = "jwt"


class MCPModule(str, Enum):
    """可暴露的模块"""
    TOOLS = "tools"
    SKILLS = "skills"
    KNOWLEDGE = "knowledge"
    WORKFLOWS = "workflows"
    AGENTS = "agents"
    MEMORY = "memory"


# ==================== Server Config ====================

class MCPServerConfigBase(BaseModel):
    """MCP 服务配置基础模型"""
    name: str = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    transport: TransportType = Field(default=TransportType.SSE, description="传输类型")
    host: str = Field(default="127.0.0.1", description="监听地址")
    port: int = Field(default=8008, description="监听端口")
    enabled: bool = Field(default=True, description="是否启用")
    auth_type: AuthType = Field(default=AuthType.NONE, description="认证类型")
    auth_config: Optional[Dict[str, Any]] = Field(default=None, description="认证配置")
    exposed_modules: List[MCPModule] = Field(
        default=[MCPModule.TOOLS, MCPModule.SKILLS],
        description="暴露的模块"
    )


class MCPServerConfigCreate(MCPServerConfigBase):
    """创建 MCP 服务配置"""
    pass


class MCPServerConfigUpdate(BaseModel):
    """更新 MCP 服务配置"""
    name: Optional[str] = None
    description: Optional[str] = None
    transport: Optional[TransportType] = None
    host: Optional[str] = None
    port: Optional[int] = None
    enabled: Optional[bool] = None
    auth_type: Optional[AuthType] = None
    auth_config: Optional[Dict[str, Any]] = None
    exposed_modules: Optional[List[MCPModule]] = None


class MCPServerConfig(MCPServerConfigBase):
    """MCP 服务配置完整模型"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Client Config ====================

class MCPClientConfigBase(BaseModel):
    """MCP 客户端配置基础模型"""
    name: str = Field(..., description="连接名称")
    description: Optional[str] = Field(None, description="连接描述")
    transport: TransportType = Field(default=TransportType.SSE, description="传输类型")
    connection_url: Optional[str] = Field(None, description="连接URL (SSE/WebSocket)")
    command: Optional[str] = Field(None, description="启动命令 (stdio)")
    enabled: bool = Field(default=True, description="是否启用")
    auto_connect: bool = Field(default=True, description="自动连接")
    auth_config: Optional[Dict[str, Any]] = Field(default=None, description="认证配置")
    tool_whitelist: Optional[List[str]] = Field(default=None, description="工具白名单")
    tool_blacklist: Optional[List[str]] = Field(default=None, description="工具黑名单")


class MCPClientConfigCreate(MCPClientConfigBase):
    """创建 MCP 客户端配置"""
    pass


class MCPClientConfigUpdate(BaseModel):
    """更新 MCP 客户端配置"""
    name: Optional[str] = None
    description: Optional[str] = None
    transport: Optional[TransportType] = None
    connection_url: Optional[str] = None
    command: Optional[str] = None
    enabled: Optional[bool] = None
    auto_connect: Optional[bool] = None
    auth_config: Optional[Dict[str, Any]] = None
    tool_whitelist: Optional[List[str]] = None
    tool_blacklist: Optional[List[str]] = None


class MCPClientConfig(MCPClientConfigBase):
    """MCP 客户端配置完整模型"""
    id: int
    user_id: int
    status: str = Field(default="disconnected", description="连接状态")
    error_message: Optional[str] = None
    last_connected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Settings Integration ====================

class MCPSettingsData(BaseModel):
    """MCP 设置数据（用于 SettingService）"""
    server_configs: List[MCPServerConfig] = Field(default_factory=list)
    client_configs: List[MCPClientConfig] = Field(default_factory=list)
    global_enabled: bool = Field(default=True, description="全局启用 MCP")
    default_timeout: int = Field(default=30, description="默认超时时间（秒）")
    max_concurrent_calls: int = Field(default=10, description="最大并发调用数")
    log_enabled: bool = Field(default=True, description="启用调用日志")
```

## 4. 与现有模块集成

### 4.1 设置管理集成

```python
# backend/app/services/setting_service.py 扩展

class SettingService:
    """设置服务类"""

    # 扩展有效设置类型
    VALID_SETTING_TYPES = ["general", "personalization", "emotion", "learning", "relationship", "mcp"]

    @staticmethod
    def get_mcp_settings(db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户 MCP 设置"""
        from app.mcp.services.config_service import MCPConfigService
        
        config_service = MCPConfigService(db)
        server_configs = config_service.get_server_configs(user_id)
        client_configs = config_service.get_client_configs(user_id)
        
        return {
            "server_configs": [config.dict() for config in server_configs],
            "client_configs": [config.dict() for config in client_configs],
            "global_enabled": True,
            "default_timeout": 30,
            "max_concurrent_calls": 10
        }

    @staticmethod
    def save_mcp_settings(db: Session, user_id: int, data: Dict[str, Any]):
        """保存 MCP 设置"""
        # 保存到 user_settings 表
        SettingService.create_or_update_setting(db, user_id, "mcp", data)
```

### 4.2 工作流集成

```python
# backend/app/modules/workflow/nodes/mcp_node.py

from typing import Dict, Any
from app.modules.workflow.models.workflow import WorkflowNode


class MCPNodeExecutor:
    """MCP 节点执行器 - 在工作流中调用 MCP 工具"""

    async def execute(self, node: WorkflowNode, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行 MCP 节点"""
        config = node.config
        
        # 获取 MCP 客户端
        from app.mcp.client import MCPClientManager
        client_manager = MCPClientManager()
        
        # 解析工具引用格式: "client_name:tool_name"
        tool_ref = config.get("tool_ref")
        client_name, tool_name = tool_ref.split(":", 1)
        
        # 获取客户端实例
        client = await client_manager.get_client(client_name)
        
        # 准备参数
        arguments = self._prepare_arguments(config, input_data)
        
        # 调用工具
        result = await client.call_tool(tool_name, arguments)
        
        return {
            "success": not result.is_error,
            "output": result.content,
            "error": result.error if result.is_error else None
        }

    def _prepare_arguments(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备工具参数"""
        arguments = {}
        param_mappings = config.get("param_mappings", {})
        
        for param_name, source in param_mappings.items():
            if source.startswith("input."):
                # 从输入数据获取
                key = source.replace("input.", "")
                arguments[param_name] = input_data.get(key)
            elif source.startswith("config."):
                # 从配置获取
                key = source.replace("config.", "")
                arguments[param_name] = config.get(key)
            else:
                # 直接值
                arguments[param_name] = source
        
        return arguments
```

### 4.3 工具系统集成

```python
# backend/app/mcp/integration/tool_adapter.py

from typing import Dict, Any, List
from app.modules.function_calling.base_tool import BaseTool, ToolParameter
from app.modules.function_calling.tool_registry import ToolRegistry


class ToolToMCPAdapter:
    """将内部工具适配为 MCP Tool 格式"""

    TYPE_MAPPING = {
        "string": "string",
        "integer": "integer",
        "number": "number",
        "boolean": "boolean",
        "array": "array",
        "object": "object"
    }

    def adapt_all_tools(self) -> List[Dict[str, Any]]:
        """适配所有已注册工具"""
        registry = ToolRegistry()
        tools = registry.get_all_tools()
        return [self.adapt_tool(tool) for tool in tools if tool.is_active]

    def adapt_tool(self, tool: BaseTool) -> Dict[str, Any]:
        """将单个工具适配为 MCP 格式"""
        metadata = tool.get_metadata()
        parameters = tool.get_parameters()

        return {
            "name": metadata.name,
            "description": self._build_description(metadata),
            "inputSchema": {
                "type": "object",
                "properties": {
                    param.name: self._adapt_parameter(param)
                    for param in parameters
                },
                "required": [
                    param.name for param in parameters if param.required
                ]
            }
        }

    def _adapt_parameter(self, param: ToolParameter) -> Dict[str, Any]:
        """适配参数定义"""
        schema = {
            "type": self.TYPE_MAPPING.get(param.type, "string"),
            "description": param.description
        }
        
        if param.default is not None:
            schema["default"] = param.default
        
        if param.enum:
            schema["enum"] = param.enum
        
        return schema

    def _build_description(self, metadata) -> str:
        """构建工具描述"""
        parts = [metadata.description]
        
        if metadata.tags:
            parts.append(f"\n标签: {', '.join(metadata.tags)}")
        
        if metadata.category:
            parts.append(f"分类: {metadata.category}")
        
        return "\n".join(parts)


class MCPToToolAdapter:
    """将 MCP Tool 适配为内部工具格式"""

    def __init__(self, client_name: str, mcp_tool: Dict[str, Any]):
        self.client_name = client_name
        self.mcp_tool = mcp_tool
        self.tool_name = mcp_tool["name"]

    def create_wrapper(self) -> BaseTool:
        """创建 MCP 工具的本地包装器"""
        from app.modules.function_calling.base_tool import BaseTool, ToolMetadata, ToolParameter

        class MCPToolWrapper(BaseTool):
            """MCP 工具包装器"""

            def _get_metadata(self) -> ToolMetadata:
                return ToolMetadata(
                    name=f"{self.client_name}:{self.tool_name}",
                    display_name=f"[{self.client_name}] {self.mcp_tool.get('name')}",
                    description=self.mcp_tool.get("description", ""),
                    category="mcp",
                    tags=["mcp", self.client_name]
                )

            def _get_parameters(self) -> List[ToolParameter]:
                schema = self.mcp_tool.get("inputSchema", {})
                properties = schema.get("properties", {})
                required = schema.get("required", [])
                
                return [
                    ToolParameter(
                        name=name,
                        type=prop.get("type", "string"),
                        description=prop.get("description", ""),
                        required=name in required,
                        default=prop.get("default"),
                        enum=prop.get("enum")
                    )
                    for name, prop in properties.items()
                ]

            async def execute(self, **kwargs) -> ToolExecutionResult:
                from app.mcp.client import MCPClientManager
                
                client_manager = MCPClientManager()
                client = await client_manager.get_client(self.client_name)
                
                result = await client.call_tool(self.tool_name, kwargs)
                
                return ToolExecutionResult(
                    success=not result.is_error,
                    result=result.content,
                    error=result.error if result.is_error else None,
                    execution_time=result.execution_time,
                    tool_name=self._get_metadata().name
                )

        return MCPToolWrapper()
```

### 4.4 知识库集成

```python
# backend/app/mcp/integration/knowledge_resource.py

from typing import List, Dict, Any
from app.modules.knowledge.services.knowledge_service import KnowledgeService


class KnowledgeResourceProvider:
    """知识库资源提供者"""

    RESOURCE_PREFIX = "knowledge://"

    async def list_resources(self) -> List[Dict[str, Any]]:
        """列出所有知识库资源"""
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            service = KnowledgeService()
            bases = service.list_knowledge_bases(db)
            
            resources = []
            for base in bases:
                resources.append({
                    "uri": f"{self.RESOURCE_PREFIX}base/{base.id}",
                    "name": base.name,
                    "description": base.description or f"知识库: {base.name}",
                    "mimeType": "application/json"
                })
            
            return resources
        finally:
            db.close()

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取知识库资源"""
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            # 解析 URI: knowledge://base/{base_id} 或 knowledge://doc/{doc_id}
            path = uri.replace(self.RESOURCE_PREFIX, "")
            parts = path.split("/")
            
            if len(parts) < 2:
                raise ValueError(f"无效的 URI: {uri}")
            
            resource_type = parts[0]
            resource_id = parts[1]
            
            service = KnowledgeService()
            
            if resource_type == "base":
                # 获取知识库概览
                base = service.get_knowledge_base(int(resource_id), db)
                documents = service.list_documents(int(resource_id), db)
                
                return {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({
                        "id": base.id,
                        "name": base.name,
                        "description": base.description,
                        "document_count": len(documents),
                        "documents": [
                            {"id": doc.id, "title": doc.title}
                            for doc in documents
                        ]
                    }, ensure_ascii=False, indent=2)
                }
            
            elif resource_type == "doc":
                # 获取文档内容
                doc = service.get_document(int(resource_id), db)
                
                return {
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": doc.content
                }
            
            else:
                raise ValueError(f"未知的资源类型: {resource_type}")
        
        finally:
            db.close()
```

### 4.5 技能系统集成

```python
# backend/app/mcp/integration/skill_adapter.py

from typing import List, Dict, Any
from app.skills.skill_registry import SkillRegistry


class SkillToMCPAdapter:
    """将技能适配为 MCP Tool"""

    def __init__(self):
        self.registry = SkillRegistry()

    async def adapt_all_skills(self) -> List[Dict[str, Any]]:
        """适配所有技能"""
        skills = await self.registry.get_all_skills()
        return [self.adapt_skill(skill) for skill in skills]

    def adapt_skill(self, skill: Dict[str, Any]) -> Dict[str, Any]:
        """将技能转换为 MCP Tool 格式"""
        metadata = skill.get("metadata", {})
        
        return {
            "name": f"skill_{metadata.get('id')}",
            "description": self._build_description(metadata),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "技能输入内容"
                    },
                    "context": {
                        "type": "object",
                        "description": "上下文信息"
                    }
                },
                "required": ["input"]
            }
        }

    def _build_description(self, metadata: Dict[str, Any]) -> str:
        """构建技能描述"""
        parts = [
            metadata.get("description", ""),
            f"\n作者: {metadata.get('author', 'Unknown')}",
            f"版本: {metadata.get('version', '1.0.0')}",
            f"分类: {metadata.get('category', 'general')}"
        ]
        
        tags = metadata.get("tags", [])
        if tags:
            parts.append(f"标签: {', '.join(tags)}")
        
        return "\n".join(parts)


class SkillExecutionHandler:
    """技能执行处理器"""

    def __init__(self):
        self.registry = SkillRegistry()

    async def execute_skill(self, skill_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        skill = self.registry.get_skill(skill_id)
        
        if not skill:
            raise ValueError(f"技能不存在: {skill_id}")
        
        module = skill.get("module")
        if not module:
            raise ValueError(f"技能未加载: {skill_id}")
        
        # 调用技能的 execute 函数
        result = await module.execute(
            input_data=arguments.get("input"),
            context=arguments.get("context", {})
        )
        
        return {
            "content": [{"type": "text", "text": str(result)}],
            "isError": False
        }
```

## 5. API 设计

### 5.1 MCP 管理 API

```python
# backend/app/api/v1/mcp.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.mcp.services.config_service import MCPConfigService
from app.mcp.schemas import (
    MCPServerConfig, MCPServerConfigCreate, MCPServerConfigUpdate,
    MCPClientConfig, MCPClientConfigCreate, MCPClientConfigUpdate
)

router = APIRouter(prefix="/mcp", tags=["MCP"])


# ==================== Server Config APIs ====================

@router.get("/servers", response_model=Dict[str, Any])
async def list_server_configs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取 MCP 服务端配置列表"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        configs = service.get_server_configs(user_id)
        
        return {
            "success": True,
            "data": [config.dict() for config in configs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/servers", response_model=Dict[str, Any])
async def create_server_config(
    config: MCPServerConfigCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建 MCP 服务端配置"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        new_config = service.create_server_config(user_id, config)
        
        return {
            "success": True,
            "data": new_config.dict(),
            "message": "配置创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建配置失败: {str(e)}")


@router.put("/servers/{config_id}", response_model=Dict[str, Any])
async def update_server_config(
    config_id: int,
    config: MCPServerConfigUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新 MCP 服务端配置"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        updated_config = service.update_server_config(user_id, config_id, config)
        
        if not updated_config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        return {
            "success": True,
            "data": updated_config.dict(),
            "message": "配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.delete("/servers/{config_id}", response_model=Dict[str, Any])
async def delete_server_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除 MCP 服务端配置"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        success = service.delete_server_config(user_id, config_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        return {
            "success": True,
            "message": "配置删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除配置失败: {str(e)}")


# ==================== Client Config APIs ====================

@router.get("/clients", response_model=Dict[str, Any])
async def list_client_configs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取 MCP 客户端配置列表"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        configs = service.get_client_configs(user_id)
        
        return {
            "success": True,
            "data": [config.dict() for config in configs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/clients", response_model=Dict[str, Any])
async def create_client_config(
    config: MCPClientConfigCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建 MCP 客户端配置"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        new_config = service.create_client_config(user_id, config)
        
        return {
            "success": True,
            "data": new_config.dict(),
            "message": "配置创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建配置失败: {str(e)}")


@router.post("/clients/{config_id}/connect", response_model=Dict[str, Any])
async def connect_client(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """连接 MCP 客户端"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        
        # 获取配置
        config = service.get_client_config(user_id, config_id)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        # 建立连接
        from app.mcp.client import MCPClientManager
        client_manager = MCPClientManager()
        result = await client_manager.connect(config)
        
        # 更新状态
        service.update_client_status(config_id, "connected" if result.success else "error", 
                                     result.error_message)
        
        return {
            "success": result.success,
            "message": "连接成功" if result.success else f"连接失败: {result.error_message}",
            "tools_discovered": result.tools_discovered
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@router.post("/clients/{config_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_client(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """断开 MCP 客户端连接"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        
        # 断开连接
        from app.mcp.client import MCPClientManager
        client_manager = MCPClientManager()
        await client_manager.disconnect(config_id)
        
        # 更新状态
        service.update_client_status(config_id, "disconnected")
        
        return {
            "success": True,
            "message": "已断开连接"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开连接失败: {str(e)}")


# ==================== Tool Management APIs ====================

@router.get("/tools", response_model=Dict[str, Any])
async def list_mcp_tools(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有 MCP 工具（包括本地暴露和外部连接）"""
    try:
        tools = []
        
        # 1. 本地工具（通过 MCP Server 暴露）
        from app.mcp.integration.tool_adapter import ToolToMCPAdapter
        adapter = ToolToMCPAdapter()
        local_tools = adapter.adapt_all_tools()
        for tool in local_tools:
            tool["source"] = "local"
            tools.append(tool)
        
        # 2. 技能
        from app.mcp.integration.skill_adapter import SkillToMCPAdapter
        skill_adapter = SkillToMCPAdapter()
        skill_tools = await skill_adapter.adapt_all_skills()
        for tool in skill_tools:
            tool["source"] = "skill"
            tools.append(tool)
        
        # 3. 外部客户端工具
        from app.mcp.client import MCPClientManager
        client_manager = MCPClientManager()
        external_tools = await client_manager.get_all_tools()
        for tool in external_tools:
            tool["source"] = "external"
            tools.append(tool)
        
        return {
            "success": True,
            "data": tools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


# ==================== Status API ====================

@router.get("/status", response_model=Dict[str, Any])
async def get_mcp_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取 MCP 整体状态"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 1
        service = MCPConfigService(db)
        
        server_configs = service.get_server_configs(user_id)
        client_configs = service.get_client_configs(user_id)
        
        # 统计连接状态
        connected_clients = sum(1 for c in client_configs if c.status == "connected")
        
        return {
            "success": True,
            "data": {
                "server_enabled": any(s.enabled for s in server_configs),
                "server_count": len(server_configs),
                "client_count": len(client_configs),
                "connected_clients": connected_clients,
                "servers": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "enabled": s.enabled,
                        "transport": s.transport,
                        "endpoint": f"{s.host}:{s.port}" if s.transport == "sse" else "stdio"
                    }
                    for s in server_configs
                ],
                "clients": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "status": c.status,
                        "enabled": c.enabled
                    }
                    for c in client_configs
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
```

## 6. 前端管理页面设计

### 6.1 页面结构

```
设置
├── 通用设置
├── 个性化
├── MCP 服务管理  <-- 新增
│   ├── 服务概览
│   ├── 服务端配置
│   │   ├── 配置列表
│   │   ├── 新建/编辑配置
│   │   └── 启动/停止服务
│   ├── 客户端连接
│   │   ├── 连接列表
│   │   ├── 新建/编辑连接
│   │   ├── 连接/断开
│   │   └── 工具管理
│   ├── 工具浏览器
│   └── 调用日志
├── 情感设置
└── 学习设置
```

### 6.2 关键界面元素

#### 服务端配置页面
- **配置列表**: 显示所有服务端配置，包括状态、传输类型、端口等
- **模块选择**: 复选框选择要暴露的模块（工具、技能、知识库、工作流）
- **启动/停止按钮**: 控制服务的启停
- **连接信息**: 显示连接 URL 和配置示例

#### 客户端连接页面
- **连接列表**: 显示所有外部连接，包括状态、工具数量
- **连接向导**: 支持 SSE URL 或 Stdio 命令配置
- **工具白名单/黑名单**: 控制可用工具
- **连接测试**: 测试连接并发现工具

#### 工具浏览器
- **工具分类**: 本地工具、技能、外部工具
- **工具详情**: 名称、描述、参数、来源
- **启用/禁用**: 控制工具的可用性

## 7. 实现阶段

### 7.1 第一阶段：基础框架与设置集成

- [ ] 数据库迁移脚本（创建 MCP 相关表）
- [ ] MCP 协议核心模型和消息定义
- [ ] 设置系统集成（SettingService 扩展）
- [ ] MCP 配置服务（CRUD 操作）
- [ ] API 接口实现
- [ ] 前端管理页面基础框架

### 7.2 第二阶段：服务端实现

- [ ] SSE Transport 实现
- [ ] Tool Handler（暴露 ToolRegistry）
- [ ] Skill Handler（暴露 SkillRegistry）
- [ ] Resource Handler（暴露知识库）
- [ ] 认证中间件
- [ ] 服务生命周期管理

### 7.3 第三阶段：客户端实现

- [ ] MCP Client Manager
- [ ] 连接池管理
- [ ] 工具发现和缓存
- [ ] MCPToToolAdapter（外部工具代理）
- [ ] 调用日志记录

### 7.4 第四阶段：模块集成

- [ ] 工作流 MCP 节点
- [ ] Agent MCP 工具调用
- [ ] 知识库 Resource 优化
- [ ] 前端页面完善
- [ ] 文档和示例

## 8. 配置示例

### 8.1 环境变量

```env
# MCP 全局配置
MCP_ENABLED=true
MCP_DEFAULT_TIMEOUT=30
MCP_MAX_CONCURRENT_CALLS=10
MCP_LOG_ENABLED=true

# 默认服务端配置
MCP_SERVER_ENABLED=true
MCP_SERVER_TRANSPORT=sse
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8008
```

### 8.2 Claude Desktop 配置

```json
{
  "mcpServers": {
    "py-copilot": {
      "command": "python",
      "args": [
        "-m",
        "app.mcp.cli",
        "--transport",
        "stdio",
        "--config",
        "~/.py-copilot/mcp-config.json"
      ],
      "env": {
        "MCP_API_KEY": "your-api-key"
      }
    }
  }
}
```

## 9. 安全考虑

### 9.1 认证授权

- **API Key**: 简单场景下的认证方式
- **JWT Token**: 与现有用户体系集成
- **请求签名**: 防止请求篡改

### 9.2 权限控制

- **模块级权限**: 控制暴露哪些模块
- **工具级权限**: 白名单/黑名单机制
- **用户隔离**: 多用户环境下的数据隔离

### 9.3 安全防护

- **速率限制**: 防止滥用
- **超时控制**: 防止长时间挂起
- **输入验证**: 防止注入攻击
- **日志审计**: 记录所有调用

## 10. 依赖项

```
# requirements.txt 新增
mcp>=1.0.0          # MCP Python SDK
sse-starlette>=1.6.0 # SSE 支持
```

## 11. 参考文档

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP 规范](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## 12. 附录

### 12.1 术语表

| 术语 | 说明 |
|-----|------|
| MCP | Model Context Protocol，模型上下文协议 |
| Server | MCP 服务端，对外提供能力 |
| Client | MCP 客户端，连接外部服务 |
| Tool | 工具，LLM 可调用的功能 |
| Resource | 资源，LLM 可读取的数据 |
| Transport | 传输层，SSE/Stdio/WebSocket |

### 12.2 版本历史

| 版本 | 日期 | 说明 |
|-----|------|------|
| 1.0.0 | 2026-02-27 | 初始设计文档 |
| 2.0.0 | 2026-02-27 | 优化设计，与现有模块深度集成 |
