import React, { useState, useEffect } from 'react';
import './FragmentEntityList.css';

/**
 * 片段级实体列表组件
 * 用于展示片段中的实体列表，支持搜索、过滤和排序
 */
const FragmentEntityList = ({ fragmentId, onEntityClick }) => {
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('all');
  const [sortField, setSortField] = useState('text');
  const [sortDirection, setSortDirection] = useState('asc');

  /**
   * 加载实体数据
   */
  useEffect(() => {
    const loadEntities = async () => {
      try {
        setLoading(true);
        setError(null);
        // 模拟API调用
        // 实际项目中应该调用真实的API
        const mockEntities = [
          {
            id: '1',
            text: '人工智能',
            type: '领域',
            start: 2,
            end: 6,
            confidence: 0.95
          },
          {
            id: '2',
            text: '机器学习',
            type: '技术',
            start: 8,
            end: 12,
            confidence: 0.92
          },
          {
            id: '3',
            text: '深度学习',
            type: '技术',
            start: 22,
            end: 26,
            confidence: 0.90
          },
          {
            id: '4',
            text: '多层神经网络',
            type: '技术',
            start: 38,
            end: 44,
            confidence: 0.88
          },
          {
            id: '5',
            text: '计算机',
            type: '设备',
            start: 14,
            end: 17,
            confidence: 0.93
          }
        ];

        // 模拟网络延迟
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setEntities(mockEntities);
      } catch (err) {
        setError('加载实体数据失败');
        console.error('加载实体数据失败:', err);
      } finally {
        setLoading(false);
      }
    };

    if (fragmentId) {
      loadEntities();
    }
  }, [fragmentId]);

  /**
   * 处理搜索查询变化
   * @param {Event} e - 输入事件
   */
  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  /**
   * 处理实体类型过滤变化
   * @param {Event} e - 选择事件
   */
  const handleTypeFilterChange = (e) => {
    setEntityTypeFilter(e.target.value);
  };

  /**
   * 处理排序字段变化
   * @param {string} field - 排序字段
   */
  const handleSortChange = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  /**
   * 过滤和排序实体
   */
  const filteredAndSortedEntities = () => {
    let result = [...entities];

    // 过滤
    if (searchQuery) {
      result = result.filter(entity => 
        entity.text.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (entityTypeFilter !== 'all') {
      result = result.filter(entity => entity.type === entityTypeFilter);
    }

    // 排序
    result.sort((a, b) => {
      let comparison = 0;
      if (sortField === 'text') {
        comparison = a.text.localeCompare(b.text);
      } else if (sortField === 'type') {
        comparison = a.type.localeCompare(b.type);
      } else if (sortField === 'position') {
        comparison = a.start - b.start;
      } else if (sortField === 'confidence') {
        comparison = b.confidence - a.confidence;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return result;
  };

  /**
   * 获取实体类型列表
   */
  const getEntityTypes = () => {
    const types = new Set(entities.map(entity => entity.type));
    return Array.from(types);
  };

  if (loading) {
    return (
      <div className="fragment-entity-list">
        <div className="fel-loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fragment-entity-list">
        <div className="fel-error">{error}</div>
      </div>
    );
  }

  const filteredEntities = filteredAndSortedEntities();
  const entityTypes = getEntityTypes();

  return (
    <div className="fragment-entity-list">
      <div className="fel-header">
        <h3>片段实体列表</h3>
        <div className="fel-controls">
          <div className="fel-search">
            <input
              type="text"
              placeholder="搜索实体..."
              value={searchQuery}
              onChange={handleSearchChange}
            />
          </div>
          
          <div className="fel-filter">
            <select 
              value={entityTypeFilter} 
              onChange={handleTypeFilterChange}
            >
              <option value="all">所有类型</option>
              {entityTypes.map((type, index) => (
                <option key={`fel-type-${type}-${index}`} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="fel-table-container">
        <table className="fel-table">
          <thead>
            <tr>
              <th 
                className={`sortable ${sortField === 'text' ? `sorted-${sortDirection}` : ''}`}
                onClick={() => handleSortChange('text')}
              >
                实体名称
                {sortField === 'text' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th 
                className={`sortable ${sortField === 'type' ? `sorted-${sortDirection}` : ''}`}
                onClick={() => handleSortChange('type')}
              >
                实体类型
                {sortField === 'type' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th 
                className={`sortable ${sortField === 'position' ? `sorted-${sortDirection}` : ''}`}
                onClick={() => handleSortChange('position')}
              >
                位置
                {sortField === 'position' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th 
                className={`sortable ${sortField === 'confidence' ? `sorted-${sortDirection}` : ''}`}
                onClick={() => handleSortChange('confidence')}
              >
                置信度
                {sortField === 'confidence' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {filteredEntities.length > 0 ? (
              filteredEntities.map((entity, index) => (
                <tr
                  key={`fel-entity-${entity.id}-${index}`}
                  className="entity-row"
                  onClick={() => onEntityClick && onEntityClick(entity)}
                >
                  <td className="entity-text">{entity.text}</td>
                  <td>
                    <span className={`entity-type-badge entity-type-${entity.type.toLowerCase()}`}>
                      {entity.type}
                    </span>
                  </td>
                  <td>{entity.start}-{entity.end}</td>
                  <td>
                    <div className="confidence-bar">
                      <div 
                        className="confidence-fill" 
                        style={{ width: `${entity.confidence * 100}%` }}
                      />
                      <span className="confidence-value">{Math.round(entity.confidence * 100)}%</span>
                    </div>
                  </td>
                  <td>
                    <button 
                      className="action-button"
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log('编辑实体:', entity);
                      }}
                    >
                      编辑
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="no-entities">
                  没有找到匹配的实体
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="fel-footer">
        <span className="entity-count">
          共 {filteredEntities.length} 个实体
        </span>
      </div>
    </div>
  );
};

export default FragmentEntityList;