/**
 * 文档实体列表组件
 *
 * 用于显示文档级别的实体列表
 */

import React, { useState, useEffect } from 'react';
import { FiFilter, FiSearch, FiChevronDown, FiChevronUp, FiFileText } from 'react-icons/fi';
import { getDocumentEntities } from '../../utils/api/hierarchyApi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import './DocumentEntityList.css';

const DocumentEntityList = ({ knowledgeBaseId, documentId }) => {
  const { setHierarchyLevel, setCurrentEntity } = useKnowledgeStore();
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('all');
  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    if (knowledgeBaseId && documentId) {
      loadEntities();
    }
  }, [knowledgeBaseId, documentId]);

  /**
   * 加载文档实体列表
   */
  const loadEntities = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getDocumentEntities(knowledgeBaseId, {
        document_id: documentId
      });
      setEntities(response.entities || response.nodes || []);
    } catch (err) {
      console.error('加载文档实体失败:', err);
      setError('加载实体失败，请稍后重试');
      // 使用模拟数据
      setEntities([
        { id: 1, name: '张三', type: 'PERSON', confidence: 0.95, occurrences: 5 },
        { id: 2, name: '科技公司', type: 'ORGANIZATION', confidence: 0.92, occurrences: 3 },
        { id: 3, name: '北京', type: 'LOCATION', confidence: 0.98, occurrences: 4 },
        { id: 4, name: '2026年', type: 'DATE', confidence: 0.90, occurrences: 2 },
        { id: 5, name: '人工智能', type: 'CONCEPT', confidence: 0.85, occurrences: 6 },
        { id: 6, name: '李四', type: 'PERSON', confidence: 0.93, occurrences: 3 },
        { id: 7, name: '上海', type: 'LOCATION', confidence: 0.97, occurrences: 2 },
        { id: 8, name: '机器学习', type: 'CONCEPT', confidence: 0.88, occurrences: 4 },
        { id: 9, name: '2025年', type: 'DATE', confidence: 0.91, occurrences: 1 },
        { id: 10, name: '互联网公司', type: 'ORGANIZATION', confidence: 0.89, occurrences: 2 },
        { id: 11, name: '王五', type: 'PERSON', confidence: 0.94, occurrences: 3 },
        { id: 12, name: '深圳', type: 'LOCATION', confidence: 0.96, occurrences: 2 },
      ]);
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
   * 处理实体点击，实现原文跳转功能
   */
  const handleEntityClick = (entity) => {
    // 设置当前实体
    setCurrentEntity(entity);
    // 切换到片段级视图
    setHierarchyLevel('fragment');
  };

  const filteredEntities = filteredAndSortedEntities();
  const pagedEntities = getPagedEntities();
  const totalPages = Math.ceil(filteredEntities.length / pageSize);

  return (
    <div className="document-entity-list">
      <div className="del-header">
        <h3>文档实体列表</h3>
        <div className="del-stats">
          共 <span className="stat-value">{filteredEntities.length}</span> 个实体
        </div>
      </div>

      {/* 搜索和过滤 */}
      <div className="del-filters">
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
              <option key={`doc-type-option-${type}-${index}`} value={type}>
                {getEntityTypeLabel(type)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 实体列表 */}
      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <div className="del-content">
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
                    onClick={() => handleSort('confidence')}
                  >
                    置信度
                    {sortField === 'confidence' && (
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
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {pagedEntities.map((entity, index) => (
                  <tr
                    key={`doc-entity-row-${entity.id}-${index}`}
                    className="entity-row"
                    onClick={() => handleEntityClick(entity)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td className="entity-name">{entity.name}</td>
                    <td>
                      <span className={`entity-type-badge ${entity.type.toLowerCase()}`}>
                        {getEntityTypeLabel(entity.type)}
                      </span>
                    </td>
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
                    <td>{entity.occurrences || 1}</td>
                    <td>
                      <button 
                        className="jump-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEntityClick(entity);
                        }}
                        title="跳转到原文"
                      >
                        <FiFileText />
                      </button>
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
        </div>
      )}
    </div>
  );
};

export default DocumentEntityList;