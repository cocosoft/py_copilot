import React, { useState, useEffect } from 'react';
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

  // 模拟模型数据
  useEffect(() => {
    setIsLoadingModels(true);
    // 模拟从API获取模型列表
    setTimeout(() => {
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
      setIsLoadingModels(false);
    }, 500);
  }, []);

  // 保存默认模型设置
  const handleSaveDefaultModel = () => {
    setIsSavingDefaultModel(true);
    // 模拟保存操作
    setTimeout(() => {
      alert('默认模型设置已保存');
      setIsSavingDefaultModel(false);
    }, 800);
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
            onModelSelect={(model) => setGlobalDefaultModel(model.id)}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => {
              // 根据供应商返回不同的LOGO URL
              return `/logos/providers/${model.supplier || 'default'}.png`;
            }}
          />
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
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, chat: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* 图像场景 */}
        <div className="setting-item">
          <label htmlFor="imageModel">图像场景</label>
          <ModelSelectDropdown
            models={getModelsByType('image')}
            selectedModel={getModelsByType('image').find(model => model.id === sceneDefaultModels.image) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, image: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* 视频场景 */}
        <div className="setting-item">
          <label htmlFor="videoModel">视频场景</label>
          <ModelSelectDropdown
            models={getModelsByType('video')}
            selectedModel={getModelsByType('video').find(model => model.id === sceneDefaultModels.video) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, video: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* 语音场景 */}
        <div className="setting-item">
          <label htmlFor="voiceModel">语音场景</label>
          <ModelSelectDropdown
            models={getModelsByType('voice')}
            selectedModel={getModelsByType('voice').find(model => model.id === sceneDefaultModels.voice) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, voice: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* 翻译场景 */}
        <div className="setting-item">
          <label htmlFor="translateModel">翻译场景</label>
          <ModelSelectDropdown
            models={getModelsByType('translate')}
            selectedModel={getModelsByType('translate').find(model => model.id === sceneDefaultModels.translate) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, translate: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* 知识库场景 */}
        <div className="setting-item">
          <label htmlFor="knowledgeModel">知识库场景</label>
          <ModelSelectDropdown
            models={getModelsByType('knowledge')}
            selectedModel={getModelsByType('knowledge').find(model => model.id === sceneDefaultModels.knowledge) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, knowledge: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* 工作流场景 */}
        <div className="setting-item">
          <label htmlFor="workflowModel">工作流场景</label>
          <ModelSelectDropdown
            models={getModelsByType('workflow')}
            selectedModel={getModelsByType('workflow').find(model => model.id === sceneDefaultModels.workflow) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, workflow: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* 工具调用场景 */}
        <div className="setting-item">
          <label htmlFor="toolModel">工具调用场景</label>
          <ModelSelectDropdown
            models={getModelsByType('tool')}
            selectedModel={getModelsByType('tool').find(model => model.id === sceneDefaultModels.tool) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, tool: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* 搜索场景 */}
        <div className="setting-item">
          <label htmlFor="searchModel">搜索场景</label>
          <ModelSelectDropdown
            models={getModelsByType('search')}
            selectedModel={getModelsByType('search').find(model => model.id === sceneDefaultModels.search) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, search: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        {/* MCP场景 */}
        <div className="setting-item">
          <label htmlFor="mcpModel">MCP场景</label>
          <ModelSelectDropdown
            models={getModelsByType('mcp')}
            selectedModel={getModelsByType('mcp').find(model => model.id === sceneDefaultModels.mcp) || null}
            onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, mcp: model.id }))}
            placeholder="请选择模型"
            disabled={isLoadingModels}
            getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
          />
        </div>
        
        <div className="setting-actions">
          <button 
            className="save-btn" 
            onClick={handleSaveDefaultModel}
            disabled={isSavingDefaultModel || isLoadingModels}
          >
            {isSavingDefaultModel ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DefaultModelManagement;