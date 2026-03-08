/**
 * 知识图谱数据清理组件
 * 
 * 提供界面化的知识图谱数据清理功能
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import knowledgeGraphApi from '../../services/knowledgeGraphApi';
import './GraphDataCleaner.css';

/**
 * 清理级别选项
 */
const CLEAR_LEVELS = [
  { value: 'all', label: '全部清理', description: '清理所有层级的实体和关系数据（文档级、知识库级、全局级）' },
  { value: 'document', label: '仅文档级', description: '仅清理文档级实体和关系' },
  { value: 'kb', label: '知识库级及以下', description: '清理知识库级和文档级数据' },
  { value: 'global', label: '仅全局级', description: '仅清理全局级实体和关系' }
];

/**
 * 知识图谱数据清理组件
 * 
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID（可选）
 * @param {number} props.documentId - 文档ID（可选）
 * @param {Function} props.onClearComplete - 清理完成回调
 */
const GraphDataCleaner = ({ 
  knowledgeBaseId = null, 
  documentId = null, 
  onClearComplete = null 
}) => {
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  /**
   * 预览将要清理的数据
   */
  const handlePreview = async () => {
    setLoading(true);
    setError(null);
    setPreviewData(null);
    setResult(null);

    try {
      const response = await knowledgeGraphApi.clearGraphData({
        level: selectedLevel,
        knowledge_base_id: knowledgeBaseId,
        document_id: documentId,
        confirm: false
      });

      if (response.success) {
        setPreviewData(response.data);
        setConfirming(true);
      } else {
        setError(response.message || '预览失败');
      }
    } catch (err) {
      setError(err.message || '预览请求失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 执行清理
   */
  const handleClear = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await knowledgeGraphApi.clearGraphData({
        level: selectedLevel,
        knowledge_base_id: knowledgeBaseId,
        document_id: documentId,
        confirm: true
      });

      if (response.success) {
        setResult(response.data);
        setPreviewData(null);
        setConfirming(false);
        
        if (onClearComplete) {
          onClearComplete(response.data);
        }
      } else {
        setError(response.message || '清理失败');
      }
    } catch (err) {
      setError(err.message || '清理请求失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 取消清理
   */
  const handleCancel = () => {
    setConfirming(false);
    setPreviewData(null);
    setError(null);
  };

  /**
   * 重置状态
   */
  const handleReset = () => {
    setSelectedLevel('all');
    setPreviewData(null);
    setConfirming(false);
    setResult(null);
    setError(null);
  };

  /**
   * 渲染统计信息
   */
  const renderStats = (stats) => {
    if (!stats) return null;

    const items = [
      { key: 'global_entities', label: '全局级实体' },
      { key: 'global_relationships', label: '全局级关系' },
      { key: 'kb_entities', label: '知识库级实体' },
      { key: 'kb_relationships', label: '知识库级关系' },
      { key: 'document_entities', label: '文档级实体' },
      { key: 'document_relationships', label: '文档级关系' },
      { key: 'documents_reset', label: '重置文档数' }
    ];

    return (
      <div className="stats-grid">
        {items.map(({ key, label }) => {
          const value = stats[key];
          if (value === undefined || value === null) return null;
          
          return (
            <div key={key} className="stat-item">
              <span className="stat-label">{label}</span>
              <span className="stat-value">{value}</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="graph-data-cleaner">
      <div className="cleaner-header">
        <h3>🧹 知识图谱数据清理</h3>
        <p className="cleaner-description">
          清理混乱的实体和关系数据，重新开始构建知识图谱
        </p>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {!result && (
        <div className="cleaner-form">
          <div className="form-group">
            <label className="form-label">选择清理级别</label>
            <div className="level-options">
              {CLEAR_LEVELS.map((level) => (
                <label
                  key={level.value}
                  className={`level-option ${selectedLevel === level.value ? 'selected' : ''}`}
                >
                  <input
                    type="radio"
                    name="clearLevel"
                    value={level.value}
                    checked={selectedLevel === level.value}
                    onChange={(e) => setSelectedLevel(e.target.value)}
                    disabled={loading || confirming}
                  />
                  <div className="level-content">
                    <span className="level-label">{level.label}</span>
                    <span className="level-description">{level.description}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {(knowledgeBaseId || documentId) && (
            <div className="scope-info">
              <span className="scope-label">清理范围:</span>
              {documentId && <span>文档 ID: {documentId}</span>}
              {knowledgeBaseId && <span>知识库 ID: {knowledgeBaseId}</span>}
            </div>
          )}

          {!confirming ? (
            <button
              className="btn-preview"
              onClick={handlePreview}
              disabled={loading}
            >
              {loading ? '加载中...' : '预览将要清理的数据'}
            </button>
          ) : (
            <div className="confirmation-section">
              <div className="warning-box">
                <span className="warning-icon">⚠️</span>
                <div className="warning-content">
                  <strong>警告：此操作不可恢复！</strong>
                  <p>确定要删除以下数据吗？</p>
                </div>
              </div>

              {previewData && (
                <div className="preview-section">
                  <h4>将要删除的数据预览</h4>
                  {renderStats(previewData.stats)}
                  <div className="total-count">
                    总计: <strong>{previewData.total}</strong> 条数据
                  </div>
                </div>
              )}

              <div className="action-buttons">
                <button
                  className="btn-cancel"
                  onClick={handleCancel}
                  disabled={loading}
                >
                  取消
                </button>
                <button
                  className="btn-confirm"
                  onClick={handleClear}
                  disabled={loading}
                >
                  {loading ? '清理中...' : '确认删除'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="result-section">
          <div className="success-message">
            <span className="success-icon">✓</span>
            <div className="success-content">
              <strong>清理完成！</strong>
              <p>成功删除 {result.total_deleted} 条数据</p>
            </div>
          </div>

          <div className="result-details">
            <h4>清理详情</h4>
            {renderStats(result.deleted_counts)}
          </div>

          <button className="btn-reset" onClick={handleReset}>
            继续清理其他数据
          </button>
        </div>
      )}
    </div>
  );
};

GraphDataCleaner.propTypes = {
  knowledgeBaseId: PropTypes.number,
  documentId: PropTypes.number,
  onClearComplete: PropTypes.func
};

export default GraphDataCleaner;
