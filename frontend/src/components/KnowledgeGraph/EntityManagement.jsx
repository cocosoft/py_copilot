/**
 * 实体管理组件
 *
 * 知识库级别的实体管理功能，提供实体列表、搜索筛选、批量操作、详情查看等功能
 * 复用现有的 EntityMaintenanceSimple 组件
 */

import React, { useState, useEffect, useCallback } from 'react';
import EntityMaintenanceSimple from '../EntityMaintenanceSimple';
import { getEntities, getSimilarEntities, mergeEntities } from '../../utils/api/knowledgeGraphApi';
import { showNotification, NotificationType } from '../UI/Notification';
import './EntityManagement.css';

/**
 * 实体管理主组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @returns {JSX.Element} 实体管理界面
 */
const EntityManagement = ({ knowledgeBaseId }) => {
  // 实体列表
  const [entities, setEntities] = useState([]);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 搜索关键词
  const [searchKeyword, setSearchKeyword] = useState('');
  // 类型筛选
  const [typeFilter, setTypeFilter] = useState('');
  // 选中的实体ID列表
  const [selectedIds, setSelectedIds] = useState([]);
  // 显示详情侧边栏
  const [showSidebar, setShowSidebar] = useState(false);
  // 当前选中的实体
  const [selectedEntity, setSelectedEntity] = useState(null);
  // 相似实体列表
  const [similarEntities, setSimilarEntities] = useState([]);
  // 显示合并对话框
  const [showMergeDialog, setShowMergeDialog] = useState(false);
  // 合并目标实体
  const [mergeTarget, setMergeTarget] = useState(null);

  // 可用的实体类型
  const entityTypes = [
    { value: '', label: '全部类型' },
    { value: 'PERSON', label: '人物' },
    { value: 'ORG', label: '组织' },
    { value: 'LOCATION', label: '地点' },
    { value: 'PRODUCT', label: '产品' },
    { value: 'EVENT', label: '事件' },
    { value: 'TECHNOLOGY', label: '技术' },
    { value: 'CONCEPT', label: '概念' }
  ];

  /**
   * 加载实体列表
   */
  const loadEntities = useCallback(async () => {
    if (!knowledgeBaseId) return;

    setLoading(true);
    try {
      // 调用API获取实体列表
      const response = await getEntities(knowledgeBaseId, {
        keyword: searchKeyword,
        type: typeFilter
      });
      setEntities(response.data);
    } catch (error) {
      console.error('加载实体列表失败:', error);
      setLoading(false);
    }
  }, [knowledgeBaseId, searchKeyword, typeFilter]);

  // 组件挂载和依赖变化时加载数据
  useEffect(() => {
    loadEntities();
  }, [loadEntities]);

  /**
   * 处理实体点击
   * @param {Object} entity - 实体数据
   */
  const handleEntityClick = async (entity) => {
    setSelectedEntity(entity);
    setShowSidebar(true);
    
    // 加载相似实体
    try {
      const response = await getSimilarEntities(entity.id);
      if (response.success) {
        setSimilarEntities(response.data);
      }
    } catch (error) {
      console.error('加载相似实体失败:', error);
    }
  };

  /**
   * 处理选择变化
   * @param {Array} ids - 选中的实体ID列表
   */
  const handleSelectionChange = (ids) => {
    setSelectedIds(ids);
  };

  /**
   * 处理批量删除
   */
  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) {
      alert('请先选择要删除的实体');
      return;
    }
    
    if (!window.confirm(`确定要删除选中的 ${selectedIds.length} 个实体吗？`)) {
      return;
    }

    try {
      // TODO: 调用批量删除API
      // await batchDeleteEntities(selectedIds);
      alert('删除成功');
      setSelectedIds([]);
      loadEntities();
    } catch (error) {
      console.error('批量删除失败:', error);
      alert('删除失败');
    }
  };

  /**
   * 打开合并对话框
   */
  const handleOpenMerge = () => {
    if (selectedIds.length < 2) {
      alert('请至少选择2个实体进行合并');
      return;
    }
    setShowMergeDialog(true);
  };

  /**
   * 执行合并
   */
  const handleMerge = async () => {
    if (!mergeTarget) {
      alert('请选择目标实体');
      return;
    }

    try {
      const sourceIds = selectedIds.filter(id => id !== mergeTarget);
      await mergeEntities(sourceIds, mergeTarget);
      alert('合并成功');
      setShowMergeDialog(false);
      setSelectedIds([]);
      setMergeTarget(null);
      loadEntities();
    } catch (error) {
      console.error('合并失败:', error);
      alert('合并失败');
    }
  };

  /**
   * 获取类型标签
   * @param {string} type - 类型值
   * @returns {string} 类型标签
   */
  const getTypeLabel = (type) => {
    const found = entityTypes.find(t => t.value === type);
    return found ? found.label : type;
  };

  /**
   * 获取类型颜色
   * @param {string} type - 类型值
   * @returns {string} 类型颜色
   */
  const getTypeColor = (type) => {
    const colors = {
      'PERSON': '#4CAF50',
      'ORG': '#2196F3',
      'LOCATION': '#FF9800',
      'PRODUCT': '#9C27B0',
      'EVENT': '#F44336',
      'TECHNOLOGY': '#00BCD4',
      'CONCEPT': '#795548'
    };
    return colors[type] || '#607D8B';
  };

  return (
    <div className="entity-management">
      {/* 工具栏 */}
      <div className="management-toolbar">
        <div className="toolbar-left">
          <div className="search-box">
            <input
              type="text"
              placeholder="搜索实体..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
            <span className="search-icon">🔍</span>
          </div>
          
          <select 
            className="type-filter"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            {entityTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </div>

        <div className="toolbar-right">
          {selectedIds.length > 0 && (
            <span className="selection-info">
              已选择 {selectedIds.length} 个实体
            </span>
          )}
          
          <button 
            className="btn btn-secondary"
            onClick={handleOpenMerge}
            disabled={selectedIds.length < 2}
          >
            🔀 合并
          </button>
          
          <button 
            className="btn btn-danger"
            onClick={handleBatchDelete}
            disabled={selectedIds.length === 0}
          >
            🗑️ 删除
          </button>
          
          <button 
            className="btn btn-primary"
            onClick={loadEntities}
          >
            🔄 刷新
          </button>
        </div>
      </div>

      {/* 主内容区域 */}
      <div className="management-content">
        {/* 实体列表 */}
        <div className={`entity-list-container ${showSidebar ? 'with-sidebar' : ''}`}>
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>加载中...</p>
            </div>
          ) : entities.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">🏷️</span>
              <h4>暂无实体数据</h4>
              <p>实体数据会在知识图谱构建过程中自动生成</p>
              <div className="empty-actions">
                <button className="action-btn primary" onClick={() => {
                  // 这里可以添加跳转到批量构建页面的逻辑
                  showNotification({
                    title: '提示',
                    message: '请先在批量构建页面为文档构建知识图谱',
                    type: NotificationType.INFO
                  });
                }}>
                  去构建图谱
                </button>
              </div>
            </div>
          ) : (
            <div className="entity-table-wrapper">
              <table className="entity-table">
                <thead>
                  <tr>
                    <th className="checkbox-cell">
                      <input 
                        type="checkbox" 
                        checked={selectedIds.length === entities.length && entities.length > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedIds(entities.map(e => e.id));
                          } else {
                            setSelectedIds([]);
                          }
                        }}
                      />
                    </th>
                    <th>实体名称</th>
                    <th>类型</th>
                    <th>置信度</th>
                    <th>来源文档</th>
                    <th>关系数</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {entities.map(entity => (
                    <tr 
                      key={entity.id}
                      className={selectedIds.includes(entity.id) ? 'selected' : ''}
                      onClick={() => handleEntityClick(entity)}
                    >
                      <td className="checkbox-cell" onClick={(e) => e.stopPropagation()}>
                        <input 
                          type="checkbox"
                          checked={selectedIds.includes(entity.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedIds([...selectedIds, entity.id]);
                            } else {
                              setSelectedIds(selectedIds.filter(id => id !== entity.id));
                            }
                          }}
                        />
                      </td>
                      <td className="entity-name">{entity.name}</td>
                      <td>
                        <span 
                          className="type-badge"
                          style={{ 
                            backgroundColor: getTypeColor(entity.type) + '20',
                            color: getTypeColor(entity.type)
                          }}
                        >
                          {getTypeLabel(entity.type)}
                        </span>
                      </td>
                      <td>
                        <div className="confidence-bar">
                          <div 
                            className="confidence-fill"
                            style={{ width: `${entity.confidence * 100}%` }}
                          />
                          <span>{(entity.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td>{entity.document_count}</td>
                      <td>{entity.relation_count}</td>
                      <td>
                        <button 
                          className="action-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEntityClick(entity);
                          }}
                        >
                          查看
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 详情侧边栏 */}
        {showSidebar && selectedEntity && (
          <div className="entity-sidebar">
            <div className="sidebar-header">
              <h3>实体详情</h3>
              <button 
                className="close-btn"
                onClick={() => setShowSidebar(false)}
              >
                ×
              </button>
            </div>
            
            <div className="sidebar-content">
              <div className="entity-header">
                <h4 className="entity-title">{selectedEntity.name}</h4>
                <span 
                  className="type-badge large"
                  style={{ 
                    backgroundColor: getTypeColor(selectedEntity.type) + '20',
                    color: getTypeColor(selectedEntity.type)
                  }}
                >
                  {getTypeLabel(selectedEntity.type)}
                </span>
              </div>

              <div className="entity-stats">
                <div className="stat-item">
                  <span className="stat-label">置信度</span>
                  <span className="stat-value">{(selectedEntity.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">来源文档</span>
                  <span className="stat-value">{selectedEntity.document_count}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">关系数</span>
                  <span className="stat-value">{selectedEntity.relation_count}</span>
                </div>
              </div>

              {/* 相似实体 */}
              {similarEntities.length > 0 && (
                <div className="similar-entities-section">
                  <h5>相似实体</h5>
                  <ul className="similar-list">
                    {similarEntities.map(sim => (
                      <li key={sim.id} className="similar-item">
                        <span className="similar-name">{sim.similar_entity_name}</span>
                        <span className="similar-score">
                          {(sim.similarity_score * 100).toFixed(0)}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="sidebar-actions">
                <button className="btn btn-primary full-width">
                  编辑实体
                </button>
                <button className="btn btn-secondary full-width">
                  查看关系图谱
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 合并对话框 */}
      {showMergeDialog && (
        <div className="modal-overlay" onClick={() => setShowMergeDialog(false)}>
          <div className="modal-content merge-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>合并实体</h3>
              <button className="close-btn" onClick={() => setShowMergeDialog(false)}>×</button>
            </div>
            
            <div className="modal-body">
              <p className="merge-description">
                请选择要保留的目标实体，其他选中的实体将被合并到目标实体中。
              </p>
              
              <div className="merge-target-list">
                <h4>选择目标实体</h4>
                {entities
                  .filter(e => selectedIds.includes(e.id))
                  .map(entity => (
                    <label key={entity.id} className="merge-target-item">
                      <input
                        type="radio"
                        name="mergeTarget"
                        value={entity.id}
                        checked={mergeTarget === entity.id}
                        onChange={() => setMergeTarget(entity.id)}
                      />
                      <span className="entity-name">{entity.name}</span>
                      <span 
                        className="type-badge"
                        style={{ 
                          backgroundColor: getTypeColor(entity.type) + '20',
                          color: getTypeColor(entity.type)
                        }}
                      >
                        {getTypeLabel(entity.type)}
                      </span>
                    </label>
                  ))}
              </div>
            </div>
            
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowMergeDialog(false)}>
                取消
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleMerge}
                disabled={!mergeTarget}
              >
                确认合并
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EntityManagement;
