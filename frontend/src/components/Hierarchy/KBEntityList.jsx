/**
 * 知识库实体列表组件
 *
 * 用于显示知识库级别的实体列表
 */

import React, { useState, useEffect } from 'react';
import { FiFilter, FiSearch, FiChevronDown, FiChevronUp, FiDownload } from 'react-icons/fi';
import './KBEntityList.css';

const KBEntityList = ({ knowledgeBaseId }) => {
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('all');
  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [showAdvancedFilter, setShowAdvancedFilter] = useState(false);
  const [advancedFilter, setAdvancedFilter] = useState({
    minOccurrences: 0,
    minConfidence: 0
  });

  useEffect(() => {
    if (knowledgeBaseId) {
      loadEntities();
    }
  }, [knowledgeBaseId]);

  /**
   * 加载知识库实体列表
   */
  const loadEntities = async () => {
    setLoading(true);
    setError(null);
    try {
      // 这里应该调用API获取实体列表
      // 暂时使用模拟数据
      setEntities([
        { id: 1, name: '张三', type: 'PERSON', occurrences: 15, confidence: 0.95, documents: 5 },
        { id: 2, name: '科技公司', type: 'ORGANIZATION', occurrences: 12, confidence: 0.92, documents: 4 },
        { id: 3, name: '北京', type: 'LOCATION', occurrences: 10, confidence: 0.98, documents: 6 },
        { id: 4, name: '人工智能', type: 'CONCEPT', occurrences: 20, confidence: 0.85, documents: 8 },
        { id: 5, name: '机器学习', type: 'CONCEPT', occurrences: 18, confidence: 0.88, documents: 7 },
        { id: 6, name: '李四', type: 'PERSON', occurrences: 8, confidence: 0.93, documents: 3 },
        { id: 7, name: '上海', type: 'LOCATION', occurrences: 7, confidence: 0.97, documents: 4 },
        { id: 8, name: '互联网公司', type: 'ORGANIZATION', occurrences: 9, confidence: 0.89, documents: 3 },
        { id: 9, name: '2026年', type: 'DATE', occurrences: 6, confidence: 0.90, documents: 2 },
        { id: 10, name: '王五', type: 'PERSON', occurrences: 5, confidence: 0.94, documents: 2 },
        { id: 11, name: '深圳', type: 'LOCATION', occurrences: 4, confidence: 0.96, documents: 2 },
        { id: 12, name: '云计算', type: 'CONCEPT', occurrences: 14, confidence: 0.86, documents: 5 },
      ]);
    } catch (err) {
      console.error('加载知识库实体失败:', err);
      setError('加载实体失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理搜索
   */
  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
  };

  /**
   * 处理排序
   */
  const handleSort = (field) => {
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

    // 搜索过滤
    if (searchQuery) {
      result = result.filter(entity => 
        entity.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // 类型过滤
    if (entityTypeFilter !== 'all') {
      result = result.filter(entity => entity.type === entityTypeFilter);
    }

    // 高级过滤
    if (advancedFilter.minOccurrences > 0) {
      result = result.filter(entity => entity.occurrences >= advancedFilter.minOccurrences);
    }

    if (advancedFilter.minConfidence > 0) {
      result = result.filter(entity => entity.confidence >= advancedFilter.minConfidence);
    }

    // 排序
    result.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) {
        return sortDirection === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortDirection === 'asc' ? 1 : -1;
      }
      return 0;
    });

    return result;
  };

  /**
   * 获取分页数据
   */
  const getPagedEntities = () => {
    const filtered = filteredAndSortedEntities();
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filtered.slice(startIndex, endIndex);
  };

  /**
   * 获取实体类型列表
   */
  const getEntityTypes = () => {
    const types = [...new Set(entities.map(entity => entity.type))];
    return ['all', ...types];
  };

  /**
   * 获取实体类型标签
   */
  const getEntityTypeLabel = (type) => {
    const typeMap = {
      PERSON: '人物',
      ORGANIZATION: '组织',
      ORG: '组织',
      LOCATION: '地点',
      LOC: '地点',
      DATE: '日期',
      MONEY: '金额',
      TECH: '技术',
      PRODUCT: '产品',
      EVENT: '事件',
      CONCEPT: '概念',
      all: '全部'
    };
    return typeMap[type] || type;
  };

  /**
   * 下载实体数据
   */
  const handleDownload = () => {
    const filtered = filteredAndSortedEntities();
    const data = JSON.stringify(filtered, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kb-entities-${knowledgeBaseId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const filteredEntities = filteredAndSortedEntities();
  const pagedEntities = getPagedEntities();
  const totalPages = Math.ceil(filteredEntities.length / pageSize);

  return (
    <div className="kb-entity-list">
      <div className="kb-el-header">
        <h3>知识库实体列表</h3>
        <div className="kb-el-actions">
          <button
            className="action-btn"
            onClick={handleDownload}
            title="下载实体数据"
          >
            <FiDownload /> 下载
          </button>
        </div>
      </div>

      {/* 搜索和过滤 */}
      <div className="kb-el-filters">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <FiSearch className="search-icon" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索实体..."
              className="search-input"
            />
          </div>
        </form>

        <div className="filter-group">
          <label htmlFor="entity-type-filter">实体类型:</label>
          <select
            id="entity-type-filter"
            value={entityTypeFilter}
            onChange={(e) => setEntityTypeFilter(e.target.value)}
            className="type-filter"
          >
            {getEntityTypes().map((type, index) => (
              <option key={`type-option-${type}-${index}`} value={type}>
                {getEntityTypeLabel(type)}
              </option>
            ))}
          </select>
        </div>

        <button
          className="advanced-filter-toggle"
          onClick={() => setShowAdvancedFilter(!showAdvancedFilter)}
        >
          {showAdvancedFilter ? '收起高级过滤' : '高级过滤'}
        </button>
      </div>

      {/* 高级过滤面板 */}
      {showAdvancedFilter && (
        <div className="advanced-filter-panel">
          <div className="filter-row">
            <div className="filter-item">
              <label>最小出现次数:</label>
              <input
                type="number"
                min="0"
                value={advancedFilter.minOccurrences}
                onChange={(e) => setAdvancedFilter({ ...advancedFilter, minOccurrences: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div className="filter-item">
              <label>最小置信度:</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={advancedFilter.minConfidence}
                onChange={(e) => setAdvancedFilter({ ...advancedFilter, minConfidence: parseFloat(e.target.value) || 0 })}
              />
            </div>
          </div>
          <button
            className="reset-filter-btn"
            onClick={() => setAdvancedFilter({ minOccurrences: 0, minConfidence: 0 })}
          >
            重置过滤
          </button>
        </div>
      )}

      {/* 实体列表 */}
      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <div className="kb-el-content">
          <div className="entity-table">
            <table>
              <thead>
                <tr>
                  <th
                    className="sortable"
                    onClick={() => handleSort('name')}
                  >
                    实体名称
                    {sortField === 'name' && (
                      sortDirection === 'asc' ? <FiChevronUp /> : <FiChevronDown />
                    )}
                  </th>
                  <th
                    className="sortable"
                    onClick={() => handleSort('type')}
                  >
                    类型
                    {sortField === 'type' && (
                      sortDirection === 'asc' ? <FiChevronUp /> : <FiChevronDown />
                    )}
                  </th>
                  <th
                    className="sortable"
                    onClick={() => handleSort('occurrences')}
                  >
                    出现次数
                    {sortField === 'occurrences' && (
                      sortDirection === 'asc' ? <FiChevronUp /> : <FiChevronDown />
                    )}
                  </th>
                  <th
                    className="sortable"
                    onClick={() => handleSort('documents')}
                  >
                    涉及文档数
                    {sortField === 'documents' && (
                      sortDirection === 'asc' ? <FiChevronUp /> : <FiChevronDown />
                    )}
                  </th>
                  <th
                    className="sortable"
                    onClick={() => handleSort('confidence')}
                  >
                    置信度
                    {sortField === 'confidence' && (
                      sortDirection === 'asc' ? <FiChevronUp /> : <FiChevronDown />
                    )}
                  </th>
                </tr>
              </thead>
              <tbody>
                {pagedEntities.map((entity, index) => (
                  <tr key={`entity-row-${entity.id}-${index}`} className="entity-row">
                    <td className="entity-name">{entity.name}</td>
                    <td>
                      <span className={`entity-type-badge ${entity.type.toLowerCase()}`}>
                        {getEntityTypeLabel(entity.type)}
                      </span>
                    </td>
                    <td>{entity.occurrences}</td>
                    <td>{entity.documents}</td>
                    <td>
                      <div className="confidence-bar">
                        <div
                          className="confidence-fill"
                          style={{ width: `${(entity.confidence || 0) * 100}%` }}
                        ></div>
                      </div>
                      <span className="confidence-value">
                        {(entity.confidence || 0) * 100}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="page-btn"
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
              >
                首页
              </button>
              <button
                className="page-btn"
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                上一页
              </button>
              <span className="page-info">
                第 {currentPage} 页，共 {totalPages} 页
              </span>
              <button
                className="page-btn"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                下一页
              </button>
              <button
                className="page-btn"
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
              >
                末页
              </button>
            </div>
          )}

          {/* 统计信息 */}
          <div className="kb-el-stats">
            共 <span className="stat-value">{filteredEntities.length}</span> 个实体
          </div>
        </div>
      )}
    </div>
  );
};

export default KBEntityList;