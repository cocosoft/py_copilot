# Py Copilot CLI 设计方案（优化版）

基于当前项目实际功能分析，优化 CLI 设计方案，使其与现有后端 API 和前端功能保持一致。

## 1. 项目现有功能分析

### 1.1 后端 API 功能模块

| 模块 | 功能 | API 端点 |
|------|------|----------|
| **认证** | 用户注册、登录、JWT Token | `/api/v1/auth/*` |
| **Agent** | 智能体 CRUD、测试、复制、导入导出 | `/api/v1/agents/*` |
| **技能** | 技能管理、执行、仓库同步 | `/api/v1/skills/*` |
| **任务** | 任务创建、分析、执行 | `/api/v1/tasks/*` |
| **工作空间** | 工作空间管理、存储配额 | `/api/v1/workspaces/*` |
| **LLM** | 文本补全、聊天、任务处理 | `/api/v1/llm/*` |
| **记忆** | 记忆 CRUD、搜索、统计分析 | `/api/v1/memories/*` |
| **工具** | 工具注册、执行、历史 | `/api/v1/tools/*` |
| **对话** | 对话管理、消息发送、流式响应 | `/api/v1/conversations/*` |
| **设置** | 用户设置管理 | `/api/v1/settings/*` |
| **文件** | 文件上传、管理 | `/api/v1/file-upload/*` |
| **模型** | 模型管理、能力管理 | `/api/v1/model-management/*` |
| **知识库** | 知识管理、语义搜索 | `/api/v1/knowledge/*` |

### 1.2 前端功能模块

- **聊天界面**：对话、文件上传、模型选择、工具调用
- **Agent 管理**：创建、编辑、分类、参数配置
- **技能市场**：浏览、安装、执行技能
- **任务管理**：创建任务、查看执行状态
- **模型管理**：供应商管理、模型配置、能力管理
- **知识图谱**：实体关系可视化
- **设置中心**：通用、个性化、情感、学习、关系设置
- **工作空间**：多工作空间切换、存储管理

### 1.3 数据库模型

- **User**: 用户、认证
- **Agent**: 智能体、分类、参数
- **Skill**: 技能、版本、依赖
- **Task**: 任务、执行记录
- **Workspace**: 工作空间、存储配额
- **Memory**: 记忆、类型、分类
- **Conversation**: 对话、消息、主题
- **Model**: 模型、供应商、能力

## 2. CLI 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Py Copilot CLI                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │   Command    │  │   Context    │  │   Output     │  │  Config │ │
│  │   Router     │  │   Manager    │  │   Formatter  │  │ Manager │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┬────┘ │
│         │                 │                 │               │      │
│         └─────────────────┴─────────────────┴───────────────┘      │
│                               │                                     │
│                               ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      Service Layer                            │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│  │  │  Auth    │ │  Agent   │ │  Skill   │ │  Conversation    │ │  │
│  │  │ Service  │ │ Service  │ │ Service  │ │    Service       │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│  │  │  Task    │ │  LLM     │ │  Memory  │ │    Workspace     │ │  │
│  │  │ Service  │ │ Service  │ │ Service  │ │    Service       │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               │                                     │
└───────────────────────────────┼─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                          │
│              REST API / WebSocket / Streaming                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 |
|------|------|
| Command Router | 命令解析、路由分发、子命令管理 |
| Context Manager | 会话上下文、工作空间、当前用户状态 |
| Output Formatter | 多种输出格式（table/json/yaml/markdown） |
| Config Manager | 配置文件管理、环境切换、密钥存储 |
| Service Layer | 与后端 API 交互的封装 |

## 3. 命令设计（与现有 API 对齐）

### 3.1 认证命令

```bash
# 登录
py-copilot auth login
py-copilot auth login --email user@example.com --password xxx

# 查看当前用户
py-copilot auth me

# 退出登录
py-copilot auth logout

# 刷新 Token
py-copilot auth refresh
```

### 3.2 智能体命令

```bash
# 列出智能体
py-copilot agent list
py-copilot agent list --category 1 --limit 20

# 查看智能体详情
py-copilot agent get <agent_id>

# 创建智能体
py-copilot agent create --name "代码助手" --description "帮助编写代码" --model gpt-4

# 更新智能体
py-copilot agent update <agent_id> --name "新名称"

# 删除智能体
py-copilot agent delete <agent_id>

# 测试智能体
py-copilot agent test <agent_id> --message "你好"

# 复制智能体
py-copilot agent copy <agent_id> --name "复制的智能体"

# 导出智能体
py-copilot agent export <agent_id> --output agent.json

# 导入智能体
py-copilot agent import --file agent.json

# 搜索智能体
py-copilot agent search "关键词"

# 获取推荐智能体
py-copilot agent recommend
```

### 3.3 对话命令

```bash
# 启动交互式对话（默认智能体）
py-copilot chat

# 使用指定智能体对话
py-copilot chat --agent <agent_id>

# 单次提问
py-copilot chat --agent <agent_id> --message "解释这段代码"

# 流式对话
py-copilot chat --agent <agent_id> --stream

# 列出对话
py-copilot conversation list

# 查看对话历史
py-copilot conversation get <conversation_id>

# 创建新对话
py-copilot conversation create --title "新对话"

# 删除对话
py-copilot conversation delete <conversation_id>

# 发送消息到指定对话
py-copilot conversation send <conversation_id> --message "你好"

# 导出对话
py-copilot conversation export <conversation_id> --output chat.md
```

### 3.4 技能命令

```bash
# 列出已安装技能
py-copilot skill list
py-copilot skill list --source local

# 查看技能详情
py-copilot skill get <skill_id>

# 安装技能
py-copilot skill install <skill_name>
py-copilot skill install --file ./skill.yaml

# 卸载技能
py-copilot skill uninstall <skill_id>

# 更新技能
py-copilot skill update <skill_id>

# 搜索技能
py-copilot skill search "关键词"

# 执行技能
py-copilot skill execute <skill_id> --task "任务描述"
py-copilot skill run <skill_name> --params '{"key": "value"}'

# 查看技能执行历史
py-copilot skill history --limit 20

# 创建技能（脚手架）
py-copilot skill create <skill_name> --template basic

# 验证技能配置
py-copilot skill validate --file ./skill.yaml

# 技能仓库管理
py-copilot skill repo list
py-copilot skill repo add --name my-repo --url https://github.com/user/skills
py-copilot skill repo sync <repo_id>
```

### 3.5 任务命令

```bash
# 列出任务
py-copilot task list
py-copilot task list --status pending

# 查看任务详情
py-copilot task get <task_id>

# 创建任务
py-copilot task create --title "分析代码" --description "分析项目代码质量"

# 更新任务
py-copilot task update <task_id> --priority high

# 删除任务
py-copilot task delete <task_id>

# 执行任务
py-copilot task run <task_id>

# 快速处理任务（无需创建）
py-copilot task process --type translate --text "Hello World" --target-lang zh

# 查看任务日志
py-copilot task logs <task_id>
```

### 3.6 工作空间命令

```bash
# 列出工作空间
py-copilot workspace list

# 查看当前工作空间
py-copilot workspace current

# 切换工作空间
py-copilot workspace switch <workspace_id>

# 创建工作空间
py-copilot workspace create --name "项目A" --description "项目A的工作空间"

# 更新工作空间
py-copilot workspace update <workspace_id> --name "新项目名"

# 删除工作空间
py-copilot workspace delete <workspace_id>

# 设置默认工作空间
py-copilot workspace set-default <workspace_id>

# 查看存储使用情况
py-copilot workspace storage
```

### 3.7 记忆命令

```bash
# 列出记忆
py-copilot memory list
py-copilot memory list --type fact --limit 50

# 查看记忆详情
py-copilot memory get <memory_id>

# 创建记忆
py-copilot memory create --content "重要信息" --type fact --category general

# 更新记忆
py-copilot memory update <memory_id> --content "更新后的内容"

# 删除记忆
py-copilot memory delete <memory_id>

# 搜索记忆
py-copilot memory search "关键词"

# 获取记忆统计
py-copilot memory stats

# 获取记忆模式分析
py-copilot memory patterns

# 获取对话上下文记忆
py-copilot memory context --conversation <conversation_id>
```

### 3.8 模型命令

```bash
# 列出可用模型
py-copilot model list
py-copilot model list --provider openai

# 查看模型详情
py-copilot model get <model_id>

# 设置默认模型
py-copilot model set-default <model_id>

# 查看当前默认模型
py-copilot model default

# 测试模型
py-copilot model test <model_id> --prompt "你好"

# 模型能力查询
py-copilot model capabilities <model_id>

# 本地模型管理
py-copilot model local list
py-copilot model local add --name "llama2" --path /models/llama2
```

### 3.9 LLM 命令

```bash
# 文本补全
py-copilot llm complete "提示文本" --model gpt-4 --max-tokens 500

# 聊天补全
py-copilot llm chat --message "你好" --system "你是一个助手"

# 流式聊天
py-copilot llm chat --message "讲个故事" --stream

# 任务处理
py-copilot llm task --type summarize --text "长文本内容"
py-copilot llm task --type translate --text "Hello" --target-lang zh
py-copilot llm task --type generate_code --text "写一个排序函数"
py-copilot llm task --type sentiment --text "今天天气真好"
```

### 3.10 工具命令

```bash
# 列出可用工具
py-copilot tool list
py-copilot tool list --category web

# 查看工具详情
py-copilot tool get <tool_name>

# 执行工具
py-copilot tool execute <tool_name> --params '{"url": "https://example.com"}'

# 查看工具历史
py-copilot tool history --limit 20

# 清空工具历史
py-copilot tool history --clear

# 工具设置
py-copilot tool settings get
py-copilot tool settings set --auto-execute true --timeout 60
```

### 3.11 文件命令

```bash
# 上传文件
py-copilot file upload <file_path>

# 列出文件
py-copilot file list

# 下载文件
py-copilot file download <file_id> --output ./download/

# 删除文件
py-copilot file delete <file_id>

# 查看文件信息
py-copilot file info <file_id>
```

### 3.12 知识库命令

```bash
# 列出知识库
py-copilot knowledge list

# 添加知识
py-copilot knowledge add <file_path>
py-copilot knowledge add --text "知识内容" --title "知识标题"

# 搜索知识
py-copilot knowledge search "查询内容"

# 查看知识详情
py-copilot knowledge get <knowledge_id>

# 删除知识
py-copilot knowledge delete <knowledge_id>

# 语义搜索
py-copilot knowledge semantic-search "查询语义"
```

### 3.13 设置命令

```bash
# 查看所有设置
py-copilot settings list

# 查看特定设置
py-copilot settings get general
py-copilot settings get personalization

# 更新设置
py-copilot settings set general.language zh-CN
py-copilot settings set personalization.theme dark

# 导出设置
py-copilot settings export --output settings.json

# 导入设置
py-copilot settings import --file settings.json
```

### 3.14 系统命令

```bash
# 查看系统状态
py-copilot status

# 诊断系统
py-copilot doctor

# 查看版本
py-copilot version

# 更新 CLI
py-copilot update

# 查看帮助
py-copilot help
py-copilot help agent
```

### 3.15 配置命令

```bash
# 查看配置
py-copilot config list

# 获取配置项
py-copilot config get api.base_url

# 设置配置项
py-copilot config set api.base_url http://localhost:8000

# 编辑配置文件
py-copilot config edit

# 重置配置
py-copilot config reset
```

## 4. 交互设计

### 4.1 交互式对话模式

```bash
$ py-copilot chat --agent 1

🤖 Py Copilot CLI v1.0.0
智能体: 代码助手 (ID: 1)
模型: GPT-4
工作空间: 默认

输入 /help 查看命令，/exit 退出，/save 保存对话

[2024-01-15 10:30:12] 用户: 你好，帮我写一个 Python 函数
[2024-01-15 10:30:15] 助手: 当然！这是一个计算斐波那契数列的函数：

```python
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib
```

> 这个函数怎么样？需要我解释吗？

[/save fib.py]  
✓ 已保存到 fib.py

[/exit]
再见！👋
```

### 4.2 对话内命令

| 命令 | 描述 |
|------|------|
| `/help` | 显示帮助 |
| `/exit` `/quit` | 退出对话 |
| `/clear` | 清空屏幕 |
| `/reset` | 重置会话 |
| `/save <文件>` | 保存最后回复 |
| `/agent <id>` | 切换智能体 |
| `/model <模型>` | 切换模型 |
| `/workspace <id>` | 切换工作空间 |
| `/file <路径>` | 上传文件 |
| `/search <关键词>` | 搜索知识 |
| `/memory` | 查看相关记忆 |

### 4.3 输出格式

```bash
# 表格格式（默认）
py-copilot agent list

# JSON 格式
py-copilot agent list --format json

# YAML 格式
py-copilot agent list --format yaml

# Markdown 格式
py-copilot agent list --format markdown

# 简洁格式
py-copilot agent list --format simple
```

## 5. 配置文件

### 5.1 配置文件位置

```
~/.py-copilot/
├── config.yaml              # 主配置
├── credentials.yaml         # 凭证（加密存储）
├── cache/                   # 缓存
│   ├── agents/
│   ├── conversations/
│   └── skills/
├── logs/                    # 日志
└── history/                 # 历史记录
```

### 5.2 配置示例

```yaml
# Py Copilot CLI 配置

version: "1.0"

# API 配置
api:
  base_url: "http://localhost:8000"
  timeout: 30
  retry_attempts: 3
  
# 认证配置
auth:
  token_file: "~/.py-copilot/credentials.yaml"
  auto_refresh: true
  
# 默认设置
defaults:
  agent: 1                    # 默认智能体 ID
  workspace: 1                # 默认工作空间 ID
  model: "gpt-4"              # 默认模型
  
# 交互配置
interaction:
  theme: "dark"
  language: "zh-CN"
  auto_complete: true
  syntax_highlight: true
  pager: "less"
  
# 输出配置
output:
  format: "table"             # table/json/yaml/markdown
  color: true
  verbose: false
  
# 对话配置
conversation:
  auto_save: true
  max_history: 100
  stream: true
  
# 日志配置
logging:
  level: "info"
  file: "~/.py-copilot/logs/copilot.log"
  max_size: "10MB"
  max_files: 5
```

## 6. 与现有 API 的映射

### 6.1 命令到 API 的映射

| CLI 命令 | API 端点 | 方法 |
|----------|----------|------|
| `auth login` | `/api/v1/auth/login` | POST |
| `auth me` | `/api/v1/auth/me` | GET |
| `agent list` | `/api/v1/agents/` | GET |
| `agent get <id>` | `/api/v1/agents/{id}` | GET |
| `agent create` | `/api/v1/agents/` | POST |
| `agent update <id>` | `/api/v1/agents/{id}` | PUT |
| `agent delete <id>` | `/api/v1/agents/{id}` | DELETE |
| `skill list` | `/api/v1/skills/` | GET |
| `skill execute <id>` | `/api/v1/skills/{id}/execute` | POST |
| `task list` | `/api/v1/tasks/` | GET |
| `task create` | `/api/v1/tasks/` | POST |
| `workspace list` | `/api/v1/workspaces/` | GET |
| `conversation list` | `/api/v1/conversations/` | GET |
| `conversation send` | `/api/v1/conversations/{id}/messages` | POST |
| `memory list` | `/api/v1/memories/` | GET |
| `memory search` | `/api/v1/memories/search` | POST |
| `llm complete` | `/api/v1/llm/completions/text` | POST |
| `llm chat` | `/api/v1/llm/completions/chat` | POST |
| `tool list` | `/api/v1/tools/` | GET |
| `file upload` | `/api/v1/file-upload/upload` | POST |
| `settings list` | `/api/v1/settings/` | GET |

## 7. 技术实现

### 7.1 技术栈

| 组件 | 技术 |
|------|------|
| CLI 框架 | Typer (基于 Click) |
| HTTP 客户端 | httpx |
| 配置管理 | Pydantic + YAML |
| 交互界面 | Rich + Prompt Toolkit |
| 自动补全 | argcomplete |
| 密钥存储 | keyring |
| 打包 | PyInstaller / Poetry |

### 7.2 项目结构

```
py-copilot-cli/
├── py_copilot_cli/
│   ├── __init__.py
│   ├── main.py              # CLI 入口
│   ├── commands/            # 命令模块
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── agent.py
│   │   ├── chat.py
│   │   ├── conversation.py
│   │   ├── skill.py
│   │   ├── task.py
│   │   ├── workspace.py
│   │   ├── memory.py
│   │   ├── model.py
│   │   ├── llm.py
│   │   ├── tool.py
│   │   ├── file.py
│   │   ├── knowledge.py
│   │   ├── settings.py
│   │   └── system.py
│   ├── services/            # API 服务封装
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── auth.py
│   │   ├── agent.py
│   │   ├── skill.py
│   │   └── ...
│   ├── core/                # 核心功能
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── context.py
│   │   ├── auth.py
│   │   └── output.py
│   ├── utils/               # 工具函数
│   │   ├── __init__.py
│   │   ├── formatters.py
│   │   ├── validators.py
│   │   └── helpers.py
│   └── templates/           # 模板文件
│       └── skill/
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

## 8. 安装与使用

### 8.1 安装

```bash
# 通过 pip 安装
pip install py-copilot-cli

# 通过源码安装
git clone https://github.com/user/py-copilot-cli.git
cd py-copilot-cli
pip install -e .
```

### 8.2 初始化配置

```bash
# 初始化配置
py-copilot init

# 配置 API 地址
py-copilot config set api.base_url http://localhost:8000

# 登录
py-copilot auth login
```

### 8.3 快速开始

```bash
# 查看状态
py-copilot status

# 列出智能体
py-copilot agent list

# 开始对话
py-copilot chat --agent 1

# 执行技能
py-copilot skill run code-generator --params '{"language": "python"}'
```

## 9. 开发计划

### 9.1 版本规划

| 版本 | 功能 | 时间 |
|------|------|------|
| v0.1.0 | 基础命令、认证、Agent 管理 | 第1阶段 |
| v0.2.0 | 对话、技能、任务 | 第2阶段 |
| v0.3.0 | 工作空间、记忆、模型 | 第3阶段 |
| v0.4.0 | 工具、文件、知识库 | 第4阶段 |
| v1.0.0 | 完整功能、稳定 API | 第5阶段 |

## 10. 总结

本 CLI 设计方案基于 Py Copilot 现有后端 API 和前端功能，提供了完整的命令行交互能力。主要特点：

1. **与现有系统对齐**：命令设计与后端 API 一一对应
2. **功能完整覆盖**：支持所有现有功能模块
3. **交互友好**：支持交互式对话、自动补全、多种输出格式
4. **配置灵活**：支持多环境、多工作空间
5. **易于扩展**：模块化设计，方便添加新命令

这个设计方案可以直接指导 CLI 的开发实现。
