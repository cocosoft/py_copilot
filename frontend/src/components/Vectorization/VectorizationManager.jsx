/**
 * 向量化管理组件
 * 
 * 提供完整的文档向量化功能，包括：
 * - 向量化任务列表管理
 * - 批量向量化操作
 * - 向量化配置管理
 * - 向量化进度监控
 * - 向量片段查看
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  vectorizeDocument,
  getDocumentChunks,
  getDocumentProcessingProgress,
  getProcessingQueueStatus,
  processDocument,
  listDocuments,
  getKnowledgeBases
} from '../../utils/api/knowledgeApi';
import './VectorizationManager.css';

/**
 * 向量化管理组件
 */
const VectorizationManager = () => {
  const { t } = useTranslation();
  
  // 状态管理
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [filteredDocuments, setFilteredDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [processingTasks, setProcessingTasks] = useState({});
  const [activeTab, setActiveTab] = useState('pending'); // 'pending', 'completed', 'all'
  
  // 配置状态
  const [config, setConfig] = useState({
    chunkSize: 500,
    chunkOverlap: 50,
    embeddingModel: 'default',
    batchSize: 10,
    autoProcess: false
  });
  
  // 搜索和过滤
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all'); // 'all', 'vectorized', 'unvectorized', 'processing'
  
  // 模态框状态
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showChunksModal, setShowChunksModal] = useState(false);
  const [selectedDocForChunks, setSelectedDocForChunks] = useState(null);
  const [documentChunks, setDocumentChunks] = useState([]);
  
  // 统计信息
  const [stats, setStats] = useState({
    total: 0,
    vectorized: 0,
    unvectorized: 0,
    processing: 0,
    failed: 0
  });

  /**
   * 加载知识库列表
   */
  const loadKnowledgeBases = useCallback(async () => {
    try {
      const response = await getKnowledgeBases();
      setKnowledgeBases(response.data || []);
      if (response.data && response.data.length > 0 && !selectedKnowledgeBase) {
        setSelectedKnowledgeBase(response.data[0].id);
      }
    } catch (error) {
      console.error('加载知识库失败:', error);
    }
  }, [selectedKnowledgeBase]);

  /**
   * 加载文档列表
   */
  const loadDocuments = useCallback(async () => {
    if (!selectedKnowledgeBase) return;
    
    setLoading(true);
    try {
      const response = await listDocuments(selectedKnowledgeBase);
      const docs = response.documents || [];
      setDocuments(docs);
      applyFilters(docs, searchQuery, filterStatus);
      updateStats(docs);
    } catch (error) {
      console.error('加载文档失败:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedKnowledgeBase, searchQuery, filterStatus]);

  /**
   * 更新统计信息
   */
  const updateStats = (docs) => {
    const stats = {
      total: docs.length,
      vectorized: docs.filter(d => d.is_vectorized).length,
      unvectorized: docs.filter(d => !d.is_vectorized && d.document_metadata?.processing_status !== 'processing').length,
      processing: docs.filter(d => d.document_metadata?.processing_status === 'processing').length,
      failed: docs.filter(d => d.document_metadata?.processing_status === 'failed').length
    };
    setStats(stats);
  };

  /**
   * 应用过滤条件
   */
  const applyFilters = (docs, query, status) => {
    let filtered = [...docs];
    
    // 搜索过滤
    if (query) {
      filtered = filtered.filter(doc => 
        doc.title.toLowerCase().includes(query.toLowerCase()) ||
        (doc.description && doc.description.toLowerCase().includes(query.toLowerCase()))
      );
    }
    
    // 状态过滤
    if (status !== 'all') {
      switch (status) {
        case 'vectorized':
          filtered = filtered.filter(d => d.is_vectorized);
          break;
        case 'unvectorized':
          filtered = filtered.filter(d => !d.is_vectorized && d.document_metadata?.processing_status !== 'processing');
          break;
        case 'processing':
          filtered = filtered.filter(d => d.document_metadata?.processing_status === 'processing');
          break;
        case 'failed':
          filtered = filtered.filter(d => d.document_metadata?.processing_status === 'failed');
          break;
        default:
          break;
      }
    }
    
    // 根据活动标签页过滤
    if (activeTab === 'pending') {
      filtered = filtered.filter(d => !d.is_vectorized);
    } else if (activeTab === 'completed') {
      filtered = filtered.filter(d => d.is_vectorized);
    }
    
    setFilteredDocuments(filtered);
  };

  /**
   * 处理单个文档向量化
   */
  const handleVectorize = async (documentId) => {
    try {
      setProcessingTasks(prev => ({
        ...prev,
        [documentId]: { status: 'processing', progress: 0 }
      }));
      
      const result = await vectorizeDocument(documentId);
      
      if (result.status === 'processing') {
        // 开始追踪进度
        trackProcessingProgress(documentId);
      }
      
      // 重新加载文档列表
      await loadDocuments();
    } catch (error) {
      console.error('向量化失败:', error);
      setProcessingTasks(prev => ({
        ...prev,
        [documentId]: { status: 'failed', error: error.message }
      }));
    }
  };

  /**
   * 批量向量化
   */
  const handleBatchVectorize = async () => {
    const docsToProcess = selectedDocuments.length > 0 
      ? selectedDocuments 
      : documents.filter(d => !d.is_vectorized);
    
    for (const docId of docsToProcess) {
      await handleVectorize(docId);
    }
    
    setSelectedDocuments([]);
  };

  /**
   * 追踪处理进度
   */
  const trackProcessingProgress = async (documentId) => {
    const checkProgress = async () => {
      try {
        const progress = await getDocumentProcessingProgress(documentId);
        
        setProcessingTasks(prev => ({
          ...prev,
          [documentId]: {
            status: progress.status,
            progress: progress.progress || 0,
            step: progress.step,
            message: progress.message
          }
        }));
        
        if (progress.status === 'processing') {
          setTimeout(checkProgress, 2000);
        } else if (progress.status === 'completed' || progress.status === 'failed') {
          await loadDocuments();
        }
      } catch (error) {
        console.error('获取进度失败:', error);
      }
    };
    
    checkProgress();
  };

  /**
   * 查看文档向量片段
   */
  const handleViewChunks = async (doc) => {
    setSelectedDocForChunks(doc);
    setShowChunksModal(true);
    
    try {
      const chunks = await getDocumentChunks(doc.id);
      setDocumentChunks(chunks);
    } catch (error) {
      console.error('加载向量片段失败:', error);
    }
  };

  /**
   * 处理文档选择
   */
  const handleSelectDocument = (docId) => {
    setSelectedDocuments(prev => {
      if (prev.includes(docId)) {
        return prev.filter(id => id !== docId);
      }
      return [...prev, docId];
    });
  };

  /**
   * 全选/取消全选
   */
  const handleSelectAll = () => {
    if (selectedDocuments.length === filteredDocuments.length) {
      setSelectedDocuments([]);
    } else {
      setSelectedDocuments(filteredDocuments.map(d => d.id));
    }
  };

  // 初始化加载
  useEffect(() => {
    loadKnowledgeBases();
  }, [loadKnowledgeBases]);

  // 知识库变化时重新加载文档
  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // 过滤条件变化时重新应用过滤
  useEffect(() => {
    applyFilters(documents, searchQuery, filterStatus);
  }, [searchQuery, filterStatus, activeTab, documents]);

  return (
    <div className="vectorization-manager">
      {/* 头部 */}
      <div className="vectorization-header">
        <h2>{t('vectorization.title', '向量化管理')}</h2>
        <div className="header-actions">
          <button 
            className="btn btn-secondary"
            onClick={() => setShowConfigModal(true)}
          >
            ⚙️ {t('vectorization.config', '配置')}
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="stats-cards">
        <div className="stat-card">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">{t('vectorization.stats.total', '总文档')}</span>
        </div>
        <div className="stat-card success">
          <span className="stat-value">{stats.vectorized}</span>
          <span className="stat-label">{t('vectorization.stats.vectorized', '已向量化')}</span>
        </div>
        <div className="stat-card warning">
          <span className="stat-value">{stats.unvectorized}</span>
          <span className="stat-label">{t('vectorization.stats.unvectorized', '待向量化')}</span>
        </div>
        <div className="stat-card info">
          <span className="stat-value">{stats.processing}</span>
          <span className="stat-label">{t('vectorization.stats.processing', '处理中')}</span>
        </div>
        <div className="stat-card error">
          <span className="stat-value">{stats.failed}</span>
          <span className="stat-label">{t('vectorization.stats.failed', '失败')}</span>
        </div>
      </div>

      {/* 工具栏 */}
      <div className="toolbar">
        <div className="toolbar-left">
          {/* 知识库选择 */}
          <select 
            className="knowledge-base-select"
            value={selectedKnowledgeBase || ''}
            onChange={(e) => setSelectedKnowledgeBase(Number(e.target.value))}
          >
            <option value="">{t('vectorization.selectKnowledgeBase', '选择知识库')}</option>
            {knowledgeBases.map(kb => (
              <option key={kb.id} value={kb.id}>{kb.name}</option>
            ))}
          </select>

          {/* 搜索框 */}
          <input
            type="text"
            className="search-input"
            placeholder={t('vectorization.searchPlaceholder', '搜索文档...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          {/* 状态过滤 */}
          <select 
            className="filter-select"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">{t('vectorization.filter.all', '全部状态')}</option>
            <option value="unvectorized">{t('vectorization.filter.unvectorized', '待向量化')}</option>
            <option value="processing">{t('vectorization.filter.processing', '处理中')}</option>
            <option value="vectorized">{t('vectorization.filter.vectorized', '已向量化')}</option>
            <option value="failed">{t('vectorization.filter.failed', '失败')}</option>
          </select>
        </div>

        <div className="toolbar-right">
          {/* 批量操作按钮 */}
          <button 
            className="btn btn-primary"
            onClick={handleBatchVectorize}
            disabled={selectedDocuments.length === 0 && stats.unvectorized === 0}
          >
            🚀 {selectedDocuments.length > 0 
              ? t('vectorization.batchProcessSelected', '批量处理选中') 
              : t('vectorization.batchProcessAll', '批量处理全部')}
          </button>
        </div>
      </div>

      {/* 标签页 */}
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
          onClick={() => setActiveTab('pending')}
        >
          {t('vectorization.tabs.pending', '待处理')}
          {stats.unvectorized > 0 && <span className="badge">{stats.unvectorized}</span>}
        </button>
        <button 
          className={`tab ${activeTab === 'completed' ? 'active' : ''}`}
          onClick={() => setActiveTab('completed')}
        >
          {t('vectorization.tabs.completed', '已完成')}
          {stats.vectorized > 0 && <span className="badge">{stats.vectorized}</span>}
        </button>
        <button 
          className={`tab ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          {t('vectorization.tabs.all', '全部')}
          <span className="badge">{stats.total}</span>
        </button>
      </div>

      {/* 文档列表 */}
      <div className="documents-table-container">
        {loading ? (
          <div className="loading">{t('common.loading', '加载中...')}</div>
        ) : (
          <table className="documents-table">
            <thead>
              <tr>
                <th>
                  <input 
                    type="checkbox" 
                    checked={selectedDocuments.length === filteredDocuments.length && filteredDocuments.length > 0}
                    onChange={handleSelectAll}
                  />
                </th>
                <th>{t('vectorization.table.title', '文档标题')}</th>
                <th>{t('vectorization.table.status', '状态')}</th>
                <th>{t('vectorization.table.progress', '进度')}</th>
                <th>{t('vectorization.table.chunks', '片段数')}</th>
                <th>{t('vectorization.table.actions', '操作')}</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.map(doc => {
                const task = processingTasks[doc.id];
                const isProcessing = task?.status === 'processing' || doc.document_metadata?.processing_status === 'processing';
                
                return (
                  <tr key={doc.id} className={isProcessing ? 'processing' : ''}>
                    <td>
                      <input 
                        type="checkbox" 
                        checked={selectedDocuments.includes(doc.id)}
                        onChange={() => handleSelectDocument(doc.id)}
                      />
                    </td>
                    <td>
                      <div className="doc-title">{doc.title}</div>
                      <div className="doc-meta">
                        {doc.file_type} • {new Date(doc.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td>
                      {doc.is_vectorized ? (
                        <span className="status-badge success">✓ {t('vectorization.status.vectorized', '已向量化')}</span>
                      ) : isProcessing ? (
                        <span className="status-badge processing">⏳ {t('vectorization.status.processing', '处理中')}</span>
                      ) : doc.document_metadata?.processing_status === 'failed' ? (
                        <span className="status-badge error">✗ {t('vectorization.status.failed', '失败')}</span>
                      ) : (
                        <span className="status-badge pending">○ {t('vectorization.status.pending', '待处理')}</span>
                      )}
                    </td>
                    <td>
                      {isProcessing && task && (
                        <div className="progress-bar">
                          <div 
                            className="progress-fill" 
                            style={{ width: `${task.progress}%` }}
                          />
                          <span className="progress-text">{task.progress}%</span>
                        </div>
                      )}
                    </td>
                    <td>{doc.chunk_count || '-'}</td>
                    <td>
                      <div className="action-buttons">
                        {!doc.is_vectorized && !isProcessing && (
                          <button 
                            className="btn btn-sm btn-primary"
                            onClick={() => handleVectorize(doc.id)}
                          >
                            {t('vectorization.action.vectorize', '向量化')}
                          </button>
                        )}
                        {doc.is_vectorized && (
                          <button 
                            className="btn btn-sm btn-secondary"
                            onClick={() => handleViewChunks(doc)}
                          >
                            {t('vectorization.action.viewChunks', '查看片段')}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        
        {filteredDocuments.length === 0 && !loading && (
          <div className="empty-state">
            <span className="empty-icon">📄</span>
            <p>{t('vectorization.empty', '暂无文档')}</p>
          </div>
        )}
      </div>

      {/* 配置模态框 */}
      {showConfigModal && (
        <div className="modal-overlay" onClick={() => setShowConfigModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{t('vectorization.configTitle', '向量化配置')}</h3>
              <button className="close-btn" onClick={() => setShowConfigModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>{t('vectorization.config.chunkSize', '分块大小')}</label>
                <input 
                  type="number" 
                  value={config.chunkSize}
                  onChange={(e) => setConfig({...config, chunkSize: Number(e.target.value)})}
                />
              </div>
              <div className="form-group">
                <label>{t('vectorization.config.chunkOverlap', '分块重叠')}</label>
                <input 
                  type="number" 
                  value={config.chunkOverlap}
                  onChange={(e) => setConfig({...config, chunkOverlap: Number(e.target.value)})}
                />
              </div>
              <div className="form-group">
                <label>{t('vectorization.config.embeddingModel', '嵌入模型')}</label>
                <select 
                  value={config.embeddingModel}
                  onChange={(e) => setConfig({...config, embeddingModel: e.target.value})}
                >
                  <option value="default">{t('vectorization.models.default', '默认模型')}</option>
                  <option value="text-embedding-3-small">{t('vectorization.models.text-embedding-3-small', 'Text Embedding 3 Small')}</option>
                  <option value="text-embedding-3-large">{t('vectorization.models.text-embedding-3-large', 'Text Embedding 3 Large')}</option>
                </select>
              </div>
              <div className="form-group">
                <label>{t('vectorization.config.batchSize', '批处理大小')}</label>
                <input 
                  type="number" 
                  value={config.batchSize}
                  onChange={(e) => setConfig({...config, batchSize: Number(e.target.value)})}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowConfigModal(false)}>
                {t('common.cancel', '取消')}
              </button>
              <button className="btn btn-primary" onClick={() => setShowConfigModal(false)}>
                {t('common.save', '保存')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 向量片段模态框 */}
      {showChunksModal && selectedDocForChunks && (
        <div className="modal-overlay" onClick={() => setShowChunksModal(false)}>
          <div className="modal-content modal-large" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{t('vectorization.chunksTitle', '向量片段')} - {selectedDocForChunks.title}</h3>
              <button className="close-btn" onClick={() => setShowChunksModal(false)}>×</button>
            </div>
            <div className="modal-body">
              {documentChunks.length === 0 ? (
                <div className="loading">{t('common.loading', '加载中...')}</div>
              ) : (
                <div className="chunks-list">
                  {documentChunks.map((chunk, index) => (
                    <div key={chunk.id || index} className="chunk-item">
                      <div className="chunk-header">
                        <span className="chunk-index">#{index + 1}</span>
                        <span className="chunk-size">{chunk.content?.length || 0} {t('vectorization.chars', '字符')}</span>
                      </div>
                      <div className="chunk-content">
                        {chunk.content?.substring(0, 200)}{chunk.content?.length > 200 ? '...' : ''}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VectorizationManager;
