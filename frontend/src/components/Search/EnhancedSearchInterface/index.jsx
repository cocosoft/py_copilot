/**
 * 增强型搜索界面组件
 *
 * 改进搜索界面，利用现有zustand状态管理
 *
 * 任务编号: Phase2-Week5
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { create } from 'zustand';
import { Card, Button, Input, Badge } from '../../UnifiedComponentLibrary';

/**
 * 搜索状态管理
 */
export const useSearchStore = create((set, get) => ({
  // 搜索状态
  query: '',
  filters: {
    type: 'all',
    dateRange: null,
    confidence: 0,
  },
  sortBy: 'relevance',
  results: [],
  loading: false,
  error: null,
  totalResults: 0,
  currentPage: 1,
  pageSize: 20,

  // 搜索历史
  searchHistory: [],

  // 最近搜索
  recentSearches: [],

  // 热门搜索
  trendingSearches: [],

  // 设置查询
  setQuery: (query) => set({ query }),

  // 设置过滤器
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
  })),

  // 设置排序
  setSortBy: (sortBy) => set({ sortBy }),

  // 设置结果
  setResults: (results, total) => set({
    results,
    totalResults: total,
    loading: false,
  }),

  // 设置加载状态
  setLoading: (loading) => set({ loading }),

  // 设置错误
  setError: (error) => set({ error, loading: false }),

  // 设置页码
  setPage: (page) => set({ currentPage: page }),

  // 添加到搜索历史
  addToHistory: (query) => {
    if (!query.trim()) return;

    set((state) => {
      const newHistory = [
        { query, timestamp: Date.now() },
        ...state.searchHistory.filter((h) => h.query !== query),
      ].slice(0, 50);

      return { searchHistory: newHistory };
    });
  },

  // 清除历史
  clearHistory: () => set({ searchHistory: [] }),

  // 执行搜索
  performSearch: async (searchQuery) => {
    const { filters, sortBy, currentPage, pageSize } = get();

    set({ loading: true, error: null, query: searchQuery });

    try {
      // 模拟API调用
      await new Promise((resolve) => setTimeout(resolve, 500));

      // 模拟搜索结果
      const mockResults = generateMockResults(searchQuery, filters, sortBy);

      set({
        results: mockResults.slice((currentPage - 1) * pageSize, currentPage * pageSize),
        totalResults: mockResults.length,
        loading: false,
      });

      get().addToHistory(searchQuery);
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  // 重置搜索
  resetSearch: () => set({
    query: '',
    filters: {
      type: 'all',
      dateRange: null,
      confidence: 0,
    },
    sortBy: 'relevance',
    results: [],
    totalResults: 0,
    currentPage: 1,
  }),
}));

/**
 * 生成模拟搜索结果
 */
function generateMockResults(query, filters, sortBy) {
  const mockData = [
    {
      id: '1',
      title: '人工智能在医疗领域的应用',
      content: '人工智能技术正在改变医疗行业，从诊断到治疗都有广泛应用...',
      type: 'document',
      confidence: 0.95,
      date: '2024-01-15',
      tags: ['AI', '医疗', '技术'],
    },
    {
      id: '2',
      title: '机器学习算法综述',
      content: '机器学习是人工智能的核心技术之一，包括监督学习、无监督学习等...',
      type: 'document',
      confidence: 0.88,
      date: '2024-01-10',
      tags: ['机器学习', '算法'],
    },
    {
      id: '3',
      title: '深度学习框架比较',
      content: 'TensorFlow、PyTorch等深度学习框架各有特点...',
      type: 'document',
      confidence: 0.82,
      date: '2024-01-05',
      tags: ['深度学习', '框架'],
    },
    {
      id: '4',
      title: '自然语言处理技术',
      content: 'NLP技术使计算机能够理解和生成人类语言...',
      type: 'document',
      confidence: 0.91,
      date: '2024-01-20',
      tags: ['NLP', 'AI'],
    },
    {
      id: '5',
      title: '计算机视觉应用',
      content: '计算机视觉在图像识别、自动驾驶等领域有重要应用...',
      type: 'document',
      confidence: 0.85,
      date: '2024-01-12',
      tags: ['CV', '图像识别'],
    },
  ];

  let results = mockData.filter((item) =>
    item.title.toLowerCase().includes(query.toLowerCase()) ||
    item.content.toLowerCase().includes(query.toLowerCase())
  );

  // 应用过滤器
  if (filters.type !== 'all') {
    results = results.filter((item) => item.type === filters.type);
  }

  if (filters.confidence > 0) {
    results = results.filter((item) => item.confidence >= filters.confidence);
  }

  // 排序
  if (sortBy === 'relevance') {
    results.sort((a, b) => b.confidence - a.confidence);
  } else if (sortBy === 'date') {
    results.sort((a, b) => new Date(b.date) - new Date(a.date));
  } else if (sortBy === 'title') {
    results.sort((a, b) => a.title.localeCompare(b.title));
  }

  return results;
}

/**
 * 搜索建议组件
 * @param {Object} props - 组件属性
 * @param {string} props.query - 当前查询
 * @param {Function} props.onSelect - 选择建议回调
 * @param {Function} props.onClose - 关闭回调
 */
const SearchSuggestions = ({ query, onSelect, onClose }) => {
  const { searchHistory, recentSearches } = useSearchStore();
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    if (!query.trim()) {
      // 显示搜索历史
      setSuggestions(searchHistory.slice(0, 5).map((h) => ({
        type: 'history',
        text: h.query,
        timestamp: h.timestamp,
      })));
    } else {
      // 基于查询生成建议
      const mockSuggestions = [
        `${query} 教程`,
        `${query} 入门`,
        `${query} 最佳实践`,
        `${query} 案例分析`,
      ];
      setSuggestions(mockSuggestions.map((s) => ({ type: 'suggestion', text: s })));
    }
  }, [query, searchHistory]);

  if (suggestions.length === 0) return null;

  return (
    <div className="search-suggestions">
      {suggestions.map((suggestion, index) => (
        <div
          key={index}
          className={`suggestion-item ${suggestion.type}`}
          onClick={() => {
            onSelect(suggestion.text);
            onClose();
          }}
        >
          <span className="suggestion-icon">
            {suggestion.type === 'history' ? '🕐' : '🔍'}
          </span>
          <span className="suggestion-text">{suggestion.text}</span>
          {suggestion.type === 'history' && (
            <span className="suggestion-time">
              {new Date(suggestion.timestamp).toLocaleDateString()}
            </span>
          )}
        </div>
      ))}
    </div>
  );
};

/**
 * 搜索结果项组件
 * @param {Object} props - 组件属性
 * @param {Object} props.result - 搜索结果
 * @param {string} props.query - 查询词
 * @param {Function} props.onClick - 点击回调
 */
const SearchResultItem = ({ result, query, onClick }) => {
  const highlightText = (text, query) => {
    if (!query.trim()) return text;

    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={index}>{part}</mark>
      ) : (
        part
      )
    );
  };

  return (
    <div className="search-result-item" onClick={() => onClick?.(result)}>
      <div className="result-header">
        <h4 className="result-title">
          {highlightText(result.title, query)}
        </h4>
        <Badge variant="info">{result.type}</Badge>
      </div>

      <p className="result-content">
        {highlightText(result.content, query)}
      </p>

      <div className="result-meta">
        <div className="meta-left">
          <span className="meta-item">
            置信度: {(result.confidence * 100).toFixed(0)}%
          </span>
          <span className="meta-item">
            日期: {result.date}
          </span>
        </div>
        <div className="meta-right">
          {result.tags?.map((tag) => (
            <Badge key={tag} variant="secondary" size="sm">
              {tag}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * 搜索过滤器组件
 * @param {Object} props - 组件属性
 * @param {Object} props.filters - 当前过滤器
 * @param {Function} props.onChange - 变更回调
 */
const SearchFilters = ({ filters, onChange }) => {
  const filterOptions = {
    type: [
      { value: 'all', label: '全部' },
      { value: 'document', label: '文档' },
      { value: 'entity', label: '实体' },
      { value: 'relation', label: '关系' },
    ],
    sortBy: [
      { value: 'relevance', label: '相关度' },
      { value: 'date', label: '日期' },
      { value: 'title', label: '标题' },
    ],
  };

  return (
    <div className="search-filters">
      <div className="filter-group">
        <label>类型</label>
        <select
          value={filters.type}
          onChange={(e) => onChange?.({ ...filters, type: e.target.value })}
        >
          {filterOptions.type.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>置信度</label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={filters.confidence}
          onChange={(e) =>
            onChange?.({ ...filters, confidence: parseFloat(e.target.value) })
          }
        />
        <span>{(filters.confidence * 100).toFixed(0)}%</span>
      </div>

      <div className="filter-group">
        <label>排序</label>
        <select
          value={filters.sortBy}
          onChange={(e) => onChange?.({ ...filters, sortBy: e.target.value })}
        >
          {filterOptions.sortBy.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

/**
 * 增强型搜索界面组件
 * @param {Object} props - 组件属性
 * @param {Function} props.onResultClick - 结果点击回调
 * @param {boolean} props.showFilters - 是否显示过滤器
 */
const EnhancedSearchInterface = ({
  onResultClick,
  showFilters = true,
}) => {
  const {
    query,
    filters,
    results,
    loading,
    error,
    totalResults,
    currentPage,
    pageSize,
    setQuery,
    setFilters,
    setSortBy,
    performSearch,
    resetSearch,
  } = useSearchStore();

  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchInputRef = useRef(null);

  // 处理搜索
  const handleSearch = useCallback(() => {
    if (query.trim()) {
      performSearch(query);
      setShowSuggestions(false);
    }
  }, [query, performSearch]);

  // 处理键盘事件
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter') {
        handleSearch();
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
      }
    },
    [handleSearch]
  );

  // 处理过滤器变更
  const handleFilterChange = useCallback(
    (newFilters) => {
      setFilters(newFilters);
      if (query.trim()) {
        performSearch(query);
      }
    },
    [query, setFilters, performSearch]
  );

  // 总页数
  const totalPages = Math.ceil(totalResults / pageSize);

  return (
    <div className="enhanced-search-interface">
      {/* 搜索头部 */}
      <div className="search-header">
        <div className="search-input-wrapper">
          <Input
            ref={searchInputRef}
            type="text"
            placeholder="输入搜索关键词..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowSuggestions(true)}
            prefix={<span>🔍</span>}
            suffix={
              query && (
                <button
                  className="clear-button"
                  onClick={() => {
                    setQuery('');
                    searchInputRef.current?.focus();
                  }}
                >
                  ✕
                </button>
              )
            }
          />

          {showSuggestions && (
            <SearchSuggestions
              query={query}
              onSelect={(text) => {
                setQuery(text);
                performSearch(text);
              }}
              onClose={() => setShowSuggestions(false)}
            />
          )}
        </div>

        <Button
          variant="primary"
          onClick={handleSearch}
          loading={loading}
        >
          搜索
        </Button>

        <Button variant="secondary" onClick={resetSearch}>
          重置
        </Button>
      </div>

      {/* 过滤器 */}
      {showFilters && (
        <SearchFilters filters={filters} onChange={handleFilterChange} />
      )}

      {/* 搜索结果 */}
      <div className="search-results">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>正在搜索...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <p>搜索出错: {error}</p>
            <Button variant="secondary" onClick={handleSearch}>
              重试
            </Button>
          </div>
        ) : results.length > 0 ? (
          <>
            <div className="results-header">
              <span className="results-count">
                找到 {totalResults} 个结果
              </span>
              <span className="results-page">
                第 {currentPage} / {totalPages} 页
              </span>
            </div>

            <div className="results-list">
              {results.map((result) => (
                <SearchResultItem
                  key={result.id}
                  result={result}
                  query={query}
                  onClick={onResultClick}
                />
              ))}
            </div>

            {/* 分页 */}
            {totalPages > 1 && (
              <div className="pagination">
                <Button
                  variant="outline"
                  disabled={currentPage === 1}
                  onClick={() => setPage(currentPage - 1)}
                >
                  上一页
                </Button>
                <span className="page-info">
                  {currentPage} / {totalPages}
                </span>
                <Button
                  variant="outline"
                  disabled={currentPage === totalPages}
                  onClick={() => setPage(currentPage + 1)}
                >
                  下一页
                </Button>
              </div>
            )}
          </>
        ) : query ? (
          <div className="empty-state">
            <p>未找到与 "{query}" 相关的结果</p>
            <p className="empty-hint">请尝试其他关键词或调整过滤器</p>
          </div>
        ) : (
          <div className="empty-state">
            <p>输入关键词开始搜索</p>
            <p className="empty-hint">支持文档、实体、关系等多种类型</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedSearchInterface;
export { useSearchStore, SearchSuggestions, SearchResultItem, SearchFilters };
