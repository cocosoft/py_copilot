/**
 * 增强版搜索页面
 * 
 * 基于用户体验分析结果，重构搜索界面功能
 * 解决功能不完善、筛选条件复杂、结果展示不清晰等问题
 */

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { 
  FiSearch, FiFilter, FiX, FiDownload, FiUpload, FiHelpCircle,
  FiChevronDown, FiChevronUp, FiStar, FiClock, FiTrendingUp,
  FiBook, FiUser, FiBuilding, FiMapPin, FiCalendar, FiTag,
  FiEye, FiEyeOff, FiCopy, FiShare2, FiBookmark, FiRefreshCw
} from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { 
  Button, 
  Modal, 
  Loading, 
  ErrorBoundary,
  designTokens 
} from '../../../components/UnifiedComponentLibrary';
import { message } from '../../../components/UI/Message/Message';
import {
  searchKnowledgeBase,
  getSearchHistory,
  saveSearchQuery,
  getSearchSuggestions
} from '../../../utils/api/searchApi';
import './enhanced-styles.css';

/**
 * 增强版搜索页面
 */
const EnhancedSearch = () => {
  const searchInputRef = useRef(null);
  const { currentKnowledgeBase } = useKnowledgeStore();
  
  // 搜索状态
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchTime, setSearchTime] = useState(0);
  
  // 筛选条件
  const [filters, setFilters] = useState({
    entityTypes: [],
    documentTypes: [],
    dateRange: { start: null, end: null },
    confidence: { min: 0, max: 1 },
    relevance: { min: 0, max: 1 },
    sources: [],
    tags: []
  });
  
  // 视图状态
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'grid' | 'timeline'
  const [sortBy, setSortBy] = useState('relevance'); // 'relevance' | 'date' | 'confidence'
  const [sortOrder, setSortOrder] = useState('desc'); // 'asc' | 'desc'
  
  // 高级功能
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [savedSearches, setSavedSearches] = useState([]);
  
  // 结果操作
  const [selectedResults, setSelectedResults] = useState(new Set());
  const [showResultDetails, setShowResultDetails] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);

  /**
   * 执行搜索
   */
  const handleSearch = useCallback(async (query = searchQuery, filterOptions = filters) => {
    if (!query.trim()) {
      message.warning({ content: '请输入搜索关键词' });
      return;
    }

    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择知识库' });
      return;
    }

    setSearching(true);
    const startTime = Date.now();

    try {
      const results = await searchKnowledgeBase({
        knowledgeBaseId: currentKnowledgeBase.id,
        query: query.trim(),
        filters: filterOptions,
        sortBy,
        sortOrder,
        limit: 100
      });

      setSearchResults(results);
      setSearchTime(Date.now() - startTime);
      
      // 保存搜索历史
      saveSearchToHistory(query.trim(), results.length);
      
      message.success({ 
        content: `搜索完成，找到 ${results.length} 条结果 (${Math.round(searchTime)}ms)` 
      });

    } catch (error) {
      message.error({ content: `搜索失败: ${error.message}` });
    } finally {
      setSearching(false);
    }
  }, [searchQuery, filters, sortBy, sortOrder, currentKnowledgeBase]);

  /**
   * 保存搜索历史
   */
  const saveSearchToHistory = useCallback(async (query, resultCount) => {
    try {
      await saveSearchQuery({
        query,
        knowledgeBaseId: currentKnowledgeBase?.id,
        resultCount,
        timestamp: new Date().toISOString()
      });
      
      // 更新本地历史记录
      setSearchHistory(prev => [
        {
          id: Date.now(),
          query,
          resultCount,
          timestamp: new Date()
        },
        ...prev.slice(0, 9) // 保留最近10条
      ]);
    } catch (error) {
      console.warn('保存搜索历史失败:', error);
    }
  }, [currentKnowledgeBase]);

  /**
   * 获取搜索建议
   */
  const fetchSuggestions = useCallback(async (query) => {
    if (!query.trim() || !currentKnowledgeBase) {
      setSuggestions([]);
      return;
    }

    try {
      const suggestions = await getSearchSuggestions({
        knowledgeBaseId: currentKnowledgeBase.id,
        query: query.trim(),
        limit: 5
      });
      setSuggestions(suggestions);
    } catch (error) {
      console.warn('获取搜索建议失败:', error);
      setSuggestions([]);
    }
  }, [currentKnowledgeBase]);

  /**
   * 快速搜索
   */
  const handleQuickSearch = useCallback((query) => {
    setSearchQuery(query);
    handleSearch(query);
  }, [handleSearch]);

  /**
   * 高级搜索
   */
  const handleAdvancedSearch = useCallback(() => {
    setShowAdvanced(true);
  }, []);

  /**
   * 结果选择操作
   */
  const handleResultSelect = useCallback((resultId, selected) => {
    setSelectedResults(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(resultId);
      } else {
        newSet.delete(resultId);
      }
      return newSet;
    });
  }, []);

  /**
   * 全选/取消全选
   */
  const handleSelectAll = useCallback((select) => {
    if (select) {
      setSelectedResults(new Set(searchResults.map(r => r.id)));
    } else {
      setSelectedResults(new Set());
    }
  }, [searchResults]);

  /**
   * 查看结果详情
   */
  const handleViewResultDetails = useCallback((result) => {
    setCurrentResult(result);
    setShowResultDetails(true);
  }, []);

  /**
   * 导出搜索结果
   */
  const handleExportResults = useCallback(() => {
    if (selectedResults.size === 0) {
      message.warning({ content: '请先选择要导出的结果' });
      return;
    }

    const selectedData = searchResults.filter(r => selectedResults.has(r.id));
    const dataStr = JSON.stringify(selectedData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `search-results-${Date.now()}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    message.success({ content: `成功导出 ${selectedResults.size} 条结果` });
  }, [selectedResults, searchResults]);

  /**
   * 保存搜索
   */
  const handleSaveSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      message.warning({ content: '请先执行搜索' });
      return;
    }

    try {
      const savedSearch = {
        id: Date.now(),
        name: `搜索: ${searchQuery}`,
        query: searchQuery,
        filters,
        resultCount: searchResults.length,
        timestamp: new Date()
      };

      setSavedSearches(prev => [savedSearch, ...prev]);
      message.success({ content: '搜索已保存' });
    } catch (error) {
      message.error({ content: '保存搜索失败' });
    }
  }, [searchQuery, filters, searchResults]);

  /**
   * 加载保存的搜索
   */
  const handleLoadSavedSearch = useCallback((savedSearch) => {
    setSearchQuery(savedSearch.query);
    setFilters(savedSearch.filters);
    handleSearch(savedSearch.query, savedSearch.filters);
    message.success({ content: '已加载保存的搜索' });
  }, [handleSearch]);

  /**
   * 渲染搜索框
   */
  const renderSearchBox = () => (
    <div className="search-box-container">
      <div className="search-box">
        <FiSearch className="search-icon" />
        <input
          ref={searchInputRef}
          type="text"
          placeholder="搜索知识库内容..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            fetchSuggestions(e.target.value);
          }}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          disabled={searching}
        />
        
        {searchQuery && (
          <Button
            variant="ghost"
            size="small"
            icon={FiX}
            onClick={() => setSearchQuery('')}
            className="clear-button"
          />
        )}
        
        <Button
          variant="primary"
          icon={FiSearch}
          onClick={() => handleSearch()}
          loading={searching}
          disabled={!searchQuery.trim() || !currentKnowledgeBase}
        >
          搜索
        </Button>
      </div>

      {/* 搜索建议 */}
      {suggestions.length > 0 && (
        <div className="search-suggestions">
          {suggestions.map((suggestion, index) => (
            <div
              key={index}
              className="suggestion-item"
              onClick={() => handleQuickSearch(suggestion)}
            >
              <FiSearch className="suggestion-icon" />
              <span>{suggestion}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  /**
   * 渲染筛选面板
   */
  const renderFilterPanel = () => (
    <div className={`filter-panel ${showFilters ? 'expanded' : ''}`}>
      <div className="panel-header">
        <FiFilter className="icon" />
        <span>筛选条件</span>
        <Button
          variant="ghost"
          size="small"
          icon={showFilters ? FiChevronUp : FiChevronDown}
          onClick={() => setShowFilters(!showFilters)}
        />
      </div>

      {showFilters && (
        <div className="filter-content">
          <div className="filter-section">
            <label>实体类型</label>
            <div className="entity-type-filters">
              {[
                { value: 'person', label: '人物', icon: FiUser },
                { value: 'organization', label: '组织', icon: FiBuilding },
                { value: 'location', label: '地点', icon: FiMapPin },
                { value: 'date', label: '日期', icon: FiCalendar },
                { value: 'other', label: '其他', icon: FiTag }
              ].map(type => (
                <div
                  key={type.value}
                  className={`type-filter ${filters.entityTypes.includes(type.value) ? 'active' : ''}`}
                  onClick={() => {
                    setFilters(prev => ({
                      ...prev,
                      entityTypes: prev.entityTypes.includes(type.value)
                        ? prev.entityTypes.filter(t => t !== type.value)
                        : [...prev.entityTypes, type.value]
                    }));
                  }}
                >
                  <type.icon className="type-icon" />
                  <span>{type.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="filter-section">
            <label>置信度范围</label>
            <div className="confidence-range">
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={filters.confidence.min}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  confidence: { ...prev.confidence, min: parseFloat(e.target.value) }
                }))}
              />
              <span>{filters.confidence.min.toFixed(1)} - {filters.confidence.max.toFixed(1)}</span>
            </div>
          </div>

          <div className="filter-section">
            <label>排序方式</label>
            <div className="sort-controls">
              <select 
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="relevance">相关性</option>
                <option value="date">日期</option>
                <option value="confidence">置信度</option>
              </select>
              
              <Button
                variant="outline"
                size="small"
                icon={sortOrder === 'desc' ? FiTrendingUp : FiTrendingDown}
                onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              >
                {sortOrder === 'desc' ? '降序' : '升序'}
              </Button>
            </div>
          </div>

          <div className="filter-actions">
            <Button
              variant="outline"
              onClick={() => setFilters({
                entityTypes: [],
                documentTypes: [],
                dateRange: { start: null, end: null },
                confidence: { min: 0, max: 1 },
                relevance: { min: 0, max: 1 },
                sources: [],
                tags: []
              })}
            >
              重置筛选
            </Button>
            <Button
              variant="primary"
              onClick={() => handleSearch()}
            >
              应用筛选
            </Button>
          </div>
        </div>
      )}
    </div>
  );

  /**
   * 渲染搜索结果
   */
  const renderSearchResults = () => {
    if (searching) {
      return (
        <div className="search-loading">
          <Loading size="large" />
          <p>正在搜索中...</p>
        </div>
      );
    }

    if (searchResults.length === 0 && searchQuery) {
      return (
        <div className="no-results">
          <FiSearch className="no-results-icon" />
          <h3>未找到相关结果</h3>
          <p>尝试调整搜索关键词或筛选条件</p>
        </div>
      );
    }

    if (searchResults.length === 0) {
      return (
        <div className="empty-state">
          <FiBook className="empty-icon" />
          <h3>开始搜索</h3>
          <p>输入关键词开始搜索知识库内容</p>
        </div>
      );
    }

    return (
      <div className="search-results">
        <div className="results-header">
          <div className="results-info">
            <span>找到 {searchResults.length} 条结果</span>
            <span className="search-time">({Math.round(searchTime)}ms)</span>
          </div>
          
          <div className="results-controls">
            <div className="view-controls">
              <Button
                variant={viewMode === 'list' ? 'primary' : 'outline'}
                size="small"
                icon={FiList}
                onClick={() => setViewMode('list')}
              >
                列表
              </Button>
              <Button
                variant={viewMode === 'grid' ? 'primary' : 'outline'}
                size="small"
                icon={FiGrid}
                onClick={() => setViewMode('grid')}
              >
                网格
              </Button>
              <Button
                variant={viewMode === 'timeline' ? 'primary' : 'outline'}
                size="small"
                icon={FiClock}
                onClick={() => setViewMode('timeline')}
              >
                时间线
              </Button>
            </div>
          </div>
        </div>

        <div className={`results-container ${viewMode}`}>
          {searchResults.map((result, index) => (
            <div
              key={result.id}
              className={`result-item ${selectedResults.has(result.id) ? 'selected' : ''}`}
              onClick={() => handleViewResultDetails(result)}
            >
              <div className="result-checkbox">
                <input
                  type="checkbox"
                  checked={selectedResults.has(result.id)}
                  onChange={(e) => handleResultSelect(result.id, e.target.checked)}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
              
              <div className="result-content">
                <div className="result-header">
                  <h4 className="result-title">{result.title || result.name}</h4>
                  <div className="result-meta">
                    <span className="confidence">置信度: {result.confidence?.toFixed(2)}</span>
                    <span className="relevance">相关性: {result.relevance?.toFixed(2)}</span>
                    <span className="date">{result.date}</span>
                  </div>
                </div>
                
                <p className="result-snippet">{result.snippet || result.description}</p>
                
                <div className="result-footer">
                  <div className="result-tags">
                    {result.tags?.slice(0, 3).map(tag => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </div>
                  <div className="result-actions">
                    <Button variant="ghost" size="small" icon={FiEye} />
                    <Button variant="ghost" size="small" icon={FiCopy} />
                    <Button variant="ghost" size="small" icon={FiShare2} />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  /**
   * 渲染批量操作栏
   */
  const renderBatchActions = () => (
    <div className={`batch-actions-bar ${selectedResults.size > 0 ? 'visible' : ''}`}>
      <div className="batch-info">
        <span>已选择 {selectedResults.size} 项</span>
      </div>
      
      <div className="batch-buttons">
        <Button
          variant="outline"
          size="small"
          onClick={() => handleSelectAll(false)}
        >
          取消全选
        </Button>
        <Button
          variant="primary"
          size="small"
          icon={FiDownload}
          onClick={handleExportResults}
        >
          导出选中
        </Button>
        <Button
          variant="outline"
          size="small"
          icon={FiBookmark}
          onClick={handleSaveSearch}
        >
          保存搜索
        </Button>
      </div>
    </div>
  );

  // 初始化数据
  useEffect(() => {
    const loadSearchHistory = async () => {
      if (currentKnowledgeBase) {
        try {
          const history = await getSearchHistory(currentKnowledgeBase.id);
          setSearchHistory(history);
        } catch (error) {
          console.warn('加载搜索历史失败:', error);
        }
      }
    };
    
    loadSearchHistory();
  }, [currentKnowledgeBase]);

  return (
    <ErrorBoundary>
      <div className="enhanced-search">
        {/* 页面头部 */}
        <div className="page-header">
          <div className="header-content">
            <h1>高级搜索</h1>
            <div className="header-actions">
              <Button 
                variant="outline"
                icon={FiHelpCircle}
                onClick={() => setShowAdvanced(true)}
              >
                使用帮助
              </Button>
              <Button 
                variant="outline"
                icon={FiBookmark}
                onClick={handleSaveSearch}
                disabled={!searchQuery.trim()}
              >
                保存搜索
              </Button>
            </div>
          </div>
        </div>

        {/* 主要内容区域 */}
        <div className="main-content">
          {/* 搜索区域 */}
          <div className="search-area">
            {renderSearchBox()}
            {renderFilterPanel()}
          </div>

          {/* 结果区域 */}
          <div className="results-area">
            {renderSearchResults()}
          </div>
        </div>

        {/* 批量操作栏 */}
        {renderBatchActions()}

        {/* 高级搜索模态框 */}
        <Modal
          isOpen={showAdvanced}
          onClose={() => setShowAdvanced(false)}
          title="高级搜索设置"
          size="large"
        >
          <div className="advanced-content">
            <h3>搜索历史</h3>
            <div className="search-history">
              {searchHistory.slice(0, 5).map(history => (
                <div key={history.id} className="history-item">
                  <span className="query">{history.query}</span>
                  <span className="count">{history.resultCount} 条结果</span>
                  <span className="time">{history.timestamp}</span>
                  <Button
                    variant="ghost"
                    size="small"
                    onClick={() => handleQuickSearch(history.query)}
                  >
                    重新搜索
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </Modal>

        {/* 结果详情模态框 */}
        <Modal
          isOpen={showResultDetails}
          onClose={() => setShowResultDetails(false)}
          title="搜索结果详情"
          size="large"
        >
          {currentResult && (
            <div className="result-details">
              <h3>{currentResult.title}</h3>
              <div className="detail-meta">
                <span>置信度: {currentResult.confidence}</span>
                <span>相关性: {currentResult.relevance}</span>
                <span>日期: {currentResult.date}</span>
              </div>
              <div className="detail-content">
                {currentResult.content || currentResult.description}
              </div>
            </div>
          )}
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

export default EnhancedSearch;