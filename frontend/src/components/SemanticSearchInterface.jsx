import React, { useState, useEffect, useCallback } from 'react';
import './SemanticSearchInterface.css';

const SemanticSearchInterface = ({ 
  knowledgeBaseId,
  onSearchResults,
  onEntitySelect,
  onDocumentSelect,
  searchHistory = []
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [searchFilters, setSearchFilters] = useState({
    entityTypes: [],
    confidenceThreshold: 0.5,
    maxResults: 20,
    includeRelationships: true,
    includeDocuments: true
  });
  const [expandedResults, setExpandedResults] = useState({});
  const [selectedResult, setSelectedResult] = useState(null);

  // 搜索建议
  useEffect(() => {
    if (searchQuery.length > 2) {
      fetchSearchSuggestions(searchQuery);
    } else {
      setSearchSuggestions([]);
    }
  }, [searchQuery]);

  const fetchSearchSuggestions = async (query) => {
    try {
      const response = await fetch('/v1/knowledge-graph/search-suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 5 })
      });
      
      if (response.ok) {
        const suggestions = await response.json();
        setSearchSuggestions(suggestions);
      }
    } catch (err) {
      console.error('获取搜索建议失败:', err);
    }
  };

  const performSemanticSearch = async (query = searchQuery) => {
    if (!query.trim()) return;

    setSearching(true);
    try {
      const response = await fetch('/v1/knowledge-graph/semantic-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          knowledge_base_id: knowledgeBaseId,
          entity_types: searchFilters.entityTypes,
          confidence_threshold: searchFilters.confidenceThreshold,
          max_results: searchFilters.maxResults,
          include_relationships: searchFilters.includeRelationships,
          include_documents: searchFilters.includeDocuments
        })
      });
      
      if (response.ok) {
        const results = await response.json();
        setSearchResults(results);
        if (onSearchResults) onSearchResults(results);
        
        // 保存搜索历史到本地存储
        saveSearchHistory(query);
      } else {
        throw new Error('搜索失败');
      }
    } catch (err) {
      console.error('语义搜索失败:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const saveSearchHistory = (query) => {
    const history = JSON.parse(localStorage.getItem('semanticSearchHistory') || '[]');
    const newHistory = [query, ...history.filter(q => q !== query)].slice(0, 10);
    localStorage.setItem('semanticSearchHistory', JSON.stringify(newHistory));
  };

  const handleSuggestionClick = (suggestion) => {
    setSearchQuery(suggestion.text || suggestion);
    performSemanticSearch(suggestion.text || suggestion);
  };

  const toggleResultExpansion = (resultId) => {
    setExpandedResults(prev => ({
      ...prev,
      [resultId]: !prev[resultId]
    }));
  };

  const handleEntityClick = (entity) => {
    setSelectedResult(entity);
    if (onEntitySelect) onEntitySelect(entity);
  };

  const handleDocumentClick = (document) => {
    setSelectedResult(document);
    if (onDocumentSelect) onDocumentSelect(document);
  };

  const handleFilterChange = (filterType, value) => {
    setSearchFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setSelectedResult(null);
    setSearchSuggestions([]);
  };

  const exportResults = () => {
    const dataStr = JSON.stringify(searchResults, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'semantic-search-results.json';
    link.click();
  };

  const getSearchHistory = () => {
    return JSON.parse(localStorage.getItem('semanticSearchHistory') || '[]');
  };

  const renderEntityResult = (entity, index) => (
    <div key={`entity-${index}`} className="search-result entity-result">
      <div 
        className="result-header"
        onClick={() => toggleResultExpansion(`entity-${index}`)}
      >
        <div className="result-type-badge entity">实体</div>
        <h4 className="result-title">{entity.name || entity.text}</h4>
        <span className="result-confidence">
          置信度: {(entity.confidence * 100).toFixed(1)}%
        </span>
        <span className="expand-icon">
          {expandedResults[`entity-${index}`] ? '▼' : '▶'}
        </span>
      </div>
      
      {expandedResults[`entity-${index}`] && (
        <div className="result-details">
          <div className="detail-row">
            <span className="detail-label">类型:</span>
            <span className="detail-value">{entity.type}</span>
          </div>
          {entity.start && entity.end && (
            <div className="detail-row">
              <span className="detail-label">位置:</span>
              <span className="detail-value">{entity.start}-{entity.end}</span>
            </div>
          )}
          {entity.relationships && entity.relationships.length > 0 && (
            <div className="detail-row">
              <span className="detail-label">关系:</span>
              <div className="relationships">
                {entity.relationships.map((rel, relIndex) => (
                  <span key={relIndex} className="relationship-tag">
                    {rel.relation}: {rel.object}
                  </span>
                ))}
              </div>
            </div>
          )}
          <button 
            className="action-btn"
            onClick={() => handleEntityClick(entity)}
          >
            查看图谱
          </button>
        </div>
      )}
    </div>
  );

  const renderDocumentResult = (document, index) => (
    <div key={`doc-${index}`} className="search-result document-result">
      <div 
        className="result-header"
        onClick={() => toggleResultExpansion(`doc-${index}`)}
      >
        <div className="result-type-badge document">文档</div>
        <h4 className="result-title">{document.title || document.filename}</h4>
        <span className="result-score">
          相似度: {(document.similarity * 100).toFixed(1)}%
        </span>
        <span className="expand-icon">
          {expandedResults[`doc-${index}`] ? '▼' : '▶'}
        </span>
      </div>
      
      {expandedResults[`doc-${index}`] && (
        <div className="result-details">
          <div className="detail-row">
            <span className="detail-label">内容:</span>
            <span className="detail-value">
              {document.content?.substring(0, 200)}...
            </span>
          </div>
          {document.entities && document.entities.length > 0 && (
            <div className="detail-row">
              <span className="detail-label">实体:</span>
              <div className="entities">
                {document.entities.slice(0, 5).map((entity, entIndex) => (
                  <span key={entIndex} className="entity-tag">
                    {entity.text} ({entity.type})
                  </span>
                ))}
                {document.entities.length > 5 && (
                  <span className="more-entities">
                    +{document.entities.length - 5} 更多
                  </span>
                )}
              </div>
            </div>
          )}
          <button 
            className="action-btn"
            onClick={() => handleDocumentClick(document)}
          >
            查看文档
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className="semantic-search-interface">
      <div className="search-header">
        <h3>语义搜索</h3>
        <div className="search-controls">
          <button 
            className="export-btn"
            onClick={exportResults}
            disabled={searchResults.length === 0}
          >
            导出结果
          </button>
          <button 
            className="clear-btn"
            onClick={clearSearch}
            disabled={!searchQuery && searchResults.length === 0}
          >
            清空
          </button>
        </div>
      </div>

      <div className="search-input-section">
        <div className="search-input-container">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="输入搜索关键词..."
            className="search-input"
            onKeyPress={(e) => e.key === 'Enter' && performSemanticSearch()}
          />
          <button 
            className="search-btn"
            onClick={() => performSemanticSearch()}
            disabled={searching || !searchQuery.trim()}
          >
            {searching ? '搜索中...' : '搜索'}
          </button>
        </div>

        {searchSuggestions.length > 0 && (
          <div className="search-suggestions">
            {searchSuggestions.map((suggestion, index) => (
              <div
                key={index}
                className="suggestion-item"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {suggestion.text || suggestion}
                {suggestion.score && (
                  <span className="suggestion-score">
                    {(suggestion.score * 100).toFixed(1)}%
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="search-filters">
        <div className="filter-group">
          <label>实体类型:</label>
          <select 
            multiple
            value={searchFilters.entityTypes}
            onChange={(e) => handleFilterChange('entityTypes', 
              Array.from(e.target.selectedOptions, option => option.value)
            )}
            className="filter-select"
          >
            <option value="PERSON">人物</option>
            <option value="ORGANIZATION">组织</option>
            <option value="LOCATION">地点</option>
            <option value="DATE">日期</option>
            <option value="MONEY">金额</option>
          </select>
        </div>

        <div className="filter-group">
          <label>置信度阈值: {searchFilters.confidenceThreshold}</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={searchFilters.confidenceThreshold}
            onChange={(e) => handleFilterChange('confidenceThreshold', parseFloat(e.target.value))}
            className="filter-slider"
          />
        </div>

        <div className="filter-group">
          <label>最大结果数:</label>
          <input
            type="number"
            min="1"
            max="100"
            value={searchFilters.maxResults}
            onChange={(e) => handleFilterChange('maxResults', parseInt(e.target.value))}
            className="filter-input"
          />
        </div>

        <div className="filter-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={searchFilters.includeRelationships}
              onChange={(e) => handleFilterChange('includeRelationships', e.target.checked)}
            />
            包含关系
          </label>
          <label>
            <input
              type="checkbox"
              checked={searchFilters.includeDocuments}
              onChange={(e) => handleFilterChange('includeDocuments', e.target.checked)}
            />
            包含文档
          </label>
        </div>
      </div>

      <div className="search-results">
        {searching ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <span>正在搜索...</span>
          </div>
        ) : searchResults.length > 0 ? (
          <>
            <div className="results-summary">
              找到 {searchResults.length} 个结果
            </div>
            <div className="results-list">
              {searchResults.map((result, index) => 
                result.type === 'entity' ? 
                  renderEntityResult(result, index) : 
                  renderDocumentResult(result, index)
              )}
            </div>
          </>
        ) : searchQuery ? (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <span>未找到匹配的结果</span>
          </div>
        ) : (
          <div className="initial-state">
            <div className="initial-icon">💡</div>
            <h4>语义搜索提示</h4>
            <ul>
              <li>输入关键词进行语义搜索</li>
              <li>支持自然语言查询</li>
              <li>使用筛选器优化搜索结果</li>
              <li>点击结果查看详细信息</li>
            </ul>
            
            {getSearchHistory().length > 0 && (
              <div className="search-history">
                <h5>搜索历史</h5>
                {getSearchHistory().map((query, index) => (
                  <span 
                    key={index}
                    className="history-item"
                    onClick={() => {
                      setSearchQuery(query);
                      performSemanticSearch(query);
                    }}
                  >
                    {query}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SemanticSearchInterface;