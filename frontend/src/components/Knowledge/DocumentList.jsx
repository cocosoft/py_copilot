/**
 * 文档列表组件
 *
 * 显示知识库中的文档列表，支持分页和操作
 */

import React from 'react';
import './DocumentList.css';

/**
 * 文档列表组件
 *
 * @param {Object} props - 组件属性
 * @param {Array} props.documents - 文档列表
 * @param {boolean} props.loading - 是否加载中
 * @param {boolean} props.loadingMore - 是否正在加载更多
 * @param {Object} props.selectedKnowledgeBase - 选中的知识库
 * @param {number} props.currentPage - 当前页码
 * @param {number} props.totalPages - 总页数
 * @param {number} props.totalDocuments - 文档总数
 * @param {number} props.documentsPerPage - 每页文档数
 * @param {Map} props.processingDocuments - 正在处理的文档
 * @param {Function} props.onPageChange - 页码变化回调
 * @param {Function} props.onPageSizeChange - 每页数量变化回调
 * @param {Function} props.onLoadMore - 加载更多回调
 * @param {Function} props.onViewDetail - 查看详情回调
 * @param {Function} props.onDownload - 下载文档回调
 * @param {Function} props.onProcess - 处理文档回调
 * @param {Function} props.onDelete - 删除文档回调
 * @returns {JSX.Element} 文档列表
 */
const DocumentList = ({
  documents,
  loading,
  loadingMore,
  selectedKnowledgeBase,
  currentPage,
  totalPages,
  totalDocuments,
  documentsPerPage,
  processingDocuments,
  onPageChange,
  onPageSizeChange,
  onLoadMore,
  onViewDetail,
  onDownload,
  onProcess,
  onDelete
}) => {
  // 获取文档状态显示
  const getDocumentStatus = (document) => {
    const isProcessing = processingDocuments.has(document.id);
    const processingStatus = document.document_metadata?.processing_status;

    // 优先判断处理中状态
    if (isProcessing || processingStatus === 'processing') {
      return { text: '🔄 处理中', className: 'processing' };
    }

    // 队列中状态
    if (processingStatus === 'queued') {
      return { text: '⏳ 队列中', className: 'queued' };
    }

    // 优先使用 is_vectorized 字段判断最终状态
    if (document.is_vectorized) {
      return { text: '✅ 已向量化', className: 'vectorized' };
    }

    // 未向量化时，根据 processing_status 显示状态
    if (processingStatus === 'pending') {
      return { text: '⏸️ 等待处理', className: 'pending' };
    }

    // 默认状态
    return { text: '未处理', className: 'not-vectorized' };
  };

  // 获取文档描述
  const getDocumentDescription = (document) => {
    // 优先显示文档内容预览
    if (document.content && document.content.trim().length > 0) {
      return document.content.substring(0, 100) + '...';
    }

    // 显示文件大小和状态信息
    const fileSize = document.document_metadata?.file_size;
    const sizeText = fileSize ? `文件大小: ${(fileSize / 1024 / 1024).toFixed(2)} MB | ` : '';

    // 统一状态判断逻辑
    if (document.is_vectorized) {
      return `${sizeText}已向量化，点击查看详情`;
    }

    const processingStatus = document.document_metadata?.processing_status;
    if (processingStatus === 'processing') {
      return `${sizeText}处理中...`;
    } else if (processingStatus === 'queued') {
      return `${sizeText}队列中等待处理`;
    } else {
      return `${sizeText}等待向量化`;
    }
  };

  // 获取文档图标
  const getDocumentIcon = (fileType) => {
    if (fileType === '.pdf') return '📄';
    if (fileType === '.docx' || fileType === '.doc') return '📝';
    return '📄';
  };

  if (!selectedKnowledgeBase) {
    return (
      <div className="knowledge-grid">
        <div className="empty-state">
          <p>请选择或创建一个知识库</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="knowledge-grid">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <span>加载文档列表...</span>
        </div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="knowledge-grid">
        <div className="empty-state">
          <p>当前知识库暂无文档，请点击"导入文档"开始使用</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="knowledge-grid">
        {documents.map(document => {
          const status = getDocumentStatus(document);
          const isProcessing = processingDocuments.has(document.id) ||
            document.document_metadata?.processing_status === 'processing';

          return (
            <div key={document.id} className="knowledge-item">
              <div className="knowledge-icon">
                {getDocumentIcon(document.file_type)}
              </div>
              <div className="knowledge-info">
                <h3
                  className="knowledge-title"
                  onClick={() => onViewDetail(document.id)}
                >
                  {document.title}
                </h3>
                <p className="knowledge-description">
                  {getDocumentDescription(document)}
                </p>
                <div className="knowledge-meta">
                  <span className="document-type">{document.file_type.toUpperCase()}</span>
                  <span className="last-updated">
                    {new Date(document.created_at).toLocaleDateString()}
                  </span>
                  <span className={`vector-status ${status.className}`}>
                    {status.text}
                  </span>
                </div>
              </div>
              <div className="knowledge-actions">
                <button
                  className="action-btn"
                  title="查看详情"
                  onClick={() => onViewDetail(document.id)}
                >
                  👁️
                </button>
                <button
                  className="action-btn"
                  title="下载文档"
                  onClick={() => onDownload(document.id, document.title)}
                >
                  📥
                </button>
                {!document.is_vectorized && (
                  <button
                    className="action-btn process-btn"
                    title="开始处理（向量化、图谱化）"
                    onClick={() => onProcess(document.id, document.title)}
                    disabled={isProcessing}
                  >
                    {isProcessing ? '⏳' : '▶️'}
                  </button>
                )}
                <button
                  className="action-btn"
                  title="删除"
                  onClick={() => onDelete(document.id)}
                >
                  🗑️
                </button>
              </div>
            </div>
          );
        })}

        {/* 加载更多指示器 */}
        {loadingMore && (
          <div className="loading-more">
            <div className="loading-spinner small"></div>
            <span>加载更多文档...</span>
          </div>
        )}
      </div>

      {/* 文档列表分页控件 */}
      {totalDocuments > 0 && (
        <div className="pagination-container">
          <div className="pagination-info">
            共 {totalDocuments} 条文档，第 {currentPage} / {totalPages} 页
          </div>
          <div className="pagination-controls">
            <button
              className="pagination-btn"
              onClick={() => onPageChange(1)}
              disabled={currentPage === 1}
            >
              首页
            </button>
            <button
              className="pagination-btn"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              上一页
            </button>

            {/* 页码按钮 */}
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                className={`pagination-btn ${currentPage === page ? 'active' : ''}`}
                onClick={() => onPageChange(page)}
              >
                {page}
              </button>
            ))}

            <button
              className="pagination-btn"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              下一页
            </button>
            <button
              className="pagination-btn"
              onClick={() => onPageChange(totalPages)}
              disabled={currentPage === totalPages}
            >
              末页
            </button>

            {/* 每页显示数量选择 */}
            <div className="page-size-selector">
              <label htmlFor="pageSize">每页：</label>
              <select
                id="pageSize"
                value={documentsPerPage}
                onChange={(e) => onPageSizeChange(Number(e.target.value))}
              >
                <option value={10}>10条</option>
                <option value={20}>20条</option>
                <option value={50}>50条</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DocumentList;
