/**
 * 删除确认弹窗组件
 *
 * 提供删除确认功能
 */

import React from 'react';
import Modal from '../../../components/UI/Modal';
import { Button } from '../../../components/UI';

/**
 * 删除确认弹窗组件
 */
const DeleteConfirmModal = ({
  visible,
  onConfirm,
  onCancel,
}) => {
  return (
    <Modal
      isOpen={visible}
      onClose={onCancel}
      title="确认删除"
      size="small"
      footer={
        <>
          <Button variant="ghost" onClick={onCancel}>
            取消
          </Button>
          <Button variant="danger" onClick={onConfirm}>
            确认删除
          </Button>
        </>
      }
    >
      <div className="delete-confirm-content">
        <div className="delete-icon">🗑️</div>
        <p>确定要删除这个实体吗？</p>
        <p className="delete-hint">此操作无法撤销</p>
      </div>
    </Modal>
  );
};

export default DeleteConfirmModal;
