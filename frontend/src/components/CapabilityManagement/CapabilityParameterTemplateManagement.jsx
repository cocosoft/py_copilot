import React, { useState, useEffect } from 'react';
import { capabilityApi } from '../../utils/api/capabilityApi';
import '../../styles/CapabilityManagement.css';

const CapabilityParameterTemplateManagement = () => {
  const [templates, setTemplates] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    parameters: {},
    level: 'standard',
    version: '1.0.0',
    capability_id: '',
    is_active: true
  });

  // 加载能力列表和参数模板数据
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 加载所有能力
      const capabilitiesResponse = await capabilityApi.getAll();
      const processedCapabilities = Array.isArray(capabilitiesResponse?.capabilities)
        ? capabilitiesResponse.capabilities
        : capabilitiesResponse;
      setCapabilities(processedCapabilities);
      
      // 加载所有参数模板（这里需要根据后端API调整）
      // 暂时为空，因为后端可能还没有提供获取所有模板的API
      setTemplates([]);
    } catch (err) {
      console.error('加载数据失败:', err);
      setError('加载数据失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 加载特定能力的参数模板
  const loadTemplatesByCapability = async (capabilityId) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await capabilityApi.getParameterTemplatesByCapability(capabilityId);
      const processedTemplates = Array.isArray(response?.data)
        ? response.data
        : response;
      
      setTemplates(processedTemplates);
    } catch (err) {
      console.error('加载参数模板失败:', err);
      setError('加载参数模板失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 打开模态框
  const openModal = (mode, template = null) => {
    setModalMode(mode);
    setCurrentTemplate(template);
    
    if (mode === 'edit' && template) {
      setFormData({
        name: template.name || '',
        display_name: template.display_name || '',
        description: template.description || '',
        parameters: template.parameters || {},
        level: template.level || 'standard',
        version: template.version || '1.0.0',
        capability_id: template.capability_id || '',
        is_active: template.is_active ?? true
      });
    } else {
      setFormData({
        name: '',
        display_name: '',
        description: '',
        parameters: {},
        level: 'standard',
        version: '1.0.0',
        capability_id: '',
        is_active: true
      });
    }
    
    setShowModal(true);
  };

  // 关闭模态框
  const closeModal = () => {
    setShowModal(false);
    setCurrentTemplate(null);
    setFormData({
      name: '',
      display_name: '',
      description: '',
      parameters: {},
      level: 'standard',
      version: '1.0.0',
      capability_id: '',
      is_active: true
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

  // 处理参数JSON输入变化
  const handleParametersChange = (e) => {
    const { value } = e.target;
    try {
      setFormData(prev => ({
        ...prev,
        parameters: value ? JSON.parse(value) : {}
      }));
    } catch (err) {
      // 不更新，保持之前的参数值
    }
  };

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      
      if (modalMode === 'add') {
        // 创建新模板
        await capabilityApi.createParameterTemplate(formData);
      } else if (modalMode === 'edit' && currentTemplate) {
        // 更新现有模板
        await capabilityApi.updateParameterTemplate(currentTemplate.id, formData);
      }
      
      setSuccess(`${modalMode === 'add' ? '创建' : '更新'}参数模板成功`);
      closeModal();
      
      // 如果选择了能力，重新加载该能力的模板
      if (formData.capability_id) {
        loadTemplatesByCapability(formData.capability_id);
      } else {
        loadAllData();
      }
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error(`${modalMode === 'add' ? '创建' : '更新'}参数模板失败:`, err);
      setError(`${modalMode === 'add' ? '创建' : '更新'}参数模板失败，请重试`);
    } finally {
      setLoading(false);
    }
  };

  // 处理删除操作
  const handleDelete = async (templateId) => {
    if (window.confirm('确定要删除这个参数模板吗？')) {
      try {
        setLoading(true);
        setError(null);
        
        // 调用API删除模板
        await capabilityApi.deleteParameterTemplate(templateId);
        
        setSuccess('删除参数模板成功');
        
        // 重新加载数据
        const selectedCapabilityId = formData.capability_id;
        if (selectedCapabilityId) {
          loadTemplatesByCapability(selectedCapabilityId);
        } else {
          loadAllData();
        }
        
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        console.error('删除参数模板失败:', err);
        setError('删除参数模板失败，请重试');
      } finally {
        setLoading(false);
      }
    }
  };

  if (loading) {
    return <div className="loading-state">加载中...</div>;
  }

  return (
    <div className="capability-parameter-template-management">
      <div className="section-header">
        <h3>能力参数模板管理</h3>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => openModal('add')}
          >
            添加参数模板
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

      {/* 能力选择器 */}
      <div className="capability-selector">
        <label htmlFor="capability-select">选择能力:</label>
        <select
          id="capability-select"
          value={formData.capability_id}
          onChange={(e) => {
            setFormData(prev => ({ ...prev, capability_id: e.target.value }));
            if (e.target.value) {
              loadTemplatesByCapability(e.target.value);
            }
          }}
        >
          <option value="">所有能力</option>
          {capabilities.map(capability => (
            <option key={capability.id} value={capability.id}>
              {capability.display_name || capability.name}
            </option>
          ))}
        </select>
      </div>

      <div className="templates-container">
        {templates.length === 0 ? (
          <div className="empty-state">暂无参数模板数据</div>
        ) : (
          <div className="templates-grid">
            {templates.map(template => (
              <div key={template.id} className="template-card">
                <div className="template-header">
                  <div>
                    <h4>{template.display_name || template.name}</h4>
                    <p className="template-description">{template.description}</p>
                  </div>
                  <div className="template-actions">
                    <span className={`status-badge ${template.is_active ? 'active' : 'inactive'}`}>
                      {template.is_active ? '启用' : '禁用'}
                    </span>
                    <button 
                      className="btn btn-small btn-info"
                      onClick={() => openModal('edit', template)}
                    >
                      编辑
                    </button>
                    <button 
                      className="btn btn-small btn-danger"
                      onClick={() => handleDelete(template.id)}
                    >
                      删除
                    </button>
                  </div>
                </div>
                <div className="template-details">
                  <div className="detail-item">
                    <span className="detail-label">版本:</span>
                    <span className="detail-value">{template.version || '1.0.0'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">级别:</span>
                    <span className="detail-value">{template.level || 'standard'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">能力:</span>
                    <span className="detail-value">
                      {capabilities.find(c => c.id === template.capability_id)?.display_name || '未知能力'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 模态框 */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>
                {modalMode === 'add' ? '添加' : '编辑'} 参数模板
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
                  placeholder="输入模板名称（英文，如：text_generation_template）"
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
                  placeholder="输入模板显示名称（中文，如：文本生成参数模板）"
                  required
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入模板描述"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>关联能力 *</label>
                <select
                  name="capability_id"
                  value={formData.capability_id}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">请选择能力</option>
                  {capabilities.map(capability => (
                    <option key={capability.id} value={capability.id}>
                      {capability.display_name || capability.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>参数配置（JSON格式）</label>
                <textarea
                  name="parameters"
                  value={JSON.stringify(formData.parameters, null, 2)}
                  onChange={handleParametersChange}
                  placeholder='输入JSON格式的参数配置，如：{"temperature": 0.7, "max_tokens": 1000}'
                  rows="6"
                  className="json-editor"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>级别</label>
                  <select
                    name="level"
                    value={formData.level}
                    onChange={handleInputChange}
                  >
                    <option value="basic">基础</option>
                    <option value="standard">标准</option>
                    <option value="advanced">高级</option>
                    <option value="expert">专家</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>版本</label>
                  <input
                    type="text"
                    name="version"
                    value={formData.version}
                    onChange={handleInputChange}
                    placeholder="如：1.0.0"
                  />
                </div>
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

export default CapabilityParameterTemplateManagement;