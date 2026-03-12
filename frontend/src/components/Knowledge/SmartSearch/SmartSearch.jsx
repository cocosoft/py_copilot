/**
 * 智能搜索组件
 * 
 * 提供搜索建议、搜索历史、实时搜索等功能
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { FiSearch, FiClock, FiX, FiFilter } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import useDebounce from '../../../hooks/useDebounce';
import './SmartSearch.css';

/**
 * 智能搜索组件
 * 
 * 支持搜索建议、搜索历史、实时搜索
 */
const SmartSearch = () => {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);

  const {
    searchHistory,
    searchSuggestions,
    documentFilters,
    addSearchHistory,
    clearSearchHistory,
    setDocumentFilters,
  } = useKnowledgeStore();

  // 防抖搜索
  const debouncedQuery = useDebounce(query, 300);

  // 监听外部点击关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        !inputRef.current.contains(event.target)
      ) {
        setIsFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 执行搜索
  const handleSearch = useCallback(() => {
    if (query.trim()) {
      addSearchHistory(query.trim());
      setDocumentFilters({ ...documentFilters, search: query.trim() });
      setIsFocused(false);
    }
  }, [query, documentFilters, addSearchHistory, setDocumentFilters]);

  // 键盘事件处理
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    } else if (e.key === 'Escape') {
      setIsFocused(false);
      inputRef.current?.blur();
    }
  };

  // 选择搜索建议
  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    addSearchHistory(suggestion);
    setDocumentFilters({ ...documentFilters, search: suggestion });
    setIsFocused(false);
  };

  // 选择搜索历史
  const handleHistoryClick = (history) => {
    setQuery(history);
    handleSearch();
  };

  // 清除搜索
  const handleClear = () => {
    setQuery('');
    setDocumentFilters({ ...documentFilters, search: '' });
    inputRef.current?.focus();
  };

  // 删除单条历史记录
  const handleRemoveHistory = (e, history) => {
    e.stopPropagation();
    // TODO: 实现删除单条历史记录
    console.log('删除历史:', history);
  };

  const hasActiveFilters = Object.keys(documentFilters).some(
    (key) => key !== 'search' && documentFilters[key]
  );

  return (
    <div className="smart-search">
      <div className="smart-search-input-wrapper">
        <div className={`smart-search-input-container ${isFocused ? 'focused' : ''}`}>
          <FiSearch className="smart-search-icon" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onKeyDown={handleKeyDown}
            placeholder="搜索文档、标签或内容..."
            className="smart-search-input"
          />
          {query && (
            <button className="smart-search-clear" onClick={handleClear}>
              <FiX />
            </button>
          )}
          {hasActiveFilters && (
            <span className="smart-search-filter-badge">
              <FiFilter />
              已筛选
            </span>
          )}
        </div>
      </div>

      {/* 下拉面板 */}
      {isFocused && (
        <div ref={dropdownRef} className="smart-search-dropdown">
          {/* 搜索建议 */}
          {query && searchSuggestions.length > 0 && (
            <div className="smart-search-section">
              <div className="smart-search-section-title">搜索建议</div>
              {searchSuggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="smart-search-item"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  <FiSearch className="smart-search-item-icon" />
                  <span className="smart-search-item-text">{suggestion}</span>
                </div>
              ))}
            </div>
          )}

          {/* 搜索历史 */}
          {searchHistory.length > 0 && (
            <div className="smart-search-section">
              <div className="smart-search-section-header">
                <span className="smart-search-section-title">搜索历史</span>
                <button
                  className="smart-search-clear-history"
                  onClick={clearSearchHistory}
                >
                  清空
                </button>
              </div>
              {searchHistory.map((history, index) => (
                <div
                  key={index}
                  className="smart-search-item"
                  onClick={() => handleHistoryClick(history)}
                >
                  <FiClock className="smart-search-item-icon" />
                  <span className="smart-search-item-text">{history}</span>
                  <button
                    className="smart-search-remove-history"
                    onClick={(e) => handleRemoveHistory(e, history)}
                  >
                    <FiX />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* 空状态 */}
          {!query && searchHistory.length === 0 && (
            <div className="smart-search-empty">
              <span>输入关键词开始搜索</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SmartSearch;
