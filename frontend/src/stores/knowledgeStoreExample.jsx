/**
 * 知识库状态管理示例 - FE-002
 *
 * 展示如何使用知识库 Store 和 Hooks
 *
 * @task FE-002
 * @phase 前端界面优化
 */

import React, { useEffect, useCallback } from 'react';
import useKnowledgeStore, {
  useKnowledgeBases,
  useDocuments,
  useDocumentSelection,
  useDocumentFilters,
  useViewState,
  useDocumentStats,
  useKnowledgeActions,
} from '../hooks/useKnowledge';

// ==================== 示例 1: 基础使用 ====================

/**
 * 知识库列表示例
 */
export const KnowledgeBaseListExample = () => {
  const { knowledgeBases, loading, error } = useKnowledgeBases();
  const { setCurrentKnowledgeBase } = useKnowledgeActions();

  if (loading) return <div>加载中...</div>;
  if (error) return <div>错误: {error}</div>;

  return (
    <div className="knowledge-base-list">
      <h3>知识库列表</h3>
      <ul>
        {knowledgeBases.map((kb) => (
          <li
            key={kb.id}
            onClick={() => setCurrentKnowledgeBase(kb)}
            className="knowledge-base-item"
          >
            {kb.name} ({kb.documentCount} 文档)
          </li>
        ))}
      </ul>
    </div>
  );
};

// ==================== 示例 2: 文档列表与选择 ====================

/**
 * 文档列表与选择示例
 */
export const DocumentListWithSelectionExample = () => {
  const { documents, loading, total } = useDocuments();
  const {
    selectedIds,
    selectedCount,
    isAllSelected,
    isPartialSelected,
    toggleSelection,
    selectAll,
  } = useDocumentSelection();

  const handleSelectAll = useCallback(
    (e) => {
      selectAll(e.target.checked);
    },
    [selectAll]
  );

  if (loading) return <div>加载文档中...</div>;

  return (
    <div className="document-list-example">
      <div className="toolbar">
        <label>
          <input
            type="checkbox"
            checked={isAllSelected}
            ref={(el) => {
              if (el) el.indeterminate = isPartialSelected;
            }}
            onChange={handleSelectAll}
          />
          全选 (已选择 {selectedCount} / {total})
        </label>
      </div>

      <ul className="document-list">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className={`document-item ${
              selectedIds.includes(doc.id) ? 'selected' : ''
            }`}
          >
            <input
              type="checkbox"
              checked={selectedIds.includes(doc.id)}
              onChange={() => toggleSelection(doc.id)}
            />
            <span>{doc.title}</span>
            <span className="status">{doc.status}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

// ==================== 示例 3: 过滤器 ====================

/**
 * 文档过滤器示例
 */
export const DocumentFiltersExample = () => {
  const { filters, setFilters, resetFilters } = useDocumentFilters();

  return (
    <div className="filters-example">
      <h4>文档过滤器</h4>

      <div className="filter-group">
        <label>搜索:</label>
        <input
          type="text"
          value={filters.search}
          onChange={(e) => setFilters({ search: e.target.value })}
          placeholder="搜索文档..."
        />
      </div>

      <div className="filter-group">
        <label>状态:</label>
        <select
          value={filters.status}
          onChange={(e) => setFilters({ status: e.target.value })}
        >
          <option value="all">全部</option>
          <option value="active">活跃</option>
          <option value="archived">已归档</option>
        </select>
      </div>

      <div className="filter-group">
        <label>文件类型:</label>
        <select
          value={filters.fileType}
          onChange={(e) => setFilters({ fileType: e.target.value })}
        >
          <option value="all">全部</option>
          <option value="pdf">PDF</option>
          <option value="doc">Word</option>
          <option value="txt">文本</option>
        </select>
      </div>

      <div className="filter-group">
        <label>排序:</label>
        <select
          value={filters.sortBy}
          onChange={(e) => setFilters({ sortBy: e.target.value })}
        >
          <option value="updatedAt">更新时间</option>
          <option value="title">标题</option>
          <option value="size">大小</option>
        </select>

        <select
          value={filters.sortOrder}
          onChange={(e) => setFilters({ sortOrder: e.target.value })}
        >
          <option value="desc">降序</option>
          <option value="asc">升序</option>
        </select>
      </div>

      <button onClick={resetFilters}>重置过滤器</button>

      <div className="filter-summary">
        <h5>当前过滤条件:</h5>
        <pre>{JSON.stringify(filters, null, 2)}</pre>
      </div>
    </div>
  );
};

// ==================== 示例 4: 统计信息 ====================

/**
 * 文档统计示例
 */
export const DocumentStatsExample = () => {
  const stats = useDocumentStats();

  return (
    <div className="stats-example">
      <h4>文档统计</h4>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">总文档数</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">
            {(stats.totalSize / 1024 / 1024).toFixed(2)} MB
          </div>
          <div className="stat-label">总大小</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{stats.totalChunks}</div>
          <div className="stat-label">总片段数</div>
        </div>
      </div>

      <div className="stats-section">
        <h5>按状态分布:</h5>
        <ul>
          {Object.entries(stats.byStatus).map(([status, count]) => (
            <li key={status}>
              {status}: {count} ({((count / stats.total) * 100).toFixed(1)}%)
            </li>
          ))}
        </ul>
      </div>

      <div className="stats-section">
        <h5>按类型分布:</h5>
        <ul>
          {Object.entries(stats.byType).map(([type, count]) => (
            <li key={type}>
              {type}: {count} ({((count / stats.total) * 100).toFixed(1)}%)
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// ==================== 示例 5: 视图状态 ====================

/**
 * 视图控制示例
 */
export const ViewControlExample = () => {
  const { viewMode, sidebarCollapsed, activeTab, setViewMode, toggleSidebar, setActiveTab } =
    useViewState();

  return (
    <div className="view-control-example">
      <h4>视图控制</h4>

      <div className="control-group">
        <label>视图模式:</label>
        <div className="button-group">
          <button
            className={viewMode === 'list' ? 'active' : ''}
            onClick={() => setViewMode('list')}
          >
            列表
          </button>
          <button
            className={viewMode === 'grid' ? 'active' : ''}
            onClick={() => setViewMode('grid')}
          >
            网格
          </button>
          <button
            className={viewMode === 'graph' ? 'active' : ''}
            onClick={() => setViewMode('graph')}
          >
            图谱
          </button>
        </div>
      </div>

      <div className="control-group">
        <label>侧边栏:</label>
        <button onClick={toggleSidebar}>
          {sidebarCollapsed ? '展开' : '折叠'}
        </button>
      </div>

      <div className="control-group">
        <label>活动标签:</label>
        <div className="button-group">
          <button
            className={activeTab === 'documents' ? 'active' : ''}
            onClick={() => setActiveTab('documents')}
          >
            文档
          </button>
          <button
            className={activeTab === 'chunks' ? 'active' : ''}
            onClick={() => setActiveTab('chunks')}
          >
            片段
          </button>
          <button
            className={activeTab === 'entities' ? 'active' : ''}
            onClick={() => setActiveTab('entities')}
          >
            实体
          </button>
          <button
            className={activeTab === 'graph' ? 'active' : ''}
            onClick={() => setActiveTab('graph')}
          >
            图谱
          </button>
        </div>
      </div>

      <div className="view-state-summary">
        <h5>当前视图状态:</h5>
        <pre>
          {JSON.stringify({ viewMode, sidebarCollapsed, activeTab }, null, 2)}
        </pre>
      </div>
    </div>
  );
};

// ==================== 示例 6: 完整集成 ====================

/**
 * 完整集成示例
 */
export const FullIntegrationExample = () => {
  // 使用多个 hooks 组合
  const { documents, loading, page, pageSize, total } = useDocuments();
  const { selectedIds, toggleSelection, selectAll } = useDocumentSelection();
  const { filters, setFilters } = useDocumentFilters();
  const { viewMode, setViewMode } = useViewState();
  const stats = useDocumentStats();

  // 使用 actions
  const {
    setDocuments,
    setDocumentsPage,
    appendDocuments,
    startBatchOperation,
    updateBatchProgress,
    endBatchOperation,
  } = useKnowledgeActions();

  // 模拟加载数据
  const loadDocuments = useCallback(async () => {
    // 模拟 API 调用
    const mockDocuments = Array.from({ length: 20 }, (_, i) => ({
      id: `doc-${page * 20 + i}`,
      title: `文档 ${page * 20 + i + 1}`,
      status: Math.random() > 0.3 ? 'active' : 'archived',
      fileType: ['pdf', 'doc', 'txt'][Math.floor(Math.random() * 3)],
      size: Math.floor(Math.random() * 1000000),
      chunkCount: Math.floor(Math.random() * 100),
      updatedAt: new Date().toISOString(),
    }));

    if (page === 1) {
      setDocuments(mockDocuments, 100);
    } else {
      appendDocuments(mockDocuments, 100);
    }
  }, [page, setDocuments, appendDocuments]);

  // 模拟批量操作
  const handleBatchDelete = useCallback(async () => {
    startBatchOperation('delete');

    for (let i = 0; i < selectedIds.length; i++) {
      // 模拟删除操作
      await new Promise((resolve) => setTimeout(resolve, 100));
      updateBatchProgress(((i + 1) / selectedIds.length) * 100);
    }

    endBatchOperation();
  }, [selectedIds, startBatchOperation, updateBatchProgress, endBatchOperation]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments, page, filters]);

  return (
    <div className="full-integration-example">
      <h3>知识库管理面板</h3>

      {/* 统计信息 */}
      <div className="stats-bar">
        <span>总文档: {stats.total}</span>
        <span>总大小: {(stats.totalSize / 1024 / 1024).toFixed(2)} MB</span>
        <span>总片段: {stats.totalChunks}</span>
      </div>

      {/* 工具栏 */}
      <div className="toolbar">
        <input
          type="text"
          placeholder="搜索文档..."
          value={filters.search}
          onChange={(e) => setFilters({ search: e.target.value })}
        />

        <select
          value={filters.status}
          onChange={(e) => setFilters({ status: e.target.value })}
        >
          <option value="all">全部状态</option>
          <option value="active">活跃</option>
          <option value="archived">已归档</option>
        </select>

        <div className="view-toggle">
          <button
            className={viewMode === 'list' ? 'active' : ''}
            onClick={() => setViewMode('list')}
          >
            列表
          </button>
          <button
            className={viewMode === 'grid' ? 'active' : ''}
            onClick={() => setViewMode('grid')}
          >
            网格
          </button>
        </div>

        {selectedIds.length > 0 && (
          <button onClick={handleBatchDelete}>
            删除选中 ({selectedIds.length})
          </button>
        )}
      </div>

      {/* 文档列表 */}
      {loading ? (
        <div>加载中...</div>
      ) : (
        <div className={`document-list ${viewMode}`}>
          {documents.map((doc) => (
            <div
              key={doc.id}
              className={`document-card ${
                selectedIds.includes(doc.id) ? 'selected' : ''
              }`}
              onClick={() => toggleSelection(doc.id)}
            >
              <input
                type="checkbox"
                checked={selectedIds.includes(doc.id)}
                onChange={() => toggleSelection(doc.id)}
                onClick={(e) => e.stopPropagation()}
              />
              <h4>{doc.title}</h4>
              <p>状态: {doc.status}</p>
              <p>类型: {doc.fileType}</p>
              <p>大小: {(doc.size / 1024).toFixed(2)} KB</p>
            </div>
          ))}
        </div>
      )}

      {/* 分页 */}
      <div className="pagination">
        <button
          disabled={page === 1}
          onClick={() => setDocumentsPage(page - 1)}
        >
          上一页
        </button>
        <span>
          第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
        </span>
        <button
          disabled={page * pageSize >= total}
          onClick={() => setDocumentsPage(page + 1)}
        >
          下一页
        </button>
      </div>
    </div>
  );
};

// ==================== 示例 7: 性能优化 ====================

/**
 * 性能优化示例 - 展示如何避免不必要的重渲染
 */
export const PerformanceOptimizationExample = () => {
  // ❌ 错误方式: 会导致组件在任意状态变化时都重渲染
  // const state = useKnowledgeStore();

  // ✅ 正确方式 1: 只订阅需要的字段
  const documents = useKnowledgeStore((state) => state.documents);

  // ✅ 正确方式 2: 使用 useShallow 订阅多个字段
  const { selectedIds, toggleSelection } = useDocumentSelection();

  // ✅ 正确方式 3: 使用派生状态
  const stats = useDocumentStats();

  return (
    <div className="performance-example">
      <h4>性能优化示例</h4>
      <p>文档数量: {documents.length}</p>
      <p>已选择: {selectedIds.length}</p>
      <p>总大小: {(stats.totalSize / 1024 / 1024).toFixed(2)} MB</p>
      <button onClick={() => toggleSelection('doc-1')}>
        切换第一个文档选择
      </button>
    </div>
  );
};

// ==================== 主示例页面 ====================

const KnowledgeStoreExamples = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h1>知识库状态管理示例 (FE-002)</h1>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '24px',
          marginTop: '24px',
        }}
      >
        <div className="example-card">
          <KnowledgeBaseListExample />
        </div>

        <div className="example-card">
          <DocumentListWithSelectionExample />
        </div>

        <div className="example-card">
          <DocumentFiltersExample />
        </div>

        <div className="example-card">
          <DocumentStatsExample />
        </div>

        <div className="example-card">
          <ViewControlExample />
        </div>

        <div className="example-card">
          <PerformanceOptimizationExample />
        </div>
      </div>

      <div className="example-card" style={{ marginTop: '24px' }}>
        <FullIntegrationExample />
      </div>
    </div>
  );
};

export default KnowledgeStoreExamples;
