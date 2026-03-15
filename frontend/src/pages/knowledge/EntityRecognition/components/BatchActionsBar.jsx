/**
 * 批量操作栏组件
 *
 * 提供批量选择和批量操作功能
 */

import React from 'react';
import { Button } from '../../../components/UI';

/**
 * 批量操作栏组件
 */
const BatchActionsBar = ({
  entities,
  selectedEntities,
  filteredEntities,
  handleSelectAllEntities,
  handleClearEntitySelection,
  handleBatchConfirm,
  handleBatchReject,
}) => {
  if (entities.length === 0) return null;

  const isAllSelected = selectedEntities.length === filteredEntities.length && filteredEntities.length > 0;
  const isIndeterminate = selectedEntities.length > 0 && selectedEntities.length < filteredEntities.length;

  return (
    <div className="batch-actions-bar">
      <label className="batch-checkbox">
        <input
          type="checkbox"
          checked={isAllSelected}
          ref={input => {
            if (input) {
              input.indeterminate = isIndeterminate;
            }
          }}
          onChange={(e) => e.target.checked ? handleSelectAllEntities() : handleClearEntitySelection()}
        />
        <span>全选</span>
      </label>
      
      <span className="selection-info">
        已选择 {selectedEntities.length} 个实体
      </span>
      
      <Button
        size="small"
        variant="primary"
        disabled={selectedEntities.length === 0}
        onClick={handleBatchConfirm}
      >
        批量确认
      </Button>
      
      <Button
        size="small"
        variant="danger"
        disabled={selectedEntities.length === 0}
        onClick={handleBatchReject}
      >
        批量拒绝
      </Button>
    </div>
  );
};

export default BatchActionsBar;
