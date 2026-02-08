import { useState, useEffect, useCallback } from 'react';
import { defaultModelApi, supplierApi, capabilityApi } from '../../../utils/api';

/**
 * 模型管理自定义钩子
 * 处理模型数据加载、保存和管理逻辑
 */
const useModelManagement = () => {
  // 状态管理
  const [globalDefaultModel, setGlobalDefaultModel] = useState(null);
  const [sceneDefaultModels, setSceneDefaultModels] = useState({
    chat: null,
    image: null,
    video: null,
    voice: null,
    translate: null,
    knowledge: null,
    workflow: null,
    tool: null,
    search: null,
    mcp: null,
    topic_title: null
  });
  const [isSavingDefaultModel, setIsSavingDefaultModel] = useState(false);
  const [models, setModels] = useState([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [error, setError] = useState(null);
  const [globalModelConfig, setGlobalModelConfig] = useState(null);
  const [sceneModelConfigs, setSceneModelConfigs] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [sceneModels, setSceneModels] = useState({});
  const [capabilityScores, setCapabilityScores] = useState({});
  const [localModels, setLocalModels] = useState([]);
  const [isLoadingLocalModels, setIsLoadingLocalModels] = useState(false);
  const [localModelConfig, setLocalModelConfig] = useState(null);

  // 验证模型选择
  const validateModelSelection = useCallback((modelId, scope, scene) => {
    const errors = {};
    
    if (!modelId) {
      errors[scope] = scope === 'global' 
        ? '请选择全局默认模型' 
        : `请选择${scene}场景的默认模型`;
    }
    
    return errors;
  }, []);

  // 检查是否有未保存的更改
  useEffect(() => {
    const hasChanges = globalDefaultModel !== globalModelConfig?.model_id ||
      Object.keys(sceneDefaultModels).some(scene => 
        sceneDefaultModels[scene] !== sceneModelConfigs[scene]?.model_id
      );
    setHasUnsavedChanges(hasChanges);
  }, [globalDefaultModel, sceneDefaultModels, globalModelConfig, sceneModelConfigs]);

  // 全局模型选择处理
  const handleGlobalModelSelect = useCallback((model) => {
    setGlobalDefaultModel(model.id);
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors.global;
      return newErrors;
    });
  }, []);

  // 场景模型选择处理
  const handleSceneModelSelect = useCallback((scene) => (model) => {
    setSceneDefaultModels(prev => ({ ...prev, [scene]: model.id }));
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[scene];
      return newErrors;
    });
  }, []);

  // 验证表单
  const validateForm = useCallback(() => {
    const errors = {};
    
    // 验证全局模型
    if (!globalDefaultModel) {
      const globalError = validateModelSelection(null, 'global');
      Object.assign(errors, globalError);
    }
    
    // 验证场景模型
    Object.entries(sceneDefaultModels).forEach(([scene, modelId]) => {
      if (!modelId) {
        const sceneError = validateModelSelection(null, 'scene', scene);
        Object.assign(errors, sceneError);
      }
    });
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [globalDefaultModel, sceneDefaultModels, validateModelSelection]);

  // 计算模型的能力匹配度
  const calculateCapabilityScore = useCallback(async (model, scene) => {
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
      translate: ['language_translation', 'multilingual_support', 'translation_quality'],
      image: ['image_generation', 'image_recognition', 'visual_understanding'],
      video: ['video_analysis', 'video_generation', 'video_understanding'],
      voice: ['speech_recognition', 'text_to_speech', 'voice_analysis'],
      knowledge: ['knowledge_retrieval', 'information_synthesis', 'context_awareness'],
      workflow: ['task_planning', 'step_coordination', 'process_optimization'],
      tool: ['tool_calling', 'api_integration', 'function_execution'],
      search: ['information_retrieval', 'relevance_ranking', 'semantic_search'],
      mcp: ['multi_modal_processing', 'cross_media_understanding', 'unified_representation'],
      topic_title: ['text_summarization', 'keyword_extraction']
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
  }, []);

  // 获取场景的推荐模型
  const getRecommendedModels = useCallback((scene) => {
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
  }, [sceneModels, capabilityScores]);

  // 智能推荐模型
  const recommendModelForScene = useCallback((scene) => {
    const recommendedModels = getRecommendedModels(scene);
    if (recommendedModels.length === 0) return null;
    
    // 返回匹配度最高的模型
    return recommendedModels[0];
  }, [getRecommendedModels]);

  // 应用智能推荐
  const applySmartRecommendation = useCallback((scene) => {
    const recommendedModel = recommendModelForScene(scene);
    if (recommendedModel && !sceneDefaultModels[scene]) {
      // 如果没有设置默认模型，应用推荐
      handleSceneModelSelect(scene)(recommendedModel);
    }
  }, [recommendModelForScene, sceneDefaultModels, handleSceneModelSelect]);

  // 加载本地模型列表
  const loadLocalModels = useCallback(async () => {
    try {
      setIsLoadingLocalModels(true);
      
      // 从后端获取本地模型列表
      const localModelsResponse = await supplierApi.getLocalModels().catch((error) => {
        console.error('获取本地模型失败:', error);
        return { items: [] };
      });
      
      // 处理API返回格式
      const localModelsList = Array.isArray(localModelsResponse) ? localModelsResponse : (localModelsResponse?.items || []);
      // 直接使用后端返回的本地模型列表（后端已根据供应商的is_local字段筛选）
      setLocalModels(localModelsList);
      
      // 获取本地模型配置
      const localConfigResponse = await defaultModelApi.getLocalModelConfig().catch(() => null);
      setLocalModelConfig(localConfigResponse || null);
      
    } catch (error) {
      console.error('加载本地模型失败:', error);
      setError('加载本地模型失败，请重试');
    } finally {
      setIsLoadingLocalModels(false);
    }
  }, []);

  // 加载模型列表和默认配置
  const loadModelsAndConfigs = useCallback(async () => {
    try {
      setIsLoadingModels(true);
      setError(null);

      // 并行获取全局默认模型和场景默认模型
      const [globalConfig, sceneConfigsResponse] = await Promise.all([
        defaultModelApi.getGlobalDefaultModel().catch(() => null),
        defaultModelApi.getDefaultModels({ scope: 'scene' }).catch(() => ({ items: [] }))
      ]);

      setGlobalModelConfig(globalConfig || null);

      // 处理场景默认模型配置
      const sceneConfigs = {};
      if (sceneConfigsResponse?.items) {
        sceneConfigsResponse.items.forEach(config => {
          sceneConfigs[config.scene] = config;
        });
      }
      setSceneModelConfigs(sceneConfigs);

      // 设置全局默认模型ID（保持为整数类型，与模型列表中的id类型一致）
      if (globalConfig?.model_id) {
        setGlobalDefaultModel(globalConfig.model_id);
      }

      // 设置场景默认模型ID（保持为整数类型，与模型列表中的id类型一致）
      const sceneDefaults = {};
      // 遍历所有可能的场景（与初始状态保持一致）
      const allScenes = ['chat', 'image', 'video', 'voice', 'translate', 'knowledge', 'workflow', 'tool', 'search', 'mcp', 'topic_title'];
      allScenes.forEach(scene => {
        if (sceneConfigs[scene]?.model_id) {
          sceneDefaults[scene] = sceneConfigs[scene].model_id;
        } else {
          sceneDefaults[scene] = null; // 确保所有场景都有值
        }
      });
      setSceneDefaultModels(sceneDefaults);

      // 加载所有模型列表
      const allModelsResponse = await supplierApi.getModels().catch(() => []);
      // 处理API返回格式：可能是直接数组或包含items属性的对象
      const allModels = Array.isArray(allModelsResponse) ? allModelsResponse : (allModelsResponse?.items || []);
      setModels(allModels);

      // 为所有场景加载特定模型
      try {
        const scenePromises = allScenes.map(scene => 
          supplierApi.getModelsByScene(scene).catch((error) => {
            console.error(`获取${scene}场景模型失败:`, error);
            return { items: [] };
          })
        );
        
        const sceneResponses = await Promise.all(scenePromises);
        
        // 处理所有场景的模型数据
        const sceneModelsData = {};
        
        // 初始化所有场景为空数组
        allScenes.forEach(scene => {
          sceneModelsData[scene] = [];
        });
        
        for (let i = 0; i < allScenes.length; i++) {
          const scene = allScenes[i];
          const response = sceneResponses[i];
          
          // 直接使用后端API返回的模型列表（后端已经根据场景能力进行了筛选）
          const modelsForScene = Array.isArray(response) ? response : (response?.models || response?.items || []);
          sceneModelsData[scene] = modelsForScene;
        }
        
        setSceneModels(sceneModelsData);

        // 异步计算所有场景的能力匹配度
        const scores = {};
        const scorePromises = [];
        
        // 为每个场景计算模型能力匹配度
        allScenes.forEach(scene => {
          const modelsForScene = sceneModelsData[scene];
          modelsForScene.forEach(model => {
            scorePromises.push(
              calculateCapabilityScore(model, scene).then(score => {
                scores[`${scene}_${model.id}`] = score;
              })
            );
          });
        });
        
        // 等待所有分数计算完成
        await Promise.all(scorePromises);
        setCapabilityScores(scores);
      } catch (error) {
        console.warn('获取场景特定模型失败，使用默认模型列表:', error);
        // 如果API调用失败，使用默认模型列表
        const defaultSceneModels = {};
        
        // 初始化所有场景为空数组
        allScenes.forEach(scene => {
          defaultSceneModels[scene] = [];
        });
        
        // 为每个场景生成模型列表
        for (const scene of allScenes) {
          // 使用原有的筛选逻辑
          defaultSceneModels[scene] = allModels.filter(model => model.type === scene || model.type === 'chat');
        }
        
        setSceneModels(defaultSceneModels);
        
        // 计算默认模型的能力匹配度
        const scores = {};
        const scorePromises = [];
        
        allScenes.forEach(scene => {
          const modelsForScene = defaultSceneModels[scene];
          modelsForScene.forEach(model => {
            scorePromises.push(
              calculateCapabilityScore(model, scene).then(score => {
                scores[`${scene}_${model.id}`] = score;
              })
            );
          });
        });
        
        await Promise.all(scorePromises);
        setCapabilityScores(scores);
      }

      // 加载本地模型
      await loadLocalModels();

    } catch (err) {
      console.error('加载默认模型配置失败:', err);
      setError('加载默认模型配置失败，请重试');
    } finally {
      setIsLoadingModels(false);
    }
  }, [calculateCapabilityScore, loadLocalModels]);

  // 保存本地模型配置
  const handleSaveLocalModelConfig = useCallback(async (localModelId) => {
    try {
      setIsSavingDefaultModel(true);
      setError(null);

      // 保存本地模型配置
      await defaultModelApi.setLocalModelConfig({
        model_id: localModelId,
        enabled: true
      });

      // 重新加载配置以确保UI同步
      await loadModelsAndConfigs();

      // 显示成功消息
      alert('本地模型配置已保存');

    } catch (err) {
      console.error('保存本地模型配置失败:', err);
      setError('保存本地模型配置失败，请重试');
    } finally {
      setIsSavingDefaultModel(false);
    }
  }, [loadModelsAndConfigs]);

  // 保存默认模型设置
  const handleSaveDefaultModel = useCallback(async () => {
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
            model_id: globalDefaultModel
          })
        );
      }

      // 保存场景默认模型
      Object.entries(sceneDefaultModels).forEach(([scene, modelId]) => {
        if (modelId) {
          savePromises.push(
            defaultModelApi.setSceneDefaultModel({
              scene,
              model_id: modelId,
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
  }, [globalDefaultModel, sceneDefaultModels, validateForm, loadModelsAndConfigs]);

  // 初始化加载
  useEffect(() => {
    loadModelsAndConfigs();
  }, [loadModelsAndConfigs]);

  return {
    // 状态
    globalDefaultModel,
    sceneDefaultModels,
    isSavingDefaultModel,
    models,
    isLoadingModels,
    error,
    globalModelConfig,
    sceneModelConfigs,
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
  };
};

export default useModelManagement;