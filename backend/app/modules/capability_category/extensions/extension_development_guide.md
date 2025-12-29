# 模型分类扩展点开发指南

## 1. 概述

本指南介绍了模型分类管理系统中的扩展点机制，该机制允许开发者在不修改核心代码的情况下，通过注册扩展函数来扩展或定制分类管理的功能。

扩展点系统提供了以下特性：
- 松耦合的插件架构
- 多种预定义的扩展点
- 简单易用的装饰器API
- 异常安全的执行环境
- 支持链式处理结果

## 2. 架构概述

扩展点系统由以下主要组件组成：

### 2.1 ExtensionManager

`ExtensionManager`是扩展点系统的核心，负责：
- 管理所有扩展点的注册
- 执行注册的扩展函数
- 处理扩展函数的异常

### 2.2 扩展点类型

扩展点分为两种主要类型：

1. **通知型扩展点**：用于接收事件通知，不影响核心流程
2. **处理型扩展点**：用于处理和转换数据，可以影响核心流程的结果

## 3. 使用扩展点

### 3.1 注册扩展函数

可以通过以下两种方式注册扩展函数：

#### 3.1.1 使用装饰器（推荐）

```python
from app.modules.capability_category.extensions.extension_manager import (
    before_create_category,
    after_create_category,
    validate_category_params
)

@before_create_category
def log_category_creation(db, category_data):
    """记录分类创建日志"""
    import logging
    logging.info(f"准备创建分类: {category_data.name}")

@validate_category_params
def validate_category_name(category_data):
    """验证分类名称"""
    if len(category_data.name) < 2:
        return {"error": "分类名称长度不能小于2个字符"}
    return None
```

#### 3.1.2 直接调用register_extension方法

```python
from app.modules.capability_category.extensions.extension_manager import extension_manager

def custom_extension_function(category):
    """自定义扩展函数"""
    category.display_name = f"自定义-{category.display_name}"
    return category

# 注册到after_get_category扩展点
extension_manager.register_extension('after_get_category', custom_extension_function)
```

### 3.2 扩展函数的参数

扩展函数的参数根据扩展点的类型不同而不同，具体参数列表见第4节的扩展点列表。

### 3.3 扩展函数的返回值

- **通知型扩展点**：忽略返回值
- **验证型扩展点**：返回None表示验证通过，返回{"error": "错误信息"}表示验证失败
- **处理型扩展点**：返回处理后的结果，将被传递给下一个扩展函数

## 4. 可用扩展点列表

### 4.1 分类创建相关扩展点

| 扩展点名称 | 类型 | 参数 | 说明 |
|------------|------|------|------|
| `before_create_category` | 通知型 | `db: Session`, `category_data: ModelCategoryCreate` | 分类创建前调用 |
| `after_create_category` | 通知型 | `db: Session`, `category: ModelCategoryDB` | 分类创建后调用 |
| `validate_category_params` | 验证型 | `category_data: Union[ModelCategoryCreate, ModelCategoryUpdate]` | 验证分类参数 |

### 4.2 分类查询相关扩展点

| 扩展点名称 | 类型 | 参数 | 说明 |
|------------|------|------|------|
| `before_get_category` | 通知型 | `db: Session`, `category_id: int` | 单个分类查询前调用 |
| `after_get_category` | 处理型 | `db: Session`, `category: ModelCategoryDB` | 单个分类查询后调用，可以修改返回的分类对象 |
| `before_get_categories` | 通知型 | `db: Session`, 各种查询参数 | 分类列表查询前调用 |
| `after_get_categories` | 处理型 | `result: Dict` | 分类列表查询后调用，可以修改返回结果 |

### 4.3 分类更新相关扩展点

| 扩展点名称 | 类型 | 参数 | 说明 |
|------------|------|------|------|
| `before_update_category` | 通知型 | `db: Session`, `category: ModelCategoryDB`, `update_data: ModelCategoryUpdate` | 分类更新前调用 |
| `after_update_category` | 通知型 | `db: Session`, `category: ModelCategoryDB` | 分类更新后调用 |

### 4.4 分类删除相关扩展点

| 扩展点名称 | 类型 | 参数 | 说明 |
|------------|------|------|------|
| `before_delete_category` | 通知型 | `db: Session`, `category: ModelCategoryDB` | 分类删除前调用 |
| `after_delete_category` | 通知型 | `db: Session`, `category_id: int` | 分类删除后调用 |

### 4.5 模型分类关联相关扩展点

| 扩展点名称 | 类型 | 参数 | 说明 |
|------------|------|------|------|
| `before_add_category_to_model` | 通知型 | `db: Session`, `model_id: int`, `category_id: int` | 模型添加分类前调用 |
| `after_add_category_to_model` | 通知型 | `db: Session`, `association: ModelCategoryAssociation`, `model: ModelDB`, `category: ModelCategoryDB` | 模型添加分类后调用 |
| `before_remove_category_from_model` | 通知型 | `db: Session`, `association: ModelCategoryAssociation` | 模型移除分类前调用 |
| `after_remove_category_from_model` | 通知型 | `db: Session`, `model_id: int`, `category_id: int` | 模型移除分类后调用 |

## 5. 扩展点执行顺序

扩展函数的执行顺序与注册顺序相同。对于处理型扩展点，前一个扩展函数的返回值会作为后一个扩展函数的输入。

## 6. 异常处理

扩展点系统会捕获并记录扩展函数的异常，但不会中断核心流程。这样可以确保即使某个扩展函数失败，核心功能仍然可以正常工作。

```python
@before_create_category
def failing_extension(db, category_data):
    """一个会失败的扩展函数"""
    raise Exception("故意抛出异常")

# 这个扩展函数的异常会被捕获并记录，但不会影响分类的创建
```

## 7. 扩展点示例

### 7.1 示例1：验证分类名称

```python
@validate_category_params
def validate_category_name_length(category_data):
    """验证分类名称长度"""
    if hasattr(category_data, 'name') and len(category_data.name) < 2:
        return {"error": "分类名称长度不能小于2个字符"}
    return None

@validate_category_params
def validate_category_name_unique(db, category_data):
    """验证分类名称唯一性"""
    from app.modules.capability_category.services.model_category_service import ModelCategoryService
    existing = ModelCategoryService.get_category_by_name(db, category_data.name)
    if existing:
        return {"error": f"分类名称 '{category_data.name}' 已存在"}
    return None
```

### 7.2 示例2：自定义分类显示名称

```python
@after_get_category
def custom_display_name(db, category):
    """自定义分类显示名称"""
    if category.dimension == "task_type":
        category.display_name = f"任务类型: {category.display_name}"
    elif category.dimension == "model_size":
        category.display_name = f"模型尺寸: {category.display_name}"
    return category
```

### 7.3 示例3：修改查询结果

```python
@after_get_categories
def add_custom_metadata(result, db):
    """为查询结果添加自定义元数据"""
    result['custom_metadata'] = {
        'timestamp': datetime.now().isoformat(),
        'source': 'custom_extension'
    }
    return result
```

## 8. 扩展开发最佳实践

1. **保持扩展函数简洁**：每个扩展函数应该只负责一个特定的功能
2. **处理异常**：在扩展函数内部处理可能的异常
3. **避免副作用**：尽量减少扩展函数对外部系统的副作用
4. **文档化扩展**：为扩展函数编写清晰的文档说明其功能和参数
5. **测试扩展**：为扩展函数编写单元测试，确保其按预期工作
6. **避免循环依赖**：扩展函数应避免与其他扩展函数产生循环依赖

## 9. 扩展点系统的限制

1. **性能影响**：过多或复杂的扩展函数可能会影响系统性能
2. **调试难度**：扩展函数的执行可能增加调试的复杂性
3. **版本兼容性**：扩展点的参数和行为可能在版本更新中发生变化

## 10. 扩展开发工具

### 10.1 扩展点发现

可以通过以下代码获取所有可用的扩展点：

```python
from app.modules.capability_category.extensions.extension_manager import extension_manager

extension_points = list(extension_manager.extensions.keys())
print("可用扩展点:", extension_points)
```

### 10.2 扩展函数列表

可以通过以下代码获取特定扩展点的所有注册函数：

```python
from app.modules.capability_category.extensions.extension_manager import extension_manager

# 获取before_create_category扩展点的所有注册函数
extensions = extension_manager.extensions.get('before_create_category', [])
for ext in extensions:
    print(f"扩展函数: {ext.__name__}")
```

## 11. 版本历史

| 版本 | 日期 | 更改说明 |
|------|------|----------|
| 1.0 | 2025-12-29 | 初始版本 |

## 12. 联系信息

如有问题或建议，请联系开发团队。