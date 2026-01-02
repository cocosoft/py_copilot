# 前后端通信约束规范

## 1. 概述

为确保前后端之间的通信顺畅、高效和一致，制定本规范文档。本规范定义了API路径命名、请求/响应格式、错误处理、版本控制等方面的约束和最佳实践。

## 2. API路径规范

### 2.1 基础路径

- 所有API请求必须使用以下基础路径格式（注意：实际路径中不包含/api前缀）：
  ```
  http://backend-url/v{version}/{endpoint}
  ```
- 示例：`http://localhost:8000/v1/categories`

详细的API列表和规范请参考 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) 文件。

### 2.2 路径命名规则

- 使用小写字母和连字符(-)分隔单词，避免使用下划线(_)或驼峰命名
- 路径应简洁明了，反映资源的语义
- 避免过长的路径，推荐深度不超过3级

**错误示例：**
```
/v1/modelCategories
/v1/model_categories
```

**正确示例：**
```
/v1/categories
/v1/knowledge-graph
```

### 2.3 资源操作

- 使用HTTP方法表示操作类型：
  - `GET`: 获取资源
  - `POST`: 创建资源
  - `PUT`: 更新资源
  - `DELETE`: 删除资源
  - `PATCH`: 部分更新资源

**示例：**
```
GET /v1/categories                # 获取所有分类
POST /v1/categories               # 创建新分类
PUT /v1/categories/{id}           # 更新分类
DELETE /v1/categories/{id}        # 删除分类
```

## 3. 模块化API路径

### 3.1 模块化路由

所有API路径应遵循模块化设计，模块的路由应在模块的`api`目录下定义，并在`app/api/v1/__init__.py`中统一注册。

### 3.2 路由前缀

模块路由应使用清晰的前缀：

| 模块名称 | 路由前缀 | 实际路径 |
|---------|---------|---------|
| capability_category | /categories | /v1/categories |
| category_templates | /category__-__templates | /v1/category_-_templates |
| knowledge | /knowledge | /v1/knowledge |
| workflow | /workflow | /v1/workflow |

## 4. 请求规范

### 4.1 请求头

- 所有请求必须包含`Content-Type`头：
  - JSON请求：`Content-Type: application/json`
  - 文件上传：`Content-Type: multipart/form-data`

### 4.2 请求体

- JSON格式的请求体应使用标准JSON语法
- 字段名应使用snake_case格式
- 避免空值字段，可省略未使用的可选字段

**示例：**
```json
{
  "name": "text-generation",
  "display_name": "文本生成",
  "description": "用于生成文本内容的模型分类"
}
```

### 4.3 查询参数

- 查询参数应使用snake_case格式
- 布尔值参数使用`true/false`（小写）
- 数组参数使用逗号分隔：`?ids=1,2,3`

## 5. 响应规范

### 5.1 响应格式

所有API响应应使用统一的JSON格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 5.2 状态码

使用标准HTTP状态码：

- `200`: 请求成功
- `201`: 资源创建成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 禁止访问
- `404`: 资源不存在
- `409`: 资源冲突
- `500`: 服务器内部错误

### 5.3 分页响应

分页资源响应应包含分页信息：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5
  }
}
```

## 6. 错误处理规范

### 6.1 错误响应格式

错误响应应包含详细的错误信息：

```json
{
  "code": 400,
  "message": "请求参数错误",
  "errors": [
    {
      "field": "name",
      "message": "分类名称不能为空"
    }
  ]
}
```

### 6.2 前端错误处理

- 捕获所有API请求异常
- 显示友好的错误信息给用户
- 记录详细的错误日志用于调试

## 7. 前后端协作流程

### 7.1 API设计与文档

1. 后端团队设计API接口
2. 使用Swagger/OpenAPI生成API文档
3. 前后端团队共同评审API设计
4. 根据评审结果调整API设计

### 7.2 开发与测试

1. 后端实现API接口
2. 前端基于API文档实现客户端
3. 前后端并行开发，定期同步进度
4. 使用Postman等工具测试API接口

### 7.3 集成与部署

1. 前后端进行集成测试
2. 修复集成过程中发现的问题
3. 部署到测试环境进行验证
4. 部署到生产环境

## 8. 版本控制

### 8.1 API版本管理

- 使用URL路径中的版本号：`/api/v1/...`
- 版本升级时，保持向后兼容
- 标记过时的API路径，逐步迁移到新版本

### 8.2 兼容性处理

- 新增字段时，确保现有客户端不受影响
- 删除字段时，提供足够的迁移时间
- 使用可选参数，避免强制客户端更新

## 9. 前端API客户端规范

### 9.1 API客户端组织

- 按功能模块组织API客户端
- 使用统一的请求/响应处理机制
- 封装错误处理和认证逻辑

**示例：**
```javascript
// frontend/src/utils/api/categoryApi.js
export const categoryApi = {
  getAll: async () => {
    return await request('/v1/categories', { method: 'GET' });
  },
  getById: async (id) => {
    return await request(`/v1/categories/${id}`, { method: 'GET' });
  },
  create: async (data) => {
    return await request('/v1/categories', { 
      method: 'POST', 
      body: JSON.stringify(data) 
    });
  }
};
```

### 9.2 API路径配置

- 避免硬编码API路径，使用配置文件管理
- 路径应与后端实际路径完全一致

**错误示例：**
```javascript
// 错误：使用了错误的路径
return await request('/v1/model/categories', { method: 'GET' });
```

**正确示例：**
```javascript
// 正确：与后端实际路径一致
return await request('/v1/categories', { method: 'GET' });
```

## 10. 最佳实践

1. **单一来源真实**：后端定义API，前端严格遵循API文档实现
2. **契约测试**：使用契约测试确保前后端接口一致
3. **日志记录**：记录所有API请求和响应，便于调试和监控
4. **性能优化**：
   - 使用分页减少数据传输量
   - 缓存频繁访问的数据
   - 压缩响应数据
5. **安全性**：
   - 使用HTTPS加密通信
   - 实现请求限流
   - 验证所有输入数据

## 11. 常见问题与解决方案

### 11.1 路径不匹配

**问题：** 前端API调用路径与后端实际路径不一致

**解决方案：**
1. 定期核对API文档与实际实现
2. 使用统一的API路径配置文件
3. 后端提供API测试工具（如Swagger UI）

### 11.2 数据格式不一致

**问题：** 前端期望的数据格式与后端返回的格式不匹配

**解决方案：**
1. 在API文档中明确定义数据格式
2. 使用JSON Schema验证数据格式
3. 前后端共同定义数据模型

### 11.3 错误处理不当

**问题：** 错误信息不清晰或处理不当

**解决方案：**
1. 遵循统一的错误响应格式
2. 提供详细的错误信息
3. 前端实现统一的错误处理机制

## 12. 结论

本规范旨在确保前后端之间的通信一致性和可靠性。所有开发人员应严格遵守本规范，定期进行代码审查和文档更新，以保持通信机制的高效和稳定。

## 13. 相关文档

- [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md): 项目整体上下文和API规范
- [PROJECT_STRUCTURE_GUIDELINES.md](./PROJECT_STRUCTURE_GUIDELINES.md): 项目结构和开发规范

---

**版本历史：**
- v1.0 (2025-12-29): 初始版本
- v1.1 (2025-12-29): 修正API路径格式，移除/api前缀，更新示例，添加相关文档引用
