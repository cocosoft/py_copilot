/**
 * 重排序功能页面
 *
 * 提供搜索结果的重排序功能，支持多种排序策略
 */

import React, { useState, useCallback } from 'react';
import { FiSearch, FiArrowUpDown, FiFilter, FiClock, FiBookmark, FiX } from 'react-icons/fi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import { Button } from '../../components/UI';
import { message } from '../../components/UI/Message/Message';
import { searchDocuments } from '../../utils/api/knowledgeApi';
import './Reranking.css';

/**
 * 重排序策略配置
 */
const RERANKING_STRATEGIES = [
  { value: 'relevance', label: '相关性排序', description: '基于语义相似度的默认排序' },
  { value: 'freshness', label: '新鲜度排序', description: '基于文档创建时间的排序' },
  { value: 'popularity', label: '流行度排序', description: '基于文档访问频率的排序' },
  { value: 'length', label: '长度排序', description: '基于文档长度的排序' },
];

/**
 * 重排序功能页面
 */
const Reranking = () => {
  const { 
    currentKnowledgeBase,
    searchHistory,
    addSearchHistory,
    clearSearchHistory,
  } = useKnowledgeStore();

  // 本地状态
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);
  const [originalResults, setOriginalResults] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState('relevance');
  const [sortOrder, setSortOrder] = useState('desc');
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
        createdAt: result.created_at || result.metadata?.created_at,
        length: (result.content || result.chunk_content || '').length,
      }));

      setOriginalResults(formattedResults);
      setResults(formattedResults);
      addSearchHistory(query);
    } catch (error) {
      message.error({ content: '搜索失败：' + error.message });
    } finally {
      setIsSearching(false);
    }
  }, [query, filters, currentKnowledgeBase, addSearchHistory]);

  /**
   * 执行重排序
   */
  const handleRerank = useCallback(() => {
    if (originalResults.length === 0) {
      message.warning({ content: '请先执行搜索' });
      return;
    }

    let rerankedResults = [...originalResults];

    // 根据选择的策略进行排序
    switch (selectedStrategy) {
      case 'freshness':
        rerankedResults.sort((a, b) => {
          const dateA = new Date(a.createdAt || 0);
          const dateB = new Date(b.createdAt || 0);
          return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });
        break;
      case 'length':
        rerankedResults.sort((a, b) => {
          return sortOrder === 'desc' ? b.length - a.length : a.length - b.length;
        });
        break;
      case 'relevance':
      default:
        rerankedResults.sort((a, b) => {
          return sortOrder === 'desc' ? b.score - a.score : a.score - b.score;
        });
        break;
    }

    setResults(rerankedResults);
  }, [originalResults, selectedStrategy, sortOrder]);

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
    setOriginalResults([]);
  };

  if (!currentKnowledgeBase) {
    return (
      <div className="reranking-empty">
        <div className="empty-icon">🔍</div>
        <h3>请选择一个知识库</h3>
        <p>从左侧边栏选择一个知识库开始重排序</p>
      </div>
    );
  }

  return (
    <div className="reranking">
      {/* 搜索区域 */}
      <div className="search-section">
        <div className="search-box">
          <FiSearch className="search-icon" size={20} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="输入关键词进行搜索..."
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

      {/* 重排序控制 */}
      {results.length > 0 && (
        <div className="reranking-controls">
          <div className="reranking-header">
            <h4>重排序设置</h4>
            <Button
              variant="primary"
              icon={<FiArrowUpDown />}
              onClick={handleRerank}
            >
              应用重排序
            </Button>
          </div>
          
          <div className="reranking-options">
            <div className="option-group">
              <label>排序策略</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
              >
                {RERANKING_STRATEGIES.map(strategy => (
                  <option key={strategy.value} value={strategy.value}>
                    {strategy.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="option-group">
              <label>排序顺序</label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
              >
                <option value="desc">降序</option>
                <option value="asc">升序</option>
              </select>
            </div>
          </div>
          
          <div className="strategy-description">
            <p>{RERANKING_STRATEGIES.find(s => s.value === selectedStrategy)?.description}</p>
          </div>
        </div>
      )}

      {/* 搜索结果 */}
      {results.length > 0 && (
        <div className="search-results">
          <div className="results-header">
            <span>找到 {results.length} 个结果</span>
            <span className="current-strategy">
              当前排序: {RERANKING_STRATEGIES.find(s => s.value === selectedStrategy)?.label} ({sortOrder === 'desc' ? '降序' : '升序'})
            </span>
          </div>
          
          <div className="results-list">
            {results.map((result, index) => (
              <div key={result.id} className="result-item">
                <div className="result-rank">
                  {index + 1}
                </div>
                <div className="result-content">
                  <div className="result-header">
                    <h4 className="result-title">{result.title}</h4>
                    <span className="result-score">
                      相关度: {(result.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="result-text">{result.content}</p>
                  <div className="result-meta">
                    <FiBookmark size={14} />
                    <span>{result.documentName}</span>
                    {result.createdAt && (
                      <span className="result-date">
                        {new Date(result.createdAt).toLocaleDateString()}
                      </span>
                    )}
                  </div>
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
            <h4>重排序提示</h4>
            <ul>
              <li>输入关键词进行搜索</li>
              <li>选择不同的排序策略</li>
              <li>点击"应用重排序"按钮查看结果</li>
              <li>调整排序顺序（升序/降序）</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reranking;