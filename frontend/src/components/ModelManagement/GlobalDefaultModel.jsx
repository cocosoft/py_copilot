import React from 'react';
import ModelSelectDropdown from './ModelSelectDropdown';

/**
 * 全局默认模型设置组件
 * 用于设置系统级别的默认AI模型
 */
const GlobalDefaultModel = ({ 
  models, 
  globalDefaultModel, 
  onModelSelect, 
  validationErrors, 
  isLoading 
}) => {
  return (
    <div className="setting-card">
      <div className="setting-header">
        <h4>全局默认模型</h4>
        <p>系统级别的默认AI模型，作为所有场景的基础默认值</p>
      </div>
      
      <div className="setting-item">
        <label htmlFor="globalDefaultModel">选择全局默认模型</label>
        <ModelSelectDropdown
          models={models}
          selectedModel={models.find(model => model.id === globalDefaultModel) || null}
          onModelSelect={onModelSelect}
          placeholder="请选择模型"
          disabled={isLoading}
          scene="chat"
        />
        {validationErrors.global && (
          <span className="field-error">{validationErrors.global}</span>
        )}
      </div>
    </div>
  );
};

export default GlobalDefaultModel;