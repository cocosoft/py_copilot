/**
 * 文档操作按钮组件
 * 
 * 根据文档的不同处理状态显示相应的操作按钮
 */

import React, { useState, useEffect } from 'react';
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
    condition: (metadata) => { 
      const status = metadata.processing_status || "idle"; 
      // 在 chunked 或 processing 状态下都显示实体识别按钮
      // processing 状态表示实体识别正在进行中
      return status === "chunked" || status === "processing"; 
    },
    // 动态标签：根据状态显示不同的文本
    getLabel: (metadata) => {
      const status = metadata.processing_status || "idle";
      if (status === "processing") {
        return "实体识别中...";
      }
      return "实体识别";
    },
    // 动态禁用状态：processing 状态下禁用按钮
    getDisabled: (metadata) => {
      const status = metadata.processing_status || "idle";
      return status === "processing";
    }
  },
  vectorize: {
    key: 'vectorize',
    label: '向量化',
    icon: FiDatabase,
    description: '将文本片段转换为向量表示',
    color: '#faad14',
    bgColor: '#fffbe6',
    condition: (metadata) => { const status = metadata.processing_status || "idle"; return status === "entity_extracted" || status === "entities_extracted" || status === "processing"; },
    getLabel: (metadata) => {
      const status = metadata?.processing_status;
      if (status === 'processing') {
        return '向量化中...';
      }
      return '向量化';
    },
    getDisabled: (metadata) => {
      const status = metadata?.processing_status;
      return status === 'processing';
    }
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
const ActionButton = ({ action, onClick, loading, disabled, metadata }) => {
  const Icon = action.icon;
  
  // 获取动态标签
  const getLabel = () => {
    if (loading) {
      return `${action.label}中...`;
    }
    // 如果 action 有 getLabel 方法，使用它
    if (action.getLabel && metadata) {
      return action.getLabel(metadata);
    }
    return action.label;
  };
  
  // 获取禁用状态
  const getDisabled = () => {
    // 如果 action 有 getDisabled 方法，使用它
    if (action.getDisabled && metadata) {
      return disabled || loading || action.getDisabled(metadata);
    }
    return disabled || loading;
  };
  
  const label = getLabel();
  const isDisabled = getDisabled();
  const isProcessing = label.includes('中...');
  
  return (
    <button
      className={`action-button ${action.key} ${loading || isProcessing ? 'loading' : ''}`}
      onClick={onClick}
      disabled={isDisabled}
      title={loading || isProcessing ? `${label}` : action.description}
      style={{
        '--action-color': action.color,
        '--action-bg-color': action.bgColor
      }}
    >
      <span className="button-icon">
        {loading || isProcessing ? <FiRefreshCw className="spin-icon" /> : <Icon />}
      </span>
      <span className="button-label">
        {label}
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
  // 使用本地状态跟踪文档对象，以便在异步操作期间立即更新UI
  const [localDocument, setLocalDocument] = useState(document);

  // 当document prop变化时，更新本地状态
  useEffect(() => {
    setLocalDocument(document);
  }, [document]);

  if (!localDocument) return null;

  const metadata = localDocument.document_metadata || {};
  const processingStatus = metadata.processing_status || 'idle';
  const knowledgeBaseId = localDocument.knowledge_base_id;

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
          response = await documentProcessingApi.extractDocumentText(localDocument.id);
          console.log(`[DocumentActions] 文本提取完成:`, response);
          break;
        case 'chunkDocument':
          console.log(`[DocumentActions] 开始切片处理`);
          response = await documentProcessingApi.chunkDocument(localDocument.id, knowledgeBaseId);
          console.log(`[DocumentActions] 切片处理完成:`, response);
          break;
        case 'extractEntities':
          console.log(`[DocumentActions] 开始实体识别`);
          try {
            // 设置较短的超时时间，因为后端是异步处理
            response = await documentProcessingApi.extractDocumentEntities(localDocument.id);
            console.log(`[DocumentActions] 实体识别任务已启动:`, response);

            // 立即更新本地状态，让UI显示"实体识别中"
            const updatedDocument = {
              ...localDocument,
              document_metadata: {
                ...localDocument.document_metadata,
                processing_status: 'processing'
              },
              _forceStatusUpdate: true
            };
            setLocalDocument(updatedDocument);

            // 立即触发状态更新回调，让父组件更新状态为"处理中"
            if (onActionComplete) {
              console.log(`[DocumentActions] 触发状态更新回调，状态: processing`);
              onActionComplete('extractEntities', updatedDocument);
            }
            // 异步操作已处理，直接返回，不执行后续的通用回调
            setLoading(prev => ({ ...prev, [action.key]: false }));
            return;
          } catch (error) {
            console.error(`[DocumentActions] 实体识别启动失败:`, error);
            // 如果是因为超时，也认为任务已启动
            if (error.message && error.message.includes('超时')) {
              console.log(`[DocumentActions] 请求超时，但任务可能已在后台启动`);
              response = { success: true, message: '实体识别任务已启动（后台处理中）' };

              // 立即更新本地状态，让UI显示"实体识别中"
              const updatedDocument = {
                ...localDocument,
                document_metadata: {
                  ...localDocument.document_metadata,
                  processing_status: 'processing'
                },
                _forceStatusUpdate: true
              };
              setLocalDocument(updatedDocument);

              if (onActionComplete) {
                onActionComplete('extractEntities', updatedDocument);
              }
              // 异步操作已处理，直接返回，不执行后续的通用回调
              setLoading(prev => ({ ...prev, [action.key]: false }));
              return;
            } else {
              throw error;
            }
          }
          break;
        case 'vectorize':
          console.log(`[DocumentActions] 开始向量化`);
          response = await documentProcessingApi.vectorizeDocument(localDocument.id, knowledgeBaseId);
          console.log(`[DocumentActions] 向量化完成:`, response);

          // 立即更新本地状态，让UI显示"向量化中"
          const vectorizeUpdatedDocument = {
            ...localDocument,
            document_metadata: {
              ...localDocument.document_metadata,
              processing_status: 'processing'
            },
            _forceStatusUpdate: true
          };
          setLocalDocument(vectorizeUpdatedDocument);

          if (onActionComplete) {
            console.log(`[DocumentActions] 触发状态更新回调，状态: processing`);
            onActionComplete('vectorize', vectorizeUpdatedDocument);
          }
          // 异步操作已处理，直接返回，不执行后续的通用回调
          setLoading(prev => ({ ...prev, [action.key]: false }));
          return;
        case 'buildGraph':
          console.log(`[DocumentActions] 开始构建知识图谱`);
          response = await documentProcessingApi.buildDocumentGraph(localDocument.id, knowledgeBaseId);
          console.log(`[DocumentActions] 知识图谱构建完成:`, response);
          break;
        case 'reprocess':
          // 使用统一的process端点进行重新处理
          console.log(`[DocumentActions] 开始重新处理文档`);
          response = await processDocument(localDocument.id);
          console.log(`[DocumentActions] 重新处理完成:`, response);
          break;
        case 'viewDetails':
          // 触发查看详情事件
          if (onActionComplete) {
            onActionComplete('viewDetails', localDocument);
          }
          return;
        case 'download':
          // 触发下载事件
          if (onActionComplete) {
            onActionComplete('download', localDocument);
          }
          return;
        case 'delete':
          // 触发删除事件
          if (onActionComplete) {
            onActionComplete('delete', localDocument);
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
        onActionComplete(action.key, localDocument);
      }
    } catch (error) {
      console.error(`[DocumentActions] 操作 ${action.key} 失败:`, error);
      
      // 添加友好的错误提示
      let errorMessage = `操作 ${action.label} 失败`;
      if (error.message) {
        errorMessage += `: ${error.message}`;
        console.error(`[DocumentActions] 错误详情: ${error.message}`);
      }
      
      // 检查是否是超时错误
      if (error.message && error.message.includes('超时')) {
        errorMessage = `操作 ${action.label} 超时，请检查网络连接或稍后重试`;
      }
      
      // 显示错误提示
      if (typeof message !== 'undefined') {
        message.error({ content: errorMessage });
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
            metadata={metadata}
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
            metadata={metadata}
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
                  metadata={metadata}
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
