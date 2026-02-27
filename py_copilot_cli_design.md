# Py Copilot CLI 设计方案

## 1. 概述

Py Copilot CLI 是一个命令行界面工具，旨在让用户能够通过终端与 AI 助手进行交互，执行各种自动化任务。设计理念参考 OpenClaw，强调**真正能做事的 AI 助手**，不仅能聊天，还能实际执行代码、管理项目、自动化工作流。

## 2. 设计目标

- **简洁高效**：通过命令行快速完成任务，无需打开图形界面
- **功能丰富**：支持代码生成、项目管理、自动化任务、系统监控等
- **可扩展性**：插件化架构，支持自定义技能扩展
- **智能化**：深度集成 AI 能力，理解上下文，提供智能建议
- **本地化**：优先在本地运行，保护用户隐私

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Py Copilot CLI                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Command   │  │   Agent     │  │   Skill     │  │  Config │ │
│  │   Parser    │  │   Engine    │  │   Manager   │  │ Manager │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬────┘ │
│         │                │                │              │      │
│         └────────────────┴────────────────┴──────────────┘      │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Core Services                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │   │
│  │  │  LLM     │ │  Memory  │ │  Tool    │ │  Execution   │ │   │
│  │  │ Service  │ │ Service  │ │ Registry │ │   Engine     │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API Gateway                        │
│              (WebSocket / HTTP / REST API)                      │
└─────────────────────────────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │   Agent     │     │   Skill     │     │   File      │
   │   Service   │     │   Service   │     │   Service   │
   └─────────────┘     └─────────────┘     └─────────────┘
```

### 3.2 模块职责

| 模块 | 职责 |
|------|------|
| Command Parser | 解析用户输入的命令，支持子命令和参数 |
| Agent Engine | 与 AI Agent 交互，管理对话上下文 |
| Skill Manager | 管理技能的安装、卸载、更新和调用 |
| Config Manager | 管理用户配置，支持多环境配置 |
| LLM Service | 与各种 LLM 模型交互（OpenAI、Claude、本地模型等） |
| Memory Service | 管理对话历史、长期记忆和知识检索 |
| Tool Registry | 注册和管理可用工具 |
| Execution Engine | 执行代码、命令和自动化任务 |

## 4. 命令设计

### 4.1 命令结构

```
py-copilot [全局选项] <命令> [子命令] [选项] [参数]
```

### 4.2 核心命令

#### 4.2.1 对话交互命令

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `chat` | `c` | 启动交互式对话模式 | `py-copilot chat` |
| `ask` | `a` | 单次提问 | `py-copilot ask "解释这段代码"` |
| `code` | - | 生成代码 | `py-copilot code "创建一个Python爬虫"` |
| `review` | - | 代码审查 | `py-copilot review file.py` |
| `explain` | `exp` | 解释代码 | `py-copilot explain function.py` |

#### 4.2.2 项目管理命令

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `project` | `proj` | 项目管理 | `py-copilot project init` |
| `project init` | - | 初始化项目 | `py-copilot project init --template flask` |
| `project analyze` | - | 分析项目结构 | `py-copilot project analyze` |
| `project build` | - | 构建项目 | `py-copilot project build` |
| `project test` | - | 运行测试 | `py-copilot project test` |

#### 4.2.3 技能管理命令

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `skill` | `s` | 技能管理 | `py-copilot skill list` |
| `skill list` | `ls` | 列出已安装技能 | `py-copilot skill list` |
| `skill install` | `i` | 安装技能 | `py-copilot skill install web-scraper` |
| `skill uninstall` | `rm` | 卸载技能 | `py-copilot skill uninstall web-scraper` |
| `skill update` | `up` | 更新技能 | `py-copilot skill update web-scraper` |
| `skill search` | `find` | 搜索技能 | `py-copilot skill search "爬虫"` |
| `skill create` | `new` | 创建新技能 | `py-copilot skill create my-skill` |
| `skill info` | - | 查看技能详情 | `py-copilot skill info web-scraper` |

#### 4.2.4 配置管理命令

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `config` | `cfg` | 配置管理 | `py-copilot config get model` |
| `config get` | - | 获取配置项 | `py-copilot config get model.name` |
| `config set` | - | 设置配置项 | `py-copilot config set model.name gpt-4` |
| `config list` | `ls` | 列出所有配置 | `py-copilot config list` |
| `config reset` | - | 重置配置 | `py-copilot config reset` |
| `config edit` | - | 编辑配置文件 | `py-copilot config edit` |

#### 4.2.5 系统管理命令

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `status` | `st` | 查看系统状态 | `py-copilot status` |
| `doctor` | - | 诊断系统问题 | `py-copilot doctor` |
| `update` | `up` | 更新 CLI | `py-copilot update` |
| `version` | `v` | 查看版本 | `py-copilot version` |
| `login` | - | 登录账户 | `py-copilot login` |
| `logout` | - | 登出账户 | `py-copilot logout` |

#### 4.2.6 任务与自动化命令

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `task` | `t` | 任务管理 | `py-copilot task list` |
| `task list` | `ls` | 列出任务 | `py-copilot task list` |
| `task run` | - | 运行任务 | `py-copilot task run daily-backup` |
| `task create` | `new` | 创建任务 | `py-copilot task create --cron "0 9 * * *"` |
| `task delete` | `rm` | 删除任务 | `py-copilot task delete task-id` |
| `run` | `r` | 执行脚本或命令 | `py-copilot run "python script.py"` |

#### 4.2.7 文件与代码操作命令

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `file` | `f` | 文件操作 | `py-copilot file search "TODO"` |
| `file search` | `grep` | 搜索文件内容 | `py-copilot file search "function" --type py` |
| `file edit` | `e` | 编辑文件 | `py-copilot file edit file.py --line 10` |
| `file create` | `touch` | 创建文件 | `py-copilot file create new.py` |
| `file read` | `cat` | 读取文件 | `py-copilot file read file.py` |
| `refactor` | `ref` | 重构代码 | `py-copilot refactor file.py` |
| `test` | - | 生成测试 | `py-copilot test generate file.py` |
| `doc` | - | 生成文档 | `py-copilot doc generate file.py` |

#### 4.2.8 知识库命令

| 命令 | 别名 | 描述 | 示例 |
|------|------|------|------|
| `knowledge` | `kb` | 知识库管理 | `py-copilot knowledge add doc.pdf` |
| `knowledge add` | - | 添加知识 | `py-copilot knowledge add document.pdf` |
| `knowledge search` | `find` | 搜索知识 | `py-copilot knowledge search "API设计"` |
| `knowledge list` | `ls` | 列出知识库 | `py-copilot knowledge list` |
| `knowledge remove` | `rm` | 删除知识 | `py-copilot knowledge remove doc-id` |

### 4.3 全局选项

| 选项 | 描述 | 示例 |
|------|------|------|
| `-v, --verbose` | 详细输出模式 | `py-copilot -v chat` |
| `-q, --quiet` | 静默模式 | `py-copilot -q run script.py` |
| `-h, --help` | 显示帮助 | `py-copilot --help` |
| `--version` | 显示版本 | `py-copilot --version` |
| `-c, --config` | 指定配置文件 | `py-copilot -c custom.yaml chat` |
| `-m, --model` | 指定模型 | `py-copilot -m gpt-4 ask "问题"` |
| `--no-color` | 禁用颜色输出 | `py-copilot --no-color status` |

## 5. 交互设计

### 5.1 交互式对话模式

```bash
$ py-copilot chat

🤖 Py Copilot v1.0.0
模型: GPT-4 | 会话: default
输入 /help 查看可用命令，/exit 退出

> 帮我写一个Python函数，计算斐波那契数列

当然！这是一个计算斐波那契数列的Python函数：

```python
def fibonacci(n):
    """
    计算斐波那契数列的前n项
    
    参数:
        n: 要计算的项数
        
    返回:
        包含斐波那契数列的列表
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# 示例使用
print(fibonacci(10))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

需要我解释这个函数的工作原理吗？

> /save fib.py
✓ 已保存到 fib.py

> /exit
再见！👋
```

### 5.2 对话内命令

在交互式对话模式中，支持以下特殊命令：

| 命令 | 描述 |
|------|------|
| `/help` | 显示帮助信息 |
| `/exit` 或 `/quit` | 退出对话 |
| `/clear` | 清空屏幕 |
| `/reset` | 重置会话上下文 |
| `/save <文件名>` | 保存最后一条回复到文件 |
| `/model <模型名>` | 切换模型 |
| `/mode <模式>` | 切换模式（code/chat/expert） |
| `/history` | 显示对话历史 |
| `/undo` | 撤销上一步操作 |

### 5.3 智能提示与补全

```bash
# 命令自动补全
$ py-copilot sk<TAB>
skill  

# 参数提示
$ py-copilot skill install <TAB>
web-scraper    code-analyzer   git-helper      api-tester

# 选项提示
$ py-copilot ask --<TAB>
--model     --temperature   --max-tokens    --context
```

## 6. 配置文件

### 6.1 配置文件位置

```
~/.py-copilot/
├── config.yaml          # 主配置文件
├── skills/              # 技能目录
│   ├── installed/       # 已安装技能
│   └── custom/          # 自定义技能
├── cache/               # 缓存目录
├── logs/                # 日志目录
└── history/             # 历史记录
```

### 6.2 配置文件示例

```yaml
# Py Copilot 配置文件

# 版本
version: "1.0"

# 模型配置
model:
  default: "gpt-4"
  fallback: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 4096
  
  # 模型提供商配置
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      base_url: "https://api.openai.com/v1"
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
    local:
      base_url: "http://localhost:11434"

# 技能配置
skills:
  auto_update: true
  registry_url: "https://skills.py-copilot.dev"
  installed:
    - name: "web-scraper"
      version: "1.2.0"
      enabled: true
    - name: "git-helper"
      version: "2.0.1"
      enabled: true

# 交互配置
interaction:
  theme: "dark"  # dark/light/auto
  language: "zh-CN"
  auto_complete: true
  syntax_highlight: true
  pager: "less"

# 记忆配置
memory:
  enabled: true
  max_history: 100
  persist_conversations: true
  knowledge_base:
    enabled: true
    embedding_model: "text-embedding-ada-002"

# 执行配置
execution:
  sandbox_mode: false
  allowed_commands:
    - "python"
    - "pip"
    - "git"
    - "pytest"
  timeout: 30

# 日志配置
logging:
  level: "info"  # debug/info/warning/error
  file: "~/.py-copilot/logs/copilot.log"
  max_size: "10MB"
  max_files: 5

# 后端连接配置
backend:
  url: "http://localhost:8000"
  websocket_url: "ws://localhost:8000/ws"
  timeout: 30
  retry_attempts: 3
```

## 7. 技能系统

### 7.1 技能结构

```
skill-name/
├── skill.yaml           # 技能元数据
├── main.py              # 技能入口
├── requirements.txt     # 依赖
├── README.md            # 技能文档
└── templates/           # 模板文件
    └── template.j2
```

### 7.2 技能元数据示例

```yaml
# skill.yaml
name: "web-scraper"
version: "1.2.0"
description: "网页数据抓取技能"
author: "Py Copilot Team"
tags: ["web", "scraping", "data"]

# 依赖
requirements:
  python: ">=3.8"
  packages:
    - "requests>=2.28.0"
    - "beautifulsoup4>=4.11.0"

# 命令定义
commands:
  - name: "scrape"
    description: "抓取网页内容"
    args:
      - name: "url"
        type: "string"
        required: true
        description: "目标URL"
      - name: "selector"
        type: "string"
        required: false
        description: "CSS选择器"
  
  - name: "batch"
    description: "批量抓取"
    args:
      - name: "urls"
        type: "array"
        required: true

# 权限
permissions:
  network: true
  filesystem: ["read", "write"]
  shell: false
```

### 7.3 内置技能

| 技能名称 | 描述 | 命令示例 |
|----------|------|----------|
| `code-generator` | 代码生成 | `py-copilot skill run code-generator python "排序算法"` |
| `git-helper` | Git 操作辅助 | `py-copilot skill run git-helper commit "提交信息"` |
| `file-manager` | 文件管理 | `py-copilot skill run file-manager organize ./downloads` |
| `api-tester` | API 测试 | `py-copilot skill run api-test test.yaml` |
| `doc-generator` | 文档生成 | `py-copilot skill run doc-generator src/ docs/` |
| `test-writer` | 测试生成 | `py-copilot skill run test-writer file.py` |

## 8. 安全设计

### 8.1 执行安全

```yaml
# 安全配置
security:
  # 沙箱模式
  sandbox:
    enabled: true
    mode: "docker"  # docker/vms/none
    
  # 命令白名单
  command_whitelist:
    - "python"
    - "pip"
    - "git"
    - "pytest"
    - "black"
    - "flake8"
  
  # 危险命令黑名单
  command_blacklist:
    - "rm -rf /"
    - "format"
    - "dd"
  
  # 文件访问限制
  file_access:
    allowed_paths:
      - "~/projects"
      - "~/workspace"
    blocked_paths:
      - "~/.ssh"
      - "/etc"
      - "/usr/bin"
  
  # 网络访问限制
  network:
    allowed_hosts:
      - "api.openai.com"
      - "api.github.com"
    blocked_hosts: []
```

### 8.2 权限确认

```bash
$ py-copilot run "rm -rf ./temp"

⚠️  检测到潜在危险操作
命令: rm -rf ./temp
影响: 将删除 ./temp 目录及其所有内容

是否继续? [y/N]: 
```

## 9. 输出格式

### 9.1 支持格式

| 格式 | 选项 | 用途 |
|------|------|------|
| 终端彩色 | `--format terminal` (默认) | 交互式显示 |
| JSON | `--format json` | 脚本处理 |
| YAML | `--format yaml` | 配置文件 |
| Markdown | `--format markdown` | 文档导出 |
| 纯文本 | `--format text` | 简单输出 |

### 9.2 JSON 输出示例

```bash
$ py-copilot skill list --format json
```

```json
{
  "skills": [
    {
      "name": "web-scraper",
      "version": "1.2.0",
      "description": "网页数据抓取技能",
      "enabled": true,
      "installed_at": "2024-01-15T10:30:00Z"
    },
    {
      "name": "git-helper",
      "version": "2.0.1",
      "description": "Git操作辅助",
      "enabled": true,
      "installed_at": "2024-01-16T14:20:00Z"
    }
  ],
  "total": 2
}
```

## 10. 错误处理

### 10.1 错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| 1 | 通用错误 | 查看错误信息 |
| 2 | 配置错误 | 检查配置文件 |
| 3 | 网络错误 | 检查网络连接 |
| 4 | API 错误 | 检查 API 密钥和配额 |
| 5 | 权限错误 | 检查文件权限 |
| 6 | 执行超时 | 增加超时时间 |
| 7 | 命令未找到 | 检查命令拼写 |
| 8 | 技能错误 | 检查技能安装状态 |

### 10.2 错误输出示例

```bash
$ py-copilot skill install invalid-skill

❌ 错误: 技能 "invalid-skill" 不存在

可能的原因:
1. 技能名称拼写错误
2. 技能尚未发布到技能仓库
3. 技能已被弃用

建议操作:
• 使用 "py-copilot skill search <关键词>" 搜索可用技能
• 访问 https://skills.py-copilot.dev 浏览技能目录
• 检查技能名称拼写

错误码: 7
```

## 11. 集成与扩展

### 11.1 Shell 集成

```bash
# Bash/Zsh 自动补全
source <(py-copilot completion bash)
source <(py-copilot completion zsh)

# PowerShell 自动补全
py-copilot completion powershell | Out-String | Invoke-Expression

# Fish 自动补全
py-copilot completion fish | source
```

### 11.2 CI/CD 集成

```yaml
# GitHub Actions 示例
- name: Code Review with Py Copilot
  run: |
    py-copilot review --format json --output review.json
    py-copilot test generate --coverage
```

### 11.3 IDE 集成

| IDE | 集成方式 |
|-----|----------|
| VS Code | 通过插件调用 CLI |
| PyCharm | 外部工具配置 |
| Vim/Neovim | 插件 + 命令映射 |
| Emacs | 包 + 函数绑定 |

## 12. 开发计划

### 12.1 版本规划

| 版本 | 功能 | 时间 |
|------|------|------|
| v0.1.0 | 基础命令、对话模式、配置管理 | 第1阶段 |
| v0.2.0 | 技能系统、代码生成、代码审查 | 第2阶段 |
| v0.3.0 | 项目管理、任务自动化、知识库 | 第3阶段 |
| v1.0.0 | 完整功能、稳定 API、文档完善 | 第4阶段 |

### 12.2 技术栈

| 组件 | 技术 |
|------|------|
| CLI 框架 | Click / Typer |
| HTTP 客户端 | httpx |
| 配置管理 | Pydantic + YAML |
| 交互式界面 | Rich / Prompt Toolkit |
| 自动补全 | argcomplete |
| 插件系统 | Pluggy |
| 测试 | pytest |
| 打包 | PyInstaller / Poetry |

## 13. 总结

Py Copilot CLI 是一个功能强大、设计优雅的命令行 AI 助手工具。通过参考 OpenClaw 的设计理念，我们构建了一个真正能做事的 CLI 工具，它不仅能进行智能对话，还能实际执行代码、管理项目、自动化任务。

核心特点：
- **简洁的命令设计**：直观易记，支持别名
- **丰富的功能覆盖**：对话、代码、项目管理、技能扩展
- **灵活的配置系统**：支持多环境、多模型
- **强大的技能系统**：可扩展、可复用
- **完善的安全机制**：沙箱、白名单、权限确认
- **良好的集成能力**：Shell、CI/CD、IDE

这个设计方案为 Py Copilot CLI 的开发提供了清晰的路线图和实现指南。
