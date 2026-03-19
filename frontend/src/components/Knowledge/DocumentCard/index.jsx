/**
 * 文档卡片组件
 * 
 * 用于展示文档信息，支持选择、状态显示等
 */

import React from 'react';
import { FiFileText, FiImage, FiMusic, FiVideo, FiFile, FiMoreVertical } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
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
 * @param {string} props.viewMode - 视图模式 (list | grid)
 */
const DocumentCard = ({
  document,
  isSelected = false,
  onSelect,
  onClick,
  viewMode = 'list'
}) => {
  const { documentFilters } = useKnowledgeStore();
  const searchQuery = documentFilters?.search?.trim() || '';
  
  const fileType = document.fileType?.toLowerCase() || 'unknown';
  const FileIcon = fileTypeIcons[fileType] || FiFile;
  const fileColor = fileTypeColors[fileType] || '#8c8c8c';
  const status = statusConfig[document.vectorizationStatus] || statusConfig.pending;

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
          <span 
            className="document-card__status"
            style={{
              color: status.color,
              backgroundColor: status.bgColor,
              borderColor: status.borderColor,
            }}
          >
            {status.text}
          </span>
          <input
            type="checkbox"
            className="document-card__checkbox"
            checked={isSelected}
            onChange={handleCheckboxClick}
          />
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
        <span 
          className="document-card__status"
          style={{
            color: status.color,
            backgroundColor: status.bgColor,
            borderColor: status.borderColor,
          }}
        >
          {status.text}
        </span>
      </div>

      <button className="document-card__more" onClick={handleMoreClick}>
        <FiMoreVertical size={16} />
      </button>
    </div>
  );
};

export default React.memo(DocumentCard);
