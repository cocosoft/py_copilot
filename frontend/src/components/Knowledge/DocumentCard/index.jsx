/**
 * 文档卡片组件
 * 
 * 用于展示文档信息，支持选择、状态显示等
 */

import React from 'react';
import { FiFileText, FiImage, FiMusic, FiVideo, FiFile, FiMoreVertical, FiLayers } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import DocumentStatusBadge from '../DocumentStatusBadge';
import DocumentProgress from '../DocumentProgress';
import './styles.css';

/**
 * 文件类型图标映射
 */
const fileTypeIcons = {
  pdf: FiFileText,
  doc: FiFileText,
  docx: FiFileText,
  txt: FiFileText,
  md: FiFileText,
  jpg: FiImage,
  jpeg: FiImage,
  png: FiImage,
  gif: FiImage,
  mp3: FiMusic,
  wav: FiMusic,
  mp4: FiVideo,
  avi: FiVideo,
};

/**
 * 文件类型颜色映射
 */
const fileTypeColors = {
  pdf: '#ff4d4f',
  doc: '#1890ff',
  docx: '#1890ff',
  txt: '#8c8c8c',
  md: '#52c41a',
  jpg: '#faad14',
  jpeg: '#faad14',
  png: '#faad14',
  gif: '#faad14',
  mp3: '#722ed1',
  wav: '#722ed1',
  mp4: '#eb2f96',
  avi: '#eb2f96',
};

/**
 * 状态配置
 * 支持向量化状态和实体识别状态
 */
const statusConfig = {
  vectorized: {
    text: '已向量化',
    color: '#52c41a',
    bgColor: '#f6ffed',
    borderColor: '#b7eb8f',
  },
  processing: {
    text: '处理中',
    color: '#faad14',
    bgColor: '#fffbe6',
    borderColor: '#ffe58f',
  },
  pending: {
    text: '待处理',
    color: '#8c8c8c',
    bgColor: '#f5f5f5',
    borderColor: '#d9d9d9',
  },
  error: {
    text: '错误',
    color: '#ff4d4f',
    bgColor: '#fff2f0',
    borderColor: '#ffccc7',
  },
  // 实体识别相关状态
  entity_processing: {
    text: '实体识别中',
    color: '#1890ff',
    bgColor: '#e6f7ff',
    borderColor: '#91d5ff',
  },
  entity_aggregating: {
    text: '实体聚合中',
    color: '#722ed1',
    bgColor: '#f9f0ff',
    borderColor: '#d3adf7',
  },
  entity_aligning: {
    text: 'KB对齐中',
    color: '#fa8c16',
    bgColor: '#fff7e6',
    borderColor: '#ffd591',
  },
  entity_completed: {
    text: '已实体识别',
    color: '#52c41a',
    bgColor: '#f6ffed',
    borderColor: '#b7eb8f',
  },
};

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 格式化日期
 */
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  
  // 小于1小时
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000);
    return minutes < 1 ? '刚刚' : `${minutes}分钟前`;
  }
  
  // 小于24小时
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000);
    return `${hours}小时前`;
  }
  
  // 小于7天
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000);
    return `${days}天前`;
  }
  
  return date.toLocaleDateString('zh-CN');
};

/**
 * 文档卡片组件
 * 
 * @param {Object} props
 * @param {Object} props.document - 文档数据
 * @param {boolean} props.isSelected - 是否选中
 * @param {Function} props.onSelect - 选择回调
 * @param {Function} props.onClick - 点击回调
 * @param {Function} props.onProcessingFlow - 处理流程回调
 * @param {string} props.viewMode - 视图模式 (list | grid)
 */
const DocumentCard = ({
  document,
  isSelected = false,
  onSelect,
  onClick,
  onProcessingFlow,
  viewMode = 'list'
}) => {
  const { documentFilters } = useKnowledgeStore();
  const searchQuery = documentFilters?.search?.trim() || '';
  
  const fileType = document.fileType?.toLowerCase() || 'unknown';
  const FileIcon = fileTypeIcons[fileType] || FiFile;
  const fileColor = fileTypeColors[fileType] || '#8c8c8c';
  
  // 获取文档元数据
  const metadata = document.document_metadata || {};
  const processingStatus = metadata.processing_status || 'idle';
  
  // 计算总体进度
  const stages = ['text_extracted', 'chunked', 'entity_extracted', 'vectorized', 'graph_built'];
  const completedStages = stages.filter(stage => metadata[stage] === true);
  const progress = (completedStages.length / stages.length) * 100;

  /**
   * 高亮搜索关键词
   */
  const highlightSearchQuery = (text) => {
    if (!searchQuery) return text;
    
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    return text.split(regex).map((part, index) => 
      regex.test(part) ? 
        <span key={index} className="document-card__title-highlight">{part}</span> : 
        part
    );
  };

  /**
   * 处理复选框点击
   */
  const handleCheckboxClick = (e) => {
    e.stopPropagation();
    onSelect?.(document.id);
  };

  /**
   * 处理卡片点击
   */
  const handleCardClick = () => {
    onClick?.(document);
  };

  /**
   * 处理更多操作
   */
  const handleMoreClick = (e) => {
    e.stopPropagation();
    // TODO: 显示更多操作菜单
    console.log('更多操作:', document.id);
  };

  /**
   * 处理流程按钮点击
   */
  const handleProcessingFlowClick = (e) => {
    e.stopPropagation();
    onProcessingFlow?.(document.id);
  };

  if (viewMode === 'grid') {
    return (
      <div 
        className={`document-card document-card--grid ${isSelected ? 'selected' : ''}`}
        onClick={handleCardClick}
      >
        <div className="document-card__header">
          <div 
            className="document-card__icon"
            style={{ backgroundColor: `${fileColor}15`, color: fileColor }}
          >
            <FileIcon size={24} />
          </div>
          <button className="document-card__more" onClick={handleMoreClick}>
            <FiMoreVertical size={16} />
          </button>
        </div>

        <div className="document-card__content">
          <h4 className="document-card__title" title={document.title}>
            {highlightSearchQuery(document.title)}
          </h4>
          <p className="document-card__meta">
            {formatFileSize(document.size)} · {formatDate(document.createdAt)}
          </p>
        </div>

        <div className="document-card__footer">
          {/* 使用新的细粒度状态显示 */}
          <DocumentStatusBadge document={document} compact={true} />
          <div className="document-card__actions">
            <button
              className="document-card__action-btn processing-flow-btn"
              onClick={handleProcessingFlowClick}
              title="处理流程"
            >
              <FiLayers size={14} />
              <span>流程</span>
            </button>
            <input
              type="checkbox"
              className="document-card__checkbox"
              checked={isSelected}
              onChange={handleCheckboxClick}
            />
          </div>
        </div>
      </div>
    );
  }

  // 列表视图
  return (
    <div 
      className={`document-card document-card--list ${isSelected ? 'selected' : ''}`}
      onClick={handleCardClick}
    >
      <div className="document-card__checkbox-wrapper">
        <input
          type="checkbox"
          className="document-card__checkbox"
          checked={isSelected}
          onChange={handleCheckboxClick}
        />
      </div>

      <div 
        className="document-card__icon"
        style={{ backgroundColor: `${fileColor}15`, color: fileColor }}
      >
        <FileIcon size={20} />
      </div>

      <div className="document-card__content">
        <h4 className="document-card__title" title={document.title}>
          {highlightSearchQuery(document.title)}
        </h4>
        <p className="document-card__meta">
          {formatFileSize(document.size)} · {formatDate(document.createdAt)}
        </p>
      </div>

      <div className="document-card__status-wrapper">
        {/* 使用新的细粒度状态显示 */}
        <DocumentStatusBadge document={document} compact={true} />
      </div>

      <button
        className="document-card__action-btn processing-flow-btn"
        onClick={handleProcessingFlowClick}
        title="处理流程"
      >
        <FiLayers size={14} />
        <span>流程</span>
      </button>

      <button className="document-card__more" onClick={handleMoreClick}>
        <FiMoreVertical size={16} />
      </button>
    </div>
  );
};

export default React.memo(DocumentCard);
