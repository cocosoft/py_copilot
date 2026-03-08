/**
 * 批量构建面板组件
 *
 * 提供批量为多个文档构建知识图谱的功能，包括文档选择、参数配置、进度监控、结果报告
 */

import React, { useState, useEffect, useCallback } from 'react';
import { batchBuildKnowledgeGraph, getBatchBuildStatus, cancelBatchBuild } from '../../utils/api/knowledgeGraphApi';
import { listDocuments } from '../../utils/api/knowledgeApi';
import './BatchBuildPanel.css';

/**
 * 批量构建面板组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @param {Function} props.onBuildComplete - 构建完成回调
 * @returns {JSX.Element} 批量构建面板界面
 */
const BatchBuildPanel = ({ knowledgeBaseId, onBuildComplete }) => {
  // 文档列表
  const [documents, setDocuments] = useState([]);
  // 选中的文档ID
  const [selectedDocs, setSelectedDocs] = useState([]);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 批量任务ID
  const [batchId, setBatchId] = useState(null);
  // 任务状态
  const [taskStatus, setTaskStatus] = useState(null);
  // 轮询定时器
  const [pollInterval, setPollInterval] = useState(null);
  // 构建参数
  const [buildParams, setBuildParams] = useState({
    extractEntities: true,
    extractRelations: true,
    minConfidence: 0.7,
    maxWorkers: 3
  });
  // 结果报告
  const [buildResult, setBuildResult] = useState(null);

  /**
   * 加载文档列表 - 只加载已向量化的文档
   */
  const loadDocuments = useCallback(async () => {
    if (!knowledgeBaseId) return;

    setLoading(true);
    try {
      // 调用API获取已向量化的文档列表
      const response = await listDocuments(0, 1000, knowledgeBaseId, true);
      // 后端返回的数据结构为 { documents, skip, limit, total }
      if (response && response.documents) {
        setDocuments(response.documents);
      } else {
        setDocuments([]);
      }
    } catch (error) {
      console.error('加载文档列表失败:', error);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId]);

  // 组件挂载时加载文档
  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  /**
   * 轮询任务状态
   */
  const pollTaskStatus = useCallback(async (id) => {
    try {
      const response = await getBatchBuildStatus(id);
      if (response.success) {
        setTaskStatus(response.data);
        
        // 任务完成或失败时停止轮询
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          if (pollInterval) {
            clearInterval(pollInterval);
            setPollInterval(null);
          }
          setBuildResult(response.data);
          if (onBuildComplete) {
            onBuildComplete();
          }
        }
      }
    } catch (error) {
      console.error('获取任务状态失败:', error);
    }
  }, [pollInterval, onBuildComplete]);

  // 清理轮询定时器
  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [pollInterval]);

  /**
   * 开始批量构建
   */
  const handleStartBuild = async () => {
    if (selectedDocs.length === 0) {
      alert('请至少选择一个文档');
      return;
    }

    try {
      // 传递 knowledge_base_id 以使用正确的提取策略配置
      const response = await batchBuildKnowledgeGraph(selectedDocs, {
        ...buildParams,
        knowledge_base_id: knowledgeBaseId
      });
      if (response.success) {
        setBatchId(response.data.batch_id);
        setTaskStatus({
          batch_id: response.data.batch_id,
          status: 'pending',
          progress: 0,
          total_documents: selectedDocs.length,
          completed_documents: 0,
          failed_documents: 0
        });
        
        // 开始轮询任务状态
        const interval = setInterval(() => {
          pollTaskStatus(response.data.batch_id);
        }, 2000);
        setPollInterval(interval);
      }
    } catch (error) {
      console.error('启动批量构建失败:', error);
      alert('启动失败: ' + error.message);
    }
  };

  /**
   * 取消批量构建
   */
  const handleCancelBuild = async () => {
    if (!batchId) return;
    
    if (!window.confirm('确定要取消批量构建任务吗？')) {
      return;
    }

    try {
      await cancelBatchBuild(batchId);
      if (pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      }
      setTaskStatus(prev => ({ ...prev, status: 'cancelled' }));
    } catch (error) {
      console.error('取消任务失败:', error);
    }
  };

  /**
   * 重置构建
   */
  const handleReset = () => {
    setBatchId(null);
    setTaskStatus(null);
    setBuildResult(null);
    setSelectedDocs([]);
    if (pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
    }
  };

  /**
   * 全选/取消全选
   */
  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedDocs(documents.map(d => d.id));
    } else {
      setSelectedDocs([]);
    }
  };

  /**
   * 选择单个文档
   */
  const handleSelectDoc = (docId, checked) => {
    if (checked) {
      setSelectedDocs([...selectedDocs, docId]);
    } else {
      setSelectedDocs(selectedDocs.filter(id => id !== docId));
    }
  };

  /**
   * 获取状态标签
   */
  const getStatusLabel = (status) => {
    const labels = {
      'pending': '等待中',
      'processing': '处理中',
      'completed': '已完成',
      'failed': '失败',
      'cancelled': '已取消'
    };
    return labels[status] || status;
  };

  /**
   * 获取状态样式类
   */
  const getStatusClass = (status) => {
    const classes = {
      'pending': 'status-pending',
      'processing': 'status-processing',
      'completed': 'status-completed',
      'failed': 'status-failed',
      'cancelled': 'status-cancelled'
    };
    return classes[status] || '';
  };

  return (
    <div className="batch-build-panel">
      {/* 步骤指示器 */}
      <div className="step-indicator">
        <div className={`step ${!batchId ? 'active' : 'completed'}`}>
          <span className="step-number">1</span>
          <span className="step-label">选择文档</span>
        </div>
        <div className="step-line"></div>
        <div className={`step ${batchId && taskStatus?.status === 'processing' ? 'active' : batchId ? 'completed' : ''}`}>
          <span className="step-number">2</span>
          <span className="step-label">构建中</span>
        </div>
        <div className="step-line"></div>
        <div className={`step ${buildResult ? 'active' : ''}`}>
          <span className="step-number">3</span>
          <span className="step-label">完成</span>
        </div>
      </div>

      {/* 步骤1: 选择文档 */}
      {!batchId && (
        <div className="step-content">
          {/* 文档选择区域 */}
          <div className="document-selection">
            <div className="selection-header">
              <h3>选择文档</h3>
              <div className="selection-actions">
                <label className="select-all-label">
                  <input
                    type="checkbox"
                    checked={selectedDocs.length === documents.length && documents.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                  />
                  全选
                </label>
                <span className="selection-count">
                  已选择 {selectedDocs.length} / {documents.length} 个文档
                </span>
              </div>
            </div>

            {loading ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>加载文档列表...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📄</div>
                <p>暂无已向量化文档</p>
                <p className="empty-hint">请先上传并处理文档，然后再进行知识图谱批量构建</p>
              </div>
            ) : (
              <div className="document-list">
                {documents.map(doc => {
                  // 所有文档都是已向量化（因为API只返回已向量化的）
                  // 检查实体提取状态
                  const metadata = doc.document_metadata || {};
                  const entitiesCount = metadata.entities_count || 0;
                  const relationshipsCount = metadata.relationships_count || 0;
                  const hasEntities = entitiesCount > 0;
                  const hasRelationships = relationshipsCount > 0;

                  // 获取实体提取状态显示
                  const getExtractionStatus = () => {
                    if (hasEntities && hasRelationships) {
                      return {
                        text: `已提取(${entitiesCount}实体/${relationshipsCount}关系)`,
                        className: 'status-extracted',
                        title: `已提取 ${entitiesCount} 个实体, ${relationshipsCount} 个关系`
                      };
                    }
                    if (hasEntities) {
                      return {
                        text: `已提取(${entitiesCount}实体)`,
                        className: 'status-extracted',
                        title: `已提取 ${entitiesCount} 个实体`
                      };
                    }
                    return {
                      text: '未提取实体',
                      className: 'status-no-entities',
                      title: '尚未提取实体和关系，可进行批量构建'
                    };
                  };

                  const extractionStatus = getExtractionStatus();

                  return (
                    <div
                      key={doc.id}
                      className={`document-item ${selectedDocs.includes(doc.id) ? 'selected' : ''} ${hasEntities ? 'has-entities' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedDocs.includes(doc.id)}
                        onChange={(e) => handleSelectDoc(doc.id, e.target.checked)}
                      />
                      <div className="document-info">
                        <span className="document-name">{doc.title}</span>
                        <span className="document-meta">
                          {doc.file_type} · <span className="status-text status-vectorized">已向量化</span>
                          {hasEntities && (
                            <span className="extraction-info">
                              · <span className="entity-count">{entitiesCount}实体</span>
                              {hasRelationships && <span className="relation-count">/{relationshipsCount}关系</span>}
                            </span>
                          )}
                        </span>
                      </div>
                      <span
                        className={`status-badge ${extractionStatus.className}`}
                        title={extractionStatus.title}
                      >
                        {extractionStatus.text}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 参数配置区域 */}
          <div className="parameter-config">
            <h3>构建参数</h3>
            
            <div className="param-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={buildParams.extractEntities}
                  onChange={(e) => setBuildParams({...buildParams, extractEntities: e.target.checked})}
                />
                <span>提取实体</span>
              </label>
            </div>

            <div className="param-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={buildParams.extractRelations}
                  onChange={(e) => setBuildParams({...buildParams, extractRelations: e.target.checked})}
                />
                <span>提取关系</span>
              </label>
            </div>

            <div className="param-group">
              <label>最小置信度</label>
              <div className="range-input">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={buildParams.minConfidence}
                  onChange={(e) => setBuildParams({...buildParams, minConfidence: parseFloat(e.target.value)})}
                />
                <span>{(buildParams.minConfidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            <div className="param-group">
              <label>并发数</label>
              <select
                value={buildParams.maxWorkers}
                onChange={(e) => setBuildParams({...buildParams, maxWorkers: parseInt(e.target.value)})}
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={3}>3</option>
                <option value={5}>5</option>
              </select>
            </div>
          </div>

          {/* 开始构建按钮 */}
          <div className="action-bar">
            <button 
              className="btn btn-primary btn-large"
              onClick={handleStartBuild}
              disabled={selectedDocs.length === 0}
            >
              ⚡ 开始批量构建
            </button>
          </div>
        </div>
      )}

      {/* 步骤2: 构建中 */}
      {batchId && !buildResult && (
        <div className="step-content">
          <div className="progress-panel">
            <div className="progress-header">
              <h3>构建进度</h3>
              <span className={`status-badge ${getStatusClass(taskStatus?.status)}`}>
                {getStatusLabel(taskStatus?.status)}
              </span>
            </div>

            <div className="progress-stats">
              <div className="stat-item">
                <span className="stat-value">{taskStatus?.total_documents || 0}</span>
                <span className="stat-label">总文档</span>
              </div>
              <div className="stat-item">
                <span className="stat-value success">{taskStatus?.completed_documents || 0}</span>
                <span className="stat-label">成功</span>
              </div>
              <div className="stat-item">
                <span className="stat-value error">{taskStatus?.failed_documents || 0}</span>
                <span className="stat-label">失败</span>
              </div>
            </div>

            <div className="progress-bar-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${taskStatus?.progress || 0}%` }}
                />
              </div>
              <span className="progress-text">{taskStatus?.progress || 0}%</span>
            </div>

            {/* 当前处理消息 */}
            {taskStatus?.current_message && (
              <div className="current-message">
                <span className="label">当前状态:</span>
                <span className="value">{taskStatus.current_message}</span>
              </div>
            )}

            {/* 详细进度日志 */}
            {taskStatus?.results && taskStatus.results.length > 0 && (
              <div className="progress-logs">
                <h4>处理详情</h4>
                <div className="logs-list">
                  {taskStatus.results.map((result, index) => (
                    <div key={index} className={`log-item ${result.success ? 'success' : 'error'}`}>
                      <div className="log-header">
                        <span className="doc-id">文档 {result.document_id}</span>
                        <span className={`status-badge ${result.success ? 'success' : 'error'}`}>
                          {result.success ? '✓' : '✗'}
                        </span>
                      </div>
                      {result.success && (
                        <div className="log-stats">
                          <span className="stat">
                            <span className="stat-label">实体:</span>
                            <span className="stat-value">{result.node_count || result.nodes_count || 0}</span>
                          </span>
                          <span className="stat">
                            <span className="stat-label">关系:</span>
                            <span className="stat-value">{result.edge_count || result.edges_count || 0}</span>
                          </span>
                        </div>
                      )}
                      {result.error && (
                        <div className="log-error">{result.error}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="action-bar">
              <button 
                className="btn btn-danger"
                onClick={handleCancelBuild}
                disabled={taskStatus?.status === 'completed' || taskStatus?.status === 'failed'}
              >
                取消构建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 步骤3: 完成 */}
      {buildResult && (
        <div className="step-content">
          <div className="result-panel">
            <div className="result-header">
              <div className={`result-icon ${buildResult.status}`}>
                {buildResult.status === 'completed' ? '✅' : '❌'}
              </div>
              <h3>构建{buildResult.status === 'completed' ? '完成' : '失败'}</h3>
            </div>

            <div className="result-stats">
              <div className="stat-row">
                <span className="stat-label">总文档数</span>
                <span className="stat-value">{buildResult.total_documents}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">成功</span>
                <span className="stat-value success">{buildResult.completed_documents}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">失败</span>
                <span className="stat-value error">{buildResult.failed_documents}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">成功率</span>
                <span className="stat-value">
                  {((buildResult.completed_documents / buildResult.total_documents) * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* 详细的构建结果 */}
            {buildResult.results && buildResult.results.length > 0 && (
              <div className="result-details">
                <h4>提取详情</h4>
                <div className="results-list">
                  {buildResult.results.map((result, index) => (
                    <div key={index} className={`result-item ${result.success ? 'success' : 'error'}`}>
                      <div className="result-item-header">
                        <span className="doc-title">{result.title || `文档 ${result.document_id}`}</span>
                        <span className={`status-badge ${result.success ? 'success' : 'error'}`}>
                          {result.success ? '成功' : '失败'}
                        </span>
                      </div>
                      {result.success ? (
                        <div className="result-item-stats">
                          <div className="stat">
                            <span className="stat-label">实体数量:</span>
                            <span className="stat-value highlight">{result.node_count || result.nodes_count || 0}</span>
                          </div>
                          <div className="stat">
                            <span className="stat-label">关系数量:</span>
                            <span className="stat-value highlight">{result.edge_count || result.edges_count || 0}</span>
                          </div>
                          {result.processing_time && (
                            <div className="stat">
                              <span className="stat-label">处理时间:</span>
                              <span className="stat-value">{result.processing_time.toFixed(2)}s</span>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="result-item-error">
                          <span className="error-label">错误:</span>
                          <span className="error-message">{result.error || '未知错误'}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* 汇总统计 */}
                <div className="summary-stats">
                  <h5>汇总统计</h5>
                  <div className="summary-grid">
                    <div className="summary-item">
                      <span className="summary-label">总实体数:</span>
                      <span className="summary-value">
                        {buildResult.results.reduce((sum, r) => sum + (r.node_count || r.nodes_count || 0), 0)}
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">总关系数:</span>
                      <span className="summary-value">
                        {buildResult.results.reduce((sum, r) => sum + (r.edge_count || r.edges_count || 0), 0)}
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">平均实体/文档:</span>
                      <span className="summary-value">
                        {(buildResult.results.reduce((sum, r) => sum + (r.node_count || r.nodes_count || 0), 0) / buildResult.results.filter(r => r.success).length || 1).toFixed(1)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {buildResult.errors && buildResult.errors.length > 0 && (
              <div className="error-list">
                <h4>错误详情</h4>
                <ul>
                  {buildResult.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="action-bar">
              <button className="btn btn-secondary" onClick={handleReset}>
                返回重新选择
              </button>
              <button className="btn btn-primary" onClick={loadDocuments}>
                🔄 刷新文档列表
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchBuildPanel;
