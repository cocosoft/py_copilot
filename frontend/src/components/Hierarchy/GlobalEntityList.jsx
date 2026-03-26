import React, { useState, useEffect, useRef, useCallback } from 'react';
import useKnowledgeStore from '../../stores/knowledgeStore';
import { getEntityHierarchy } from '../../utils/api/hierarchyApi';
import './GlobalEntityList.css';

/**
 * 全局级实体列表组件
 * 用于展示跨知识库的实体列表，支持搜索、过滤和排序
 */
const GlobalEntityList = () => {
  const { setHierarchyLevel, setCurrentEntity, setCurrentKnowledgeBase } = useKnowledgeStore();
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('all');
  const [knowledgeBaseFilter, setKnowledgeBaseFilter] = useState('all');
  const [sortField, setSortField] = useState('text');
  const [sortDirection, setSortDirection] = useState('asc');
  
  // 虚拟滚动相关状态
  const [startIndex, setStartIndex] = useState(0);
  const [endIndex, setEndIndex] = useState(20);
  const itemHeight = 50; // 每个列表项的高度
  const containerRef = useRef(null);
  const listRef = useRef(null);

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
            knowledgeBaseId: 'kb1',
            knowledgeBaseName: '技术知识库',
            documentCount: 25,
            relationCount: 42
          },
          {
            id: '2',
            text: '机器学习',
            type: '技术',
            knowledgeBaseId: 'kb1',
            knowledgeBaseName: '技术知识库',
            documentCount: 30,
            relationCount: 55
          },
          {
            id: '3',
            text: '深度学习',
            type: '技术',
            knowledgeBaseId: 'kb1',
            knowledgeBaseName: '技术知识库',
            documentCount: 22,
            relationCount: 38
          },
          {
            id: '4',
            text: '多层神经网络',
            type: '技术',
            knowledgeBaseId: 'kb1',
            knowledgeBaseName: '技术知识库',
            documentCount: 18,
            relationCount: 30
          },
          {
            id: '5',
            text: '计算机',
            type: '设备',
            knowledgeBaseId: 'kb1',
            knowledgeBaseName: '技术知识库',
            documentCount: 45,
            relationCount: 62
          },
          {
            id: '6',
            text: '数据挖掘',
            type: '技术',
            knowledgeBaseId: 'kb2',
            knowledgeBaseName: '数据知识库',
            documentCount: 28,
            relationCount: 45
          },
          {
            id: '7',
            text: '大数据',
            type: '领域',
            knowledgeBaseId: 'kb2',
            knowledgeBaseName: '数据知识库',
            documentCount: 35,
            relationCount: 58
          },
          {
            id: '8',
            text: '云计算',
            type: '技术',
            knowledgeBaseId: 'kb3',
            knowledgeBaseName: '云服务知识库',
            documentCount: 32,
            relationCount: 50
          },
          {
            id: '9',
            text: '容器',
            type: '技术',
            knowledgeBaseId: 'kb3',
            knowledgeBaseName: '云服务知识库',
            documentCount: 20,
            relationCount: 35
          },
          {
            id: '10',
            text: '微服务',
            type: '架构',
            knowledgeBaseId: 'kb3',
            knowledgeBaseName: '云服务知识库',
            documentCount: 26,
            relationCount: 42
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

    loadEntities();
  }, []);

  /**
   * 处理搜索查询变化
   * @param {Event} e - 输入事件
   */
  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
    setPage(1);
  };

  /**
   * 处理实体类型过滤变化
   * @param {Event} e - 选择事件
   */
  const handleTypeFilterChange = (e) => {
    setEntityTypeFilter(e.target.value);
    setPage(1);
  };

  /**
   * 处理知识库过滤变化
   * @param {Event} e - 选择事件
   */
  const handleKnowledgeBaseFilterChange = (e) => {
    setKnowledgeBaseFilter(e.target.value);
    setPage(1);
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
   * 处理分页变化
   * @param {number} newPage - 新页码
   */
  const handlePageChange = (newPage) => {
    setPage(newPage);
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

    if (knowledgeBaseFilter !== 'all') {
      result = result.filter(entity => entity.knowledgeBaseId === knowledgeBaseFilter);
    }

    // 排序
    result.sort((a, b) => {
      let comparison = 0;
      if (sortField === 'text') {
        comparison = a.text.localeCompare(b.text);
      } else if (sortField === 'type') {
        comparison = a.type.localeCompare(b.type);
      } else if (sortField === 'knowledgeBase') {
        comparison = a.knowledgeBaseName.localeCompare(b.knowledgeBaseName);
      } else if (sortField === 'documentCount') {
        comparison = b.documentCount - a.documentCount;
      } else if (sortField === 'relationCount') {
        comparison = b.relationCount - a.relationCount;
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

  /**
   * 获取知识库列表
   */
  const getKnowledgeBases = () => {
    const kbs = new Map();
    entities.forEach(entity => {
      kbs.set(entity.knowledgeBaseId, entity.knowledgeBaseName);
    });
    return Array.from(kbs.entries()).map(([id, name]) => ({ id, name }));
  };

  /**
   * 分页处理
   */
  const paginatedEntities = () => {
    const filtered = filteredAndSortedEntities();
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filtered.slice(startIndex, endIndex);
  };

  /**
   * 计算总页数
   */
  const totalPages = () => {
    const filtered = filteredAndSortedEntities();
    return Math.ceil(filtered.length / pageSize);
  };

  /**
   * 处理实体点击，实现跨层级查询和跳转
   */
  const handleEntityClick = async (entity) => {
    try {
      // 设置当前实体
      setCurrentEntity(entity);
      // 设置当前知识库
      setCurrentKnowledgeBase({ id: entity.knowledgeBaseId, name: entity.knowledgeBaseName });
      // 切换到知识库级视图
      setHierarchyLevel('knowledge_base');
      
      // 实际项目中可以调用API获取实体的层级信息
      // const hierarchyData = await getEntityHierarchy(entity.id, 'knowledge_base');
      // console.log('实体层级信息:', hierarchyData);
    } catch (error) {
      console.error('跨层级查询失败:', error);
    }
  };

  /**
   * 处理滚动事件，实现虚拟滚动
   */
  const handleScroll = useCallback(() => {
    if (containerRef.current) {
      const { scrollTop, clientHeight } = containerRef.current;
      const newStartIndex = Math.floor(scrollTop / itemHeight);
      const newEndIndex = Math.min(
        newStartIndex + Math.ceil(clientHeight / itemHeight) + 5, // 额外渲染5个元素，提高滚动体验
        filteredAndSortedEntities().length
      );
      
      setStartIndex(newStartIndex);
      setEndIndex(newEndIndex);
    }
  }, [itemHeight]);

  /**
   * 计算可见的实体列表
   */
  const getVisibleEntities = () => {
    const filtered = filteredAndSortedEntities();
    return filtered.slice(startIndex, endIndex);
  };

  if (loading) {
    return (
      <div className="global-entity-list">
        <div className="gel-loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="global-entity-list">
        <div className="gel-error">{error}</div>
      </div>
    );
  }

  const filteredEntities = filteredAndSortedEntities();
  const paginated = paginatedEntities();
  const entityTypes = getEntityTypes();
  const knowledgeBases = getKnowledgeBases();
  const total = totalPages();

  return (
    <div className="global-entity-list">
      <div className="gel-header">
        <h3>全局实体列表</h3>
        <div className="gel-controls">
          <div className="gel-search">
            <input
              type="text"
              placeholder="搜索实体..."
              value={searchQuery}
              onChange={handleSearchChange}
            />
          </div>
          
          <div className="gel-filters">
            <div className="gel-filter">
              <select 
                value={entityTypeFilter} 
                onChange={handleTypeFilterChange}
              >
                <option value="all">所有类型</option>
                {entityTypes.map((type, index) => (
                  <option key={`gel-type-${type}-${index}`} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div className="gel-filter">
              <select 
                value={knowledgeBaseFilter} 
                onChange={handleKnowledgeBaseFilterChange}
              >
                <option value="all">所有知识库</option>
                {knowledgeBases.map((kb, index) => (
                  <option key={`gel-kb-${kb.id}-${index}`} value={kb.id}>{kb.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div 
        className="gel-table-container"
        ref={containerRef}
        onScroll={handleScroll}
        style={{ 
          height: '600px', 
          overflowY: 'auto',
          position: 'relative'
        }}
      >
        <table className="gel-table">
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
                className={`sortable ${sortField === 'knowledgeBase' ? `sorted-${sortDirection}` : ''}`}
                onClick={() => handleSortChange('knowledgeBase')}
              >
                知识库
                {sortField === 'knowledgeBase' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th 
                className={`sortable ${sortField === 'documentCount' ? `sorted-${sortDirection}` : ''}`}
                onClick={() => handleSortChange('documentCount')}
              >
                文档数
                {sortField === 'documentCount' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th 
                className={`sortable ${sortField === 'relationCount' ? `sorted-${sortDirection}` : ''}`}
                onClick={() => handleSortChange('relationCount')}
              >
                关系数
                {sortField === 'relationCount' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody 
            ref={listRef}
            style={{
              height: `${filteredEntities.length * itemHeight}px`,
              position: 'relative'
            }}
          >
            {getVisibleEntities().length > 0 ? (
              getVisibleEntities().map((entity, index) => (
                <tr
                  key={`gel-entity-${entity.id}-${index}`}
                  className="entity-row"
                  style={{
                    position: 'absolute',
                    top: `${(startIndex + index) * itemHeight}px`,
                    width: '100%'
                  }}
                >
                  <td className="entity-text">{entity.text}</td>
                  <td>
                    <span className={`entity-type-badge entity-type-${entity.type.toLowerCase()}`}>
                      {entity.type}
                    </span>
                  </td>
                  <td>{entity.knowledgeBaseName}</td>
                  <td>{entity.documentCount}</td>
                  <td>{entity.relationCount}</td>
                  <td>
                    <button 
                      className="action-button"
                      onClick={() => handleEntityClick(entity)}
                    >
                      查看详情
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="no-entities">
                  没有找到匹配的实体
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="gel-footer">
        <div className="entity-count">
          共 {filteredEntities.length} 个实体
        </div>
      </div>
    </div>
  );
};

export default GlobalEntityList;