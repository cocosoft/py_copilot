/**
 * 文档管理页面
 * 
 * 知识库文档管理主页面，整合所有新组件
 */

import React, { useEffect, useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiGrid, FiList, FiFilter, FiUpload, FiSearch } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import BatchOperationToolbar from '../../../components/Knowledge/BatchOperationToolbar/BatchOperationToolbar';
import { VirtualListEnhanced } from '../../../components/UI';
import DocumentCard from '../../../components/Knowledge/DocumentCard';
import UploadButton from '../../../components/Knowledge/UploadButton';
import SmartSearch from '../../../components/Knowledge/SmartSearch/SmartSearch';
import { message } from '../../../components/UI/Message/Message';
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
  } = useKnowledgeStore();

  // 本地状态
  const [viewMode, setViewMode] = useState(VIEW_MODES.LIST);
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('createdAt-desc');
  const [filterStatus, setFilterStatus] = useState('all');

  /**
   * 获取文档列表
   */
  const fetchDocuments = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    setDocumentsLoading(true);
    setDocumentsError(null);

    try {
      // TODO: 替换为实际 API 调用
      // const response = await knowledgeApi.listDocuments({
      //   knowledgeBaseId: currentKnowledgeBase.id,
      //   page: documentsPage,
      //   pageSize: documentsPageSize,
      //   filters: documentFilters,
      //   sortBy,
      // });
      
      // 模拟数据
      const mockDocuments = Array.from({ length: 50 }, (_, i) => ({
        id: `doc-${i}`,
        title: `文档 ${i + 1}.pdf`,
        fileType: 'pdf',
        size: Math.random() * 10 * 1024 * 1024,
        createdAt: new Date(Date.now() - Math.random() * 86400000 * 30),
        vectorizationStatus: ['vectorized', 'processing', 'pending'][Math.floor(Math.random() * 3)],
      }));

      // 模拟排序
      const sortedDocs = [...mockDocuments].sort((a, b) => {
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

      // 模拟过滤
      const filteredDocs = filterStatus === 'all' 
        ? sortedDocs 
        : sortedDocs.filter(d => d.vectorizationStatus === filterStatus);

      setDocuments(filteredDocs, filteredDocs.length);
    } catch (error) {
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
   * 处理搜索
   */
  const handleSearch = useCallback((query) => {
    setDocumentFilters({ ...documentFilters, searchQuery: query });
    if (query) {
      addSearchHistory(query);
    }
  }, [documentFilters, setDocumentFilters, addSearchHistory]);

  /**
   * 处理文件上传
   */
  const handleUpload = useCallback((files) => {
    // TODO: 实现实际上传逻辑
    message.success({ content: `已选择 ${files.length} 个文件` });
    fetchDocuments();
  }, [fetchDocuments]);

  /**
   * 处理文档点击
   */
  const handleDocumentClick = useCallback((document) => {
    navigate(`/knowledge/documents/${document.id}`);
  }, [navigate]);

  /**
   * 渲染文档项
   */
  const renderDocument = useCallback((doc, index) => (
    <DocumentCard
      key={doc.id}
      document={doc}
      isSelected={selectedDocuments.includes(doc.id)}
      onSelect={() => toggleDocumentSelection(doc.id)}
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
  };

  /**
   * 处理过滤变更
   */
  const handleFilterChange = (status) => {
    setFilterStatus(status);
    setShowFilters(false);
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

      {/* 统计信息 */}
      <div className="document-management-stats">
        <span>共 {documentsTotal} 个文档</span>
        {selectedDocuments.length > 0 && (
          <span className="selected-count">已选择 {selectedDocuments.length} 个</span>
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
            <p>文档 ID: {documentId}</p>
            {/* TODO: 文档详情组件 */}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentManagement;
