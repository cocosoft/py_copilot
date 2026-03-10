/**
 * 搜索面板组件
 *
 * 提供搜索、上传、批量处理等功能
 */

import React from 'react';
import './SearchPanel.css';

/**
 * 搜索面板组件
 *
 * @param {Object} props - 组件属性
 * @param {string} props.searchQuery - 搜索关键词
 * @param {Function} props.onSearchChange - 搜索变化回调
 * @param {boolean} props.uploading - 是否正在上传
 * @param {boolean} props.hasSelectedKnowledgeBase - 是否已选择知识库
 * @param {Function} props.onFileUpload - 文件上传回调
 * @param {boolean} props.hasPendingDocuments - 是否有等待处理的文档
 * @param {Function} props.onBatchProcess - 批量处理回调
 * @param {number} props.processingCount - 正在处理的文档数量
 * @param {Function} props.onEditKnowledgeBase - 编辑知识库回调
 * @param {string} props.mainActiveTab - 当前激活的标签页
 * @param {Function} props.onTabChange - 标签页变化回调
 * @returns {JSX.Element} 搜索面板
 */
const SearchPanel = ({
  searchQuery,
  onSearchChange,
  uploading,
  hasSelectedKnowledgeBase,
  onFileUpload,
  hasPendingDocuments,
  onBatchProcess,
  processingCount,
  onEditKnowledgeBase,
  mainActiveTab,
  onTabChange
}) => {
  return (
    <>
      {/* 工具栏区域 */}
      <div className="knowledge-toolbar">
        <div className="search-container">
          <input
            type="text"
            placeholder="搜索知识库..."
            className="knowledge-search"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          <button className="search-btn">
            🔍
          </button>
        </div>

        <div className="toolbar-actions">
          <input
            type="file"
            id="file-upload"
            onChange={onFileUpload}
            disabled={uploading || !hasSelectedKnowledgeBase}
            accept=".pdf,.docx,.doc,.txt,.xlsx,.xls,.pptx,.ppt,.png,.jpg,.jpeg,.gif,.bmp,.wps,.et,.dps"
            multiple
            style={{ display: 'none' }}
          />
          <label
            htmlFor="file-upload"
            className="import-btn"
            title="支持格式: PDF/DOC/DOCX/TXT/XLS/XLSX/PPT/PPTX/图片等，单个文件最大50MB，每次最多10个文件"
          >
            {uploading ? '上传中...' : !hasSelectedKnowledgeBase ? '请选择知识库' : '选择文档'}
          </label>
          <small className="upload-hint">
            最多10个文件，单个最大50MB
          </small>

          {/* 批量处理按钮 - 当有等待处理的文档时显示 */}
          {hasSelectedKnowledgeBase && hasPendingDocuments && (
            <button
              className="batch-process-btn"
              onClick={onBatchProcess}
              title="批量处理所有等待中的文档"
            >
              ▶️ 批量处理
            </button>
          )}

          {/* 批量处理中提示 */}
          {hasSelectedKnowledgeBase && processingCount > 0 && (
            <span className="batch-processing-hint">
              🔄 正在处理 {processingCount} 个文档...
            </span>
          )}

          {hasSelectedKnowledgeBase && (
            <button
              className="create-btn"
              onClick={onEditKnowledgeBase}
              disabled={uploading}
            >
              编辑知识库
            </button>
          )}
        </div>
      </div>

      {/* 主界面标签页导航 */}
      <div className="main-tab-navigation">
        <button
          className={`main-tab-btn ${mainActiveTab === 'documents' ? 'active' : ''}`}
          onClick={() => onTabChange('documents')}
        >
          文档管理
        </button>
        <button
          className={`main-tab-btn ${mainActiveTab === 'vectorization' ? 'active' : ''}`}
          onClick={() => onTabChange('vectorization')}
        >
          向量化管理
        </button>
        <button
          className={`main-tab-btn ${mainActiveTab === 'knowledge-graph' ? 'active' : ''}`}
          onClick={() => onTabChange('knowledge-graph')}
        >
          知识图谱
        </button>
      </div>
    </>
  );
};

export default SearchPanel;
