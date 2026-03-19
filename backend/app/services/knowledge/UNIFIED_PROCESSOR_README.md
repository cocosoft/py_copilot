# 统一文档处理器使用说明

## 概述

统一文档处理器（`UnifiedDocumentProcessor`）整合了项目中多个重复的文档处理器，提供统一的文档处理接口。

## 解决的问题

### 功能重复问题
- **DocumentProcessor** (core/document_processor.py)
- **DocumentProcessor** (document_processor.py) - 重复类名！
- **AdaptiveDocumentProcessor** (adaptive_document_processor.py)

### 整合的功能模块
- 文档解析：基于 `core/document_parser.py`
- 文本处理：基于 `core/advanced_text_processor.py`
- 文本分块：基于 `text_processor.py`
- 向量化：基于 `ChromaService`
- 知识图谱：基于 `KnowledgeGraphService`
- 批次处理：基于 `AdaptiveBatchProcessor`

## 使用方法

### 1. 基本使用

```python
from app.services.knowledge.unified_document_processor import UnifiedDocumentProcessor

# 创建处理器实例
processor = UnifiedDocumentProcessor()

# 同步处理文档
result = processor.process_document(
    file_path="/path/to/document.pdf",
    file_type="pdf",
    document_id=123,
    knowledge_base_id=1,
    document_name="测试文档"
)
```

### 2. 异步处理

```python
import asyncio

# 异步处理文档
async def process_async():
    result = await processor.process_document_async(
        file_path="/path/to/document.pdf",
        file_type="pdf",
        document_id=123
    )
    return result

# 运行异步处理
result = asyncio.run(process_async())
```

### 3. 批量处理

```python
# 批量处理文档
async def process_batch():
    documents = [
        {
            'file_path': '/path/to/doc1.pdf',
            'file_type': 'pdf',
            'document_id': 1
        },
        {
            'file_path': '/path/to/doc2.docx',
            'file_type': 'word',
            'document_id': 2
        }
    ]
    
    results = await processor.process_documents_batch(documents)
    return results

# 运行批量处理
results = asyncio.run(process_batch())
```

### 4. 纯文本处理

```python
# 处理纯文本
text = "这是一个测试文档内容..."
chunks = processor.process_document_text(text, chunk_size=1000)
print(f"生成 {len(chunks)} 个文本块")
```

### 5. 查询处理状态

```python
# 查询文档处理状态
status = processor.get_processing_status(document_id=123)
print(f"处理状态: {status}")
```

## API 接口

### UnifiedDocumentProcessor 类

#### 构造函数
```python
def __init__(self, batch_config: Optional[BatchConfig] = None)
```

#### 方法列表

**process_document** - 同步文档处理
```python
def process_document(self, file_path: str, file_type: str, document_id: int,
                   knowledge_base_id: Optional[int] = None, db: Session = None,
                   document_uuid: Optional[str] = None, document_name: str = None) -> Dict[str, Any]
```

**process_document_async** - 异步文档处理
```python
async def process_document_async(self, file_path: str, file_type: str, document_id: int,
                               knowledge_base_id: Optional[int] = None, db: Session = None,
                               document_uuid: Optional[str] = None, document_name: str = None) -> Dict[str, Any]
```

**process_documents_batch** - 批量文档处理
```python
async def process_documents_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

**process_document_text** - 纯文本处理
```python
def process_document_text(self, text: str, chunk_size: int = 1000) -> List[str]
```

**get_processing_status** - 查询处理状态
```python
def get_processing_status(self, document_id: Union[int, str]) -> Dict[str, Any]
```

## 迁移指南

### 从旧处理器迁移

#### 1. 替换 DocumentProcessor

**旧代码：**
```python
from app.services.knowledge.document_processor import DocumentProcessor

processor = DocumentProcessor()
result = processor.process_document(file_path, file_type, document_id)
```

**新代码：**
```python
from app.services.knowledge.unified_document_processor import UnifiedDocumentProcessor

processor = UnifiedDocumentProcessor()
result = processor.process_document(file_path, file_type, document_id)
```

#### 2. 替换 AdaptiveDocumentProcessor

**旧代码：**
```python
from app.services.knowledge.adaptive_document_processor import AdaptiveDocumentProcessor

processor = AdaptiveDocumentProcessor()
result = await processor.process_document_async(file_path, file_type, document_id)
```

**新代码：**
```python
from app.services.knowledge.unified_document_processor import UnifiedDocumentProcessor

processor = UnifiedDocumentProcessor()
result = await processor.process_document_async(file_path, file_type, document_id)
```

## 全局实例

为了方便迁移，提供了全局实例：

```python
from app.services.knowledge.unified_document_processor import unified_document_processor

# 直接使用全局实例
result = unified_document_processor.process_document(file_path, file_type, document_id)
```

## 注意事项

1. **向下兼容**：新处理器保持与旧处理器相同的接口
2. **渐进迁移**：建议分阶段迁移，避免一次性替换
3. **测试验证**：迁移后请进行充分测试
4. **性能监控**：监控新处理器的性能表现

## 版本历史

- **v1.0.0** (2025-03-18): 初始版本，整合三个重复的文档处理器

## 技术支持

如有问题，请参考项目文档或联系开发团队。