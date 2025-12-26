import React, { useState, useEffect } from 'react';

const AgentParameterModal = ({ mode, parameter, onSave, onClose, saving }) => {
  const [formData, setFormData] = useState({
    parameter_name: '',
    parameter_value: '',
    parameter_type: 'string',
    description: '',
    parameter_group: ''
  });
  const [errors, setErrors] = useState({});
  const [bulkParams, setBulkParams] = useState([{ key: '', value: '', type: 'string' }]);
  const [showValidation, setShowValidation] = useState(false);

  useEffect(() => {
    if (mode === 'edit' && parameter) {
      setFormData({
        parameter_name: parameter.parameter_name || '',
        parameter_value: parameter.parameter_value || '',
        parameter_type: parameter.parameter_type || 'string',
        description: parameter.description || '',
        parameter_group: parameter.parameter_group || ''
      });
    } else if (mode === 'bulk') {
      setBulkParams([{ key: '', value: '', type: 'string' }]);
    }
    setErrors({});
    setShowValidation(false);
  }, [mode, parameter]);

  const validateField = (name, value) => {
    const newErrors = { ...errors };

    if (name === 'parameter_name') {
      if (!value.trim()) {
        newErrors.parameter_name = '参数名称不能为空';
      } else if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(value)) {
        newErrors.parameter_name = '参数名称只能包含字母、数字和下划线，且必须以字母或下划线开头';
      } else {
        delete newErrors.parameter_name;
      }
    }

    if ((name === 'parameter_value' || name === 'default_value') && formData.is_required && !value.trim()) {
      newErrors.parameter_value = '必填参数不能为空';
    } else if (name === 'parameter_value') {
      try {
        if (value.trim() !== '') {
          switch (formData.parameter_type) {
            case 'number':
              if (isNaN(Number(value))) {
                newErrors.parameter_value = '请输入有效的数字';
              } else {
                delete newErrors.parameter_value;
              }
              break;
            case 'boolean':
              if (value.toLowerCase() !== 'true' && value.toLowerCase() !== 'false') {
                newErrors.parameter_value = '布尔值只能是 true 或 false';
              } else {
                delete newErrors.parameter_value;
              }
              break;
            case 'array':
            case 'object':
              JSON.parse(value);
              delete newErrors.parameter_value;
              break;
            default:
              delete newErrors.parameter_value;
          }
        } else {
          delete newErrors.parameter_value;
        }
      } catch (e) {
        if (formData.parameter_type === 'array' || formData.parameter_type === 'object') {
          newErrors.parameter_value = `请输入有效的${formData.parameter_type}格式`;
        } else {
          delete newErrors.parameter_value;
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
    validateField(name, newValue);
  };

  const handleBulkParamChange = (index, field, value) => {
    const newBulkParams = [...bulkParams];
    newBulkParams[index] = { ...newBulkParams[index], [field]: value };
    setBulkParams(newBulkParams);
  };

  const addBulkParamRow = () => {
    setBulkParams([...bulkParams, { key: '', value: '', type: 'string' }]);
  };

  const removeBulkParamRow = (index) => {
    if (bulkParams.length > 1) {
      setBulkParams(bulkParams.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setShowValidation(true);

    if (mode === 'bulk') {
      const validParams = bulkParams.filter(p => p.key.trim() !== '' && p.value.trim() !== '');
      if (validParams.length === 0) {
        setErrors({ bulk: '请至少添加一个有效参数' });
        return;
      }
      onSave(validParams);
      onClose();
      return;
    }

    const allErrors = {
      ...validateField('parameter_name', formData.parameter_name),
      ...validateField('parameter_value', formData.parameter_value)
    };

    if (Object.keys(allErrors).length === 0) {
      onSave(formData);
      onClose();
    }
  };

  const renderValueInput = () => {
    switch (formData.parameter_type) {
      case 'number':
        return (
          <input
            type="number"
            name="parameter_value"
            value={formData.parameter_value}
            onChange={handleChange}
            placeholder="例如: 0.7"
            step="any"
          />
        );
      case 'boolean':
        return (
          <select name="parameter_value" value={formData.parameter_value} onChange={handleChange}>
            <option value="">请选择</option>
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        );
      case 'array':
      case 'object':
        return (
          <textarea
            name="parameter_value"
            value={formData.parameter_value}
            onChange={handleChange}
            placeholder={formData.parameter_type === 'array' ? '例如: ["value1", "value2"]' : '例如: {"key": "value"}'}
            rows="4"
          />
        );
      default:
        return (
          <input
            type="text"
            name="parameter_value"
            value={formData.parameter_value}
            onChange={handleChange}
            placeholder="例如: value"
          />
        );
    }
  };

  const getModalTitle = () => {
    switch (mode) {
      case 'add':
        return '添加参数';
      case 'edit':
        return '编辑参数';
      case 'bulk':
        return '批量添加参数';
      default:
        return '参数设置';
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content agent-parameter-modal">
        <div className="modal-header">
          <h2>{getModalTitle()}</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {mode === 'bulk' ? (
            <div className="bulk-form">
              <div className="bulk-header">
                <span>参数名称</span>
                <span>参数值</span>
                <span>类型</span>
                <span>操作</span>
              </div>
              {bulkParams.map((param, index) => (
                <div key={index} className="bulk-row">
                  <input
                    type="text"
                    value={param.key}
                    onChange={(e) => handleBulkParamChange(index, 'key', e.target.value)}
                    placeholder="参数名"
                  />
                  <input
                    type="text"
                    value={param.value}
                    onChange={(e) => handleBulkParamChange(index, 'value', e.target.value)}
                    placeholder="参数值"
                  />
                  <select
                    value={param.type}
                    onChange={(e) => handleBulkParamChange(index, 'type', e.target.value)}
                  >
                    <option value="string">字符串</option>
                    <option value="number">数值</option>
                    <option value="boolean">布尔值</option>
                    <option value="integer">整数</option>
                  </select>
                  <button
                    type="button"
                    className="bulk-remove-btn"
                    onClick={() => removeBulkParamRow(index)}
                    disabled={bulkParams.length === 1}
                  >
                    ×
                  </button>
                </div>
              ))}
              <button type="button" className="bulk-add-btn" onClick={addBulkParamRow}>
                + 添加参数
              </button>
              {errors.bulk && <div className="error-message">{errors.bulk}</div>}
            </div>
          ) : (
            <>
              <div className="form-group">
                <label htmlFor="parameter_name">参数名称 *</label>
                <input
                  type="text"
                  id="parameter_name"
                  name="parameter_name"
                  value={formData.parameter_name}
                  onChange={handleChange}
                  placeholder="例如: temperature"
                  disabled={mode === 'edit'}
                />
                {showValidation && errors.parameter_name && (
                  <div className="error-message">{errors.parameter_name}</div>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="parameter_value">参数值 {formData.parameter_type === 'boolean' ? '' : ''}</label>
                {renderValueInput()}
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
                  <option value="number">数值</option>
                  <option value="integer">整数</option>
                  <option value="boolean">布尔值</option>
                  <option value="array">数组</option>
                  <option value="object">对象</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="parameter_group">参数分组</label>
                <input
                  type="text"
                  id="parameter_group"
                  name="parameter_group"
                  value={formData.parameter_group}
                  onChange={handleChange}
                  placeholder="例如: LLM配置"
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
                />
              </div>
            </>
          )}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              取消
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? '保存中...' : (mode === 'add' ? '添加' : mode === 'bulk' ? '批量添加' : '保存')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AgentParameterModal;
