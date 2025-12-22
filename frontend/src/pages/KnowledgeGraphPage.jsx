import React, { useState, useEffect } from 'react';
import EnhancedKnowledgeGraph from '../components/EnhancedKnowledgeGraph';
import SemanticSearchInterface from '../components/SemanticSearchInterface';
import './KnowledgeGraphPage.css';

const KnowledgeGraphPage = () => {
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [selectedRelationship, setSelectedRelationship] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [activeTab, setActiveTab] = useState('search'); // 'search' or 'graph'
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);

  // 加载知识库列表
  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  const loadKnowledgeBases = async () => {
    try {
      const response = await fetch('/v1/knowledge/knowledge-bases');
      if (response.ok) {
        const data = await response.json();
        setKnowledgeBases(data.knowledge_bases || []);
        if (data.knowledge_bases && data.knowledge_bases.length > 0) {
          setSelectedKnowledgeBase(data.knowledge_bases[0].id);
        }
      }
    } catch (err) {
      console.error('加载知识库失败:', err);
    }
  };

  const handleSearchResults = (results) => {
    setSearchResults(results);
    
    // 如果有搜索结果，切换到图谱视图
    if (results.length > 0) {
      setActiveTab('graph');
      
      // 从搜索结果中提取实体数据用于图谱展示
      const entities = results
        .filter(result => result.type === 'entity')
        .map(entity => ({
          ...entity,
          id: entity.entity_id || Math.random(),
          name: entity.text || entity.name
        }));
      
      const relationships = results
        .filter(result => result.relationships)
        .flatMap(result => result.relationships)
        .map(rel => ({
          ...rel,
          source: entities.find(e => e.text === rel.subject),
          target: entities.find(e => e.text === rel.object)
        }))
        .filter(rel => rel.source && rel.target);

      setGraphData({
        entities,
        relationships
      });
    }
  };

  const handleEntitySelect = (entity) => {
    setSelectedEntity(entity);
    setSelectedRelationship(null);
    
    // 在搜索结果中高亮相关实体
    if (searchResults.length > 0) {
      const relatedResults = searchResults.filter(result => 
        result.type === 'entity' && result.entity_id === entity.id
      );
      // 可以在这里添加高亮逻辑
    }
  };

  const handleRelationshipSelect = (relationship) => {
    setSelectedRelationship(relationship);
    setSelectedEntity(null);
  };

  const handleDocumentSelect = (document) => {
    setSelectedDocument(document);
    
    // 加载文档的知识图谱
    if (document.document_id) {
      loadDocumentGraph(document.document_id);
    }
  };

  const loadDocumentGraph = async (documentId) => {
    setLoading(true);
    try {
      const response = await fetch(`/v1/knowledge-graph/document/${documentId}/entities`);
      if (response.ok) {
        const data = await response.json();
        setGraphData(data);
        setActiveTab('graph');
      }
    } catch (err) {
      console.error('加载文档图谱失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearSelection = () => {
    setSelectedEntity(null);
    setSelectedRelationship(null);
    setSelectedDocument(null);
  };

  const exportKnowledgeGraph = () => {
    if (!graphData) return;
    
    const data = {
      graph: graphData,
      searchResults: searchResults,
      timestamp: new Date().toISOString(),
      knowledgeBase: selectedKnowledgeBase
    };
    
    const dataStr = JSON.stringify(data, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `knowledge-graph-${new Date().getTime()}.json`;
    link.click();
  };

  return (
    <div className="knowledge-graph-page">
      <div className="page-header">
        <h1>知识图谱管理系统</h1>
        <div className="header-controls">
          <div className="knowledge-base-selector">
            <label>知识库:</label>
            <select 
              value={selectedKnowledgeBase || ''}
              onChange={(e) => setSelectedKnowledgeBase(e.target.value)}
            >
              <option value="">选择知识库</option>
              {knowledgeBases.map(kb => (
                <option key={kb.id} value={kb.id}>
                  {kb.name}
                </option>
              ))}
            </select>
          </div>
          
          <button 
            className="export-btn"
            onClick={exportKnowledgeGraph}
            disabled={!graphData}
          >
            导出图谱数据
          </button>
          
          <button 
            className="clear-btn"
            onClick={clearSelection}
            disabled={!selectedEntity && !selectedRelationship && !selectedDocument}
          >
            清空选择
          </button>
        </div>
      </div>

      <div className="content-area">
        {/* 左侧面板 - 语义搜索 */}
        <div className="left-panel">
          <div className="panel-tabs">
            <button 
              className={`tab-button ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              语义搜索
            </button>
            <button 
              className={`tab-button ${activeTab === 'graph' ? 'active' : ''}`}
              onClick={() => setActiveTab('graph')}
            >
              知识图谱
            </button>
          </div>

          <div className="panel-content">
            {activeTab === 'search' ? (
              <SemanticSearchInterface
                knowledgeBaseId={selectedKnowledgeBase}
                onSearchResults={handleSearchResults}
                onEntitySelect={handleEntitySelect}
                onDocumentSelect={handleDocumentSelect}
              />
            ) : (
              <div className="graph-panel">
                <EnhancedKnowledgeGraph
                  documentId={selectedDocument?.document_id}
                  textContent={selectedDocument?.content}
                  width={600}
                  height={500}
                  onEntitySelect={handleEntitySelect}
                  onRelationshipSelect={handleRelationshipSelect}
                  searchQuery=""
                />
              </div>
            )}
          </div>
        </div>

        {/* 右侧面板 - 详细信息 */}
        <div className="right-panel">
          <div className="details-header">
            <h3>详细信息</h3>
          </div>

          <div className="details-content">
            {selectedEntity && (
              <div className="entity-details">
                <h4>实体信息</h4>
                <div className="detail-section">
                  <div className="detail-item">
                    <span className="label">名称:</span>
                    <span className="value">{selectedEntity.name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">类型:</span>
                    <span className="value">{selectedEntity.type}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">置信度:</span>
                    <span className="value">
                      {selectedEntity.confidence ? 
                        `${(selectedEntity.confidence * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  {selectedEntity.start && selectedEntity.end && (
                    <div className="detail-item">
                      <span className="label">位置:</span>
                      <span className="value">
                        {selectedEntity.start}-{selectedEntity.end}
                      </span>
                    </div>
                  )}
                </div>

                {selectedEntity.relationships && selectedEntity.relationships.length > 0 && (
                  <div className="relationships-section">
                    <h5>关联关系</h5>
                    <div className="relationships-list">
                      {selectedEntity.relationships.map((rel, index) => (
                        <div key={index} className="relationship-item">
                          <span className="relation">{rel.relation}</span>
                          <span className="object">{rel.object}</span>
                          <span className="confidence">
                            {rel.confidence ? `${(rel.confidence * 100).toFixed(1)}%` : ''}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {selectedRelationship && (
              <div className="relationship-details">
                <h4>关系信息</h4>
                <div className="detail-section">
                  <div className="detail-item">
                    <span className="label">关系:</span>
                    <span className="value">{selectedRelationship.relation}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">主体:</span>
                    <span className="value">{selectedRelationship.subject}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">客体:</span>
                    <span className="value">{selectedRelationship.object}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">置信度:</span>
                    <span className="value">
                      {selectedRelationship.confidence ? 
                        `${(selectedRelationship.confidence * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {selectedDocument && (
              <div className="document-details">
                <h4>文档信息</h4>
                <div className="detail-section">
                  <div className="detail-item">
                    <span className="label">标题:</span>
                    <span className="value">{selectedDocument.title || selectedDocument.filename}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">相似度:</span>
                    <span className="value">
                      {selectedDocument.similarity ? 
                        `${(selectedDocument.similarity * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  {selectedDocument.entities && (
                    <div className="detail-item">
                      <span className="label">实体数量:</span>
                      <span className="value">{selectedDocument.entities.length}</span>
                    </div>
                  )}
                </div>

                {selectedDocument.content && (
                  <div className="content-section">
                    <h5>内容预览</h5>
                    <div className="content-preview">
                      {selectedDocument.content.substring(0, 300)}...
                    </div>
                  </div>
                )}
              </div>
            )}

            {!selectedEntity && !selectedRelationship && !selectedDocument && (
              <div className="empty-details">
                <div className="empty-icon">ℹ️</div>
                <p>选择实体、关系或文档查看详细信息</p>
                <ul>
                  <li>在左侧搜索或图谱中选择项目</li>
                  <li>查看实体属性和关系</li>
                  <li>浏览文档内容和关联信息</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 底部状态栏 */}
      <div className="status-bar">
        <div className="status-info">
          <span>知识库: {knowledgeBases.find(kb => kb.id === selectedKnowledgeBase)?.name || '未选择'}</span>
          <span>实体数量: {graphData?.entities?.length || 0}</span>
          <span>关系数量: {graphData?.relationships?.length || 0}</span>
          <span>搜索结果: {searchResults.length}</span>
        </div>
        <div className="status-actions">
          {loading && <span className="loading-text">加载中...</span>}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphPage;