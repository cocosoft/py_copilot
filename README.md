# Py Copilot

Py Copilot 是一个功能强大的AI智能助手平台，提供多种AI功能，帮助用户提高工作效率。该平台采用前后端分离架构，支持多模态交互，包括聊天、图像、视频、语音等功能。

## 功能特性

### 核心功能

- **聊天功能**：与智能体进行自然语言对话，支持上下文理解
- **智能体管理**：创建、配置和使用不同的AI智能体
- **多模态支持**：
  - 图像生成和处理
  - 视频生成和编辑
  - 语音识别和合成
  - 多语言翻译
- **知识库**：管理和使用知识文档，支持语义搜索
- **知识图谱**：可视化展示知识实体和关系
- **工作流管理**：创建和执行AI工作流，自动化复杂任务
- **模型管理**：管理AI模型和供应商，配置模型参数

### 管理功能

- **用户认证**：注册、登录和权限管理
- **能力管理**：管理AI能力类型和维度
- **参数模板**：创建和管理模型参数模板
- **供应商管理**：管理AI服务供应商

## 技术栈

### 后端

- **框架**：FastAPI (Python)
- **数据库**：SQLAlchemy ORM (支持多种关系型数据库)
- **认证**：JWT (JSON Web Tokens)
- **API文档**：自动生成OpenAPI文档
- **中间件**：CORS支持、性能监控

### 前端

- **框架**：React 18
- **路由**：React Router v6
- **状态管理**：React Query (数据获取和缓存)
- **HTTP客户端**：Axios (带拦截器)
- **UI组件**：自定义组件库
- **开发工具**：Vite

### 桌面应用

- **框架**：Electron
- **功能**：桌面端运行支持，系统托盘集成

## 架构设计

### 整体架构

Py Copilot 采用前后端分离的微服务架构：

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  前端应用       │     │  后端API服务    │     │  数据库         │
│  (React)        │────►│  (FastAPI)      │────►│  (SQLAlchemy)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 后端架构

后端采用模块化设计，每个功能模块独立开发和部署：

```
backend/
├── app/
│   ├── api/           # API路由层
│   │   ├── endpoints/ # 端点定义
│   │   └── v1/        # v1版本API
│   ├── core/          # 核心配置和工具
│   ├── models/        # 数据模型
│   ├── modules/       # 功能模块
│   │   ├── auth/      # 认证模块
│   │   ├── capability_category/ # 能力分类模块
│   │   ├── conversation/ # 对话模块
│   │   ├── knowledge/ # 知识库模块
│   │   ├── llm/       # LLM模块
│   │   ├── supplier_model_management/ # 供应商模型管理
│   │   └── workflow/  # 工作流模块
│   ├── schemas/       # 数据验证和序列化
│   ├── services/      # 业务逻辑层
│   ├── shared/        # 共享基础类
│   └── utils/         # 工具函数
├── config/            # 配置文件
├── init_db.py         # 数据库初始化脚本
└── run_server.py      # 应用入口
```

### 前端架构

前端采用组件化设计，基于React Router进行路由管理：

```
frontend/
├── src/
│   ├── components/    # UI组件
│   │   ├── CapabilityManagement/ # 能力管理组件
│   │   ├── Common/    # 通用组件
│   │   ├── Layout/    # 布局组件
│   │   ├── ModelManagement/ # 模型管理组件
│   │   ├── SkillManagement/ # 技能管理组件
│   │   ├── SupplierManagement/ # 供应商管理组件
│   │   └── UI/        # 基础UI组件
│   ├── config/        # 应用配置
│   ├── configs/       # 其他配置文件
│   ├── contexts/      # React上下文
│   ├── hooks/         # 自定义React hooks
│   ├── pages/         # 页面组件
│   │   ├── Home/      # 首页
│   │   ├── Chat/      # 聊天页面
│   │   ├── Agent/     # 智能体页面
│   │   ├── Image/     # 图像功能
│   │   ├── Video/     # 视频功能
│   │   ├── Voice/     # 语音功能
│   │   ├── Translate/ # 翻译功能
│   │   ├── Knowledge/ # 知识库
│   │   ├── KnowledgeGraphPage/ # 知识图谱
│   │   ├── ModelsPage/ # 模型页面
│   │   ├── Workflow/  # 工作流
│   │   ├── Tool/      # 工具页面
│   │   ├── PersonalCenter/ # 个人中心
│   │   ├── HelpCenter/ # 帮助中心
│   │   └── Settings/  # 设置页面
│   ├── routes/        # 路由配置
│   ├── services/      # API服务层
│   ├── stores/        # 状态管理
│   ├── styles/        # 全局样式
│   ├── utils/         # 工具函数
│   ├── App.jsx        # 应用入口组件
│   └── main.jsx       # React入口文件
```

## 应用内的相关关系

### 前后端交互

1. **API通信**：前端通过axios库与后端API进行通信，所有请求都经过统一的API客户端处理
2. **认证机制**：用户登录后获取JWT令牌，前端存储在localStorage中，每次请求自动添加Authorization头
3. **数据状态管理**：使用React Query进行数据获取、缓存和状态管理，提高应用性能

### 组件依赖关系

1. **页面组件**：每个页面由多个功能组件组成
2. **功能组件**：封装特定功能，可在多个页面复用
3. **基础UI组件**：提供基础UI元素，如按钮、输入框、模态框等

### 模块间关系

1. **认证模块**：为其他模块提供用户认证功能
2. **对话模块**：依赖LLM模块进行自然语言处理
3. **知识库模块**：与对话模块集成，提供知识支持
4. **工作流模块**：协调多个AI能力，实现复杂任务自动化

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 8+

### 后端部署

1. 安装依赖：

```bash
cd backend
pip install -r requirements.txt
```

2. 配置环境变量：

```bash
cp .env.example .env
# 编辑.env文件，配置数据库连接等参数
```

3. 初始化数据库：

```bash
python init_db.py
```

4. 启动后端服务：

```bash
python run_server.py
```

后端服务将在 http://localhost:8000 启动

### 前端部署

1. 安装依赖：

```bash
cd frontend
npm install
```

2. 配置环境变量：

```bash
cp .env.example .env
# 编辑.env文件，配置API基础URL
```

3. 启动前端开发服务器：

```bash
npm run dev
```

前端服务将在 http://localhost:5173 启动

### 访问应用

在浏览器中访问 http://localhost:5173，即可使用Py Copilot应用

## 使用说明

### 用户认证

1. 访问登录页面：http://localhost:5173/login
2. 点击"注册"按钮创建新账户
3. 使用注册的账户登录

### 聊天功能

1. 登录后，点击左侧菜单的"聊天"选项
2. 在聊天输入框中输入问题或指令
3. 点击发送按钮，与智能体进行对话

### 智能体管理

1. 点击左侧菜单的"智能体"选项
2. 可以查看、创建和管理不同的智能体
3. 选择一个智能体后，可以与它进行对话

### 多模态功能

1. **图像功能**：点击左侧菜单的"图像"选项，使用图像生成和处理功能
2. **视频功能**：点击左侧菜单的"视频"选项，使用视频生成和编辑功能
3. **语音功能**：点击左侧菜单的"语音"选项，使用语音识别和合成功能
4. **翻译功能**：点击左侧菜单的"翻译"选项，使用多语言翻译功能

### 知识库管理

1. 点击左侧菜单的"知识库"选项
2. 可以管理知识文档，进行语义搜索
3. 点击"知识图谱"选项，可以查看知识实体和关系的可视化展示

### 模型管理

1. 点击左侧菜单的"设置"选项
2. 在设置页面中，可以查看和配置AI模型、供应商、参数模板等
3. 可以管理系统参数和参数归一化规则

### 工作流管理

1. 点击左侧菜单的"工作流"选项
2. 可以创建和执行AI工作流，自动化复杂任务
3. 支持可视化工作流设计和执行监控

## API文档

后端服务提供自动生成的API文档：

- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

### 主要API端点

- **认证**：`/api/v1/auth/*` - 用户注册、登录和认证
- **对话**：`/api/v1/conversations/*` - 对话管理和消息历史
- **LLM**：`/api/v1/llm/*` - 大语言模型接口
- **模型管理**：`/api/v1/model-management/*` - AI模型配置和参数
- **供应商模型**：`/api/v1/supplier-model/*` - 供应商和模型管理
- **智能体**：`/api/v1/agents/*` - 智能体管理和配置
- **能力管理**：`/api/v1/capability/*` - AI能力和分类
- **知识库**：`/api/v1/knowledge/*` - 知识文档和检索
- **知识图谱**：`/api/v1/knowledge-graph/*` - 知识图谱管理
- **工作流**：`/api/v1/workflows/*` - 工作流管理和执行
- **技能管理**：`/api/v1/skills/*` - AI技能管理

## 项目结构

```
py copilot IV/
├── backend/           # 后端代码
│   ├── app/           # 应用代码
│   ├── config/        # 配置文件
│   ├── tests/         # 测试代码
│   ├── .env.example   # 环境变量示例
│   ├── requirements.txt # 依赖列表
│   ├── init_db.py     # 数据库初始化脚本
│   └── run_server.py  # 启动脚本
├── frontend/          # 前端代码
│   ├── public/        # 静态文件
│   ├── src/           # 源代码
│   ├── .env.example   # 环境变量示例
│   ├── package.json   # 项目配置
│   └── vite.config.js # Vite配置
├── electron/          # Electron桌面应用代码
└── README.md          # 项目说明文档
```

## 贡献指南

1. Fork 项目仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature`
5. 提交Pull Request

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请通过以下方式联系我们：

- 项目地址：[GitHub Repository]
- 邮箱：[contact@example.com]

---

© 2026 Py Copilot Team