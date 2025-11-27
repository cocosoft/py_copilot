# Py Copilot - 开源公益项目

智能私人助手应用，旨在提供个性化服务，帮助用户提高工作效率、管理日程、解答问题并提供各类实用工具。作为一个开源公益项目，我们致力于为社区提供高质量的AI工具，并根据代码贡献度分配收益。

## 项目架构

```
├── backend/             # 后端应用
│   ├── app/             # 应用主目录
│   │   ├── api/         # API端点
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # 数据验证模式
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   ├── tests/           # 测试目录
│   ├── requirements.txt # 依赖列表
│   ├── .env             # 环境变量（本地使用，不提交到版本控制）
│   └── .env.example     # 环境变量示例（提交到版本控制）
├── frontend/            # 前端应用
│   ├── public/          # 静态资源
│   └── src/             # 源代码
│       ├── components/  # React组件
│       ├── context/     # React上下文
│       ├── hooks/       # 自定义钩子
│       ├── pages/       # 页面组件
│       ├── styles/      # 样式文件
│       └── utils/       # 工具函数
├── config/              # 配置文件
└── docs/                # 文档
```

## 技术栈

### 后端
- **编程语言**: Python 3.10+
- **Web框架**: FastAPI
- **数据库**: PostgreSQL, Redis
- **AI组件**: LangChain, OpenAI API, Hugging Face

### 前端
- **框架**: React.js
- **语言**: JavaScript/JSX
- **构建工具**: Vite
- **路由**: React Router
- **Markdown支持**: React Markdown, KaTeX

## 开始使用

### 前提条件
- Python 3.10 或更高版本
- Node.js 16 或更高版本
- PostgreSQL 数据库
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
   python main.py
   ```
   服务器将在 http://localhost:8001 运行

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

### 生产环境准备
1. 更新后端 .env 文件中的配置：
   - 设置 DEBUG=False
   - 使用强随机的 SECRET_KEY
   - 更新数据库连接信息

2. 构建前端应用：
```bash
cd frontend
npm run build
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