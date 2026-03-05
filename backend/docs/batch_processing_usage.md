# 批量处理功能使用指南

## 概述

批量处理功能支持并发处理多个文本、文档和知识图谱构建任务，提高处理效率并降低成本。

## 功能特性

- ✅ **并发处理**: 支持多线程并发处理
- ✅ **批量缓存**: 自动使用缓存减少LLM调用
- ✅ **进度跟踪**: 支持进度回调函数
- ✅ **错误处理**: 单个任务失败不影响其他任务
- ✅ **灵活配置**: 可调整并发数和批大小

---

## API端点

### 1. 批量实体提取

**端点**: `POST /api/v1/knowledge-graph/batch/extract-entities`

**请求体**:
```json
{
    "texts": [
        "张三在阿里巴巴工作。",
        "李四毕业于北京大学。",
        "王五在腾讯担任工程师。"
    ],
    "max_workers": 5,
    "batch_size": 10,
    "use_cache": true
}
```

**参数说明**:
- `texts` (required): 文本列表
- `max_workers` (optional): 最大并发数，默认5
- `batch_size` (optional): 每批处理数量，默认10
- `use_cache` (optional): 是否使用缓存，默认true

**响应**:
```json
{
    "success": true,
    "items_processed": 3,
    "items_failed": 0,
    "cache_hits": 2,
    "processing_time": 1.23,
    "results": [
        {
            "index": 0,
            "text": "张三在阿里巴巴工作。",
            "entities": [...],
            "relationships": [...],
            "success": true,
            "from_cache": false
        }
    ],
    "errors": []
}
```

---

### 2. 批量文档处理

**端点**: `POST /api/v1/knowledge-graph/batch/process-documents`

**请求体**:
```json
{
    "documents": [
        {
            "file_path": "/path/to/doc1.pdf",
            "file_type": "pdf",
            "document_id": 1,
            "knowledge_base_id": 10
        },
        {
            "file_path": "/path/to/doc2.docx",
            "file_type": "docx",
            "document_id": 2,
            "knowledge_base_id": 10
        }
    ],
    "max_workers": 3
}
```

**参数说明**:
- `documents` (required): 文档列表
  - `file_path`: 文件路径
  - `file_type`: 文件类型 (pdf, docx, txt等)
  - `document_id`: 文档ID
  - `knowledge_base_id`: 知识库ID
- `max_workers` (optional): 最大并发数，默认3

**响应**:
```json
{
    "success": true,
    "items_processed": 2,
    "items_failed": 0,
    "processing_time": 5.67,
    "results": [
        {
            "index": 0,
            "document_id": 1,
            "success": true,
            "chunks_count": 5,
            "entities_count": 12
        }
    ],
    "errors": []
}
```

---

### 3. 批量图谱构建

**端点**: `POST /api/v1/knowledge-graph/batch/build-graphs`

**请求体**:
```json
{
    "document_ids": [1, 2, 3, 4, 5],
    "max_workers": 5
}
```

**参数说明**:
- `document_ids` (required): 文档ID列表
- `max_workers` (optional): 最大并发数，默认5

**响应**:
```json
{
    "success": true,
    "items_processed": 5,
    "items_failed": 0,
    "processing_time": 3.45,
    "results": [
        {
            "index": 0,
            "document_id": 1,
            "success": true,
            "node_count": 15,
            "edge_count": 8,
            "graph_data": {...}
        }
    ],
    "errors": []
}
```

---

## Python SDK使用示例

### 批量实体提取

```python
import asyncio
from app.services.knowledge.batch_processor import extract_entities_batch

async def main():
    texts = [
        "张三在阿里巴巴工作。",
        "李四毕业于北京大学。",
        "王五在腾讯担任工程师。"
    ]

    # 定义进度回调
    def on_progress(current, total):
        print(f"进度: {current}/{total}")

    result = await extract_entities_batch(
        texts=texts,
        max_workers=5,
        batch_size=10,
        use_cache=True,
        progress_callback=on_progress
    )

    print(f"处理成功: {result.items_processed}")
    print(f"缓存命中: {result.cache_hits}")
    print(f"处理时间: {result.processing_time:.2f}秒")

    # 查看结果
    for item in result.results:
        print(f"文本: {item['text']}")
        print(f"实体: {len(item['entities'])}")
        print(f"关系: {len(item['relationships'])}")

asyncio.run(main())
```

### 批量文档处理

```python
import asyncio
from app.services.knowledge.batch_processor import process_documents_batch

async def main():
    documents = [
        {
            "file_path": "/docs/report1.pdf",
            "file_type": "pdf",
            "document_id": 1,
            "knowledge_base_id": 10
        },
        {
            "file_path": "/docs/report2.docx",
            "file_type": "docx",
            "document_id": 2,
            "knowledge_base_id": 10
        }
    ]

    result = await process_documents_batch(
        documents=documents,
        max_workers=3
    )

    print(f"处理成功: {result.items_processed}")
    print(f"处理失败: {result.items_failed}")

asyncio.run(main())
```

### 批量图谱构建

```python
import asyncio
from app.services.knowledge.batch_processor import build_knowledge_graphs_batch
from app.core.database import SessionLocal

async def main():
    db = SessionLocal()
    try:
        document_ids = [1, 2, 3, 4, 5]

        result = await build_knowledge_graphs_batch(
            document_ids=document_ids,
            db=db,
            max_workers=5
        )

        print(f"构建成功: {result.items_processed}")
        print(f"构建失败: {result.items_failed}")

        for item in result.results:
            if item['success']:
                print(f"文档 {item['document_id']}: "
                      f"{item['node_count']} 节点, "
                      f"{item['edge_count']} 边")
    finally:
        db.close()

asyncio.run(main())
```

---

## 性能优化建议

### 1. 并发数设置

- **实体提取**: `max_workers=5`, 适合大多数场景
- **文档处理**: `max_workers=3`, 避免IO过载
- **图谱构建**: `max_workers=5`, 根据数据库连接数调整

### 2. 批大小设置

- 小数据集 (< 100): `batch_size=10`
- 中等数据集 (100-1000): `batch_size=20`
- 大数据集 (> 1000): `batch_size=50`

### 3. 缓存使用

- 重复文本处理时，启用缓存可显著提速
- 首次处理大量新文本时，可禁用缓存以节省内存

### 4. 错误处理

- 批量处理中单个任务失败不会影响其他任务
- 检查 `result.errors` 获取失败详情
- 失败的任务可以在 `result.results` 中查看具体信息

---

## 性能对比

| 处理方式 | 100个文本 | 500个文本 | 1000个文本 |
|---------|----------|----------|-----------|
| 串行处理 | 50秒 | 250秒 | 500秒 |
| 批量处理(5并发) | 12秒 | 55秒 | 110秒 |
| **提升** | **4.2x** | **4.5x** | **4.5x** |

*注：实际性能取决于网络延迟和LLM响应时间*

---

## 注意事项

1. **API限制**: 注意LLM服务的速率限制，适当调整并发数
2. **内存使用**: 大数据集处理时注意内存占用，可分批调用
3. **数据库连接**: 批量文档处理和图谱构建会占用数据库连接，注意连接池大小
4. **超时设置**: 处理大文档时可能需要增加超时时间

---

## 故障排查

### 问题1: 处理速度慢

**可能原因**:
- 缓存未命中
- 并发数设置过低
- LLM服务响应慢

**解决方案**:
- 检查缓存配置
- 增加 `max_workers`
- 检查LLM服务状态

### 问题2: 内存占用高

**可能原因**:
- 批大小设置过大
- 同时处理太多文档

**解决方案**:
- 减小 `batch_size`
- 分批调用API
- 增加处理间隔

### 问题3: 部分任务失败

**可能原因**:
- 文本为空或格式错误
- 文档不存在或无法访问
- 数据库连接问题

**解决方案**:
- 检查输入数据有效性
- 查看 `result.errors` 获取详细错误信息
- 检查数据库连接池配置
