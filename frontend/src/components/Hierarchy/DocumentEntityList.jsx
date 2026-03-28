/**
 * 文档实体列表组件
 *
 * 用于显示文档级别的实体列表
 */

import React, { useState, useEffect } from 'react';
import { FiFilter, FiSearch, FiChevronDown, FiChevronUp, FiFileText } from 'react-icons/fi';
import { getDocumentEntitiesDetail } from '../../utils/api/hierarchyApi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import './DocumentEntityList.css';

const DocumentEntityList = ({ knowledgeBaseId, documentId }) => {
  const { setHierarchyLevel, setCurrentEntity } = useKnowledgeStore();
  const [entities, setEntities] = useState([]);
  const [totalEntities, setTotalEntities] = useState(0);
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
    } else {
      // 未选择文档时清空数据
      setEntities([]);
      setTotalEntities(0);
    }
  }, [knowledgeBaseId, documentId, currentPage, entityTypeFilter]);

  /**
   * 加载文档实体列表
   */
  const loadEntities = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getDocumentEntitiesDetail(knowledgeBaseId, documentId, {
        page: currentPage,
        pageSize: pageSize,
        entityType: entityTypeFilter !== 'all' ? entityTypeFilter : ''
      });

      if (response.code === 200 && response.data) {
        // 转换数据格式以适配组件显示
        const entityList = response.data.list || [];
        const formattedEntities = entityList.map(entity => ({
          id: entity.id,
          name: entity.text || entity.name,
          type: entity.type || entity.entity_type,
          confidence: entity.confidence || 0,
          occurrences: entity.occurrences || 1
        }));
        setEntities(formattedEntities);
        // 设置总数（来自API返回的总数）
        setTotalEntities(response.data.total || entityList.length);
      } else {
        setEntities([]);
        setTotalEntities(0);
      }
    } catch (err) {
      console.error('加载文档实体失败:', err);
      setError('加载实体失败，请稍后重试');
      setEntities([]);
      setTotalEntities(0);
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
   * 获取分页数据
   * 注意：API已经返回分页数据，这里只进行搜索和排序
   * 类型筛选已经在API请求时处理
   */
  const getPagedEntities = () => {
    // 由于API已经分页，entities就是当前页的数据
    // 只需要进行搜索过滤和排序
    let result = [...entities];

    // 搜索过滤（前端搜索当前页）
    if (searchQuery) {
      result = result.filter(entity =>
        entity.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
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

  const pagedEntities = getPagedEntities();
  // 使用API返回的总数
  const displayTotal = totalEntities;
  const totalPages = Math.ceil(displayTotal / pageSize);

  return (
    <div className="document-entity-list">
      {/* 标题和统计 - 简化为一行 */}
      <div className="del-header">
        <h3>文档实体列表 <span className="entity-count">({displayTotal})</span></h3>
      </div>

      {/* 搜索、过滤和分页 */}
      <div className="del-toolbar">
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
            onChange={(e) => {
              setEntityTypeFilter(e.target.value);
              setCurrentPage(1); // 切换类型时重置到第一页
            }}
            className="type-filter"
          >
            {getEntityTypes().map((type, index) => (
              <option key={`doc-type-option-${type}-${index}`} value={type}>
                {getEntityTypeLabel(type)}
              </option>
            ))}
          </select>
        </div>

        {/* 分页移到上面 */}
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
              {currentPage}/{totalPages}
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
        </div>
      )}
    </div>
  );
};

export default DocumentEntityList;