/**
 * 关系管理组件
 *
 * 用于管理知识图谱中的关系，支持关系的增删改查操作
 */

import React, { useState, useEffect, useRef } from 'react';
import { getRelations, getRelationTypes } from '../../utils/api/knowledgeGraphApi';
import { showNotification, NotificationType } from '../UI/Notification';
import HierarchyNavigator from '../Hierarchy/HierarchyNavigator';
import HierarchyViewContainer from '../Hierarchy/HierarchyViewContainer';
import './RelationManagement.css';

/**
 * 关系管理组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @returns {JSX.Element} 关系管理界面
 */
const RelationManagement = ({ knowledgeBaseId }) => {
  // 关系列表
  const [relations, setRelations] = useState([]);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 筛选状态
  const [filter, setFilter] = useState('all'); // all, active, inactive
  // 搜索关键词
  const [searchKeyword, setSearchKeyword] = useState('');
  // 高级过滤选项
  const [advancedFilters, setAdvancedFilters] = useState({
    relationType: '',
    sourceEntityType: '',
    targetEntityType: '',
    minConfidence: 0,
    maxConfidence: 1,
    startDate: '',
    endDate: ''
  });
  // 显示高级过滤面板
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  // 关系类型
  const [relationTypes, setRelationTypes] = useState([]);
  // 文件输入引用
  const fileInputRef = useRef(null);
  // 批量选中的关系
  const [selectedIds, setSelectedIds] = useState([]);
  // 显示批量操作栏
  const [showBatchActions, setShowBatchActions] = useState(false);
  // 编辑中的关系
  const [editingRelation, setEditingRelation] = useState(null);
  // 编辑表单数据
  const [editForm, setEditForm] = useState({});
  // 显示创建关系对话框
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  // 创建表单数据
  const [createForm, setCreateForm] = useState({
    sourceEntity: '',
    targetEntity: '',
    relationType: '',
    properties: {}
  });

  // 初始化数据
  useEffect(() => {
    if (knowledgeBaseId) {
      loadRelations();
      loadRelationTypes();
    }
  }, [knowledgeBaseId]);

  // 加载关系列表
  const loadRelations = async () => {
    setLoading(true);
    try {
      // 调用API获取关系列表
      const response = await getRelations(knowledgeBaseId, {
        filter: filter,
        keyword: searchKeyword,
        ...advancedFilters
      });
      setRelations(response.data);
    } catch (error) {
      console.error('加载关系列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 加载关系类型
  const loadRelationTypes = async () => {
    try {
      // 调用API获取关系类型
      const response = await getRelationTypes();
      setRelationTypes(response.data);
    } catch (error) {
      console.error('加载关系类型失败:', error);
    }
  };

  // 获取筛选后的关系
  const filteredRelations = relations.filter(relation => {
    // 状态筛选
    if (filter !== 'all' && relation.status !== filter) return false;
    
    // 搜索筛选
    if (searchKeyword) {
      const keyword = searchKeyword.toLowerCase();
      const match = (
        relation.sourceEntity.toLowerCase().includes(keyword) ||
        relation.targetEntity.toLowerCase().includes(keyword) ||
        relation.relationType.toLowerCase().includes(keyword)
      );
      if (!match) return false;
    }
    
    // 高级过滤
    // 关系类型过滤
    if (advancedFilters.relationType && relation.relationTypeId !== advancedFilters.relationType) {
      return false;
    }
    
    // 源实体类型过滤
    if (advancedFilters.sourceEntityType && relation.sourceEntityType !== advancedFilters.sourceEntityType) {
      return false;
    }
    
    // 目标实体类型过滤
    if (advancedFilters.targetEntityType && relation.targetEntityType !== advancedFilters.targetEntityType) {
      return false;
    }
    
    // 置信度范围过滤
    if (relation.confidence < advancedFilters.minConfidence || relation.confidence > advancedFilters.maxConfidence) {
      return false;
    }
    
    // 时间范围过滤
    if (advancedFilters.startDate) {
      const relationDate = new Date(relation.createdAt);
      const startDate = new Date(advancedFilters.startDate);
      if (relationDate < startDate) return false;
    }
    
    if (advancedFilters.endDate) {
      const relationDate = new Date(relation.createdAt);
      const endDate = new Date(advancedFilters.endDate);
      // 结束日期包含当天
      endDate.setHours(23, 59, 59, 999);
      if (relationDate > endDate) return false;
    }
    
    return true;
  });

  // 选择/取消选择关系
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
    if (selectedIds.length === filteredRelations.length) {
      setSelectedIds([]);
      setShowBatchActions(false);
    } else {
      setSelectedIds(filteredRelations.map(r => r.id));
      setShowBatchActions(true);
    }
  };

  // 批量删除
  const handleBatchDelete = () => {
    if (window.confirm(`确定要删除选中的 ${selectedIds.length} 个关系吗？`)) {
      const updated = relations.filter(r => !selectedIds.includes(r.id));
      setRelations(updated);
      setSelectedIds([]);
      setShowBatchActions(false);
      showNotification({
        title: '批量删除成功',
        message: `已删除 ${selectedIds.length} 个关系`,
        type: NotificationType.SUCCESS
      });
    }
  };

  // 批量激活/停用
  const handleBatchToggleStatus = (status) => {
    const updated = relations.map(r => 
      selectedIds.includes(r.id) ? { ...r, status } : r
    );
    setRelations(updated);
    setSelectedIds([]);
    setShowBatchActions(false);
    showNotification({
      title: status === 'active' ? '批量激活成功' : '批量停用成功',
      message: `已${status === 'active' ? '激活' : '停用'} ${selectedIds.length} 个关系`,
      type: NotificationType.SUCCESS
    });
  };

  // 开始编辑
  const handleEdit = (relation) => {
    setEditingRelation(relation);
    setEditForm({
      relationType: relation.relationTypeId,
      properties: { ...relation.properties }
    });
  };

  // 保存编辑
  const handleSaveEdit = () => {
    if (!editingRelation) return;

    const updated = relations.map(r =>
      r.id === editingRelation.id
        ? {
            ...r,
            relationTypeId: editForm.relationType,
            relationType: relationTypes.find(t => t.id === editForm.relationType)?.name || r.relationType,
            properties: editForm.properties
          }
        : r
    );
    setRelations(updated);
    setEditingRelation(null);
    setEditForm({});
    showNotification({
      title: '编辑成功',
      message: '关系信息已更新',
      type: NotificationType.SUCCESS
    });
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setEditingRelation(null);
    setEditForm({});
  };

  // 删除关系
  const handleDelete = (relation) => {
    if (window.confirm(`确定要删除关系 "${relation.sourceEntity} ${relation.relationType} ${relation.targetEntity}" 吗？`)) {
      const updated = relations.filter(r => r.id !== relation.id);
      setRelations(updated);
      showNotification({
        title: '删除成功',
        message: `关系 "${relation.sourceEntity} ${relation.relationType} ${relation.targetEntity}" 已删除`,
        type: NotificationType.SUCCESS
      });
    }
  };

  // 切换关系状态
  const handleToggleStatus = (relation) => {
    const newStatus = relation.status === 'active' ? 'inactive' : 'active';
    const updated = relations.map(r =>
      r.id === relation.id ? { ...r, status: newStatus } : r
    );
    setRelations(updated);
    showNotification({
      title: newStatus === 'active' ? '激活成功' : '停用成功',
      message: `关系 "${relation.sourceEntity} ${relation.relationType} ${relation.targetEntity}" 已${newStatus === 'active' ? '激活' : '停用'}`,
      type: NotificationType.SUCCESS
    });
  };

  // 打开创建对话框
  const handleOpenCreateDialog = () => {
    setCreateForm({
      sourceEntity: '',
      targetEntity: '',
      relationType: '',
      properties: {}
    });
    setShowCreateDialog(true);
  };

  // 关闭创建对话框
  const handleCloseCreateDialog = () => {
    setShowCreateDialog(false);
  };

  // 提交创建表单
  const handleSubmitCreate = () => {
    // TODO: 验证表单
    if (!createForm.sourceEntity || !createForm.targetEntity || !createForm.relationType) {
      showNotification({
        title: '验证失败',
        message: '请填写完整的关系信息',
        type: NotificationType.ERROR
      });
      return;
    }

    const newRelation = {
      id: `rel-${Date.now()}`,
      sourceEntity: createForm.sourceEntity,
      sourceEntityId: `entity-${Date.now()}-1`,
      sourceEntityType: 'PERSON',
      targetEntity: createForm.targetEntity,
      targetEntityId: `entity-${Date.now()}-2`,
      targetEntityType: 'ORG',
      relationType: relationTypes.find(t => t.id === createForm.relationType)?.name || '',
      relationTypeId: createForm.relationType,
      confidence: 0.9,
      properties: createForm.properties,
      status: 'active',
      createdAt: new Date().toISOString()
    };

    setRelations([...relations, newRelation]);
    setShowCreateDialog(false);
    showNotification({
      title: '创建成功',
      message: `关系 "${newRelation.sourceEntity} ${newRelation.relationType} ${newRelation.targetEntity}" 已创建`,
      type: NotificationType.SUCCESS
    });
  };

  // 刷新数据
  const handleRefresh = () => {
    loadRelations();
    showNotification({
      title: '刷新成功',
      message: '关系数据已更新',
      type: NotificationType.SUCCESS
    });
  };

  // 导出关系数据
  const handleExport = () => {
    if (relations.length === 0) {
      showNotification({
        title: '导出失败',
        message: '暂无关系数据可导出',
        type: NotificationType.ERROR
      });
      return;
    }

    // 准备导出数据
    const exportData = relations.map(relation => ({
      id: relation.id,
      sourceEntity: relation.sourceEntity,
      sourceEntityType: relation.sourceEntityType,
      targetEntity: relation.targetEntity,
      targetEntityType: relation.targetEntityType,
      relationType: relation.relationType,
      confidence: relation.confidence,
      properties: relation.properties,
      status: relation.status,
      createdAt: relation.createdAt
    }));

    // 导出为 JSON 文件
    const jsonData = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `relations_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification({
      title: '导出成功',
      message: `已导出 ${relations.length} 个关系数据`,
      type: NotificationType.SUCCESS
    });
  };

  // 触发导入文件选择
  const handleImport = () => {
    fileInputRef.current?.click();
  };

  // 处理文件导入
  const handleFileImport = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const importedData = JSON.parse(event.target.result);
        
        if (!Array.isArray(importedData)) {
          throw new Error('导入文件格式错误');
        }

        // 验证导入数据格式
        const validData = importedData.filter(item => {
          return item.sourceEntity && item.targetEntity && item.relationType;
        });

        if (validData.length === 0) {
          throw new Error('导入文件中没有有效的关系数据');
        }

        // 生成新的关系数据
        const newRelations = validData.map((item, index) => ({
          id: `imported_${Date.now()}_${index}`,
          sourceEntity: item.sourceEntity,
          sourceEntityId: `entity_${Date.now()}_${index}_1`,
          sourceEntityType: item.sourceEntityType || 'PERSON',
          targetEntity: item.targetEntity,
          targetEntityId: `entity_${Date.now()}_${index}_2`,
          targetEntityType: item.targetEntityType || 'ORG',
          relationType: item.relationType,
          relationTypeId: relationTypes.find(t => t.name === item.relationType)?.id || 'rel-1',
          confidence: item.confidence || 0.9,
          properties: item.properties || {},
          status: item.status || 'active',
          createdAt: item.createdAt || new Date().toISOString()
        }));

        // 添加到现有关系中
        setRelations(prev => [...prev, ...newRelations]);

        showNotification({
          title: '导入成功',
          message: `已导入 ${newRelations.length} 个关系数据`,
          type: NotificationType.SUCCESS
        });
      } catch (error) {
        showNotification({
          title: '导入失败',
          message: `导入文件格式错误：${error.message}`,
          type: NotificationType.ERROR
        });
      }
    };
    reader.onerror = () => {
      showNotification({
        title: '导入失败',
        message: '读取文件失败',
        type: NotificationType.ERROR
      });
    };
    reader.readAsText(file);

    // 重置文件输入
    e.target.value = '';
  };

  return (
    <div className="relation-management">
      {/* 层级导航器 */}
      <HierarchyNavigator />
      
      {/* 层级视图容器 */}
      <div className="hierarchy-view-container">
        <HierarchyViewContainer knowledgeBaseId={knowledgeBaseId} />
      </div>
      
      {/* 头部 */}
      <div className="relation-header">
        <h3>关系管理</h3>
        <div className="relation-actions">
          <div className="search-box">
            <input
              type="text"
              placeholder="搜索关系..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
          </div>
          <button className="btn-primary" onClick={handleOpenCreateDialog}>
            ➕ 新建关系
          </button>
          <button className="btn-secondary" onClick={handleRefresh} title="刷新">
            🔄
          </button>
          <button className="btn-secondary" onClick={handleExport} title="导出关系">
            📤 导出
          </button>
          <button className="btn-secondary" onClick={handleImport} title="导入关系">
            📥 导入
          </button>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".json,.csv"
            onChange={handleFileImport}
          />
        </div>
      </div>

      {/* 筛选栏 */}
      <div className="relation-filters">
        <div className="filter-group">
          <label>状态：</label>
          <div className="filter-buttons">
            <button
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              全部
            </button>
            <button
              className={`filter-btn ${filter === 'active' ? 'active' : ''}`}
              onClick={() => setFilter('active')}
            >
              活跃
            </button>
            <button
              className={`filter-btn ${filter === 'inactive' ? 'active' : ''}`}
              onClick={() => setFilter('inactive')}
            >
              停用
            </button>
          </div>
          <button
            className="advanced-filter-toggle"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          >
            ⚙️ {showAdvancedFilters ? '收起高级过滤' : '高级过滤'}
          </button>
        </div>
        
        {/* 高级过滤面板 */}
        {showAdvancedFilters && (
          <div className="advanced-filter-panel">
            <div className="advanced-filter-row">
              <div className="advanced-filter-item">
                <label>关系类型：</label>
                <select
                  value={advancedFilters.relationType}
                  onChange={(e) => setAdvancedFilters({ ...advancedFilters, relationType: e.target.value })}
                >
                  <option value="">全部</option>
                  {relationTypes.map(type => (
                    <option key={type.id} value={type.id}>{type.name}</option>
                  ))}
                </select>
              </div>
              <div className="advanced-filter-item">
                <label>源实体类型：</label>
                <select
                  value={advancedFilters.sourceEntityType}
                  onChange={(e) => setAdvancedFilters({ ...advancedFilters, sourceEntityType: e.target.value })}
                >
                  <option value="">全部</option>
                  <option value="PERSON">人物</option>
                  <option value="ORG">组织</option>
                  <option value="LOCATION">地点</option>
                  <option value="EVENT">事件</option>
                  <option value="CONCEPT">概念</option>
                </select>
              </div>
              <div className="advanced-filter-item">
                <label>目标实体类型：</label>
                <select
                  value={advancedFilters.targetEntityType}
                  onChange={(e) => setAdvancedFilters({ ...advancedFilters, targetEntityType: e.target.value })}
                >
                  <option value="">全部</option>
                  <option value="PERSON">人物</option>
                  <option value="ORG">组织</option>
                  <option value="LOCATION">地点</option>
                  <option value="EVENT">事件</option>
                  <option value="CONCEPT">概念</option>
                </select>
              </div>
            </div>
            
            <div className="advanced-filter-row">
              <div className="advanced-filter-item">
                <label>置信度范围：</label>
                <div className="confidence-range">
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={advancedFilters.minConfidence}
                    onChange={(e) => setAdvancedFilters({ ...advancedFilters, minConfidence: parseFloat(e.target.value) || 0 })}
                    placeholder="最小"
                  />
                  <span>至</span>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={advancedFilters.maxConfidence}
                    onChange={(e) => setAdvancedFilters({ ...advancedFilters, maxConfidence: parseFloat(e.target.value) || 1 })}
                    placeholder="最大"
                  />
                </div>
              </div>
            </div>
            
            <div className="advanced-filter-row">
              <div className="advanced-filter-item">
                <label>创建时间：</label>
                <div className="date-range">
                  <input
                    type="date"
                    value={advancedFilters.startDate}
                    onChange={(e) => setAdvancedFilters({ ...advancedFilters, startDate: e.target.value })}
                  />
                  <span>至</span>
                  <input
                    type="date"
                    value={advancedFilters.endDate}
                    onChange={(e) => setAdvancedFilters({ ...advancedFilters, endDate: e.target.value })}
                  />
                </div>
              </div>
            </div>
            
            <div className="advanced-filter-actions">
              <button
                className="btn-secondary"
                onClick={() => setAdvancedFilters({
                  relationType: '',
                  sourceEntityType: '',
                  targetEntityType: '',
                  minConfidence: 0,
                  maxConfidence: 1,
                  startDate: '',
                  endDate: ''
                })}
              >
                重置过滤
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 批量操作栏 */}
      {showBatchActions && (
        <div className="batch-actions-bar">
          <span className="selected-count">已选择 {selectedIds.length} 个关系</span>
          <div className="batch-buttons">
            <button className="btn-batch-delete" onClick={handleBatchDelete}>
              ✕ 批量删除
            </button>
            <button className="btn-batch-activate" onClick={() => handleBatchToggleStatus('active')}>
              ✓ 批量激活
            </button>
            <button className="btn-batch-deactivate" onClick={() => handleBatchToggleStatus('inactive')}>
              ⏸ 批量停用
            </button>
            <button className="btn-clear" onClick={() => { setSelectedIds([]); setShowBatchActions(false); }}>
              清除选择
            </button>
          </div>
        </div>
      )}

      {/* 关系列表 */}
      <div className="relations-list-container">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>加载关系数据...</p>
          </div>
        ) : filteredRelations.length > 0 ? (
          <>
            {/* 表头 */}
            <div className="list-header">
              <label className="checkbox-wrapper">
                <input
                  type="checkbox"
                  checked={selectedIds.length === filteredRelations.length && filteredRelations.length > 0}
                  onChange={toggleSelectAll}
                />
              </label>
              <span className="header-cell">源实体</span>
              <span className="header-cell">关系类型</span>
              <span className="header-cell">目标实体</span>
              <span className="header-cell">置信度</span>
              <span className="header-cell">状态</span>
              <span className="header-cell">创建时间</span>
              <span className="header-cell">操作</span>
            </div>

            {/* 关系项 */}
            <div className="relations-list">
              {filteredRelations.map(relation => (
                <div
                  key={relation.id}
                  className={`relation-item ${relation.status} ${selectedIds.includes(relation.id) ? 'selected' : ''}`}
                >
                  {editingRelation?.id === relation.id ? (
                    // 编辑模式
                    <div className="edit-row">
                      <span className="entity-cell">{relation.sourceEntity}</span>
                      <select
                        value={editForm.relationType}
                        onChange={(e) => setEditForm({ ...editForm, relationType: e.target.value })}
                        className="edit-select"
                      >
                        {relationTypes.map(type => (
                          <option key={type.id} value={type.id}>{type.name}</option>
                        ))}
                      </select>
                      <span className="entity-cell">{relation.targetEntity}</span>
                      <span className="entity-cell">{(relation.confidence * 100).toFixed(0)}%</span>
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
                          checked={selectedIds.includes(relation.id)}
                          onChange={() => toggleSelection(relation.id)}
                        />
                      </label>
                      <span className="entity-cell source">
                        <span className="entity-name">{relation.sourceEntity}</span>
                        <span className="entity-type">{relation.sourceEntityType}</span>
                      </span>
                      <span className="entity-cell relation">
                        <span className="relation-name">{relation.relationType}</span>
                      </span>
                      <span className="entity-cell target">
                        <span className="entity-name">{relation.targetEntity}</span>
                        <span className="entity-type">{relation.targetEntityType}</span>
                      </span>
                      <span className="entity-cell confidence">
                        {(relation.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="entity-cell status">
                        <span
                          className={`status-badge ${relation.status}`}
                        >
                          {relation.status === 'active' ? '活跃' : '停用'}
                        </span>
                      </span>
                      <span className="entity-cell created">
                        {new Date(relation.createdAt).toLocaleString()}
                      </span>
                      <span className="entity-cell actions">
                        <button
                          className="action-btn edit"
                          onClick={() => handleEdit(relation)}
                          title="编辑"
                        >
                          ✏️
                        </button>
                        <button
                          className="action-btn toggle"
                          onClick={() => handleToggleStatus(relation)}
                          title={relation.status === 'active' ? '停用' : '激活'}
                        >
                          {relation.status === 'active' ? '⏸' : '✓'}
                        </button>
                        <button
                          className="action-btn delete"
                          onClick={() => handleDelete(relation)}
                          title="删除"
                        >
                          🗑️
                        </button>
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>

            {/* 分页 */}
            <div className="pagination">
              <span>共 {filteredRelations.length} 个关系</span>
              <div className="page-controls">
                <button className="page-btn" disabled>上一页</button>
                <span className="page-info">1 / 1</span>
                <button className="page-btn" disabled>下一页</button>
              </div>
            </div>
          </>
        ) : (
          <div className="empty-state">
            <span className="empty-icon">🔗</span>
            <h4>暂无关系数据</h4>
            <p>点击 "新建关系" 开始创建关系</p>
            <button className="btn-primary" onClick={handleOpenCreateDialog}>
              ➕ 新建关系
            </button>
          </div>
        )}
      </div>

      {/* 创建关系对话框 */}
      {showCreateDialog && (
        <div className="dialog-overlay">
          <div className="dialog-content">
            <div className="dialog-header">
              <h4>新建关系</h4>
              <button className="dialog-close" onClick={handleCloseCreateDialog}>✕</button>
            </div>
            <div className="dialog-body">
              <div className="form-group">
                <label>源实体：</label>
                <input
                  type="text"
                  value={createForm.sourceEntity}
                  onChange={(e) => setCreateForm({ ...createForm, sourceEntity: e.target.value })}
                  placeholder="输入源实体名称"
                />
              </div>
              <div className="form-group">
                <label>关系类型：</label>
                <select
                  value={createForm.relationType}
                  onChange={(e) => setCreateForm({ ...createForm, relationType: e.target.value })}
                >
                  <option value="">选择关系类型</option>
                  {relationTypes.map(type => (
                    <option key={type.id} value={type.id}>{type.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>目标实体：</label>
                <input
                  type="text"
                  value={createForm.targetEntity}
                  onChange={(e) => setCreateForm({ ...createForm, targetEntity: e.target.value })}
                  placeholder="输入目标实体名称"
                />
              </div>
              <div className="form-group">
                <label>属性：</label>
                <textarea
                  value={JSON.stringify(createForm.properties, null, 2)}
                  onChange={(e) => {
                    try {
                      setCreateForm({ ...createForm, properties: JSON.parse(e.target.value) });
                    } catch (e) {
                      // 忽略格式错误
                    }
                  }}
                  placeholder='{"key": "value"}'
                  rows={3}
                />
              </div>
            </div>
            <div className="dialog-footer">
              <button className="btn-secondary" onClick={handleCloseCreateDialog}>
                取消
              </button>
              <button className="btn-primary" onClick={handleSubmitCreate}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RelationManagement;
