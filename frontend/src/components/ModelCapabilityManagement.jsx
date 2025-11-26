import React, { useState, useEffect } from 'react';
import { capabilityApi } from '../utils/api';
import '../styles/ModelCapabilityManagement.css';

const ModelCapabilityManagement = () => {
  const [capabilities, setCapabilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentCapability, setCurrentCapability] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    capability_type: '',
    is_active: true
  });
  
  // 获取所有能力
  const loadCapabilities = async () => {
    try {
      console.log('🔄 开始加载能力数据...');
      setLoading(true);
      const response = await capabilityApi.getAll();
      
      // 统一响应格式处理
      let capabilitiesData = [];
      if (Array.isArray(response)) {
        capabilitiesData = response;
      } else if (response?.capabilities) {
        capabilitiesData = response.capabilities;
      } else if (response?.data) {
        capabilitiesData = response.data;
      }
      
      // 标准化能力数据，确保每个能力都有必要的属性
      const normalizedCapabilities = capabilitiesData.map(capability => ({
        id: capability.id ?? `capability_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: capability.name ?? `未命名能力_${capability.id || 'unknown'}`,
        display_name: capability.display_name ?? capability.name ?? '未命名能力',
        description: capability.description || '',
        capability_type: capability.capability_type || 'general',
        is_active: capability.is_active ?? true,
        ...capability
      }));
      
      console.log('✅ 能力数据加载成功，共加载', normalizedCapabilities.length, '个能力');
      setCapabilities(normalizedCapabilities);
      setError(null);
    } catch (err) {
      console.error('❌ 获取能力失败:', err);
      setError('获取能力列表失败，请稍后重试');
      
      // 错误降级处理：使用本地模拟数据
      const mockCapabilities = [
        { id: 1, name: 'text_generation', display_name: '文本生成', capability_type: 'text', is_active: true },
        { id: 2, name: 'code_generation', display_name: '代码生成', capability_type: 'code', is_active: true },
        { id: 3, name: 'image_generation', display_name: '图像生成', capability_type: 'vision', is_active: true },
        { id: 4, name: 'multi_modal', display_name: '多模态', capability_type: 'general', is_active: true },
        { id: 5, name: 'embedding', display_name: '向量嵌入', capability_type: 'text', is_active: true }
      ];
      console.log('⚠️ 使用模拟能力数据作为降级方案');
      setCapabilities(mockCapabilities);
    } finally {
      setLoading(false);
    }
  };
  
  // 初始化加载
  useEffect(() => {
    loadCapabilities();
  }, []);
  
  // 处理输入变化
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      description: '',
      capability_type: '',
      is_active: true
    });
    setCurrentCapability(null);
  };
  
  // 打开创建模态框
  const handleCreateModalOpen = () => {
    resetForm();
    setShowCreateModal(true);
  };
  
  // 打开编辑模态框
  const handleEditModalOpen = (capability) => {
    setCurrentCapability(capability);
    setFormData({
      name: capability.name,
      display_name: capability.display_name,
      description: capability.description || '',
      capability_type: capability.capability_type || '',
      is_active: capability.is_active
    });
    setShowEditModal(true);
  };
  
  // 关闭模态框
  const handleModalClose = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    resetForm();
  };
  
  // 提交创建表单
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      await capabilityApi.create(formData);
      setShowCreateModal(false);
      loadCapabilities(); // 重新加载列表
    } catch (err) {
      console.error('创建能力失败:', err);
      setError('创建能力失败，请检查输入并重试');
    }
  };
  
  // 提交编辑表单
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!currentCapability) return;
    
    try {
      await capabilityApi.update(currentCapability.id, formData);
      setShowEditModal(false);
      loadCapabilities(); // 重新加载列表
    } catch (err) {
      console.error('更新能力失败:', err);
      setError('更新能力失败，请检查输入并重试');
    }
  };
  
  // 处理删除
  const handleDelete = async (capabilityId) => {
    if (window.confirm('确定要删除这个能力吗？删除前请确保该能力没有关联的模型。')) {
      try {
        await capabilityApi.delete(capabilityId);
        loadCapabilities(); // 重新加载列表
      } catch (err) {
        console.error('删除能力失败:', err);
        setError('删除能力失败，可能是因为该能力与模型存在关联');
      }
    }
  };
  
  // 获取不同类型的能力列表（用于筛选）
  const getCapabilityTypes = () => {
    const types = new Set(capabilities.map(cap => cap.capability_type).filter(Boolean));
    return Array.from(types);
  };
  
  const capabilityTypes = getCapabilityTypes();
  
  if (loading) {
    return <div className="capability-management-loading">加载中...</div>;
  }
  
  return (
    <div className="model-capability-management">
      <div className="capability-header">
        <button 
          className="btn btn-primary" 
          onClick={handleCreateModalOpen}
        >
          创建能力
        </button>
      </div>
      
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      <div className="capability-content">
        {capabilities.length === 0 ? (
          <div className="empty-state">暂无能力数据</div>
        ) : (
          <div className="capability-tabs">
            <div className="tab active" data-type="all">所有能力</div>
            {capabilityTypes.map(type => (
              <div key={type} className="tab" data-type={type}>
                {type}
              </div>
            ))}
            <div className="tab" data-type="active">启用</div>
            <div className="tab" data-type="inactive">禁用</div>
          </div>
        )}
        
        <div className="capability-table-container">
          <table className="capability-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>名称</th>
                <th>显示名称</th>
                <th>类型</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {capabilities.map(capability => (
                <tr key={capability.id}>
                  <td>{capability.id}</td>
                  <td>{capability.name}</td>
                  <td>{capability.display_name}</td>
                  <td>
                    <span className={`capability-type-badge ${capability.capability_type}`}>
                      {capability.capability_type || '-'}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${capability.is_active ? 'active' : 'inactive'}`}>
                      {capability.is_active ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="action-buttons">
                    <button 
                      className="btn btn-small btn-info" 
                      onClick={() => handleEditModalOpen(capability)}
                      title="编辑"
                    >
                      编辑
                    </button>
                    <button 
                      className="btn btn-small btn-danger" 
                      onClick={() => handleDelete(capability.id)}
                      title="删除"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* 创建能力模态框 */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>创建新能力</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleCreateSubmit} className="modal-form">
              <div className="form-group">
                <label>名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入能力名称（英文，如：text_generation）"
                />
              </div>
              <div className="form-group">
                <label>显示名称 *</label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入能力显示名称（中文，如：文本生成）"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入能力描述"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>类型</label>
                <input
                  type="text"
                  name="capability_type"
                  value={formData.capability_type}
                  onChange={handleInputChange}
                  placeholder="输入能力类型（如：text, vision, code）"
                />
              </div>
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
                <button type="button" className="btn btn-secondary" onClick={handleModalClose}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  创建
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* 编辑能力模态框 */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>编辑能力</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleEditSubmit} className="modal-form">
              <div className="form-group">
                <label>名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入能力名称（英文）"
                />
              </div>
              <div className="form-group">
                <label>显示名称 *</label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入能力显示名称（中文）"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入能力描述"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>类型</label>
                <input
                  type="text"
                  name="capability_type"
                  value={formData.capability_type}
                  onChange={handleInputChange}
                  placeholder="输入能力类型"
                />
              </div>
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  id="is_active_edit"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                />
                <label htmlFor="is_active_edit">启用</label>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={handleModalClose}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  更新
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelCapabilityManagement;