/**
 * 实体项组件
 *
 * 显示单个实体信息和操作按钮
 */

import React from 'react';
import { FiCheck, FiX, FiEdit2, FiTrash2 } from 'react-icons/fi';

/**
 * 实体类型配置
 */
const ENTITY_TYPES = [
  { value: 'person', label: '人物', color: '#1890ff' },
  { value: 'organization', label: '组织', color: '#52c41a' },
  { value: 'location', label: '地点', color: '#faad14' },
  { value: 'time', label: '时间', color: '#722ed1' },
  { value: 'event', label: '事件', color: '#eb2f96' },
  { value: 'concept', label: '概念', color: '#13c2c2' },
  { value: 'product', label: '产品', color: '#f5222d' },
  { value: 'technology', label: '技术', color: '#2f54eb' },
];

/**
 * 实体状态配置
 */
const ENTITY_STATUS = {
  pending: { label: '待确认', color: '#faad14', bgColor: '#fffbe6' },
  confirmed: { label: '已确认', color: '#52c41a', bgColor: '#f6ffed' },
  rejected: { label: '已拒绝', color: '#ff4d4f', bgColor: '#fff2f0' },
  modified: { label: '已修改', color: '#1890ff', bgColor: '#e6f7ff' },
};

/**
 * 实体项组件
 */
const EntityItem = ({
  entity,
  isSelected,
  editingEntity,
  editForm,
  setEditForm,
  onToggleSelection,
  onConfirm,
  onReject,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onDelete,
}) => {
  const typeConfig = ENTITY_TYPES.find(t => t.value === entity.type) || ENTITY_TYPES[5];
  const statusConfig = ENTITY_STATUS[entity.status] || ENTITY_STATUS.pending;
  const isEditing = editingEntity === entity.id;

  return (
    <div className={`entity-item ${entity.status}`}>
      {isEditing ? (
        <div className="entity-edit-form">
          <input
            type="text"
            value={editForm.name}
            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            className="edit-input"
            placeholder="实体名称"
          />
          <select
            value={editForm.type}
            onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
            className="edit-select"
          >
            {ENTITY_TYPES.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={editForm.description}
            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
            className="edit-input"
            placeholder="描述（可选）"
          />
          <div className="edit-actions">
            <button className="save-btn" onClick={() => onSaveEdit(entity.id)} aria-label="保存修改">
              <FiCheck size={16} />
            </button>
            <button className="cancel-btn" onClick={onCancelEdit} aria-label="取消编辑">
              <FiX size={16} />
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="entity-checkbox">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onToggleSelection(entity.id)}
            />
          </div>
          
          <div className="entity-info">
            <div className="entity-header">
              <span
                className="entity-type-badge"
                style={{ backgroundColor: typeConfig.color + '20', color: typeConfig.color }}
              >
                {typeConfig.label}
              </span>
              <span
                className="entity-status-badge"
                style={{ backgroundColor: statusConfig.bgColor, color: statusConfig.color }}
              >
                {statusConfig.label}
              </span>
            </div>
            <h4 className="entity-name">{entity.name}</h4>
            {entity.description && (
              <p className="entity-description">{entity.description}</p>
            )}
            <div className="entity-meta">
              <span>来源: {entity.documentName}</span>
              <span>置信度: {(entity.confidence * 100).toFixed(1)}%</span>
              <span>出现次数: {entity.occurrences}</span>
            </div>
          </div>
          
          <div className="entity-actions">
            {entity.status === 'pending' && (
              <>
                <button
                  className="action-btn confirm"
                  onClick={() => onConfirm(entity.id)}
                  title="确认"
                  aria-label="确认实体"
                >
                  <FiCheck size={16} />
                </button>
                <button
                  className="action-btn reject"
                  onClick={() => onReject(entity.id)}
                  title="拒绝"
                  aria-label="拒绝实体"
                >
                  <FiX size={16} />
                </button>
              </>
            )}
            <button
              className="action-btn edit"
              onClick={() => onStartEdit(entity)}
              title="编辑"
              aria-label="编辑实体"
            >
              <FiEdit2 size={16} />
            </button>
            <button
              className="action-btn delete"
              onClick={() => onDelete(entity.id)}
              title="删除"
              aria-label="删除实体"
            >
              <FiTrash2 size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default EntityItem;
