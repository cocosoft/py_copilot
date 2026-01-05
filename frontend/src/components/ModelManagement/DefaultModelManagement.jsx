import { useState, useEffect } from 'react';
import { defaultModelApi } from '../../utils/api';
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
      Object.keys(sceneDefaultModels).forEach(scene => {
        if (sceneConfigs[scene]?.model_id) {
          sceneDefaults[scene] = sceneConfigs[scene].model_id.toString();
        }
      });
      setSceneDefaultModels(prev => ({ ...prev, ...sceneDefaults }));

      // 加载模型列表（这里需要根据实际的模型API进行调整）
      // 目前使用模拟数据，后续需要集成真实的模型API
      const mockModels = [
        { id: 'model-123', name: '通用聊天模型', supplier: 'openai', type: 'chat' },
        { id: 'model-456', name: '高级推理模型', supplier: 'anthropic', type: 'chat' },
        { id: 'model-789', name: '图像生成模型', supplier: 'openai', type: 'image' },
        { id: 'model-101', name: '视频分析模型', supplier: 'google', type: 'video' },
        { id: 'model-102', name: '语音识别模型', supplier: 'baidu', type: 'voice' },
        { id: 'model-103', name: '多语言翻译模型', supplier: 'microsoft', type: 'translate' },
        { id: 'model-104', name: '知识库模型', supplier: 'openai', type: 'knowledge' },
        { id: 'model-105', name: '工作流模型', supplier: 'anthropic', type: 'workflow' },
        { id: 'model-106', name: '工具调用模型', supplier: 'openai', type: 'tool' },
        { id: 'model-107', name: '搜索增强模型', supplier: 'google', type: 'search' },
        { id: 'model-108', name: 'MCP上下文模型', supplier: 'openai', type: 'mcp' }
      ];
      setModels(mockModels);

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
      <div className="content-header">
        <h3>默认模型</h3>
        <p>设置系统默认使用的AI模型</p>
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
              return `/logos/providers/${model.supplier || 'default'}.png`;
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
          <label htmlFor="chatModel">聊天场景</label>
          <ModelSelectDropdown
            models={getModelsByType('chat')}
            selectedModel={getModelsByType('chat').find(model => model.id === sceneDefaultModels.chat) || null}
            onModelSelect={handleSceneModelSelect('chat')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
          {validationErrors.chat && (
            <span className="field-error">{validationErrors.chat}</span>
          )}
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
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
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
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
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
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
          {validationErrors.voice && (
            <span className="field-error">{validationErrors.voice}</span>
          )}
        </div>
        
        {/* 翻译场景 */}
        <div className="setting-item">
          <label htmlFor="translateModel">翻译场景</label>
          <ModelSelectDropdown
            models={getModelsByType('translate')}
            selectedModel={getModelsByType('translate').find(model => model.id === sceneDefaultModels.translate) || null}
            onModelSelect={handleSceneModelSelect('translate')}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
          {validationErrors.translate && (
            <span className="field-error">{validationErrors.translate}</span>
          )}
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
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
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
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
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
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
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
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
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
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
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