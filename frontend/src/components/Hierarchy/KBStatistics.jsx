/**
 * 知识库统计组件
 *
 * 用于显示知识库级别的统计信息和分析结果
 */

import React, { useState, useEffect } from 'react';
import { FiBarChart2, FiPieChart, FiTrendingUp, FiDownload, FiRefreshCw } from 'react-icons/fi';
import './KBStatistics.css';

const KBStatistics = ({ knowledgeBaseId }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'entity' | 'document' | 'relation'

  useEffect(() => {
    if (knowledgeBaseId) {
      loadStatistics();
    }
  }, [knowledgeBaseId]);

  /**
   * 加载知识库统计数据
   */
  const loadStatistics = async () => {
    setLoading(true);
    setError(null);
    try {
      // 这里应该调用API获取统计数据
      // 暂时使用模拟数据
      setStats({
        overview: {
          documentCount: 25,
          entityCount: 1500,
          relationCount: 800,
          averageEntitiesPerDocument: 60,
          totalWords: 50000,
          uniqueEntities: 800
        },
        entityTypeDistribution: [
          { type: 'CONCEPT', count: 600, percentage: 40 },
          { type: 'PERSON', count: 250, percentage: 16.67 },
          { type: 'ORGANIZATION', count: 200, percentage: 13.33 },
          { type: 'LOCATION', count: 180, percentage: 12 },
          { type: 'DATE', count: 120, percentage: 8 },
          { type: 'MONEY', count: 80, percentage: 5.33 },
          { type: 'OTHER', count: 70, percentage: 4.67 }
        ],
        documentStats: [
          { id: 1, title: '人工智能概述', entityCount: 85, wordCount: 2500, confidence: 0.92 },
          { id: 2, title: '机器学习基础', entityCount: 72, wordCount: 2100, confidence: 0.88 },
          { id: 3, title: '深度学习进阶', entityCount: 90, wordCount: 2800, confidence: 0.94 },
          { id: 4, title: '计算机视觉应用', entityCount: 65, wordCount: 1900, confidence: 0.86 },
          { id: 5, title: '自然语言处理', entityCount: 78, wordCount: 2300, confidence: 0.90 }
        ],
        relationStats: [
          { type: '包含', count: 350, percentage: 43.75 },
          { type: '相关', count: 200, percentage: 25 },
          { type: '属于', count: 150, percentage: 18.75 },
          { type: '研究', count: 50, percentage: 6.25 },
          { type: '开发', count: 30, percentage: 3.75 },
          { type: '其他', count: 20, percentage: 2.5 }
        ],
        trends: {
          entityGrowth: [100, 250, 400, 600, 800, 1000, 1200, 1500],
          documentGrowth: [5, 10, 15, 18, 20, 22, 24, 25],
          months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月']
        }
      });
    } catch (err) {
      console.error('加载知识库统计失败:', err);
      setError('加载统计数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 下载统计数据
   */
  const handleDownload = () => {
    if (!stats) return;
    
    const data = JSON.stringify(stats, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kb-stats-${knowledgeBaseId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  /**
   * 获取实体类型标签
   */
  const getEntityTypeLabel = (type) => {
    const typeMap = {
      CONCEPT: '概念',
      PERSON: '人物',
      ORGANIZATION: '组织',
      LOCATION: '地点',
      DATE: '日期',
      MONEY: '金额',
      OTHER: '其他'
    };
    return typeMap[type] || type;
  };

  /**
   * 渲染概览统计卡片
   */
  const renderOverviewCards = () => {
    if (!stats) return null;

    const overviewData = [
      {
        label: '文档数量',
        value: stats.overview.documentCount,
        icon: '📄',
        color: '#1890ff'
      },
      {
        label: '实体数量',
        value: stats.overview.entityCount,
        icon: '🏷️',
        color: '#52c41a'
      },
      {
        label: '关系数量',
        value: stats.overview.relationCount,
        icon: '🔗',
        color: '#faad14'
      },
      {
        label: '平均实体/文档',
        value: stats.overview.averageEntitiesPerDocument,
        icon: '📊',
        color: '#722ed1'
      },
      {
        label: '总词数',
        value: stats.overview.totalWords.toLocaleString(),
        icon: '📝',
        color: '#13c2c2'
      },
      {
        label: '唯一实体',
        value: stats.overview.uniqueEntities,
        icon: '🔍',
        color: '#eb2f96'
      }
    ];

    return (
      <div className="stats-cards">
        {overviewData.map((item, index) => (
          <div key={index} className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: item.color }}>
              {item.icon}
            </div>
            <div className="stat-info">
              <span className="stat-label">{item.label}</span>
              <span className="stat-value">{item.value}</span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  /**
   * 渲染实体类型分布
   */
  const renderEntityDistribution = () => {
    if (!stats || !stats.entityTypeDistribution) return null;

    return (
      <div className="distribution-chart">
        <h4>实体类型分布</h4>
        <div className="distribution-bars">
          {stats.entityTypeDistribution.map((item, index) => (
            <div key={index} className="distribution-item">
              <div className="distribution-label">
                <span>{getEntityTypeLabel(item.type)}</span>
                <span className="distribution-percentage">{item.percentage.toFixed(2)}%</span>
              </div>
              <div className="distribution-bar">
                <div
                  className="distribution-fill"
                  style={{ 
                    width: `${item.percentage}%`,
                    backgroundColor: getEntityTypeColor(item.type)
                  }}
                ></div>
              </div>
              <div className="distribution-count">{item.count}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  /**
   * 获取实体类型颜色
   */
  const getEntityTypeColor = (type) => {
    const colorMap = {
      CONCEPT: '#1890ff',
      PERSON: '#ff6b6b',
      ORGANIZATION: '#4ecdc4',
      LOCATION: '#45b7d1',
      DATE: '#96ceb4',
      MONEY: '#feca57',
      OTHER: '#999999'
    };
    return colorMap[type] || '#999999';
  };

  /**
   * 渲染文档统计
   */
  const renderDocumentStats = () => {
    if (!stats || !stats.documentStats) return null;

    return (
      <div className="document-stats">
        <h4>文档统计</h4>
        <div className="document-table">
          <table>
            <thead>
              <tr>
                <th>文档标题</th>
                <th>实体数量</th>
                <th>词数</th>
                <th>平均置信度</th>
              </tr>
            </thead>
            <tbody>
              {stats.documentStats.map((doc, index) => (
                <tr key={`doc-stat-${doc.id}-${index}`}>
                  <td>{doc.title}</td>
                  <td>{doc.entityCount}</td>
                  <td>{doc.wordCount}</td>
                  <td>
                    <div className="confidence-bar">
                      <div
                        className="confidence-fill"
                        style={{ width: `${doc.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="confidence-value">{doc.confidence.toFixed(2)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  /**
   * 渲染关系统计
   */
  const renderRelationStats = () => {
    if (!stats || !stats.relationStats) return null;

    return (
      <div className="relation-stats">
        <h4>关系类型分布</h4>
        <div className="relation-chart">
          {stats.relationStats.map((item, index) => (
            <div key={index} className="relation-item">
              <div className="relation-label">
                <span>{item.type}</span>
                <span className="relation-count">{item.count}</span>
              </div>
              <div className="relation-bar">
                <div
                  className="relation-fill"
                  style={{ width: `${item.percentage}%` }}
                ></div>
              </div>
              <div className="relation-percentage">{item.percentage.toFixed(2)}%</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  /**
   * 渲染趋势图表
   */
  const renderTrends = () => {
    if (!stats || !stats.trends) return null;

    return (
      <div className="trends-chart">
        <h4>增长趋势</h4>
        <div className="trends-container">
          <div className="trend-line">
            <h5>实体增长</h5>
            <div className="line-chart">
              {stats.trends.entityGrowth.map((value, index) => (
                <div key={index} className="chart-point">
                  <div 
                    className="point"
                    style={{ 
                      left: `${(index / (stats.trends.entityGrowth.length - 1)) * 100}%`,
                      bottom: `${(value / Math.max(...stats.trends.entityGrowth)) * 100}%`
                    }}
                  ></div>
                  <div 
                    className="point-label"
                    style={{ left: `${(index / (stats.trends.entityGrowth.length - 1)) * 100}%` }}
                  >
                    {value}
                  </div>
                </div>
              ))}
              <div className="chart-line">
                {stats.trends.entityGrowth.map((value, index) => (
                  <div 
                    key={index}
                    className="line-segment"
                    style={{
                      left: `${(index / (stats.trends.entityGrowth.length - 1)) * 100}%`,
                      bottom: `${(value / Math.max(...stats.trends.entityGrowth)) * 100}%`
                    }}
                  ></div>
                ))}
              </div>
              <div className="chart-x-axis">
                {stats.trends.months.map((month, index) => (
                  <div 
                    key={index}
                    className="x-axis-label"
                    style={{ left: `${(index / (stats.trends.months.length - 1)) * 100}%` }}
                  >
                    {month}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="kb-statistics">
      <div className="kb-stats-header">
        <h3>知识库统计分析</h3>
        <div className="stats-actions">
          <button
            className="action-btn"
            onClick={loadStatistics}
            title="刷新数据"
          >
            <FiRefreshCw /> 刷新
          </button>
          <button
            className="action-btn"
            onClick={handleDownload}
            title="下载统计数据"
          >
            <FiDownload /> 下载
          </button>
        </div>
      </div>

      {/* 标签页 */}
      <div className="stats-tabs">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <FiBarChart2 /> 概览
        </button>
        <button
          className={`tab-btn ${activeTab === 'entity' ? 'active' : ''}`}
          onClick={() => setActiveTab('entity')}
        >
          <FiPieChart /> 实体分析
        </button>
        <button
          className={`tab-btn ${activeTab === 'document' ? 'active' : ''}`}
          onClick={() => setActiveTab('document')}
        >
          📄 文档分析
        </button>
        <button
          className={`tab-btn ${activeTab === 'relation' ? 'active' : ''}`}
          onClick={() => setActiveTab('relation')}
        >
          🔗 关系分析
        </button>
      </div>

      {/* 统计内容 */}
      <div className="stats-content">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <div className="overview-tab">
                {renderOverviewCards()}
                {renderTrends()}
              </div>
            )}
            {activeTab === 'entity' && (
              <div className="entity-tab">
                {renderEntityDistribution()}
              </div>
            )}
            {activeTab === 'document' && (
              <div className="document-tab">
                {renderDocumentStats()}
              </div>
            )}
            {activeTab === 'relation' && (
              <div className="relation-tab">
                {renderRelationStats()}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default KBStatistics;