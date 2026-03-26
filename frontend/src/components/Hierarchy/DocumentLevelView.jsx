/**
 * 文档级视图组件
 *
 * 用于显示文档级别的实体和关系
 */

import React, { useState, useEffect } from 'react';
import { FiGrid, FiList, FiLink2 } from 'react-icons/fi';
import { 
  getDocumentEntities,
  getDocumentGraph,
  getDocumentLevelStats
} from '../../utils/api/hierarchyApi';
import DocumentEntityList from './DocumentEntityList';
import DocumentGraph from './DocumentGraph';
import RelationManagement from '../KnowledgeGraph/RelationManagement';
import './DocumentLevelView.css';

const DocumentLevelView = ({ knowledgeBaseId, documentId }) => {
  const [viewMode, setViewMode] = useState('graph'); // 'graph' | 'list' | 'relations'
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [currentDocumentId, setCurrentDocumentId] = useState(documentId);
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    if (knowledgeBaseId) {
      loadStats();
      loadDocuments();
    }
  }, [knowledgeBaseId]);

  useEffect(() => {
    if (currentDocumentId) {
      // 当文档ID变化时，可以在这里加载相关数据
    }
  }, [currentDocumentId]);

  /**
   * 加载文档级统计数据
   */
  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await getDocumentLevelStats(knowledgeBaseId);
      setStats(response);
    } catch (error) {
      console.error('加载文档级统计失败:', error);
      // 使用模拟数据
      setStats({
        documentCount: 50,
        entityCount: 1200,
        relationCount: 800,
        avgEntitiesPerDoc: 24,
        entityTypes: [
          { type: 'person', count: 350 },
          { type: 'organization', count: 250 },
          { type: 'location', count: 200 },
          { type: 'date', count: 150 },
          { type: 'other', count: 250 },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * 加载文档列表
   */
  const loadDocuments = async () => {
    try {
      // 这里应该调用API获取文档列表
      // 暂时使用模拟数据
      setDocuments([
        { id: 1, title: '文档1', entityCount: 25, relationCount: 18 },
        { id: 2, title: '文档2', entityCount: 32, relationCount: 24 },
        { id: 3, title: '文档3', entityCount: 18, relationCount: 12 },
        { id: 4, title: '文档4', entityCount: 45, relationCount: 32 },
        { id: 5, title: '文档5', entityCount: 22, relationCount: 16 },
      ]);
      
      // 如果没有指定文档ID，选择第一个文档
      if (!currentDocumentId && documents.length > 0) {
        setCurrentDocumentId(documents[0].id);
      }
    } catch (error) {
      console.error('加载文档列表失败:', error);
    }
  };

  /**
   * 处理文档选择
   */
  const handleDocumentSelect = (documentId) => {
    setCurrentDocumentId(documentId);
  };

  return (
    <div className="document-level-view">
      <div className="dl-header">
        <h2>文档级视图</h2>
        <div className="view-modes">
          <button 
            className={`mode-btn ${viewMode === 'graph' ? 'active' : ''}`}
            onClick={() => setViewMode('graph')}
          >
            <FiGrid /> 文档图谱
          </button>
          <button 
            className={`mode-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            <FiList /> 实体列表
          </button>
          <button 
            className={`mode-btn ${viewMode === 'relations' ? 'active' : ''}`}
            onClick={() => setViewMode('relations')}
          >
            <FiLink2 /> 关系管理
          </button>
        </div>
      </div>
      
      {loading && stats === null ? (
        <div className="loading">加载中...</div>
      ) : (
        <div className="dl-content">
          {/* 文档选择器 */}
          <div className="document-selector">
            <label htmlFor="document-select">选择文档:</label>
            <select
              id="document-select"
              value={currentDocumentId || ''}
              onChange={(e) => handleDocumentSelect(e.target.value)}
              className="document-select"
            >
              <option value="">请选择文档</option>
              {documents.map(doc => (
                <option key={doc.id} value={doc.id}>
                  {doc.title} ({doc.entityCount}个实体, {doc.relationCount}个关系)
                </option>
              ))}
            </select>
          </div>
          
          {/* 统计信息 */}
          {stats && (
            <div className="dl-stats">
              <div className="stat-item">
                <span className="stat-label">总文档数:</span>
                <span className="stat-value">{stats.documentCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">总实体数:</span>
                <span className="stat-value">{stats.entityCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">总关系数:</span>
                <span className="stat-value">{stats.relationCount}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">平均实体数/文档:</span>
                <span className="stat-value">{stats.avgEntitiesPerDoc}</span>
              </div>
            </div>
          )}
          
          {/* 视图内容 */}
          <div className="dl-view-content">
            {viewMode === 'graph' && (
              <DocumentGraph 
                knowledgeBaseId={knowledgeBaseId} 
                documentId={currentDocumentId} 
              />
            )}
            {viewMode === 'list' && (
              <DocumentEntityList 
                knowledgeBaseId={knowledgeBaseId} 
                documentId={currentDocumentId} 
              />
            )}
            {viewMode === 'relations' && (
              <RelationManagement 
                knowledgeBaseId={knowledgeBaseId} 
                documentId={currentDocumentId} 
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentLevelView;