/**
 * 文档选择器组件
 *
 * 用于在层级视图中选择文档，支持搜索、分页和加载状态显示
 *
 * @task Phase3-Week10
 * @phase 层级视图逻辑修复
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { getDocumentsList } from '../../utils/api/hierarchyApi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import './DocumentSelector.css';

/**
 * 文档选择器组件
 *
 * @param {Object} props - 组件属性
 * @param {string|number} props.knowledgeBaseId - 知识库ID
 * @param {string|number} props.value - 当前选中的文档ID
 * @param {Function} props.onChange - 选择变更回调函数 (document) => void
 * @param {string} props.placeholder - 占位提示文本
 * @param {boolean} props.disabled - 是否禁用
 * @param {string} props.className - 自定义类名
 */
const DocumentSelector = ({
  knowledgeBaseId,
  value,
  onChange,
  placeholder = '请选择文档',
  disabled = false,
  className = ''
}) => {
  // 本地状态
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // Refs
  const containerRef = useRef(null);
  const searchInputRef = useRef(null);
  const loadMoreRef = useRef(null);

  const pageSize = 20;

  /**
   * 加载文档列表
   */
  const loadDocuments = useCallback(async (pageNum = 1, search = '', append = false) => {
    if (!knowledgeBaseId) {
      setDocuments([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await getDocumentsList(knowledgeBaseId, {
        page: pageNum,
        pageSize,
        search
      });

      const { list, total: totalCount } = response.data || {};

      if (append) {
        setDocuments(prev => [...prev, ...(list || [])]);
      } else {
        setDocuments(list || []);
      }

      setTotal(totalCount || 0);
      setHasMore((list || []).length === pageSize);
    } catch (err) {
      setError('加载文档列表失败');
      console.error('加载文档列表失败:', err);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId]);

  /**
   * 初始加载
   */
  useEffect(() => {
    if (isOpen && knowledgeBaseId) {
      loadDocuments(1, searchQuery);
      setPage(1);
    }
  }, [isOpen, knowledgeBaseId, loadDocuments]);

  /**
   * 搜索防抖
   */
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isOpen) {
        loadDocuments(1, searchQuery);
        setPage(1);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, isOpen, loadDocuments]);

  /**
   * 点击外部关闭
   */
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  /**
   * 打开时聚焦搜索框
   */
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  /**
   * 加载更多
   */
  const handleLoadMore = useCallback(() => {
    if (!loading && hasMore) {
      const nextPage = page + 1;
      loadDocuments(nextPage, searchQuery, true);
      setPage(nextPage);
    }
  }, [loading, hasMore, page, searchQuery, loadDocuments]);

  /**
   * 选择文档
   */
  const handleSelect = useCallback((document) => {
    if (onChange) {
      onChange(document);
    }
    setIsOpen(false);
    setSearchQuery('');
  }, [onChange]);

  /**
   * 获取选中文档的显示文本
   */
  const getSelectedLabel = useCallback(() => {
    if (!value) return placeholder;
    const selected = documents.find(doc => String(doc.id) === String(value));
    return selected ? selected.title : placeholder;
  }, [value, documents, placeholder]);

  /**
   * 渲染文档项
   */
  const renderDocumentItem = (doc) => {
    const isSelected = String(doc.id) === String(value);

    return (
      <div
        key={doc.id}
        className={`document-item ${isSelected ? 'selected' : ''}`}
        onClick={() => handleSelect(doc)}
      >
        <div className="document-item-header">
          <span className="document-title">{doc.title}</span>
          <span className="document-type">{doc.file_type}</span>
        </div>
        <div className="document-item-stats">
          <span className="stat-item">
            <i className="icon-entity"></i>
            {doc.entity_count} 实体
          </span>
          <span className="stat-item">
            <i className="icon-relation"></i>
            {doc.relation_count} 关系
          </span>
          <span className="stat-item">
            <i className="icon-chunk"></i>
            {doc.chunk_count} 片段
          </span>
        </div>
      </div>
    );
  };

  return (
    <div
      ref={containerRef}
      className={`document-selector ${className} ${disabled ? 'disabled' : ''}`}
    >
      {/* 选择器触发按钮 */}
      <div
        className={`selector-trigger ${isOpen ? 'open' : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <span className={`trigger-text ${!value ? 'placeholder' : ''}`}>
          {getSelectedLabel()}
        </span>
        <span className={`trigger-arrow ${isOpen ? 'up' : 'down'}`}>
          ▼
        </span>
      </div>

      {/* 下拉面板 */}
      {isOpen && (
        <div className="selector-dropdown">
          {/* 搜索框 */}
          <div className="selector-search">
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索文档..."
              className="search-input"
            />
            {searchQuery && (
              <button
                className="search-clear"
                onClick={() => setSearchQuery('')}
              >
                ×
              </button>
            )}
          </div>

          {/* 文档列表 */}
          <div className="selector-list">
            {loading && documents.length === 0 ? (
              <div className="selector-loading">
                <div className="loading-spinner"></div>
                <span>加载中...</span>
              </div>
            ) : error ? (
              <div className="selector-error">
                <span className="error-icon">⚠</span>
                <span>{error}</span>
                <button onClick={() => loadDocuments(1, searchQuery)}>
                  重试
                </button>
              </div>
            ) : documents.length === 0 ? (
              <div className="selector-empty">
                <span className="empty-icon">📄</span>
                <span>{searchQuery ? '未找到匹配的文档' : '暂无文档'}</span>
              </div>
            ) : (
              <>
                <div className="document-list">
                  {documents.map(renderDocumentItem)}
                </div>

                {/* 加载更多 */}
                {hasMore && (
                  <div
                    ref={loadMoreRef}
                    className="load-more"
                    onClick={handleLoadMore}
                  >
                    {loading ? (
                      <>
                        <div className="loading-spinner small"></div>
                        <span>加载中...</span>
                      </>
                    ) : (
                      <span>加载更多 ({documents.length}/{total})</span>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          {/* 底部信息 */}
          {documents.length > 0 && (
            <div className="selector-footer">
              <span>共 {total} 个文档</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

DocumentSelector.propTypes = {
  knowledgeBaseId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
  disabled: PropTypes.bool,
  className: PropTypes.string
};

export default DocumentSelector;
