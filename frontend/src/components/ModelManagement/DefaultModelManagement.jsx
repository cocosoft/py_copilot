import { useState, useEffect } from 'react';
import { defaultModelApi, supplierApi } from '../../utils/api';
import ModelSelectDropdown from './ModelSelectDropdown';

const DefaultModelManagement = () => {
  const [globalDefaultModel, setGlobalDefaultModel] = useState('');
  const [sceneDefaultModels, setSceneDefaultModels] = useState({
    chat: '',
    image: '',
    video: '',
    voice: '',
    translate: '',
    knowledge: '',
    workflow: '',
    tool: '',
    search: '',
    mcp: ''
  });
  const [isSavingDefaultModel, setIsSavingDefaultModel] = useState(false);
  const [models, setModels] = useState([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [error, setError] = useState(null);
  const [globalModelConfig, setGlobalModelConfig] = useState(null);
  const [sceneModelConfigs, setSceneModelConfigs] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [sceneModels, setSceneModels] = useState({
    chat: [],
    translate: []
  });
  const [capabilityScores, setCapabilityScores] = useState({});

  // 加载模型数据和默认配置
  useEffect(() => {
    loadModelsAndConfigs();
  }, []);

  // 验证模型选择
  const validateModelSelection = (modelId, scope, scene) => {
    const errors = {};
    
    if (!modelId) {
      errors[scope] = scope === 'global' 
        ? '请选择全局默认模型' 
        : `请选择${scene}场景的默认模型`;
    }
    
    return errors;
  };

  // 检查是否有未保存的更改
  useEffect(() => {
    const hasChanges = globalDefaultModel !== (globalModelConfig?.model_id?.toString() || '') ||
      Object.keys(sceneDefaultModels).some(scene => 
        sceneDefaultModels[scene] !== (sceneModelConfigs[scene]?.model_id?.toString() || '')
      );
    setHasUnsavedChanges(hasChanges);
  }, [globalDefaultModel, sceneDefaultModels, globalModelConfig, sceneModelConfigs]);

  // 全局模型选择处理
  const handleGlobalModelSelect = (model) => {
    setGlobalDefaultModel(model.id);
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors.global;
      return newErrors;
    });
  };

  // 场景模型选择处理
  const handleSceneModelSelect = (scene) => (model) => {
    setSceneDefaultModels(prev => ({ ...prev, [scene]: model.id }));
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[scene];
      return newErrors;
    });
  };

  // 验证表单
  const validateForm = () => {
    const errors = {};
    
    // 验证全局模型
    if (globalDefaultModel) {
      const globalError = validateModelSelection(globalDefaultModel, 'global');
      Object.assign(errors, globalError);
    }
    
    // 验证场景模型
    Object.entries(sceneDefaultModels).forEach(([scene, modelId]) => {
      if (modelId) {
        const sceneError = validateModelSelection(modelId, 'scene', scene);
        Object.assign(errors, sceneError);
      }
    });
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // 计算模型的能力匹配度
  const calculateCapabilityScore = async (model, scene) => {
    try {
      // 尝试从后端获取真实的能力匹配度
      const response = await supplierApi.getModelCapabilityScores(model.id, scene);
      if (response?.data?.score) {
        return Math.round(response.data.score * 100);
      }
    } catch (error) {
      console.warn(`获取模型 ${model.id} 在场景 ${scene} 的能力分数失败:`, error);
    }
    
    // 如果后端API不可用，使用基于模型参数的简单计算
    const sceneCapabilities = {
      chat: ['chat', 'multi_turn_conversation', 'context_management'],
      translate: ['language_translation', 'multilingual_support', 'translation_quality']
    };
    
    const requiredCapabilities = sceneCapabilities[scene] || [];
    if (requiredCapabilities.length === 0) return 0;
    
    // 基于模型参数的简单匹配度计算
    let baseScore = 0.7; // 基础分数
    
    // 根据模型参数规模调整分数
    if (model.parameters) {
      try {
        const params = parseInt(model.parameters.replace(/[BM]/g, ''));
        if (model.parameters.includes('B')) {
          // 十亿级参数模型
          baseScore += 0.2;
        } else if (model.parameters.includes('M') && params > 100) {
          // 大模型（超过1亿参数）
          baseScore += 0.1;
        }
      } catch (e) {
        // 参数解析失败，使用基础分数
      }
    }
    
    // 根据模型类型调整分数
    if (model.type === scene) {
      baseScore += 0.1;
    }
    
    // 确保分数在合理范围内
    baseScore = Math.min(Math.max(baseScore, 0.5), 0.95);
    return Math.round(baseScore * 100);
  };

  // 获取场景的推荐模型
  const getRecommendedModels = (scene) => {
    const modelsForScene = sceneModels[scene] || [];
    if (modelsForScene.length === 0) return [];
    
    // 根据能力匹配度排序，返回前3个推荐模型
    return modelsForScene
      .map(model => ({
        ...model,
        score: capabilityScores[`${scene}_${model.id}`] || 0
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  };

  // 智能推荐模型
  const recommendModelForScene = (scene) => {
    const recommendedModels = getRecommendedModels(scene);
    if (recommendedModels.length === 0) return null;
    
    // 返回匹配度最高的模型
    return recommendedModels[0];
  };

  // 应用智能推荐
  const applySmartRecommendation = (scene) => {
    const recommendedModel = recommendModelForScene(scene);
    if (recommendedModel && !sceneDefaultModels[scene]) {
      // 如果没有设置默认模型，应用推荐
      handleSceneModelSelect(scene)(recommendedModel);
    }
  };

  // 加载模型列表和默认配置
  const loadModelsAndConfigs = async () => {
    try {
      setIsLoadingModels(true);
      setError(null);

      // 并行获取全局默认模型和场景默认模型
      const [globalConfig, sceneConfigsResponse] = await Promise.all([
        defaultModelApi.getGlobalDefaultModel().catch(() => null),
        defaultModelApi.getDefaultModels({ scope: 'scene' }).catch(() => ({ items: [] }))
      ]);

      setGlobalModelConfig(globalConfig?.data || null);

      // 处理场景默认模型配置
      const sceneConfigs = {};
      if (sceneConfigsResponse?.items) {
        sceneConfigsResponse.items.forEach(config => {
          sceneConfigs[config.scene] = config;
        });
      }
      setSceneModelConfigs(sceneConfigs);

      // 设置全局默认模型ID
      if (globalConfig?.data?.model_id) {
        setGlobalDefaultModel(globalConfig.data.model_id.toString());
      }

      // 设置场景默认模型ID
      const sceneDefaults = {};
      // 遍历所有可能的场景（与初始状态保持一致）
      const allScenes = ['chat', 'image', 'video', 'voice', 'translate', 'knowledge', 'workflow', 'tool', 'search', 'mcp'];
      allScenes.forEach(scene => {
        if (sceneConfigs[scene]?.model_id) {
          sceneDefaults[scene] = sceneConfigs[scene].model_id.toString();
        } else {
          sceneDefaults[scene] = ''; // 确保所有场景都有值
        }
      });
      setSceneDefaultModels(sceneDefaults);

      // 加载所有模型列表
      const allModelsResponse = await supplierApi.getModels().catch(() => []);
      // 处理API返回格式：可能是直接数组或包含items属性的对象
      const allModels = Array.isArray(allModelsResponse) ? allModelsResponse : (allModelsResponse?.items || []);
      setModels(allModels);

      // 为chat和translate场景加载特定模型
      try {
        const [chatModelsResponse, translateModelsResponse] = await Promise.all([
          supplierApi.getModelsByScene('chat').catch((error) => {
            console.error('获取chat场景模型失败:', error);
            return { items: [] };
          }),
          supplierApi.getModelsByScene('translate').catch((error) => {
            console.error('获取translate场景模型失败:', error);
            return { items: [] };
          })
        ]);

        // 调试信息：打印API响应
        console.log('=== 调试信息：场景模型API响应 ===');
        console.log('chat场景模型响应:', chatModelsResponse);
        console.log('translate场景模型响应:', translateModelsResponse);
        console.log('所有模型数量:', allModels.length);
        console.log('所有模型列表:', allModels.map(m => ({ id: m.id, name: m.model_name, type: m.type })));

        // 处理API返回格式：可能是直接数组或包含items属性的对象
        const chatModels = Array.isArray(chatModelsResponse) ? chatModelsResponse : (chatModelsResponse?.items || []);
        const translateModels = Array.isArray(translateModelsResponse) ? translateModelsResponse : (translateModelsResponse?.items || []);

        // 调试信息：打印场景模型数据
        console.log('chat场景模型数量:', chatModels.length);
        console.log('chat场景模型列表:', chatModels.map(m => ({ id: m.id, name: m.model_name, type: m.type })));
        console.log('translate场景模型数量:', translateModels.length);
        console.log('translate场景模型列表:', translateModels.map(m => ({ id: m.id, name: m.model_name, type: m.type })));

        setSceneModels({
          chat: chatModels,
          translate: translateModels
        });

        // 异步计算能力匹配度
        const scores = {};
        
        // 并行计算所有模型的能力匹配度
        const scorePromises = [];
        
        // 计算chat场景的匹配度
        chatModels.forEach(model => {
          scorePromises.push(
            calculateCapabilityScore(model, 'chat').then(score => {
              scores[`chat_${model.id}`] = score;
            })
          );
        });
        
        // 计算translate场景的匹配度
        translateModels.forEach(model => {
          scorePromises.push(
            calculateCapabilityScore(model, 'translate').then(score => {
              scores[`translate_${model.id}`] = score;
            })
          );
        });
        
        // 等待所有分数计算完成
        await Promise.all(scorePromises);
        setCapabilityScores(scores);
      } catch (error) {
        console.warn('获取场景特定模型失败，使用默认模型列表:', error);
        // 如果API调用失败，使用默认模型列表
        setSceneModels({
          chat: allModels.filter(model => model.type === 'chat'),
          translate: allModels.filter(model => model.type === 'translate')
        });
      }

    } catch (err) {
      console.error('加载默认模型配置失败:', err);
      setError('加载默认模型配置失败，请重试');
    } finally {
      setIsLoadingModels(false);
    }
  };

  // 保存默认模型设置
  const handleSaveDefaultModel = async () => {
    try {
      // 验证表单
      if (!validateForm()) {
        return;
      }

      setIsSavingDefaultModel(true);
      setError(null);

      // 并行保存全局默认模型和所有场景默认模型
      const savePromises = [];

      // 保存全局默认模型（如果有选择）
      if (globalDefaultModel) {
        savePromises.push(
          defaultModelApi.setGlobalDefaultModel({
            model_id: parseInt(globalDefaultModel)
          })
        );
      }

      // 保存场景默认模型
      Object.entries(sceneDefaultModels).forEach(([scene, modelId]) => {
        if (modelId) {
          savePromises.push(
            defaultModelApi.setSceneDefaultModel({
              scene,
              model_id: parseInt(modelId),
              priority: 1
            })
          );
        }
      });

      // 等待所有保存操作完成
      await Promise.all(savePromises);

      // 重新加载配置以确保UI同步
      await loadModelsAndConfigs();

      // 显示成功消息
      alert('默认模型设置已保存');

    } catch (err) {
      console.error('保存默认模型设置失败:', err);
      setError('保存默认模型设置失败，请重试');
    } finally {
      setIsSavingDefaultModel(false);
    }
  };

  // 根据场景类型过滤模型
  const getModelsByType = (type) => {
    return models.filter(model => model.type === type || model.type === 'chat');
  };

  return (
    <div className="default-model-management">
      
      {/* 调试信息面板 */}
      <div className="debug-panel" style={{ 
        background: '#f5f5f5', 
        border: '1px solid #ddd', 
        padding: '10px', 
        marginBottom: '20px',
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        <h4 style={{ margin: '0 0 10px 0', color: '#666' }}>调试信息</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <div>
            <strong>数据状态:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: '15px' }}>
              <li>所有模型数量: {models.length}</li>
              <li>chat场景模型: {sceneModels.chat.length}</li>
              <li>translate场景模型: {sceneModels.translate.length}</li>
              <li>加载状态: {isLoadingModels ? '加载中...' : '完成'}</li>
            </ul>
          </div>
          <div>
            <strong>API端点:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: '15px' }}>
              <li>/api/v1/models: {models.length > 0 ? '✅ 有数据' : '❌ 无数据'}</li>
              <li>/api/v1/models/by-scene/chat: {sceneModels.chat.length > 0 ? '✅ 有数据' : '❌ 无数据'}</li>
              <li>/api/v1/models/by-scene/translate: {sceneModels.translate.length > 0 ? '✅ 有数据' : '❌ 无数据'}</li>
            </ul>
          </div>
        </div>
        <div>
          <strong>问题分析:</strong>
          <p style={{ margin: '5px 0', fontSize: '11px', color: '#d63384' }}>
            {sceneModels.chat.length === 0 && sceneModels.translate.length === 0 
              ? '⚠️ 场景模型为空：可能原因 - 1. 数据库能力关联数据不足 2. 能力强度要求过高 3. API路径错误' 
              : '✅ 数据正常'}
          </p>
        </div>
      </div>
      
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
            onModelSelect={handleGlobalModelSelect}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              // 根据供应商返回不同的LOGO URL
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.global && (
            <span className="field-error">{validationErrors.global}</span>
          )}
        </div>
      </div>
      
      {/* 场景默认模型 */}
      <div className="setting-card">
        <div className="setting-header">
          <h4>场景默认模型</h4>
          <p>为特定业务场景设置专属默认模型</p>
        </div>
        
        {/* 聊天场景 */}
        <div className="setting-item">
          <div className="scene-header">
            <div className="scene-title">
              <label htmlFor="chatModel">聊天场景</label>
              <button 
                className="recommend-btn"
                onClick={() => applySmartRecommendation('chat')}
                disabled={isLoadingModels || sceneModels.chat.length === 0}
                title="应用智能推荐"
              >
                💡 智能推荐
              </button>
            </div>
            <span className="scene-description">对话、多轮对话、上下文管理</span>
          </div>
          <ModelSelectDropdown
            models={sceneModels.chat.length > 0 ? sceneModels.chat : getModelsByType('chat')}
            selectedModel={(sceneModels.chat.length > 0 ? sceneModels.chat : getModelsByType('chat')).find(model => model.id === sceneDefaultModels.chat) || null}
            onModelSelect={handleSceneModelSelect('chat')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
            getModelBadge={(model) => {
              const score = capabilityScores[`chat_${model.id}`];
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
          {validationErrors.chat && (
            <span className="field-error">{validationErrors.chat}</span>
          )}
          <div className="capability-info">
            <span className="info-text">基于对话、多轮对话、上下文管理能力进行匹配</span>
            {getRecommendedModels('chat').length > 0 && (
              <div className="recommendation-list">
                <span className="recommendation-title">推荐模型：</span>
                {getRecommendedModels('chat').map((model, index) => (
                  <span key={model.id} className="recommendation-item">
                    {index + 1}. {model.model_name || model.name} ({model.score}%)
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* 图像场景 */}
        <div className="setting-item">
          <label htmlFor="imageModel">图像场景</label>
          <ModelSelectDropdown
            models={getModelsByType('image')}
            selectedModel={getModelsByType('image').find(model => model.id === sceneDefaultModels.image) || null}
            onModelSelect={handleSceneModelSelect('image')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.image && (
            <span className="field-error">{validationErrors.image}</span>
          )}
        </div>
        
        {/* 视频场景 */}
        <div className="setting-item">
          <label htmlFor="videoModel">视频场景</label>
          <ModelSelectDropdown
            models={getModelsByType('video')}
            selectedModel={getModelsByType('video').find(model => model.id === sceneDefaultModels.video) || null}
            onModelSelect={handleSceneModelSelect('video')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.video && (
            <span className="field-error">{validationErrors.video}</span>
          )}
        </div>
        
        {/* 语音场景 */}
        <div className="setting-item">
          <label htmlFor="voiceModel">语音场景</label>
          <ModelSelectDropdown
            models={getModelsByType('voice')}
            selectedModel={getModelsByType('voice').find(model => model.id === sceneDefaultModels.voice) || null}
            onModelSelect={handleSceneModelSelect('voice')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.voice && (
            <span className="field-error">{validationErrors.voice}</span>
          )}
        </div>
        
        {/* 翻译场景 */}
        <div className="setting-item">
          <div className="scene-header">
            <div className="scene-title">
              <label htmlFor="translateModel">翻译场景</label>
              <button 
                className="recommend-btn"
                onClick={() => applySmartRecommendation('translate')}
                disabled={isLoadingModels || sceneModels.translate.length === 0}
                title="应用智能推荐"
              >
                💡 智能推荐
              </button>
            </div>
            <span className="scene-description">语言翻译、多语言支持、翻译质量</span>
          </div>
          <ModelSelectDropdown
            models={sceneModels.translate.length > 0 ? sceneModels.translate : getModelsByType('translate')}
            selectedModel={(sceneModels.translate.length > 0 ? sceneModels.translate : getModelsByType('translate')).find(model => model.id === sceneDefaultModels.translate) || null}
            onModelSelect={handleSceneModelSelect('translate')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
            getModelBadge={(model) => {
              const score = capabilityScores[`translate_${model.id}`];
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
          {validationErrors.translate && (
            <span className="field-error">{validationErrors.translate}</span>
          )}
          <div className="capability-info">
            <span className="info-text">基于语言翻译、多语言支持、翻译质量能力进行匹配</span>
            {getRecommendedModels('translate').length > 0 && (
              <div className="recommendation-list">
                <span className="recommendation-title">推荐模型：</span>
                {getRecommendedModels('translate').map((model, index) => (
                  <span key={model.id} className="recommendation-item">
                    {index + 1}. {model.model_name || model.name} ({model.score}%)
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* 知识库场景 */}
        <div className="setting-item">
          <label htmlFor="knowledgeModel">知识库场景</label>
          <ModelSelectDropdown
            models={getModelsByType('knowledge')}
            selectedModel={getModelsByType('knowledge').find(model => model.id === sceneDefaultModels.knowledge) || null}
            onModelSelect={handleSceneModelSelect('knowledge')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.knowledge && (
            <span className="field-error">{validationErrors.knowledge}</span>
          )}
        </div>
        
        {/* 工作流场景 */}
        <div className="setting-item">
          <label htmlFor="workflowModel">工作流场景</label>
          <ModelSelectDropdown
            models={getModelsByType('workflow')}
            selectedModel={getModelsByType('workflow').find(model => model.id === sceneDefaultModels.workflow) || null}
            onModelSelect={handleSceneModelSelect('workflow')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.workflow && (
            <span className="field-error">{validationErrors.workflow}</span>
          )}
        </div>
        
        {/* 工具调用场景 */}
        <div className="setting-item">
          <label htmlFor="toolModel">工具调用场景</label>
          <ModelSelectDropdown
            models={getModelsByType('tool')}
            selectedModel={getModelsByType('tool').find(model => model.id === sceneDefaultModels.tool) || null}
            onModelSelect={handleSceneModelSelect('tool')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.tool && (
            <span className="field-error">{validationErrors.tool}</span>
          )}
        </div>
        
        {/* 搜索场景 */}
        <div className="setting-item">
          <label htmlFor="searchModel">搜索场景</label>
          <ModelSelectDropdown
            models={getModelsByType('search')}
            selectedModel={getModelsByType('search').find(model => model.id === sceneDefaultModels.search) || null}
            onModelSelect={handleSceneModelSelect('search')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.search && (
            <span className="field-error">{validationErrors.search}</span>
          )}
        </div>
        
        {/* MCP场景 */}
        <div className="setting-item">
          <label htmlFor="mcpModel">MCP场景</label>
          <ModelSelectDropdown
            models={getModelsByType('mcp')}
            selectedModel={getModelsByType('mcp').find(model => model.id === sceneDefaultModels.mcp) || null}
            onModelSelect={handleSceneModelSelect('mcp')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              const supplier = model.supplier;
              // 优先使用供应商LOGO文件名，如果没有则使用供应商名称
              const logoFileName = supplier?.logo || supplier?.name || supplier?.display_name || supplier?.id || 'default';
              return `/logos/providers/${logoFileName}`;
            }}
          />
          {validationErrors.mcp && (
            <span className="field-error">{validationErrors.mcp}</span>
          )}
        </div>
        
        <div className="setting-actions">
          <button 
            className="save-btn" 
            onClick={handleSaveDefaultModel}
            disabled={isSavingDefaultModel || isLoadingModels || Object.keys(validationErrors).length > 0}
          >
            {isSavingDefaultModel ? '保存中...' : '保存设置'}
          </button>
          
          {hasUnsavedChanges && (
            <span className="unsaved-changes-indicator">
              有未保存的更改
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default DefaultModelManagement;