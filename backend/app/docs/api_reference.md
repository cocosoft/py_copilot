# Py Copilot 技能API参考文档

## 📋 概述

本文档提供Py Copilot技能管理系统的完整API参考，涵盖技能安装、卸载、管理、执行等所有接口。

## 🔌 API基础信息

### 基础URL
```
http://localhost:8000/api
```

### 认证方式
- **API密钥**：在请求头中传递`X-API-Key`
- **会话认证**：使用用户会话令牌

### 响应格式
所有API响应都遵循以下格式：

```json
{
    "success": true,
    "data": {...},
    "message": "操作成功",
    "error": null,
    "metadata": {
        "timestamp": "2024-01-27T00:00:00",
        "request_id": "req-123456"
    }
}
```

## 📚 技能管理API

### 获取已安装技能列表

**端点**: `GET /api/skills/installed`

**描述**: 获取当前已安装的所有技能信息

**参数**:
- `category` (可选): 按分类筛选
- `official` (可选): 是否官方技能
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页数量，默认20

**响应**:
```json
{
    "success": true,
    "data": {
        "skills": [
            {
                "id": "data-analysis",
                "name": "数据分析助手",
                "description": "强大的数据分析工具",
                "category": "数据分析",
                "rating": 4.8,
                "version": "1.2.3",
                "installed": true,
                "last_updated": "2024-01-15T00:00:00"
            }
        ],
        "total_count": 15,
        "installed_count": 8,
        "page": 1,
        "page_size": 20,
        "total_pages": 1
    }
}
```

### 获取技能市场列表

**端点**: `GET /api/skills/market`

**描述**: 获取技能市场中的可用技能列表

**参数**:
- `category` (可选): 按分类筛选
- `official` (可选): 是否官方技能
- `min_rating` (可选): 最低评分
- `page` (可选): 页码
- `page_size` (可选): 每页数量

**响应**:
```json
{
    "success": true,
    "data": {
        "skills": [
            {
                "id": "web-scraping",
                "name": "网页爬虫",
                "description": "自动化网页数据采集",
                "category": "数据采集",
                "rating": 4.5,
                "downloads": 1870,
                "official": false,
                "installed": false
            }
        ],
        "total_count": 156,
        "page": 1,
        "page_size": 20,
        "total_pages": 8
    }
}
```

### 安装技能

**端点**: `POST /api/skills/install`

**描述**: 安装指定技能

**请求体**:
```json
{
    "skill_id": "data-analysis",
    "source": "https://market.pycopilot.com/skills/data-analysis.zip",
    "force": false,
    "install_dependencies": true
}
```

**参数说明**:
- `skill_id`: 技能ID（必填）
- `source`: 技能来源（URL、Git地址、本地路径）
- `force`: 是否强制重新安装
- `install_dependencies`: 是否安装依赖

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "message": "技能安装成功",
        "install_path": "/app/skills/data-analysis",
        "metadata": {
            "name": "数据分析助手",
            "version": "1.2.3"
        }
    }
}
```

### 卸载技能

**端点**: `POST /api/skills/uninstall`

**描述**: 卸载指定技能

**请求体**:
```json
{
    "skill_id": "data-analysis",
    "cleanup": true
}
```

**参数说明**:
- `skill_id`: 技能ID（必填）
- `cleanup`: 是否清理配置和数据

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "message": "技能卸载成功",
        "cleanup_performed": true,
        "cleanup_result": {
            "removed_files": 15,
            "removed_directories": 3,
            "database_records": 25
        }
    }
}
```

### 更新技能

**端点**: `POST /api/skills/update`

**描述**: 更新已安装的技能

**请求体**:
```json
{
    "skill_id": "data-analysis",
    "source": "https://market.pycopilot.com/skills/data-analysis-v2.zip"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "message": "技能更新成功",
        "old_version": "1.2.3",
        "new_version": "2.0.0"
    }
}
```

### 获取技能详细信息

**端点**: `GET /api/skills/{skill_id}/info`

**描述**: 获取指定技能的详细信息

**路径参数**:
- `skill_id`: 技能ID

**响应**:
```json
{
    "success": true,
    "data": {
        "id": "data-analysis",
        "name": "数据分析助手",
        "description": "强大的数据分析工具",
        "long_description": "详细的功能描述...",
        "version": "1.2.3",
        "category": "数据分析",
        "author": "Py Copilot团队",
        "rating": 4.8,
        "downloads": 2560,
        "dependencies": {
            "pandas": ">=1.5.0",
            "matplotlib": ">=3.6.0"
        },
        "examples": [
            {
                "title": "基本使用",
                "description": "数据分析基本示例",
                "code": "from data_analysis import execute..."
            }
        ],
        "installed": true,
        "install_path": "/app/skills/data-analysis"
    }
}
```

### 检查技能依赖

**端点**: `GET /api/skills/{skill_id}/dependencies`

**描述**: 检查技能的依赖状态

**路径参数**:
- `skill_id`: 技能ID

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "dependencies": [
            {
                "name": "pandas",
                "version": ">=1.5.0",
                "installed": true,
                "installed_version": "1.5.3",
                "compatible": true
            },
            {
                "name": "matplotlib",
                "version": ">=3.6.0",
                "installed": true,
                "installed_version": "3.7.0",
                "compatible": true
            }
        ],
        "all_installed": true,
        "missing_dependencies": []
    }
}
```

### 搜索技能

**端点**: `POST /api/skills/search`

**描述**: 搜索技能市场中的技能

**请求体**:
```json
{
    "query": "数据分析",
    "category": "数据分析",
    "tags": ["可视化", "统计"],
    "official": true,
    "installed": false,
    "min_rating": 4.0,
    "sort_by": "popularity",
    "page": 1,
    "page_size": 20
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "skills": [
            {
                "id": "data-analysis",
                "name": "数据分析助手",
                "description": "强大的数据分析工具",
                "category": "数据分析",
                "rating": 4.8,
                "downloads": 2560
            }
        ],
        "total_count": 45,
        "page": 1,
        "page_size": 20,
        "total_pages": 3
    }
}
```

### 检查技能健康状态

**端点**: `GET /api/skills/{skill_id}/health`

**描述**: 检查技能的健康状态

**路径参数**:
- `skill_id`: 技能ID

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "healthy": true,
        "last_check": "2024-01-27T00:00:00",
        "issues": [],
        "dependencies_ok": true,
        "permissions_ok": true,
        "config_valid": true
    }
}
```

### 获取技能分类列表

**端点**: `GET /api/skills/categories`

**描述**: 获取所有可用的技能分类

**响应**:
```json
{
    "success": true,
    "data": {
        "categories": [
            "数据分析",
            "数据采集",
            "文档处理",
            "自动化",
            "开发工具"
        ]
    }
}
```

## ⚡ 技能执行API

### 执行技能

**端点**: `POST /api/skills/{skill_id}/execute`

**描述**: 执行指定技能

**路径参数**:
- `skill_id`: 技能ID

**请求体**:
```json
{
    "data": {
        "input_data": [1, 2, 3, 4, 5]
    },
    "parameters": {
        "operation": "sum",
        "format": "json"
    },
    "config": {
        "timeout": 30,
        "max_retries": 3
    }
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "result": {
            "sum": 15,
            "average": 3,
            "count": 5
        },
        "execution_time": 0.125,
        "message": "执行成功"
    }
}
```

### 批量执行技能

**端点**: `POST /api/skills/batch-execute`

**描述**: 批量执行多个技能

**请求体**:
```json
{
    "tasks": [
        {
            "skill_id": "data-analysis",
            "input_data": {"numbers": [1,2,3]}
        },
        {
            "skill_id": "file-processor", 
            "input_data": {"file_path": "/data/file.txt"}
        }
    ],
    "parallel": true,
    "timeout": 60
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "results": [
            {
                "skill_id": "data-analysis",
                "success": true,
                "result": {"sum": 6},
                "execution_time": 0.1
            },
            {
                "skill_id": "file-processor",
                "success": true,
                "result": {"file_size": 1024},
                "execution_time": 0.2
            }
        ],
        "total_time": 0.3,
        "success_count": 2,
        "failed_count": 0
    }
}
```

## 🔧 技能配置API

### 获取技能配置

**端点**: `GET /api/skills/{skill_id}/config`

**描述**: 获取技能的配置信息

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "config_schema": {
            "type": "object",
            "properties": {
                "timeout": {"type": "integer", "default": 30},
                "max_retries": {"type": "integer", "default": 3}
            }
        },
        "current_config": {
            "timeout": 30,
            "max_retries": 3
        },
        "default_config": {
            "timeout": 30,
            "max_retries": 3
        }
    }
}
```

### 更新技能配置

**端点**: `PUT /api/skills/{skill_id}/config`

**描述**: 更新技能的配置

**请求体**:
```json
{
    "config": {
        "timeout": 60,
        "max_retries": 5,
        "new_setting": "value"
    },
    "validate": true
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "message": "配置更新成功",
        "updated_fields": ["timeout", "max_retries", "new_setting"],
        "validation_errors": []
    }
}
```

### 重置技能配置

**端点**: `DELETE /api/skills/{skill_id}/config`

**描述**: 重置技能配置为默认值

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "message": "配置重置成功",
        "reset_to_default": true
    }
}
```

## 📊 技能统计API

### 获取技能使用统计

**端点**: `GET /api/skills/{skill_id}/stats`

**描述**: 获取技能的使用统计信息

**查询参数**:
- `period` (可选): 统计周期（day, week, month, year）
- `start_date` (可选): 开始日期
- `end_date` (可选): 结束日期

**响应**:
```json
{
    "success": true,
    "data": {
        "skill_id": "data-analysis",
        "period": "month",
        "execution_count": 156,
        "average_execution_time": 0.25,
        "success_rate": 0.98,
        "popular_parameters": [
            {"operation": "sum", "count": 45},
            {"operation": "average", "count": 38}
        ],
        "usage_trend": [
            {"date": "2024-01-01", "count": 5},
            {"date": "2024-01-02", "count": 8}
        ]
    }
}
```

### 获取全局技能统计

**端点**: `GET /api/skills/stats/global`

**描述**: 获取所有技能的全局统计信息

**响应**:
```json
{
    "success": true,
    "data": {
        "total_skills": 156,
        "installed_skills": 23,
        "total_executions": 12560,
        "average_rating": 4.3,
        "popular_categories": [
            {"category": "数据分析", "count": 45},
            {"category": "自动化", "count": 38}
        ],
        "recent_activity": [
            {
                "skill_id": "data-analysis",
                "action": "install",
                "timestamp": "2024-01-27T10:00:00"
            }
        ]
    }
}
```

## 🛡️ 错误处理

### 错误响应格式

```json
{
    "success": false,
    "error": {
        "code": "SKILL_NOT_FOUND",
        "message": "技能未找到",
        "details": "技能ID: invalid-skill 不存在",
        "timestamp": "2024-01-27T00:00:00"
    },
    "data": null
}
```

### 常见错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|----------|
| `SKILL_NOT_FOUND` | 技能未找到 | 检查技能ID是否正确 |
| `SKILL_ALREADY_INSTALLED` | 技能已安装 | 使用force参数强制重新安装 |
| `DEPENDENCY_CONFLICT` | 依赖冲突 | 检查依赖版本兼容性 |
| `PERMISSION_DENIED` | 权限不足 | 检查技能权限设置 |
| `INVALID_CONFIG` | 配置无效 | 检查配置参数格式 |
| `EXECUTION_TIMEOUT` | 执行超时 | 增加超时时间或优化技能 |

## 🔄 WebSocket API

### 实时技能执行状态

**端点**: `ws://localhost:8000/api/skills/ws`

**消息类型**:

1. **订阅执行状态**
```json
{
    "type": "subscribe",
    "skill_id": "data-analysis",
    "execution_id": "exec-123456"
}
```

2. **执行进度更新**
```json
{
    "type": "progress",
    "execution_id": "exec-123456",
    "progress": 50,
    "message": "正在处理数据..."
}
```

3. **执行完成**
```json
{
    "type": "complete",
    "execution_id": "exec-123456",
    "result": {...},
    "success": true
}
```

## 📚 代码示例

### Python客户端示例

```python
import requests
import json

class PyCopilotClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def install_skill(self, skill_id, source):
        """安装技能"""
        data = {
            "skill_id": skill_id,
            "source": source
        }
        
        response = requests.post(
            f"{self.base_url}/api/skills/install",
            headers=self.headers,
            json=data
        )
        
        return response.json()
    
    def execute_skill(self, skill_id, input_data):
        """执行技能"""
        response = requests.post(
            f"{self.base_url}/api/skills/{skill_id}/execute",
            headers=self.headers,
            json=input_data
        )
        
        return response.json()

# 使用示例
client = PyCopilotClient()
result = client.execute_skill("data-analysis", {
    "data": [1, 2, 3, 4, 5],
    "parameters": {"operation": "sum"}
})

if result["success"]:
    print(f"执行结果: {result['data']['result']}")
else:
    print(f"执行失败: {result['error']}")
```

### JavaScript客户端示例

```javascript
class PyCopilotClient {
    constructor(baseUrl = 'http://localhost:8000', apiKey = null) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json'
        };
        
        if (apiKey) {
            this.headers['X-API-Key'] = apiKey;
        }
    }
    
    async installSkill(skillId, source) {
        const response = await fetch(`${this.baseUrl}/api/skills/install`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                skill_id: skillId,
                source: source
            })
        });
        
        return await response.json();
    }
    
    async executeSkill(skillId, inputData) {
        const response = await fetch(`${this.baseUrl}/api/skills/${skillId}/execute`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(inputData)
        });
        
        return await response.json();
    }
}

// 使用示例
const client = new PyCopilotClient();
client.executeSkill('data-analysis', {
    data: [1, 2, 3, 4, 5],
    parameters: {operation: 'sum'}
}).then(result => {
    if (result.success) {
        console.log('执行结果:', result.data.result);
    } else {
        console.error('执行失败:', result.error);
    }
});
```

---

**版本**: 1.0.0  
**最后更新**: 2024-01-27  
**作者**: Py Copilot开发团队