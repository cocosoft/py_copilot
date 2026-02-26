import React, { useState, useEffect } from 'react';
import { useI18n } from '../../hooks/useI18n';
import '../../styles/ModelModal.css';

const ModelParameterModal = ({ isOpen, onClose, onSave, parameter, mode }) => {
  const { t } = useI18n();
  const [formData, setFormData] = useState({
    parameter_name: '',
    parameter_value: '',
    parameter_type: 'string',
    default_value: '',
    description: '',
    is_required: false,
    validation_rules: {
      min: '',
      max: '',
      regex: '',
      enum_values: '',
      min_length: '',
      max_length: '',
      custom_message: ''
    }
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
        is_required: parameter.is_required || false,
        validation_rules: parameter.validation_rules || {
          min: '',
          max: '',
          regex: '',
          enum_values: '',
          min_length: '',
          max_length: '',
          custom_message: ''
        }
      });
    } else {
      setFormData({
        parameter_name: '',
        parameter_value: '',
        parameter_type: 'string',
        default_value: '',
        description: '',
        is_required: false,
        validation_rules: {
          min: '',
          max: '',
          regex: '',
          enum_values: '',
          min_length: '',
          max_length: '',
          custom_message: ''
        }
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
        newErrors.parameter_name = t('settings.modelParameterModal.validation.nameRequired');
      } else if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(value)) {
        newErrors.parameter_name = t('settings.modelParameterModal.validation.nameFormat');
      } else {
        delete newErrors.parameter_name;
      }
    }
    
    // 参数值验证
    if (name === 'parameter_value' || name === 'default_value') {
      if (formData.is_required && name === 'parameter_value' && !value.trim()) {
        newErrors.parameter_value = t('settings.modelParameterModal.validation.valueRequired');
      } else {
        try {
          // 根据参数类型进行验证
          if (value.trim() !== '') {
            switch (formData.parameter_type) {
              case 'number':
                const numValue = Number(value);
                if (isNaN(numValue)) {
                  newErrors[name] = t('settings.modelParameterModal.validation.invalidNumber');
                } else {
                  // 验证最小值
                  if (formData.validation_rules.min !== '' && numValue < Number(formData.validation_rules.min)) {
                    newErrors[name] = t('settings.modelParameterModal.validation.minValue', { min: formData.validation_rules.min });
                  }
                  // 验证最大值
                  else if (formData.validation_rules.max !== '' && numValue > Number(formData.validation_rules.max)) {
                    newErrors[name] = t('settings.modelParameterModal.validation.maxValue', { max: formData.validation_rules.max });
                  }
                  else {
                    delete newErrors[name];
                  }
                }
                break;
              case 'boolean':
                if (value.toLowerCase() !== 'true' && value.toLowerCase() !== 'false') {
                  newErrors[name] = t('settings.modelParameterModal.validation.invalidBoolean');
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
              case 'string':
                // 验证正则表达式
                if (formData.validation_rules.regex !== '' && !new RegExp(formData.validation_rules.regex).test(value)) {
                  newErrors[name] = t('settings.modelParameterModal.validation.regexError', { regex: formData.validation_rules.regex });
                }
                // 验证字符串长度
                else if (formData.validation_rules.min_length !== '' && value.length < Number(formData.validation_rules.min_length)) {
                  newErrors[name] = t('settings.modelParameterModal.validation.minLength', { minLength: formData.validation_rules.min_length });
                }
                else if (formData.validation_rules.max_length !== '' && value.length > Number(formData.validation_rules.max_length)) {
                  newErrors[name] = t('settings.modelParameterModal.validation.maxLength', { maxLength: formData.validation_rules.max_length });
                }
                // 验证枚举值
                else if (formData.validation_rules.enum_values !== '') {
                  const enumValues = JSON.parse(formData.validation_rules.enum_values);
                  if (!enumValues.includes(value)) {
                    newErrors[name] = t('settings.modelParameterModal.validation.enumError', { values: enumValues.join(', ') });
                  } else {
                    delete newErrors[name];
                  }
                }
                else {
                  delete newErrors[name];
                }
                break;
              default:
                delete newErrors[name];
            }
          } else {
            delete newErrors[name];
          }
        } catch (e) {
          if (e instanceof SyntaxError && (formData.parameter_type === 'array' || formData.parameter_type === 'object')) {
            newErrors[name] = t('settings.modelParameterModal.validation.invalidType', { type: formData.parameter_type });
          } else if (e instanceof SyntaxError && formData.validation_rules.enum_values) {
            newErrors.enum_values = t('settings.modelParameterModal.validation.enumFormatError');
          } else {
            newErrors[name] = formData.validation_rules.custom_message || t('settings.modelParameterModal.validation.invalidValue');
          }
        }
      }
    }
    
    // 验证规则字段验证
    if (name.startsWith('validation_rules.')) {
      const ruleName = name.split('.')[1];
      switch (ruleName) {
        case 'min':
        case 'max':
        case 'min_length':
        case 'max_length':
          if (value !== '' && isNaN(Number(value))) {
            newErrors[name] = t('settings.modelParameterModal.validation.invalidMin');
          } else {
            delete newErrors[name];
          }
          break;
        case 'regex':
          try {
            if (value !== '') {
              new RegExp(value);
            }
            delete newErrors[name];
          } catch (e) {
            newErrors[name] = t('settings.modelParameterModal.validation.invalidRegex');
          }
          break;
        case 'enum_values':
          try {
            if (value !== '') {
              const parsed = JSON.parse(value);
              if (!Array.isArray(parsed)) {
                newErrors[name] = t('settings.modelParameterModal.validation.enumArrayError');
              } else {
                delete newErrors[name];
              }
            } else {
              delete newErrors[name];
            }
          } catch (e) {
            newErrors[name] = t('settings.modelParameterModal.validation.enumFormatError');
          }
          break;
      }
    }
    
    setErrors(newErrors);
    return newErrors;
  };

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
      validateField(name, newValue);
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: newValue
      }));
      validateField(name, newValue);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setShowValidation(true);
    
    // 验证所有字段
    const allErrors = {
      ...validateField('parameter_name', formData.parameter_name),
      ...validateField('parameter_value', formData.parameter_value),
      ...validateField('default_value', formData.default_value),
      ...validateField('validation_rules.min', formData.validation_rules.min),
      ...validateField('validation_rules.max', formData.validation_rules.max),
      ...validateField('validation_rules.min_length', formData.validation_rules.min_length),
      ...validateField('validation_rules.max_length', formData.validation_rules.max_length),
      ...validateField('validation_rules.regex', formData.validation_rules.regex),
      ...validateField('validation_rules.enum_values', formData.validation_rules.enum_values)
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
            placeholder={t('settings.modelParameterModal.placeholders.number')}
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
            <option value="">{t('settings.modelParameterModal.booleanOptions.placeholder')}</option>
            <option value="true">{t('settings.modelParameterModal.booleanOptions.true')}</option>
            <option value="false">{t('settings.modelParameterModal.booleanOptions.false')}</option>
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
            placeholder={formData.parameter_type === 'array'
              ? t('settings.modelParameterModal.placeholders.array')
              : t('settings.modelParameterModal.placeholders.object')
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
            placeholder={t('settings.modelParameterModal.placeholders.string')}
          />
        );
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{mode === 'add' ? t('settings.modelParameterModal.title.add') : t('settings.modelParameterModal.title.edit')}</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="modal-body">
            <div className="form-group">
              <label htmlFor="parameter_name">{t('settings.modelParameterModal.form.parameterName')}</label>
              {renderInputComponent('parameter_name', formData.parameter_name, handleChange)}
              {showValidation && errors.parameter_name && (
                <div className="error-message">{errors.parameter_name}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="parameter_value">
                {formData.is_required
                  ? t('settings.modelParameterModal.form.parameterValueRequired')
                  : t('settings.modelParameterModal.form.parameterValue')
                }
              </label>
              {renderInputComponent('parameter_value', formData.parameter_value, handleChange)}
              {showValidation && errors.parameter_value && (
                <div className="error-message">{errors.parameter_value}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="parameter_type">{t('settings.modelParameterModal.form.parameterType')}</label>
              <select
                id="parameter_type"
                name="parameter_type"
                value={formData.parameter_type}
                onChange={handleChange}
              >
                <option value="string">{t('settings.modelParameterModal.types.string')}</option>
                <option value="number">{t('settings.modelParameterModal.types.number')}</option>
                <option value="boolean">{t('settings.modelParameterModal.types.boolean')}</option>
                <option value="array">{t('settings.modelParameterModal.types.array')}</option>
                <option value="object">{t('settings.modelParameterModal.types.object')}</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="default_value">{t('settings.modelParameterModal.form.defaultValue')}</label>
              {renderInputComponent('default_value', formData.default_value, handleChange)}
              {showValidation && errors.default_value && (
                <div className="error-message">{errors.default_value}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="description">{t('settings.modelParameterModal.form.description')}</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder={t('settings.modelParameterModal.form.descriptionPlaceholder')}
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
              <label htmlFor="is_required">{t('settings.modelParameterModal.form.isRequired')}</label>
            </div>

            <div className="form-section">
              <h3>{t('settings.modelParameterModal.form.validationRules')}</h3>

              {/* 数字类型验证规则 */}
              {formData.parameter_type === 'number' && (
                <>
                  <div className="form-row">
                    <div className="form-group half-width">
                      <label htmlFor="validation_rules.min">{t('settings.modelParameterModal.form.min')}</label>
                      <input
                        type="number"
                        id="validation_rules.min"
                        name="validation_rules.min"
                        value={formData.validation_rules.min}
                        onChange={handleChange}
                        placeholder={t('settings.modelParameterModal.form.minPlaceholder')}
                        step="any"
                      />
                      {showValidation && errors['validation_rules.min'] && (
                        <div className="error-message">{errors['validation_rules.min']}</div>
                      )}
                    </div>

                    <div className="form-group half-width">
                      <label htmlFor="validation_rules.max">{t('settings.modelParameterModal.form.max')}</label>
                      <input
                        type="number"
                        id="validation_rules.max"
                        name="validation_rules.max"
                        value={formData.validation_rules.max}
                        onChange={handleChange}
                        placeholder={t('settings.modelParameterModal.form.maxPlaceholder')}
                        step="any"
                      />
                      {showValidation && errors['validation_rules.max'] && (
                        <div className="error-message">{errors['validation_rules.max']}</div>
                      )}
                    </div>
                  </div>
                </>
              )}
              
              {/* 字符串类型验证规则 */}
              {formData.parameter_type === 'string' && (
                <>
                  <div className="form-group">
                    <label htmlFor="validation_rules.regex">{t('settings.modelParameterModal.form.regex')}</label>
                    <input
                      type="text"
                      id="validation_rules.regex"
                      name="validation_rules.regex"
                      value={formData.validation_rules.regex}
                      onChange={handleChange}
                      placeholder={t('settings.modelParameterModal.form.regexPlaceholder')}
                    />
                    {showValidation && errors['validation_rules.regex'] && (
                      <div className="error-message">{errors['validation_rules.regex']}</div>
                    )}
                  </div>

                  <div className="form-row">
                    <div className="form-group half-width">
                      <label htmlFor="validation_rules.min_length">{t('settings.modelParameterModal.form.minLength')}</label>
                      <input
                        type="number"
                        id="validation_rules.min_length"
                        name="validation_rules.min_length"
                        value={formData.validation_rules.min_length}
                        onChange={handleChange}
                        placeholder={t('settings.modelParameterModal.form.minLengthPlaceholder')}
                      />
                      {showValidation && errors['validation_rules.min_length'] && (
                        <div className="error-message">{errors['validation_rules.min_length']}</div>
                      )}
                    </div>

                    <div className="form-group half-width">
                      <label htmlFor="validation_rules.max_length">{t('settings.modelParameterModal.form.maxLength')}</label>
                      <input
                        type="number"
                        id="validation_rules.max_length"
                        name="validation_rules.max_length"
                        value={formData.validation_rules.max_length}
                        onChange={handleChange}
                        placeholder={t('settings.modelParameterModal.form.maxLengthPlaceholder')}
                      />
                      {showValidation && errors['validation_rules.max_length'] && (
                        <div className="error-message">{errors['validation_rules.max_length']}</div>
                      )}
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="validation_rules.enum_values">{t('settings.modelParameterModal.form.enumValues')}</label>
                    <input
                      type="text"
                      id="validation_rules.enum_values"
                      name="validation_rules.enum_values"
                      value={formData.validation_rules.enum_values}
                      onChange={handleChange}
                      placeholder={t('settings.modelParameterModal.form.enumValuesPlaceholder')}
                    />
                    {showValidation && errors['validation_rules.enum_values'] && (
                      <div className="error-message">{errors['validation_rules.enum_values']}</div>
                    )}
                  </div>
                </>
              )}

              {/* 通用验证规则 */}
              <div className="form-group">
                <label htmlFor="validation_rules.custom_message">{t('settings.modelParameterModal.form.customMessage')}</label>
                <input
                  type="text"
                  id="validation_rules.custom_message"
                  name="validation_rules.custom_message"
                  value={formData.validation_rules.custom_message}
                  onChange={handleChange}
                  placeholder={t('settings.modelParameterModal.form.customMessagePlaceholder')}
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              {t('settings.modelParameterModal.buttons.cancel')}
            </button>
            <button type="submit" className="btn btn-primary">
              {mode === 'add' ? t('settings.modelParameterModal.buttons.add') : t('settings.modelParameterModal.buttons.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ModelParameterModal;