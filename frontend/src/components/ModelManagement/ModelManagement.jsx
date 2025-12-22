import React, { useState, useEffect } from 'react';
import { getImageUrl, DEFAULT_IMAGES } from '../../config/imageConfig';
import ModelModal from './ModelModal';
import ModelParameterModal from './ModelParameterModal';
import SupplierDetail from '../SupplierManagement/SupplierDetail';
import ModelCapabilityAssociation from '../CapabilityManagement/ModelCapabilityAssociation';
import ParameterManagementMain from './ParameterManagementMain';
import '../../styles/ModelManagement.css';
import api from '../../utils/api';

const ModelManagement = ({ selectedSupplier, onSupplierSelect, onSupplierUpdate }) => {
  const [currentModels, setCurrentModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentModel, setCurrentModel] = useState(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(null); // 成功消息状态
  
  // 获取模型LOGO，如果模型没有LOGO，则使用供应商LOGO
  const getModelLogo = (model, supplier) => {
    if (!model && !supplier) return DEFAULT_IMAGES.provider;
    
    try {
      // 优先使用模型LOGO
      if (model && model.logo) {
        // 检测是否为外部URL
        if (model.logo.startsWith('http')) {
          // 使用后端代理端点处理外部URL，避免ORB安全限制
          const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(model.logo)}`;
          return proxyUrl;
        } else {
          // 使用配置的图片路径生成函数
          return getImageUrl('models', model.logo);
        }
      }
      
      // 如果模型没有LOGO，使用供应商LOGO
      if (supplier && supplier.logo) {
        // 检测是否为外部URL
        if (supplier.logo.startsWith('http')) {
          // 使用后端代理端点处理外部URL，避免ORB安全限制
          const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(supplier.logo)}`;
          return proxyUrl;
        } else {
          // 使用配置的图片路径生成函数
          return getImageUrl('providers', supplier.logo);
        }
      }
      
      // 没有logo时的默认路径
      return DEFAULT_IMAGES.provider;
    } catch (error) {
      console.error('获取模型logo失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      return DEFAULT_IMAGES.provider;
    }
  };
  
  // 模型模态框相关状态
  const [isModelModalOpen, setIsModelModalOpen] = useState(false);
  const [modelModalMode, setModelModalMode] = useState('add');
  const [editingModel, setEditingModel] = useState(null);
  
  // 模型参数相关状态
  const [modelParameters, setModelParameters] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [isParameterModalOpen, setIsParameterModalOpen] = useState(false);
  const [parameterModalMode, setParameterModalMode] = useState('add');
  const [editingParameter, setEditingParameter] = useState(null);
  
  // 模型能力相关状态
  const [modelCapabilities, setModelCapabilities] = useState({}); // 存储每个模型的能力信息
  const [isCapabilityModalOpen, setIsCapabilityModalOpen] = useState(false);
  const [currentCapabilitiesModel, setCurrentCapabilitiesModel] = useState(null);
  
  // 参数管理相关状态
  const [isParameterManagementView, setIsParameterManagementView] = useState(false);
  
  // 描述展开状态管理
  const [expandedDescriptions, setExpandedDescriptions] = useState({});
  
  // 获取模型相关状态
  const [fetchedModels, setFetchedModels] = useState([]);
  const [isModelSelectionOpen, setIsModelSelectionOpen] = useState(false);
  
  // 翻页和筛选相关状态
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredModels, setFilteredModels] = useState([]);
  const [selectedModelIds, setSelectedModelIds] = useState([]);

  // 当选择的供应商改变时，加载对应模型列表
  useEffect(() => {
    if (selectedSupplier) {
      loadModels();
    } else {
      setCurrentModels([]);
      setModelCapabilities({});
      setError(null);
    }
  }, [selectedSupplier]);

  // 模型筛选和翻页逻辑
  useEffect(() => {
    if (fetchedModels.length > 0) {
      // 筛选模型
      const filtered = fetchedModels.filter(model => 
        model.model_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.model_id.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredModels(filtered);
      setCurrentPage(1); // 重置到第一页
    } else {
      setFilteredModels([]);
    }
  }, [fetchedModels, searchTerm]);

  // 确保deepseek供应商有默认的deepseek-chat模型
  useEffect(() => {
    const addDefaultModel = async () => {
      if (selectedSupplier && selectedSupplier.key === 'deepseek' && currentModels.length === 0 && !saving) {
        // 创建默认模型，确保包含supplier_id字段以及后端要求的必填字段
        const defaultModel = {
          id: 1, // 使用整数ID
          model_id: 'deepseek-chat', // 后端必需字段
          name: 'DeepSeek Chat',
          description: '深度求索的对话模型',
          contextWindow: 8000,
          type: 'chat', // 后端必需字段
          isDefault: true,
          supplier_id: selectedSupplier.id, // 使用供应商的整数ID
          context_window: 8000, // 后端所需格式
          default_temperature: 0.7,
          default_max_tokens: 1000,
          default_top_p: 1.0,
          default_frequency_penalty: 0.0,
          default_presence_penalty: 0.0,
          is_active: true,
          is_default: true
        };

        try {
          setSaving(true);
          // 确保使用整数ID
          await api.modelApi.create(selectedSupplier.id, defaultModel);
          await loadModels();
        } catch (error) {
          console.error('Failed to add default model:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
          // 降级处理：直接添加到本地状态
          setCurrentModels([defaultModel]);
        } finally {
          setSaving(false);
        }
      }
    };

    // 添加延迟执行，防止初始加载时重复调用
    const timeoutId = setTimeout(addDefaultModel, 300);
    return () => clearTimeout(timeoutId);
  }, [selectedSupplier, currentModels.length, saving]);

  // 加载模型列表
  const loadModels = async () => {
    if (!selectedSupplier) return;

    setLoading(true);
    try {
      // 使用selectedSupplier.id作为参数调用更新后的API方法
      const result = await api.modelApi.getBySupplier(selectedSupplier.id);
      
      // 从结果中提取models数组
      const models = result.models || [];
      setCurrentModels(models);
      
      // 为每个模型加载能力信息
      await Promise.all(
        models.map(model => loadModelCapabilities(model.id))
      );
    } catch (err) {
      const errorMessage = err.message || '加载模型失败';
      console.error('❌ 加载模型失败:', errorMessage);
      setError(`加载模型失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };
  
  // 加载模型能力信息
  const loadModelCapabilities = async (modelId) => {
    try {
      const capabilities = await api.capabilityApi.getModelCapabilities(modelId);
      setModelCapabilities(prev => ({
        ...prev,
        [modelId]: capabilities
      }));
    } catch (err) {
      console.error(`加载模型 ${modelId} 的能力失败:`, JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      // 即使加载失败，也设置为空数组，避免显示错误
      setModelCapabilities(prev => ({
        ...prev,
        [modelId]: []
      }));
    }
  };

  // 添加模型
  const handleAddModelClick = () => {
    setEditingModel(null);
    setModelModalMode('add');
    setIsModelModalOpen(true);
  };

  // 获取模型列表
  const handleFetchModelsClick = async () => {
    if (!selectedSupplier) return;
    
    try {
      setSaving(true);
      
      // 获取供应商的API配置
      const supplierDetail = await api.supplierApi.getById(selectedSupplier.id);
      
      const apiConfig = {
        apiUrl: supplierDetail.api_endpoint || supplierDetail.apiUrl,
        apiKey: supplierDetail.api_key
      };
      
      console.log('获取模型API配置:', apiConfig);
      
      // 调用获取模型列表API
      const response = await api.supplierApi.fetchModelsFromApi(selectedSupplier.id, apiConfig);
      
      if (response.status === 'success' && response.models && response.models.length > 0) {
        // 获取已保存的模型列表
        const existingModels = await api.modelApi.getBySupplier(selectedSupplier.id);
        const existingModelIds = existingModels.models.map(model => model.model_id);
        
        // 过滤掉已保存的模型
        const newModels = response.models.filter(model => 
          !existingModelIds.includes(model.model_id)
        );
        
        if (newModels.length > 0) {
          // 显示模型选择界面
          setFetchedModels(newModels);
          // 默认选中所有模型
          setSelectedModelIds(newModels.map(model => model.model_id));
          setIsModelSelectionOpen(true);
          setSuccess(`成功获取 ${newModels.length} 个新模型（已过滤掉 ${response.models.length - newModels.length} 个已保存的模型）`);
        } else {
          setSuccess('所有模型都已保存，没有新的模型可添加');
        }
      } else {
        setError('未获取到模型列表，请检查API配置是否正确');
      }
    } catch (err) {
      const errorMessage = err.message || '获取模型列表失败';
      console.error('❌ 获取模型列表失败:', errorMessage);
      setError(`获取模型列表失败: ${errorMessage}`);
    } finally {
      setSaving(false);
    }
  };

  // 翻页相关函数
  const getCurrentPageModels = () => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredModels.slice(startIndex, endIndex);
  };

  const totalPages = Math.ceil(filteredModels.length / pageSize);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  // 处理模型选择状态变化
  const handleModelSelectionChange = (modelId, isSelected) => {
    if (isSelected) {
      setSelectedModelIds(prev => [...prev, modelId]);
    } else {
      setSelectedModelIds(prev => prev.filter(id => id !== modelId));
    }
  };

  // 保存选中的模型
  const handleSaveSelectedModels = async (selectedModelIds) => {
    try {
      setSaving(true);
      
      const selectedModels = fetchedModels.filter(model => 
        selectedModelIds.includes(model.model_id)
      );
      
      let savedCount = 0;
      let errorCount = 0;
      const errorMessages = [];
      
      for (const model of selectedModels) {
        try {
          // 检查模型是否已存在
          const existingModels = await api.modelApi.getBySupplier(selectedSupplier.id);
          const modelExists = existingModels.models.some(existing => 
            existing.model_id === model.model_id
          );
          
          if (!modelExists) {
            // 调试：检查模型对象结构
            console.log('模型对象结构:', JSON.stringify(model, null, 2));
            console.log('模型ID:', model.model_id, '类型:', typeof model.model_id);
            
            // 构建完整的模型数据，确保包含所有必需字段，格式与API期望一致
            const modelData = {
              model_id: model.model_id,
              model_name: model.model_name || model.model_id,
              description: model.description || '',
              context_window: Number(model.context_window) || 8000,
              max_tokens: Number(model.max_tokens) || 1000,
              is_active: true,
              is_default: false,
              supplier_id: selectedSupplier.id
            };
            
            console.log('准备保存模型数据:', JSON.stringify(modelData, null, 2));
            
            await api.modelApi.create(selectedSupplier.id, modelData);
            savedCount++;
            console.log(`✅ 模型 ${model.model_id} 保存成功`);
          } else {
            console.log(`ℹ️ 模型 ${model.model_id} 已存在，跳过保存`);
          }
        } catch (err) {
          errorCount++;
          const errorMsg = `模型 ${model.model_id} 保存失败: ${err.message}`;
          errorMessages.push(errorMsg);
          console.error(`❌ ${errorMsg}`);
        }
      }
      
      // 关闭选择界面并重新加载模型列表
      setIsModelSelectionOpen(false);
      setFetchedModels([]);
      await loadModels();
      
      // 显示保存结果
      if (errorCount === 0) {
        setSuccess(`成功保存 ${savedCount} 个模型`);
      } else {
        setError(`保存完成：成功 ${savedCount} 个，失败 ${errorCount} 个。失败详情：${errorMessages.join('; ')}`);
      }
    } catch (err) {
      const errorMessage = err.message || '保存模型失败';
      console.error('❌ 保存模型失败:', errorMessage);
      setError(`保存模型失败: ${errorMessage}`);
    } finally {
      setSaving(false);
    }
  };

  // 关闭模型选择界面
  const handleCloseModelSelection = () => {
    setIsModelSelectionOpen(false);
    setFetchedModels([]);
    setSelectedModelIds([]);
    setSearchTerm('');
    setCurrentPage(1);
  };

  // 编辑模型
  const handleEditModelClick = (model) => {
    setEditingModel(model);
    setModelModalMode('edit');
    setIsModelModalOpen(true);
  };

  // 关闭模型模态框
  const handleCloseModelModal = () => {
    setIsModelModalOpen(false);
    setEditingModel(null);
  };

  // 保存模型数据
  const handleSaveModelData = async (modelData, logo) => {
    try {
      setSaving(true);
      let savedModel;
      
      // 保存模型基本信息
      if (modelModalMode === 'add') {
        savedModel = await api.modelApi.create(selectedSupplier.id, { ...modelData, logo });
        setSuccess('模型添加成功');
      } else {
        savedModel = await api.modelApi.update(selectedSupplier.id, editingModel.id, { ...modelData, logo });
        setSuccess('模型更新成功');
      }
      
      // 如果选择了参数模板，同步模型参数与模板
      if (modelData.parameterTemplateId) {
        await api.modelApi.syncModelParametersWithTemplate(
          selectedSupplier.id, 
          savedModel.id || (modelModalMode === 'edit' ? editingModel.id : null), 
          modelData.parameterTemplateId
        );
        setSuccess('模型保存成功并与参数模板同步');
      }
      
      await loadModels();
    } catch (err) {
      const errorMessage = err.message || '保存模型失败';
      console.error('❌ 保存模型失败:', errorMessage);
      setError(`保存模型失败: ${errorMessage}`);
    } finally {
      setSaving(false);
      setIsModelModalOpen(false);
      setSuccess(null);
    }
  };

  // 删除模型
  const handleDeleteModel = async (modelId) => {
    if (window.confirm('确定要删除这个模型吗？')) {
      try {
        setSaving(true);
        await api.modelApi.delete(selectedSupplier.id, modelId);
        setSuccess('模型删除成功');
        await loadModels();
      } catch (err) {
        const errorMessage = err.message || '删除模型失败';
        console.error('❌ 删除模型失败:', errorMessage);
        setError(`删除模型失败: ${errorMessage}`);
      } finally {
        setSaving(false);
        setSuccess(null);
      }
    }
  };

  // 设置默认模型
  const handleSetDefault = async (modelId) => {
    try {
      setSaving(true);
      await api.modelApi.setDefault(selectedSupplier.id, modelId);
      setSuccess('默认模型设置成功');
      await loadModels();
    } catch (err) {
      const errorMessage = err.message || '设置默认模型失败';
      console.error('❌ 设置默认模型失败:', errorMessage);
      setError(`设置默认模型失败: ${errorMessage}`);
    } finally {
      setSaving(false);
      setSuccess(null);
    }
  };
  
  // 管理模型能力
  const handleManageCapabilities = (model) => {
    setCurrentCapabilitiesModel(model);
    setIsCapabilityModalOpen(true);
  };
  
  // 关闭能力管理模态框
  const handleCloseCapabilityModal = () => {
    setIsCapabilityModalOpen(false);
    setCurrentCapabilitiesModel(null);
  };
  
  // 切换描述展开状态
  const toggleDescription = (modelId) => {
    setExpandedDescriptions(prev => ({
      ...prev,
      [modelId]: !prev[modelId]
    }));
  };
  
  // 导航到参数管理主界面
  const handleNavigateToParameterManagement = () => {
    setIsParameterManagementView(true);
  };
  
  // 从参数管理主界面返回
  const handleBackFromParameterManagement = () => {
    setIsParameterManagementView(false);
  };
  
  // 截断描述文本
  const truncateDescription = (text, maxLength = 100) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // 关闭时重新加载模型能力，以便更新显示
  const handleCapabilityModalClose = () => {
    if (selectedModel) {
      loadModelCapabilities(selectedModel.id);
    }
  };

  // 模型参数相关处理函数
  const handleViewParameters = (model) => {
    setSelectedModel(model);
    loadModelParameters(model.id);
  };

  const handleBackToModels = () => {
    setSelectedModel(null);
    setModelParameters([]);
  };

  const loadModelParameters = async (modelId) => {
    try {
      setLoading(true);
      const parameters = await api.modelApi.getParameters(selectedSupplier.id, modelId);
      setModelParameters(parameters);
    } catch (err) {
      console.error('加载模型参数失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      setError('加载模型参数失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAddParameterClick = () => {
    setEditingParameter(null);
    setParameterModalMode('add');
    setIsParameterModalOpen(true);
  };

  const handleEditParameterClick = (parameter) => {
    // 如果是继承参数，给出提示
    if (parameter.inherited) {
      setError('继承参数不能被编辑');
      return;
    }
    
    setEditingParameter(parameter);
    setParameterModalMode('edit');
    setIsParameterModalOpen(true);
  };

  const handleCloseParameterModal = () => {
    setIsParameterModalOpen(false);
    setEditingParameter(null);
  };

  const handleSaveParameterData = async (parameterData) => {
    try {
      setSaving(true);
      if (parameterModalMode === 'add') {
        await api.modelApi.createParameter(selectedSupplier.id, selectedModel.id, parameterData);
        setSuccess('参数添加成功');
      } else {
        await api.modelApi.updateParameter(selectedSupplier.id, selectedModel.id, editingParameter.id, parameterData);
        setSuccess('参数更新成功');
      }
      loadModelParameters(selectedModel.id);
    } catch (err) {
      console.error('保存参数失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      setError('保存参数失败');
    } finally {
      setSaving(false);
      setIsParameterModalOpen(false);
      setSuccess(null);
    }
  };

  const handleDeleteParameter = async (parameterId) => {
    // 查找要删除的参数
    const parameter = modelParameters.find(p => p.id === parameterId);
    
    // 如果是继承参数，不允许删除
    if (parameter && parameter.inherited) {
      setError('继承参数不能被删除');
      return;
    }
    
    if (window.confirm('确定要删除这个参数吗？')) {
      try {
        setSaving(true);
        await api.modelApi.deleteParameter(selectedSupplier.id, selectedModel.id, parameterId);
        setSuccess('参数删除成功');
        loadModelParameters(selectedModel.id);
      } catch (err) {
      console.error('删除参数失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      setError('删除参数失败');
    } finally {
        setSaving(false);
        setSuccess(null);
      }
    }
  };

  return (
    <div className="model-management-container">
      {/* 供应商详情 */}
      <div className="supplier-detail-section">
        <SupplierDetail
          selectedSupplier={selectedSupplier}
          onSupplierSelect={onSupplierSelect}
          onSupplierUpdate={onSupplierUpdate}
          onNavigateToParameterManagement={handleNavigateToParameterManagement}
        />
      </div>

      {/* 参数管理主界面 */}
      {isParameterManagementView ? (
        <ParameterManagementMain
          selectedSupplier={selectedSupplier}
          onBack={handleBackFromParameterManagement}
          selectedModel={selectedModel}
        />
      ) : selectedModel ? (
        <div className="model-parameters-section">
          <div className="section-header">
            <h2>{selectedModel.modelName ? `${selectedModel.modelName} (${selectedModel.modelId})` : selectedModel.modelId} - 参数管理</h2>
            <div className="section-actions">
              <button
                className="btn btn-primary"
                onClick={() => handleAddParameterClick()}
                disabled={saving}
              >
                添加参数
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => handleBackToModels()}
                disabled={saving}
              >
                返回模型列表
              </button>
            </div>
          </div>

          {loading ? (
            <div className="loading-state">加载参数中...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : modelParameters.length === 0 ? (
            <div className="empty-state">暂无参数，请添加参数</div>
          ) : (
            <div className="parameters-table-container">
              <table className="parameters-table">
                <thead>
                  <tr>
                    <th>参数名称</th>
                    <th>参数值</th>
                    <th>类型</th>
                    <th>默认值</th>
                    <th>描述</th>
                    <th>必填</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {modelParameters.map((param) => {
                    return (
                      <tr key={param.id} className={param.inherited ? 'inherited-parameter' : 'custom-parameter'}>
                        <td>
                          {param.parameter_name}
                          {param.inherited && <span className="inherited-badge">继承</span>}
                        </td>
                        <td>{typeof param.parameter_value === 'object' ? JSON.stringify(param.parameter_value) : param.parameter_value}</td>
                        <td>{param.parameter_type}</td>
                        <td>{typeof param.default_value === 'object' ? JSON.stringify(param.default_value) : param.default_value}</td>
                        <td>{param.description}</td>
                        <td>{param.is_required ? '是' : '否'}</td>
                        <td>
                        <div className="parameter-actions">
                          <button
                            className="btn btn-secondary btn-small"
                            onClick={() => handleEditParameterClick(param)}
                            disabled={saving || param.inherited}
                          >
                            编辑
                          </button>
                          <button
                            className="btn btn-danger btn-small"
                            onClick={() => handleDeleteParameter(param.id)}
                            disabled={saving || param.inherited}
                          >
                            删除
                          </button>
                        </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="model-management-section">
          {/* 模型卡片 */}
          <div className="model-section">
            <div className="section-header">
              <h2>模型卡片</h2>
              <div className="section-actions">
                <button className="btn btn-primary"
                  onClick={() => handleAddModelClick()}
                  disabled={saving || !selectedSupplier}
                >
                  添加模型
                </button>
                <button className="btn btn-secondary"
                  onClick={() => handleFetchModelsClick()}
                  disabled={saving || !selectedSupplier}
                >
                  获取模型
                </button>
              </div>
            </div>

            {loading ? (
              <div className="loading-state">加载模型中...</div>
            ) : error ? (
              <div className="error-message">{error}</div>
            ) : currentModels.length === 0 ? (
              <div className="empty-state">暂无模型，请添加模型</div>
            ) : (
              <div className="models-container">
                {currentModels.map((model) => (
                  <div key={model.id} className={`model-card ${model.is_default ? 'default' : ''}`}>
                    <div className="model-header">
                      <div className="model-header-left">
                        <div className="model-logo">
                          <img 
                            src={getModelLogo(model, selectedSupplier)} 
                            alt="模型LOGO" 
                            className="model-logo-image"
                            onError={(e) => {
                              e.target.src = DEFAULT_IMAGES.provider;
                              e.target.alt = '默认LOGO';
                            }}
                          />
                        </div>
                        <h3 className="model-name">{model.modelName ? `${model.modelName} (${model.modelId})` : model.modelId}</h3>
                      </div>
                      <div className="model-header-right">
                        {model.is_default && <span className="default-badge">默认</span>}
                        {/* 模型分类信息 */}
                        {model.categories && model.categories.length > 0 ? (
                          <div className="model-categories">
                            {model.categories.map((category) => (
                              <span key={category.id} className="model-category-badge">
                                {category.logo ? (
                                  <img 
                                    src={category.logo} 
                                    alt={category.display_name} 
                                    className="category-logo"
                                    onError={(e) => {
                                      e.target.style.display = 'none';
                                    }}
                                  />
                                ) : null}
                                {category.display_name || category.name}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="model-type-badge">
                            {model.modelTypeLogo && (
                              <div 
                                dangerouslySetInnerHTML={{__html: model.modelTypeLogo}}
                                className="model-type-logo"
                                title={model.modelTypeDisplayName || model.modelTypeName}
                              />
                            )}
                            {model.modelTypeDisplayName || model.modelTypeName || model.modelType || '未分类'}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="model-desc">
                      <div className="description-content">
                        {expandedDescriptions[model.id] 
                          ? model.description 
                          : truncateDescription(model.description, 100)
                        }
                      </div>
                      {model.description && model.description.length > 100 && (
                        <button 
                          className="description-toggle"
                          onClick={() => toggleDescription(model.id)}
                        >
                          {expandedDescriptions[model.id] ? '收起' : '显示更多'}
                        </button>
                      )}
                    </div>
                    <div className="model-meta">
                        <div className="meta-item">上下文窗口: {model.contextWindow || model.context_window}</div>
                        <div className="meta-item">最大Token: {model.max_tokens || 1000}</div>
                      {/* 显示模型能力信息 */}
                      <div className="meta-item">
                        <span>能力:</span>
                        <div className="capabilities-list">
                          {modelCapabilities[model.id]?.length > 0 ? (
                            modelCapabilities[model.id].map(capability => (
                              <span key={capability.id} className="capability-tag">
                                {capability.display_name || capability.name}
                              </span>
                            ))
                          ) : (
                            <span className="no-capabilities">暂无能力</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="model-actions">
                      <button
                        className="btn btn-secondary btn-small"
                        onClick={() => handleEditModelClick(model)}
                        disabled={saving}
                      >
                        编辑
                      </button>
                      <button
                        className="btn btn-success btn-small"
                        onClick={() => handleViewParameters(model)}
                        disabled={saving}
                      >
                        参数
                      </button>
                      <button
                        className="btn btn-info btn-small"
                        onClick={() => handleManageCapabilities(model)}
                        disabled={saving}
                      >
                        能力
                      </button>
                      <button
                        className="btn btn-danger btn-small"
                        onClick={() => handleDeleteModel(model.id)}
                        disabled={saving}
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 模型模态窗口 */}
      <ModelModal
        isOpen={isModelModalOpen}
        onClose={handleCloseModelModal}
        onSave={handleSaveModelData}
        model={editingModel}
        mode={modelModalMode}
        isFirstModel={currentModels.length === 0}
      />

      {/* 模型参数模态窗口 */}
      <ModelParameterModal
        isOpen={isParameterModalOpen}
        onClose={handleCloseParameterModal}
        onSave={handleSaveParameterData}
        parameter={editingParameter}
        mode={parameterModalMode}
      />
      
      {/* 模型能力管理模态窗口 */}
      {currentCapabilitiesModel && (
        <ModelCapabilityAssociation
          isOpen={isCapabilityModalOpen}
          onClose={handleCloseCapabilityModal}
          model={currentCapabilitiesModel}
        />
      )}
      
      {/* 模型选择界面 */}
      {isModelSelectionOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>选择要保存的模型</h3>
              <button className="modal-close" onClick={handleCloseModelSelection}>
                ×
              </button>
            </div>
            
            {/* 搜索框 */}
            <div className="modal-search">
              <input
                type="text"
                placeholder="搜索模型名称或ID..."
                value={searchTerm}
                onChange={handleSearchChange}
                className="search-input"
              />
              <div className="search-info">
                <span>共找到 {filteredModels.length} 个模型</span>
              </div>
            </div>
            
            <div className="modal-body">
              <div className="model-selection-list">
                {getCurrentPageModels().map((model) => (
                  <div key={model.model_id} className="model-selection-item">
                    <input
                      type="checkbox"
                      id={`model-${model.model_id}`}
                      value={model.model_id}
                      checked={selectedModelIds.includes(model.model_id)}
                      onChange={(e) => handleModelSelectionChange(model.model_id, e.target.checked)}
                    />
                    <label htmlFor={`model-${model.model_id}`} className="model-selection-label">
                      <div className="model-info">
                        <strong>{model.model_name}</strong>
                        <span className="model-id">ID: {model.model_id}</span>
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>
            
            {/* 翻页控件 */}
            {totalPages > 1 && (
              <div className="modal-pagination">
                <button 
                  className="pagination-btn" 
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  上一页
                </button>
                <span className="pagination-info">
                  第 {currentPage} 页 / 共 {totalPages} 页
                </span>
                <button 
                  className="pagination-btn" 
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  下一页
                </button>
              </div>
            )}
            <div className="modal-footer">
              <button 
                className="btn btn-secondary" 
                onClick={handleCloseModelSelection}
              >
                取消
              </button>
              <button 
                className="btn btn-primary" 
                onClick={() => handleSaveSelectedModels(selectedModelIds)}
                disabled={selectedModelIds.length === 0}
              >
                保存选中模型 ({selectedModelIds.length})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelManagement;