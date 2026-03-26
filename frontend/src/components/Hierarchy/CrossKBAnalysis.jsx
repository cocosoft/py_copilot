import React, { useState, useEffect } from 'react';
import './CrossKBAnalysis.css';

/**
 * 跨知识库分析组件
 * 用于分析不同知识库之间的实体关系和分布
 */
const CrossKBAnalysis = () => {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState('entityDistribution');
  const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState([]);
  const [knowledgeBases, setKnowledgeBases] = useState([]);

  /**
   * 加载分析数据
   */
  useEffect(() => {
    const loadAnalysisData = async () => {
      try {
        setLoading(true);
        setError(null);
        // 模拟API调用
        // 实际项目中应该调用真实的API
        const mockAnalysisData = {
          knowledgeBases: [
            { id: 'kb1', name: '技术知识库' },
            { id: 'kb2', name: '数据知识库' },
            { id: 'kb3', name: '云服务知识库' }
          ],
          entityDistribution: [
            { type: '领域', kb1: 5, kb2: 3, kb3: 2, total: 10 },
            { type: '技术', kb1: 15, kb2: 8, kb3: 12, total: 35 },
            { type: '架构', kb1: 3, kb2: 2, kb3: 8, total: 13 },
            { type: '设备', kb1: 2, kb2: 4, kb3: 1, total: 7 },
            { type: '组织', kb1: 1, kb2: 2, kb3: 1, total: 4 }
          ],
          entityOverlap: {
            totalEntities: 60,
            uniqueEntities: 45,
            overlapCount: 15,
            overlapPercentage: 25,
            commonEntities: [
              { id: '1', label: '人工智能', count: 3 },
              { id: '2', label: '大数据', count: 2 },
              { id: '3', label: '云计算', count: 2 }
            ]
          },
          relationAnalysis: [
            { relation: '包含', count: 25, percentage: 35 },
            { relation: '相关', count: 18, percentage: 25 },
            { relation: '应用于', count: 12, percentage: 17 },
            { relation: '使用', count: 10, percentage: 14 },
            { relation: '支持', count: 6, percentage: 9 }
          ],
          knowledgeBaseStats: [
            { id: 'kb1', name: '技术知识库', entities: 26, relations: 45, documents: 12 },
            { id: 'kb2', name: '数据知识库', entities: 19, relations: 28, documents: 8 },
            { id: 'kb3', name: '云服务知识库', entities: 25, relations: 32, documents: 10 }
          ]
        };

        // 模拟网络延迟
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setAnalysisData(mockAnalysisData);
        setKnowledgeBases(mockAnalysisData.knowledgeBases);
        setSelectedKnowledgeBases(mockAnalysisData.knowledgeBases.map(kb => kb.id));
      } catch (err) {
        setError('加载分析数据失败');
        console.error('加载分析数据失败:', err);
      } finally {
        setLoading(false);
      }
    };

    loadAnalysisData();
  }, []);

  /**
   * 处理知识库选择变更
   * @param {Event} e - 输入事件
   */
  const handleKnowledgeBaseChange = (e) => {
    const { value, checked } = e.target;
    if (checked) {
      setSelectedKnowledgeBases(prev => [...prev, value]);
    } else {
      setSelectedKnowledgeBases(prev => prev.filter(id => id !== value));
    }
  };

  /**
   * 渲染实体分布分析
   */
  const renderEntityDistribution = () => {
    if (!analysisData) return null;

    return (
      <div className="analysis-section">
        <h4>实体类型分布</h4>
        <div className="distribution-table-container">
          <table className="distribution-table">
            <thead>
              <tr>
                <th>实体类型</th>
                {knowledgeBases.map(kb => (
                  <th key={kb.id}>{kb.name}</th>
                ))}
                <th>总计</th>
              </tr>
            </thead>
            <tbody>
              {analysisData.entityDistribution.map((item, index) => (
                <tr key={index}>
                  <td>{item.type}</td>
                  {knowledgeBases.map(kb => (
                    <td key={kb.id}>{item[kb.id]}</td>
                  ))}
                  <td className="total-cell">{item.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="distribution-chart">
          {analysisData.entityDistribution.map((item, index) => {
            const maxTotal = Math.max(...analysisData.entityDistribution.map(d => d.total));
            const width = (item.total / maxTotal) * 100;
            return (
              <div key={index} className="distribution-bar">
                <span className="bar-label">{item.type}</span>
                <div className="bar-container">
                  <div 
                    className="bar-fill"
                    style={{ 
                      width: `${width}%`,
                      backgroundColor: getBarColor(index)
                    }}
                  ></div>
                </div>
                <span className="bar-value">{item.total}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  /**
   * 渲染实体重叠分析
   */
  const renderEntityOverlap = () => {
    if (!analysisData) return null;

    const { entityOverlap } = analysisData;

    return (
      <div className="analysis-section">
        <h4>实体重叠分析</h4>
        <div className="overlap-stats">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <span className="stat-value">{entityOverlap.totalEntities}</span>
              <span className="stat-label">总实体数</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🔍</div>
            <div className="stat-content">
              <span className="stat-value">{entityOverlap.uniqueEntities}</span>
              <span className="stat-label">唯一实体数</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🔄</div>
            <div className="stat-content">
              <span className="stat-value">{entityOverlap.overlapCount}</span>
              <span className="stat-label">重叠实体数</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <span className="stat-value">{entityOverlap.overlapPercentage}%</span>
              <span className="stat-label">重叠率</span>
            </div>
          </div>
        </div>
        <div className="common-entities">
          <h5>跨知识库常见实体</h5>
          <ul className="common-entities-list">
            {entityOverlap.commonEntities.map((entity, index) => (
              <li key={index} className="common-entity-item">
                <span className="entity-name">{entity.label}</span>
                <span className="entity-count">出现在 {entity.count} 个知识库中</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  /**
   * 渲染关系分析
   */
  const renderRelationAnalysis = () => {
    if (!analysisData) return null;

    return (
      <div className="analysis-section">
        <h4>关系类型分析</h4>
        <div className="relation-chart">
          {analysisData.relationAnalysis.map((item, index) => (
            <div key={index} className="relation-item">
              <div className="relation-info">
                <span className="relation-name">{item.relation}</span>
                <span className="relation-count">{item.count}</span>
              </div>
              <div className="relation-bar-container">
                <div 
                  className="relation-bar-fill"
                  style={{ 
                    width: `${item.percentage}%`,
                    backgroundColor: getBarColor(index)
                  }}
                ></div>
              </div>
              <span className="relation-percentage">{item.percentage}%</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  /**
   * 渲染知识库统计
   */
  const renderKnowledgeBaseStats = () => {
    if (!analysisData) return null;

    return (
      <div className="analysis-section">
        <h4>知识库统计</h4>
        <div className="kb-stats-grid">
          {analysisData.knowledgeBaseStats.map((kb, index) => (
            <div key={kb.id} className="kb-stat-card">
              <div className="kb-stat-header">
                <h5>{kb.name}</h5>
                <span className="kb-id">ID: {kb.id}</span>
              </div>
              <div className="kb-stat-body">
                <div className="kb-stat-item">
                  <span className="kb-stat-label">实体数:</span>
                  <span className="kb-stat-value">{kb.entities}</span>
                </div>
                <div className="kb-stat-item">
                  <span className="kb-stat-label">关系数:</span>
                  <span className="kb-stat-value">{kb.relations}</span>
                </div>
                <div className="kb-stat-item">
                  <span className="kb-stat-label">文档数:</span>
                  <span className="kb-stat-value">{kb.documents}</span>
                </div>
                <div className="kb-stat-item">
                  <span className="kb-stat-label">实体/文档:</span>
                  <span className="kb-stat-value">{((kb.entities / kb.documents) * 10).toFixed(1)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  /**
   * 获取柱状图颜色
   * @param {number} index - 索引
   * @returns {string} 颜色值
   */
  const getBarColor = (index) => {
    const colors = ['#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#e74c3c'];
    return colors[index % colors.length];
  };

  if (loading) {
    return (
      <div className="cross-kb-analysis">
        <div className="cka-loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cross-kb-analysis">
        <div className="cka-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="cross-kb-analysis">
      <div className="cka-header">
        <h3>跨知识库分析</h3>
        <div className="cka-controls">
          <div className="analysis-type-selector">
            <label>分析类型:</label>
            <select 
              value={selectedAnalysisType} 
              onChange={(e) => setSelectedAnalysisType(e.target.value)}
            >
              <option value="entityDistribution">实体类型分布</option>
              <option value="entityOverlap">实体重叠分析</option>
              <option value="relationAnalysis">关系类型分析</option>
              <option value="knowledgeBaseStats">知识库统计</option>
            </select>
          </div>
          <div className="knowledge-base-selector">
            <label>选择知识库:</label>
            <div className="kb-checkboxes">
              {knowledgeBases.map(kb => (
                <div key={kb.id} className="kb-checkbox-item">
                  <input
                    type="checkbox"
                    id={`kb-${kb.id}`}
                    value={kb.id}
                    checked={selectedKnowledgeBases.includes(kb.id)}
                    onChange={handleKnowledgeBaseChange}
                  />
                  <label htmlFor={`kb-${kb.id}`}>{kb.name}</label>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="cka-content">
        {selectedAnalysisType === 'entityDistribution' && renderEntityDistribution()}
        {selectedAnalysisType === 'entityOverlap' && renderEntityOverlap()}
        {selectedAnalysisType === 'relationAnalysis' && renderRelationAnalysis()}
        {selectedAnalysisType === 'knowledgeBaseStats' && renderKnowledgeBaseStats()}
      </div>
    </div>
  );
};

export default CrossKBAnalysis;