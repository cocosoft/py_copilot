import React from 'react';
import './GlobalStatistics.css';

const GlobalStatistics = ({ stats }) => {
  if (!stats) {
    return <div className="loading">加载统计数据中...</div>;
  }

  const getEntityTypeColor = (type) => {
    switch (type) {
      case 'person': return '#ffc107';
      case 'organization': return '#28a745';
      case 'location': return '#007bff';
      case 'date': return '#dc3545';
      case 'other': return '#7b1fa2';
      default: return '#6c757d';
    }
  };

  return (
    <div className="global-statistics">
      <div className="stats-header">
        <h3>全局统计分析</h3>
      </div>
      
      <div className="stats-overview">
        <div className="stat-card">
          <div className="stat-icon kb-icon">📚</div>
          <div className="stat-info">
            <div className="stat-value">{stats.totalKnowledgeBases}</div>
            <div className="stat-label">知识库总数</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon entity-icon">📊</div>
          <div className="stat-info">
            <div className="stat-value">{stats.totalEntities}</div>
            <div className="stat-label">实体总数</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon relation-icon">🔗</div>
          <div className="stat-info">
            <div className="stat-value">{stats.totalRelations}</div>
            <div className="stat-label">关系总数</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon document-icon">📄</div>
          <div className="stat-info">
            <div className="stat-value">{stats.totalDocuments}</div>
            <div className="stat-label">文档总数</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon chunk-icon">📑</div>
          <div className="stat-info">
            <div className="stat-value">{stats.totalChunks}</div>
            <div className="stat-label">片段总数</div>
          </div>
        </div>
      </div>
      
      <div className="top-knowledge-bases">
        <h4>Top 知识库</h4>
        <div className="kb-ranking">
          {stats.topKnowledgeBases.map((kb, index) => (
            <div key={kb.id} className="kb-rank-item">
              <div className="rank-number">{index + 1}</div>
              <div className="rank-info">
                <div className="kb-name">{kb.name}</div>
                <div className="kb-stats">
                  <span>{kb.entityCount} 个实体</span>
                  <span>{kb.relationCount} 个关系</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="entity-type-distribution">
        <h4>实体类型分布</h4>
        <div className="distribution-chart">
          {stats.entityTypeDistribution.map((item, index) => (
            <div key={index} className="distribution-item">
              <div 
                className="distribution-bar"
                style={{
                  width: `${(item.count / stats.totalEntities) * 100}%`,
                  backgroundColor: getEntityTypeColor(item.type)
                }}
              ></div>
              <div className="distribution-info">
                <span className="type-name">
                  {item.type === 'person' && '人物'}
                  {item.type === 'organization' && '组织'}
                  {item.type === 'location' && '地点'}
                  {item.type === 'date' && '日期'}
                  {item.type === 'other' && '其他'}
                </span>
                <span className="type-count">{item.count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="stats-insights">
        <h4>全局数据洞察</h4>
        <div className="insights-grid">
          <div className="insight-item">
            <div className="insight-icon">📈</div>
            <div className="insight-content">
              <h5>知识库平均规模</h5>
              <p>平均每个知识库包含 {Math.round(stats.totalEntities / stats.totalKnowledgeBases)} 个实体</p>
            </div>
          </div>
          <div className="insight-item">
            <div className="insight-icon">🔍</div>
            <div className="insight-content">
              <h5>关系网络密度</h5>
              <p>平均每个实体参与 {Math.round(stats.totalRelations / stats.totalEntities)} 个关系</p>
            </div>
          </div>
          <div className="insight-item">
            <div className="insight-icon">📋</div>
            <div className="insight-content">
              <h5>文档处理效率</h5>
              <p>平均每篇文档被分割为 {Math.round(stats.totalChunks / stats.totalDocuments)} 个片段</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlobalStatistics;