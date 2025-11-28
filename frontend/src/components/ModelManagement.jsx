import React, { useState, useEffect } from 'react';
import SupplierModal from './SupplierModal';
import ModelModal from './ModelModal';
import '../styles/ModelManagement.css';
import api from '../utils/api';

const ModelManagement = ({ selectedSupplier, onSupplierSelect, onSupplierUpdate }) => {
  const [currentModels, setCurrentModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentModel, setCurrentModel] = useState(null);
  const [saving, setSaving] = useState(false);
  const [currentSupplier, setCurrentSupplier] = useState(null);
  const [isSupplierModalOpen, setIsSupplierModalOpen] = useState(false);
  const [supplierModalMode, setSupplierModalMode] = useState('edit');
  // 模型模态框相关状态
  const [isModelModalOpen, setIsModelModalOpen] = useState(false);
  const [modelModalMode, setModelModalMode] = useState('add');
  const [editingModel, setEditingModel] = useState(null);
  const [newModel, setNewModel] = useState({
    id: '',
    name: '',
    description: '',
    contextWindow: 8000,
    isDefault: false
  });

  // 当选择的供应商改变时，加载对应模型列表
  // 初始加载时，如果有供应商，加载其模型
  useEffect(() => {
    if (selectedSupplier) {
      loadModels();
    } else {
      setCurrentModels([]);
      setError(null);
    }
  }, [selectedSupplier]);

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

        // 处理切换供应商启用状态
        const handleToggleSupplierStatus = async (supplier) => {
          try {
            setSaving(true);

            // 切换启用状态
            const newStatus = !supplier.is_active;
            const confirmation = newStatus
              ? `确定要启用供应商 "${supplier.name}" 吗？`
              : `确定要停用供应商 "${supplier.name}" 吗？`;

            if (!window.confirm(confirmation)) {
              return;
            }

            // 调用API更新状态
            const apiUrl = `http://localhost:8000/api/model-management/suppliers/${supplier.id}`;
            const response = await fetch(apiUrl, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ is_active: newStatus })
            });

            if (!response.ok) {
              const errorText = await response.text();
              throw new Error(`状态更新失败: ${errorText}`);
            }

            // 通知父组件更新供应商列表
            if (onSupplierUpdate) {
              setTimeout(() => onSupplierUpdate(), 0);
            }

            console.log(`供应商状态已${newStatus ? '启用' : '停用'}: ${supplier.name}`);
          } catch (err) {
            setError('更新供应商状态失败');
            console.error('Failed to toggle supplier status:', err);
          } finally {
            setSaving(false);
          }
        };

        try {
          setSaving(true);
          console.log('创建默认模型:', defaultModel);
          // 确保使用整数ID
          await api.modelApi.create(selectedSupplier.id, defaultModel);
          await loadModels();

          console.error('Failed to add default model:', err);
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

  // 加载模型数据
  const loadModels = async () => {
    if (!selectedSupplier) {
      console.warn('⚠️ 没有选择供应商');
      return;
    }

    try {
      setLoading(true);
      console.log(`🔄 加载模型数据，供应商ID: ${selectedSupplier.id}`);
      // 使用selectedSupplier.id的原始值（字符串或数字）
      const data = await api.modelApi.getBySupplier(selectedSupplier.id);

      // 统一处理不同的响应格式
      let models = [];
      if (Array.isArray(data)) {
        models = data;
      } else if (data && Array.isArray(data.models)) {
        models = data.models;
      } else if (data && Array.isArray(data.data)) {
        models = data.data;
      }

      // 确保所有模型都有必要的属性
      const normalizedModels = models.map(model => ({
        ...model,
        id: model.id || model.model_id || String(Date.now() + Math.random()),
        name: model.name || '未知模型',
        description: model.description || '暂无描述',
        isDefault: model.isDefault || model.is_default || false
      }));

      console.log(`✅ 模型加载完成，数量: ${normalizedModels.length}`);
      setCurrentModels(normalizedModels);
      setError(null);
    } catch (err) {
      console.error('❌ 加载模型数据失败:', err);
      setError('加载模型数据失败');

      // 降级处理：设置空数组，因为api.modelApi.getBySupplier应该已经处理了降级
      setCurrentModels([]);
    } finally {
      setLoading(false);
    }
  };

  // 设置默认模型
  const handleSetDefault = async (modelId) => {
    if (!selectedSupplier || saving) return;

    try {
      setSaving(true);
      // 使用selectedSupplier.id的原始值（字符串）
      await api.modelApi.setDefault(selectedSupplier.id, modelId);
      // 刷新模型列表
      await loadModels();
    } catch (err) {
      setError('设置默认模型失败');
      console.error('Failed to set default model:', err);
      // 降级处理：本地更新
      const updatedModels = currentModels.map(model => ({
        ...model,
        isDefault: model.id === modelId
      }));
      setCurrentModels(updatedModels);
    } finally {
      setSaving(false);
    }
  };

  // 保存模型
  const handleSaveModel = async () => {
    if (!currentModel || !selectedSupplier || saving) return;

    try {
      setSaving(true);
      // 使用selectedSupplier.id的原始值（字符串）
      await api.modelApi.update(selectedSupplier.id, currentModel.id, currentModel);
      await loadModels();
      setIsEditing(false);
    } catch (err) {
      setError('更新模型失败');
      console.error('Failed to update model:', err);
      // 降级处理：本地更新
      const updatedModels = currentModels.map(model =>
        model.id === currentModel.id ? currentModel : model
      );
      setCurrentModels(updatedModels);
      setIsEditing(false);
    } finally {
      setSaving(false);
    }
  };

  // 保存模型数据（用于模态框）
  const handleSaveModelData = async (modelData) => {
    if (!selectedSupplier || saving) return;

    try {
      setSaving(true);
      
      if (modelModalMode === 'add') {
        // 构建符合后端要求的模型数据结构
        const modelToAdd = {
          name: modelData.name,
          display_name: modelData.name, // 使用name作为display_name
          description: modelData.description || '',
          context_window: modelData.contextWindow || 8000,
          max_tokens: 1000,
          is_active: true,
          is_default: modelData.isDefault || currentModels.length === 0
          // 不需要手动设置supplier_id，后端路由会处理
        };
        
        await api.modelApi.create(selectedSupplier.id, modelToAdd);
      } else {
        // 更新模型
        const modelToUpdate = {
          ...modelData,
          context_window: modelData.contextWindow || 8000,
          model_type: modelData.modelType || 'chat', // 添加model_type字段
          max_tokens: modelData.maxTokens || 1000, // 添加max_tokens字段
          is_default: modelData.isDefault
        };
        
        await api.modelApi.update(selectedSupplier.id, modelData.id, modelToUpdate);
      }
      
      // 重新加载模型列表
      await loadModels();
      // 成功提示
      alert(modelModalMode === 'add' ? '模型添加成功' : '模型更新成功');
    } catch (err) {
      setError(modelModalMode === 'add' ? '添加模型失败' : '更新模型失败');
      console.error(`${modelModalMode === 'add' ? 'Failed to add' : 'Failed to update'} model:`, err);
      
      // 降级处理：本地更新
      if (modelModalMode === 'add') {
        const localModel = {
          id: modelData.id || String(Date.now()),
          model_id: modelData.id,
          name: modelData.name || '未命名模型',
          description: modelData.description || '暂无描述',
          contextWindow: modelData.contextWindow || 8000,
          context_window: modelData.contextWindow || 8000,
          isDefault: modelData.isDefault || currentModels.length === 0,
          is_default: modelData.isDefault || currentModels.length === 0,
          supplier_id: selectedSupplier.id,
          model_type: 'chat', // 修改为model_type，与后端API匹配
          max_tokens: 1000, // 添加max_tokens字段
          is_active: true
        };
        setCurrentModels([...currentModels, localModel]);
      } else {
        const updatedModels = currentModels.map(model =>
          model.id === modelData.id ? {
            ...model,
            ...modelData,
            context_window: modelData.contextWindow || 8000,
            model_type: modelData.modelType || model.model_type || 'chat', // 添加model_type字段
            max_tokens: modelData.maxTokens || model.max_tokens || 1000, // 添加max_tokens字段
            is_default: modelData.isDefault
          } : model
        );
        setCurrentModels(updatedModels);
      }
    } finally {
      setSaving(false);
    }
  };

  // 添加新模型
  const handleAddModel = async () => {
    if (!newModel.id || !newModel.name || !selectedSupplier || saving) return;

    // 如果是第一个模型，自动设为默认
    const isFirstModel = currentModels.length === 0;

    // 构建符合后端要求的模型数据结构
    const modelToAdd = {
      model_id: newModel.id, // 映射到后端需要的model_id字段
      name: newModel.name,
      description: newModel.description || '',
      type: 'chat', // 默认为chat类型，这是后端必需字段
      context_window: newModel.contextWindow || 8000, // 映射到后端格式
      default_temperature: 0.7,
      default_max_tokens: 1000,
      default_top_p: 1.0,
      default_frequency_penalty: 0.0,
      default_presence_penalty: 0.0,
      is_active: true,
      is_default: isFirstModel,
      supplier_id: selectedSupplier.id // 使用供应商的整数ID
    };

    try {
      setSaving(true);
      console.log('🔄 添加模型数据:', modelToAdd);
      await api.modelApi.create(selectedSupplier.id, modelToAdd);
      console.log('✅ 模型添加成功');
      await loadModels();

      // 重置新模型表单
      setNewModel({
        id: '',
        name: '',
        description: '',
        contextWindow: 8000,
        isDefault: false
      });
    } catch (err) {
      console.error('❌ 添加模型失败:', err);
      setError('添加模型失败，但已保存到本地');

      // 降级处理：本地添加，使用更完善的数据格式
      console.log('⚠️ 降级处理：将模型添加到本地状态');
      const localModel = {
        id: newModel.id || String(Date.now()),
        model_id: newModel.id,
        name: newModel.name || '未命名模型',
        description: newModel.description || '暂无描述',
        contextWindow: newModel.contextWindow || 8000,
        context_window: newModel.contextWindow || 8000, // 同时支持两种格式
        isDefault: isFirstModel,
        is_default: isFirstModel,
        supplier_id: selectedSupplier.id,
        type: 'chat',
        is_active: true
      };

      const updatedModels = [...currentModels, localModel];
      setCurrentModels(updatedModels);

      // 重置表单，确保用户体验一致
      setNewModel({
        id: '',
        name: '',
        description: '',
        contextWindow: 8000,
        isDefault: false
      });
    } finally {
      setSaving(false);
    }
  };

  // 删除模型
  const handleDeleteModel = async (modelId) => {
    if (!selectedSupplier || saving) return;

    if (!window.confirm('确定要删除这个模型吗？')) {
      return;
    }

    try {
      setSaving(true);
      // 使用selectedSupplier.id的原始值（字符串）
      await api.modelApi.delete(selectedSupplier.id, modelId);
      await loadModels();
    } catch (err) {
      setError('删除模型失败');
      console.error('Failed to delete model:', err);
      // 降级处理：本地删除
      const modelToDelete = currentModels.find(model => model.id === modelId);
      const updatedModels = currentModels.filter(model => model.id !== modelId);

      // 如果删除的是默认模型，将第一个模型设为默认
      if (modelToDelete.isDefault && updatedModels.length > 0) {
        updatedModels[0].isDefault = true;
      }

      setCurrentModels(updatedModels);
    } finally {
      setSaving(false);
    }
  };

  // 编辑模型
  const handleEditModel = (model) => {
    setCurrentModel({ ...model });
    setIsEditing(true);
  };

  if (!selectedSupplier) {
    return (
      <div className="model-management">
        <div className="model-header">
          <h3>模型管理</h3>
          {selectedSupplier && (
            <button
              className="btn btn-primary"
              onClick={handleAddModelClick}
              disabled={saving}
            >
              添加模型
            </button>
          )}
        </div>
        <div className="no-supplier-selected">
          <p>请先选择一个供应商</p>
        </div>
      </div>
    );
  }

  // 安全显示API密钥的函数
  const formatApiKey = (apiKey) => {
    if (!apiKey) return '未设置';
    if (apiKey.length <= 8) return apiKey;
    const prefix = apiKey.slice(0, 4);
    const suffix = apiKey.slice(-4);
    const maskedLength = apiKey.length - 8;
    const masked = '*'.repeat(maskedLength);
    return `${prefix}${masked}${suffix}`;
  };

  // 处理编辑供应商
  const handleEditSupplier = (supplier) => {
    setCurrentSupplier({ ...supplier });
    setSupplierModalMode('edit');
    setIsSupplierModalOpen(true);
  };

  // 处理关闭供应商模态窗口
  const handleCloseSupplierModal = () => {
    setIsSupplierModalOpen(false);
    setCurrentSupplier(null);
  };
  
  // 处理打开添加模型模态窗口
  const handleAddModelClick = () => {
    setModelModalMode('add');
    setEditingModel(null);
    setIsModelModalOpen(true);
  };
  
  // 处理编辑模型
  const handleEditModelClick = (model) => {
    setEditingModel({ ...model });
    setModelModalMode('edit');
    setIsModelModalOpen(true);
  };
  
  // 处理关闭模型模态窗口
  const handleCloseModelModal = () => {
    setIsModelModalOpen(false);
    setEditingModel(null);
  };

  // 处理保存供应商（更新）
  const handleSaveSupplier = async (apiData, frontendData) => {
    try {
      setSaving(true);

      console.log('DEBUG: 提交的API数据(已格式化):', apiData);
      console.log('DEBUG: 提交的前端数据:', frontendData);
      console.log('DEBUG: 当前模态窗口模式:', modalMode);
      console.log('DEBUG: 当前供应商状态:', currentSupplier);

      // 检查是否是FormData对象（用于文件上传）
      const isFormData = apiData instanceof FormData;
      console.log('DEBUG: 是否为FormData对象:', isFormData);
      
      let dataToSend = apiData;
      
      if (!isFormData) {
        // 直接使用apiData，因为它已经是正确的格式
        // 只需要确保is_active字段被正确设置
        dataToSend = {
          ...apiData,
          is_active: apiData.is_active !== undefined ? apiData.is_active : true,
          is_domestic: apiData.is_domestic !== undefined ? apiData.is_domestic : false
        };
      }

      // 只在提供了API密钥时设置api_key_env_name
      if (dataToSend.api_key && dataToSend.api_key.trim()) {
        // 使用currentSupplier的key或name作为环境变量名的一部分
        const supplierKey = currentSupplier ?
          (currentSupplier.key || currentSupplier.name).toUpperCase() :
          (apiData.id || '').toUpperCase();
        dataToSend.api_key_env_name = `API_KEY_${supplierKey}`;
      }

      console.log('发送到API的数据:', dataToSend);

      let updatedSupplierData;

      if (modalMode === 'edit' && currentSupplier) {
        // 编辑模式 - 确保ID是数字类型
        const supplierId = Number(currentSupplier.id);
        console.log('更新供应商ID:', currentSupplier.id, '转换后的数字ID:', supplierId);

        // 使用api.js中的supplierApi.update方法，确保数据格式一致
        updatedSupplierData = await api.supplierApi.update(supplierId, dataToSend);
        console.log('DEBUG: API返回的更新后数据:', updatedSupplierData);

        // 将后端返回的数据映射回前端格式，使用frontendData保留用户的原始输入
        const frontendFormat = {
          ...frontendData,
          id: updatedSupplierData.id,
          key: String(updatedSupplierData.id),
          name: updatedSupplierData.name,
          description: updatedSupplierData.description,
          isDomestic: frontendData.isDomestic !== undefined ? frontendData.isDomestic : updatedSupplierData.is_domestic || false
        };

        console.log('DEBUG: 更新后的前端格式数据:', frontendFormat);
        console.log('DEBUG: 保留原始用户输入的URL - website:', frontendData.website, 'apiUrl:', frontendData.apiUrl);

        // 立即更新本地currentSupplier状态
        setCurrentSupplier(frontendFormat);

        // 同时更新当前选中的供应商
        if (selectedSupplier?.id === updatedSupplierData.id) {
          if (onSupplierSelect) {
            console.log('调用onSupplierSelect更新选中的供应商');
            onSupplierSelect(frontendFormat);
          }
        }

        // 强制刷新页面数据
        if (onSupplierUpdate) {
          console.log('调用onSupplierUpdate刷新数据');
          // 使用setTimeout确保状态更新完成后再调用刷新
          setTimeout(() => onSupplierUpdate(), 0);
        }

        console.log('保存成功，准备关闭模态窗口');

        // 返回成功信息，确保模态窗口可以正确关闭
        return { success: true, data: frontendFormat };
      }
    } catch (err) {
      setError(modalMode === 'add' ? '添加供应商失败' : '更新供应商失败');
      console.error(`${modalMode === 'add' ? '添加' : '更新'}供应商失败:`, err);
      console.error('错误详情:', err.stack);
      throw err; // 抛出错误让模态窗口处理
    } finally {
      setSaving(false);
    }
  };

  // 处理删除供应商
  // 根据供应商返回对应的LOGO图标
  const getSupplierLogo = (supplier) => {
    if (!supplier) return '';

    // 优先使用数据库中的logo字段，如果为空则使用名称生成
    // 注意：在Vite项目中，public目录下的资源直接从根路径开始引用
    console.log('DEBUG: 获取供应商logo:', supplier.logo);
    const logoPath = supplier.logo
      ? `/logos/providers/${supplier.logo}`
      : `/logos/providers/${(supplier.name || '').toLowerCase().replace(/\s+/g, '_')}.png`;

    return (
      <img
        src={logoPath}
        alt={`${supplier.name} logo`}
        style={{ width: '30px', height: '30px', borderRadius: '4px' }}
        onError={(e) => {
          // 图片加载失败时，显示供应商名称首字母
          e.target.style.display = 'none';
          const fallbackElement = document.createElement('div');
          fallbackElement.style.cssText = 'width: 30px; height: 30px; backgroundColor: #e0e0e0; borderRadius: 4px; display: flex; alignItems: center; justifyContent: center;';
          fallbackElement.textContent = '';
          fallbackElement.textContent = supplier.name?.[0] || '?';
          e.target.parentNode.appendChild(fallbackElement);
        }}
      />
    )
  };

  const handleDeleteSupplier = async (supplier) => {
    if (!window.confirm(`确定要删除供应商 "${supplier.name}" 吗？删除后将无法恢复。`)) {
      return;
    }

    try {
      setSaving(true);
      // 使用api.supplierApi.delete方法删除供应商，确保使用正确的API端口
      await api.supplierApi.delete(supplier.id);
      // api.supplierApi.delete方法内部已经处理了错误情况，如果成功则继续执行

      // 清空当前模型列表
      setCurrentModels([]);

      // 通知父组件更新供应商列表
      if (onSupplierUpdate) {
        onSupplierUpdate();
      }

      // 通知父组件清除选中的供应商
      if (onSupplierSelect) {
        onSupplierSelect(null);
      }
    } catch (err) {
      setError('删除供应商失败');
      console.error('Failed to delete supplier:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="model-management">
      <div className="model-header">
        <div className="model-actions" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="supplier-logo">{getSupplierLogo(selectedSupplier)}</span>
            {selectedSupplier.name}
          </h3>

          <button
            className="btn"
            onClick={(e) => {
              e.stopPropagation();
              handleEditSupplier(selectedSupplier);
            }}
            title="编辑供应商"
            style={{
              padding: '3px 6px',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ✏️
          </button>
          <button
            className="btn"
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteSupplier(selectedSupplier);
            }}
            title="删除供应商"
            style={{
              padding: '3px 6px',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            🗑️
          </button>
        </div>
      </div>

      {/* 供应商详情面板 */}
      <div className="supplier-info-panel panel">
        <h4></h4>
        <div className="supplier-info-grid">
          <div className="info-item">
            <label>描述:</label>
            <span className="info-value">{selectedSupplier.description || '未提供描述'}</span>
          </div>
          <div className="info-item">
            <label>官网:</label>
            <span className="info-value">
              {selectedSupplier.website ? (
                <a href={selectedSupplier.website} target="_blank" rel="noopener noreferrer" className="external-link">
                  访问官网
                </a>
              ) : '未设置'}
            </span>
          </div>
          <div className="info-item">
            <label>API地址:</label>
            <span className="info-value">{selectedSupplier.apiUrl ? (
                <a href={selectedSupplier.apiUrl} target="_blank" rel="noopener noreferrer" className="external-link">
                  {selectedSupplier.apiUrl}
                </a>
              ) : '未设置'}</span>
          </div>
          <div className="info-item">
            <label>API密钥:</label>
            <span className="info-value api-key">{formatApiKey(selectedSupplier.api_key)}</span>
          </div>
          <div className="info-item">
            <label>API文档:</label>
            <span className="info-value">
              {selectedSupplier.api_docs ? (
                <a href={selectedSupplier.api_docs} target="_blank" rel="noopener noreferrer" className="external-link">
                  {selectedSupplier.api_docs}
                </a>
              ) : '未设置'}
            </span>
          </div>
          <div className="info-item">
            <label>供应商类型:</label>
            <span className="info-value">{selectedSupplier.is_domestic ? '国内供应商' : '国际供应商'}</span>
          </div>
          <div className="info-item">
            <label>启用状态:</label>
            <span className="info-value">
              {selectedSupplier.is_active === false ? (
                <span style={{ color: '#e74c3c', fontWeight: '500' }}>未启用</span>
              ) : (
                <span style={{ color: '#27ae60', fontWeight: '500' }}>已启用</span>
              )}
              <label className="toggle-switch" title={selectedSupplier.is_active ? '点击停用' : '点击启用'}>
                <input
                  type="checkbox"
                  checked={selectedSupplier.is_active}
                  onClick={(e) => {
                    e.stopPropagation();
                    // 直接在组件内部定义切换逻辑，避免函数作用域问题
                    const toggleStatus = async () => {
                      try {
                        setSaving(true);
                        const newStatus = !selectedSupplier.is_active;
                        const confirmation = newStatus
                          ? `确定要启用供应商 "${selectedSupplier.name}" 吗？`
                          : `确定要停用供应商 "${selectedSupplier.name}" 吗？`;

                        if (!window.confirm(confirmation)) {
                          return;
                        }

                        // 调用专门的状态更新方法，只更新is_active字段
                        await api.supplierApi.updateSupplierStatus(selectedSupplier.id, newStatus);

                        if (onSupplierUpdate) {
                          setTimeout(() => onSupplierUpdate(), 0);
                        }

                        console.log(`供应商状态已${newStatus ? '启用' : '停用'}: ${selectedSupplier.name}`);
                      } catch (err) {
                        // 提供更详细的错误信息
                        const errorMessage = err.message || '网络连接错误，请检查后端服务是否运行';
                        setError(`更新供应商状态失败: ${errorMessage}`);
                        console.error('Failed to toggle supplier status:', err);
                        // 可以考虑在这里添加一个toast通知或其他用户反馈机制
                      } finally {
                        setSaving(false);
                      }
                    };
                    toggleStatus();
                  }}
                  onChange={(e) => e.stopPropagation()} // 防止意外触发
                  disabled={saving}
                />
                <span className="toggle-slider"></span>
              </label>
            </span>
          </div>
          {selectedSupplier.created_at && (
            <div className="info-item">
              <label>创建时间:</label>
              <span className="info-value">{new Date(selectedSupplier.created_at).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>

      {/* 新增模型功能已移至模态对话框 */}

      {/* 模型列表 */}
      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <div className="model-list panel">
          <h4>模型列表</h4>        <button
            className="btn btn-primary"
            onClick={handleAddModelClick}
            disabled={saving}
          >
            添加模型
          </button>
          <div className="model-items">
            {currentModels.length === 0 ? (
              <p className="empty-message">该供应商暂无模型，请添加模型</p>
            ) : (
              currentModels.map(model => (
                <div key={model.id} className={`model-item ${model.isDefault ? 'default' : ''}`}>
                  <div className="model-info">
                    <div className="model-header-info">
                      <span className="model-name">{model.name}</span>
                      {model.isDefault && <span className="model-default-tag">默认</span>}
                    </div>
                    <div className="model-desc">{model.description}</div>
                    <div className="model-meta">
                      <span className="context-window">上下文窗口: {model.contextWindow}</span>
                    </div>
                  </div>

                  <div className="model-actions">
                    {!model.isDefault && (
                      <button
                        className="btn btn-secondary btn-small"
                        onClick={() => handleSetDefault(model.id)}
                        disabled={saving}
                      >
                        设为默认
                      </button>
                    )}
                    <button
                      className="btn btn-secondary btn-small"
                      onClick={() => handleEditModelClick(model)}
                      disabled={saving}
                    >
                      编辑
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
              ))
            )}
          </div>
        </div>
      )}

      {/* 编辑模型功能已移至模态对话框 */}
      {/* 供应商模态窗口 */}
      <SupplierModal
        isOpen={isSupplierModalOpen}
        onClose={handleCloseSupplierModal}
        onSave={handleSaveSupplier}
        supplier={currentSupplier}
        mode={supplierModalMode}
      />
      
      {/* 模型模态窗口 */}
      <ModelModal
        isOpen={isModelModalOpen}
        onClose={handleCloseModelModal}
        onSave={handleSaveModelData}
        model={editingModel}
        mode={modelModalMode}
        isFirstModel={currentModels.length === 0}
      />
    </div>
  );
};

export default ModelManagement;