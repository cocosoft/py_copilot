/**
 * 实体确认列表组件
 *
 * 用于文档知识图谱中的实体确认、修改和删除操作，支持原文高亮定位
 */

import React, { useState, useEffect } from 'react';
import './EntityConfirmationList.css';

/**
 * 实体确认列表组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.documentId - 文档ID
 * @param {Array} props.entities - 实体列表
 * @param {Function} props.onConfirm - 确认实体回调
 * @param {Function} props.onModify - 修改实体回调
 * @param {Function} props.onDelete - 删除实体回调
 * @param {Function} props.onHighlight - 高亮定位回调
 * @param {Function} props.onReextract - 重新提取回调
 * @returns {JSX.Element} 实体确认列表界面
 */
const EntityConfirmationList = ({
  documentId,
  entities: initialEntities,
  onConfirm,
  onModify,
  onDelete,
  onHighlight,
  onReextract
}) => {
  // 实体列表
  const [entities, setEntities] = useState([]);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 筛选状态
  const [filter, setFilter] = useState('all'); // all, pending, confirmed, rejected
  // 类型筛选
  const [typeFilter, setTypeFilter] = useState('');
  // 搜索关键词
  const [searchKeyword, setSearchKeyword] = useState('');
  // 编辑中的实体
  const [editingEntity, setEditingEntity] = useState(null);
  // 编辑表单数据
  const [editForm, setEditForm] = useState({});
  // 批量选中的实体
  const [selectedIds, setSelectedIds] = useState([]);
  // 显示批量操作栏
  const [showBatchActions, setShowBatchActions] = useState(false);

  // 初始化实体列表
  useEffect(() => {
    if (initialEntities) {
      setEntities(initialEntities.map(e => ({
        ...e,
        status: e.status || 'pending' // pending, confirmed, rejected
      })));
    } else {
      loadEntities();
    }
  }, [initialEntities, documentId]);

  // 加载实体数据
  const loadEntities = async () => {
    if (!documentId) return;

    setLoading(true);
    // TODO: 调用API获取文档实体
    setTimeout(() => {
      const mockEntities = [
        { id: 1, name: '张三', type: 'PERSON', confidence: 0.95, status: 'pending', position: { start: 100, end: 102 }, context: '张三是一位资深工程师' },
        { id: 2, name: 'ABC公司', type: 'ORG', confidence: 0.88, status: 'confirmed', position: { start: 200, end: 205 }, context: 'ABC公司成立于2010年' },
        { id: 3, name: '北京', type: 'LOCATION', confidence: 0.92, status: 'pending', position: { start: 350, end: 352 }, context: '公司总部位于北京' },
        { id: 4, name: '李四', type: 'PERSON', confidence: 0.75, status: 'rejected', position: { start: 500, end: 502 }, context: '李四提出了不同意见' },
        { id: 5, name: '人工智能', type: 'CONCEPT', confidence: 0.85, status: 'pending', position: { start: 800, end: 804 }, context: '人工智能技术的应用' }
      ];
      setEntities(mockEntities);
      setLoading(false);
    }, 800);
  };

  // 获取筛选后的实体
  const filteredEntities = entities.filter(entity => {
    // 状态筛选
    if (filter !== 'all' && entity.status !== filter) return false;
    // 类型筛选
    if (typeFilter && entity.type !== typeFilter) return false;
    // 搜索筛选
    if (searchKeyword && !entity.name.toLowerCase().includes(searchKeyword.toLowerCase())) return false;
    return true;
  });

  // 获取统计信息
  const stats = {
    total: entities.length,
    pending: entities.filter(e => e.status === 'pending').length,
    confirmed: entities.filter(e => e.status === 'confirmed').length,
    rejected: entities.filter(e => e.status === 'rejected').length
  };

  // 获取实体类型选项
  const entityTypes = [...new Set(entities.map(e => e.type))];

  // 获取实体类型标签
  const getEntityTypeLabel = (type) => {
    const typeMap = {
      'PERSON': '人物',
      'ORG': '组织',
      'LOCATION': '地点',
      'TIME': '时间',
      'EVENT': '事件',
      'CONCEPT': '概念',
      'PRODUCT': '产品'
    };
    return typeMap[type] || type;
  };

  // 获取状态标签
  const getStatusLabel = (status) => {
    const statusMap = {
      'pending': { label: '待确认', color: '#f59e0b' },
      'confirmed': { label: '已确认', color: '#10b981' },
      'rejected': { label: '已拒绝', color: '#ef4444' }
    };
    return statusMap[status] || { label: status, color: '#6b7280' };
  };

  // 确认实体
  const handleConfirm = (entity) => {
    const updated = entities.map(e =>
      e.id === entity.id ? { ...e, status: 'confirmed' } : e
    );
    setEntities(updated);
    if (onConfirm) onConfirm(entity);
  };

  // 拒绝实体
  const handleReject = (entity) => {
    const updated = entities.map(e =>
      e.id === entity.id ? { ...e, status: 'rejected' } : e
    );
    setEntities(updated);
    if (onDelete) onDelete(entity);
  };

  // 开始编辑
  const handleEdit = (entity) => {
    setEditingEntity(entity);
    setEditForm({
      name: entity.name,
      type: entity.type,
      confidence: entity.confidence
    });
  };

  // 保存编辑
  const handleSaveEdit = () => {
    if (!editingEntity) return;

    const updated = entities.map(e =>
      e.id === editingEntity.id
        ? { ...e, ...editForm, status: 'confirmed' }
        : e
    );
    setEntities(updated);
    if (onModify) onModify({ ...editingEntity, ...editForm });
    setEditingEntity(null);
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setEditingEntity(null);
    setEditForm({});
  };

  // 高亮定位
  const handleHighlight = (entity) => {
    if (onHighlight) onHighlight(entity.position);
  };

  // 批量确认
  const handleBatchConfirm = () => {
    const updated = entities.map(e =>
      selectedIds.includes(e.id) ? { ...e, status: 'confirmed' } : e
    );
    setEntities(updated);
    setSelectedIds([]);
    setShowBatchActions(false);
  };

  // 批量拒绝
  const handleBatchReject = () => {
    const updated = entities.map(e =>
      selectedIds.includes(e.id) ? { ...e, status: 'rejected' } : e
    );
    setEntities(updated);
    setSelectedIds([]);
    setShowBatchActions(false);
  };

  // 选择/取消选择实体
  const toggleSelection = (id) => {
    setSelectedIds(prev => {
      const newSelection = prev.includes(id)
        ? prev.filter(i => i !== id)
        : [...prev, id];
      setShowBatchActions(newSelection.length > 0);
      return newSelection;
    });
  };

  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedIds.length === filteredEntities.length) {
      setSelectedIds([]);
      setShowBatchActions(false);
    } else {
      setSelectedIds(filteredEntities.map(e => e.id));
      setShowBatchActions(true);
    }
  };

  return (
    <div className="entity-confirmation-list">
      {/* 头部统计 */}
      <div className="confirmation-header">
        <div className="stats-cards">
          <div className="stat-card" onClick={() => setFilter('all')}>
            <span className="stat-value">{stats.total}</span>
            <span className="stat-label">全部</span>
          </div>
          <div className="stat-card pending" onClick={() => setFilter('pending')}>
            <span className="stat-value">{stats.pending}</span>
            <span className="stat-label">待确认</span>
          </div>
          <div className="stat-card confirmed" onClick={() => setFilter('confirmed')}>
            <span className="stat-value">{stats.confirmed}</span>
            <span className="stat-label">已确认</span>
          </div>
          <div className="stat-card rejected" onClick={() => setFilter('rejected')}>
            <span className="stat-value">{stats.rejected}</span>
            <span className="stat-label">已拒绝</span>
          </div>
        </div>

        {/* 工具栏 */}
        <div className="confirmation-toolbar">
          <div className="search-box">
            <input
              type="text"
              placeholder="搜索实体..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
          </div>
          <select
            className="type-filter"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">所有类型</option>
            {entityTypes.map(type => (
              <option key={type} value={type}>{getEntityTypeLabel(type)}</option>
            ))}
          </select>
          <button className="reextract-btn" onClick={onReextract}>
            🔄 重新提取
          </button>
        </div>
      </div>

      {/* 批量操作栏 */}
      {showBatchActions && (
        <div className="batch-actions-bar">
          <span className="selected-count">已选择 {selectedIds.length} 个实体</span>
          <div className="batch-buttons">
            <button className="btn-batch-confirm" onClick={handleBatchConfirm}>
              ✓ 批量确认
            </button>
            <button className="btn-batch-reject" onClick={handleBatchReject}>
              ✕ 批量拒绝
            </button>
            <button className="btn-clear" onClick={() => { setSelectedIds([]); setShowBatchActions(false); }}>
              清除选择
            </button>
          </div>
        </div>
      )}

      {/* 实体列表 */}
      <div className="entities-list-container">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>加载实体数据...</p>
          </div>
        ) : filteredEntities.length > 0 ? (
          <>
            {/* 表头 */}
            <div className="list-header">
              <label className="checkbox-wrapper">
                <input
                  type="checkbox"
                  checked={selectedIds.length === filteredEntities.length && filteredEntities.length > 0}
                  onChange={toggleSelectAll}
                />
              </label>
              <span className="header-cell">实体名称</span>
              <span className="header-cell">类型</span>
              <span className="header-cell">置信度</span>
              <span className="header-cell">状态</span>
              <span className="header-cell">上下文</span>
              <span className="header-cell">操作</span>
            </div>

            {/* 实体项 */}
            <div className="entities-list">
              {filteredEntities.map(entity => (
                <div
                  key={entity.id}
                  className={`entity-item ${entity.status} ${selectedIds.includes(entity.id) ? 'selected' : ''}`}
                >
                  {editingEntity?.id === entity.id ? (
                    // 编辑模式
                    <div className="edit-row">
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="edit-input"
                      />
                      <select
                        value={editForm.type}
                        onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
                        className="edit-select"
                      >
                        <option value="PERSON">人物</option>
                        <option value="ORG">组织</option>
                        <option value="LOCATION">地点</option>
                        <option value="TIME">时间</option>
                        <option value="EVENT">事件</option>
                        <option value="CONCEPT">概念</option>
                        <option value="PRODUCT">产品</option>
                      </select>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={editForm.confidence}
                        onChange={(e) => setEditForm({ ...editForm, confidence: parseFloat(e.target.value) })}
                        className="edit-input confidence"
                      />
                      <div className="edit-actions">
                        <button className="btn-save" onClick={handleSaveEdit}>✓</button>
                        <button className="btn-cancel" onClick={handleCancelEdit}>✕</button>
                      </div>
                    </div>
                  ) : (
                    // 显示模式
                    <>
                      <label className="checkbox-wrapper">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(entity.id)}
                          onChange={() => toggleSelection(entity.id)}
                        />
                      </label>
                      <span className="entity-cell name">{entity.name}</span>
                      <span className="entity-cell type">
                        <span className="type-badge">{getEntityTypeLabel(entity.type)}</span>
                      </span>
                      <span className="entity-cell confidence">
                        {(entity.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="entity-cell status">
                        <span
                          className="status-badge"
                          style={{ backgroundColor: getStatusLabel(entity.status).color + '20', color: getStatusLabel(entity.status).color }}
                        >
                          {getStatusLabel(entity.status).label}
                        </span>
                      </span>
                      <span className="entity-cell context" title={entity.context}>
                        {entity.context}
                      </span>
                      <span className="entity-cell actions">
                        {entity.status === 'pending' && (
                          <>
                            <button
                              className="action-btn confirm"
                              onClick={() => handleConfirm(entity)}
                              title="确认"
                            >
                              ✓
                            </button>
                            <button
                              className="action-btn reject"
                              onClick={() => handleReject(entity)}
                              title="拒绝"
                            >
                              ✕
                            </button>
                          </>
                        )}
                        <button
                          className="action-btn edit"
                          onClick={() => handleEdit(entity)}
                          title="编辑"
                        >
                          ✏️
                        </button>
                        <button
                          className="action-btn highlight"
                          onClick={() => handleHighlight(entity)}
                          title="定位"
                        >
                          📍
                        </button>
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <span className="empty-icon">📋</span>
            <p>暂无实体数据</p>
            <button className="reextract-btn-large" onClick={onReextract}>
              重新提取实体
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default EntityConfirmationList;
