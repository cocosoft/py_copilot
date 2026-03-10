/**
 * 文档详情模态框组件
 *
 * 显示文档的详细信息、内容预览、向量片段和知识图谱
 */

import React from 'react';
import './DocumentDetailModal.css';

/**
 * 文档详情模态框组件
 *
 * @param {Object} props - 组件属性
 * @param {Object} props.document - 文档对象
 * @param {Object} props.selectedKnowledgeBase - 选中的知识库
 * @param {string} props.activeTab - 当前激活的标签页
 * @param {Function} props.onTabChange - 标签页变化回调
 * @param {Function} props.onClose - 关闭回调
 * @param {boolean} props.previewLoading - 是否正在加载预览
 * @param {string} props.previewError - 预览错误信息
 * @param {React.ReactNode} props.previewContent - 预览内容
 * @param {Array} props.documentTags - 文档标签列表
 * @param {boolean} props.loadingTags - 是否正在加载标签
 * @param {string} props.newTagName - 新标签名称
 * @param {Function} props.onNewTagNameChange - 新标签名称变化回调
 * @param {Function} props.onAddTag - 添加标签回调
 * @param {Function} props.onRemoveTag - 移除标签回调
 * @param {Array} props.documentChunks - 向量片段列表
 * @param {boolean} props.loadingChunks - 是否正在加载片段
 * @param {number} props.totalChunks - 片段总数
 * @param {number} props.currentChunkPage - 当前片段页码
 * @param {number} props.chunksPerPage - 每页片段数
 * @param {Function} props.onChunkPageChange - 片段页码变化回调
 * @param {boolean} props.buildingGraph - 是否正在构建知识图谱
 * @param {number} props.graphBuildProgress - 构建进度
 * @param {string} props.graphBuildSuccess - 构建成功消息
 * @param {string} props.graphBuildError - 构建错误消息
 * @param {Object} props.graphStatistics - 图谱统计信息
 * @param {Function} props.onBuildKnowledgeGraph - 构建知识图谱回调
 * @param {Function} props.onVectorizeDocument - 向量化文档回调
 * @param {boolean} props.updatingDocument - 是否正在更新文档
 * @param {Function} props.onUpdateDocument - 更新文档回调
 * @param {Function} props.onDownloadDocument - 下载文档回调
 * @param {Function} props.onDeleteDocument - 删除文档回调
 * @param {React.Component} props.HierarchicalGraphViewer - 知识图谱查看器组件
 * @param {React.Component} props.EntityConfirmationList - 实体确认列表组件
 * @returns {JSX.Element} 文档详情模态框
 */
const DocumentDetailModal = ({
  document,
  selectedKnowledgeBase,
  activeTab,
  onTabChange,
  onClose,
  previewLoading,
  previewError,
  previewContent,
  documentTags,
  loadingTags,
  newTagName,
  onNewTagNameChange,
  onAddTag,
  onRemoveTag,
  documentChunks,
  loadingChunks,
  totalChunks,
  currentChunkPage,
  chunksPerPage,
  onChunkPageChange,
  buildingGraph,
  graphBuildProgress,
  graphBuildSuccess,
  graphBuildError,
  graphStatistics,
  onBuildKnowledgeGraph,
  onVectorizeDocument,
  updatingDocument,
  onUpdateDocument,
  onDownloadDocument,
  onDeleteDocument,
  HierarchicalGraphViewer,
  EntityConfirmationList
}) => {
  if (!document) return null;

  const totalChunkPages = Math.ceil(totalChunks / chunksPerPage);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content document-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">文档详情</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="document-detail">
            <div className="document-detail-header">
              <h1 className="document-detail-title">{document.title}</h1>
              <div className="document-detail-meta">
                <span>文件类型: {document.file_type.toUpperCase()}</span>
                <span>创建时间: {new Date(document.created_at).toLocaleString()}</span>
                <span className={`vector-status ${document.is_vectorized ? 'vectorized' : 'not-vectorized'}`}>
                  向量化状态: {document.is_vectorized ? '已向量化' : '未向量化'}
                </span>
                {document.is_vectorized && (
                  <span className={`graph-status ${graphStatistics && graphStatistics.nodes_count > 0 ? 'has-graph' : 'no-graph'}`}>
                    知识图谱: {graphStatistics && graphStatistics.nodes_count > 0 ? `已构建 (${graphStatistics.nodes_count}节点)` : '未构建'}
                  </span>
                )}
              </div>
            </div>

            {/* 标签页导航 */}
            <div className="document-detail-tabs">
              <button
                className={`tab-btn ${activeTab === 'document' ? 'active' : ''}`}
                onClick={() => onTabChange('document')}
              >
                文档内容
              </button>
              {document.is_vectorized && (
                <button
                  className={`tab-btn ${activeTab === 'chunks' ? 'active' : ''}`}
                  onClick={() => onTabChange('chunks')}
                >
                  向量片段
                </button>
              )}
              <button
                className={`tab-btn ${activeTab === 'knowledge-graph' ? 'active' : ''}`}
                onClick={() => onTabChange('knowledge-graph')}
              >
                知识图谱
              </button>
            </div>

            {/* 标签页内容 */}
            <div className="tab-content">
              {/* 文档内容标签页 */}
              {activeTab === 'document' && (
                <div>
                  <div className="document-detail-content">
                    {previewLoading ? (
                      <div className="loading-container">
                        <div className="loading-spinner"></div>
                        <span>加载文档预览...</span>
                      </div>
                    ) : (
                      <>
                        {previewError && (
                          <div className="preview-error">
                            <span className="error-icon">⚠️</span>
                            <span>{previewError}</span>
                          </div>
                        )}
                        {previewContent}
                      </>
                    )}
                  </div>

                  {/* 标签管理区域 */}
                  <div className="document-tags-section">
                    <h3>文档标签</h3>

                    {/* 当前标签列表 */}
                    <div className="current-tags">
                      {loadingTags ? (
                        <div className="loading-container">
                          <div className="loading-spinner"></div>
                          <span>加载标签...</span>
                        </div>
                      ) : documentTags.length > 0 ? (
                        <div className="tags-list">
                          {documentTags.map(tag => (
                            <div key={tag.id} className="tag-item">
                              <span className="tag-name">{tag.name}</span>
                              <button
                                className="tag-remove-btn"
                                onClick={() => onRemoveTag(tag.id)}
                                title="删除标签"
                              >
                                ×
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty-tags">
                          <span>当前文档没有标签</span>
                        </div>
                      )}
                    </div>

                    {/* 添加新标签 */}
                    <div className="add-tag-form">
                      <input
                        type="text"
                        className="tag-input"
                        placeholder="添加新标签..."
                        value={newTagName}
                        onChange={(e) => onNewTagNameChange(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && onAddTag()}
                      />
                      <button
                        className="btn-primary tag-add-btn"
                        onClick={onAddTag}
                        disabled={!newTagName.trim()}
                      >
                        添加
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* 向量片段标签页 */}
              {activeTab === 'chunks' && (
                <div className="document-chunks-section">
                  <h3>向量片段 ({totalChunks} 个)</h3>

                  {loadingChunks ? (
                    <div className="loading-container">
                      <div className="loading-spinner"></div>
                      <span>加载向量片段...</span>
                    </div>
                  ) : documentChunks.length > 0 ? (
                    <>
                      {/* 向量片段列表 */}
                      <div className="chunks-list">
                        {documentChunks.slice((currentChunkPage - 1) * chunksPerPage, currentChunkPage * chunksPerPage).map((chunk) => (
                          <div key={chunk.id} className="chunk-item">
                            <div className="chunk-header">
                              <span className="chunk-index">片段 {chunk.chunk_index + 1}/{chunk.total_chunks}</span>
                              <span className="chunk-title">{chunk.title}</span>
                            </div>
                            <div className="chunk-content">
                              <p>{chunk.content}</p>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* 分页控件 */}
                      {totalChunks > chunksPerPage && (
                        <div className="chunks-pagination">
                          <div className="pagination-controls">
                            <button
                              className="pagination-btn"
                              onClick={() => onChunkPageChange(1)}
                              disabled={currentChunkPage === 1}
                            >
                              首页
                            </button>
                            <button
                              className="pagination-btn"
                              onClick={() => onChunkPageChange(currentChunkPage - 1)}
                              disabled={currentChunkPage === 1}
                            >
                              上一页
                            </button>

                            {/* 页码按钮 */}
                            {Array.from({ length: totalChunkPages }, (_, i) => i + 1).map(page => (
                              <button
                                key={page}
                                className={`pagination-btn ${currentChunkPage === page ? 'active' : ''}`}
                                onClick={() => onChunkPageChange(page)}
                              >
                                {page}
                              </button>
                            ))}

                            <button
                              className="pagination-btn"
                              onClick={() => onChunkPageChange(currentChunkPage + 1)}
                              disabled={currentChunkPage === totalChunkPages}
                            >
                              下一页
                            </button>
                            <button
                              className="pagination-btn"
                              onClick={() => onChunkPageChange(totalChunkPages)}
                              disabled={currentChunkPage === totalChunkPages}
                            >
                              末页
                            </button>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="empty-chunks">
                      <div className="empty-icon">📋</div>
                      <p>当前文档没有向量片段</p>
                      {!document.is_vectorized && (
                        <div className="empty-details">
                          <p>文档尚未进行向量化处理</p>
                          <ul>
                            <li>向量化可以将文档内容转换为计算机可理解的向量表示</li>
                            <li>向量片段是语义搜索和智能问答的基础</li>
                          </ul>
                          <button
                            className="btn-vectorize btn-primary"
                            onClick={() => onVectorizeDocument(document.id)}
                            disabled={updatingDocument || previewLoading}
                          >
                            启动向量化
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* 知识图谱标签页 */}
              {activeTab === 'knowledge-graph' && (
                <div className="knowledge-graph-tab optimized">
                  {/* 构建状态显示 */}
                  {buildingGraph && (
                    <div className="graph-build-status">
                      <div className="progress-container">
                        <div className="progress-bar">
                          <div
                            className="progress-fill"
                            style={{ width: `${graphBuildProgress}%` }}
                          ></div>
                        </div>
                        <span className="progress-text">{graphBuildProgress}%</span>
                      </div>
                      <p>正在构建知识图谱，请稍候...</p>
                    </div>
                  )}

                  {/* 构建结果消息 */}
                  {graphBuildSuccess && (
                    <div className="success-message">
                      <span className="success-icon">✓</span>
                      {graphBuildSuccess}
                    </div>
                  )}

                  {graphBuildError && (
                    <div className="error-message">
                      <span className="error-icon">✗</span>
                      {graphBuildError}
                    </div>
                  )}

                  {/* 三级知识图谱统一查看器 */}
                  <div className="hierarchical-graph-wrapper" style={{ height: '600px' }}>
                    <HierarchicalGraphViewer
                      documentId={document?.id}
                      knowledgeBaseId={selectedKnowledgeBase?.id}
                      defaultLevel="document"
                      showLevelSelector={true}
                      showComparison={true}
                      onNodeClick={(node) => console.log('点击节点:', node)}
                      onLevelChange={(level) => console.log('切换到层级:', level)}
                    />
                  </div>

                  {/* 实体确认面板 */}
                  <div className="entity-confirmation-section" style={{ marginTop: '20px' }}>
                    <h4>📝 实体确认</h4>
                    <EntityConfirmationList
                      documentId={document.id}
                      onConfirm={(entity) => console.log('确认实体:', entity)}
                      onModify={(entity) => console.log('修改实体:', entity)}
                      onDelete={(entity) => console.log('删除实体:', entity)}
                      onHighlight={(position) => console.log('高亮位置:', position)}
                      onReextract={() => onBuildKnowledgeGraph(document.id, null)}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="modal-footer">
          <button
            className="btn-primary"
            onClick={onUpdateDocument}
            disabled={updatingDocument || previewLoading}
          >
            {updatingDocument ? '更新中...' : '更新文档'}
          </button>
          <button
            className="btn-primary"
            onClick={onDownloadDocument}
            disabled={previewLoading || updatingDocument}
          >
            {previewLoading ? '下载中...' : '下载文档'}
          </button>
          {!document.is_vectorized && (
            <button
              className="btn-primary"
              onClick={() => onVectorizeDocument(document.id)}
              disabled={updatingDocument || previewLoading}
            >
              {updatingDocument ? '处理中...' : '向量化'}
            </button>
          )}
          <button
            className="btn-secondary"
            onClick={() => onDeleteDocument(document.id)}
            disabled={updatingDocument || previewLoading}
          >
            删除文档
          </button>
          <button className="btn-secondary" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentDetailModal;
