# 知识库文件上传性能优化方案 - 实施总结

## 优化方案概览

本次优化针对知识库文件上传慢的问题，从5个维度进行了系统性优化：

### 优化1: 预加载spaCy和jieba模型 ✅

**问题**: 首次处理文档时，需要加载NLP模型（spaCy约2-3秒，jieba约1秒），导致首次处理特别慢。

**解决方案**: 在应用启动时，在后台线程中预加载这些模型。

**实施文件**: `backend/app/api/main.py`

```python
# 预加载知识库处理模型（spaCy和jieba）
def preload_models():
    try:
        # 预加载jieba
        import jieba
        jieba.initialize()
        # 预加载spaCy
        import spacy
        nlp = spacy.load("zh_core_web_sm")
    except Exception as e:
        logger.warning(f"模型预加载失败: {e}")

# 启动后台线程预加载模型
preload_thread = threading.Thread(target=preload_models, daemon=True)
preload_thread.start()
```

**预期效果**: 首次文档处理时间减少3-5秒

---

### 优化2: 实现批量向量化处理 ✅

**问题**: 当前逐个块向量化，每次都有网络请求开销。如果有50个块，需要50次API调用。

**解决方案**: 
1. 在ChromaDB服务器端添加批量添加端点
2. 在客户端添加批量添加方法
3. 修改文档处理器使用批量添加

**实施文件**:
- `backend/chroma_server.py` - 添加 `/collections/{collection_name}/documents/batch` 端点
- `backend/app/services/knowledge/chroma_service.py` - 添加 `add_documents_batch()` 方法
- `backend/app/services/knowledge/document_processor.py` - 使用批量添加

**预期效果**: 向量化速度提升5-10倍（取决于块数量）

---

### 优化3: 添加文档处理进度反馈 ✅

**问题**: 用户不知道处理进度，体验不好。

**解决方案**: 
1. 创建进度追踪服务
2. 在文档处理各阶段更新进度
3. 提供API接口供前端查询

**实施文件**:
- `backend/app/services/knowledge/processing_progress_service.py` - 进度追踪服务
- `backend/app/services/knowledge/document_processor.py` - 集成进度更新
- `backend/app/modules/knowledge/api/knowledge.py` - 添加 `/documents/{document_id}/progress` 接口

**进度阶段**:
1. 文档解析
2. 文本清理
3. 智能分块
4. 实体识别
5. 向量化完成
6. 知识图谱构建

**API响应示例**:
```json
{
  "document_id": "123",
  "status": "processing",
  "current_step": 4,
  "total_steps": 6,
  "step_name": "实体识别",
  "progress_percent": 67,
  "message": "正在识别实体和提取关系..."
}
```

---

### 优化4: 实现文档MD5去重缓存 ✅

**问题**: 重复上传相同文件会重复处理，浪费资源。

**解决方案**: 
1. 在文档模型添加 `file_hash` 字段
2. 上传时计算MD5哈希
3. 检测到重复文件时直接返回已有文档

**实施文件**:
- `backend/app/modules/knowledge/models/knowledge_document.py` - 添加 `file_hash` 字段
- `backend/app/modules/knowledge/services/knowledge_service.py` - 添加去重逻辑
- `backend/app/modules/knowledge/api/knowledge.py` - 处理重复文件响应

**去重响应示例**:
```json
{
  "message": "该文件已存在于知识库中",
  "document_id": 456,
  "status": "duplicate",
  "is_vectorized": true,
  "warning": "系统检测到您上传的文件与知识库中现有文件内容完全相同"
}
```

---

### 优化5: 优化知识图谱构建流程 ✅

**问题**: 每次请求都重新构建图谱，对于相同内容的文档重复计算。

**解决方案**: 
1. 创建知识图谱缓存服务
2. 使用文档内容哈希作为缓存键
3. 缓存TTL设置为1小时

**实施文件**:
- `backend/app/services/knowledge/knowledge_graph_cache.py` - 缓存服务
- `backend/app/services/knowledge/knowledge_graph_service.py` - 集成缓存

**缓存策略**:
- 缓存键: `doc_{document_id}_{content_hash[:16]}`
- TTL: 3600秒（1小时）
- 自动清理过期缓存

---

## 待办事项

### 1. 数据库迁移 ⚠️ 重要

需要为 `knowledge_documents` 表添加 `file_hash` 字段：

```sql
ALTER TABLE knowledge_documents ADD COLUMN file_hash VARCHAR(64) NULL;
CREATE INDEX idx_file_hash ON knowledge_documents(file_hash);
```

或者使用Alembic迁移：

```bash
cd backend
alembic revision --autogenerate -m "add file_hash to knowledge_documents"
alembic upgrade head
```

### 2. 前端进度显示

前端可以轮询 `/api/knowledge/documents/{document_id}/progress` 接口来显示处理进度。

建议实现：
- 上传文件后获取 document_id
- 每2-3秒查询一次进度
- 根据进度更新进度条和状态文字

---

## 性能提升预估

| 优化项 | 预期提升 | 备注 |
|--------|----------|------|
| 模型预加载 | 3-5秒 | 首次处理 |
| 批量向量化 | 5-10倍 | 块数量越多提升越大 |
| 文档去重 | 100% | 重复文件直接返回 |
| 图谱缓存 | 90%+ | 缓存命中时 |

**综合效果**: 对于新文件，处理时间预计减少30-50%；对于重复文件，处理时间减少99%。

---

## 文件变更清单

### 后端文件

1. `backend/app/api/main.py` - 添加模型预加载
2. `backend/chroma_server.py` - 添加批量添加端点
3. `backend/app/services/knowledge/chroma_service.py` - 添加批量添加方法
4. `backend/app/services/knowledge/document_processor.py` - 批量向量化 + 进度反馈
5. `backend/app/services/knowledge/processing_progress_service.py` - 新增进度追踪服务
6. `backend/app/services/knowledge/knowledge_graph_cache.py` - 新增图谱缓存服务
7. `backend/app/services/knowledge/knowledge_graph_service.py` - 集成缓存
8. `backend/app/modules/knowledge/models/knowledge_document.py` - 添加file_hash字段
9. `backend/app/modules/knowledge/services/knowledge_service.py` - 添加去重逻辑
10. `backend/app/modules/knowledge/api/knowledge.py` - 添加进度查询接口 + 重复文件处理

### 新增文件

- `backend/app/services/knowledge/processing_progress_service.py`
- `backend/app/services/knowledge/knowledge_graph_cache.py`
- `backend/PERFORMANCE_OPTIMIZATION_SUMMARY.md`

---

## 测试建议

1. **首次上传测试**: 验证模型预加载是否生效（首次处理应该很快）
2. **批量处理测试**: 上传包含大量文本的文件，验证批量向量化效果
3. **重复文件测试**: 上传相同文件两次，第二次应该立即返回
4. **进度查询测试**: 上传文件后立即查询进度接口，验证进度更新
5. **图谱缓存测试**: 多次查询同一文档的图谱，验证缓存命中

---

## 注意事项

1. 批量向量化端点设置了120秒超时，如果文档块数过多可能需要调整
2. 进度追踪服务每小时自动清理过期记录
3. 知识图谱缓存TTL为1小时，可通过修改 `knowledge_graph_cache.py` 中的 `ttl_seconds` 调整
4. MD5去重只检查同一知识库内的重复文件
