/**
 * 文档级视图组件（重构版）
 *
 * 用于显示文档级别的实体和关系
 * 支持文档选择功能
 *
 * @task Phase3-Week10
 * @phase 层级视图逻辑修复
 */

import React, { useState, useEffect, useCallback } from 'react';
import { FiGrid, FiList, FiLink2, FiRefreshCw } from 'react-icons/fi';
import {
  getDocumentEntities,
  getDocumentGraph,
  getDocumentLevelStats,
  getDocumentsList,
  aggregateDocumentEntities,
  getDocumentExtractionStatus
} from '../../utils/api/hierarchyApi';
import DocumentSelector from './DocumentSelector';
import DocumentEntityList from './DocumentEntityList';
import DocumentGraph from './DocumentGraph';
import DocumentRelationManagement from './DocumentRelationManagement';
import useKnowledgeStore from '../../stores/knowledgeStore';
import { useNotification } from '../../hooks/useNotification';
import './DocumentLevelView.css';

/**
 * 文档级视图组件
 *
 * @param {Object} props - 组件属性
 * @param {string|number} props.knowledgeBaseId - 知识库ID
 * @param {string|number} props.documentId - 文档ID（可选）
 */
const DocumentLevelView = ({ knowledgeBaseId, documentId: propDocumentId }) => {
  // 视图模式
  const [viewMode, setViewMode] = useState('graph'); // 'graph' | 'list' | 'relations'

  // 加载状态
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [aggregating, setAggregating] = useState(false);

  // 数据状态
  const [stats, setStats] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [documentsTotal, setDocumentsTotal] = useState(0);
  const [extractionStatus, setExtractionStatus] = useState(null);

  // 当前选中文档
  const [currentDocumentId, setCurrentDocumentId] = useState(propDocumentId || null);

  // 从状态管理获取层级相关状态
  const {
    setHierarchySelectedDocument,
    setHierarchyStats
  } = useKnowledgeStore();

  // 通知钩子
  const { showNotification } = useNotification();

  /**
   * 加载文档列表
   */
  const loadDocuments = useCallback(async () => {
    if (!knowledgeBaseId) {
      setDocuments([]);
      return;
    }

    try {
      setLoading(true);

      // 使用新的文档列表API
      const response = await getDocumentsList(knowledgeBaseId, {
        page: 1,
        pageSize: 100
      });

      const { list, total } = response.data || {};
      const docs = list || [];

      setDocuments(docs);
      setDocumentsTotal(total || 0);

      // 不再自动选择第一个文档，让用户手动选择
      // 只有在明确传入documentId时才自动选择
      if (propDocumentId && !currentDocumentId) {
        setCurrentDocumentId(propDocumentId);
        setHierarchySelectedDocument(propDocumentId);
      }
    } catch (error) {
      console.error('加载文档列表失败:', error);
      // 错误时显示空列表
      setDocuments([]);
      setDocumentsTotal(0);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, propDocumentId, setHierarchySelectedDocument]);

  /**
   * 加载文档级统计数据
   * 只有在选择了文档时才加载
   */
  const loadStats = useCallback(async () => {
    // 未选择文档时不加载统计
    if (!currentDocumentId) {
      setStats(null);
      return;
    }

    setStatsLoading(true);
    try {
      const response = await getDocumentLevelStats(knowledgeBaseId);
      const statsData = response.data || response;
      setStats(statsData);

      // 更新状态管理中的统计数据
      setHierarchyStats('document', statsData);
    } catch (error) {
      console.error('加载文档级统计失败:', error);
      // 错误时清空统计
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }, [knowledgeBaseId, currentDocumentId, setHierarchyStats]);

  /**
   * 加载文档实体识别状态
   */
  const loadExtractionStatus = useCallback(async () => {
    if (!currentDocumentId || !knowledgeBaseId) {
      setExtractionStatus(null);
      return;
    }

    try {
      const response = await getDocumentExtractionStatus(knowledgeBaseId, currentDocumentId);
      if (response.code === 200) {
        setExtractionStatus(response.data);
      }
    } catch (error) {
      console.error('加载文档识别状态失败:', error);
      setExtractionStatus(null);
    }
  }, [knowledgeBaseId, currentDocumentId]);

  /**
   * 聚合文档实体
   */
  const handleAggregateEntities = useCallback(async () => {
    if (!currentDocumentId || !knowledgeBaseId) {
      showNotification({
        type: 'warning',
        message: '请先选择一个文档'
      });
      return;
    }

    setAggregating(true);
    try {
      const response = await aggregateDocumentEntities(knowledgeBaseId, currentDocumentId);
      
      if (response.code === 200) {
        const data = response.data;
        showNotification({
          type: 'success',
          message: `实体聚合成功！片段级实体: ${data.chunk_entity_count}，文档级实体: ${data.document_entity_count}`
        });
        
        // 刷新状态
        await loadExtractionStatus();
        // 刷新统计数据
        await loadStats();
      } else {
        showNotification({
          type: 'error',
          message: response.message || '实体聚合失败'
        });
      }
    } catch (error) {
      console.error('实体聚合失败:', error);
      showNotification({
        type: 'error',
        message: '实体聚合失败: ' + (error.message || '未知错误')
      });
    } finally {
      setAggregating(false);
    }
  }, [knowledgeBaseId, currentDocumentId, loadExtractionStatus, loadStats, showNotification]);

  // 初始加载
  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // 加载统计数据
  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // 加载文档识别状态
  useEffect(() => {
    loadExtractionStatus();
  }, [loadExtractionStatus]);

  // 当props中的documentId变化时更新
  useEffect(() => {
    if (propDocumentId && propDocumentId !== currentDocumentId) {
      setCurrentDocumentId(propDocumentId);
      setHierarchySelectedDocument(propDocumentId);
    }
  }, [propDocumentId, currentDocumentId, setHierarchySelectedDocument]);

  /**
   * 处理文档选择
   */
  const handleDocumentSelect = useCallback((document) => {
    if (document) {
      setCurrentDocumentId(document.id);
      setHierarchySelectedDocument(document.id);
    }
  }, [setHierarchySelectedDocument]);

  // 获取当前选中的文档信息
  const currentDocument = documents.find(doc => String(doc.id) === String(currentDocumentId));

  // 渲染加载状态
  if (loading && documents.length === 0) {
    return (
      <div className="document-level-view">
        <div className="dlv-loading">
          <div className="loading-spinner"></div>
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="document-level-view">
      {/* 头部区域 */}
      <div className="dl-header">
        <h2>文档级视图</h2>
        <div className="view-modes">
          <button
            className={`mode-btn ${viewMode === 'graph' ? 'active' : ''}`}
            onClick={() => setViewMode('graph')}
          >
            <FiGrid /> 文档图谱
          </button>
          <button
            className={`mode-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            <FiList /> 实体列表
          </button>
          <button
            className={`mode-btn ${viewMode === 'relations' ? 'active' : ''}`}
            onClick={() => setViewMode('relations')}
          >
            <FiLink2 /> 关系管理
          </button>
        </div>
      </div>

      {/* 选择器区域 */}
      <div className="dlv-selectors">
        <div className="selector-group">
          <label className="selector-label">选择文档:</label>
          <DocumentSelector
            knowledgeBaseId={knowledgeBaseId}
            value={currentDocumentId}
            onChange={handleDocumentSelect}
            placeholder="请选择文档"
          />
        </div>
      </div>

      {/* 文档识别状态显示 */}
      {currentDocumentId && extractionStatus && (
        <div className="extraction-status-bar">
          <div className="status-info">
            <span className="status-label">实体识别状态:</span>
            <span className={`status-value status-${extractionStatus.status}`}>
              {extractionStatus.status === 'completed' ? '已完成' : 
               extractionStatus.status === 'processing' ? '处理中' : '待处理'}
            </span>
            <span className="status-progress">
              ({extractionStatus.processed_chunks}/{extractionStatus.total_chunks} 片段)
            </span>
          </div>
          <div className="status-stats">
            <span>片段级实体: {extractionStatus.chunk_entity_count}</span>
            <span>文档级实体: {extractionStatus.document_entity_count}</span>
          </div>
          <button
            className="aggregate-btn"
            onClick={handleAggregateEntities}
            disabled={aggregating}
            title="将片段级实体聚合到文档级"
          >
            {aggregating ? (
              <>
                <span className="loading-icon">⏳</span>
                <span>聚合中...</span>
              </>
            ) : (
              <>
                <FiRefreshCw />
                <span>聚合实体</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* 视图内容 */}
      <div className="dl-view-content">
        {!currentDocumentId ? (
          <div className="empty-content">
            <span className="empty-icon">📄</span>
            <span>请选择文档查看内容</span>
          </div>
        ) : (
          <>
            {viewMode === 'graph' && (
              <DocumentGraph
                knowledgeBaseId={knowledgeBaseId}
                documentId={currentDocumentId}
              />
            )}
            {viewMode === 'list' && (
              <DocumentEntityList
                knowledgeBaseId={knowledgeBaseId}
                documentId={currentDocumentId}
              />
            )}
            {viewMode === 'relations' && (
              <DocumentRelationManagement
                knowledgeBaseId={knowledgeBaseId}
                documentId={currentDocumentId}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default DocumentLevelView;
