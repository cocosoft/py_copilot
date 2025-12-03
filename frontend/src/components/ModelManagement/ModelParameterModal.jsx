import React, { useState, useEffect } from 'react';
import '../../styles/ModelModal.css';

const ModelParameterModal = ({ isOpen, onClose, onSave, parameter, mode }) => {
  const [formData, setFormData] = useState({
    parameter_name: '',
    parameter_value: '',
    parameter_type: 'string',
    default_value: '',
    description: '',
    is_required: false
  });

  // 当参数或模式变化时，重置表单数据
  useEffect(() => {
    if (parameter) {
      setFormData({
        parameter_name: parameter.parameter_name || '',
        parameter_value: parameter.parameter_value || '',
        parameter_type: parameter.parameter_type || 'string',
        default_value: parameter.default_value || '',
        description: parameter.description || '',
        is_required: parameter.is_required || false
      });
    } else {
      setFormData({
        parameter_name: '',
        parameter_value: '',
        parameter_type: 'string',
        default_value: '',
        description: '',
        is_required: false
      });
    }
  }, [parameter, mode]);

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
    onSave(formData);
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{mode === 'add' ? '添加模型参数' : '编辑模型参数'}</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="parameter_name">参数名称</label>
            <input
              type="text"
              id="parameter_name"
              name="parameter_name"
              value={formData.parameter_name}
              onChange={handleChange}
              required
              placeholder="例如: temperature"
            />
          </div>

          <div className="form-group">
            <label htmlFor="parameter_value">参数值</label>
            <input
              type="text"
              id="parameter_value"
              name="parameter_value"
              value={formData.parameter_value}
              onChange={handleChange}
              required
              placeholder="例如: 0.7"
            />
          </div>

          <div className="form-group">
            <label htmlFor="parameter_type">参数类型</label>
            <select
              id="parameter_type"
              name="parameter_type"
              value={formData.parameter_type}
              onChange={handleChange}
            >
              <option value="string">字符串</option>
              <option value="number">数字</option>
              <option value="boolean">布尔值</option>
              <option value="array">数组</option>
              <option value="object">对象</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="default_value">默认值</label>
            <input
              type="text"
              id="default_value"
              name="default_value"
              value={formData.default_value}
              onChange={handleChange}
              placeholder="例如: 0.7"
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">描述</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="参数的详细描述"
              rows="3"
            ></textarea>
          </div>

          <div className="form-group checkbox-group">
            <input
              type="checkbox"
              id="is_required"
              name="is_required"
              checked={formData.is_required}
              onChange={handleChange}
            />
            <label htmlFor="is_required">必填参数</label>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              取消
            </button>
            <button type="submit" className="btn btn-primary">
              {mode === 'add' ? '添加' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ModelParameterModal;