/**
 * 质量评估面板组件 - FE-004 质量评估面板
 *
 * 展示向量化质量评估结果，包括质量分数、异常片段标记、重处理功能
 *
 * @task FE-004
 * @phase 前端功能拓展
 */

import React, { useState, useMemo, useCallback } from 'react';
import './QualityPanel.css';

/**
 * 质量等级配置
 */
const QUALITY_LEVELS = {
  excellent: { color: '#52c41a', label: '优秀', minScore: 90 },
  good: { color: '#1890ff', label: '良好', minScore: 70 },
  fair: { color: '#faad14', label: '一般', minScore: 50 },
  poor: { color: '#ff4d4f', label: '较差', minScore: 0 },
};

/**
 * 获取质量等级
 *
 * @param {number} score - 质量分数
 * @returns {Object} 质量等级配置
 */
const getQualityLevel = (score) => {
  if (score >= QUALITY_LEVELS.excellent.minScore) return QUALITY_LEVELS.excellent;
  if (score >= QUALITY_LEVELS.good.minScore) return QUALITY_LEVELS.good;
  if (score >= QUALITY_LEVELS.fair.minScore) return QUALITY_LEVELS.fair;
  return QUALITY_LEVELS.poor;
};

/**
 * 质量分数卡片组件
 */
const QualityScoreCard = ({ score, title, subtitle }) => {
  const level = getQualityLevel(score);

  return (
    <div className="quality-score-card">
      <div className="score-header">
        <h4>{title}</h4>
        {subtitle && <span className="subtitle">{subtitle}</span>}
      </div>

      <div className="score-content">
        <div
          className="score-circle"
          style={{
            background: `conic-gradient(${level.color} ${score * 3.6}deg, #f0f0f0 0deg)`,
          }}
        >
          <div className="score-inner">
            <span className="score-value" style={{ color: level.color }}>
              {score}
            </span>
            <span className="score-label">分</span>
          </div>
        </div>
        <span className="score-level" style={{ color: level.color }}>
          {level.label}
        </span>
      </div>
    </div>
  );
};

/**
 * 质量分布图表组件（简化版）
 */
const QualityDistributionChart = ({ data }) => {
  const chartData = useMemo(() => {
    return [
      { name: '优秀', value: data.excellent || 0, color: QUALITY_LEVELS.excellent.color },
      { name: '良好', value: data.good || 0, color: QUALITY_LEVELS.good.color },
      { name: '一般', value: data.fair || 0, color: QUALITY_LEVELS.fair.color },
      { name: '较差', value: data.poor || 0, color: QUALITY_LEVELS.poor.color },
    ];
  }, [data]);

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="chart-container">
      <h4 className="chart-title">质量分布</h4>
      <div className="distribution-chart">
        {chartData.map((item, index) => (
          <div key={index} className="distribution-item">
            <div className="distribution-bar-container">
              <div
                className="distribution-bar"
                style={{
                  width: total > 0 ? `${(item.value / total) * 100}%` : '0%',
                  backgroundColor: item.color
                }}
              />
            </div>
            <div className="distribution-info">
              <span className="distribution-name" style={{ color: item.color }}>
                {item.name}
              </span>
              <span className="distribution-value">{item.value}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * 异常片段列表组件
 */
const AnomalyChunkList = ({
  chunks,
  onReprocess,
  onReprocessAll,
  onSelect,
  selectedIds,
  loading,
}) => {
  const [expandedId, setExpandedId] = useState(null);
  const [filter, setFilter] = useState('all');

  const filteredChunks = useMemo(() => {
    if (filter === 'all') return chunks;
    return chunks.filter((chunk) => chunk.anomalyType === filter);
  }, [chunks, filter]);

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getAnomalyLabel = (type) => {
    switch (type) {
      case 'low_quality':
        return '质量过低';
      case 'incomplete':
        return '内容不完整';
      case 'duplicated':
        return '重复内容';
      default:
        return '异常';
    }
  };

  return (
    <div className="anomaly-chunk-list">
      <div className="list-header">
        <h4>
          异常片段
          <span className="count">({filteredChunks.length})</span>
        </h4>

        <div className="list-actions">
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">全部类型</option>
            <option value="low_quality">质量过低</option>
            <option value="incomplete">内容不完整</option>
            <option value="duplicated">重复内容</option>
          </select>

          <button
            className="btn-reprocess-all"
            onClick={onReprocessAll}
            disabled={loading || filteredChunks.length === 0}
          >
            全部重处理
          </button>
        </div>
      </div>

      <div className="chunk-list">
        {filteredChunks.map((chunk) => (
          <div
            key={chunk.id}
            className={`chunk-item ${selectedIds.includes(chunk.id) ? 'selected' : ''}`}
          >
            <div className="chunk-header">
              <input
                type="checkbox"
                checked={selectedIds.includes(chunk.id)}
                onChange={() => onSelect(chunk.id)}
              />

              <div className="chunk-info">
                <span className="chunk-id">片段 #{chunk.id}</span>
                <span className="chunk-source">{chunk.sourceDocument}</span>
              </div>

              <div className="chunk-badges">
                <span
                  className="anomaly-badge"
                  style={{
                    backgroundColor: `${getQualityLevel(chunk.score).color}20`,
                    color: getQualityLevel(chunk.score).color,
                  }}
                >
                  {getAnomalyLabel(chunk.anomalyType)}
                </span>

                <span
                  className="score-badge"
                  style={{
                    backgroundColor: `${getQualityLevel(chunk.score).color}20`,
                    color: getQualityLevel(chunk.score).color,
                  }}
                >
                  {chunk.score}分
                </span>
              </div>

              <button
                className="btn-expand"
                onClick={() => toggleExpand(chunk.id)}
              >
                {expandedId === chunk.id ? '收起' : '展开'}
              </button>
            </div>

            {expandedId === chunk.id && (
              <div className="chunk-details">
                <div className="detail-section">
                  <h5>片段内容</h5>
                  <p className="chunk-content">{chunk.content}</p>
                </div>

                <div className="detail-section">
                  <h5>质量问题</h5>
                  <ul className="issue-list">
                    {chunk.issues?.map((issue, index) => (
                      <li key={index} className={`issue-${issue.severity}`}>
                        {issue.description}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="chunk-actions">
                  <button
                    className="btn-reprocess"
                    onClick={() => onReprocess(chunk.id)}
                    disabled={loading}
                  >
                    重新处理
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * 质量评估面板主组件
 */
const QualityPanel = ({
  documentId,
  qualityData,
  anomalyChunks,
  onReprocess,
  onReprocessAll,
  onReprocessSelected,
  loading,
}) => {
  const [selectedChunks, setSelectedChunks] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');

  // 计算统计数据
  const stats = useMemo(() => {
    if (!qualityData) return null;

    return {
      overallScore: qualityData.overallScore || 0,
      documentCount: qualityData.documentCount || 0,
      chunkCount: qualityData.chunkCount || 0,
      anomalyCount: anomalyChunks?.length || 0,
      averageScore: qualityData.averageScore || 0,
    };
  }, [qualityData, anomalyChunks]);

  // 选择/取消选择片段
  const handleSelectChunk = useCallback((chunkId) => {
    setSelectedChunks((prev) =>
      prev.includes(chunkId)
        ? prev.filter((id) => id !== chunkId)
        : [...prev, chunkId]
    );
  }, []);

  if (!stats) {
    return (
      <div className="quality-panel empty">
        <p>暂无质量评估数据</p>
      </div>
    );
  }

  return (
    <div className="quality-panel">
      {/* 头部 */}
      <div className="panel-header">
        <h3>质量评估面板</h3>

        <div className="header-actions">
          {selectedChunks.length > 0 && (
            <button
              className="btn-batch-reprocess"
              onClick={() => onReprocessSelected?.(selectedChunks)}
              disabled={loading}
            >
              重处理选中 ({selectedChunks.length})
            </button>
          )}
        </div>
      </div>

      {/* 标签页 */}
      <div className="panel-tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          概览
        </button>
        <button
          className={activeTab === 'anomalies' ? 'active' : ''}
          onClick={() => setActiveTab('anomalies')}
        >
          异常片段
          {anomalyChunks?.length > 0 && (
            <span className="badge">{anomalyChunks.length}</span>
          )}
        </button>
      </div>

      {/* 概览标签 */}
      {activeTab === 'overview' && (
        <div className="tab-content overview">
          {/* 质量分数卡片 */}
          <div className="score-cards">
            <QualityScoreCard
              score={Math.round(stats.overallScore)}
              title="整体质量"
              subtitle={`${stats.documentCount} 文档 / ${stats.chunkCount} 片段`}
            />

            <QualityScoreCard
              score={Math.round(stats.averageScore)}
              title="平均分数"
              subtitle="所有片段平均值"
            />

            <div className="stat-card">
              <div className="stat-header">
                <span>异常片段</span>
              </div>
              <div className="stat-value" style={{ color: '#ff4d4f' }}>
                {stats.anomalyCount}
              </div>
              <div className="stat-desc">
                占比 {((stats.anomalyCount / stats.chunkCount) * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* 图表区域 */}
          <div className="charts-grid">
            <QualityDistributionChart data={qualityData.distribution || {}} />
          </div>
        </div>
      )}

      {/* 异常片段标签 */}
      {activeTab === 'anomalies' && (
        <div className="tab-content anomalies">
          <AnomalyChunkList
            chunks={anomalyChunks || []}
            onReprocess={onReprocess}
            onReprocessAll={onReprocessAll}
            onSelect={handleSelectChunk}
            selectedIds={selectedChunks}
            loading={loading}
          />
        </div>
      )}
    </div>
  );
};

export default QualityPanel;
