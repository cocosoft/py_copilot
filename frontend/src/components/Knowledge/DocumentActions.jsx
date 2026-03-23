/**
 * 文档操作按钮组件
 * 
 * 根据文档的不同处理状态显示相应的操作按钮
 */

import React, { useState } from 'react';
import { 
  FiFileText, FiScissors, FiUsers, FiDatabase, 
  FiShare2, FiRefreshCw, FiTrash2, FiDownload,
  FiEye, FiEdit, FiPlay, FiPause
} from 'react-icons/fi';
import { request } from '../../utils/apiUtils';
import { 
  processDocument
} from '../../utils/api/knowledgeApi';
import * as documentProcessingApi from '../../utils/api/documentProcessingApi';
import './DocumentActions.css';

/**
 * 操作按钮配置
 */
const ACTION_CONFIG = {
  extractText: {
    key: 'extractText',
    label: '提取文本',
    icon: FiFileText,
    description: '从文档中提取文本内容',
    color: '#1890ff',
    bgColor: '#e6f7ff',
    condition: (metadata) => { const status = metadata.processing_status || "idle"; return status === "idle" || status === "pending" || status === "text_extraction_failed"; }
  },
  chunkDocument: {
    key: 'chunkDocument',
    label: '切片处理',
    icon: FiScissors,
    description: '将文本分割成适合向量化的片段',
    color: '#52c41a',
    bgColor: '#f6ffed',
    condition: (metadata) => { const status = metadata.processing_status || "idle"; return status === "text_extracted"; }
  },
  extractEntities: {
    key: 'extractEntities',
    label: '实体识别',
    icon: FiUsers,
    description: '识别文档中的命名实体',
    color: '#722ed1',
    bgColor: '#f9f0ff',
    condition: (metadata) => { const status = metadata.processing_status || "idle"; return status === "chunked"; }
  },
  vectorize: {
    key: 'vectorize',
    label: '向量化',
    icon: FiDatabase,
    description: '将文本片段转换为向量表示',
    color: '#faad14',
    bgColor: '#fffbe6',
    condition: (metadata) => { const status = metadata.processing_status || "idle"; return status === "entity_extracted"; }
  },
  buildGraph: {
    key: 'buildGraph',
    label: '构建图谱',
    icon: FiShare2,
    description: '构建实体关系图谱',
    color: '#eb2f96',
    bgColor: '#fff1f0',
    condition: (metadata) => { const status = metadata.processing_status || "idle"; return status === "vectorized"; }
  },
  reprocess: {
    key: 'reprocess',
    label: '重新处理',
    icon: FiRefreshCw,
    description: '重新执行文档处理流程',
    color: '#fa8c16',
    bgColor: '#fff7e6',
    condition: (metadata) => { const status = metadata.processing_status || "idle"; return status === "failed" || status === "error" || status === "text_extraction_failed" || status === "chunking_failed" || status === "entity_extraction_failed" || status === "vectorization_failed" || status === "graph_building_failed"; }
  },
  viewDetails: {
    key: 'viewDetails',
    label: '查看详情',
    icon: FiEye,
    description: '查看文档处理详情',
    color: '#8c8c8c',
    bgColor: '#f5f5f5',
    condition: () => true // 总是显示
  },
  download: {
    key: 'download',
    label: '下载',
    icon: FiDownload,
    description: '下载文档',
    color: '#52c41a',
    bgColor: '#f6ffed',
    condition: () => true // 总是显示
  },
  delete: {
    key: 'delete',
    label: '删除',
    icon: FiTrash2,
    description: '删除文档',
    color: '#ff4d4f',
    bgColor: '#fff2f0',
    condition: () => true // 总是显示
  }
};

/**
 * 单个操作按钮组件
 */
const ActionButton = ({ action, onClick, loading, disabled }) => {
  const Icon = action.icon;
  
  return (
    <button
      className={`action-button ${action.key} ${loading ? 'loading' : ''}`}
      onClick={onClick}
      disabled={disabled || loading}
      title={loading ? `${action.label}处理中...` : action.description}
      style={{
        '--action-color': action.color,
        '--action-bg-color': action.bgColor
      }}
    >
      <span className="button-icon">
        {loading ? <FiRefreshCw className="spin-icon" /> : <Icon />}
      </span>
      <span className="button-label">
        {loading ? `${action.label}中...` : action.label}
      </span>
    </button>
  );
};

/**
 * 文档操作按钮主组件
 */
const DocumentActions = ({ document, onActionComplete, compact = false }) => {
  const [loading, setLoading] = useState({});
  const [showMore, setShowMore] = useState(false);

  if (!document) return null;

  const metadata = document.document_metadata || {};
  const processingStatus = metadata.processing_status || 'idle';
  const knowledgeBaseId = document.knowledge_base_id;

  // 根据条件筛选可用的操作
  const availableActions = Object.values(ACTION_CONFIG).filter(action => 
    action.condition(metadata)
  );

  // 主要操作（前4个）
  const primaryActions = availableActions.slice(0, 4);
  // 次要操作（剩余的）
  const secondaryActions = availableActions.slice(4);

  // 执行操作
  const handleAction = async (action) => {
    if (loading[action.key]) return;

    setLoading(prev => ({ ...prev, [action.key]: true }));

    try {
      let response = null;

      switch (action.key) {
        case 'extractText':
          console.log(`[DocumentActions] 开始提取文本`);
          response = await documentProcessingApi.extractDocumentText(document.id);
          console.log(`[DocumentActions] 文本提取完成:`, response);
          break;
        case 'chunkDocument':
          console.log(`[DocumentActions] 开始切片处理`);
          response = await documentProcessingApi.chunkDocument(document.id, knowledgeBaseId);
          console.log(`[DocumentActions] 切片处理完成:`, response);
          break;
        case 'extractEntities':
          console.log(`[DocumentActions] 开始实体识别`);
          response = await documentProcessingApi.extractDocumentEntities(document.id);
          console.log(`[DocumentActions] 实体识别完成:`, response);
          break;
        case 'vectorize':
          console.log(`[DocumentActions] 开始向量化`);
          response = await documentProcessingApi.vectorizeDocument(document.id, knowledgeBaseId);
          console.log(`[DocumentActions] 向量化完成:`, response);
          break;
        case 'buildGraph':
          console.log(`[DocumentActions] 开始构建知识图谱`);
          response = await documentProcessingApi.buildDocumentGraph(document.id, knowledgeBaseId);
          console.log(`[DocumentActions] 知识图谱构建完成:`, response);
          break;
        case 'reprocess':
          // 使用统一的process端点进行重新处理
          console.log(`[DocumentActions] 开始重新处理文档`);
          response = await processDocument(document.id);
          console.log(`[DocumentActions] 重新处理完成:`, response);
          break;
        case 'viewDetails':
          // 触发查看详情事件
          if (onActionComplete) {
            onActionComplete('viewDetails', document);
          }
          return;
        case 'download':
          // 触发下载事件
          if (onActionComplete) {
            onActionComplete('download', document);
          }
          return;
        case 'delete':
          // 触发删除事件
          if (onActionComplete) {
            onActionComplete('delete', document);
          }
          return;
        default:
          console.warn('Unknown action:', action.key);
          return;
      }

      // 检查响应是否成功
      if (response && response.success) {
        console.log(`[DocumentActions] ${action.label} 操作成功`);
      } else if (response) {
        console.warn(`[DocumentActions] ${action.label} 操作响应异常:`, response);
      }

      // 操作成功回调 - 触发父组件刷新文档列表
      if (onActionComplete) {
        console.log(`[DocumentActions] 触发 onActionComplete 回调: ${action.key}`);
        onActionComplete(action.key, document);
      }
    } catch (error) {
      console.error(`[DocumentActions] 操作 ${action.key} 失败:`, error);
      // 可以添加错误提示
      if (error.message) {
        console.error(`[DocumentActions] 错误详情: ${error.message}`);
      }
    } finally {
      setLoading(prev => ({ ...prev, [action.key]: false }));
    }
  };

  // 如果是紧凑模式，只显示主要操作
  if (compact) {
    return (
      <div className="document-actions compact">
        {primaryActions.map(action => (
          <ActionButton
            key={action.key}
            action={action}
            onClick={() => handleAction(action)}
            loading={loading[action.key]}
            disabled={processingStatus === 'processing'}
          />
        ))}
      </div>
    );
  }

  // 完整模式显示所有操作
  return (
    <div className="document-actions">
      <div className="actions-primary">
        {primaryActions.map(action => (
          <ActionButton
            key={action.key}
            action={action}
            onClick={() => handleAction(action)}
            loading={loading[action.key]}
            disabled={processingStatus === 'processing'}
          />
        ))}
      </div>

      {secondaryActions.length > 0 && (
        <div className="actions-secondary">
          <button 
            className="more-actions-button"
            onClick={() => setShowMore(!showMore)}
          >
            <span>更多操作</span>
            <span className={`arrow ${showMore ? 'up' : 'down'}`}>▼</span>
          </button>

          {showMore && (
            <div className="more-actions-dropdown">
              {secondaryActions.map(action => (
                <ActionButton
                  key={action.key}
                  action={action}
                  onClick={() => handleAction(action)}
                  loading={loading[action.key]}
                  disabled={processingStatus === 'processing'}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* 处理中状态显示 */}
      {processingStatus === 'processing' && (
        <div className="processing-indicator">
          <FiRefreshCw className="spin-icon" />
          <span>文档处理中...</span>
        </div>
      )}
    </div>
  );
};

export default DocumentActions;
