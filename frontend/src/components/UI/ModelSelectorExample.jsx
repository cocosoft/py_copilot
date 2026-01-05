import React, { useState } from 'react';
import { ModelSelector, Card, Badge, Icon } from './index';

/**
 * 模型选择器使用示例
 * 展示各种配置选项和使用场景
 */
const ModelSelectorExample = () => {
  // 示例数据
  const [models] = useState([
    {
      id: 1,
      name: 'GPT-4',
      model_name: 'GPT-4',
      model_id: 'gpt-4',
      supplier: { display_name: 'OpenAI', logo: 'openai-logo.png' },
      description: '最先进的大语言模型，具备强大的理解和生成能力',
      category: '文本生成',
      model_type: 'LLM',
      version: '4.0',
      max_tokens: 8192,
      is_default: true
    },
    {
      id: 2,
      name: 'Claude-3',
      model_name: 'Claude-3 Opus',
      model_id: 'claude-3-opus',
      supplier: { display_name: 'Anthropic', logo: 'anthropic-logo.png' },
      description: 'Anthropic开发的强大AI助手，擅长分析和推理',
      category: '文本生成',
      model_type: 'LLM',
      version: '3.0',
      max_tokens: 100000
    },
    {
      id: 3,
      name: 'DALL-E 3',
      model_name: 'DALL-E 3',
      model_id: 'dalle-3',
      supplier: { display_name: 'OpenAI', logo: 'openai-logo.png' },
      description: '最新的图像生成模型，能够创建高质量的图像',
      category: '图像生成',
      model_type: '图像生成',
      version: '3.0',
      max_tokens: 4000
    },
    {
      id: 4,
      name: 'Whisper',
      model_name: 'Whisper',
      model_id: 'whisper-1',
      supplier: { display_name: 'OpenAI', logo: 'openai-logo.png' },
      description: '强大的语音识别模型，支持多种语言',
      category: '语音识别',
      model_type: '语音',
      version: '1.0',
      max_tokens: null
    },
    {
      id: 5,
      name: 'Gemini Pro',
      model_name: 'Gemini Pro',
      model_id: 'gemini-pro',
      supplier: { display_name: 'Google', logo: 'google-logo.png' },
      description: 'Google开发的多模态AI模型',
      category: '多模态',
      model_type: '多模态',
      version: '1.0',
      max_tokens: 32768
    }
  ]);

  // 状态管理
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedModels, setSelectedModels] = useState([]);
  const [favorites, setFavorites] = useState(new Set([1, 3])); // 预置一些收藏

  // 处理函数
  const handleSingleSelection = (models) => {
    setSelectedModel(models[0] || null);
    console.log('单选模式 - 选中的模型:', models[0]);
  };

  const handleMultipleSelection = (models) => {
    setSelectedModels(models);
    console.log('多选模式 - 选中的模型:', models);
  };

  const handleModelPreview = (model) => {
    console.log('预览模型:', model);
    // 这里可以打开详细的模型信息模态框
  };

  const handleModelFavorite = (modelId, isFavorite) => {
    console.log(`模型 ${modelId} ${isFavorite ? '已收藏' : '取消收藏'}`);
    // 这里可以同步到后端
  };

  const handleCreateNew = () => {
    console.log('创建新模型');
    // 这里可以打开创建模型的表单
  };

  // 自定义过滤函数
  const customFilter = (model) => {
    // 只显示支持多模态的模型
    return model.model_type === '多模态';
  };

  return (
    <div className="model-selector-example p-8 space-y-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">模型选择器组件示例</h1>

        {/* 1. 单选模式 */}
        <Card className="p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Icon name="settings" size={20} />
            单选模式
          </h2>
          <p className="text-gray-600 mb-4">
            最基本的用法，选择一个模型。适用于需要指定特定模型的场景。
          </p>
          
          <div className="space-y-4">
            <ModelSelector
              models={models}
              selectedModels={selectedModel ? [selectedModel] : []}
              onSelectionChange={handleSingleSelection}
              mode="single"
              placeholder="请选择一个AI模型..."
              showSearch={true}
              showCategoryFilter={true}
              showSupplierFilter={true}
              showPreview={true}
              enableFavorites={true}
              enableKeyboard={true}
              size="medium"
              showCreateButton={true}
              onCreateNew={handleCreateNew}
              onModelPreview={handleModelPreview}
              onModelFavorite={handleModelFavorite}
            />
            
            {selectedModel && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">当前选择:</h4>
                <div className="flex items-center gap-3">
                  <img 
                    src={selectedModel.supplier?.logo ? `/logos/providers/${selectedModel.supplier.logo}` : '/logos/models/default.png'} 
                    alt={selectedModel.model_name}
                    className="w-8 h-8 rounded object-cover"
                  />
                  <div>
                    <p className="font-medium text-blue-900">{selectedModel.model_name}</p>
                    <p className="text-sm text-blue-700">{selectedModel.supplier?.display_name}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* 2. 多选模式 */}
        <Card className="p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Icon name="list" size={20} />
            多选模式
          </h2>
          <p className="text-gray-600 mb-4">
            可以选择多个模型。适用于需要比较多个模型或批量操作的场景。
          </p>
          
          <div className="space-y-4">
            <ModelSelector
              models={models}
              selectedModels={selectedModels}
              onSelectionChange={handleMultipleSelection}
              mode="multiple"
              placeholder="选择多个模型进行比较..."
              showSearch={true}
              showCategoryFilter={true}
              showSupplierFilter={true}
              showPreview={true}
              enableFavorites={true}
              enableKeyboard={true}
              size="medium"
              maxHeight="300px"
              showCreateButton={false}
            />
            
            {selectedModels.length > 0 && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">
                  已选择 {selectedModels.length} 个模型:
                </h4>
                <div className="flex flex-wrap gap-2">
                  {selectedModels.map(model => (
                    <Badge 
                      key={model.id} 
                      variant="success" 
                      className="flex items-center gap-1"
                    >
                      {model.model_name}
                      <button 
                        onClick={() => handleMultipleSelection(selectedModels.filter(m => m.id !== model.id))}
                        className="ml-1 hover:text-red-600"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* 3. 小尺寸版本 */}
        <Card className="p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Icon name="minus" size={20} />
            小尺寸版本
          </h2>
          <p className="text-gray-600 mb-4">
            紧凑的版本，适用于空间有限的地方，如表单字段或工具栏。
          </p>
          
          <div className="space-y-4">
            <ModelSelector
              models={models}
              selectedModels={selectedModel ? [selectedModel] : []}
              onSelectionChange={handleSingleSelection}
              mode="single"
              placeholder="快速选择..."
              size="small"
              showSearch={false}
              showCategoryFilter={false}
              showSupplierFilter={false}
              showPreview={false}
              enableFavorites={false}
              enableKeyboard={false}
              className="w-64"
            />
          </div>
        </Card>

        {/* 4. 大尺寸版本 */}
        <Card className="p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Icon name="plus" size={20} />
            大尺寸版本
          </h2>
          <p className="text-gray-600 mb-4">
            更大的版本，提供更好的用户体验和更多的显示空间。
          </p>
          
          <div className="space-y-4">
            <ModelSelector
              models={models}
              selectedModels={selectedModel ? [selectedModel] : []}
              onSelectionChange={handleSingleSelection}
              mode="single"
              placeholder="详细选择..."
              size="large"
              showSearch={true}
              showCategoryFilter={true}
              showSupplierFilter={true}
              showPreview={true}
              enableFavorites={true}
              enableKeyboard={true}
              maxHeight="500px"
            />
          </div>
        </Card>

        {/* 5. 自定义过滤 */}
        <Card className="p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Icon name="filter" size={20} />
            自定义过滤
          </h2>
          <p className="text-gray-600 mb-4">
            只显示多模态模型的应用场景。
          </p>
          
          <div className="space-y-4">
            <ModelSelector
              models={models}
              selectedModels={[]}
              onSelectionChange={(models) => console.log('过滤后的选择:', models)}
              mode="single"
              placeholder="仅显示多模态模型..."
              showSearch={true}
              showCategoryFilter={false}
              showSupplierFilter={false}
              showPreview={true}
              enableFavorites={true}
              enableKeyboard={true}
              customFilter={customFilter}
            />
          </div>
        </Card>

        {/* 6. 禁用状态 */}
        <Card className="p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Icon name="lock" size={20} />
            禁用状态
          </h2>
          <p className="text-gray-600 mb-4">
            展示禁用状态下的模型选择器。
          </p>
          
          <div className="space-y-4">
            <ModelSelector
              models={models}
              selectedModels={[]}
              onSelectionChange={() => {}}
              mode="single"
              placeholder="当前不可用..."
              disabled={true}
              size="medium"
            />
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ModelSelectorExample;