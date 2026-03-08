import React from 'react';
import ModelSelectDropdown from './ModelSelectDropdown';

/**
 * 场景默认模型设置组件
 * 为特定业务场景设置专属默认模型
 */
const SceneDefaultModels = ({ 
  sceneDefaultModels, 
  onModelSelect, 
  onApplyRecommendation, 
  getRecommendedModels, 
  sceneModels, 
  capabilityScores, 
  validationErrors, 
  isLoading 
}) => {
  // 场景配置
  const scenes = [
    {
      key: 'chat',
      label: '聊天场景',
      description: '对话、多轮对话、上下文管理'
    },
    {
      key: 'image',
      label: '图像场景',
      description: '图像生成、图像识别、视觉理解'
    },
    {
      key: 'video',
      label: '视频场景',
      description: '视频分析、视频生成、视频理解'
    },
    {
      key: 'voice',
      label: '语音场景',
      description: '语音识别、语音合成、语音分析'
    },
    {
      key: 'translate',
      label: '翻译场景',
      description: '语言翻译、多语言支持、翻译质量'
    },
    {
      key: 'knowledge',
      label: '知识库场景',
      description: '知识检索、信息合成、上下文感知'
    },
    {
      key: 'workflow',
      label: '工作流场景',
      description: '任务规划、步骤协调、流程优化'
    },
    {
      key: 'tool',
      label: '工具调用场景',
      description: '工具调用、API集成、函数执行'
    },
    {
      key: 'search',
      label: '搜索场景',
      description: '信息检索、相关性排序、语义搜索'
    },
    {
      key: 'mcp',
      label: 'MCP场景',
      description: '多模态处理、跨媒体理解、统一表示'
    },
    {
      key: 'topic_title',
      label: '话题标题生成',
      description: '对话内容总结、标题提炼、核心意图提取'
    },
    {
      key: 'embedding',
      label: '向量化场景',
      description: '文本向量化、语义嵌入、向量表示'
    },
    {
      key: 'rerank',
      label: '重排序场景',
      description: '搜索结果重排序、相关性优化、排序精调'
    }
  ];

  return (
    <div className="setting-card">
      <div className="setting-header">
        <h4>场景默认模型</h4>
        <p>为特定业务场景设置专属默认模型</p>
      </div>
      
      {scenes.map(scene => {
        const modelsForScene = Array.isArray(sceneModels[scene.key]) ? sceneModels[scene.key] : [];
        const recommendedModels = getRecommendedModels(scene.key);
        
        return (
          <div key={scene.key} className="setting-item">
            <div className="scene-header">
              <div className="scene-title">
                <label htmlFor={`${scene.key}Model`}>{scene.label}</label>
                <button 
                  className="recommend-btn"
                  onClick={() => onApplyRecommendation(scene.key)}
                  disabled={isLoading || !sceneModels[scene.key]?.length}
                  title="应用智能推荐"
                >
                  💡 智能推荐
                </button>
              </div>
              <span className="scene-description">{scene.description}</span>
            </div>
            <ModelSelectDropdown
              models={modelsForScene}
              selectedModel={modelsForScene.find(model => model.id === sceneDefaultModels[scene.key]) || null}
              onModelSelect={onModelSelect(scene.key)}
              placeholder="请选择模型"
              disabled={isLoading}
              scene={scene.key}
              getModelBadge={(model) => {
                const score = capabilityScores[`${scene.key}_${model.id}`];
                if (score) {
                  return (
                    <span className={`capability-badge ${score >= 90 ? 'excellent' : score >= 80 ? 'good' : score >= 70 ? 'fair' : 'poor'}`}>
                      {score}% 匹配
                    </span>
                  );
                }
                return null;
              }}
            />
            {validationErrors[scene.key] && (
              <span className="field-error">{validationErrors[scene.key]}</span>
            )}
            <div className="capability-info">
              <span className="info-text">基于{scene.description}能力进行匹配</span>
              {recommendedModels.length > 0 && (
                <div className="recommendation-list">
                  <span className="recommendation-title">推荐模型：</span>
                  {recommendedModels.map((model, index) => (
                    <span key={model.id} className="recommendation-item">
                      {index + 1}. {model.model_name || model.name} ({model.score}%)
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SceneDefaultModels;