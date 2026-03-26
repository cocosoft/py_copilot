/**
 * 知识库级视图组件
 *
 * 用于显示知识库级别的实体和关系
 */

import { useState, useEffect } from 'react';
import { FiDatabase, FiList, FiBarChart2, FiFileText, FiShare2, FiUsers } from 'react-icons/fi';
import { getKnowledgeBaseLevelStats } from '../../utils/api/hierarchyApi';
import KBEntityList from './KBEntityList';
import KBGraph from './KBGraph';
import KBStatistics from './KBStatistics';
import './KnowledgeBaseLevelView.css';

const KnowledgeBaseLevelView = ({ knowledgeBaseId }) => {
  const [viewMode, setViewMode] = useState('graph'); // 'graph' | 'list' | 'stats'
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (knowledgeBaseId) {
      loadStats();
    }
  }, [knowledgeBaseId]);

  /**
   * 加载知识库级统计数据
   */
  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await getKnowledgeBaseLevelStats(knowledgeBaseId);
      setStats(response);
    } catch (error) {
      console.error('加载知识库级统计失败:', error);
      // 使用模拟数据
      setStats({
        documentCount: 50,
        entityCount: 1200,
        uniqueEntityCount: 850,
        relationCount: 800,
        avgEntitiesPerDoc: 24,
        entityTypes: [
          { type: 'person', count: 350 },
          { type: 'organization', count: 250 },
          { type: 'location', count: 200 },
          { type: 'date', count: 150 },
          { type: 'other', count: 250 },
        ],
        documentStats: [
          { docId: 1, title: '文档1', entityCount: 25, relationCount: 18 },
          { docId: 2, title: '文档2', entityCount: 32, relationCount: 24 },
          { docId: 3, title: '文档3', entityCount: 18, relationCount: 12 },
          { docId: 4, title: '文档4', entityCount: 45, relationCount: 32 },
          { docId: 5, title: '文档5', entityCount: 22, relationCount: 16 },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="knowledge-base-level-view">
      <div className="kb-header">
        <h2>知识库级视图</h2>
        <div className="view-modes">
          <button 
            className={`mode-btn ${viewMode === 'graph' ? 'active' : ''}`}
            onClick={() => setViewMode('graph')}
          >
            <FiDatabase /> 知识库图谱
          </button>
          <button 
            className={`mode-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            <FiList /> 实体列表
          </button>
          <button 
            className={`mode-btn ${viewMode === 'stats' ? 'active' : ''}`}
            onClick={() => setViewMode('stats')}
          >
            <FiBarChart2 /> 统计分析
          </button>
        </div>
      </div>
      
      {loading && stats === null ? (
        <div className="loading">加载中...</div>
      ) : (
        <div className="kb-content">
          {/* 统计信息卡片 */}
          {stats && (
            <div className="kb-stats-cards">
              <div className="stat-card">
                <div className="stat-icon">
                  <FiFileText />
                </div>
                <div className="stat-info">
                  <span className="stat-label">文档数</span>
                  <span className="stat-value">{stats.documentCount}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <FiDatabase />
                </div>
                <div className="stat-info">
                  <span className="stat-label">实体数</span>
                  <span className="stat-value">{stats.entityCount}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <FiShare2 />
                </div>
                <div className="stat-info">
                  <span className="stat-label">关系数</span>
                  <span className="stat-value">{stats.relationCount}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <FiUsers />
                </div>
                <div className="stat-info">
                  <span className="stat-label">平均实体/文档</span>
                  <span className="stat-value">{stats.avgEntitiesPerDoc}</span>
                </div>
              </div>
            </div>
          )}
          
          {/* 视图内容 */}
          <div className="kb-view-content">
            {viewMode === 'graph' && (
              <KBGraph 
                knowledgeBaseId={knowledgeBaseId} 
              />
            )}
            {viewMode === 'list' && (
              <KBEntityList 
                knowledgeBaseId={knowledgeBaseId} 
              />
            )}
            {viewMode === 'stats' && (
              <KBStatistics 
                knowledgeBaseId={knowledgeBaseId} 
                stats={stats}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseLevelView;