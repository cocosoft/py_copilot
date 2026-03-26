import React, { useState, useEffect } from 'react';
import { FiSearch, FiFilter } from 'react-icons/fi';
import './KnowledgeBaseList.css';

const KnowledgeBaseList = () => {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  const loadKnowledgeBases = async () => {
    setLoading(true);
    try {
      // 这里应该调用API获取知识库列表
      // 暂时使用模拟数据
      const mockKnowledgeBases = [
        { id: 1, name: '技术知识库', entityCount: 300, relationCount: 400, documentCount: 50, created: '2024-01-01' },
        { id: 2, name: '产品知识库', entityCount: 250, relationCount: 350, documentCount: 40, created: '2024-01-02' },
        { id: 3, name: '营销知识库', entityCount: 200, relationCount: 280, documentCount: 35, created: '2024-01-03' },
        { id: 4, name: '客户知识库', entityCount: 180, relationCount: 250, documentCount: 30, created: '2024-01-04' },
        { id: 5, name: '财务知识库', entityCount: 150, relationCount: 200, documentCount: 25, created: '2024-01-05' },
        { id: 6, name: '人力资源知识库', entityCount: 120, relationCount: 180, documentCount: 20, created: '2024-01-06' },
        { id: 7, name: '运营知识库', entityCount: 100, relationCount: 150, documentCount: 18, created: '2024-01-07' },
        { id: 8, name: '销售知识库', entityCount: 90, relationCount: 130, documentCount: 15, created: '2024-01-08' },
        { id: 9, name: '法务知识库', entityCount: 80, relationCount: 120, documentCount: 12, created: '2024-01-09' },
        { id: 10, name: '行政知识库', entityCount: 70, relationCount: 100, documentCount: 10, created: '2024-01-10' },
      ];
      setKnowledgeBases(mockKnowledgeBases);
    } catch (error) {
      console.error('加载知识库列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredKnowledgeBases = knowledgeBases.filter(kb => 
    kb.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const sortedKnowledgeBases = [...filteredKnowledgeBases].sort((a, b) => {
    if (a[sortField] < b[sortField]) return sortOrder === 'asc' ? -1 : 1;
    if (a[sortField] > b[sortField]) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  return (
    <div className="knowledge-base-list">
      <div className="list-header">
        <h3>知识库列表</h3>
        <div className="list-controls">
          <div className="search-box">
            <FiSearch />
            <input 
              type="text"
              placeholder="搜索知识库..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>
      
      <div className="kb-table">
        <div className="table-header">
          <div 
            className="header-cell" 
            onClick={() => handleSort('name')}
          >
            知识库名称
            {sortField === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div 
            className="header-cell" 
            onClick={() => handleSort('entityCount')}
          >
            实体数量
            {sortField === 'entityCount' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div 
            className="header-cell" 
            onClick={() => handleSort('relationCount')}
          >
            关系数量
            {sortField === 'relationCount' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div 
            className="header-cell" 
            onClick={() => handleSort('documentCount')}
          >
            文档数量
            {sortField === 'documentCount' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div 
            className="header-cell" 
            onClick={() => handleSort('created')}
          >
            创建时间
            {sortField === 'created' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
        </div>
        
        <div className="table-body">
          {loading ? (
            <div className="loading">加载中...</div>
          ) : sortedKnowledgeBases.length > 0 ? (
            sortedKnowledgeBases.map((kb, index) => (
              <div key={`kb-list-${kb.id}-${index}`} className="table-row">
                <div className="table-cell">{kb.name}</div>
                <div className="table-cell">{kb.entityCount}</div>
                <div className="table-cell">{kb.relationCount}</div>
                <div className="table-cell">{kb.documentCount}</div>
                <div className="table-cell">{kb.created}</div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <p>没有找到知识库</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBaseList;