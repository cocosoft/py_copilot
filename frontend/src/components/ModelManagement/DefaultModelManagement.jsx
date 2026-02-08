import React from 'react';
import useModelManagement from './hooks/useModelManagement';
import GlobalDefaultModel from './GlobalDefaultModel';
import LocalLLMConfig from './LocalLLMConfig';
import SceneDefaultModels from './SceneDefaultModels';
import DebugPanel from './DebugPanel';
import './DefaultModelManagement.css';

/**
 * 默认模型管理主组件
 * 整合所有子组件，提供完整的模型管理功能
 */
const DefaultModelManagement = () => {
  // 使用自定义钩子管理模型数据和逻辑
  const {
    // 状态
    globalDefaultModel,
    sceneDefaultModels,
    isSavingDefaultModel,
    models,
    isLoadingModels,
    error,
    validationErrors,
    hasUnsavedChanges,
    sceneModels,
    capabilityScores,
    localModels,
    isLoadingLocalModels,
    localModelConfig,
    
    // 方法
    handleGlobalModelSelect,
    handleSceneModelSelect,
    applySmartRecommendation,
    getRecommendedModels,
    handleSaveDefaultModel,
    handleSaveLocalModelConfig,
    loadModelsAndConfigs
  } = useModelManagement();

  return (
    <div className="default-model-management">
      
      {/* 调试信息面板 */}
      <DebugPanel 
        models={models}
        sceneModels={sceneModels}
        isLoading={isLoadingModels}
        localModels={localModels}
      />
      
      {/* 错误显示 */}
      {error && (
        <div className="error-message">
          <span>{error}</span>
          <button 
            className="retry-btn"
            onClick={loadModelsAndConfigs}
            disabled={isLoadingModels}
          >
            重试
          </button>
        </div>
      )}
      
      {/* 全局默认模型 */}
      <GlobalDefaultModel 
        models={models}
        globalDefaultModel={globalDefaultModel}
        onModelSelect={handleGlobalModelSelect}
        validationErrors={validationErrors}
        isLoading={isLoadingModels}
      />
      
      {/* 本地LLM调度配置 */}
      <LocalLLMConfig 
        localModels={localModels}
        localModelConfig={localModelConfig}
        onModelSelect={(model) => handleSaveLocalModelConfig(model.id)}
        isLoading={isLoadingLocalModels}
        isSaving={isSavingDefaultModel}
      />
      
      {/* 场景默认模型 */}
      <SceneDefaultModels 
        sceneDefaultModels={sceneDefaultModels}
        onModelSelect={handleSceneModelSelect}
        onApplyRecommendation={applySmartRecommendation}
        getRecommendedModels={getRecommendedModels}
        sceneModels={sceneModels}
        capabilityScores={capabilityScores}
        validationErrors={validationErrors}
        isLoading={isLoadingModels}
      />
      
      {/* 保存按钮 */}
      <div className="setting-actions">
        <button 
          className="save-btn" 
          onClick={handleSaveDefaultModel}
          disabled={isSavingDefaultModel || isLoadingModels || Object.keys(validationErrors).length > 0}
        >
          {isSavingDefaultModel && <span className="loading-spinner"></span>}
          {isSavingDefaultModel ? '保存中...' : '保存设置'}
        </button>
        
        {hasUnsavedChanges && (
          <span className="unsaved-changes-indicator">
            有未保存的更改
          </span>
        )}
      </div>
    </div>
  );
};

export default DefaultModelManagement;