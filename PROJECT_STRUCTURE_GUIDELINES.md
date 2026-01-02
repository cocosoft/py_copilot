# 项目结构规范指南

## 1. 项目概述

本项目采用模块化架构设计，将功能划分为独立的模块，每个模块包含完整的路由、服务和模型定义。

**项目上下文参考**：项目的整体介绍、目标、技术栈、API规范等内容请参考 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) 文件。

## 2. 整体目录结构

```
PY_COPILOT/
├── backend/                 # 后端应用
│   ├── app/                 # 主应用目录
│   │   ├── api/             # API路由（传统结构）
│   │   │   ├── __init__.py
│   │   │   ├── main.py      # FastAPI应用主入口
│   │   │   └── v1/          # API v1版本
│   │   │       ├── __init__.py  # 路由注册中心
│   │   │       └── *.py     # 非模块化API路由
│   │   ├── core/            # 核心配置和工具
│   │   ├── models/          # 数据库模型定义
│   │   ├── modules/         # 功能模块（推荐使用）
│   │   │   ├── module_name/ # 模块名称
│   │   │   │   ├── api/     # 模块API路由
│   │   │   │   ├── schemas/ # 模块数据模式
│   │   │   │   ├── services/# 模块业务逻辑
│   │   │   │   └── __init__.py
│   │   ├── schemas/         # 全局数据模式
│   │   ├── services/        # 全局业务逻辑
│   │   └── utils/           # 工具函数
│   ├── tests/               # 测试文件
│   ├── main.py              # 应用入口
│   └── run_server.py        # 服务器启动脚本
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── components/      # React组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API服务
│   │   ├── utils/           # 工具函数
│   │   │   └── api/         # API客户端
│   │   └── App.jsx          # 应用入口
│   └── package.json         # 前端配置
├── FRONTEND_BACKEND_COMMUNICATION_GUIDELINES.md  # 前后端通信规范
├── PROJECT_STRUCTURE_GUIDELINES.md               # 项目结构指南
├── PROJECT_CONTEXT.md                            # 项目上下文
└── .trae/documents/PROJECT_DEVELOPMENT_GUIDELINES.md  # 开发规范
```

## 3. 路由层规范

### 3.1 模块化路由（优先推荐）

**模块优先原则**：所有新功能必须优先采用模块化路由设计，避免在传统的`api/v1/`目录下添加新路由。路由文件应放在模块的`api`目录下：

```python
# backend/app/modules/capability_category/api/model_categories.py
from fastapi import APIRouter

router = APIRouter(prefix="/categories", tags=["model_categories"])

# 路由定义...
```

### 3.2 路由注册

模块化路由应在`app/api/v1/__init__.py`中统一注册：

```python
# backend/app/api/v1/__init__.py
from app.modules.capability_category.api.model_categories import router as model_categories_router

api_router = APIRouter()
api_router.include_router(model_categories_router, tags=["model__-__categories"])
```

### 3.3 路由路径规范

- 模块化路由的`prefix`应简洁明了，反映功能特性
- 避免过长的路由路径，推荐深度不超过3级
- 使用小写字母和连字符(-)分隔单词

## 4. 服务层规范

### 4.1 服务层组织

- 服务类应放在模块的`services`目录下
- 每个服务类应专注于单一功能领域
- 服务方法应明确表达业务逻辑

```python
# backend/app/modules/capability_category/services/model_category_service.py
class ModelCategoryService:
    @staticmethod
    def get_all_categories_by_dimension(db: Session) -> Dict[str, List[ModelCategory]]:
        # 业务逻辑...
```

### 4.2 服务调用

- 路由层应通过服务层访问数据，不直接操作数据库
- 服务层应处理业务逻辑、数据验证和异常处理

## 5. 数据库迁移规范

### 5.1 迁移工具

项目使用Alembic进行数据库迁移管理，确保数据库结构的一致性和可追踪性。

### 5.2 迁移文件组织

迁移文件应存放在`backend/alembic/versions/`目录下，遵循Alembic的命名规范。

### 5.3 迁移命令

```bash
# 创建迁移脚本
cd backend
alembic revision --autogenerate -m "描述迁移内容"

# 执行迁移
cd backend
alembic upgrade head

# 回滚迁移
cd backend
alembic downgrade <revision_id>
```

### 5.4 迁移最佳实践

1. **每次修改模型后创建迁移**：对数据库模型进行任何修改后，都应创建新的迁移脚本
2. **清晰的迁移描述**：迁移信息应简洁明了地描述所做的更改
3. **测试迁移**：在生产环境应用迁移前，应在开发和测试环境充分测试
4. **版本控制**：迁移文件应与代码一起进行版本控制

## 6. 模型层规范

### 6.1 模型定义

- 数据库模型应放在`app/models`目录下
- 模型类应继承自统一的基类
- 字段命名应使用snake_case格式

```python
# backend/app/models/model_category.py
class ModelCategory(Base):
    __tablename__ = "model_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    # 其他字段...
```

### 6.2 数据模式

- 请求和响应的数据模式应放在模块的`schemas`目录下
- 使用Pydantic模型进行数据验证和序列化

```python
# backend/app/modules/capability_category/schemas/model_category.py
class ModelCategoryCreate(BaseModel):
    name: str
    display_name: str
    # 其他字段...
```

## 7. 前后端通信规范

### 7.1 API路径规范

- 前端API调用前缀应使用与后端实际路径一致的URL
- **正确路径**：`/v1/categories/`（后端实际路径）
- **避免错误路径**：`/v1/model/categories/`
- 避免硬编码API路径，使用统一的API客户端

### 7.2 API客户端组织

```javascript
// frontend/src/utils/api/categoryApi.js
export const categoryApi = {
  getAll: async () => {
    return await request('/v1/categories', { method: 'GET' });
  },
  // 其他API方法...
};
```

## 8. 代码清理与维护

### 8.1 废弃代码处理

- 删除不再使用的文件和代码
- 避免保留重复的路由、服务或模型
- 确保所有导入都是正确和必要的

### 8.2 命名规范

- 文件和目录命名应使用snake_case格式
- 类名应使用PascalCase格式
- 函数和变量名应使用snake_case格式

## 9. 最佳实践

1. **单一职责原则**：每个文件、类和函数应只负责一个功能
2. **模块化设计**：将相关功能组织到同一个模块中
3. **分层架构**：严格遵循路由层→服务层→模型层的调用链
4. **代码复用**：提取通用功能到工具类或服务中
5. **文档化**：为公共API和复杂逻辑添加文档注释
6. **数据处理注意事项**：注意数据过滤条件，避免遗漏重要数据；确保数据格式的一致性和兼容性

## 10. 常见错误与避免

- **重复代码**：定期检查并删除重复的路由、服务或模型
- **路径不一致**：确保前端API调用路径与后端实际路径一致
- **导入错误**：确保所有导入路径正确，避免导入不存在的模块
- **过度耦合**：避免模块间的过度依赖，保持模块独立性

---

**注意**：本规范应作为项目开发的基准，所有开发人员都应遵守。如有疑问或需要调整，应通过团队讨论决定。