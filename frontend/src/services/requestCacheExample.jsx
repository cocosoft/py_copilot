/**
 * 请求缓存使用示例 - FE-003
 *
 * 展示如何使用请求缓存服务
 *
 * @task FE-003
 * @phase 前端界面优化
 */

import React, { useState, useCallback } from 'react';
import {
  useKnowledgeBases,
  useDocuments,
  useDocument,
  useChunks,
  useEntities,
  useKnowledgeSearch,
  useKnowledgeStats,
  useCreateDocument,
  useUpdateDocument,
  useDeleteDocument,
  useBatchDeleteDocuments,
  useCacheManager,
  usePrefetch,
} from '../hooks/useCachedQuery';
import requestCacheService from './requestCacheService';

// ==================== 示例 1: 基础查询 ====================

/**
 * 知识库列表示例
 */
export const KnowledgeBasesExample = () => {
  const { data, isLoading, error, refetch } = useKnowledgeBases();

  if (isLoading) return <div>加载知识库列表...</div>;
  if (error) return <div>错误: {error.message}</div>;

  return (
    <div className="example-section">
      <h3>知识库列表 (缓存10分钟)</h3>
      <button onClick={() => refetch()}>刷新</button>
      <ul>
        {data?.map((kb) => (
          <li key={kb.id}>
            {kb.name} - {kb.documentCount} 文档
          </li>
        ))}
      </ul>
    </div>
  );
};

// ==================== 示例 2: 带参数的查询 ====================

/**
 * 文档列表示例
 */
export const DocumentsExample = () => {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const params = { page, pageSize: 20, search };
  const { data, isLoading, error } = useDocuments(params);

  return (
    <div className="example-section">
      <h3>文档列表 (缓存2分钟)</h3>

      <div className="filters">
        <input
          type="text"
          placeholder="搜索文档..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div>加载中...</div>
      ) : (
        <>
          <ul>
            {data?.items?.map((doc) => (
              <li key={doc.id}>{doc.title}</li>
            ))}
          </ul>

          <div className="pagination">
            <button disabled={page === 1} onClick={() => setPage(page - 1)}>
              上一页
            </button>
            <span>第 {page} 页</span>
            <button onClick={() => setPage(page + 1)}>下一页</button>
          </div>
        </>
      )}
    </div>
  );
};

// ==================== 示例 3: 详情查询 ====================

/**
 * 文档详情示例
 */
export const DocumentDetailExample = ({ documentId }) => {
  const { data, isLoading, error } = useDocument(documentId);

  if (!documentId) return <div>请选择文档</div>;
  if (isLoading) return <div>加载文档详情...</div>;
  if (error) return <div>错误: {error.message}</div>;

  return (
    <div className="example-section">
      <h3>文档详情 (缓存5分钟)</h3>
      <h4>{data?.title}</h4>
      <p>状态: {data?.status}</p>
      <p>大小: {data?.size} bytes</p>
      <p>片段数: {data?.chunkCount}</p>
    </div>
  );
};

// ==================== 示例 4: 搜索查询 ====================

/**
 * 搜索示例
 */
export const SearchExample = () => {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // 防抖处理
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const { data, isLoading } = useKnowledgeSearch(debouncedQuery);

  return (
    <div className="example-section">
      <h3>知识库搜索 (缓存30秒)</h3>

      <input
        type="text"
        placeholder="输入搜索关键词..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {isLoading && <div>搜索中...</div>}

      {data?.results && (
        <ul>
          {data.results.map((result, index) => (
            <li key={index}>
              <strong>{result.title}</strong>
              <p>{result.snippet}</p>
              <small>相似度: {(result.score * 100).toFixed(1)}%</small>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

// ==================== 示例 5: Mutation 和缓存失效 ====================

/**
 * 文档管理示例
 */
export const DocumentManagementExample = () => {
  const [newDocTitle, setNewDocTitle] = useState('');
  const [selectedDoc, setSelectedDoc] = useState(null);

  const { data: documents, refetch } = useDocuments({ page: 1, pageSize: 10 });
  const createMutation = useCreateDocument();
  const updateMutation = useUpdateDocument();
  const deleteMutation = useDeleteDocument();

  const handleCreate = async () => {
    if (!newDocTitle.trim()) return;

    await createMutation.mutateAsync({
      title: newDocTitle,
      content: '',
    });

    setNewDocTitle('');
    // 列表会自动刷新（通过 onSuccess 回调）
  };

  const handleUpdate = async (id) => {
    await updateMutation.mutateAsync({
      id,
      data: { title: `更新后的标题 ${Date.now()}` },
    });
  };

  const handleDelete = async (id) => {
    if (confirm('确定删除此文档？')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  return (
    <div className="example-section">
      <h3>文档管理 (自动缓存失效)</h3>

      <div className="create-form">
        <input
          type="text"
          placeholder="新文档标题"
          value={newDocTitle}
          onChange={(e) => setNewDocTitle(e.target.value)}
        />
        <button onClick={handleCreate} disabled={createMutation.isPending}>
          {createMutation.isPending ? '创建中...' : '创建'}
        </button>
      </div>

      <ul>
        {documents?.items?.map((doc) => (
          <li key={doc.id} className="document-item">
            <span>{doc.title}</span>
            <div className="actions">
              <button onClick={() => handleUpdate(doc.id)}>更新</button>
              <button onClick={() => handleDelete(doc.id)}>删除</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

// ==================== 示例 6: 批量操作 ====================

/**
 * 批量操作示例
 */
export const BatchOperationsExample = () => {
  const [selectedIds, setSelectedIds] = useState([]);
  const { data: documents } = useDocuments({ page: 1, pageSize: 20 });
  const batchDeleteMutation = useBatchDeleteDocuments();

  const toggleSelection = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) return;
    if (!confirm(`确定删除选中的 ${selectedIds.length} 个文档？`)) return;

    await batchDeleteMutation.mutateAsync(selectedIds);
    setSelectedIds([]);
    // 所有相关缓存会自动失效
  };

  return (
    <div className="example-section">
      <h3>批量操作 (批量缓存失效)</h3>

      {selectedIds.length > 0 && (
        <div className="batch-toolbar">
          <span>已选择 {selectedIds.length} 项</span>
          <button
            onClick={handleBatchDelete}
            disabled={batchDeleteMutation.isPending}
          >
            {batchDeleteMutation.isPending ? '删除中...' : '批量删除'}
          </button>
        </div>
      )}

      <ul>
        {documents?.items?.map((doc) => (
          <li key={doc.id} className="document-item">
            <input
              type="checkbox"
              checked={selectedIds.includes(doc.id)}
              onChange={() => toggleSelection(doc.id)}
            />
            <span>{doc.title}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

// ==================== 示例 7: 缓存管理 ====================

/**
 * 缓存管理示例
 */
export const CacheManagerExample = () => {
  const {
    invalidateCache,
    invalidatePattern,
    clearAllCache,
    getCacheStats,
  } = useCacheManager();

  const [stats, setStats] = useState(getCacheStats());

  const refreshStats = () => {
    setStats(getCacheStats());
  };

  const handleInvalidateDocuments = () => {
    invalidatePattern('knowledge\\.documents');
    alert('文档缓存已清除');
    refreshStats();
  };

  const handleInvalidateAll = () => {
    invalidatePattern('knowledge\\.');
    alert('知识库相关缓存已清除');
    refreshStats();
  };

  const handleClearAll = () => {
    if (confirm('确定清除所有缓存？')) {
      clearAllCache();
      alert('所有缓存已清除');
      refreshStats();
    }
  };

  return (
    <div className="example-section">
      <h3>缓存管理</h3>

      <div className="cache-stats">
        <h4>缓存统计</h4>
        <pre>{JSON.stringify(stats, null, 2)}</pre>
        <button onClick={refreshStats}>刷新统计</button>
      </div>

      <div className="cache-actions">
        <h4>缓存操作</h4>
        <button onClick={handleInvalidateDocuments}>清除文档缓存</button>
        <button onClick={handleInvalidateAll}>清除知识库缓存</button>
        <button onClick={handleClearAll}>清除所有缓存</button>
      </div>
    </div>
  );
};

// ==================== 示例 8: 预加载 ====================

/**
 * 预加载示例
 */
export const PrefetchExample = () => {
  const { data: documents } = useDocuments({ page: 1, pageSize: 10 });
  const { prefetchDocument } = usePrefetch();
  const [currentDoc, setCurrentDoc] = useState(null);

  // 预加载文档详情
  const handleMouseEnter = useCallback(
    (docId) => {
      prefetchDocument(docId);
    },
    [prefetchDocument]
  );

  const handleClick = (doc) => {
    setCurrentDoc(doc);
  };

  return (
    <div className="example-section">
      <h3>预加载示例 (鼠标悬停预加载)</h3>

      <div className="document-list">
        <h4>文档列表</h4>
        <ul>
          {documents?.items?.map((doc) => (
            <li
              key={doc.id}
              onMouseEnter={() => handleMouseEnter(doc.id)}
              onClick={() => handleClick(doc)}
              className="prefetch-item"
            >
              {doc.title}
            </li>
          ))}
        </ul>
      </div>

      {currentDoc && (
        <DocumentDetailView documentId={currentDoc.id} />
      )}
    </div>
  );
};

// 文档详情视图（使用预加载的数据）
const DocumentDetailView = ({ documentId }) => {
  const { data, isLoading } = useDocument(documentId);

  return (
    <div className="document-detail">
      <h4>文档详情</h4>
      {isLoading ? (
        <div>加载中...(应该很快，因为已预加载)</div>
      ) : (
        <>
          <p>标题: {data?.title}</p>
          <p>状态: {data?.status}</p>
          <p>大小: {data?.size} bytes</p>
        </>
      )}
    </div>
  );
};

// ==================== 示例 9: 手动缓存操作 ====================

/**
 * 手动缓存操作示例
 */
export const ManualCacheExample = () => {
  const [cacheKey, setCacheKey] = useState('');
  const [cacheData, setCacheData] = useState('');

  const handleSetCache = () => {
    if (!cacheKey || !cacheData) return;

    requestCacheService.set(
      cacheKey,
      {},
      JSON.parse(cacheData),
      60 * 1000 // 1分钟TTL
    );

    alert('缓存已设置');
  };

  const handleGetCache = () => {
    if (!cacheKey) return;

    const data = requestCacheService.get(cacheKey, {});
    if (data) {
      setCacheData(JSON.stringify(data, null, 2));
    } else {
      alert('缓存未找到');
    }
  };

  const handleInvalidateCache = () => {
    if (!cacheKey) return;

    requestCacheService.invalidate(cacheKey, {});
    alert('缓存已清除');
  };

  return (
    <div className="example-section">
      <h3>手动缓存操作</h3>

      <div className="manual-cache-form">
        <input
          type="text"
          placeholder="缓存键"
          value={cacheKey}
          onChange={(e) => setCacheKey(e.target.value)}
        />

        <textarea
          placeholder="缓存数据 (JSON)"
          value={cacheData}
          onChange={(e) => setCacheData(e.target.value)}
          rows={5}
        />

        <div className="actions">
          <button onClick={handleSetCache}>设置缓存</button>
          <button onClick={handleGetCache}>获取缓存</button>
          <button onClick={handleInvalidateCache}>清除缓存</button>
        </div>
      </div>
    </div>
  );
};

// ==================== 主示例页面 ====================

const RequestCacheExamples = () => {
  const [activeExample, setActiveExample] = useState('bases');

  const examples = {
    bases: { title: '知识库列表', component: KnowledgeBasesExample },
    documents: { title: '文档列表', component: DocumentsExample },
    detail: { title: '文档详情', component: DocumentDetailExample },
    search: { title: '搜索', component: SearchExample },
    management: { title: '文档管理', component: DocumentManagementExample },
    batch: { title: '批量操作', component: BatchOperationsExample },
    cacheManager: { title: '缓存管理', component: CacheManagerExample },
    prefetch: { title: '预加载', component: PrefetchExample },
    manual: { title: '手动缓存', component: ManualCacheExample },
  };

  const ActiveComponent = examples[activeExample].component;

  return (
    <div style={{ padding: '24px' }}>
      <h1>请求缓存示例 (FE-003)</h1>

      <div style={{ marginBottom: '24px' }}>
        {Object.entries(examples).map(([key, { title }]) => (
          <button
            key={key}
            onClick={() => setActiveExample(key)}
            style={{
              marginRight: '8px',
              marginBottom: '8px',
              padding: '8px 16px',
              background: activeExample === key ? '#1890ff' : '#f0f0f0',
              color: activeExample === key ? '#fff' : '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            {title}
          </button>
        ))}
      </div>

      <div
        style={{
          padding: '24px',
          background: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <h2>{examples[activeExample].title}</h2>
        <ActiveComponent />
      </div>
    </div>
  );
};

export default RequestCacheExamples;
