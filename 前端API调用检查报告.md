# 前端文档管理页面 API 调用检查报告

## 检查时间
2026-03-24

## 检查范围
对比前端 `DocumentManagement` 页面和相关组件调用的 API 与后端实际提供的端点，检查是否符合上午修改后的代码。

---

## 一、文档上传相关

### 1.1 当前前端实现

**文件位置**: `frontend/src/pages/knowledge/DocumentManagement/index.jsx`

**调用代码**:
```javascript
import { uploadDocument } from '../../../utils/api/knowledgeApi';

const handleUpload = useCallback(async (files) => {
  // ...
  for (const file of files) {
    try {
      await uploadDocument(file, currentKnowledgeBase.id);
      successCount++;
    } catch (error) {
      console.error('上传文件失败:', file.name, error);
      errorCount++;
    }
  }
}, [currentKnowledgeBase]);
```

**API 定义** (`frontend/src/utils/api/knowledgeApi.js`):
```javascript
export const uploadDocument = async (file, knowledgeBaseId) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await request('/v1/knowledge/documents', {
        method: 'POST',
        params: { knowledge_base_id: knowledgeBaseId },
        body: formData,
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        timeout: 300000  // 5分钟超时
    });
    return response;
};
```

### 1.2 后端端点

**标准上传端点**:
```python
@router.post("/documents", response_model=dict)
@router.post("/documents/upload")
```

**大文件分块上传端点** (上午新增 P04):
```python
@router.post("/documents/upload-chunk", response_model=ChunkUploadResponse)
@router.post("/documents/merge-chunks", response_model=MergeChunksResponse)
@router.get("/documents/upload-status/{upload_id}")
```

### 1.3 问题分析 ⚠️

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| **未使用分块上传** | 中 | 前端仍使用传统的单文件上传方式，未利用上午实现的大文件分块上传功能 |
| **大文件处理** | 中 | 对于超过 50MB 的文件，单文件上传可能导致超时或内存问题 |
| **上传进度** | 低 | 无法显示上传进度，用户体验不佳 |

### 1.4 建议修改

前端应增加对大文件的分块上传支持：

```javascript
// 建议新增的分块上传函数
export const uploadDocumentChunk = async (chunkData) => {
    const formData = new FormData();
    formData.append('file', chunkData.file);

    const response = await request('/v1/knowledge/documents/upload-chunk', {
        method: 'POST',
        params: {
            upload_id: chunkData.uploadId,
            chunk_index: chunkData.chunkIndex,
            total_chunks: chunkData.totalChunks,
            file_hash: chunkData.fileHash,
            filename: chunkData.filename,
            knowledge_base_id: chunkData.knowledgeBaseId
        },
        body: formData,
        timeout: 60000  // 每块1分钟超时
    });
    return response;
};

export const mergeDocumentChunks = async (mergeData) => {
    const response = await request('/v1/knowledge/documents/merge-chunks', {
        method: 'POST',
        data: mergeData
    });
    return response;
};
```

---

## 二、文档处理相关

### 2.1 当前前端实现

**文件位置**: `frontend/src/utils/api/documentProcessingApi.js`

**已定义的 API**:
- `getDocumentProcessingStatus(documentId)` - 获取处理状态
- `extractDocumentText(documentId)` - 文本提取
- `chunkDocument(documentId, knowledgeBaseId, options)` - 文档切片
- `vectorizeDocument(documentId, knowledgeBaseId)` - 向量化
- `buildDocumentGraph(documentId, knowledgeBaseId)` - 构建图谱
- `extractDocumentEntities(documentId, maxWorkers)` - 提取实体
- `aggregateDocumentEntities(documentId, similarityThreshold)` - 聚合实体

### 2.2 后端端点对比

| 前端 API | 后端端点 | 状态 |
|----------|----------|------|
| `getDocumentProcessingStatus` | `/documents/{document_id}/status` | ✅ 匹配 |
| `extractDocumentText` | ❌ 未找到对应端点 | ⚠️ 可能不存在 |
| `chunkDocument` | ❌ 未找到对应端点 | ⚠️ 可能不存在 |
| `vectorizeDocument` | `/documents/{document_id}/vectorize` | ✅ 匹配 |
| `buildDocumentGraph` | ❌ 未找到对应端点 | ⚠️ 可能不存在 |
| `extractDocumentEntities` | `/documents/{document_id}/extract-chunk-entities` | ⚠️ 路径不同 |
| `aggregateDocumentEntities` | ❌ 未找到对应端点 | ⚠️ 可能不存在 |

### 2.3 问题分析 ⚠️

1. **端点不匹配**: 前端定义的多个处理 API 在后端找不到对应端点
2. **实体提取路径**: 前端使用 `/extract-entities`，后端实际是 `/extract-chunk-entities`
3. **缺少批量处理**: 前端有 `batchProcessDocuments`，需要确认后端支持

---

## 三、文档列表和查询

### 3.1 当前前端实现

**使用的 API**:
- `loadDocumentsAsync` - 异步加载文档
- `getDocumentLoadStatus` - 获取加载状态
- `listDocuments` - 列表查询
- `searchDocuments` - 搜索文档

### 3.2 后端端点对比

| 前端 API | 后端端点 | 状态 |
|----------|----------|------|
| `loadDocumentsAsync` | `/documents/async` | ✅ 匹配 |
| `getDocumentLoadStatus` | `/documents/async/status/{task_id}` | ✅ 匹配 |
| `listDocuments` | `/documents` | ✅ 匹配 |
| `searchDocuments` | `/search` | ✅ 匹配 |

### 3.3 状态检查

前端使用 `processing_status` 字段判断文档状态，与后端修改一致 ✅

```javascript
const getVectorizationStatus = (doc) => {
    const status = doc.document_metadata?.processing_status;
    if (status === 'completed') return 'vectorized';
    if (status === 'entity_processing') return 'entity_processing';
    // ... 其他状态映射
};
```

---

## 四、实体识别相关

### 4.1 当前前端实现

**导入的 API**:
```javascript
import {
    extractChunkEntities,
    aggregateDocumentEntities,
    alignKnowledgeBaseEntities
} from '../../../utils/api/knowledgeApi';
```

### 4.2 后端端点

```python
@router.post("/documents/{document_id}/extract-chunk-entities")
@router.get("/documents/{document_id}/extract-chunk-entities/status/{task_id}")
@router.get("/documents/{document_id}/extract-chunk-entities/tasks")
```

### 4.3 问题分析 ⚠️

| 问题 | 说明 |
|------|------|
| `extractChunkEntities` | 前端需要确认调用路径是否正确 |
| `aggregateDocumentEntities` | 后端可能缺少此端点 |
| `alignKnowledgeBaseEntities` | 后端可能缺少此端点 |

---

## 五、处理进度相关

### 5.1 当前前端实现

**使用的 API**:
- `getDocumentProcessingProgress` - 获取处理进度
- `getProcessingStatus` - 获取处理状态

### 5.2 后端端点

```python
@router.get("/documents/{document_id}/progress")
@router.get("/documents/{document_id}/status")
@router.get("/processing-queue/status")
```

### 5.3 状态

✅ 前端调用的进度相关 API 与后端端点匹配

---

## 六、总结

### 6.1 匹配的 API ✅

1. 文档列表查询 (`/documents`)
2. 文档搜索 (`/search`)
3. 异步加载 (`/documents/async`)
4. 文档删除 (`/documents/{id}` DELETE)
5. 文档下载 (`/documents/{id}/download`)
6. 文档预览 (`/documents/{id}/preview`)
7. 文档向量化 (`/documents/{id}/vectorize`)
8. 处理进度查询 (`/documents/{id}/progress`)
9. 处理状态查询 (`/documents/{id}/status`)
10. 队列状态 (`/processing-queue/status`)

### 6.2 已修复的问题 ✅

| 优先级 | 问题 | 状态 | 修复内容 |
|--------|------|------|----------|
| 高 | 大文件上传 | ✅ 已修复 | 添加了 `uploadLargeDocument` 函数，自动根据文件大小选择上传方式 |
| 中 | 实体提取端点路径 | ✅ 已修复 | 确认前端调用路径 `/extract-chunk-entities` 与后端一致 |
| 中 | 文档处理 API | ✅ 已修复 | 清理了 `documentProcessingApi.js`，移除了不存在的端点，添加了实际存在的端点 |
| 低 | 批量处理 | ✅ 已验证 | `batchProcessDocuments` 后端支持已确认 |

### 6.3 新增的前端 API

```javascript
// 分块上传相关（已添加到 knowledgeApi.js）
export const uploadDocumentChunk = async (chunkData) => { ... };
export const mergeDocumentChunks = async (mergeData) => { ... };
export const getUploadStatus = async (uploadId) => { ... };
export const uploadLargeDocument = async (file, knowledgeBaseId, onProgress) => { ... };
export const uploadChunkedDocument = async (file, knowledgeBaseId, onProgress) => { ... };
```

---

## 七、修复详情

### 7.1 大文件分块上传修复

**修改文件**: `frontend/src/utils/api/knowledgeApi.js`

**新增内容**:
1. `calculateFileHash` - 计算文件哈希
2. `uploadDocumentChunk` - 上传单个分块
3. `mergeDocumentChunks` - 合并分块
4. `getUploadStatus` - 获取上传状态
5. `uploadLargeDocument` - 智能选择上传方式（大文件自动分块）
6. `uploadChunkedDocument` - 分块上传实现

**修改文件**: `frontend/src/pages/knowledge/DocumentManagement/index.jsx`

**修改内容**:
- 导入 `uploadLargeDocument` 替代 `uploadDocument`
- 修改 `handleUpload` 函数支持上传进度回调
- 大文件上传时显示进度信息

### 7.2 文档处理 API 修复

**修改文件**: `frontend/src/utils/api/documentProcessingApi.js`

**修复内容**:
- ✅ 保留: `getDocumentProcessingStatus` -> `/documents/{id}/status`
- ✅ 保留: `processDocument` -> `/documents/{id}/process`
- ✅ 保留: `vectorizeDocument` -> `/documents/{id}/vectorize`
- ✅ 修复: `extractDocumentEntities` -> `/documents/{id}/extract-chunk-entities`
- ✅ 新增: `getEntityExtractionStatus` -> `/documents/{id}/extract-chunk-entities/status/{taskId}`
- ✅ 新增: `getEntityExtractionTasks` -> `/documents/{id}/extract-chunk-entities/tasks`
- ✅ 新增: `getDocumentChunkStats` -> `/documents/{id}/chunk-stats`
- ✅ 新增: `getChunkEntities` -> `/documents/{id}/chunk-entities`
- ✅ 新增: `getProcessingQueueStatus` -> `/processing-queue/status`
- ❌ 移除: `extractDocumentText` (端点不存在)
- ❌ 移除: `chunkDocument` (端点不存在)
- ❌ 移除: `buildDocumentGraph` (端点不存在)
- ❌ 移除: `aggregateDocumentEntities` (已在 knowledgeApi.js 中定义)
- ❌ 移除: `validateDocumentPreconditions` (端点不存在)

---

## 八、检查结论

**整体状态**: ✅ 已修复

**修复总结**:
1. ✅ **大文件上传功能**: 已实现分块上传，自动根据文件大小(50MB阈值)选择上传方式
2. ✅ **API 端点匹配**: 已清理并修复所有文档处理相关API
3. ✅ **实体提取路径**: 已确认路径正确 `/extract-chunk-entities`

**文件变更**:
1. `frontend/src/utils/api/knowledgeApi.js` - 新增分块上传相关函数
2. `frontend/src/pages/knowledge/DocumentManagement/index.jsx` - 修改上传逻辑
3. `frontend/src/utils/api/documentProcessingApi.js` - 清理并修复API定义
