# 统一向量化服务使用说明

## 概述

统一向量化服务（`UnifiedVectorizationService`）整合了项目中多个重复的向量化服务，提供统一的向量化接口。

## 解决的问题

### 功能重复问题
- **ChromaService** (vectorization/chroma_service.py)
- **ChromaService** (chroma_service.py) - 完全相同的文件！
- **FAISSIndexService** (vectorization/faiss_index_service.py)
- **FAISSIndexService** (faiss_index_service.py) - 重复类名！
- **VectorStoreAdapter** (vectorization/vector_store_adapter.py)
- **VectorStoreAdapter** (vector_store_adapter.py) - 完全相同的文件！

### 整合的功能模块
- ChromaDB服务：基于 `vectorization/chroma_service.py`
- FAISS索引服务：基于 `vectorization/faiss_index_service.py`
- 向量存储适配器：基于 `vectorization/vector_store_adapter.py`
- 检索服务：基于 `retrieval/retrieval_service.py`
- 语义搜索服务：基于 `retrieval/semantic_search_service.py`

## 使用方法

### 1. 基本使用

```python
from app.services.knowledge.unified_vectorization_service import (
    UnifiedVectorizationService, VectorStoreType
)

# 创建服务实例（默认使用ChromaDB）
service = UnifiedVectorizationService()

# 添加文档到向量存储
documents = ["文档1内容", "文档2内容"]
metadatas = [{"doc_id": 1}, {"doc_id": 2}]
result = service.add_documents(documents, metadatas, "my_collection")

# 向量搜索
search_result = service.search("查询文本", n_results=10, collection_name="my_collection")
```

### 2. 使用不同存储后端

```python
# 使用FAISS后端
faiss_service = UnifiedVectorizationService(VectorStoreType.FAISS)

# 使用混合模式（ChromaDB + FAISS）
hybrid_service = UnifiedVectorizationService(VectorStoreType.HYBRID)
```

### 3. 异步处理

```python
import asyncio

# 异步添加文档
async def add_docs_async():
    result = await service.add_documents_async(documents, metadatas)
    return result

# 异步搜索
async def search_async():
    result = await service.search_async("查询文本", n_results=10)
    return result

# 运行异步操作
result = asyncio.run(add_docs_async())
```

### 4. 语义搜索

```python
# 使用语义搜索
semantic_result = service.semantic_search("查询文本", n_results=10)
```

### 5. 文档管理

```python
# 获取文档分块
chunks = service.get_document_chunks(document_id=123)

# 删除文档
delete_result = service.delete_documents(["doc_id_1", "doc_id_2"])

# 获取集合信息
collection_info = service.get_collection_info("my_collection")
```

## API 接口

### UnifiedVectorizationService 类

#### 构造函数
```python
def __init__(self, vector_store_type: VectorStoreType = VectorStoreType.CHROMA)
```

#### 方法列表

**add_documents** - 添加文档到向量存储
```python
def add_documents(self, documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None,
                 collection_name: str = "default") -> Dict[str, Any]
```

**search** - 向量搜索
```python
def search(self, query: str, n_results: int = 10, collection_name: str = "default",
          filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
```

**semantic_search** - 语义搜索
```python
def semantic_search(self, query: str, n_results: int = 10, 
                   collection_name: str = "default") -> Dict[str, Any]
```

**get_document_chunks** - 获取文档分块
```python
def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]
```

**delete_documents** - 删除文档
```python
def delete_documents(self, document_ids: List[str], 
                    collection_name: str = "default") -> Dict[str, Any]
```

**get_collection_info** - 获取集合信息
```python
def get_collection_info(self, collection_name: str = "default") -> Dict[str, Any]
```

**add_documents_async** - 异步添加文档
```python
async def add_documents_async(self, documents: List[str], 
                             metadatas: Optional[List[Dict[str, Any]]] = None,
                             collection_name: str = "default") -> Dict[str, Any]
```

**search_async** - 异步向量搜索
```python
async def search_async(self, query: str, n_results: int = 10, 
                     collection_name: str = "default",
                     filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
```

### VectorStoreType 枚举

```python
class VectorStoreType(Enum):
    CHROMA = "chroma"    # ChromaDB后端
    FAISS = "faiss"      # FAISS后端
    HYBRID = "hybrid"    # 混合模式
```

## 迁移指南

### 从旧服务迁移

#### 1. 替换 ChromaService

**旧代码：**
```python
from app.services.knowledge.vectorization.chroma_service import ChromaService

service = ChromaService()
result = service.add_documents(documents, metadatas, collection_name)
```

**新代码：**
```python
from app.services.knowledge.unified_vectorization_service import UnifiedVectorizationService

service = UnifiedVectorizationService()
result = service.add_documents(documents, metadatas, collection_name)
```

#### 2. 替换 FAISSIndexService

**旧代码：**
```python
from app.services.knowledge.vectorization.faiss_index_service import FAISSIndexService

service = FAISSIndexService()
result = service.search(query, n_results)
```

**新代码：**
```python
from app.services.knowledge.unified_vectorization_service import (
    UnifiedVectorizationService, VectorStoreType
)

service = UnifiedVectorizationService(VectorStoreType.FAISS)
result = service.search(query, n_results)
```

#### 3. 替换检索服务

**旧代码：**
```python
from app.services.knowledge.retrieval.retrieval_service import RetrievalService

service = RetrievalService()
chunks = service.get_document_chunks(document_id)
```

**新代码：**
```python
from app.services.knowledge.unified_vectorization_service import UnifiedVectorizationService

service = UnifiedVectorizationService()
chunks = service.get_document_chunks(document_id)
```

## 全局实例

为了方便迁移，提供了全局实例：

```python
from app.services.knowledge.unified_vectorization_service import unified_vectorization_service

# 直接使用全局实例
result = unified_vectorization_service.search("查询文本", n_results=10)
```

## 存储后端选择指南

### ChromaDB（默认）
- **优点**：功能完整，支持元数据过滤，易于管理
- **缺点**：需要独立服务运行
- **适用场景**：生产环境，需要完整功能

### FAISS
- **优点**：高性能，内存中运行，无需外部服务
- **缺点**：功能相对简单，重启后数据丢失
- **适用场景**：开发测试，性能要求高的场景

### 混合模式
- **优点**：兼具两者优势，数据冗余存储
- **缺点**：资源消耗较大
- **适用场景**：高可用性要求，数据安全性要求高

## 注意事项

1. **向下兼容**：新服务保持与旧服务相同的接口
2. **渐进迁移**：建议分阶段迁移，避免一次性替换
3. **存储选择**：根据实际需求选择合适的存储后端
4. **性能监控**：监控新服务的性能表现
5. **数据备份**：迁移前确保数据备份

## 版本历史

- **v1.0.0** (2025-03-18): 初始版本，整合多个重复的向量化服务

## 技术支持

如有问题，请参考项目文档或联系开发团队。