/**
 * 文档选择组件
 *
 * 提供文档搜索、选择功能
 */

import React from 'react';
import { FiSearch, FiSettings, FiBox, FiCpu } from 'react-icons/fi';
import { Button } from '../../../components/UI';

/**
 * 文档选择组件
 */
const DocumentSelector = ({
  documents,
  filteredDocuments,
  selectedDocuments,
  docSearchQuery,
  setDocSearchQuery,
  handleSelectAllDocuments,
  handleClearDocumentSelection,
  toggleDocumentSelection,
  defaultModel,
  loadingModel,
  extracting,
  extractProgress,
  handleExtractEntities,
  setConfigModalVisible,
}) => {
  return (
    <div className="document-selection">
      <div className="selection-header">
        <h4>选择要处理的文档</h4>
        <div className="header-actions">
          <Button
            variant="ghost"
            size="small"
            icon={<FiSettings />}
            onClick={() => setConfigModalVisible(true)}
            className="config-btn"
          >
            实体配置
          </Button>
          <div className="model-info">
            <FiBox size={14} />
            {loadingModel ? (
              <span className="model-loading">加载模型配置...</span>
            ) : defaultModel ? (
              <span className="model-name">
                使用模型: {defaultModel.model_name || defaultModel.name || '默认模型'}
              </span>
            ) : (
              <span className="model-warning">未配置默认模型，将使用系统默认</span>
            )}
          </div>
        </div>
      </div>
      
      <div className="document-list-header">
        <div className="doc-search">
          <FiSearch size={14} />
          <input
            type="text"
            placeholder="搜索文档..."
            value={docSearchQuery}
            onChange={(e) => setDocSearchQuery(e.target.value)}
          />
        </div>
        <div className="selection-actions">
          <Button size="small" variant="ghost" onClick={handleSelectAllDocuments}>
            全选
          </Button>
          <Button size="small" variant="ghost" onClick={handleClearDocumentSelection}>
            清除
          </Button>
          <span className="selected-count">
            已选 {selectedDocuments.length} / {documents.length} 个
          </span>
        </div>
      </div>
      
      <div className="document-list">
        {filteredDocuments.map(doc => (
          <label key={doc.id} className="document-checkbox">
            <input
              type="checkbox"
              checked={selectedDocuments.includes(doc.id)}
              onChange={() => toggleDocumentSelection(doc.id)}
            />
            <span className="document-name">{doc.title}</span>
            <span className="document-type">{doc.file_type}</span>
          </label>
        ))}
        {filteredDocuments.length === 0 && documents.length > 0 && (
          <div className="no-results">没有匹配的文档</div>
        )}
        {documents.length === 0 && (
          <div className="no-documents">暂无文档，请先上传文档到知识库</div>
        )}
      </div>
      
      <Button
        variant="primary"
        icon={<FiCpu />}
        onClick={handleExtractEntities}
        loading={extracting}
        disabled={extracting || selectedDocuments.length === 0 || loadingModel}
      >
        {extracting ? `提取中 ${extractProgress}%` : '开始实体提取'}
      </Button>
    </div>
  );
};

export default DocumentSelector;
