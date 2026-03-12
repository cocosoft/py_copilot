/**
 * 知识库侧边栏组件
 *
 * 显示知识库列表，支持选择、创建、导入、导出和删除操作
 */

import React from 'react';
import { FaDownload } from 'react-icons/fa';
import './KnowledgeBaseSidebar.css';

/**
 * 知识库侧边栏组件
 *
 * @param {Object} props - 组件属性
 * @param {Array} props.knowledgeBases - 知识库列表
 * @param {Object} props.selectedKnowledgeBase - 选中的知识库
 * @param {boolean} props.loading - 是否加载中
 * @param {number} props.currentPage - 当前页码
 * @param {number} props.totalPages - 总页数
 * @param {number} props.totalKbs - 知识库总数
 * @param {Function} props.onSelect - 选择知识库回调
 * @param {Function} props.onCreate - 创建知识库回调
 * @param {Function} props.onImport - 导入知识库回调
 * @param {Function} props.onExport - 导出知识库回调
 * @param {Function} props.onDelete - 删除知识库回调
 * @param {Function} props.onPageChange - 页码变化回调
 * @returns {JSX.Element} 知识库侧边栏
 */
const KnowledgeBaseSidebar = ({
  knowledgeBases,
  selectedKnowledgeBase,
  loading,
  currentPage,
  totalPages,
  totalKbs,
  onSelect,
  onCreate,
  onImport,
  onExport,
  onDelete,
  onPageChange
}) => {
  return (
    <div className="knowledge-sidebar">
      <div className="sidebar-header">
        <h3>知识库</h3>
        <div className="sidebar-actions">
          <button
            className="sidebar-btn create-btn"
            onClick={onCreate}
            title="新建知识库"
          >
            +
          </button>
          <button
            className="sidebar-btn import-btn"
            onClick={onImport}
            title="导入知识库"
          >
            📥
          </button>
        </div>
      </div>

      <div className="sidebar-content">
        {loading ? (
          <div className="sidebar-loading">
            <div className="loading-spinner"></div>
            <span>加载中...</span>
          </div>
        ) : knowledgeBases?.length > 0 ? (
          <div className="sidebar-list">
            {knowledgeBases.map(kb => (
              <div
                key={kb.id}
                className={`sidebar-item ${selectedKnowledgeBase?.id === kb.id ? 'active' : ''}`}
                onClick={() => onSelect(kb)}
                title={kb.description || kb.name}
              >
                <div className="sidebar-item-icon">📚</div>
                <div className="sidebar-item-info">
                  <span className="sidebar-item-name">{kb.name}</span>
                  {kb.document_count !== undefined && (
                    <span className="sidebar-item-count">{kb.document_count} 文档</span>
                  )}
                </div>
                <div className="sidebar-item-actions">
                  <button
                    className="sidebar-action-btn export-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      onExport(kb);
                    }}
                    title="导出"
                  >
                    <FaDownload />
                  </button>
                  <button
                    className="sidebar-action-btn delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(kb);
                    }}
                    title="删除"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="sidebar-empty">
            <span>暂无知识库</span>
            <button onClick={onCreate}>创建知识库</button>
          </div>
        )}
      </div>

      {/* 知识库分页控件 */}
      {totalKbs > 0 && (
        <div className="sidebar-pagination">
          <div className="sidebar-pagination-info">
            {currentPage}/{totalPages}页
          </div>
          <div className="sidebar-pagination-controls">
            <button
              className="sidebar-page-btn"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              ‹
            </button>
            <button
              className="sidebar-page-btn"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              ›
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseSidebar;
