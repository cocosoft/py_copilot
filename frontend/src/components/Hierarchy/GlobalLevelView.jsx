import React, { useState, useEffect } from 'react';
import GlobalEntityList from './GlobalEntityList';
import GlobalGraph from './GlobalGraph';
import CrossKBAnalysis from './CrossKBAnalysis';
import './GlobalLevelView.css';

/**
 * 全局级视图组件
 * 用于展示跨知识库的全局实体和关系
 */
const GlobalLevelView = () => {
  const [viewMode, setViewMode] = useState('graph'); // 'graph' | 'list' | 'analysis'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  /**
   * 加载全局统计数据
   */
  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        setError(null);
        // 模拟API调用
        // 实际项目中应该调用真实的API
        const mockStats = {
          knowledgeBaseCount: 5,
          documentCount: 120,
          entityCount: 3500,
          relationCount: 2800,
          averageEntitiesPerDocument: 29.2,
          averageRelationsPerDocument: 23.3
        };

        // 模拟网络延迟
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setStats(mockStats);
      } catch (err) {
        setError('加载全局统计数据失败');
        console.error('加载全局统计数据失败:', err);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="global-level-view">
        <div className="glv-loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="global-level-view">
        <div className="glv-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="global-level-view">
      <div className="glv-header">
        <h2>全局级视图</h2>
        <div className="glv-breadcrumb">
          <span>全局</span>
        </div>
      </div>

      <div className="glv-stats">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">🏛️</div>
            <div className="stat-content">
              <span className="stat-value">{stats.knowledgeBaseCount}</span>
              <span className="stat-label">知识库数量</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📄</div>
            <div className="stat-content">
              <span className="stat-value">{stats.documentCount}</span>
              <span className="stat-label">文档数量</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🏷️</div>
            <div className="stat-content">
              <span className="stat-value">{stats.entityCount}</span>
              <span className="stat-label">实体数量</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🔗</div>
            <div className="stat-content">
              <span className="stat-value">{stats.relationCount}</span>
              <span className="stat-label">关系数量</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <span className="stat-value">{stats.averageEntitiesPerDocument.toFixed(1)}</span>
              <span className="stat-label">平均实体数/文档</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🔄</div>
            <div className="stat-content">
              <span className="stat-value">{stats.averageRelationsPerDocument.toFixed(1)}</span>
              <span className="stat-label">平均关系数/文档</span>
            </div>
          </div>
        </div>
      </div>

      <div className="glv-content">
        <div className="glv-view-modes">
          <button
            className={`view-mode-button ${viewMode === 'graph' ? 'active' : ''}`}
            onClick={() => setViewMode('graph')}
          >
            全局图谱
          </button>
          <button
            className={`view-mode-button ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            全局实体列表
          </button>
          <button
            className={`view-mode-button ${viewMode === 'analysis' ? 'active' : ''}`}
            onClick={() => setViewMode('analysis')}
          >
            跨知识库分析
          </button>
        </div>

        <div className="glv-view-content">
          {viewMode === 'graph' && (
            <div className="glv-view-panel">
              <GlobalGraph />
            </div>
          )}

          {viewMode === 'list' && (
            <div className="glv-view-panel">
              <GlobalEntityList />
            </div>
          )}

          {viewMode === 'analysis' && (
            <div className="glv-view-panel">
              <CrossKBAnalysis />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GlobalLevelView;