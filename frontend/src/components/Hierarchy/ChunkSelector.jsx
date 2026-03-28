/**
 * 片段选择器组件
 *
 * 用于在层级视图中选择文档片段，依赖文档选择
 *
 * @task Phase3-Week10
 * @phase 层级视图逻辑修复
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { getDocumentChunksList } from '../../utils/api/hierarchyApi';
import './ChunkSelector.css';

/**
 * 片段选择器组件
 *
 * @param {Object} props - 组件属性
 * @param {string|number} props.knowledgeBaseId - 知识库ID
 * @param {string|number} props.documentId - 文档ID（必需）
 * @param {string|number} props.value - 当前选中的片段ID
 * @param {Function} props.onChange - 选择变更回调函数 (chunk) => void
 * @param {string} props.placeholder - 占位提示文本
 * @param {boolean} props.disabled - 是否禁用
 * @param {string} props.className - 自定义类名
 */
const ChunkSelector = ({
  knowledgeBaseId,
  documentId,
  value,
  onChange,
  placeholder = '请选择片段',
  disabled = false,
  className = ''
}) => {
  // 本地状态
  const [isOpen, setIsOpen] = useState(false);
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // Refs
  const containerRef = useRef(null);
  const listRef = useRef(null);

  const pageSize = 20;

  /**
   * 加载片段列表
   */
  const loadChunks = useCallback(async (pageNum = 1, append = false) => {
    if (!knowledgeBaseId || !documentId) {
      setChunks([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await getDocumentChunksList(knowledgeBaseId, documentId, {
        page: pageNum,
        pageSize
      });

      const { list, total: totalCount } = response.data || {};

      if (append) {
        setChunks(prev => [...prev, ...(list || [])]);
      } else {
        setChunks(list || []);
      }

      setTotal(totalCount || 0);
      setHasMore((list || []).length === pageSize);
    } catch (err) {
      setError('加载片段列表失败');
      console.error('加载片段列表失败:', err);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, documentId]);

  /**
   * 初始加载
   */
  useEffect(() => {
    if (isOpen && knowledgeBaseId && documentId) {
      loadChunks(1);
      setPage(1);
    }
  }, [isOpen, knowledgeBaseId, documentId, loadChunks]);

  /**
   * 文档变更时清空选择
   */
  useEffect(() => {
    // 文档变更时，片段列表会自动重新加载
    setChunks([]);
    setPage(1);
    setTotal(0);
    setHasMore(false);
  }, [documentId]);

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
   * 加载更多
   */
  const handleLoadMore = useCallback(() => {
    if (!loading && hasMore) {
      const nextPage = page + 1;
      loadChunks(nextPage, true);
      setPage(nextPage);
    }
  }, [loading, hasMore, page, loadChunks]);

  /**
   * 选择片段
   */
  const handleSelect = useCallback((chunk) => {
    if (onChange) {
      onChange(chunk);
    }
    setIsOpen(false);
  }, [onChange]);

  /**
   * 获取选中片段的显示文本
   */
  const getSelectedLabel = useCallback(() => {
    if (!value) {
      return !documentId ? '请先选择文档' : placeholder;
    }
    const selected = chunks.find(chunk => String(chunk.id) === String(value));
    return selected ? `片段 ${selected.index}` : placeholder;
  }, [value, chunks, placeholder, documentId]);

  /**
   * 渲染片段项
   */
  const renderChunkItem = (chunk) => {
    const isSelected = String(chunk.id) === String(value);

    return (
      <div
        key={chunk.id}
        className={`chunk-item ${isSelected ? 'selected' : ''}`}
        onClick={() => handleSelect(chunk)}
      >
        <div className="chunk-item-header">
          <span className="chunk-index">片段 {chunk.index}</span>
          <span className="chunk-entity-count">
            {chunk.entity_count} 实体
          </span>
        </div>
        <div className="chunk-text">
          {chunk.text_preview || chunk.text}
        </div>
        <div className="chunk-position">
          位置: {chunk.start_position} - {chunk.end_position}
        </div>
      </div>
    );
  };

  // 判断是否禁用
  const isDisabled = disabled || !documentId;

  return (
    <div
      ref={containerRef}
      className={`chunk-selector ${className} ${isDisabled ? 'disabled' : ''}`}
    >
      {/* 选择器触发按钮 */}
      <div
        className={`selector-trigger ${isOpen ? 'open' : ''}`}
        onClick={() => !isDisabled && setIsOpen(!isOpen)}
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
          {/* 头部信息 */}
          <div className="selector-header">
            <span>共 {total} 个片段</span>
          </div>

          {/* 片段列表 */}
          <div ref={listRef} className="selector-list">
            {loading && chunks.length === 0 ? (
              <div className="selector-loading">
                <div className="loading-spinner"></div>
                <span>加载中...</span>
              </div>
            ) : error ? (
              <div className="selector-error">
                <span className="error-icon">⚠</span>
                <span>{error}</span>
                <button onClick={() => loadChunks(1)}>
                  重试
                </button>
              </div>
            ) : chunks.length === 0 ? (
              <div className="selector-empty">
                <span className="empty-icon">📄</span>
                <span>暂无片段</span>
              </div>
            ) : (
              <>
                <div className="chunk-list">
                  {chunks.map(renderChunkItem)}
                </div>

                {/* 加载更多 */}
                {hasMore && (
                  <div
                    className="load-more"
                    onClick={handleLoadMore}
                  >
                    {loading ? (
                      <>
                        <div className="loading-spinner small"></div>
                        <span>加载中...</span>
                      </>
                    ) : (
                      <span>加载更多 ({chunks.length}/{total})</span>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

ChunkSelector.propTypes = {
  knowledgeBaseId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  documentId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
  disabled: PropTypes.bool,
  className: PropTypes.string
};

export default ChunkSelector;
