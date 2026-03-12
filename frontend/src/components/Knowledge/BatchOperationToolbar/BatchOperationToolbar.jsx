/**
 * 批量操作工具栏组件
 * 
 * 提供文档批量选择、导出、向量化、删除等操作
 */

import React from 'react';
import { FiDownload, FiTrash2, FiZap, FiX, FiCheckSquare, FiSquare } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../UI';
import './BatchOperationToolbar.css';

/**
 * 批量操作工具栏
 * 
 * 当选中文档时显示，提供批量操作功能
 */
const BatchOperationToolbar = () => {
  const {
    documents,
    selectedDocuments,
    toggleDocumentSelection,
    setSelectedDocuments,
    isProcessing,
  } = useKnowledgeStore();

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
   * 处理批量导出
   */
  const handleBatchExport = () => {
    // TODO: 实现批量导出逻辑
    console.log('批量导出:', selectedDocuments);
  };

  /**
   * 处理批量向量化
   */
  const handleBatchVectorize = () => {
    // TODO: 实现批量向量化逻辑
    console.log('批量向量化:', selectedDocuments);
  };

  /**
   * 处理批量删除
   */
  const handleBatchDelete = () => {
    // TODO: 实现批量删除逻辑
    if (window.confirm(`确定要删除选中的 ${selectedCount} 个文档吗？`)) {
      console.log('批量删除:', selectedDocuments);
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
          onClick={handleBatchExport}
          disabled={isProcessing}
        >
          导出
        </Button>

        <Button
          variant="secondary"
          size="small"
          icon={<FiZap />}
          onClick={handleBatchVectorize}
          disabled={isProcessing}
        >
          向量化
        </Button>

        <Button
          variant="danger"
          size="small"
          icon={<FiTrash2 />}
          onClick={handleBatchDelete}
          disabled={isProcessing}
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
