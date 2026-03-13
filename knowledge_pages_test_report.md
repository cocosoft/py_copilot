# 知识库前端页面测试报告

## 测试概述

通过代码审查和 Playwright 自动化测试，对知识库文档管理页面进行了全面检查。

## 发现的问题

### 1. 搜索功能问题 ⚠️

**现状：**
- SmartSearch 组件存在，提供搜索框、搜索历史、筛选面板等功能
- 但搜索功能**仅在前端进行过滤**，没有调用后端搜索 API

**问题代码位置：**
```javascript
// DocumentManagement/index.jsx 第 151 行
const documents = (response.documents || []).map(doc => ({
  // ...
  vectorizationStatus: doc.is_vectorized ? 'vectorized' : (doc.document_metadata?.processing_status || 'pending'),
}));

// 第 172-174 行 - 仅客户端过滤
const filteredDocs = filterStatus === 'all' || filterStatus === 'vectorized'
  ? sortedDocs
  : sortedDocs.filter(d => d.vectorizationStatus === filterStatus);
```

**建议修复：**
- 搜索应该调用后端 API `/api/v1/knowledge/search` 或 `/api/v1/knowledge/documents?search=xxx`
- 当前仅基于已加载的文档列表进行客户端过滤，无法实现全文搜索

### 2. 文档状态显示问题 ⚠️

**现状：**
- 文档列表页显示的状态基于 `is_vectorized` 字段和 `processing_status`
- 但状态逻辑可能不准确

**问题代码位置：**
```javascript
// DocumentManagement/index.jsx 第 151 行
vectorizationStatus: doc.is_vectorized ? 'vectorized' : (doc.document_metadata?.processing_status || 'pending'),
```

**问题分析：**
1. 当 `is_vectorized = true` 时，显示"已向量化"
2. 当 `is_vectorized = false` 时，显示 `processing_status` 或 "待处理"
3. 但 `processing_status` 可能为 `null`，导致状态显示为"待处理"，而实际可能已经处理失败

**后端状态定义：**
- `idle` - 空闲/待处理
- `queued` - 排队中
- `processing` - 处理中
- `completed` - 已完成
- `failed` - 处理失败

**建议修复：**
```javascript
// 改进状态映射逻辑
const getVectorizationStatus = (doc) => {
  if (doc.is_vectorized) return 'vectorized';
  const status = doc.document_metadata?.processing_status;
  if (status === 'failed') return 'error';
  if (status === 'processing' || status === 'queued') return 'processing';
  return 'pending';
};
```

### 3. 向量片段显示问题 ❌

**现状：**
- 文档详情页面有"向量片段"标签页
- 但用户反馈：前端显示"已向量化"，但详情中没有显示向量片段

**问题分析：**

1. **前端显示逻辑：**
```javascript
// DocumentManagement/index.jsx 第 782-789 行
{selectedDocument.is_vectorized && (
  <button
    className={`detail-tab ${activeTab === 'chunks' ? 'active' : ''}`}
    onClick={() => setActiveTab('chunks')}
  >
    向量片段 ({documentChunks.length})
  </button>
)}
```
- 只有当 `is_vectorized = true` 时才显示"向量片段"标签页

2. **向量片段获取逻辑：**
```javascript
// 第 371-378 行
const fetchDocumentChunks = useCallback(async (docId) => {
  setChunksLoading(true);
  try {
    const response = await getDocumentChunks(docId, 0, 50);
    setDocumentChunks(response.chunks || []);
  } catch (error) {
    console.error('获取文档片段失败:', error);
    setDocumentChunks([]);
  }
  // ...
}, []);
```

3. **后端获取逻辑：**
```python
# knowledge_service.py 第 1025-1040 行
def get_document_chunks(self, document_id: int, db: Session) -> List[Dict[str, Any]]:
    # ...
    chunks = self.retrieval_service.get_document_chunks(document_id)
    return chunks

# retrieval_service.py 第 56-60 行
def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
    where_filter = {"document_id": document_id}
    results = self.chroma_service.search_documents_by_metadata(where_filter)
    return self.format_chunks(results)
```

**可能的原因：**

1. **数据不一致：**
   - 数据库中 `is_vectorized = 1`，但 ChromaDB 中没有对应的向量片段
   - 可能向量化过程部分失败，或者数据被手动修改

2. **ChromaDB 查询问题：**
   - `search_documents_by_metadata` 可能返回空结果
   - metadata 中的 `document_id` 类型不匹配（字符串 vs 整数）

3. **前端渲染问题：**
   - `documentChunks` 为空数组时，显示"暂无向量片段"
   - 但用户可能看不到这个提示

**建议诊断步骤：**

1. 检查数据库中该文档的 `is_vectorized` 和 `vector_id` 字段
2. 直接查询 ChromaDB 验证向量片段是否存在
3. 检查前后端数据类型是否一致

## 修复建议

### 优先级 1：修复向量片段显示问题

1. 添加调试日志，追踪向量片段获取流程
2. 验证 ChromaDB 中的数据与数据库的一致性
3. 修复可能的数据类型不匹配问题

### 优先级 2：完善搜索功能

1. 实现后端全文搜索 API 调用
2. 支持按内容、标题、标签搜索
3. 添加搜索高亮功能

### 优先级 3：优化状态显示

1. 统一前后端状态定义
2. 添加更多状态类型（处理中、排队中、失败等）
3. 显示详细的处理错误信息

## 测试截图

测试脚本已生成，但由于页面动态加载，需要手动查看以下截图：
- `test_screenshots/01_homepage.png` - 首页
- `test_screenshots/02_knowledge_page.png` - 知识库页面
- `test_screenshots/03_document_management.png` - 文档管理页面
- `test_screenshots/04_search_test.png` - 搜索测试
- `test_screenshots/05_document_detail.png` - 文档详情页面

## 后续行动

1. 验证 ChromaDB 中向量片段数据是否存在
2. 检查特定文档的数据库记录和向量数据一致性
3. 根据修复建议逐步改进代码
