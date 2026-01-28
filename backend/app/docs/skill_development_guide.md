# Py Copilot 技能开发指南

## 📋 概述

本文档为Py Copilot技能开发者提供完整的开发指南，涵盖技能创建、测试、打包和发布的完整流程。

## 🎯 技能开发基础

### 什么是技能？

技能是Py Copilot的可扩展功能模块，每个技能都具备特定的功能，如数据分析、文件处理、网络操作等。

### 技能的基本结构

```
my_skill/
├── skill.json          # 技能元数据文件
├── main.py             # 技能主文件
├── requirements.txt    # 依赖包列表（可选）
├── config/             # 配置文件目录（可选）
├── data/               # 数据文件目录（可选）
├── tests/              # 测试文件目录（可选）
└── docs/               # 文档目录（可选）
```

## 📝 技能元数据定义

### skill.json 文件格式

```json
{
    "id": "my-skill",
    "name": "我的技能",
    "description": "这是一个示例技能",
    "long_description": "详细的技能描述信息...",
    "version": "1.0.0",
    
    "category": "数据分析",
    "tags": ["数据分析", "可视化", "统计"],
    
    "author": "开发者姓名",
    "author_email": "developer@example.com",
    "author_url": "https://example.com",
    
    "official": false,
    "popular": false,
    "installed": false,
    
    "rating": 4.5,
    "review_count": 10,
    "downloads": 100,
    
    "size": "2.5MB",
    "last_updated": "2024-01-27T00:00:00",
    "compatibility": "Py Copilot 1.0+",
    "license": "MIT",
    
    "dependencies": {
        "pandas": ">=1.5.0",
        "matplotlib": ">=3.6.0"
    },
    "skill_dependencies": [],
    
    "icon": "icon.png",
    "screenshots": ["screenshot1.png", "screenshot2.png"],
    
    "examples": [
        {
            "title": "基本使用示例",
            "description": "展示技能的基本使用方法",
            "code": "from my_skill import execute\nresult = execute({'data': [1,2,3]})"
        }
    ],
    
    "reviews": [
        {
            "author": "用户A",
            "rating": 5.0,
            "date": "2024-01-20T00:00:00",
            "content": "非常好用的技能！"
        }
    ],
    
    "config_schema": {
        "type": "object",
        "properties": {
            "max_retries": {
                "type": "integer",
                "default": 3,
                "description": "最大重试次数"
            }
        }
    },
    "default_config": {
        "max_retries": 3
    },
    
    "entry_point": "main:execute",
    "main_file": "main.py",
    
    "permissions": ["file_read", "network_access"],
    
    "marketplace_id": "skill-001",
    "marketplace_url": "https://market.pycopilot.com/skills/skill-001"
}
```

### 必填字段说明

- **id**: 技能的唯一标识符，只能包含字母、数字和连字符
- **name**: 技能的显示名称
- **description**: 技能的简短描述
- **version**: 技能版本号，遵循语义化版本规范
- **category**: 技能分类
- **author**: 开发者姓名

## 🔧 技能代码开发

### 主文件结构

每个技能必须包含一个主文件（通常是`main.py`），该文件必须包含一个`execute`函数：

```python
"""
我的技能 - 技能描述

这是一个示例技能，用于演示技能开发规范。
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def execute(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行技能的主要函数
    
    Args:
        input_data: 输入数据字典
        
    Returns:
        执行结果字典
    """
    try:
        # 参数验证
        if not input_data:
            return {
                "success": False,
                "error": "输入数据不能为空"
            }
        
        # 业务逻辑处理
        result = process_data(input_data)
        
        # 返回结果
        return {
            "success": True,
            "result": result,
            "message": "技能执行成功"
        }
        
    except Exception as e:
        logger.error(f"技能执行失败: {e}")
        return {
            "success": False,
            "error": f"执行失败: {str(e)}"
        }


def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """处理数据的辅助函数
    
    Args:
        data: 输入数据
        
    Returns:
        处理结果
    """
    # 实现具体的业务逻辑
    return {
        "processed": True,
        "data_size": len(str(data)),
        "timestamp": "2024-01-27T00:00:00"
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """验证配置参数
    
    Args:
        config: 配置参数
        
    Returns:
        是否验证通过
    """
    required_fields = ["api_key", "base_url"]
    for field in required_fields:
        if field not in config:
            return False
    return True


# 异步版本（可选）
async def execute_async(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """异步执行技能
    
    Args:
        input_data: 输入数据字典
        
    Returns:
        执行结果字典
    """
    # 异步处理逻辑
    import asyncio
    await asyncio.sleep(0.1)
    return execute(input_data)


if __name__ == "__main__":
    # 本地测试代码
    test_data = {"test": "data"}
    result = execute(test_data)
    print(f"测试结果: {result}")
```

### 输入输出规范

#### 输入数据格式

```python
{
    "data": "原始数据",
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    },
    "config": {
        "api_key": "your_api_key",
        "timeout": 30
    }
}
```

#### 输出数据格式

```python
{
    "success": True,           # 执行是否成功
    "result": {...},           # 执行结果数据
    "message": "成功消息",      # 执行消息
    "error": None,             # 错误信息（失败时）
    "metadata": {              # 元数据（可选）
        "execution_time": 0.5,
        "data_size": 1024
    }
}
```

### 错误处理规范

1. **参数验证错误**：返回明确的错误信息
2. **业务逻辑错误**：记录日志并返回用户友好的错误信息
3. **系统错误**：记录详细日志，返回通用错误信息

```python
def execute(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # 参数验证
        if "data" not in input_data:
            return {
                "success": False,
                "error": "缺少必要参数: data"
            }
        
        # 业务逻辑
        result = process_business_logic(input_data["data"])
        
        return {
            "success": True,
            "result": result
        }
        
    except ValueError as e:
        # 业务逻辑错误
        logger.warning(f"业务逻辑错误: {e}")
        return {
            "success": False,
            "error": f"处理失败: {str(e)}"
        }
        
    except Exception as e:
        # 系统错误
        logger.error(f"系统错误: {e}")
        return {
            "success": False,
            "error": "系统内部错误，请稍后重试"
        }
```

## 📦 依赖管理

### requirements.txt 文件

如果技能需要额外的Python包依赖，创建`requirements.txt`文件：

```text
# 技能依赖包列表
pandas>=1.5.0
matplotlib>=3.6.0
requests>=2.28.0

# 开发依赖（可选）
pytest>=7.0.0
black>=22.0.0
```

### 技能间依赖

如果技能依赖其他技能，在`skill.json`中声明：

```json
{
    "skill_dependencies": ["data-processor", "file-manager"]
}
```

## ⚙️ 配置管理

### 配置参数定义

在`skill.json`中定义配置参数的模式：

```json
{
    "config_schema": {
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "description": "API密钥",
                "minLength": 1
            },
            "timeout": {
                "type": "integer",
                "default": 30,
                "description": "请求超时时间（秒）",
                "minimum": 1,
                "maximum": 300
            },
            "retry_count": {
                "type": "integer",
                "default": 3,
                "description": "重试次数"
            }
        },
        "required": ["api_key"]
    },
    "default_config": {
        "timeout": 30,
        "retry_count": 3
    }
}
```

### 配置使用

在技能代码中使用配置：

```python
def execute(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # 获取配置
    config = input_data.get("config", {})
    
    # 使用配置参数
    timeout = config.get("timeout", 30)
    retry_count = config.get("retry_count", 3)
    
    # 业务逻辑...
```

## 🧪 测试开发

### 测试文件结构

```
tests/
├── __init__.py
├── test_main.py          # 主测试文件
├── test_integration.py   # 集成测试
└── conftest.py           # 测试配置
```

### 测试示例

```python
"""技能测试用例"""

import pytest
from main import execute, process_data


class TestSkill:
    """技能测试类"""
    
    def test_execute_success(self):
        """测试成功执行"""
        input_data = {
            "data": "test data",
            "parameters": {"param1": "value1"}
        }
        
        result = execute(input_data)
        
        assert result["success"] is True
        assert "result" in result
        assert result["message"] == "技能执行成功"
    
    def test_execute_empty_input(self):
        """测试空输入"""
        result = execute({})
        
        assert result["success"] is False
        assert "error" in result
    
    def test_process_data(self):
        """测试数据处理函数"""
        data = {"key": "value"}
        result = process_data(data)
        
        assert result["processed"] is True
        assert "data_size" in result
    
    @pytest.mark.asyncio
    async def test_execute_async(self):
        """测试异步执行"""
        from main import execute_async
        
        input_data = {"data": "async test"}
        result = await execute_async(input_data)
        
        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])
```

## 🔒 权限管理

### 权限声明

在`skill.json`中声明所需的权限：

```json
{
    "permissions": [
        "file_read",      # 读取文件
        "file_write",     # 写入文件
        "network_access", # 网络访问
        "database_access",# 数据库访问
        "system_info"     # 系统信息访问
    ]
}
```

### 权限检查

在技能代码中检查权限：

```python
def execute(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # 检查权限（由系统自动处理）
    # 如果权限不足，系统会阻止技能执行
    
    # 业务逻辑...
```

## 📊 性能优化

### 性能最佳实践

1. **内存管理**：及时释放大对象
2. **缓存策略**：合理使用缓存提高性能
3. **异步处理**：IO密集型操作使用异步
4. **批量处理**：减少频繁的系统调用

```python
import asyncio
from functools import lru_cache


@lru_cache(maxsize=128)
def expensive_operation(param):
    """缓存昂贵操作的结果"""
    # 复杂的计算逻辑
    return result


async def process_batch(data_list):
    """批量处理数据"""
    tasks = [process_single_item(item) for item in data_list]
    return await asyncio.gather(*tasks)
```

## 📋 打包发布

### 技能打包

创建技能发布包：

```bash
# 创建技能目录结构
mkdir my-skill-1.0.0
cp skill.json my-skill-1.0.0/
cp main.py my-skill-1.0.0/
cp requirements.txt my-skill-1.0.0/

# 打包为zip文件
zip -r my-skill-1.0.0.zip my-skill-1.0.0/
```

### 发布到技能市场

1. **准备发布材料**：技能包、截图、文档
2. **提交审核**：提交到Py Copilot技能市场
3. **版本管理**：遵循语义化版本规范

## 🔍 调试与日志

### 日志记录

```python
import logging

logger = logging.getLogger(__name__)


def execute(input_data: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("开始执行技能")
    
    try:
        # 业务逻辑
        logger.debug(f"处理数据: {input_data}")
        
        result = process_data(input_data)
        logger.info("技能执行成功")
        
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"技能执行失败: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
```

### 调试技巧

1. **本地测试**：使用`if __name__ == "__main__"`进行本地测试
2. **单元测试**：编写完整的测试用例
3. **日志分析**：使用详细的日志记录
4. **性能分析**：使用性能分析工具

## 🚀 高级特性

### 技能间通信

技能可以通过消息系统进行通信：

```python
def execute(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # 调用其他技能
    other_skill_result = await call_other_skill("data-processor", {"data": input_data})
    
    # 处理结果
    return {"success": True, "result": other_skill_result}
```

### 事件处理

技能可以注册事件处理器：

```python
from app.skills.event_system import register_event_handler


@register_event_handler("file_created")
async def handle_file_created(event_data):
    """处理文件创建事件"""
    # 处理逻辑
    pass
```

## 📚 资源链接

- [Py Copilot 官方文档](https://docs.pycopilot.com)
- [技能市场](https://market.pycopilot.com)
- [开发者社区](https://community.pycopilot.com)
- [API参考文档](./api_reference.md)

---

**版本**: 1.0.0  
**最后更新**: 2024-01-27  
**作者**: Py Copilot开发团队