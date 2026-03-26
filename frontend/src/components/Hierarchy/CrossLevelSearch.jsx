/**
 * 跨层级实体查询组件
 *
 * 允许用户在不同层级之间查询实体，支持跨层级搜索和导航
 */

import React, { useState, useEffect } from 'react';
import { FiSearch, FiFilter, FiX } from 'react-icons/fi';
import { searchEntitiesByLevel, getEntityHierarchy } from '../../utils/api/hierarchyApi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import './CrossLevelSearch.css';

const CrossLevelSearch = ({ knowledgeBaseId }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('knowledge_base');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [entityHierarchy, setEntityHierarchy] = useState(null);
  
  const { setCurrentHierarchyLevel, setHierarchyData, setDrillDownPath } = useKnowledgeStore();

  // 层级选项
  const levelOptions = [
    { value: 'fragment', label: '片段级' },
    { value: 'document', label: '文档级' },
    { value: 'knowledge_base', label: '知识库级' },
    { value: 'global', label: '全局级' }
  ];

  /**
   * 处理搜索提交
   */
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      const results = await searchEntitiesByLevel(selectedLevel, searchQuery, {
        knowledge_base_id: knowledgeBaseId
      });
      setSearchResults(results.entities || results.nodes || []);
    } catch (err) {
      console.error('搜索失败:', err);
      setError('搜索失败，请稍后重试');
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理实体点击，查看层级信息
   */
  const handleEntityClick = async (entity) => {
    setLoading(true);
    try {
      const hierarchy = await getEntityHierarchy(entity.id, selectedLevel);
      setEntityHierarchy({
        entity,
        hierarchy,
        currentLevel: selectedLevel
      });
    } catch (err) {
      console.error('获取实体层级失败:', err);
      setError('获取实体层级失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 导航到指定层级
   */
  const navigateToLevel = (level, entityData) => {
    setCurrentHierarchyLevel(level);
    setHierarchyData({ entity: entityData, knowledgeBaseId });
    setDrillDownPath([{ level: selectedLevel, data: { entity: entityHierarchy.entity } }, { level, data: { entity: entityData } }]);
    setEntityHierarchy(null);
  };

  /**
   * 清除搜索结果
   */
  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setError(null);
    setEntityHierarchy(null);
  };

  return (
    <div className="cross-level-search">
      <div className="search-header">
        <h3>跨层级实体查询</h3>
        <p>在不同层级之间搜索和导航实体</p>
      </div>

      <form onSubmit={handleSearch} className="search-form">
        <div className="form-group">
          <label htmlFor="search-level">搜索层级:</label>
          <select
            id="search-level"
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="level-select"
          >
            {levelOptions.map((option, index) => (
              <option key={`level-option-${option.value}-${index}`} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="search-input-group">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="输入实体名称进行搜索..."
            className="search-input"
          />
          <button type="submit" className="search-btn" disabled={loading}>
            {loading ? '搜索中...' : <FiSearch />}
          </button>
          {searchQuery && (
            <button type="button" className="clear-btn" onClick={clearSearch}>
              <FiX />
            </button>
          )}
        </div>
      </form>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {searchResults.length > 0 && (
        <div className="search-results">
          <h4>搜索结果 ({searchResults.length})</h4>
          <div className="results-list">
            {searchResults.map((entity, index) => (
              <div key={`search-result-${entity.id || ''}-${index}`} className="result-item" onClick={() => handleEntityClick(entity)}>
                <div className="entity-name">{entity.name || entity.label}</div>
                <div className="entity-type">{entity.type || '未知类型'}</div>
                <div className="entity-meta">
                  {entity.confidence && (
                    <span className="confidence">置信度: {(entity.confidence * 100).toFixed(1)}%</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {entityHierarchy && (
        <div className="entity-hierarchy">
          <div className="hierarchy-header">
            <h4>实体层级信息</h4>
            <button className="close-btn" onClick={() => setEntityHierarchy(null)}>
              <FiX />
            </button>
          </div>
          <div className="hierarchy-content">
            <div className="current-entity">
              <h5>{entityHierarchy.entity.name || entityHierarchy.entity.label}</h5>
              <p>类型: {entityHierarchy.entity.type || '未知类型'}</p>
            </div>
            <div className="hierarchy-levels">
              <h6>跨层级导航</h6>
              {levelOptions.map((option, index) => {
                // 跳过当前层级
                if (option.value === entityHierarchy.currentLevel) return null;
                return (
                  <button
                    key={`level-nav-${option.value}-${index}`}
                    className="level-nav-btn"
                    onClick={() => navigateToLevel(option.value, entityHierarchy.entity)}
                  >
                    查看 {option.label} 视图
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CrossLevelSearch;