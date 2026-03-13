/**
 * 高级搜索页面
 * 
 * 提供语义搜索和高级筛选功能
 */

import React, { useState, useCallback } from 'react';
import { FiSearch, FiFilter, FiClock, FiBookmark, FiX } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { message } from '../../../components/UI/Message/Message';
import { searchDocuments } from '../../../utils/api/knowledgeApi';
import './styles.css';

/**
 * 高级搜索页面
 */
const AdvancedSearch = () => {
  const { 
    currentKnowledgeBase,
    searchHistory,
    searchSuggestions,
    addSearchHistory,
    clearSearchHistory,
  } = useKnowledgeStore();

  // 本地状态
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    fileTypes: [],
    dateRange: null,
    vectorizedOnly: false,
  });

  /**
   * 执行搜索
   */
  const handleSearch = useCallback(async () => {
    if (!query.trim()) {
      message.warning({ content: '请输入搜索内容' });
      return;
    }

    setIsSearching(true);
    try {
      // 调用真实 API 进行搜索
      const searchResults = await searchDocuments(
        query,
        20,
        currentKnowledgeBase?.id,
        'relevance',
        'desc',
        filters.fileTypes || [],
        filters.dateRange?.start,
        filters.dateRange?.end
      );

      // 转换后端数据为前端格式
      const formattedResults = (searchResults || []).map((result, index) => ({
        id: result.id || `result-${index}`,
        title: result.title || '无标题',
        content: result.content || result.chunk_content || '无内容',
        score: result.score || result.similarity || 0,
        documentId: result.document_id || result.id,
        documentName: result.document_name || result.title || '未知文档',
        highlight: result.highlight || result.content || '',
      }));

      setResults(formattedResults);
      addSearchHistory(query);
    } catch (error) {
      message.error({ content: '搜索失败：' + error.message });
    } finally {
      setIsSearching(false);
    }
  }, [query, filters, currentKnowledgeBase, addSearchHistory]);

  /**
   * 处理历史记录点击
   */
  const handleHistoryClick = (historyQuery) => {
    setQuery(historyQuery);
    handleSearch();
  };

  /**
   * 清除搜索
   */
  const handleClear = () => {
    setQuery('');
    setResults([]);
  };

  if (!currentKnowledgeBase) {
    return (
      <div className="advanced-search-empty">
        <div className="empty-icon">🔍</div>
        <h3>请选择一个知识库</h3>
        <p>从左侧边栏选择一个知识库开始搜索</p>
      </div>
    );
  }

  return (
    <div className="advanced-search">
      {/* 搜索区域 */}
      <div className="search-section">
        <div className="search-box">
          <FiSearch className="search-icon" size={20} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="输入关键词进行语义搜索..."
          />
          {query && (
            <button className="clear-btn" onClick={handleClear}>
              <FiX size={18} />
            </button>
          )}
        </div>

        <div className="search-actions">
          <Button
            variant="secondary"
            icon={<FiFilter />}
            onClick={() => setShowFilters(!showFilters)}
          >
            筛选
          </Button>
          <Button
            variant="primary"
            icon={<FiSearch />}
            onClick={handleSearch}
            loading={isSearching}
          >
            搜索
          </Button>
        </div>
      </div>

      {/* 筛选面板 */}
      {showFilters && (
        <div className="filters-panel">
          <h4>搜索筛选</h4>
          <div className="filter-options">
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.vectorizedOnly}
                onChange={(e) => setFilters({ ...filters, vectorizedOnly: e.target.checked })}
              />
              仅搜索已向量化文档
            </label>
          </div>
        </div>
      )}

      {/* 搜索结果 */}
      {results.length > 0 && (
        <div className="search-results">
          <div className="results-header">
            <span>找到 {results.length} 个结果</span>
          </div>
          
          <div className="results-list">
            {results.map((result) => (
              <div key={result.id} className="result-item">
                <div className="result-header">
                  <h4 className="result-title">{result.title}</h4>
                  <span className="result-score">
                    相关度: {(result.score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="result-content">{result.content}</p>
                <div className="result-meta">
                  <FiBookmark size={14} />
                  <span>{result.documentName}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 搜索历史和提示 */}
      {results.length === 0 && !isSearching && (
        <div className="search-tips">
          {searchHistory.length > 0 && (
            <div className="history-section">
              <div className="section-header">
                <FiClock size={16} />
                <h4>搜索历史</h4>
                <button onClick={clearSearchHistory}>清除</button>
              </div>
              <div className="history-list">
                {searchHistory.slice(0, 10).map((item, index) => (
                  <button
                    key={index}
                    className="history-item"
                    onClick={() => handleHistoryClick(item.query)}
                  >
                    {item.query}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="tips-section">
            <h4>搜索提示</h4>
            <ul>
              <li>输入关键词进行语义搜索</li>
              <li>支持自然语言查询</li>
              <li>使用筛选器缩小搜索范围</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedSearch;
