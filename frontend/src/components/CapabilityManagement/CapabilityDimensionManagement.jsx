import React, { useState, useEffect } from 'react';
import { capabilityApi } from '../../utils/api/capabilityApi';

const CapabilityDimensionManagement = () => {
  const [dimensions, setDimensions] = useState([]);
  const [subdimensions, setSubdimensions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [isSubdimension, setIsSubdimension] = useState(false);
  const [currentItem, setCurrentItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    is_active: true,
    dimension_id: null
  });

  // 加载维度和子维度数据
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [dimensionsData, subdimensionsData] = await Promise.all([
        capabilityApi.getDimensions(),
        capabilityApi.getSubdimensions()
      ]);

      // 标准化数据格式
      const processedDimensions = Array.isArray(dimensionsData.data) 
        ? dimensionsData.data 
        : dimensionsData.dimensions || [];

      const processedSubdimensions = Array.isArray(subdimensionsData.data) 
        ? subdimensionsData.data 
        : subdimensionsData.subdimensions || [];

      setDimensions(processedDimensions);
      setSubdimensions(processedSubdimensions);
    } catch (err) {
      console.error('加载能力维度数据失败:', err);
      setError('加载数据失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 打开模态框
  const openModal = (mode, isSubdim = false, item = null) => {
    setModalMode(mode);
    setIsSubdimension(isSubdim);
    setCurrentItem(item);
    
    if (mode === 'edit' && item) {
      setFormData({
        name: item.name || '',
        display_name: item.display_name || '',
        description: item.description || '',
        is_active: item.is_active ?? true,
        dimension_id: item.dimension_id || null
      });
    } else {
      setFormData({
        name: '',
        display_name: '',
        description: '',
        is_active: true,
        dimension_id: null
      });
    }
    
    setShowModal(true);
  };

  // 关闭模态框
  const closeModal = () => {
    setShowModal(false);
    setCurrentItem(null);
    setFormData({
      name: '',
      display_name: '',
      description: '',
      is_active: true,
      dimension_id: null
    });
  };

  // 处理表单输入变化
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      
      if (isSubdimension) {
        if (modalMode === 'add') {
          await capabilityApi.createSubdimension(formData);
        } else if (modalMode === 'edit' && currentItem) {
          await capabilityApi.updateSubdimension(currentItem.id, formData);
        }
      } else {
        if (modalMode === 'add') {
          await capabilityApi.createDimension(formData);
        } else if (modalMode === 'edit' && currentItem) {
          await capabilityApi.updateDimension(currentItem.id, formData);
        }
      }
      
      setSuccess(`${modalMode === 'add' ? '创建' : '更新'}${isSubdimension ? '子维度' : '维度'}成功`);
      closeModal();
      loadAllData(); // 重新加载数据
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error(`${modalMode === 'add' ? '创建' : '更新'}${isSubdimension ? '子维度' : '维度'}失败:`, err);
      setError(`${modalMode === 'add' ? '创建' : '更新'}${isSubdimension ? '子维度' : '维度'}失败，请重试`);
    } finally {
      setLoading(false);
    }
  };

  // 处理删除操作
  const handleDelete = async (id, isSubdim = false) => {
    if (window.confirm(`确定要删除这个${isSubdim ? '子维度' : '维度'}吗？`)) {
      try {
        setLoading(true);
        setError(null);
        
        if (isSubdim) {
          await capabilityApi.deleteSubdimension(id);
        } else {
          await capabilityApi.deleteDimension(id);
        }
        
        setSuccess(`删除${isSubdim ? '子维度' : '维度'}成功`);
        loadAllData(); // 重新加载数据
        
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        console.error(`删除${isSubdim ? '子维度' : '维度'}失败:`, err);
        setError(`删除${isSubdim ? '子维度' : '维度'}失败，请重试`);
      } finally {
        setLoading(false);
      }
    }
  };

  // 根据维度ID获取子维度
  const getSubdimensionsByDimension = (dimensionId) => {
    return subdimensions.filter(subdim => subdim.dimension_id === dimensionId);
  };

  if (loading) {
    return <div className="loading-state">加载中...</div>;
  }

  return (
    <div className="capability-dimension-management">
      <div className="section-header">
        <h3>能力维度管理</h3>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => openModal('add', false)}
          >
            添加维度
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="btn btn-small">×</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => setSuccess(null)} className="btn btn-small">×</button>
        </div>
      )}

      <div className="dimensions-container">
        {dimensions.length === 0 ? (
          <div className="empty-state">暂无能力维度数据</div>
        ) : (
          dimensions.map(dimension => {
            const dimSubdimensions = getSubdimensionsByDimension(dimension.id);
            return (
              <div key={dimension.id} className="dimension-card">
                <div className="dimension-header">
                  <div>
                    <h4>{dimension.display_name || dimension.name}</h4>
                    <p className="dimension-description">{dimension.description}</p>
                  </div>
                  <div className="dimension-actions">
                    <span className={`status-badge ${dimension.is_active ? 'active' : 'inactive'}`}>
                      {dimension.is_active ? '启用' : '禁用'}
                    </span>
                    <button 
                      className="btn btn-small btn-info"
                      onClick={() => openModal('edit', false, dimension)}
                    >
                      编辑
                    </button>
                    <button 
                      className="btn btn-small btn-danger"
                      onClick={() => handleDelete(dimension.id, false)}
                    >
                      删除
                    </button>
                  </div>
                </div>
                
                <div className="subdimensions-section">
                  <div className="subdimension-header">
                    <h5>子维度</h5>
                    <button 
                      className="btn btn-small btn-primary"
                      onClick={() => openModal('add', true, { dimension_id: dimension.id })}
                    >
                      添加子维度
                    </button>
                  </div>
                  
                  {dimSubdimensions.length === 0 ? (
                    <div className="empty-subdimensions">暂无子维度数据</div>
                  ) : (
                    <div className="subdimensions-list">
                      {dimSubdimensions.map(subdim => (
                        <div key={subdim.id} className="subdimension-item">
                          <div>
                            <span className="subdimension-name">{subdim.display_name || subdim.name}</span>
                            <span className="subdimension-description">{subdim.description}</span>
                          </div>
                          <div className="subdimension-actions">
                            <span className={`status-badge ${subdim.is_active ? 'active' : 'inactive'}`}>
                              {subdim.is_active ? '启用' : '禁用'}
                            </span>
                            <button 
                              className="btn btn-small btn-info"
                              onClick={() => openModal('edit', true, subdim)}
                            >
                              编辑
                            </button>
                            <button 
                              className="btn btn-small btn-danger"
                              onClick={() => handleDelete(subdim.id, true)}
                            >
                              删除
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 模态框 */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>
                {modalMode === 'add' ? '添加' : '编辑'} 
                {isSubdimension ? '子维度' : '维度'}
              </h3>
              <button className="btn-close" onClick={closeModal}>×</button>
            </div>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="输入维度名称（英文，如：performance）"
                  required
                />
              </div>
              <div className="form-group">
                <label>显示名称 *</label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  placeholder="输入维度显示名称（中文，如：性能）"
                  required
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入维度描述"
                  rows="3"
                />
              </div>
              {isSubdimension && (
                <div className="form-group">
                  <label>父维度 *</label>
                  <select
                    name="dimension_id"
                    value={formData.dimension_id || ''}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="">请选择父维度</option>
                    {dimensions.map(dim => (
                      <option key={dim.id} value={dim.id}>
                        {dim.display_name || dim.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  id="is_active"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                />
                <label htmlFor="is_active">启用</label>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  {modalMode === 'add' ? '创建' : '更新'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CapabilityDimensionManagement;
