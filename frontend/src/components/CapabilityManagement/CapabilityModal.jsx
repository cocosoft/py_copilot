import React, { useState, useEffect } from 'react';
import '../../styles/ModelCapabilityManagement.css';

const CapabilityModal = ({ 
  visible, 
  mode, 
  capability, 
  onCancel, 
  onSubmit 
}) => {
  // 表单数据状态
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    capability_type: '',
    is_active: true
  });
  
  // 表单验证错误状态
  const [errors, setErrors] = useState({});
  
  // 当capability变化时更新表单数据（编辑模式）
  useEffect(() => {
    if (mode === 'edit' && capability) {
      setFormData({
        name: capability.name || '',
        display_name: capability.display_name || '',
        description: capability.description || '',
        capability_type: capability.capability_type || '',
        is_active: capability.is_active ?? true
      });
    } else if (mode === 'add') {
      // 创建模式时重置表单
      setFormData({
        name: '',
        display_name: '',
        description: '',
        capability_type: '',
        is_active: true
      });
    }
    // 重置错误信息
    setErrors({});
  }, [capability, mode]);
  
  // 处理输入变化
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // 清除对应字段的错误
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };
  
  // 表单验证
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = '请输入能力名称';
    } else if (formData.name.length > 100) {
      newErrors.name = '能力名称不能超过100个字符';
    }
    
    if (!formData.display_name.trim()) {
      newErrors.display_name = '请输入能力显示名称';
    } else if (formData.display_name.length > 100) {
      newErrors.display_name = '能力显示名称不能超过100个字符';
    }
    
    if (formData.description && formData.description.length > 500) {
      newErrors.description = '能力描述不能超过500个字符';
    }
    
    if (formData.capability_type && formData.capability_type.length > 50) {
      newErrors.capability_type = '能力类型不能超过50个字符';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // 处理表单提交
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };
  
  if (!visible) return null;
  
  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h3>{mode === 'add' ? '创建新能力' : '编辑能力'}</h3>
          <button className="btn-close" onClick={onCancel}>×</button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>名称 *</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="输入能力名称（英文，如：text_generation）"
              className={errors.name ? 'error-input' : ''}
            />
            {errors.name && <div className="error-message">{errors.name}</div>}
          </div>
          <div className="form-group">
            <label>显示名称 *</label>
            <input
              type="text"
              name="display_name"
              value={formData.display_name}
              onChange={handleInputChange}
              placeholder="输入能力显示名称（中文，如：文本生成）"
              className={errors.display_name ? 'error-input' : ''}
            />
            {errors.display_name && <div className="error-message">{errors.display_name}</div>}
          </div>
          <div className="form-group">
            <label>描述</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="输入能力描述"
              rows="3"
              className={errors.description ? 'error-input' : ''}
            />
            {errors.description && <div className="error-message">{errors.description}</div>}
          </div>
          <div className="form-group">
            <label>类型</label>
            <input
              type="text"
              name="capability_type"
              value={formData.capability_type}
              onChange={handleInputChange}
              placeholder="输入能力类型（如：text, vision, code）"
              className={errors.capability_type ? 'error-input' : ''}
            />
            {errors.capability_type && <div className="error-message">{errors.capability_type}</div>}
          </div>
          <div className="form-group form-check">
            <input
              type="checkbox"
              id={`is_active_${mode}`}
              name="is_active"
              checked={formData.is_active}
              onChange={handleInputChange}
            />
            <label htmlFor={`is_active_${mode}`}>启用</label>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onCancel}>
              取消
            </button>
            <button type="submit" className="btn btn-primary">
              {mode === 'add' ? '创建' : '更新'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CapabilityModal;