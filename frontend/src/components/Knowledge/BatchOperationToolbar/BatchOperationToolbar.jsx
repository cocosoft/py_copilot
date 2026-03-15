/**
 * 批量操作工具栏组件
 *
 * 提供文档批量选择、导出、向量化、删除等操作
 */

import React, { useState } from 'react';
import { FiDownload, FiTrash2, FiZap, FiX, FiCheckSquare, FiSquare } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button, showSuccess, showError, showWarning } from '../../UI';
import { batchDeleteDocuments, batchDownloadDocuments, processDocument } from '../../../utils/api/knowledgeApi';
import websocketService from '../../../services/websocketService';
import './BatchOperationToolbar.css';

/**
 * 批量操作工具栏
 *
 * 当选中文档时显示，提供批量操作功能
 *
 * @param {Object} props - 组件属性
 * @param {Function} props.onBatchVectorizeStart - 批量向量化开始回调，接收文档ID数组
 */
const BatchOperationToolbar = ({ onBatchVectorizeStart }) => {
  const {
    documents,
    selectedDocuments,
    toggleDocumentSelection,
    setSelectedDocuments,
    isProcessing,
    fetchDocuments,
    currentKnowledgeBase,
  } = useKnowledgeStore();

  const [isDeleting, setIsDeleting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isVectorizing, setIsVectorizing] = useState(false);

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
    try {
      // 获取选中文档
      const selectedDocs = documents.filter(doc =>
        selectedDocuments.some(id => String(id) === String(doc.id))
      );

      // 依次处理每个文档
      let successCount = 0;
      let errorCount = 0;
      const successfullyStartedDocs = [];

      for (const doc of selectedDocs) {
        try {
          const docId = doc.uuid || doc.id;
          console.log('[BatchVectorize] 启动文档处理:', docId);
          console.log('[BatchVectorize] 调用processDocument API...');
          const result = await processDocument(docId);
          console.log('[BatchVectorize] 文档处理启动结果:', result);
          successCount++;
          successfullyStartedDocs.push(doc);
        } catch (error) {
          console.error('[BatchVectorize] 向量化失败:', doc.id, error);
          errorCount++;
        }
      }

      // 只有在API调用成功后才显示进度面板
      if (successfullyStartedDocs.length > 0 && onBatchVectorizeStart) {
        console.log('[BatchVectorize] 调用父组件回调，显示进度面板:', successfullyStartedDocs);
        onBatchVectorizeStart(successfullyStartedDocs);
      }

      if (successCount > 0) {
        showSuccess(`成功启动 ${successCount} 个文档的向量化`);
      }
      if (errorCount > 0) {
        showWarning(`${errorCount} 个文档向量化失败`);
      }

      // 清空选择
      setSelectedDocuments([]);

      // 刷新文档列表
      if (currentKnowledgeBase) {
        fetchDocuments(currentKnowledgeBase.id);
      }
    } catch (error) {
      showError('批量向量化失败：' + error.message);
    } finally {
      setIsVectorizing(false);
    }
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
      if (currentKnowledgeBase) {
        fetchDocuments(currentKnowledgeBase.id);
      }
    } catch (error) {
      showError('批量删除失败：' + error.message);
    } finally {
      setIsDeleting(false);
    }
  };

  /**
   * 清空选择
   */
  const handleClearSelection = () => {
    setSelectedDocuments([]);
  };

  return (
    <div className="batch-operation-toolbar">
      <div className="batch-toolbar-left">
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

      <div className="batch-toolbar-center">
        {/* 批量操作按钮 */}
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

      <div className="batch-toolbar-right">
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
    </div>
  );
};

export default BatchOperationToolbar;
