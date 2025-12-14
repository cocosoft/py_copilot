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
  const [errors, setErrors] = useState({});
  const [showValidation, setShowValidation] = useState(false);

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
    setErrors({});
    setShowValidation(false);
  }, [parameter, mode]);

  if (!isOpen) return null;

  // 实时验证函数
  const validateField = (name, value) => {
    const newErrors = { ...errors };
    
    // 参数名称验证
    if (name === 'parameter_name') {
      if (!value.trim()) {
        newErrors.parameter_name = '参数名称不能为空';
      } else if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(value)) {
        newErrors.parameter_name = '参数名称只能包含字母、数字和下划线，且必须以字母或下划线开头';
      } else {
        delete newErrors.parameter_name;
      }
    }
    
    // 参数值验证
    if (name === 'parameter_value' || name === 'default_value') {
      if (formData.is_required && name === 'parameter_value' && !value.trim()) {
        newErrors.parameter_value = '必填参数不能为空';
      } else {
        try {
          // 根据参数类型进行验证
          if (value.trim() !== '') {
            switch (formData.parameter_type) {
              case 'number':
                if (isNaN(Number(value))) {
                  newErrors[name] = '请输入有效的数字';
                } else {
                  delete newErrors[name];
                }
                break;
              case 'boolean':
                if (value.toLowerCase() !== 'true' && value.toLowerCase() !== 'false') {
                  newErrors[name] = '布尔值只能是 true 或 false';
                } else {
                  delete newErrors[name];
                }
                break;
              case 'array':
                JSON.parse(value);
                delete newErrors[name];
                break;
              case 'object':
                JSON.parse(value);
                delete newErrors[name];
                break;
              default:
                delete newErrors[name];
            }
          } else {
            delete newErrors[name];
          }
        } catch (e) {
          newErrors[name] = `请输入有效的${formData.parameter_type}格式`;
        }
      }
    }
    
    setErrors(newErrors);
    return newErrors;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));
    
    // 实时验证
    validateField(name, newValue);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setShowValidation(true);
    
    // 验证所有字段
    const allErrors = {
      ...validateField('parameter_name', formData.parameter_name),
      ...validateField('parameter_value', formData.parameter_value),
      ...validateField('default_value', formData.default_value)
    };
    
    if (Object.keys(allErrors).length === 0) {
      onSave(formData);
      onClose();
    }
  };

  // 根据参数类型渲染不同的输入组件
  const renderInputComponent = (fieldName, value, onChange) => {
    const fieldValue = value || '';
    
    switch (formData.parameter_type) {
      case 'number':
        return (
          <input
            type="number"
            id={fieldName}
            name={fieldName}
            value={fieldValue === '' ? '' : Number(fieldValue)}
            onChange={onChange}
            placeholder={fieldName === 'parameter_value' ? '例如: 0.7' : '例如: 0.7'}
            step="any"
          />
        );
      case 'boolean':
        return (
          <select
            id={fieldName}
            name={fieldName}
            value={fieldValue}
            onChange={onChange}
          >
            <option value="">请选择</option>
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        );
      case 'array':
      case 'object':
        return (
          <textarea
            id={fieldName}
            name={fieldName}
            value={fieldValue}
            onChange={onChange}
            placeholder={fieldName === 'parameter_value' ? 
              formData.parameter_type === 'array' ? '例如: ["value1", "value2"]' : '例如: {"key": "value"}' : 
              formData.parameter_type === 'array' ? '例如: ["value1", "value2"]' : '例如: {"key": "value"}'
            }
            rows="4"
            className="json-editor"
          />
        );
      default:
        return (
          <input
            type="text"
            id={fieldName}
            name={fieldName}
            value={fieldValue}
            onChange={onChange}
            placeholder={fieldName === 'parameter_value' ? '例如: value' : '例如: value'}
          />
        );
    }
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
            <label htmlFor="parameter_name">参数名称 *</label>
            {renderInputComponent('parameter_name', formData.parameter_name, handleChange)}
            {showValidation && errors.parameter_name && (
              <div className="error-message">{errors.parameter_name}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="parameter_value">参数值 {formData.is_required ? '*' : ''}</label>
            {renderInputComponent('parameter_value', formData.parameter_value, handleChange)}
            {showValidation && errors.parameter_value && (
              <div className="error-message">{errors.parameter_value}</div>
            )}
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
            {renderInputComponent('default_value', formData.default_value, handleChange)}
            {showValidation && errors.default_value && (
              <div className="error-message">{errors.default_value}</div>
            )}
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