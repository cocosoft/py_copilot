/**
 * 知识图谱概览面板组件
 * 
 * 展示知识库知识图谱的整体统计信息、实体类型分布、关系类型分布、最近更新动态等
 */

import React, { useState, useEffect } from 'react';
import { 
  getKnowledgeBaseGraphStats, 
  getEntityTypeDistribution, 
  getRelationTypeDistribution 
} from '../../utils/api/knowledgeGraphApi';
import './KnowledgeGraphDashboard.css';

/**
 * 知识图谱概览面板组件
 * 
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @param {string} props.knowledgeBaseName - 知识库名称
 * @param {Object} props.stats - 统计信息
 * @param {boolean} props.loading - 加载状态
 * @param {Function} props.onRefresh - 刷新回调
 * @returns {JSX.Element} 概览面板界面
 */
const KnowledgeGraphDashboard = ({ 
  knowledgeBaseId, 
  knowledgeBaseName, 
  stats, 
  loading, 
  onRefresh 
}) => {
  // 实体类型分布
  const [entityDistribution, setEntityDistribution] = useState([]);
  // 关系类型分布
  const [relationDistribution, setRelationDistribution] = useState([]);
  // 最近活动
  const [recentActivities, setRecentActivities] = useState([]);

  /**
   * 加载分布数据
   */
  const loadDistributionData = async () => {
    if (!knowledgeBaseId) return;

    try {
      // 加载实体类型分布
      const entityRes = await getEntityTypeDistribution(knowledgeBaseId);
      if (entityRes.success) {
        setEntityDistribution(entityRes.data.distribution);
      }

      // 加载关系类型分布
      const relationRes = await getRelationTypeDistribution(knowledgeBaseId);
      if (relationRes.success) {
        setRelationDistribution(relationRes.data.distribution);
      }

      // 加载最近活动
      // TODO: 调用API获取最近活动数据
      setRecentActivities([]);
    } catch (error) {
      console.error('加载分布数据失败:', error);
    }
  };

  useEffect(() => {
    loadDistributionData();
  }, [knowledgeBaseId]);

  /**
   * 格式化数字
   * @param {number} num - 数字
   * @returns {string} 格式化后的字符串
   */
  const formatNumber = (num) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + '万';
    }
    return num.toString();
  };

  /**
   * 格式化日期
   * @param {string} dateString - 日期字符串
   * @returns {string} 格式化后的日期
   */
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  // 颜色配置
  const colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4', '#795548', '#607D8B'];

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <div className="knowledge-graph-dashboard">
      {/* 统计卡片区域 */}
      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-icon entities">🏷️</div>
          <div className="stat-info">
            <span className="stat-value">{stats ? formatNumber(stats.entities_count) : '-'}</span>
            <span className="stat-label">实体总数</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon relations">🔗</div>
          <div className="stat-info">
            <span className="stat-value">{stats ? formatNumber(stats.relationships_count) : '-'}</span>
            <span className="stat-label">关系总数</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon types">📋</div>
          <div className="stat-info">
            <span className="stat-value">{stats ? stats.entity_types_count : '-'}</span>
            <span className="stat-label">实体类型</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon coverage">📊</div>
          <div className="stat-info">
            <span className="stat-value">{stats ? Math.round(stats.coverage * 100) + '%' : '-'}</span>
            <span className="stat-label">图谱覆盖率</span>
          </div>
        </div>
      </div>

      {/* 分布图表区域 */}
      <div className="distribution-section">
        {/* 实体类型分布 */}
        <div className="distribution-card">
          <div className="card-header">
            <h3>实体类型分布</h3>
            <span className="card-subtitle">各类型实体数量占比</span>
          </div>
          <div className="card-body">
            {entityDistribution.length > 0 ? (
              <div className="distribution-chart">
                {/* 水平条形图 */}
                <div className="horizontal-bars">
                  {entityDistribution.map((item, index) => (
                    <div key={item.type} className="bar-item">
                      <div className="bar-label">
                        <span className="label-name">{item.type}</span>
                        <span className="label-value">{item.count} ({item.percentage}%)</span>
                      </div>
                      <div className="bar-track">
                        <div 
                          className="bar-fill"
                          style={{ 
                            width: `${item.percentage}%`,
                            backgroundColor: colors[index % colors.length]
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-chart">
                <span className="empty-icon">📊</span>
                <p>暂无数据</p>
              </div>
            )}
          </div>
        </div>

        {/* 关系类型分布 */}
        <div className="distribution-card">
          <div className="card-header">
            <h3>关系类型分布</h3>
            <span className="card-subtitle">各类型关系数量占比</span>
          </div>
          <div className="card-body">
            {relationDistribution.length > 0 ? (
              <div className="distribution-chart">
                {/* 水平条形图 */}
                <div className="horizontal-bars">
                  {relationDistribution.map((item, index) => (
                    <div key={item.type} className="bar-item">
                      <div className="bar-label">
                        <span className="label-name">{item.type}</span>
                        <span className="label-value">{item.count} ({item.percentage}%)</span>
                      </div>
                      <div className="bar-track">
                        <div 
                          className="bar-fill"
                          style={{ 
                            width: `${item.percentage}%`,
                            backgroundColor: colors[(index + 3) % colors.length]
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-chart">
                <span className="empty-icon">📊</span>
                <p>暂无数据</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 底部区域 */}
      <div className="dashboard-footer">
        {/* 最近更新动态 */}
        <div className="activity-card">
          <div className="card-header">
            <h3>最近更新</h3>
            <button className="refresh-btn" onClick={onRefresh}>
              🔄 刷新
            </button>
          </div>
          <div className="card-body">
            {recentActivities.length > 0 ? (
              <ul className="activity-list">
                {recentActivities.map(activity => (
                  <li key={activity.id} className={`activity-item ${activity.type}`}>
                    <span className="activity-icon">
                      {activity.type === 'entity_added' && '🏷️'}
                      {activity.type === 'relation_added' && '🔗'}
                      {activity.type === 'graph_built' && '🕸️'}
                      {activity.type === 'entity_merged' && '🔀'}
                      {activity.type === 'batch_build' && '⚡'}
                    </span>
                    <span className="activity-message">{activity.message}</span>
                    <span className="activity-time">{activity.time}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="empty-activity">
                <p>暂无更新记录</p>
              </div>
            )}
          </div>
        </div>

        {/* 概览信息 */}
        <div className="overview-card">
          <div className="card-header">
            <h3>概览信息</h3>
          </div>
          <div className="card-body">
            <div className="overview-item">
              <span className="overview-label">知识库名称</span>
              <span className="overview-value">{knowledgeBaseName}</span>
            </div>
            <div className="overview-item">
              <span className="overview-label">最后更新</span>
              <span className="overview-value">{formatDate(stats?.last_updated)}</span>
            </div>
            <div className="overview-item">
              <span className="overview-label">关系类型数</span>
              <span className="overview-value">{stats?.relationship_types_count || '-'} 种</span>
            </div>
            <div className="overview-item">
              <span className="overview-label">平均每个实体关系数</span>
              <span className="overview-value">
                {stats ? (stats.relationships_count / stats.entities_count).toFixed(1) : '-'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphDashboard;
