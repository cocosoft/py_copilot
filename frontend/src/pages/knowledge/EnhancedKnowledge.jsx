/**
 * 增强版知识库页面
 * 
 * 集成了以下优化功能：
 * - 虚拟列表 (FE-001): 提升大数据量文档列表性能
 * - 状态管理 (FE-002): 使用 knowledgeStore 统一管理状态
 * - 请求缓存 (FE-003): 使用 React Query 缓存请求
 * 
 * @module EnhancedKnowledge
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';

// 导入原知识库页面组件
import Knowledge from '../Knowledge';

// 导入虚拟列表组件
import EnhancedVirtualList from '../../components/VirtualList';

// 导入状态管理
import useKnowledge from '../../hooks/useKnowledge';

// 导入 API
import { listDocuments, getKnowledgeBases } from '../../utils/api/knowledgeApi';

// 导入样式
import './EnhancedKnowledge.css';

/**
 * 文档卡片组件
 * 
 * @param {Object} props - 组件属性
 * @param {Object} props.doc - 文档数据
 * @param {number} props.index - 文档索引
 * @param {Function} props.onSelect - 选择回调
 * @param {Function} props.onDelete - 删除回调
 * @param {boolean} props.isSelected - 是否选中
 */
const DocumentCard = ({ doc, index, onSelect, onDelete, isSelected }) => {
  const { t } = useTranslation(['knowledge', 'common']);

  // 获取文档状态（支持多种字段格式）
  const getDocStatus = (doc) => {
    // 优先检查 vectorization_status
    if (doc.vectorization_status) {
      return doc.vectorization_status;
    }
    // 检查 processing_status（根级别或 document_metadata 中）
    const processingStatus = doc.processing_status || doc.document_metadata?.processing_status;
    if (processingStatus && processingStatus !== 'pending') {
      return processingStatus;
    }
    // 检查是否已向量化
    if (doc.is_vectorized === 1 || doc.is_vectorized === true) {
      return 'vectorized';
    }
    return 'pending';
  };

  const docStatus = getDocStatus(doc);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'vectorized':
        return '✓';
      case 'processing':
        return '⏳';
      case 'failed':
        return '✗';
      default:
        return '○';
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'vectorized':
        return 'status-vectorized';
      case 'processing':
        return 'status-processing';
      case 'failed':
        return 'status-failed';
      default:
        return 'status-pending';
    }
  };

  return (
    <div
      className={`document-card ${isSelected ? 'selected' : ''} ${getStatusClass(docStatus)}`}
      onClick={() => onSelect(doc)}
      style={{ height: '100%' }}
    >
      <div className="document-card-header">
        <span className="document-index">#{index + 1}</span>
        <span className={`status-badge ${getStatusClass(docStatus)}`}>
          {getStatusIcon(docStatus)}
          {t(`knowledge:status.${docStatus}`)}
        </span>
      </div>
      
      <div className="document-card-content">
        <h4 className="document-title" title={doc.title}>
          {doc.title || t('knowledge:untitled')}
        </h4>
        <p className="document-meta">
          <span>{doc.file_type?.toUpperCase()}</span>
          <span>•</span>
          <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
          <span>•</span>
          <span>{new Date(doc.created_at).toLocaleDateString()}</span>
        </p>
      </div>
      
      <div className="document-card-actions">
        <button 
          className="btn-icon"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(doc);
          }}
          title={t('common:delete')}
        >
          🗑️
        </button>
      </div>
    </div>
  );
};

/**
 * 增强版知识库页面组件
 * 
 * @component
 */
const EnhancedKnowledge = () => {
  const { t } = useTranslation(['knowledge', 'common']);
  
  // 使用状态管理
  const {
    currentKnowledgeBase,
    setCurrentKnowledgeBase,
    viewMode,
    setViewMode,
    filters,
    setFilters,
    selectedDocuments,
    setSelectedDocuments,
    toggleDocumentSelection,
    clearSelection
  } = useKnowledge();

  // 兼容旧代码的别名
  const selectedKnowledgeBase = currentKnowledgeBase;
  const setSelectedKnowledgeBase = setCurrentKnowledgeBase;
  
  // 本地状态
  const [searchQuery, setSearchQuery] = useState('');
  const [showVirtualList, setShowVirtualList] = useState(true);
  
  // 使用 React Query 获取知识库列表（带缓存）
  const { 
    data: knowledgeBasesData, 
    isLoading: isLoadingKBs 
  } = useQuery({
    queryKey: ['knowledgeBases'],
    queryFn: () => getKnowledgeBases(0, 50),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
  
  // 支持两种数据结构：response.knowledge_bases 或 response.data
  const knowledgeBases = knowledgeBasesData?.knowledge_bases || knowledgeBasesData?.data || knowledgeBasesData || [];
  
  // 使用 React Query 获取文档列表（带缓存）
  const {
    data: documentsData,
    isLoading: isLoadingDocs,
    error: docsError,
    refetch: refetchDocs
  } = useQuery({
    queryKey: ['documents', selectedKnowledgeBase, filters],
    queryFn: () => listDocuments(0, 1000, selectedKnowledgeBase, null),
    enabled: !!selectedKnowledgeBase,
    staleTime: 2 * 60 * 1000, // 2分钟缓存
  });

  // 支持多种数据结构
  const documents = documentsData?.documents || documentsData?.data || documentsData || [];
  
  // 过滤文档
  const filteredDocuments = React.useMemo(() => {
    if (!searchQuery) return documents;
    return documents.filter(doc => 
      doc.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.content?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [documents, searchQuery]);
  
  // 处理文档选择
  const handleSelectDocument = useCallback((doc) => {
    toggleDocumentSelection(doc.id);
  }, [toggleDocumentSelection]);
  
  // 处理文档删除
  const handleDeleteDocument = useCallback((doc) => {
    if (window.confirm(t('knowledge:confirmDeleteDocument', { title: doc.title }))) {
      // 调用删除 API
      console.log('删除文档:', doc.id);
    }
  }, [t]);

  // 批量操作进度状态
  const [batchProgress, setBatchProgress] = useState({
    isProcessing: false,
    current: 0,
    total: 0,
    operation: null // 'vectorize' | 'delete'
  });

  // 处理批量向量化
  const handleBatchVectorize = useCallback(async () => {
    if (selectedDocuments.length === 0) return;

    if (!window.confirm(t('knowledge:confirmBatchVectorize', { count: selectedDocuments.length }))) {
      return;
    }

    // 设置进度状态
    setBatchProgress({
      isProcessing: true,
      current: 0,
      total: selectedDocuments.length,
      operation: 'vectorize'
    });

    // 导入 API 函数
    const { vectorizeDocument } = await import('../../utils/api/knowledgeApi');

    let successCount = 0;
    let failCount = 0;
    const failedDocs = [];

    // 依次向量化选中的文档（顺序执行以显示进度）
    for (let i = 0; i < selectedDocuments.length; i++) {
      const docId = selectedDocuments[i];
      setBatchProgress(prev => ({ ...prev, current: i }));

      try {
        await vectorizeDocument(docId);
        successCount++;
      } catch (error) {
        console.error(`文档 ${docId} 向量化失败:`, error);
        failCount++;
        failedDocs.push(docId);
      }
    }

    setBatchProgress(prev => ({ ...prev, current: selectedDocuments.length }));

    // 显示处理结果
    if (failCount === 0) {
      alert(t('knowledge:batchVectorizeSuccess', { count: successCount }));
    } else if (successCount === 0) {
      alert(t('knowledge:batchVectorizeFailed', { count: failCount }));
    } else {
      alert(t('knowledge:batchVectorizePartial', { success: successCount, failed: failCount }));
    }

    clearSelection();
    refetchDocs();
    setBatchProgress({ isProcessing: false, current: 0, total: 0, operation: null });
  }, [selectedDocuments, t, clearSelection, refetchDocs]);

  // 处理批量删除
  const handleBatchDelete = useCallback(async () => {
    if (selectedDocuments.length === 0) return;

    if (!window.confirm(t('knowledge:confirmBatchDelete', { count: selectedDocuments.length }))) {
      return;
    }

    // 设置进度状态
    setBatchProgress({
      isProcessing: true,
      current: 0,
      total: selectedDocuments.length,
      operation: 'delete'
    });

    // 导入 API 函数
    const { deleteDocument } = await import('../../utils/api/knowledgeApi');

    let successCount = 0;
    let failCount = 0;

    // 依次删除选中的文档（顺序执行以显示进度）
    for (let i = 0; i < selectedDocuments.length; i++) {
      const docId = selectedDocuments[i];
      setBatchProgress(prev => ({ ...prev, current: i }));

      try {
        await deleteDocument(docId);
        successCount++;
      } catch (error) {
        console.error(`文档 ${docId} 删除失败:`, error);
        failCount++;
      }
    }

    setBatchProgress(prev => ({ ...prev, current: selectedDocuments.length }));

    // 显示处理结果
    if (failCount === 0) {
      alert(t('knowledge:batchDeleteSuccess', { count: successCount }));
    } else if (successCount === 0) {
      alert(t('knowledge:batchDeleteFailed', { count: failCount }));
    } else {
      alert(t('knowledge:batchDeletePartial', { success: successCount, failed: failCount }));
    }

    clearSelection();
    refetchDocs();
    setBatchProgress({ isProcessing: false, current: 0, total: 0, operation: null });
  }, [selectedDocuments, t, clearSelection, refetchDocs]);

  // 处理知识库切换
  const handleKnowledgeBaseChange = useCallback((kbId) => {
    setSelectedKnowledgeBase(kbId);
    clearSelection();
  }, [setSelectedKnowledgeBase, clearSelection]);
  
  // 渲染文档项（用于虚拟列表）
  const renderDocumentItem = useCallback((doc, index) => (
    <DocumentCard
      key={doc.id || index}
      doc={doc}
      index={index}
      onSelect={handleSelectDocument}
      onDelete={handleDeleteDocument}
      isSelected={selectedDocuments.includes(doc.id)}
    />
  ), [handleSelectDocument, handleDeleteDocument, selectedDocuments]);
  
  // 统计信息
  const stats = React.useMemo(() => {
    return {
      total: documents.length,
      vectorized: documents.filter(d => {
        // 支持多种字段格式：is_vectorized (1/0) 或 vectorization_status ('vectorized')
        return d.is_vectorized === 1 || d.is_vectorized === true || d.vectorization_status === 'vectorized';
      }).length,
      processing: documents.filter(d => {
        const status = d.vectorization_status || d.processing_status || d.document_metadata?.processing_status;
        return status === 'processing';
      }).length,
      failed: documents.filter(d => {
        const status = d.vectorization_status || d.processing_status || d.document_metadata?.processing_status;
        return status === 'failed';
      }).length,
      pending: documents.filter(d => {
        const isVectorized = d.is_vectorized === 1 || d.is_vectorized === true || d.vectorization_status === 'vectorized';
        const status = d.vectorization_status || d.processing_status || d.document_metadata?.processing_status;
        const isProcessing = status === 'processing';
        const isFailed = status === 'failed';
        return !isVectorized && !isProcessing && !isFailed;
      }).length,
    };
  }, [documents]);
  
  return (
    <div className="enhanced-knowledge-page">
      {/* 页面头部 */}
      <div className="page-header">
        <h1>{t('knowledge:title')}</h1>
        
        {/* 知识库选择器 */}
        <div className="knowledge-base-selector">
          <select 
            value={selectedKnowledgeBase || ''}
            onChange={(e) => handleKnowledgeBaseChange(e.target.value)}
            disabled={isLoadingKBs}
          >
            <option value="">{t('knowledge:selectKnowledgeBase')}</option>
            {knowledgeBases.map(kb => (
              <option key={kb.id} value={kb.id}>{kb.name}</option>
            ))}
          </select>
          
          <button className="btn-primary">
            + {t('knowledge:createKnowledgeBase')}
          </button>
        </div>
      </div>
      
      {/* 统计信息栏 */}
      <div className="stats-bar">
        <div className="stat-item">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">{t('knowledge:totalDocuments')}</span>
        </div>
        <div className="stat-item vectorized">
          <span className="stat-value">{stats.vectorized}</span>
          <span className="stat-label">{t('knowledge:vectorized')}</span>
        </div>
        <div className="stat-item processing">
          <span className="stat-value">{stats.processing}</span>
          <span className="stat-label">{t('knowledge:processing')}</span>
        </div>
        <div className="stat-item failed">
          <span className="stat-value">{stats.failed}</span>
          <span className="stat-label">{t('knowledge:failed')}</span>
        </div>
        <div className="stat-item pending">
          <span className="stat-value">{stats.pending}</span>
          <span className="stat-label">{t('knowledge:pending')}</span>
        </div>
      </div>
      
      {/* 工具栏 */}
      <div className="toolbar">
        <div className="search-box">
          <input
            type="text"
            placeholder={t('knowledge:searchDocuments')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className="btn-icon">🔍</button>
        </div>
        
        <div className="toolbar-actions">
          <label className="toggle-virtual-list">
            <input
              type="checkbox"
              checked={showVirtualList}
              onChange={(e) => setShowVirtualList(e.target.checked)}
            />
            {t('knowledge:useVirtualList')}
          </label>
          
          <button className="btn-secondary" onClick={() => refetchDocs()}>
            🔄 {t('common:refresh')}
          </button>
          
          <button className="btn-primary">
            + {t('knowledge:uploadDocument')}
          </button>
        </div>
      </div>
      
      {/* 批量操作栏 */}
      {selectedDocuments.length > 0 && !batchProgress.isProcessing && (
        <div className="batch-actions-bar">
          <span>{t('knowledge:selectedCount', { count: selectedDocuments.length })}</span>
          <button className="btn-secondary" onClick={handleBatchVectorize}>
            {t('knowledge:batchVectorize')}
          </button>
          <button className="btn-danger" onClick={handleBatchDelete}>
            {t('knowledge:batchDelete')}
          </button>
          <button className="btn-text" onClick={clearSelection}>
            {t('common:clearSelection')}
          </button>
        </div>
      )}

      {/* 批量操作进度显示 */}
      {batchProgress.isProcessing && (
        <div className="batch-progress-bar">
          <div className="progress-info">
            <span className="progress-label">
              {batchProgress.operation === 'vectorize'
                ? t('knowledge:vectorizingProgress')
                : t('knowledge:deletingProgress')}
            </span>
            <span className="progress-count">
              {batchProgress.current} / {batchProgress.total}
            </span>
          </div>
          <div className="progress-bar-container">
            <div
              className="progress-bar-fill"
              style={{
                width: `${batchProgress.total > 0 ? (batchProgress.current / batchProgress.total) * 100 : 0}%`
              }}
            />
          </div>
          <span className="progress-percentage">
            {batchProgress.total > 0
              ? Math.round((batchProgress.current / batchProgress.total) * 100)
              : 0}%
          </span>
        </div>
      )}
      
      {/* 文档列表区域 */}
      <div className="documents-section">
        {isLoadingDocs ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>{t('common:loading')}</p>
          </div>
        ) : docsError ? (
          <div className="error-state">
            <p>{t('knowledge:loadError')}</p>
            <button onClick={() => refetchDocs()}>{t('common:retry')}</button>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="empty-state">
            <p>{t('knowledge:noDocuments')}</p>
            <button className="btn-primary">
              + {t('knowledge:uploadDocument')}
            </button>
          </div>
        ) : showVirtualList && filteredDocuments.length > 50 ? (
          // 使用虚拟列表（大数据量时）
          <EnhancedVirtualList
            items={filteredDocuments}
            renderItem={renderDocumentItem}
            itemHeight={100}
            overscan={5}
            className="documents-virtual-list"
          />
        ) : (
          // 普通列表（小数据量时）
          <div className="documents-list">
            {filteredDocuments.map((doc, index) => renderDocumentItem(doc, index))}
          </div>
        )}
      </div>
      
      {/* 嵌入原知识库页面的其他功能 */}
      <div className="original-knowledge-content" style={{ display: 'none' }}>
        <Knowledge />
      </div>
    </div>
  );
};

export default EnhancedKnowledge;
