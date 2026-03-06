/**
 * 关系类型配置组件
 *
 * 用于管理系统中可用的关系类型，支持增删改查操作
 * 复用现有的 Modal 和 Button 组件
 */

import React, { useState, useEffect } from 'react';
import { getRelationTypes, addRelationType, updateRelationType, deleteRelationType } from '../../utils/api/knowledgeGraphApi';
import './RelationTypeConfig.css';

/**
 * 关系类型配置主组件
 *
 * @returns {JSX.Element} 关系类型配置界面
 */
const RelationTypeConfig = () => {
  // 关系类型列表
  const [relationTypes, setRelationTypes] = useState([]);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 错误信息
  const [error, setError] = useState(null);
  // 模态框显示状态
  const [showModal, setShowModal] = useState(false);
  // 当前编辑的关系类型
  const [currentType, setCurrentType] = useState(null);
  // 表单数据
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    directional: true,
    sourceEntityTypes: [],
    targetEntityTypes: [],
    properties: [],
    constraints: {
      unique: false,
      transitive: false,
      symmetric: false
    }
  });
  // 搜索关键词
  const [searchKeyword, setSearchKeyword] = useState('');

  // 可用的实体类型（从现有实体类型配置中获取）
  const availableEntityTypes = [
    { value: 'PERSON', label: '人物', color: '#4CAF50' },
    { value: 'ORG', label: '组织', color: '#2196F3' },
    { value: 'LOCATION', label: '地点', color: '#FF9800' },
    { value: 'PRODUCT', label: '产品', color: '#9C27B0' },
    { value: 'EVENT', label: '事件', color: '#F44336' },
    { value: 'TECHNOLOGY', label: '技术', color: '#00BCD4' },
    { value: 'CONCEPT', label: '概念', color: '#795548' }
  ];

  /**
   * 加载关系类型列表
   */
  const loadRelationTypes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getRelationTypes();
      if (response.success) {
        setRelationTypes(response.data);
      }
    } catch (err) {
      setError('加载关系类型失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadRelationTypes();
  }, []);

  /**
   * 打开添加模态框
   */
  const handleAdd = () => {
    setCurrentType(null);
    setFormData({
      name: '',
      description: '',
      directional: true,
      sourceEntityTypes: [],
      targetEntityTypes: [],
      properties: [],
      constraints: {
        unique: false,
        transitive: false,
        symmetric: false
      }
    });
    setShowModal(true);
  };

  /**
   * 打开编辑模态框
   * @param {Object} type 关系类型数据
   */
  const handleEdit = (type) => {
    setCurrentType(type);
    setFormData({
      name: type.name,
      description: type.description || '',
      directional: type.directional,
      sourceEntityTypes: type.sourceEntityTypes || [],
      targetEntityTypes: type.targetEntityTypes || [],
      properties: type.properties || [],
      constraints: type.constraints || { unique: false, transitive: false, symmetric: false }
    });
    setShowModal(true);
  };

  /**
   * 删除关系类型
   * @param {Object} type 关系类型数据
   */
  const handleDelete = async (type) => {
    if (!window.confirm(`确定要删除关系类型 "${type.name}" 吗？`)) {
      return;
    }

    try {
      await deleteRelationType(type.id);
      await loadRelationTypes();
    } catch (err) {
      setError('删除失败: ' + err.message);
    }
  };

  /**
   * 保存关系类型
   */
  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert('请输入关系类型名称');
      return;
    }

    try {
      if (currentType) {
        await updateRelationType(currentType.id, formData);
      } else {
        await addRelationType(formData);
      }
      setShowModal(false);
      await loadRelationTypes();
    } catch (err) {
      setError('保存失败: ' + err.message);
    }
  };

  /**
   * 处理表单字段变化
   * @param {string} field 字段名
   * @param {any} value 字段值
   */
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  /**
   * 处理约束条件变化
   * @param {string} constraint 约束名
   * @param {boolean} value 约束值
   */
  const handleConstraintChange = (constraint, value) => {
    setFormData(prev => ({
      ...prev,
      constraints: { ...prev.constraints, [constraint]: value }
    }));
  };

  /**
   * 处理实体类型选择
   * @param {string} field 字段名（sourceEntityTypes 或 targetEntityTypes）
   * @param {string} value 实体类型值
   * @param {boolean} checked 是否选中
   */
  const handleEntityTypeChange = (field, value, checked) => {
    setFormData(prev => ({
      ...prev,
      [field]: checked
        ? [...prev[field], value]
        : prev[field].filter(v => v !== value)
    }));
  };

  /**
   * 过滤后的关系类型列表
   */
  const filteredTypes = relationTypes.filter(type =>
    type.name.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    (type.description && type.description.toLowerCase().includes(searchKeyword.toLowerCase()))
  );

  return (
    <div className="relation-type-config">
      {/* 工具栏 */}
      <div className="config-toolbar">
        <div className="toolbar-left">
          <button className="btn btn-primary" onClick={handleAdd}>
            <span className="btn-icon">+</span>
            添加关系类型
          </button>
        </div>
        <div className="toolbar-right">
          <div className="search-box">
            <input
              type="text"
              placeholder="搜索关系类型..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
            <span className="search-icon">🔍</span>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
          <button className="close-btn" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* 关系类型列表 */}
      <div className="relation-type-list">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>加载中...</p>
          </div>
        ) : filteredTypes.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">🔗</span>
            <p>{searchKeyword ? '没有找到匹配的关系类型' : '暂无关系类型，请点击上方按钮添加'}</p>
          </div>
        ) : (
          <div className="type-grid">
            {filteredTypes.map(type => (
              <div key={type.id} className="type-card">
                <div className="type-header">
                  <h4 className="type-name">{type.name}</h4>
                  <div className="type-actions">
                    <button
                      className="action-btn edit"
                      onClick={() => handleEdit(type)}
                      title="编辑"
                    >
                      ✏️
                    </button>
                    <button
                      className="action-btn delete"
                      onClick={() => handleDelete(type)}
                      title="删除"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <p className="type-description">{type.description || '暂无描述'}</p>

                <div className="type-meta">
                  <span className={`direction-badge ${type.directional ? 'directional' : 'bidirectional'}`}>
                    {type.directional ? '→ 有向' : '↔ 无向'}
                  </span>
                </div>

                <div className="type-entities">
                  <div className="entity-section">
                    <span className="entity-label">源实体:</span>
                    <div className="entity-tags">
                      {type.sourceEntityTypes?.length > 0 ? (
                        type.sourceEntityTypes.map(et => {
                          const entityType = availableEntityTypes.find(t => t.value === et);
                          return (
                            <span
                              key={et}
                              className="entity-tag"
                              style={{ backgroundColor: entityType?.color + '20', color: entityType?.color }}
                            >
                              {entityType?.label || et}
                            </span>
                          );
                        })
                      ) : (
                        <span className="entity-tag empty">任意</span>
                      )}
                    </div>
                  </div>

                  <div className="entity-section">
                    <span className="entity-label">目标实体:</span>
                    <div className="entity-tags">
                      {type.targetEntityTypes?.length > 0 ? (
                        type.targetEntityTypes.map(et => {
                          const entityType = availableEntityTypes.find(t => t.value === et);
                          return (
                            <span
                              key={et}
                              className="entity-tag"
                              style={{ backgroundColor: entityType?.color + '20', color: entityType?.color }}
                            >
                              {entityType?.label || et}
                            </span>
                          );
                        })
                      ) : (
                        <span className="entity-tag empty">任意</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="type-constraints">
                  {type.constraints?.unique && (
                    <span className="constraint-tag" title="唯一关系">唯一</span>
                  )}
                  {type.constraints?.transitive && (
                    <span className="constraint-tag" title="传递关系">传递</span>
                  )}
                  {type.constraints?.symmetric && (
                    <span className="constraint-tag" title="对称关系">对称</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 添加/编辑模态框 */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{currentType ? '编辑关系类型' : '添加关系类型'}</h3>
              <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>关系名称 <span className="required">*</span></label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="例如：就职于、位于、合作"
                />
              </div>

              <div className="form-group">
                <label>描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="描述此关系的含义"
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.directional}
                    onChange={(e) => handleChange('directional', e.target.checked)}
                  />
                  <span>有向关系（A → B）</span>
                </label>
              </div>

              <div className="form-row">
                <div className="form-group half">
                  <label>源实体类型</label>
                  <div className="entity-type-selector">
                    {availableEntityTypes.map(type => (
                      <label key={type.value} className="checkbox-label small">
                        <input
                          type="checkbox"
                          checked={formData.sourceEntityTypes.includes(type.value)}
                          onChange={(e) => handleEntityTypeChange('sourceEntityTypes', type.value, e.target.checked)}
                        />
                        <span style={{ color: type.color }}>{type.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="form-group half">
                  <label>目标实体类型</label>
                  <div className="entity-type-selector">
                    {availableEntityTypes.map(type => (
                      <label key={type.value} className="checkbox-label small">
                        <input
                          type="checkbox"
                          checked={formData.targetEntityTypes.includes(type.value)}
                          onChange={(e) => handleEntityTypeChange('targetEntityTypes', type.value, e.target.checked)}
                        />
                        <span style={{ color: type.color }}>{type.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label>约束条件</label>
                <div className="constraints-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.constraints.unique}
                      onChange={(e) => handleConstraintChange('unique', e.target.checked)}
                    />
                    <span>唯一关系（两个实体间只能有一个此类型的关系）</span>
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.constraints.transitive}
                      onChange={(e) => handleConstraintChange('transitive', e.target.checked)}
                    />
                    <span>传递关系（如果 A→B 且 B→C，则 A→C）</span>
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.constraints.symmetric}
                      onChange={(e) => handleConstraintChange('symmetric', e.target.checked)}
                    />
                    <span>对称关系（如果 A→B，则 B→A）</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleSave}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RelationTypeConfig;
