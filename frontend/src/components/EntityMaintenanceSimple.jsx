import React, { useState, useEffect, useCallback } from 'react';
import {
  getKBEntities,
  getGlobalEntities,
  updateKBEntity,
  deleteDocumentEntity,
  batchDeleteEntities,
  submitEntityFeedback,
  getEntityStatistics,
  ENTITY_TYPES,
} from '../services/entityMaintenanceApi';
import './EntityMaintenanceSimple.css';

/**
 * 简化的实体维护组件
 * 使用与知识库页面一致的样式
 */
export default function EntityMaintenanceSimple({ knowledgeBaseId, embedded = false }) {
  const [activeTab, setActiveTab] = useState('kb'); // 'kb' 或 'global'
  const [entities, setEntities] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [entityType, setEntityType] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [message, setMessage] = useState({ text: '', type: '' });
  
  // 编辑对话框状态
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingEntity, setEditingEntity] = useState(null);
  const [editForm, setEditForm] = useState({ entity_text: '', entity_type: '', aliases: '' });

  const showMessage = (text, type = 'info') => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), 3000);
  };

  const loadEntities = useCallback(async () => {
    if (!knowledgeBaseId) return;
    
    setLoading(true);
    try {
      let response;
      const params = { page, pageSize, entityType };

      if (activeTab === 'kb') {
        response = await getKBEntities(knowledgeBaseId, params);
      } else {
        response = await getGlobalEntities(params);
      }

      setEntities(response.entities || []);
      setTotal(response.total || 0);
    } catch (error) {
      console.error('加载实体失败:', error);
      showMessage('加载实体失败', 'error');
    } finally {
      setLoading(false);
    }
  }, [activeTab, page, pageSize, entityType, knowledgeBaseId]);

  const loadStats = useCallback(async () => {
    if (!knowledgeBaseId) return;
    
    try {
      const response = await getEntityStatistics(knowledgeBaseId);
      setStats(response);
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  }, [knowledgeBaseId]);

  useEffect(() => {
    loadEntities();
  }, [loadEntities]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(entities.map(e => e.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(sid => sid !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleEdit = (entity) => {
    setEditingEntity(entity);
    setEditForm({
      entity_text: entity.canonical_name || entity.global_name || '',
      entity_type: entity.type || '',
      aliases: entity.aliases?.join(', ') || ''
    });
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    try {
      const data = {
        entity_text: editForm.entity_text,
        entity_type: editForm.entity_type,
      };
      if (activeTab === 'kb' && editForm.aliases) {
        data.aliases = editForm.aliases.split(',').map(a => a.trim()).filter(Boolean);
      }
      
      await updateKBEntity(editingEntity.id, data);
      showMessage('更新成功', 'success');
      setEditDialogOpen(false);
      loadEntities();
    } catch (error) {
      console.error('更新失败:', error);
      showMessage('更新失败', 'error');
    }
  };

  const handleDelete = async (entityId) => {
    if (!window.confirm('确定要删除这个实体吗？')) return;

    try {
      // 根据当前标签页选择删除方式
      if (activeTab === 'document') {
        // 文档级实体使用单个删除API
        await deleteDocumentEntity(entityId);
      } else {
        // 知识库级和全局级实体使用批量删除API
        await batchDeleteEntities([entityId], activeTab);
      }
      showMessage('删除成功', 'success');
      loadEntities();
    } catch (error) {
      console.error('删除失败:', error);
      showMessage('删除失败', 'error');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) {
      showMessage('请先选择要删除的实体', 'warning');
      return;
    }
    if (!window.confirm(`确定要删除选中的 ${selectedIds.length} 个实体吗？`)) return;

    try {
      await batchDeleteEntities(selectedIds, activeTab);
      showMessage('批量删除成功', 'success');
      setSelectedIds([]);
      loadEntities();
    } catch (error) {
      console.error('批量删除失败:', error);
      showMessage('批量删除失败', 'error');
    }
  };

  const getEntityDisplayName = (entity) => {
    return entity.canonical_name || entity.global_name || entity.text || '';
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="entity-maintenance-container">
      {/* 消息提示 */}
      {message.text && (
        <div className={`notification ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 工具栏 */}
      <div className="entity-toolbar">
        <div className="toolbar-left">
          <button 
            className="btn-secondary"
            onClick={loadEntities}
            disabled={loading}
          >
            {loading ? '刷新中...' : '刷新'}
          </button>
          
          {selectedIds.length > 0 && (
            <button 
              className="btn-danger"
              onClick={handleBatchDelete}
            >
              批量删除 ({selectedIds.length})
            </button>
          )}
        </div>
        
        <div className="toolbar-right">
          {/* 实体类型筛选 */}
          <select 
            className="form-select"
            value={entityType}
            onChange={(e) => {
              setEntityType(e.target.value);
              setPage(1);
            }}
          >
            {ENTITY_TYPES.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          
          <span className="total-info">共 {total} 个实体</span>
        </div>
      </div>

      {/* 统计信息 */}
      {stats && (
        <div className="stats-cards">
          <div className="stat-card">
            <div className="stat-label">文档级实体</div>
            <div className="stat-value">{stats.document_entities}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">知识库级实体</div>
            <div className="stat-value">{stats.kb_entities}</div>
          </div>
        </div>
      )}

      {/* 标签页 */}
      <div className="entity-tabs">
        <button 
          className={`tab-btn ${activeTab === 'kb' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('kb');
            setPage(1);
            setSelectedIds([]);
          }}
        >
          知识库级实体
        </button>
        <button 
          className={`tab-btn ${activeTab === 'global' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('global');
            setPage(1);
            setSelectedIds([]);
          }}
        >
          全局级实体
        </button>
      </div>

      {/* 实体列表 */}
      <div className="entity-table-container">
        <table className="entity-table">
          <thead>
            <tr>
              <th className="checkbox-col">
                <input 
                  type="checkbox" 
                  checked={entities.length > 0 && selectedIds.length === entities.length}
                  onChange={handleSelectAll}
                />
              </th>
              <th>ID</th>
              <th>实体名称</th>
              <th>类型</th>
              {activeTab === 'kb' && (
                <>
                  <th>别名</th>
                  <th>文档数</th>
                </>
              )}
              {activeTab === 'global' && (
                <>
                  <th>知识库数</th>
                  <th>文档数</th>
                </>
              )}
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {entities.map(entity => (
              <tr key={entity.id}>
                <td>
                  <input 
                    type="checkbox" 
                    checked={selectedIds.includes(entity.id)}
                    onChange={() => handleSelectOne(entity.id)}
                  />
                </td>
                <td>{entity.id}</td>
                <td>{getEntityDisplayName(entity)}</td>
                <td>
                  <span className={`entity-type-badge type-${entity.type?.toLowerCase()}`}>
                    {ENTITY_TYPES.find(t => t.value === entity.type)?.label || entity.type}
                  </span>
                </td>
                {activeTab === 'kb' && (
                  <>
                    <td>{entity.aliases?.join(', ') || '-'}</td>
                    <td>{entity.document_count}</td>
                  </>
                )}
                {activeTab === 'global' && (
                  <>
                    <td>{entity.kb_count}</td>
                    <td>{entity.document_count}</td>
                  </>
                )}
                <td>
                  <button 
                    className="btn-icon edit"
                    onClick={() => handleEdit(entity)}
                    title="编辑"
                  >
                    ✏️
                  </button>
                  <button 
                    className="btn-icon delete"
                    onClick={() => handleDelete(entity.id)}
                    title="删除"
                  >
                    🗑️
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {entities.length === 0 && !loading && (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p>暂无实体数据</p>
          </div>
        )}
      </div>

      {/* 分页 */}
      <div className="pagination">
        <div className="pagination-info">
          显示 {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} / {total}
        </div>
        <div className="pagination-controls">
          <button 
            className="pagination-btn"
            onClick={() => setPage(1)}
            disabled={page === 1}
          >
            首页
          </button>
          <button 
            className="pagination-btn"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            上一页
          </button>
          
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            const pageNum = i + 1;
            return (
              <button 
                key={pageNum}
                className={`pagination-btn ${page === pageNum ? 'active' : ''}`}
                onClick={() => setPage(pageNum)}
              >
                {pageNum}
              </button>
            );
          })}
          
          <button 
            className="pagination-btn"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            下一页
          </button>
          <button 
            className="pagination-btn"
            onClick={() => setPage(totalPages)}
            disabled={page === totalPages}
          >
            末页
          </button>
        </div>
        <div className="page-size-selector">
          <select 
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
          >
            <option value={10}>10条/页</option>
            <option value={25}>25条/页</option>
            <option value={50}>50条/页</option>
            <option value={100}>100条/页</option>
          </select>
        </div>
      </div>

      {/* 编辑对话框 */}
      {editDialogOpen && (
        <div className="modal-overlay" onClick={() => setEditDialogOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>编辑实体</h3>
              <button className="modal-close" onClick={() => setEditDialogOpen(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>实体名称</label>
                <input 
                  type="text"
                  className="form-input"
                  value={editForm.entity_text}
                  onChange={(e) => setEditForm({...editForm, entity_text: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>实体类型</label>
                <select 
                  className="form-select"
                  value={editForm.entity_type}
                  onChange={(e) => setEditForm({...editForm, entity_type: e.target.value})}
                >
                  {ENTITY_TYPES.filter(t => t.value).map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              {activeTab === 'kb' && (
                <div className="form-group">
                  <label>别名（用逗号分隔）</label>
                  <textarea 
                    className="form-textarea"
                    value={editForm.aliases}
                    onChange={(e) => setEditForm({...editForm, aliases: e.target.value})}
                    rows={3}
                  />
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setEditDialogOpen(false)}>
                取消
              </button>
              <button className="btn-primary" onClick={handleSaveEdit}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
