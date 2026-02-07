import React from 'react';
import ModelSelectDropdown from './ModelSelectDropdown';

/**
 * 本地LLM调度配置组件
 * 用于配置本地模型作为调度器
 */
const LocalLLMConfig = ({ 
  localModels, 
  localModelConfig, 
  onModelSelect, 
  isLoading, 
  isSaving 
}) => {
  return (
    <div className="setting-card">
      <div className="setting-header">
        <h4>本地LLM调度配置</h4>
        <p>配置本地模型作为调度器，处理高频、简单的调度决策</p>
      </div>
      
      <div className="setting-item">
        <label htmlFor="localModel">选择本地调度模型</label>
        <ModelSelectDropdown
          models={localModels}
          selectedModel={localModels.find(model => model.id === localModelConfig?.model_id) || null}
          onModelSelect={onModelSelect}
          placeholder="请选择本地模型"
          disabled={isLoading || isSaving}
          scene="chat"
        />
        {isLoading && (
          <span className="loading-text">加载本地模型中...</span>
        )}
        {localModelConfig && (
          <div className="config-info">
            <span>当前配置: {localModels.find(m => m.id === localModelConfig.model_id)?.model_name || localModelConfig.model_id}</span>
          </div>
        )}
      </div>
      
      <div className="setting-info">
        <h5>本地LLM调度优势</h5>
        <ul>
          <li>降低成本：减少对云端API的依赖</li>
          <li>提升性能：本地调用延迟更低</li>
          <li>增强隐私：敏感数据不出本地</li>
          <li>提高可控性：完全控制调度逻辑</li>
        </ul>
        <h5>推荐模型</h5>
        <p>Llama 3.1 8B 或 Qwen2.5 7B（平衡性能和资源占用）</p>
      </div>
    </div>
  );
};

export default LocalLLMConfig;