# Py Copilot - 开源公益项目

智能私人助手应用，旨在提供个性化服务，帮助用户提高工作效率、管理日程、解答问题并提供各类实用工具。作为一个开源公益项目，我们致力于为社区提供高质量的AI工具，并根据代码贡献度分配收益。

## 项目文档

- **[PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md)**: 详细的项目上下文，包括项目定位、目标、API规范、数据库结构和核心功能
- **[PROJECT_STRUCTURE_GUIDELINES.md](./PROJECT_STRUCTURE_GUIDELINES.md)**: 项目结构规范、模块化设计和开发实践指南

## 项目架构

项目采用前后端分离的模块化架构设计：
- **backend/**: 基于FastAPI的后端服务
- **frontend/**: 基于React的前端应用

详细的项目结构规范请参考 [PROJECT_STRUCTURE_GUIDELINES.md](./PROJECT_STRUCTURE_GUIDELINES.md) 文件。

## 技术栈

### 后端
- **核心框架**: Python 3.10+, FastAPI 0.104.1
- **数据库**: SQLite (开发), PostgreSQL (生产)
- **ORM**: SQLAlchemy 2.0.23
- **缓存**: Redis 5.0.1
- **AI框架**: LangChain 0.1.5, OpenAI SDK 1.6.0, Hugging Face Hub 0.19.4
- **NLP处理**: jieba 0.42.1 (中文分词), Transformers 4.35.2

### 前端
- **核心框架**: React 18.2.0
- **语言**: JavaScript/TypeScript
- **构建工具**: Vite 5.0.8
- **路由**: React Router DOM 6.22.0
- **可视化**: ReactFlow, D3.js
- **文档处理**: React Markdown 10.1.0, KaTeX 0.16.25

详细的技术栈信息请参考 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) 文件。

## 开始使用

### 前提条件
- Python 3.10 或更高版本
- Node.js 16 或更高版本
- Poetry 依赖管理工具
- SQLite 数据库
- Redis 服务

### 后端设置
1. 进入backend目录
   ```bash
   cd backend
   ```
2. 创建虚拟环境
   ```bash
   python -m venv venv
   ```
3. 激活虚拟环境
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
5. 配置环境变量
   - 复制环境变量示例文件
   ```bash
   cp .env.example .env
   ```
   - 编辑.env文件，填入实际的配置值
6. 初始化数据库
   ```bash
   alembic upgrade head
   ```
7. 启动开发服务器
   ```bash
   python run_server.py
   ```
   服务器将在 http://localhost:8000 运行

### 前端设置
1. 进入frontend目录
   ```bash
   cd frontend
   ```
2. 安装依赖
   ```bash
   npm install
   ```
3. 启动开发服务器
   ```bash
   npm run dev
   ```
   开发服务器将在 http://localhost:5173 运行

## 开发指南

### API文档

项目提供了完整的API规范，包括所有API端点、参数和响应格式。详细的API文档请参考 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) 文件中的API规范章节。

### 代码规范
- 后端使用 Python 的 PEP 8 规范
- 前端使用 ESLint 进行代码检查

### 提交代码
1. 确保所有代码都通过了相应的测试
2. 不要提交敏感信息（如API密钥、数据库凭证等）
3. 使用有意义的提交信息

### 运行测试
后端测试：
```bash
cd backend
python -m pytest
```

## 部署

详细的部署流程请参考 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) 文件中的开发与部署流程章节，包括环境配置、依赖安装、数据库初始化、构建和部署等完整步骤。

### 生产环境快速部署

1. **后端部署**：
   ```bash
   cd backend
   # 安装依赖
   pip install -r requirements.txt
   # 配置环境变量
   cp .env.example .env
   # 编辑.env文件设置生产环境参数
   # 初始化数据库
   alembic upgrade head
   # 构建应用
   python -m build
   # 启动生产服务器（推荐使用Gunicorn）
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.api.main:app
   ```

2. **前端部署**：
   ```bash
   cd frontend
   # 安装依赖
   npm install
   # 构建生产版本
   npm run build
   # 部署dist目录到静态文件服务器
   ```

## 许可证

MIT License

## 贡献指南

欢迎贡献代码！请遵循以下步骤：
1. Fork 项目
2. 创建功能分支 (git checkout -b feature/amazing-feature)
3. 提交更改 (git commit -m 'Add some amazing feature')
4. 推送到分支 (git push origin feature/amazing-feature)
5. 开启 Pull Request