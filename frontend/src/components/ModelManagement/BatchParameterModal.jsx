import React, { useState } from 'react';
import '../../styles/ModelModal.css';

const BatchParameterModal = ({ isOpen, onClose, onSave, selectedParameters }) => {
  const [formData, setFormData] = useState({
    parameter_value: '',
    is_required: null,
    description: ''
  });

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // 过滤出有值的字段
    const updateData = {};
    if (formData.parameter_value !== '') {
      updateData.parameter_value = formData.parameter_value;
    }
    if (formData.is_required !== null) {
      updateData.is_required = formData.is_required;
    }
    if (formData.description !== '') {
      updateData.description = formData.description;
    }
    
    if (Object.keys(updateData).length === 0) {
      alert('请选择要更新的字段');
      return;
    }
    
    onSave(updateData);
    onClose();
    
    // 重置表单
    setFormData({
      parameter_value: '',
      is_required: null,
      description: ''
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>批量编辑参数</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        
        <div className="modal-info">
          <p>将批量更新选中的 <strong>{selectedParameters.length} 个参数</strong></p>
          <p className="batch-edit-hint">提示：仅选择有变化的字段进行更新</p>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="parameter_value">参数值</label>
            <input
              type="text"
              id="parameter_value"
              name="parameter_value"
              value={formData.parameter_value}
              onChange={handleChange}
              placeholder="例如: 0.7"
            />
          </div>

          <div className="form-group checkbox-group">
            <input
              type="checkbox"
              id="is_required"
              name="is_required"
              checked={formData.is_required === true}
              onChange={(e) => handleChange({ target: { name: 'is_required', checked: e.target.checked, type: 'checkbox' } })}
            />
            <label htmlFor="is_required">设为必填参数</label>
          </div>

          <div className="form-group">
            <label htmlFor="description">描述</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="更新参数的描述"
              rows="3"
            ></textarea>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              取消
            </button>
            <button type="submit" className="btn btn-primary">
              批量更新
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BatchParameterModal;