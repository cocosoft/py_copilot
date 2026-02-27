# Py Copilot MCP 集成实施方案

## 1. 项目现状分析

### 1.1 技术栈
- **后端**: FastAPI + SQLAlchemy + SQLite/PostgreSQL
- **前端**: React + Vite
- **数据库迁移**: Alembic
- **路由管理**: 动态路由组加载机制
- **设置管理**: 基于 `UserSetting` 模型的 JSON 存储

### 1.2 现有模块
- **设置管理**: `SettingsManager` 组件 + `SettingService` 服务
- **工作流**: `Workflow` 模块，支持节点编排
- **知识库**: `Knowledge` 模块，支持文档管理
- **工具系统**: `ToolRegistry` + `BaseTool` 体系
- **技能系统**: `SkillRegistry` 动态加载技能

### 1.3 代码规范
- 后端: 使用 `app/` 作为 Python 包根目录
- 模型: SQLAlchemy ORM，继承 `Base` 基类
- API: FastAPI Router，在 `app/api/v1/__init__.py` 中注册
- 前端: JSX 组件，使用 `request` 工具调用 API

## 2. 实施阶段规划

### 阶段一：基础框架搭建（预计 3-4 天）

#### 2.1.1 数据库迁移脚本
```
文件: backend/alembic/versions/003_add_mcp_support.py
```

**实施步骤**:
1. 创建 `mcp_server_configs` 表
2. 创建 `mcp_client_configs` 表
3. 创建 `mcp_tool_mappings` 表
4. 创建 `mcp_call_logs` 表

**注意事项**:
- 使用 Alembic 的 `op.create_table` 和 `op.drop_table`
- 字段类型与现有项目保持一致（INTEGER, VARCHAR, JSON, DateTime）
- 添加适当的索引

#### 2.1.2 MCP 协议核心模型
```
目录: backend/app/mcp/
├── __init__.py
├── models.py          # 数据库模型
├── schemas.py         # Pydantic 模型
├── config.py          # MCP 配置
└── constants.py       # 常量定义
```

**实施步骤**:
1. 定义 `MCPServerConfigModel` SQLAlchemy 模型
2. 定义 `MCPClientConfigModel` SQLAlchemy 模型
3. 定义对应的 Pydantic schemas
4. 定义传输类型、认证类型的枚举

#### 2.1.3 配置服务
```
文件: backend/app/mcp/services/config_service.py
```

**实施步骤**:
1. 实现 `MCPConfigService` 类
2. 实现服务端配置的 CRUD
3. 实现客户端配置的 CRUD
4. 实现状态更新方法

#### 2.1.4 API 接口
```
文件: backend/app/api/v1/mcp.py
```

**实施步骤**:
1. 创建 MCP Router
2. 实现 `/mcp/servers` CRUD 接口
3. 实现 `/mcp/clients` CRUD 接口
4. 实现 `/mcp/status` 状态接口
5. 在 `app/api/v1/__init__.py` 中注册路由

**代码示例**:
```python
# backend/app/api/v1/__init__.py 修改
ROUTE_GROUPS = {
    # ... 现有路由组 ...
    'mcp': [
        {'module': 'app.api.v1.mcp', 'prefix': '/mcp', 'tags': ['mcp']}
    ]
}
```

#### 2.1.5 前端设置页面
```
文件: 
- frontend/src/components/SettingsManagement/MCPSettings.jsx
- frontend/src/components/SettingsManagement/MCPSettings.css
```

**实施步骤**:
1. 创建 `MCPSettings` 组件
2. 实现服务端配置管理界面
3. 实现客户端连接管理界面
4. 在 `SettingsManager.jsx` 中添加 MCP 标签页

**代码示例**:
```jsx
// SettingsManager.jsx 修改
const tabs = [
  { id: 'general', label: t('settings.tabs.general') },
  { id: 'personalization', label: t('settings.tabs.personalization') },
  { id: 'emotion', label: t('settings.tabs.emotion') },
  { id: 'learning', label: t('settings.tabs.learning') },
  { id: 'relationship', label: t('settings.tabs.relationship') },
  { id: 'mcp', label: t('settings.tabs.mcp') }  // 新增
];
```

### 阶段二：MCP 服务端实现（预计 4-5 天）

#### 2.2.1 传输层实现
```
目录: backend/app/mcp/transport/
├── __init__.py
├── base.py
├── sse.py
└── stdio.py
```

**实施步骤**:
1. 定义 `BaseTransport` 抽象基类
2. 实现 `SSETransport`（基于 `sse-starlette`）
3. 实现 `StdioTransport`（基于标准输入输出）

**依赖安装**:
```bash
pip install sse-starlette mcp
```

#### 2.2.2 协议处理器
```
目录: backend/app/mcp/handlers/
├── __init__.py
├── base.py
├── tools.py
├── resources.py
└── prompts.py
```

**实施步骤**:
1. 实现 `ToolHandler` - 处理工具列表和调用
2. 实现 `ResourceHandler` - 处理资源列表和读取
3. 实现 `PromptHandler` - 处理提示模板

#### 2.2.3 工具适配器
```
文件: backend/app/mcp/adapters/tool_adapter.py
```

**实施步骤**:
1. 实现 `ToolToMCPAdapter` - 将内部工具转为 MCP 格式
2. 复用现有的 `ToolRegistry` 获取工具列表
3. 实现参数类型映射

#### 2.2.4 技能适配器
```
文件: backend/app/mcp/adapters/skill_adapter.py
```

**实施步骤**:
1. 实现 `SkillToMCPAdapter` - 将技能转为 MCP Tool
2. 复用 `SkillRegistry` 获取技能列表
3. 实现技能执行代理

#### 2.2.5 知识库资源适配器
```
文件: backend/app/mcp/adapters/knowledge_adapter.py
```

**实施步骤**:
1. 实现 `KnowledgeResourceProvider`
2. 定义 URI 格式: `knowledge://base/{id}`, `knowledge://doc/{id}`
3. 实现资源列表和读取方法

#### 2.2.6 MCP 服务器主类
```
文件: backend/app/mcp/server.py
```

**实施步骤**:
1. 实现 `MCPServer` 类
2. 集成传输层和处理器
3. 实现生命周期管理（启动、停止）
4. 实现配置热重载

#### 2.2.7 与 FastAPI 集成
```
文件修改: backend/app/api/main.py
```

**实施步骤**:
1. 在 `startup_event` 中初始化 MCP 服务器
2. 在 `shutdown_event` 中关闭 MCP 服务器
3. 根据配置决定是否启动服务

**代码示例**:
```python
# app/api/main.py 修改
mcp_server = None

@app.on_event("startup")
async def startup_event():
    # ... 现有代码 ...
    
    # 初始化 MCP 服务器
    if settings.mcp_enabled:
        from app.mcp.server import MCPServer
        from app.mcp.services.config_service import MCPConfigService
        
        db = SessionLocal()
        try:
            config_service = MCPConfigService(db)
            server_configs = config_service.get_server_configs(user_id=1)
            
            for config in server_configs:
                if config.enabled:
                    mcp_server = MCPServer(config)
                    await mcp_server.start()
                    logger.info(f"MCP 服务器已启动: {config.name}")
        finally:
            db.close()

@app.on_event("shutdown")
async def shutdown_event():
    # ... 现有代码 ...
    
    # 关闭 MCP 服务器
    if mcp_server:
        await mcp_server.stop()
        logger.info("MCP 服务器已关闭")
```

### 阶段三：MCP 客户端实现（预计 4-5 天）

#### 2.3.1 客户端管理器
```
文件: backend/app/mcp/client/manager.py
```

**实施步骤**:
1. 实现 `MCPClientManager` 单例类
2. 实现连接池管理
3. 实现客户端生命周期管理

#### 2.3.2 客户端连接实现
```
文件: backend/app/mcp/client/connection.py
```

**实施步骤**:
1. 实现 `MCPClientConnection` 类
2. 支持 SSE 和 Stdio 传输
3. 实现工具发现和缓存

#### 2.3.3 外部工具代理
```
文件: backend/app/mcp/client/tool_proxy.py
```

**实施步骤**:
1. 实现 `MCPToToolAdapter`
2. 创建外部工具的本地包装器
3. 将外部工具注册到 `ToolRegistry`

#### 2.3.4 工具同步服务
```
文件: backend/app/mcp/services/tool_sync_service.py
```

**实施步骤**:
1. 实现工具同步逻辑
2. 处理工具名称冲突
3. 实现白名单/黑名单过滤

### 阶段四：模块集成（预计 3-4 天）

#### 2.4.1 工作流 MCP 节点
```
文件: backend/app/modules/workflow/nodes/mcp_node.py
```

**实施步骤**:
1. 实现 `MCPNodeExecutor` 类
2. 在工作流设计器中添加 MCP 节点类型
3. 实现参数映射配置

**前端修改**:
```
文件: frontend/src/components/WorkflowDesigner.jsx
```

#### 2.4.2 Agent MCP 工具调用
```
文件修改: backend/app/agents/agent_engine.py
```

**实施步骤**:
1. 在 Agent 执行引擎中集成 MCP 工具
2. 实现工具调用决策逻辑

#### 2.4.3 前端工具浏览器
```
文件: frontend/src/components/MCP/ToolBrowser.jsx
```

**实施步骤**:
1. 创建工具浏览器组件
2. 显示本地工具、技能、外部工具
3. 实现工具启用/禁用功能

### 阶段五：测试与优化（预计 2-3 天）

#### 2.5.1 单元测试
```
目录: backend/tests/mcp/
```

**测试内容**:
1. 配置服务 CRUD 测试
2. 工具适配器测试
3. 协议处理器测试

#### 2.5.2 集成测试

**测试场景**:
1. MCP 服务端与 Claude Desktop 集成
2. MCP 客户端连接外部服务
3. 工作流中调用 MCP 工具

#### 2.5.3 性能优化

**优化点**:
1. 工具缓存机制
2. 连接池优化
3. 日志记录优化

## 3. 详细实施清单

### 3.1 后端文件清单

| 阶段 | 文件路径 | 说明 | 优先级 |
|------|----------|------|--------|
| 1 | `alembic/versions/003_add_mcp_support.py` | 数据库迁移脚本 | P0 |
| 1 | `app/mcp/__init__.py` | MCP 包初始化 | P0 |
| 1 | `app/mcp/models.py` | 数据库模型 | P0 |
| 1 | `app/mcp/schemas.py` | Pydantic 模型 | P0 |
| 1 | `app/mcp/config.py` | 配置类 | P0 |
| 1 | `app/mcp/constants.py` | 常量定义 | P0 |
| 1 | `app/mcp/services/config_service.py` | 配置服务 | P0 |
| 1 | `app/api/v1/mcp.py` | MCP API 接口 | P0 |
| 2 | `app/mcp/transport/base.py` | 传输层基类 | P0 |
| 2 | `app/mcp/transport/sse.py` | SSE 传输 | P0 |
| 2 | `app/mcp/transport/stdio.py` | Stdio 传输 | P1 |
| 2 | `app/mcp/handlers/base.py` | 处理器基类 | P0 |
| 2 | `app/mcp/handlers/tools.py` | 工具处理器 | P0 |
| 2 | `app/mcp/handlers/resources.py` | 资源处理器 | P1 |
| 2 | `app/mcp/handlers/prompts.py` | 提示处理器 | P2 |
| 2 | `app/mcp/adapters/tool_adapter.py` | 工具适配器 | P0 |
| 2 | `app/mcp/adapters/skill_adapter.py` | 技能适配器 | P0 |
| 2 | `app/mcp/adapters/knowledge_adapter.py` | 知识库适配器 | P1 |
| 2 | `app/mcp/server.py` | MCP 服务器 | P0 |
| 3 | `app/mcp/client/manager.py` | 客户端管理器 | P0 |
| 3 | `app/mcp/client/connection.py` | 客户端连接 | P0 |
| 3 | `app/mcp/client/tool_proxy.py` | 工具代理 | P0 |
| 3 | `app/mcp/services/tool_sync_service.py` | 工具同步服务 | P1 |
| 4 | `app/modules/workflow/nodes/mcp_node.py` | MCP 工作流节点 | P1 |

### 3.2 前端文件清单

| 阶段 | 文件路径 | 说明 | 优先级 |
|------|----------|------|--------|
| 1 | `src/components/SettingsManagement/MCPSettings.jsx` | MCP 设置组件 | P0 |
| 1 | `src/components/SettingsManagement/MCPSettings.css` | 样式文件 | P0 |
| 1 | `src/components/SettingsManagement/MCPServerConfig.jsx` | 服务端配置 | P0 |
| 1 | `src/components/SettingsManagement/MCPClientConfig.jsx` | 客户端配置 | P0 |
| 4 | `src/components/MCP/ToolBrowser.jsx` | 工具浏览器 | P1 |
| 4 | `src/components/MCP/ToolBrowser.css` | 样式文件 | P1 |
| 4 | `src/services/mcpService.js` | MCP API 服务 | P0 |

### 3.3 修改文件清单

| 阶段 | 文件路径 | 修改内容 |
|------|----------|----------|
| 1 | `backend/app/api/v1/__init__.py` | 添加 MCP 路由组 |
| 1 | `backend/app/services/setting_service.py` | 扩展 VALID_SETTING_TYPES |
| 2 | `backend/app/api/main.py` | 添加 MCP 启动/关闭逻辑 |
| 2 | `backend/requirements.txt` | 添加 mcp, sse-starlette 依赖 |
| 1 | `frontend/src/components/SettingsManagement/SettingsManager.jsx` | 添加 MCP 标签页 |
| 1 | `frontend/src/locales/zh-CN/settings.json` | 添加 MCP 相关翻译 |
| 1 | `frontend/src/locales/en-US/settings.json` | 添加 MCP 相关翻译 |

## 4. 依赖管理

### 4.1 Python 依赖

```txt
# backend/requirements.txt 新增

# MCP 支持
mcp>=1.0.0
sse-starlette>=1.6.0
```

### 4.2 Node.js 依赖

无需新增依赖，复用现有 React 生态。

## 5. 配置说明

### 5.1 环境变量

```env
# .env 文件新增

# MCP 全局配置
MCP_ENABLED=true
MCP_DEFAULT_TIMEOUT=30
MCP_MAX_CONCURRENT_CALLS=10
MCP_LOG_ENABLED=true
```

### 5.2 配置文件

MCP 配置存储在数据库中，通过前端界面管理。

## 6. 测试计划

### 6.1 单元测试

```bash
# 运行 MCP 相关测试
pytest backend/tests/mcp/ -v
```

### 6.2 集成测试

1. **服务端测试**:
   - 启动 MCP 服务
   - 使用 Claude Desktop 连接
   - 测试工具调用

2. **客户端测试**:
   - 配置外部 MCP 服务
   - 测试连接和工具发现
   - 测试工具代理

3. **工作流测试**:
   - 创建包含 MCP 节点的工作流
   - 执行工作流
   - 验证结果

## 7. 部署注意事项

### 7.1 数据库迁移

```bash
cd backend
alembic upgrade head
```

### 7.2 依赖安装

```bash
pip install -r requirements.txt
```

### 7.3 配置检查

确保环境变量 `MCP_ENABLED` 设置为 `true`。

## 8. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| MCP SDK 版本变更 | 高 | 锁定版本号，关注官方更新 |
| 性能瓶颈 | 中 | 实现缓存机制，连接池优化 |
| 安全漏洞 | 高 | 实现认证授权，输入验证 |
| 与现有功能冲突 | 中 | 充分测试，渐进式集成 |

## 9. 时间估算

| 阶段 | 预计时间 | 实际时间 |
|------|----------|----------|
| 阶段一：基础框架 | 3-4 天 | - |
| 阶段二：服务端实现 | 4-5 天 | - |
| 阶段三：客户端实现 | 4-5 天 | - |
| 阶段四：模块集成 | 3-4 天 | - |
| 阶段五：测试优化 | 2-3 天 | - |
| **总计** | **16-21 天** | - |

## 10. 验收标准

- [ ] MCP 服务端可正常启动，Claude Desktop 可连接
- [ ] 本地工具、技能可通过 MCP 协议暴露
- [ ] 知识库可作为 Resource 被外部读取
- [ ] 可配置外部 MCP 客户端，工具自动同步到 ToolRegistry
- [ ] 工作流支持 MCP 节点类型
- [ ] 前端设置页面可管理 MCP 配置
- [ ] 所有单元测试通过
- [ ] 集成测试通过
