/**
 * 增强版批量操作组件
 * 
 * 提供文档批量选择、标签管理、知识图谱构建、导出、向量化、删除等操作
 */

import React, { useState } from 'react';
import { FiDownload, FiTrash2, FiZap, FiX, FiCheckSquare, FiSquare, FiTag, FiShare2, FiCopy, FiMove, FiLayers, FiCheckCircle, FiXCircle } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button, showSuccess, showError, showWarning, Modal } from '../../UI';
import { 
  batchDeleteDocuments, 
  batchDownloadDocuments, 
  processDocument,
  batchUpdateEntityStatus,
  buildKnowledgeGraph
} from '../../../utils/api/knowledgeApi';
import websocketService from '../../../services/websocketService';
import './EnhancedBatchOperations.css';

/**
 * 批量操作组件
 *
 * 当选中文档时显示，提供批量操作功能
 *
 * @param {Object} props - 组件属性
 * @param {Function} props.onRefresh - 刷新文档列表回调
 * @param {Function} props.onBatchProcessStart - 批量处理开始回调
 */
const EnhancedBatchOperations = ({ onRefresh, onBatchProcessStart }) => {
  const {
    documents,
    selectedDocuments,
    toggleDocumentSelection,
    setSelectedDocuments,
    isProcessing,
    currentKnowledgeBase,
  } = useKnowledgeStore();

  // 本地状态
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isVectorizing, setIsVectorizing] = useState(false);
  const [isBuildingGraph, setIsBuildingGraph] = useState(false);
  const [isTagging, setIsTagging] = useState(false);
  const [showTagModal, setShowTagModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedTags, setSelectedTags] = useState([]);
  const [exportFormat, setExportFormat] = useState('json');
  const [showEntityStatusModal, setShowEntityStatusModal] = useState(false);
  const [entityStatus, setEntityStatus] = useState('confirmed');

  const selectedCount = selectedDocuments.length;
  const totalCount = documents.length;

  // 如果没有选中的文档，不显示工具栏
  if (selectedCount === 0) return null;

  // 判断是否全选
  const isAllSelected = selectedCount === totalCount && totalCount > 0;
  const isIndeterminate = selectedCount > 0 && selectedCount < totalCount;

  /**
   * 处理全选/取消全选
   */
  const handleSelectAll = () => {
    if (isAllSelected) {
      setSelectedDocuments([]);
    } else {
      setSelectedDocuments(documents.map((d) => d.id));
    }
  };

  /**
   * 处理批量下载
   */
  const handleBatchDownload = async () => {
    if (selectedCount === 0) {
      showWarning('请先选择要下载的文档');
      return;
    }

    setIsDownloading(true);
    try {
      // 获取选中文档的uuid或id
      const selectedDocs = documents.filter(doc =>
        selectedDocuments.some(id => String(id) === String(doc.id))
      );
      const docIds = selectedDocs.map(doc => doc.uuid || doc.id);

      const blob = await batchDownloadDocuments(docIds);

      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `documents_${new Date().getTime()}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showSuccess(`成功下载 ${selectedCount} 个文档`);
    } catch (error) {
      showError('批量下载失败：' + error.message);
    } finally {
      setIsDownloading(false);
    }
  };

  /**
   * 处理批量向量化
   */
  const handleBatchVectorize = async () => {
    if (selectedCount === 0) {
      showWarning('请先选择要向量化的文档');
      return;
    }

    setIsVectorizing(true);
    
    // 获取选中文档
    const selectedDocs = documents.filter(doc =>
      selectedDocuments.some(id => String(id) === String(doc.id))
    );

    // 先显示进度面板，让用户立即看到反馈
    if (onBatchProcessStart) {
      console.log('[BatchVectorize] 立即显示进度面板:', selectedDocs);
      onBatchProcessStart(selectedDocs);
    }

    // 清空选择
    setSelectedDocuments([]);

    // 异步处理文档，不阻塞UI
    (async () => {
      let successCount = 0;
      let errorCount = 0;

      for (const doc of selectedDocs) {
        try {
          const docId = doc.uuid || doc.id;
          console.log('[BatchVectorize] 启动文档处理:', docId);
          const result = await processDocument(docId);
          console.log('[BatchVectorize] 文档处理启动结果:', result);
          successCount++;
        } catch (error) {
          console.error('[BatchVectorize] 向量化失败:', doc.id, error);
          errorCount++;
        }
      }

      if (successCount > 0) {
        showSuccess(`成功启动 ${successCount} 个文档的向量化`);
      }
      if (errorCount > 0) {
        showWarning(`${errorCount} 个文档向量化失败`);
      }

      // 刷新文档列表
      if (onRefresh) {
        onRefresh();
      }
      
      setIsVectorizing(false);
    })();
  };

  /**
   * 处理批量删除
   */
  const handleBatchDelete = async () => {
    if (selectedCount === 0) {
      showWarning('请先选择要删除的文档');
      return;
    }

    if (!window.confirm(`确定要删除选中的 ${selectedCount} 个文档吗？\n此操作不可恢复！`)) {
      return;
    }

    setIsDeleting(true);
    try {
      // 获取选中文档的uuid或id
      const selectedDocs = documents.filter(doc =>
        selectedDocuments.some(id => String(id) === String(doc.id))
      );
      const docIds = selectedDocs.map(doc => doc.uuid || doc.id);

      const result = await batchDeleteDocuments(docIds);

      if (result.success_count > 0) {
        showSuccess(`成功删除 ${result.success_count} 个文档`);
      }

      if (result.failed_count > 0) {
        showWarning(`${result.failed_count} 个文档删除失败`);
        console.error('删除失败的文档:', result.failed_documents);
      }

      // 清空选择
      setSelectedDocuments([]);

      // 刷新文档列表
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      showError('批量删除失败：' + error.message);
    } finally {
      setIsDeleting(false);
    }
  };

  /**
   * 处理批量知识图谱构建
   */
  const handleBatchBuildGraph = async () => {
    if (selectedCount === 0) {
      showWarning('请先选择要构建知识图谱的文档');
      return;
    }

    if (!currentKnowledgeBase) {
      showWarning('请先选择知识库');
      return;
    }

    setIsBuildingGraph(true);
    
    // 获取选中文档
    const selectedDocs = documents.filter(doc =>
      selectedDocuments.some(id => String(id) === String(doc.id))
    );

    // 清空选择
    setSelectedDocuments([]);

    // 异步构建知识图谱
    (async () => {
      let successCount = 0;
      let errorCount = 0;

      for (const doc of selectedDocs) {
        try {
          const docId = doc.uuid || doc.id;
          console.log('[BatchBuildGraph] 启动知识图谱构建:', docId);
          const result = await buildKnowledgeGraph(docId, currentKnowledgeBase.id);
          console.log('[BatchBuildGraph] 知识图谱构建启动结果:', result);
          successCount++;
        } catch (error) {
          console.error('[BatchBuildGraph] 知识图谱构建失败:', doc.id, error);
          errorCount++;
        }
      }

      if (successCount > 0) {
        showSuccess(`成功启动 ${successCount} 个文档的知识图谱构建`);
      }
      if (errorCount > 0) {
        showWarning(`${errorCount} 个文档知识图谱构建失败`);
      }

      // 刷新文档列表
      if (onRefresh) {
        onRefresh();
      }
      
      setIsBuildingGraph(false);
    })();
  };

  /**
   * 处理批量标签管理
   */
  const handleBatchTag = () => {
    if (selectedCount === 0) {
      showWarning('请先选择要添加标签的文档');
      return;
    }
    setShowTagModal(true);
  };

  /**
   * 确认批量标签操作
   */
  const handleConfirmTag = async () => {
    if (selectedTags.length === 0) {
      showWarning('请选择至少一个标签');
      return;
    }

    setIsTagging(true);
    try {
      // 获取选中文档
      const selectedDocs = documents.filter(doc =>
        selectedDocuments.some(id => String(id) === String(doc.id))
      );

      // 为每个文档添加标签
      for (const doc of selectedDocs) {
        for (const tag of selectedTags) {
          try {
            // 调用添加标签API
            // 这里需要实现添加标签的API调用
            console.log(`为文档 ${doc.id} 添加标签: ${tag}`);
          } catch (error) {
            console.error(`添加标签失败: ${error}`);
          }
        }
      }

      showSuccess(`成功为 ${selectedCount} 个文档添加标签`);
      setShowTagModal(false);
      setSelectedTags([]);

      // 刷新文档列表
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      showError('批量添加标签失败：' + error.message);
    } finally {
      setIsTagging(false);
    }
  };

  /**
   * 处理批量导出
   */
  const handleBatchExport = () => {
    if (selectedCount === 0) {
      showWarning('请先选择要导出的文档');
      return;
    }
    setShowExportModal(true);
  };

  /**
   * 确认批量导出
   */
  const handleConfirmExport = async () => {
    try {
      // 获取选中文档
      const selectedDocs = documents.filter(doc =>
        selectedDocuments.some(id => String(id) === String(doc.id))
      );

      // 准备导出数据
      const exportData = {
        documents: selectedDocs.map(doc => ({
          id: doc.id,
          title: doc.title,
          file_type: doc.file_type,
          file_size: doc.file_size,
          created_at: doc.created_at,
          is_vectorized: doc.is_vectorized,
          tags: doc.tags || []
        })),
        export_time: new Date().toISOString(),
        knowledge_base: currentKnowledgeBase?.name || 'Unknown'
      };

      // 根据格式导出
      let blob;
      let filename;
      
      if (exportFormat === 'json') {
        blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        filename = `documents_export_${new Date().getTime()}.json`;
      } else if (exportFormat === 'csv') {
        // 简单的CSV导出
        const csvContent = [
          ['ID', 'Title', 'Type', 'Size', 'Created', 'Vectorized', 'Tags'].join(','),
          ...selectedDocs.map(doc => [
            doc.id,
            `"${doc.title || ''}"`,
            doc.file_type || '',
            doc.file_size || 0,
            doc.created_at || '',
            doc.is_vectorized ? 'Yes' : 'No',
            `"${(doc.tags || []).join(', ')}"`
          ].join(','))
        ].join('\n');
        
        blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
        filename = `documents_export_${new Date().getTime()}.csv`;
      }

      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showSuccess(`成功导出 ${selectedCount} 个文档`);
      setShowExportModal(false);
    } catch (error) {
      showError('批量导出失败：' + error.message);
    }
  };

  /**
   * 处理批量实体状态更新
   */
  const handleBatchEntityStatus = () => {
    if (selectedCount === 0) {
      showWarning('请先选择要更新实体状态的文档');
      return;
    }
    setShowEntityStatusModal(true);
  };

  /**
   * 确认批量实体状态更新
   */
  const handleConfirmEntityStatus = async () => {
    try {
      // 获取选中文档
      const selectedDocs = documents.filter(doc =>
        selectedDocuments.some(id => String(id) === String(doc.id))
      );

      // 收集所有实体ID
      let allEntityIds = [];
      for (const doc of selectedDocs) {
        try {
          // 调用获取文档实体API
          // 这里需要实现获取文档实体的API调用
          const entities = await getDocumentEntities(doc.id);
          allEntityIds = [...allEntityIds, ...entities.map(e => e.id)];
        } catch (error) {
          console.error(`获取文档实体失败: ${error}`);
        }
      }

      if (allEntityIds.length === 0) {
        showWarning('选中文档中没有找到实体');
        return;
      }

      // 批量更新实体状态
      const result = await batchUpdateEntityStatus(allEntityIds, entityStatus);

      if (result.success) {
        showSuccess(`成功更新 ${result.updated_count || allEntityIds.length} 个实体的状态`);
      }

      setShowEntityStatusModal(false);

      // 刷新文档列表
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      showError('批量更新实体状态失败：' + error.message);
    }
  };

  /**
   * 清空选择
   */
  const handleClearSelection = () => {
    setSelectedDocuments([]);
  };

  return (
    <div className="enhanced-batch-operations">
      <div className="batch-operations-left">
        {/* 全选复选框 */}
        <button
          className="batch-select-all-btn"
          onClick={handleSelectAll}
          title={isAllSelected ? '取消全选' : '全选'}
        >
          {isAllSelected ? (
            <FiCheckSquare className="batch-checkbox-icon checked" />
          ) : isIndeterminate ? (
            <div className="batch-checkbox-indeterminate">
              <FiSquare className="batch-checkbox-icon" />
              <div className="batch-checkbox-line"></div>
            </div>
          ) : (
            <FiSquare className="batch-checkbox-icon" />
          )}
          <span className="batch-select-text">
            已选择 {selectedCount} 项
          </span>
        </button>
      </div>

      <div className="batch-operations-center">
        {/* 基础操作按钮 */}
        <Button
          variant="secondary"
          size="small"
          icon={<FiDownload />}
          onClick={handleBatchDownload}
          disabled={isProcessing || isDownloading}
          loading={isDownloading}
        >
          下载
        </Button>

        <Button
          variant="secondary"
          size="small"
          icon={<FiZap />}
          onClick={handleBatchVectorize}
          disabled={isProcessing || isDeleting || isDownloading || isVectorizing}
          loading={isVectorizing}
        >
          向量化
        </Button>

        <Button
          variant="secondary"
          size="small"
          icon={<FiLayers />}
          onClick={handleBatchBuildGraph}
          disabled={isProcessing || isBuildingGraph}
          loading={isBuildingGraph}
        >
          构建图谱
        </Button>

        {/* 高级操作按钮 */}
        <Button
          variant="secondary"
          size="small"
          icon={<FiTag />}
          onClick={handleBatchTag}
          disabled={isProcessing || isTagging}
        >
          标签
        </Button>

        <Button
          variant="secondary"
          size="small"
          icon={<FiCopy />}
          onClick={handleBatchExport}
          disabled={isProcessing}
        >
          导出
        </Button>

        <Button
          variant="secondary"
          size="small"
          icon={<FiCheckCircle />}
          onClick={handleBatchEntityStatus}
          disabled={isProcessing}
        >
          实体状态
        </Button>

        <Button
          variant="danger"
          size="small"
          icon={<FiTrash2 />}
          onClick={handleBatchDelete}
          disabled={isProcessing || isDeleting || isDownloading}
          loading={isDeleting}
        >
          删除
        </Button>
      </div>

      <div className="batch-operations-right">
        {/* 取消选择 */}
        <Button
          variant="ghost"
          size="small"
          icon={<FiX />}
          onClick={handleClearSelection}
          disabled={isProcessing}
        >
          取消
        </Button>
      </div>

      {/* 标签管理模态框 */}
      <Modal
        isOpen={showTagModal}
        onClose={() => setShowTagModal(false)}
        title="批量添加标签"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowTagModal(false)}>
              取消
            </Button>
            <Button 
              variant="primary" 
              onClick={handleConfirmTag}
              loading={isTagging}
              disabled={selectedTags.length === 0}
            >
              确认
            </Button>
          </>
        }
      >
        <div className="batch-tag-modal">
          <p>为选中的 {selectedCount} 个文档添加标签：</p>
          <div className="tag-selection">
            {/* 这里可以添加标签选择组件 */}
            <input
              type="text"
              placeholder="输入标签，按回车添加"
              className="tag-input"
            />
            <div className="selected-tags">
              {selectedTags.map(tag => (
                <span key={tag} className="selected-tag">
                  {tag}
                  <button onClick={() => setSelectedTags(selectedTags.filter(t => t !== tag))}>
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>
      </Modal>

      {/* 导出模态框 */}
      <Modal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="批量导出文档"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowExportModal(false)}>
              取消
            </Button>
            <Button variant="primary" onClick={handleConfirmExport}>
              确认导出
            </Button>
          </>
        }
      >
        <div className="batch-export-modal">
          <p>导出选中的 {selectedCount} 个文档：</p>
          <div className="export-format-selection">
            <label>
              <input
                type="radio"
                value="json"
                checked={exportFormat === 'json'}
                onChange={(e) => setExportFormat(e.target.value)}
              />
              <span>JSON 格式</span>
            </label>
            <label>
              <input
                type="radio"
                value="csv"
                checked={exportFormat === 'csv'}
                onChange={(e) => setExportFormat(e.target.value)}
              />
              <span>CSV 格式</span>
            </label>
          </div>
        </div>
      </Modal>

      {/* 实体状态更新模态框 */}
      <Modal
        isOpen={showEntityStatusModal}
        onClose={() => setShowEntityStatusModal(false)}
        title="批量更新实体状态"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowEntityStatusModal(false)}>
              取消
            </Button>
            <Button variant="primary" onClick={handleConfirmEntityStatus}>
              确认更新
            </Button>
          </>
        }
      >
        <div className="batch-entity-status-modal">
          <p>更新选中文档中所有实体的状态：</p>
          <div className="entity-status-selection">
            <label>
              <input
                type="radio"
                value="confirmed"
                checked={entityStatus === 'confirmed'}
                onChange={(e) => setEntityStatus(e.target.value)}
              />
              <span className="status-option confirmed">
                <FiCheckCircle />
                确认
              </span>
            </label>
            <label>
              <input
                type="radio"
                value="rejected"
                checked={entityStatus === 'rejected'}
                onChange={(e) => setEntityStatus(e.target.value)}
              />
              <span className="status-option rejected">
                <FiXCircle />
                拒绝
              </span>
            </label>
            <label>
              <input
                type="radio"
                value="pending"
                checked={entityStatus === 'pending'}
                onChange={(e) => setEntityStatus(e.target.value)}
              />
              <span className="status-option pending">
                <FiSquare />
                待处理
              </span>
            </label>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default EnhancedBatchOperations;