/**
 * 处理流程面板
 * 
 * 展示文档的四级处理流程和状态
 */

import React, { useState, useEffect } from 'react';
import { FiCheck, FiLoader, FiCircle, FiPlay, FiAlertTriangle } from 'react-icons/fi';
import { Button, Tooltip, Progress } from 'antd';
import * as documentProcessingApi from '../../utils/api/documentProcessingApi';
import './ProcessingFlowPanel.css';

/**
 * 处理步骤配置
 */
const PROCESS_STEPS = [
  {
    key: 'text_extracted',
    title: '文本提取',
    description: '文档解析、文本清理',
    actionLabel: '执行文本提取',
    actionApi: 'extractDocumentText',
    nextStage: 'chunked'
  },
  {
    key: 'chunked',
    title: '文档分块',
    description: '智能分块、向量化',
    actionLabel: '执行分块',
    actionApi: 'chunkDocument',
    nextStage: 'entity_extracted'
  },
  {
    key: 'entity_extracted',
    title: '实体识别',
    description: '片段级实体识别、文档级聚合',
    actionLabel: '执行实体识别',
    actionApi: 'extractDocumentEntities',
    nextStage: 'vectorized'
  },
  {
    key: 'vectorized',
    title: '向量化完成',
    description: '向量存储、索引构建',
    actionLabel: '执行向量化',
    actionApi: 'vectorizeDocument',
    nextStage: 'graph_built'
  },
  {
    key: 'graph_built',
    title: '知识图谱',
    description: '实体关系提取、图谱构建',
    actionLabel: '构建知识图谱',
    actionApi: null,
    nextStage: 'completed'
  }
];

/**
 * 状态图标
 */
const StatusIcon = ({ status, size = '16px' }) => {
  switch (status) {
    case 'completed':
      return <FiCheck className="status-icon completed" style={{ fontSize: size }} />;
    case 'processing':
      return <FiLoader className="status-icon processing" style={{ fontSize: size }} />;
    case 'failed':
      return <FiAlertTriangle className="status-icon failed" style={{ fontSize: size }} />;
    case 'pending':
    default:
      return <FiCircle className="status-icon pending" style={{ fontSize: size }} />;
  }
};

/**
 * 处理流程面板
 */
const ProcessingFlowPanel = ({ document, knowledgeBaseId, onStatusUpdate }) => {
  const [statusInfo, setStatusInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState({});

  // 加载文档状态
  useEffect(() => {
    if (document?.id) {
      loadDocumentStatus();
    }
  }, [document?.id]);

  const loadDocumentStatus = async () => {
    if (!document?.id) return;
    
    try {
      setLoading(true);
      const data = await documentProcessingApi.getDocumentProcessingStatus(document.id);
      setStatusInfo(data);
      onStatusUpdate && onStatusUpdate(data);
    } catch (error) {
      console.error('加载文档状态失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStepStatus = (step) => {
    if (!statusInfo) return 'pending';
    
    const stages = statusInfo.stages || {};
    if (stages[step.key]) {
      return 'completed';
    }
    
    return 'pending';
  };

  const canExecuteStep = (stepIndex) => {
    if (stepIndex === 0) return true;
    
    const prevStep = PROCESS_STEPS[stepIndex - 1];
    const prevStatus = getStepStatus(prevStep);
    return prevStatus === 'completed';
  };

  const handleStepAction = async (step) => {
    if (!document?.id || !knowledgeBaseId) return;
    
    setActionLoading(prev => ({ ...prev, [step.key]: true }));
    
    try {
      switch (step.actionApi) {
        case 'extractDocumentText':
          await documentProcessingApi.extractDocumentText(document.id);
          break;
        case 'chunkDocument':
          await documentProcessingApi.chunkDocument(document.id, knowledgeBaseId);
          break;
        case 'extractDocumentEntities':
          await documentProcessingApi.extractDocumentEntities(document.id);
          // 实体识别后自动聚合
          await documentProcessingApi.aggregateDocumentEntities(document.id);
          break;
        case 'vectorizeDocument':
          await documentProcessingApi.vectorizeDocument(document.id, knowledgeBaseId);
          break;
        default:
          break;
      }
      
      // 重新加载状态
      await loadDocumentStatus();
    } catch (error) {
      console.error('执行步骤失败:', error);
      alert(`执行${step.title}失败: ${error.message || '未知错误'}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [step.key]: false }));
    }
  };

  if (!document) {
    return (
      <div className="processing-flow-panel">
        <div className="panel-title">📋 文档处理流程</div>
        <div className="no-document">请选择一个文档查看处理流程</div>
      </div>
    );
  }

  return (
    <div className="processing-flow-panel">
      <div className="panel-title">📋 文档处理流程</div>
      
      {loading ? (
        <div className="loading">加载中...</div>
      ) : (
        <div className="flow-container">
          {PROCESS_STEPS.map((step, index) => {
            const status = getStepStatus(step);
            const canExecute = canExecuteStep(index);
            const isLast = index === PROCESS_STEPS.length - 1;
            
            return (
              <React.Fragment key={step.key}>
                {/* 步骤卡片 */}
                <div className={`step-card ${status}`}>
                  <div className="step-header">
                    <StatusIcon status={status} />
                    <span className="step-title">{step.title}</span>
                  </div>
                  
                  <div className="step-description">
                    {step.description}
                  </div>
                  
                  {status === 'completed' && (
                    <div className="step-status-text">✓ 完成</div>
                  )}
                  
                  {status === 'pending' && canExecute && step.actionApi && (
                    <Button 
                      type="primary" 
                      size="small" 
                      loading={actionLoading[step.key]}
                      onClick={() => handleStepAction(step)}
                      icon={<FiPlay />}
                    >
                      {step.actionLabel}
                    </Button>
                  )}
                  
                  {status === 'pending' && !canExecute && (
                    <Tooltip title="等待前置步骤完成">
                      <Button 
                        size="small" 
                        disabled 
                      >
                        {step.actionLabel}
                      </Button>
                    </Tooltip>
                  )}
                </div>
                
                {/* 连接箭头 */}
                {!isLast && (
                  <div className="step-connector">
                    <div className={`connector-line ${status === 'completed' ? 'active' : ''}`} />
                    <div className="connector-arrow">▶</div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      )}
      
      {/* 状态摘要 */}
      {statusInfo && (
        <div className="status-summary">
          <div className="summary-item">
            <span className="summary-label">当前状态：</span>
            <span className={`summary-value ${statusInfo.processing_status}`}>
              {statusInfo.processing_status}
            </span>
          </div>
          {statusInfo.stats && (
            <div className="summary-item">
              <span className="summary-label">片段数：</span>
              <span className="summary-value">{statusInfo.stats.chunks_count || 0}</span>
            </div>
          )}
          {statusInfo.stats && (
            <div className="summary-item">
              <span className="summary-label">实体数：</span>
              <span className="summary-value">{statusInfo.stats.entities_count || 0}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProcessingFlowPanel;
