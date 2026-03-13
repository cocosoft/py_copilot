/**
 * 文档管理页面
 *
 * 知识库文档管理主页面，整合所有新组件
 */

import React, { useEffect, useCallback, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiGrid, FiList, FiFilter, FiUpload, FiSearch, FiDownload, FiTrash2, FiFile, FiPlayCircle, FiLoader } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import BatchOperationToolbar from '../../../components/Knowledge/BatchOperationToolbar/BatchOperationToolbar';
import { VirtualListEnhanced } from '../../../components/UI';
import DocumentCard from '../../../components/Knowledge/DocumentCard';
import UploadButton from '../../../components/Knowledge/UploadButton';
import SmartSearch from '../../../components/Knowledge/SmartSearch/SmartSearch';
import { message } from '../../../components/UI/Message/Message';
import {
  listDocuments,
  uploadDocument,
  getDocument,
  deleteDocument,
  downloadDocument,
  getDocumentChunks,
  processDocument,
  batchProcessDocuments,
  getUnprocessedDocuments,
  getProcessingStatus,
  searchDocuments,
  getKnowledgeBases
} from '../../../utils/api/knowledgeApi';
import './styles.css';

/**
 * 视图模式
 */
const VIEW_MODES = {
  LIST: 'list',
  GRID: 'grid',
};

/**
 * 排序选项
 */
const SORT_OPTIONS = [
  { value: 'createdAt-desc', label: '最新上传' },
  { value: 'createdAt-asc', label: '最早上传' },
  { value: 'title-asc', label: '名称 A-Z' },
  { value: 'title-desc', label: '名称 Z-A' },
  { value: 'size-desc', label: '大小 大→小' },
  { value: 'size-asc', label: '大小 小→大' },
];

/**
 * 过滤器选项
 */
const FILTER_OPTIONS = [
  { value: 'all', label: '全部文档' },
  { value: 'vectorized', label: '已向量化' },
  { value: 'processing', label: '处理中' },
  { value: 'pending', label: '待处理' },
  { value: 'error', label: '处理失败' },
];

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 记忆化文档卡片组件
 * 用于优化虚拟列表性能，避免不必要的重渲染
 */
const MemoDocumentCard = React.memo(({
  document,
  selectedDocuments,
  onSelect,
  onClick,
  viewMode
}) => {
  const isSelected = selectedDocuments.some(id => String(id) === String(document.id));

  const handleSelect = useCallback(() => {
    onSelect(document.id);
  }, [onSelect, document.id]);

  const handleClick = useCallback(() => {
    onClick(document);
  }, [onClick, document]);

  return (
    <DocumentCard
      document={document}
      isSelected={isSelected}
      onSelect={handleSelect}
      onClick={handleClick}
      viewMode={viewMode}
    />
  );
});

/**
 * 文档管理页面
 */
const DocumentManagement = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  
  const {
    currentKnowledgeBase,
    documents,
    selectedDocuments,
    documentFilters,
    documentsLoading,
    documentsError,
    documentsTotal,
    documentsPage,
    documentsPageSize,
    setDocuments,
    setDocumentsLoading,
    setDocumentsError,
    toggleDocumentSelection,
    setSelectedDocuments,
    setDocumentsPage,
    setDocumentFilters,
    addSearchHistory,
    setCurrentKnowledgeBase,
  } = useKnowledgeStore();

  // 本地状态
  const [viewMode, setViewMode] = useState(VIEW_MODES.LIST);
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('createdAt-desc');
  const [filterStatus, setFilterStatus] = useState('all');

  // 文档详情状态
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [documentDetailLoading, setDocumentDetailLoading] = useState(false);
  const [documentChunks, setDocumentChunks] = useState([]);
  const [chunksLoading, setChunksLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('info'); // 'info', 'content', 'chunks'

  // 批量处理状态
  const [batchProcessing, setBatchProcessing] = useState(false);
  const [unprocessedCount, setUnprocessedCount] = useState(0);
  const [showBatchProcessModal, setShowBatchProcessModal] = useState(false);
  const [batchProcessResult, setBatchProcessResult] = useState(null);

  // 实时处理进度状态
  const [processingStatus, setProcessingStatus] = useState(null);
  const [showProgressPanel, setShowProgressPanel] = useState(false);

  /**
   * 获取向量状态
   */
  const getVectorizationStatus = (doc) => {
    if (doc.is_vectorized) return 'vectorized';
    const status = doc.document_metadata?.processing_status;
    if (status === 'failed') return 'error';
    if (status === 'processing' || status === 'queued') return 'processing';
    if (status === 'idle') return 'pending';
    return 'pending';
  };

  /**
   * 获取文档列表
   */
  const fetchDocuments = useCallback(async () => {
    console.log('[fetchDocuments] 开始获取文档列表, currentKnowledgeBase:', currentKnowledgeBase);
    if (!currentKnowledgeBase) {
      console.log('[fetchDocuments] currentKnowledgeBase 为 null，跳过获取');
      return;
    }

    setDocumentsLoading(true);
    setDocumentsError(null);

    try {
      let documents = [];
      let total = 0;

      console.log('[fetchDocuments] 知识库ID:', currentKnowledgeBase.id);
      console.log('[fetchDocuments] documentFilters:', documentFilters);

      // 检查是否有搜索关键词
      const searchQuery = documentFilters?.search?.trim();
      console.log('[fetchDocuments] searchQuery:', searchQuery);

      if (searchQuery) {
        console.log('[fetchDocuments] 使用搜索API');
        // 使用搜索API
        const searchResponse = await searchDocuments(
          searchQuery,
          documentsPageSize,
          currentKnowledgeBase.id,
          sortBy.split('-')[0] || 'relevance',
          sortBy.split('-')[1] || 'desc'
        );

        console.log('[fetchDocuments] 搜索API响应:', searchResponse);

        // 搜索API可能直接返回数组或包含results的对象
        const searchResults = Array.isArray(searchResponse) ? searchResponse : (searchResponse.results || []);
        console.log('[fetchDocuments] 搜索结果数组:', searchResults);

        // 转换搜索结果
        documents = searchResults.map(result => ({
          id: String(result.id || result.document_id),
          title: result.title,
          fileType: result.file_type || 'unknown',
          size: result.metadata?.file_size || 0,
          createdAt: result.created_at || result.metadata?.created_at,
          vectorizationStatus: result.is_vectorized ? 'vectorized' : (result.metadata?.processing_status || 'pending'),
          score: result.score,
        }));
        total = Array.isArray(searchResponse) ? searchResults.length : (searchResponse.total || documents.length);
      } else {
        // 调用普通列表API
        const skip = (documentsPage - 1) * documentsPageSize;
        const isVectorized = filterStatus === 'all' ? null : filterStatus === 'vectorized';

        console.log('[fetchDocuments] 调用 listDocuments:', { skip, limit: documentsPageSize, kbId: currentKnowledgeBase.id, isVectorized });

        const response = await listDocuments(
          skip,
          documentsPageSize,
          currentKnowledgeBase.id,
          isVectorized
        );

        console.log('[fetchDocuments] API响应:', response);

        // 转换后端数据为前端格式
        documents = (response.documents || []).map(doc => ({
          id: String(doc.id),
          title: doc.title,
          fileType: doc.file_type || 'unknown',
          size: doc.document_metadata?.file_size || 0,
          createdAt: doc.created_at,
          vectorizationStatus: getVectorizationStatus(doc),
        }));
        total = response.total || documents.length;
        console.log('[fetchDocuments] 处理后的文档数:', documents.length, '总数:', total);
      }

      // 客户端排序（仅当不是搜索模式时）
      if (!searchQuery) {
        documents = [...documents].sort((a, b) => {
          const [field, order] = sortBy.split('-');
          const multiplier = order === 'desc' ? -1 : 1;

          if (field === 'createdAt') {
            return multiplier * (new Date(a.createdAt) - new Date(b.createdAt));
          }
          if (field === 'title') {
            return multiplier * a.title.localeCompare(b.title);
          }
          if (field === 'size') {
            return multiplier * (a.size - b.size);
          }
          return 0;
        });

        // 过滤处理状态
        if (filterStatus !== 'all' && filterStatus !== 'vectorized') {
          documents = documents.filter(d => d.vectorizationStatus === filterStatus);
        }
      }

      console.log('[fetchDocuments] 成功获取文档:', documents.length, '个, 总数:', total, '页码:', documentsPage, '是否追加:', documentsPage > 1);
      // 使用追加模式当页码大于1时
      setDocuments(documents, total, documentsPage > 1);
    } catch (error) {
      console.error('[fetchDocuments] 获取文档列表失败:', error);
      setDocumentsError(error.message);
      message.error({ content: '获取文档列表失败：' + error.message });
    } finally {
      setDocumentsLoading(false);
    }
  }, [
    currentKnowledgeBase,
    documentsPage,
    documentsPageSize,
    documentFilters,
    sortBy,
    filterStatus,
    setDocuments,
    setDocumentsLoading,
    setDocumentsError,
  ]);

  // 初始加载和筛选变化时重新获取
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  /**
   * 获取未处理文档数量
   */
  const fetchUnprocessedCount = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      const response = await getUnprocessedDocuments(currentKnowledgeBase.id);
      if (response.success) {
        setUnprocessedCount(response.total_unprocessed);
      }
    } catch (error) {
      console.error('获取未处理文档数量失败:', error);
    }
  }, [currentKnowledgeBase]);

  // 初始加载时获取未处理文档数量
  useEffect(() => {
    fetchUnprocessedCount();
  }, [fetchUnprocessedCount]);

  // 组件加载时清除搜索关键词
  useEffect(() => {
    if (documentFilters?.search) {
      console.log('[DocumentManagement] 清除搜索关键词');
      setDocumentFilters({ search: '' });
    }
  }, []);

  /**
   * 加载知识库列表
   * 如果没有当前知识库，自动选择第一个
   */
  const loadKnowledgeBases = useCallback(async () => {
    // 如果已经有当前知识库，不需要重新加载
    if (currentKnowledgeBase) return;

    try {
      const response = await getKnowledgeBases(0, 10);
      const knowledgeBasesList = response.knowledge_bases || response;

      if (knowledgeBasesList.length > 0) {
        console.log('[DocumentManagement] 自动选择第一个知识库:', knowledgeBasesList[0].name);
        setCurrentKnowledgeBase(knowledgeBasesList[0]);
      } else {
        console.warn('[DocumentManagement] 没有可用的知识库');
      }
    } catch (error) {
      console.error('[DocumentManagement] 加载知识库列表失败:', error);
    }
  }, [currentKnowledgeBase, setCurrentKnowledgeBase]);

  // 组件加载时，如果没有当前知识库，加载知识库列表
  useEffect(() => {
    loadKnowledgeBases();
  }, [loadKnowledgeBases]);

  /**
   * 获取处理状态
   */
  const fetchProcessingStatus = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      const response = await getProcessingStatus(currentKnowledgeBase.id);
      if (response.success) {
        setProcessingStatus(response);

        // 如果有正在处理的文档，显示进度面板
        const hasProcessing = response.queue_status.processing_count > 0 ||
                             response.queue_status.queue_size > 0;
        if (hasProcessing) {
          setShowProgressPanel(true);
        }

        // 更新未处理数量
        setUnprocessedCount(response.statistics.unprocessed_documents);
      }
    } catch (error) {
      console.error('获取处理状态失败:', error);
    }
  }, [currentKnowledgeBase]);

  // 轮询处理状态
  useEffect(() => {
    if (!currentKnowledgeBase) return;

    // 立即获取一次
    fetchProcessingStatus();

    // 每3秒轮询一次
    const interval = setInterval(() => {
      fetchProcessingStatus();
    }, 3000);

    return () => clearInterval(interval);
  }, [currentKnowledgeBase, fetchProcessingStatus]);

  /**
   * 处理批量处理
   */
  const handleBatchProcess = useCallback(async () => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    if (unprocessedCount === 0) {
      message.info({ content: '没有需要处理的文档' });
      return;
    }

    setBatchProcessing(true);
    try {
      const response = await batchProcessDocuments(currentKnowledgeBase.id);
      setBatchProcessResult(response);
      setShowBatchProcessModal(true);

      if (response.success) {
        message.success({
          content: `批量处理已启动！共 ${response.total_documents} 个文档，成功加入队列 ${response.queued_documents} 个`
        });
        // 更新未处理数量
        setUnprocessedCount(response.total_documents - response.queued_documents);
        // 显示进度面板
        setShowProgressPanel(true);
        // 立即获取处理状态
        fetchProcessingStatus();
        // 刷新文档列表
        fetchDocuments();
      } else {
        message.error({ content: response.message || '批量处理失败' });
      }
    } catch (error) {
      message.error({ content: '批量处理失败：' + error.message });
    } finally {
      setBatchProcessing(false);
    }
  }, [currentKnowledgeBase, unprocessedCount, fetchDocuments, fetchProcessingStatus]);

  /**
   * 处理搜索
   */
  const handleSearch = useCallback((query) => {
    // 重置页码和列表
    setDocumentsPage(1);
    setDocuments([], 0);
    setDocumentFilters({ search: query });
    if (query) {
      addSearchHistory(query);
    }
  }, [setDocumentFilters, addSearchHistory, setDocumentsPage, setDocuments]);

  /**
   * 处理文件上传
   */
  const handleUpload = useCallback(async (files) => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    try {
      let successCount = 0;
      let errorCount = 0;

      for (const file of files) {
        try {
          await uploadDocument(file, currentKnowledgeBase.id);
          successCount++;
        } catch (error) {
          console.error('上传文件失败:', file.name, error);
          errorCount++;
        }
      }

      if (successCount > 0) {
        message.success({ content: `成功上传 ${successCount} 个文件` });
        fetchDocuments();
      }
      if (errorCount > 0) {
        message.error({ content: `${errorCount} 个文件上传失败` });
      }
    } catch (error) {
      message.error({ content: '上传失败：' + error.message });
    }
  }, [currentKnowledgeBase, fetchDocuments]);

  /**
   * 获取文档详情
   */
  const fetchDocumentDetail = useCallback(async (docId) => {
    if (!docId) return;

    setDocumentDetailLoading(true);
    try {
      const doc = await getDocument(docId);
      setSelectedDocument(doc);
    } catch (error) {
      message.error({ content: '获取文档详情失败：' + error.message });
    } finally {
      setDocumentDetailLoading(false);
    }
  }, []);

  /**
   * 获取文档片段
   */
  const fetchDocumentChunks = useCallback(async (docId) => {
    if (!docId) {
      console.log('[fetchDocumentChunks] docId 为空，跳过获取');
      return;
    }

    console.log('[fetchDocumentChunks] 开始获取向量片段, docId:', docId);
    setChunksLoading(true);
    try {
      const response = await getDocumentChunks(docId, 0, 50);
      console.log('[fetchDocumentChunks] API 原始响应:', response);
      // API 直接返回数组，不是 {chunks: [...]} 格式
      const chunks = Array.isArray(response) ? response : (response.chunks || []);
      console.log(`[fetchDocumentChunks] 处理后的向量片段数: ${chunks.length}`);
      console.log('[fetchDocumentChunks] 第一个片段:', chunks[0]);
      setDocumentChunks(chunks);
    } catch (error) {
      console.error('[fetchDocumentChunks] 获取文档片段失败:', error);
      setDocumentChunks([]);
    } finally {
      setChunksLoading(false);
    }
  }, []);

  // 当 documentId 变化时，获取文档详情
  useEffect(() => {
    console.log('[DocumentManagement] documentId 变化:', documentId);
    if (documentId) {
      console.log('[DocumentManagement] 获取文档详情和向量片段, ID:', documentId);
      fetchDocumentDetail(documentId);
      fetchDocumentChunks(documentId);
    } else {
      console.log('[DocumentManagement] 清空文档详情');
      setSelectedDocument(null);
      setDocumentChunks([]);
    }
  }, [documentId, fetchDocumentDetail, fetchDocumentChunks]);

  /**
   * 处理文档点击
   */
  const handleDocumentClick = useCallback((document) => {
    // 使用uuid进行导航，如果没有uuid则使用id
    const docId = document.uuid || document.id;
    navigate(`/knowledge/documents/${docId}`);
  }, [navigate]);

  /**
   * 处理下载文档
   */
  const handleDownloadDocument = useCallback(async () => {
    if (!selectedDocument) return;

    try {
      // 使用uuid或id下载文档
      const docId = selectedDocument.uuid || selectedDocument.id;
      const blob = await downloadDocument(docId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = selectedDocument.title;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      message.success({ content: '文档下载成功' });
    } catch (error) {
      message.error({ content: '下载失败：' + error.message });
    }
  }, [selectedDocument]);

  /**
   * 处理删除文档
   */
  const handleDeleteDocument = useCallback(async () => {
    if (!selectedDocument) return;

    if (!window.confirm(`确定要删除文档 "${selectedDocument.title}" 吗？`)) {
      return;
    }

    try {
      // 使用uuid或id删除文档
      const docId = selectedDocument.uuid || selectedDocument.id;
      await deleteDocument(docId);
      message.success({ content: '文档已删除' });
      navigate('/knowledge/documents');
      fetchDocuments();
    } catch (error) {
      message.error({ content: '删除失败：' + error.message });
    }
  }, [selectedDocument, navigate, fetchDocuments]);

  /**
   * 处理向量化文档
   */
  const handleVectorizeDocument = useCallback(async () => {
    if (!selectedDocument) return;

    try {
      // 使用uuid或id处理文档
      const docId = selectedDocument.uuid || selectedDocument.id;
      await processDocument(docId);
      message.success({ content: '文档已向量化' });
      fetchDocumentDetail(docId);
      fetchDocuments();
    } catch (error) {
      message.error({ content: '向量化失败：' + error.message });
    }
  }, [selectedDocument, fetchDocumentDetail, fetchDocuments]);

  /**
   * 渲染文档项 - 使用稳定引用避免不必要的重渲染
   */
  const renderDocument = useCallback((doc, index) => (
    <MemoDocumentCard
      document={doc}
      selectedDocuments={selectedDocuments}
      onSelect={toggleDocumentSelection}
      onClick={handleDocumentClick}
      viewMode={viewMode}
    />
  ), [selectedDocuments, toggleDocumentSelection, handleDocumentClick, viewMode]);

  /**
   * 加载更多
   */
  const handleLoadMore = useCallback(() => {
    if (!documentsLoading && documents.length < documentsTotal) {
      setDocumentsPage(documentsPage + 1);
    }
  }, [documentsLoading, documents.length, documentsTotal, documentsPage, setDocumentsPage]);

  /**
   * 切换视图模式
   */
  const toggleViewMode = () => {
    setViewMode(prev => prev === VIEW_MODES.LIST ? VIEW_MODES.GRID : VIEW_MODES.LIST);
  };

  /**
   * 处理排序变更
   */
  const handleSortChange = (e) => {
    setSortBy(e.target.value);
    // 重置页码和列表
    setDocumentsPage(1);
    setDocuments([], 0);
  };

  /**
   * 处理过滤变更
   */
  const handleFilterChange = (status) => {
    setFilterStatus(status);
    setShowFilters(false);
    // 重置页码和列表
    setDocumentsPage(1);
    setDocuments([], 0);
  };

  if (documentsError) {
    return (
      <div className="document-management-error">
        <div className="error-icon">⚠️</div>
        <h3>加载失败</h3>
        <p>{documentsError}</p>
        <button className="retry-button" onClick={fetchDocuments}>
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="document-management">
      {/* 顶部工具栏 */}
      <div className="document-management-header">
        <div className="header-left">
          <UploadButton onUpload={handleUpload} />
          
          {/* 批量处理按钮 */}
          {unprocessedCount > 0 && (
            <button
              className="batch-process-button"
              onClick={handleBatchProcess}
              disabled={batchProcessing}
              title={`批量处理 ${unprocessedCount} 个未处理文档`}
            >
              {batchProcessing ? (
                <>
                  <FiLoader size={16} className="spinning" />
                  <span>处理中...</span>
                </>
              ) : (
                <>
                  <FiPlayCircle size={16} />
                  <span>批量处理 ({unprocessedCount})</span>
                </>
              )}
            </button>
          )}
        </div>
        
        <div className="header-right">
          {/* 搜索框 */}
          <div className="header-search">
            <SmartSearch 
              onSearch={handleSearch}
              placeholder="搜索文档..."
            />
          </div>
          
          {/* 过滤器 */}
          <div className="header-filters">
            <button 
              className={`filter-toggle ${showFilters ? 'active' : ''}`}
              onClick={() => setShowFilters(!showFilters)}
            >
              <FiFilter size={16} />
              <span>筛选</span>
            </button>
            
            {showFilters && (
              <div className="filter-dropdown">
                {FILTER_OPTIONS.map(option => (
                  <button
                    key={option.value}
                    className={`filter-option ${filterStatus === option.value ? 'active' : ''}`}
                    onClick={() => handleFilterChange(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {/* 排序选择 */}
          <div className="header-sort">
            <select value={sortBy} onChange={handleSortChange}>
              {SORT_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* 视图切换 */}
          <div className="header-view-toggle">
            <button 
              className={viewMode === VIEW_MODES.LIST ? 'active' : ''}
              onClick={() => setViewMode(VIEW_MODES.LIST)}
              title="列表视图"
            >
              <FiList size={18} />
            </button>
            <button 
              className={viewMode === VIEW_MODES.GRID ? 'active' : ''}
              onClick={() => setViewMode(VIEW_MODES.GRID)}
              title="网格视图"
            >
              <FiGrid size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* 批量操作工具栏 */}
      {selectedDocuments.length > 0 && <BatchOperationToolbar />}

      {/* 实时处理进度面板 */}
      {showProgressPanel && processingStatus && (
        <div className="processing-progress-panel">
          <div className="progress-panel-header">
            <div className="progress-title">
              <FiLoader size={16} className="spinning" />
              <span>文档处理中...</span>
            </div>
            <button
              className="close-progress-panel"
              onClick={() => setShowProgressPanel(false)}
              title="隐藏进度面板"
            >
              ×
            </button>
          </div>
          <div className="progress-panel-content">
            {/* 总体进度 */}
            <div className="progress-overview">
              <div className="progress-stat">
                <span className="stat-label">总文档:</span>
                <span className="stat-value">{processingStatus.statistics?.total_documents || 0}</span>
              </div>
              <div className="progress-stat">
                <span className="stat-label">已完成:</span>
                <span className="stat-value success">{processingStatus.statistics?.vectorized_documents || 0}</span>
              </div>
              <div className="progress-stat">
                <span className="stat-label">待处理:</span>
                <span className="stat-value warning">{processingStatus.statistics?.unprocessed_documents || 0}</span>
              </div>
              <div className="progress-stat">
                <span className="stat-label">完成率:</span>
                <span className="stat-value info">{processingStatus.statistics?.vectorization_rate || 0}%</span>
              </div>
            </div>

            {/* 队列状态 */}
            <div className="queue-status">
              <div className="queue-item">
                <span className="queue-label">队列中:</span>
                <span className="queue-value">{processingStatus.queue_status?.queue_size || 0}</span>
              </div>
              <div className="queue-item">
                <span className="queue-label">处理中:</span>
                <span className="queue-value processing">{processingStatus.queue_status?.processing_count || 0}</span>
              </div>
              <div className="queue-item">
                <span className="queue-label">已完成:</span>
                <span className="queue-value success">{processingStatus.queue_status?.completed_count || 0}</span>
              </div>
              <div className="queue-item">
                <span className="queue-label">失败:</span>
                <span className="queue-value error">{processingStatus.queue_status?.failed_count || 0}</span>
              </div>
            </div>

            {/* 正在处理的文档 */}
            {processingStatus.processing_documents && processingStatus.processing_documents.length > 0 && (
              <div className="processing-documents">
                <div className="processing-documents-title">正在处理:</div>
                {processingStatus.processing_documents.map((doc) => (
                  <div key={doc.document_id} className="processing-document-item">
                    <FiFile size={14} />
                    <span className="document-name" title={doc.document_name}>
                      {doc.document_name}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* 进度条 */}
            <div className="progress-bar-container">
              <div
                className="progress-bar"
                style={{
                  width: `${processingStatus.statistics?.vectorization_rate || 0}%`
                }}
              />
              <span className="progress-text">
                {processingStatus.statistics?.vectorization_rate || 0}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 统计信息 */}
      <div className="document-management-stats">
        <span>共 {documentsTotal} 个文档</span>
        {selectedDocuments.length > 0 && (
          <span className="selected-count">已选择 {selectedDocuments.length} 个</span>
        )}
        {processingStatus?.statistics?.vectorization_rate !== undefined && (
          <span className="vectorization-rate">
            向量化: {processingStatus.statistics.vectorization_rate}%
          </span>
        )}
      </div>

      {/* 文档列表 */}
      <div className={`document-list-container ${viewMode === VIEW_MODES.GRID ? 'grid-view' : 'list-view'}`}>
        <VirtualListEnhanced
          items={documents}
          renderItem={renderDocument}
          estimateSize={viewMode === VIEW_MODES.GRID ? 200 : 80}
          overscan={10}
          onEndReached={handleLoadMore}
          hasMore={documents.length < documentsTotal}
          loading={documentsLoading}
          emptyText={
            <div className="empty-state">
              <div className="empty-icon">📁</div>
              <h3>暂无文档</h3>
              <p>点击上方"上传文档"按钮添加文档</p>
            </div>
          }
        />
      </div>

      {/* 文档详情面板 */}
      {documentId && (
        <div className="document-detail-panel">
          <div className="document-detail-header">
            <h3>文档详情</h3>
            <button
              className="close-detail"
              onClick={() => navigate('/knowledge/documents')}
            >
              ×
            </button>
          </div>
          <div className="document-detail-content">
            {documentDetailLoading ? (
              <div className="detail-loading">加载中...</div>
            ) : selectedDocument ? (
              <>
                {/* 文档基本信息 */}
                <div className="detail-section">
                  <h4 className="detail-title">{selectedDocument.title}</h4>
                  <div className="detail-meta">
                    <span className="detail-meta-item">
                      <FiFile size={14} />
                      类型: {selectedDocument.file_type?.toUpperCase() || '未知'}
                    </span>
                    <span className="detail-meta-item">
                      大小: {formatFileSize(selectedDocument.document_metadata?.file_size || 0)}
                    </span>
                    <span className="detail-meta-item">
                      创建时间: {new Date(selectedDocument.created_at).toLocaleString('zh-CN')}
                    </span>
                    <span className={`detail-meta-item status-${selectedDocument.is_vectorized ? 'vectorized' : 'pending'}`}>
                      状态: {selectedDocument.is_vectorized ? '已向量化' : '未向量化'}
                    </span>
                  </div>
                </div>

                {/* 标签页导航 */}
                <div className="detail-tabs">
                  <button
                    className={`detail-tab ${activeTab === 'info' ? 'active' : ''}`}
                    onClick={() => setActiveTab('info')}
                  >
                    基本信息
                  </button>
                  {selectedDocument.is_vectorized && (
                    <button
                      className={`detail-tab ${activeTab === 'chunks' ? 'active' : ''}`}
                      onClick={() => setActiveTab('chunks')}
                    >
                      向量片段 ({documentChunks.length})
                    </button>
                  )}
                </div>

                {/* 标签页内容 */}
                <div className="detail-tab-content">
                  {activeTab === 'info' && (
                    <div className="info-content">
                      <div className="info-item">
                        <label>文档 ID:</label>
                        <span>{selectedDocument.id}</span>
                      </div>
                      <div className="info-item">
                        <label>知识库 ID:</label>
                        <span>{selectedDocument.knowledge_base_id}</span>
                      </div>
                      {selectedDocument.document_metadata?.processing_status && (
                        <div className="info-item">
                          <label>处理状态:</label>
                          <span>{selectedDocument.document_metadata.processing_status}</span>
                        </div>
                      )}
                      {selectedDocument.document_metadata?.chunk_count !== undefined && (
                        <div className="info-item">
                          <label>片段数量:</label>
                          <span>{selectedDocument.document_metadata.chunk_count}</span>
                        </div>
                      )}

                      {/* 操作按钮 */}
                      <div className="detail-actions">
                        <button
                          className="action-btn primary"
                          onClick={handleDownloadDocument}
                        >
                          <FiDownload size={16} />
                          下载文档
                        </button>
                        {!selectedDocument.is_vectorized && (
                          <button
                            className="action-btn secondary"
                            onClick={handleVectorizeDocument}
                          >
                            向量化
                          </button>
                        )}
                        <button
                          className="action-btn danger"
                          onClick={handleDeleteDocument}
                        >
                          <FiTrash2 size={16} />
                          删除文档
                        </button>
                      </div>
                    </div>
                  )}

                  {activeTab === 'chunks' && (
                    <div className="chunks-content">
                      {chunksLoading ? (
                        <div className="detail-loading">加载片段中...</div>
                      ) : documentChunks.length > 0 ? (
                        <div className="chunks-list">
                          {documentChunks.map((chunk, index) => (
                            <div key={chunk.id || index} className="chunk-item">
                              <div className="chunk-header">
                                <span className="chunk-index">
                                  片段 {chunk.chunk_index !== undefined ? chunk.chunk_index + 1 : index + 1}
                                  {chunk.total_chunks ? ` / ${chunk.total_chunks}` : ''}
                                </span>
                                {chunk.score !== undefined && (
                                  <span className="chunk-score">
                                    相似度: {(chunk.score * 100).toFixed(1)}%
                                  </span>
                                )}
                              </div>
                              <div className="chunk-text">{chunk.content || chunk.text || '无内容'}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty-chunks">
                          <p>暂无向量片段</p>
                          {selectedDocument.is_vectorized && (
                            <p className="empty-hint">文档已向量化，但未能获取到片段数据</p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="detail-error">无法加载文档详情</div>
            )}
          </div>
        </div>
      )}

      {/* 批量处理结果弹窗 */}
      {showBatchProcessModal && batchProcessResult && (
        <div className="batch-process-modal-overlay" onClick={() => setShowBatchProcessModal(false)}>
          <div className="batch-process-modal" onClick={(e) => e.stopPropagation()}>
            <div className="batch-process-modal-header">
              <h3>批量处理结果</h3>
              <button className="close-button" onClick={() => setShowBatchProcessModal(false)}>×</button>
            </div>
            <div className="batch-process-modal-content">
              <div className="result-summary">
                <div className="result-item">
                  <span className="result-label">知识库:</span>
                  <span className="result-value">{batchProcessResult.knowledge_base_name}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">总文档数:</span>
                  <span className="result-value">{batchProcessResult.total_documents}</span>
                </div>
                <div className="result-item success">
                  <span className="result-label">成功加入队列:</span>
                  <span className="result-value">{batchProcessResult.queued_documents}</span>
                </div>
                {batchProcessResult.skipped_documents > 0 && (
                  <div className="result-item warning">
                    <span className="result-label">跳过:</span>
                    <span className="result-value">{batchProcessResult.skipped_documents}</span>
                  </div>
                )}
                {batchProcessResult.failed_documents > 0 && (
                  <div className="result-item error">
                    <span className="result-label">失败:</span>
                    <span className="result-value">{batchProcessResult.failed_documents}</span>
                  </div>
                )}
              </div>
              <div className="result-message">
                <p>{batchProcessResult.message}</p>
              </div>
              <div className="queue-status">
                <h4>队列状态</h4>
                <div className="status-item">
                  <span>处理中:</span>
                  <span>{batchProcessResult.queue_status?.processing_count || 0}</span>
                </div>
                <div className="status-item">
                  <span>队列中:</span>
                  <span>{batchProcessResult.queue_status?.queue_size || 0}</span>
                </div>
              </div>
            </div>
            <div className="batch-process-modal-footer">
              <button className="confirm-button" onClick={() => setShowBatchProcessModal(false)}>
                确定
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentManagement;
