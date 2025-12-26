import React, { useState, useEffect } from 'react';
import '../../styles/ParameterManagement.css';
import api from '../../utils/api';

const ParameterTemplateModal = ({ isOpen, onClose, onSave, templateData, mode }) => {
  const [formData, setFormData] = useState({
    template_name: '',
    description: '',
    parameters: []
  });
  
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  
  // 当模板数据变化时，更新表单数据
  useEffect(() => {
    if (templateData && mode === 'edit') {
      setFormData({
        template_name: templateData.template_name || templateData.name || '',
        description: templateData.description || '',
        parameters: templateData.parameters || [],
      });
    } else if (mode === 'add') {
      setFormData({
        template_name: '',
        description: '',
        parameters: []
      });
    }
  }, [templateData, mode]);
  
  // 处理表单字段变化
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // 清除该字段的错误
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };
  
  // 处理参数列表变化
  const handleParameterChange = (index, field, value) => {
    const newParameters = [...formData.parameters];
    if (!newParameters[index]) {
      newParameters[index] = {};
    }
    newParameters[index][field] = value;
    setFormData(prev => ({
      ...prev,
      parameters: newParameters
    }));
  };
  
  // 添加新参数
  const addParameter = () => {
    setFormData(prev => ({
      ...prev,
      parameters: [...prev.parameters, {
        parameter_name: '',
        parameter_value: '',
        parameter_type: 'string',
        default_value: '',
        description: '',
        is_required: false
      }]
    }));
  };
  
  // 删除参数
  const removeParameter = (index) => {
    const newParameters = formData.parameters.filter((_, i) => i !== index);
    setFormData(prev => ({
      ...prev,
      parameters: newParameters
    }));
  };
  
  // 表单验证
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.template_name.trim()) {
      newErrors.template_name = '模板名称不能为空';
    }
    
    // 验证参数列表
    formData.parameters.forEach((param, index) => {
      if (!param.parameter_name.trim()) {
        if (!newErrors.parameters) {
          newErrors.parameters = [];
        }
        newErrors.parameters[index] = '参数名称不能为空';
      }
      
      // 验证数组和对象类型的参数值格式
      if (param.parameter_type === 'array' || param.parameter_type === 'object') {
        if (param.parameter_value.trim()) {
          try {
            JSON.parse(param.parameter_value);
          } catch (e) {
            if (!newErrors.parameters) {
              newErrors.parameters = [];
            }
            newErrors.parameters[index] = `${param.parameter_type === 'array' ? '数组' : '对象'}类型的参数值必须是有效的JSON格式`;
          }
        }
        
        if (param.default_value.trim()) {
          try {
            JSON.parse(param.default_value);
          } catch (e) {
            if (!newErrors.parameters) {
              newErrors.parameters = [];
            }
            newErrors.parameters[index] = `${param.parameter_type === 'array' ? '数组' : '对象'}类型的默认值必须是有效的JSON格式`;
          }
        }
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      setLoading(true);
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error('保存参数模板失败:', error);
      setErrors({ submit: '保存失败，请重试' });
    } finally {
      setLoading(false);
    }
  };
  
  // 处理关闭模态框
  const handleClose = () => {
    setErrors({});
    onClose();
  };
  
  if (!isOpen) {
    return null;
  }
  
  return (
    <div className="modal-overlay">
      <div className="modal-content template-modal">
        <div className="modal-header">
          <h3>{mode === 'add' ? '创建参数模板' : '编辑参数模板'}</h3>
          <button className="close-button" onClick={handleClose}>&times;</button>
        </div>
        
        <form onSubmit={handleSubmit} className="parameter-template-form">
          {errors.submit && <div className="error-message">{errors.submit}</div>}
          
          <div className="modal-body">
            <div className="form-group">
              <label htmlFor="template_name">模板名称 <span className="required">*</span></label>
              <input
                type="text"
                id="template_name"
                name="template_name"
                value={formData.template_name}
                onChange={handleChange}
                placeholder="请输入模板名称"
                className={errors.template_name ? 'error' : ''}
              />
              {errors.template_name && <div className="error-text">{errors.template_name}</div>}
            </div>
            

            

            
            <div className="form-group">
              <label htmlFor="description">描述</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="请输入模板描述"
                rows={3}
              />
            </div>
            
            <div className="parameters-section">
              <div className="section-header">
                <h4>参数配置</h4>
                <button type="button" className="btn btn-primary btn-small" onClick={addParameter}>
                  添加参数
                </button>
              </div>
              
              {formData.parameters.length > 0 ? (
                <div className="parameters-list">
                  {formData.parameters.map((param, index) => (
                    <div key={index} className="parameter-item">
                      <div className="parameter-header">
                        <h5>参数 {index + 1}</h5>
                        <button 
                          type="button" 
                          className="btn btn-danger btn-small"
                          onClick={() => removeParameter(index)}
                        >
                          删除
                        </button>
                      </div>
                      
                      <div className="parameter-form">
                        <div className="form-row">
                          <div className="form-group">
                            <label>参数名称 <span className="required">*</span></label>
                            <input
                              type="text"
                              value={param.parameter_name || ''}
                              onChange={(e) => handleParameterChange(index, 'parameter_name', e.target.value)}
                              placeholder="请输入参数名称"
                              className={errors.parameters?.[index] ? 'error' : ''}
                            />
                            {errors.parameters?.[index] && <div className="error-text">{errors.parameters[index]}</div>}
                          </div>
                          
                          <div className="form-group">
                            <label>参数类型</label>
                            <select
                              value={param.parameter_type || 'string'}
                              onChange={(e) => handleParameterChange(index, 'parameter_type', e.target.value)}
                            >
                              <option value="string">字符串</option>
                              <option value="integer">整数</option>
                              <option value="float">浮点数</option>
                              <option value="boolean">布尔值</option>
                              <option value="array">数组</option>
                              <option value="object">对象</option>
                            </select>
                          </div>
                        </div>
                        
                        <div className="form-row">
                          <div className="form-group">
                            <label>参数值</label>
                            <input
                              type="text"
                              value={param.parameter_value || ''}
                              onChange={(e) => handleParameterChange(index, 'parameter_value', e.target.value)}
                              placeholder="请输入参数值"
                            />
                          </div>
                          
                          <div className="form-group">
                            <label>默认值</label>
                            <input
                              type="text"
                              value={param.default_value || ''}
                              onChange={(e) => handleParameterChange(index, 'default_value', e.target.value)}
                              placeholder="请输入默认值"
                            />
                          </div>
                        </div>
                        
                        <div className="form-row">
                          <div className="form-group">
                            <label>描述</label>
                            <input
                              type="text"
                              value={param.description || ''}
                              onChange={(e) => handleParameterChange(index, 'description', e.target.value)}
                              placeholder="请输入参数描述"
                            />
                          </div>
                          
                          <div className="form-group">
                            <label>必填</label>
                            <select
                              value={param.is_required ? 'true' : 'false'}
                              onChange={(e) => handleParameterChange(index, 'is_required', e.target.value === 'true')}
                            >
                              <option value="false">否</option>
                              <option value="true">是</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">暂无参数，请点击"添加参数"按钮添加参数</div>
              )}
            </div>
          </div>
          
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={handleClose} disabled={loading}>
              取消
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? (mode === 'add' ? '创建中...' : '保存中...') : (mode === 'add' ? '创建' : '保存')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ParameterTemplateModal;