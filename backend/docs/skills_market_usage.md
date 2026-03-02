# 技能市场使用文档

## 概述

Py Copilot 技能市场是一个兼容 ClawHub 技能系统的扩展框架，支持从 NPM 或 Git 安装技能，并将其集成到 Py Copilot 的工具系统中。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Py Copilot 后端                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   API 端点    │  │  技能管理器   │  │  工具管理器   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │              │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐      │
│  │ skills_market│  │ clawhub_     │  │   工具注册    │      │
│  │    .py       │  │ adapter.py   │  │              │      │
│  └──────────────┘  └──────┬───────┘  └──────────────┘      │
│                           │                                 │
│                    ┌──────▼───────┐                        │
│                    │  Node.js     │                        │
│                    │  进程调用    │                        │
│                    └──────┬───────┘                        │
└───────────────────────────┼─────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  ClawHub 技能   │
                    │  (NPM/Git)     │
                    └────────────────┘
```

## 快速开始

### 1. 查看已安装的技能

```bash
GET /api/v1/skills-market
```

### 2. 从 NPM 安装技能

```bash
POST /api/v1/skills-market/install/npm
Content-Type: application/json

{
    "package_name": "web-scraper",
    "version": "1.0.0"
}
```

### 3. 从 Git 安装技能

```bash
POST /api/v1/skills-market/install/git
Content-Type: application/json

{
    "git_url": "https://github.com/openclaw-skills/web-scraper",
    "skill_name": "web-scraper"
}
```

### 4. 执行技能

```bash
POST /api/v1/skills-market/{skill_name}/execute
Content-Type: application/json

{
    "parameters": {
        "action": "scrape",
        "url": "https://example.com"
    },
    "timeout": 60
}
```

## API 接口

### 技能管理

#### 获取技能列表
```http
GET /api/v1/skills-market
```

**查询参数**:
- `category`: 按类别过滤
- `active_only`: 仅返回激活的技能

#### 获取技能详情
```http
GET /api/v1/skills-market/{skill_name}
```

#### 卸载技能
```http
DELETE /api/v1/skills-market/{skill_name}
```

#### 启用/禁用技能
```http
POST /api/v1/skills-market/{skill_name}/enable
Content-Type: application/json

{
    "enable": true
}
```

### 技能安装

#### 从 NPM 安装
```http
POST /api/v1/skills-market/install/npm
Content-Type: application/json

{
    "package_name": "skill-name",
    "version": "1.0.0"  // 可选
}
```

#### 从 Git 安装
```http
POST /api/v1/skills-market/install/git
Content-Type: application/json

{
    "git_url": "https://github.com/user/repo",
    "skill_name": "custom-name"  // 可选
}
```

### 技能执行

```http
POST /api/v1/skills-market/{skill_name}/execute
Content-Type: application/json

{
    "parameters": {
        // 技能特定参数
    },
    "timeout": 60  // 可选
}
```

### 技能市场（远程）

#### 浏览可用技能
```http
GET /api/v1/skills-market-remote
```

**查询参数**:
- `category`: 类别过滤
- `search`: 搜索关键词

#### 获取技能详情
```http
GET /api/v1/skills-market-remote/{skill_name}
```

### 统计信息

#### 获取统计
```http
GET /api/v1/skills-market/statistics
```

#### 获取类别列表
```http
GET /api/v1/skills-market/categories
```

## 示例技能使用

### 网页自动化技能

#### 抓取网页内容
```bash
curl -X POST http://localhost:8000/api/v1/skills-market/web-automation/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "action": "scrape",
      "url": "https://example.com",
      "selector": "h1"
    }
  }'
```

#### 网页截图
```bash
curl -X POST http://localhost:8000/api/v1/skills-market/web-automation/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "action": "screenshot",
      "url": "https://example.com",
      "fullPage": true
    }
  }'
```

#### 填写表单
```bash
curl -X POST http://localhost:8000/api/v1/skills-market/web-automation/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "action": "fill_form",
      "url": "https://example.com/form",
      "formData": {
        "#username": "myuser",
        "#password": "mypass"
      }
    }
  }'
```

## 开发自定义技能

### 技能结构

```
skill-name/
├── package.json      # NPM 包配置
├── skill.json        # 技能元数据
├── index.js          # 入口文件
└── README.md         # 说明文档
```

### package.json

```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "description": "我的自定义技能",
  "main": "index.js",
  "author": "Your Name",
  "dependencies": {
    // 依赖包
  }
}
```

### skill.json

```json
{
  "metadata": {
    "name": "my-skill",
    "displayName": "我的技能",
    "description": "技能描述",
    "version": "1.0.0",
    "author": "Your Name",
    "category": "utility",
    "tags": ["tag1", "tag2"],
    "icon": "🔧"
  },
  "config": {
    "entryPoint": "index.js",
    "runtime": "node",
    "timeout": 30,
    "permissions": ["network", "filesystem"]
  },
  "parameters": [
    {
      "name": "param1",
      "type": "string",
      "description": "参数说明",
      "required": true
    }
  ]
}
```

### index.js 模板

```javascript
#!/usr/bin/env node

/**
 * 技能入口文件
 */

// 解析参数
function parseArgs() {
    const args = process.argv.slice(2);
    for (let i = 0; i < args.length; i += 2) {
        if (args[i] === '--params' && args[i + 1]) {
            return JSON.parse(args[i + 1]);
        }
    }
    return {};
}

// 主函数
async function main() {
    const params = parseArgs();
    
    try {
        // 实现技能逻辑
        const result = await yourSkillLogic(params);
        
        // 输出结果
        console.log(JSON.stringify({
            success: true,
            result
        }));
        
    } catch (error) {
        console.error(JSON.stringify({
            success: false,
            error: error.message
        }));
        process.exit(1);
    }
}

main();
```

## 技能类别

| 类别 | 说明 | 示例 |
|------|------|------|
| browser | 浏览器自动化 | 网页抓取、截图、表单填写 |
| coding | 代码辅助 | 代码审查、格式化、生成 |
| data | 数据处理 | 分析、转换、可视化 |
| productivity | 生产力工具 | 任务管理、自动化 |
| communication | 通信 | 邮件、消息发送 |
| media | 媒体处理 | 图片、视频处理 |
| security | 安全 | 加密、扫描 |
| utility | 通用工具 | 各种实用功能 |

## 最佳实践

1. **参数验证**: 在技能中验证所有输入参数
2. **错误处理**: 使用 try-catch 捕获异常并返回错误信息
3. **超时控制**: 设置合理的超时时间
4. **资源清理**: 确保关闭浏览器、文件句柄等资源
5. **日志记录**: 使用 console.log 输出调试信息
6. **输出格式**: 始终返回 JSON 格式的结果

## 安全注意事项

1. **权限控制**: 在 skill.json 中声明需要的权限
2. **输入验证**: 验证所有用户输入
3. **沙箱执行**: 技能在独立进程中执行
4. **超时限制**: 防止长时间运行的技能
5. **资源限制**: 监控 CPU 和内存使用

## 故障排除

### 技能安装失败

1. 检查 Node.js 版本（需要 16+）
2. 检查网络连接
3. 查看 npm 错误日志
4. 确认包名正确

### 技能执行失败

1. 检查技能是否已正确安装
2. 查看技能日志输出
3. 验证参数格式
4. 检查超时设置

### 依赖问题

```bash
# 手动安装技能依赖
cd backend/app/modules/skills/installed/skill-name
npm install
```

## 更新日志

### v1.0.0
- 初始版本
- 支持 NPM 和 Git 安装
- 提供网页自动化示例技能
- 完整的 API 接口
