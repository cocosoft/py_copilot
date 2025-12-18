import React, { useState } from 'react';
import '../../styles/ModelModal.css';

const BatchParameterModal = ({ isOpen, onClose, onSave, selectedParameters }) => {
  const [formData, setFormData] = useState({
    parameter_value: '',
    parameter_type: '',
    default_value: '',
    is_required: null,
    description: '',
    // 验证规则 - 只支持部分通用规则的批量更新
    validation_rules: {
      min: '',
      max: '',
      min_length: '',
      max_length: ''
    }
  });

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    
    if (name.startsWith('validation_rules.')) {
      // 处理验证规则的嵌套对象变更
      const ruleName = name.split('.')[1];
      setFormData(prev => ({
        ...prev,
        validation_rules: {
          ...prev.validation_rules,
          [ruleName]: newValue
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: newValue
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // 过滤出有值的字段
    const updateData = {};
    
    if (formData.parameter_value !== '') {
      updateData.parameter_value = formData.parameter_value;
    }
    
    if (formData.parameter_type !== '') {
      updateData.parameter_type = formData.parameter_type;
    }
    
    if (formData.default_value !== '') {
      updateData.default_value = formData.default_value;
    }
    
    if (formData.is_required !== null) {
      updateData.is_required = formData.is_required;
    }
    
    if (formData.description !== '') {
      updateData.description = formData.description;
    }
    
    // 处理验证规则
    const validationRules = {};
    Object.entries(formData.validation_rules).forEach(([key, value]) => {
      if (value !== '') {
        validationRules[key] = key === 'min' || key === 'max' || key === 'min_length' || key === 'max_length' ? Number(value) : value;
      }
    });
    
    if (Object.keys(validationRules).length > 0) {
      updateData.validation_rules = validationRules;
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
      parameter_type: '',
      default_value: '',
      is_required: null,
      description: '',
      validation_rules: {
        min: '',
        max: '',
        min_length: '',
        max_length: ''
      }
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

          <div className="form-group">
            <label htmlFor="parameter_type">参数类型</label>
            <select
              id="parameter_type"
              name="parameter_type"
              value={formData.parameter_type}
              onChange={handleChange}
            >
              <option value="">保持不变</option>
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
              placeholder="例如: 0.5"
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

          <div className="form-section">
            <h3>验证规则（批量更新）</h3>
            
            <div className="form-row">
              <div className="form-group half-width">
                <label htmlFor="validation_rules.min">最小值</label>
                <input
                  type="number"
                  id="validation_rules.min"
                  name="validation_rules.min"
                  value={formData.validation_rules.min}
                  onChange={handleChange}
                  placeholder="例如: 0"
                  step="any"
                />
              </div>
              
              <div className="form-group half-width">
                <label htmlFor="validation_rules.max">最大值</label>
                <input
                  type="number"
                  id="validation_rules.max"
                  name="validation_rules.max"
                  value={formData.validation_rules.max}
                  onChange={handleChange}
                  placeholder="例如: 100"
                  step="any"
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group half-width">
                <label htmlFor="validation_rules.min_length">最小长度</label>
                <input
                  type="number"
                  id="validation_rules.min_length"
                  name="validation_rules.min_length"
                  value={formData.validation_rules.min_length}
                  onChange={handleChange}
                  placeholder="例如: 1"
                />
              </div>
              
              <div className="form-group half-width">
                <label htmlFor="validation_rules.max_length">最大长度</label>
                <input
                  type="number"
                  id="validation_rules.max_length"
                  name="validation_rules.max_length"
                  value={formData.validation_rules.max_length}
                  onChange={handleChange}
                  placeholder="例如: 100"
                />
              </div>
            </div>
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