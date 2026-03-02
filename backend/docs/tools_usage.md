# 工具系统使用文档

## 概述

Py Copilot 工具系统提供了一套完整的工具调用框架，支持14种不同类型的工具，包括搜索、知识库、记忆、文件操作、文本处理、图像处理、计算、数据处理、代码执行、API调用、日期时间和随机数生成等功能。

## 工具列表

### 1. 联网搜索工具 (web_search)
- **功能**: 使用搜索引擎查询网络信息
- **参数**:
  - `query` (string, 必需): 搜索查询词
  - `engine` (string, 可选): 搜索引擎 (google/bing/baidu)
  - `limit` (integer, 可选): 结果数量限制

**使用示例**:
```python
result = await tool_manager.execute_tool(
    "web_search",
    query="Python异步编程",
    engine="google",
    limit=5
)
```

### 2. 知识库搜索工具 (knowledge_search)
- **功能**: 在知识库中搜索文档
- **参数**:
  - `query` (string, 必需): 搜索查询词
  - `knowledge_base_id` (integer, 可选): 知识库ID
  - `limit` (integer, 可选): 结果数量限制

**使用示例**:
```python
result = await tool_manager.execute_tool(
    "knowledge_search",
    query="机器学习基础",
    limit=10
)
```

### 3. 记忆工具 (memory)
- **功能**: 管理用户记忆
- **参数**:
  - `action` (string, 必需): 操作类型 (search/store/get/list)
  - `query` (string, 可选): 搜索查询词
  - `content` (string, 可选): 记忆内容
  - `title` (string, 可选): 记忆标题
  - `memory_type` (string, 可选): 记忆类型

**使用示例**:
```python
# 存储记忆
result = await tool_manager.execute_tool(
    "memory",
    action="store",
    content="用户喜欢Python编程",
    title="用户偏好",
    memory_type="LONG_TERM"
)

# 搜索记忆
result = await tool_manager.execute_tool(
    "memory",
    action="search",
    query="Python"
)
```

### 4. 文件操作工具 (file_operation)
- **功能**: 文件读写和管理
- **参数**:
  - `action` (string, 必需): 操作类型 (read/write/list/info/delete)
  - `file_path` (string, 可选): 文件路径
  - `content` (string, 可选): 文件内容
  - `user_id` (integer, 必需): 用户ID

**使用示例**:
```python
# 读取文件
result = await tool_manager.execute_tool(
    "file_operation",
    action="read",
    file_path="/path/to/file.txt",
    user_id=1
)

# 写入文件
result = await tool_manager.execute_tool(
    "file_operation",
    action="write",
    content="Hello World",
    filename="hello.txt",
    user_id=1
)
```

### 5. 文本处理工具 (text_processing)
- **功能**: 文本清理、分块、格式化
- **参数**:
  - `action` (string, 必需): 操作类型 (clean/chunk/process/count/extract)
  - `text` (string, 必需): 输入文本
  - `chunk_size` (integer, 可选): 分块大小

**使用示例**:
```python
# 清理文本
result = await tool_manager.execute_tool(
    "text_processing",
    action="clean",
    text="  Hello   World  \n\n  "
)

# 文本分块
result = await tool_manager.execute_tool(
    "text_processing",
    action="chunk",
    text="长文本内容...",
    chunk_size=500
)

# 提取信息
result = await tool_manager.execute_tool(
    "text_processing",
    action="extract",
    text="联系邮箱: example@email.com, 网址: https://example.com"
)
```

### 6. 图像处理工具 (image_processing)
- **功能**: 图像调整、格式转换、OCR
- **参数**:
  - `action` (string, 必需): 操作类型
  - `image_path` (string, 必需): 图像路径
  - `width/height` (integer, 可选): 目标尺寸
  - `format` (string, 可选): 目标格式

**使用示例**:
```python
# 调整图像大小
result = await tool_manager.execute_tool(
    "image_processing",
    action="resize",
    image_path="/path/to/image.jpg",
    width=800,
    height=600
)

# 获取图像信息
result = await tool_manager.execute_tool(
    "image_processing",
    action="get_info",
    image_path="/path/to/image.jpg"
)

# 格式转换
result = await tool_manager.execute_tool(
    "image_processing",
    action="convert_format",
    image_path="/path/to/image.jpg",
    format="PNG"
)
```

### 7. 计算器工具 (calculator)
- **功能**: 数学计算、表达式求值、单位转换
- **参数**:
  - `expression` (string, 必需): 数学表达式
  - `precision` (integer, 可选): 结果精度
  - `operation` (string, 可选): 操作类型

**使用示例**:
```python
# 基本计算
result = await tool_manager.execute_tool(
    "calculator",
    expression="2 + 3 * 4"
)

# 科学计算
result = await tool_manager.execute_tool(
    "calculator",
    expression="sqrt(16) + sin(pi/2)"
)

# 统计计算
result = await tool_manager.execute_tool(
    "calculator",
    expression="1,2,3,4,5",
    operation="statistical"
)

# 单位转换
result = await tool_manager.execute_tool(
    "calculator",
    expression="100 km to miles",
    operation="conversion"
)
```

### 8. 数据处理工具 (data_processing)
- **功能**: 数据转换、格式化、验证、分析
- **参数**:
  - `action` (string, 必需): 操作类型
  - `data` (string, 必需): 输入数据
  - `options` (object, 可选): 操作选项

**使用示例**:
```python
# JSON转CSV
json_data = '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'
result = await tool_manager.execute_tool(
    "data_processing",
    action="json_to_csv",
    data=json_data
)

# 格式化JSON
result = await tool_manager.execute_tool(
    "data_processing",
    action="format_json",
    data='{"name":"Alice","age":30}'
)

# 验证JSON
result = await tool_manager.execute_tool(
    "data_processing",
    action="validate_json",
    data='{"name": "Alice"}'
)
```

### 9. 代码执行工具 (code_execution)
- **功能**: 安全执行代码
- **参数**:
  - `code` (string, 必需): 代码内容
  - `language` (string, 必需): 编程语言
  - `timeout` (integer, 可选): 超时时间

**使用示例**:
```python
# 执行Python代码
result = await tool_manager.execute_tool(
    "code_execution",
    code="print('Hello, World!')",
    language="python",
    timeout=10
)

# 执行JavaScript代码
result = await tool_manager.execute_tool(
    "code_execution",
    code="console.log('Hello');",
    language="javascript"
)
```

### 10. API调用工具 (api_call)
- **功能**: 发送HTTP请求
- **参数**:
  - `url` (string, 必需): 请求URL
  - `method` (string, 可选): HTTP方法
  - `headers` (object, 可选): 请求头
  - `data` (object, 可选): 请求体

**使用示例**:
```python
# GET请求
result = await tool_manager.execute_tool(
    "api_call",
    url="https://api.example.com/data",
    method="GET"
)

# POST请求
result = await tool_manager.execute_tool(
    "api_call",
    url="https://api.example.com/submit",
    method="POST",
    data={"key": "value"},
    headers={"Authorization": "Bearer token"}
)
```

### 11. 日期时间工具 (datetime)
- **功能**: 日期时间获取、格式化、计算
- **参数**:
  - `action` (string, 必需): 操作类型
  - `datetime_str` (string, 可选): 日期时间字符串
  - `format` (string, 可选): 格式字符串

**使用示例**:
```python
# 获取当前时间
result = await tool_manager.execute_tool(
    "datetime",
    action="now"
)

# 格式化日期时间
result = await tool_manager.execute_tool(
    "datetime",
    action="format",
    datetime_str="2024-01-15 10:30:00",
    format="%Y年%m月%d日"
)

# 添加时间
result = await tool_manager.execute_tool(
    "datetime",
    action="add",
    datetime_str="2024-01-15",
    amount=7,
    unit="days"
)

# 获取日历
result = await tool_manager.execute_tool(
    "datetime",
    action="get_calendar",
    year=2024,
    month=1
)
```

### 12. 随机数生成工具 (random_generator)
- **功能**: 生成随机数、字符串、UUID等
- **参数**:
  - `action` (string, 必需): 操作类型
  - `min_value/max_value` (number, 可选): 数值范围
  - `length` (integer, 可选): 长度
  - `count` (integer, 可选): 数量

**使用示例**:
```python
# 生成随机整数
result = await tool_manager.execute_tool(
    "random_generator",
    action="integer",
    min_value=1,
    max_value=100
)

# 生成随机字符串
result = await tool_manager.execute_tool(
    "random_generator",
    action="string",
    length=10
)

# 生成密码
result = await tool_manager.execute_tool(
    "random_generator",
    action="password",
    length=16,
    include_special=True
)

# 生成UUID
result = await tool_manager.execute_tool(
    "random_generator",
    action="uuid"
)

# 随机选择
result = await tool_manager.execute_tool(
    "random_generator",
    action="choice",
    choices=["选项A", "选项B", "选项C"]
)
```

## API接口

### 获取工具列表
```http
GET /api/v1/tools
```

**查询参数**:
- `category`: 按类别过滤
- `active_only`: 仅返回激活的工具

### 获取工具详情
```http
GET /api/v1/tools/{tool_name}
```

### 执行工具
```http
POST /api/v1/tools/execute
Content-Type: application/json

{
    "tool_name": "calculator",
    "params": {
        "expression": "1 + 1"
    }
}
```

### 批量执行工具
```http
POST /api/v1/tools/execute/batch
Content-Type: application/json

{
    "calls": [
        {
            "tool_name": "calculator",
            "params": {"expression": "1 + 1"}
        },
        {
            "tool_name": "datetime",
            "params": {"action": "now"}
        }
    ]
}
```

### 获取工具统计
```http
GET /api/v1/tools/statistics
```

### 启用/禁用工具
```http
POST /api/v1/tools/{tool_name}/enable?enable=true
```

## 开发新工具

### 1. 继承BaseTool
```python
from app.modules.function_calling.base_tool import BaseTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter, ToolMetadata, ToolExecutionResult
)

class MyNewTool(BaseTool):
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_new_tool",
            display_name="我的新工具",
            description="工具描述",
            category="utility",
            version="1.0.0",
            author="Your Name",
            icon="🔧",
            tags=["标签1", "标签2"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="param1",
                type="string",
                description="参数描述",
                required=True
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        # 实现工具逻辑
        pass
```

### 2. 注册工具
```python
from app.modules.function_calling.tool_manager import tool_manager
from app.modules.function_calling.tools import MyNewTool

tool_manager.register_tool(MyNewTool())
```

## 最佳实践

1. **参数验证**: 始终使用 `validate_parameters()` 方法验证输入参数
2. **错误处理**: 使用 `ToolExecutionResult.error_result()` 返回错误信息
3. **执行时间**: 记录工具执行时间，便于性能分析
4. **日志记录**: 使用 `logger` 记录工具执行日志
5. **资源清理**: 确保在工具执行完成后清理临时资源

## 注意事项

1. 代码执行工具有安全检查，禁止执行危险操作
2. API调用工具默认超时时间为30秒
3. 图像处理工具需要安装Pillow库
4. OCR功能需要安装pytesseract和Tesseract-OCR引擎
5. 时区转换需要安装pytz库
