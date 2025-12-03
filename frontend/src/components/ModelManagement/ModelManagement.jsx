import React, { useState, useEffect } from 'react';
import ModelModal from './ModelModal';
import SupplierDetail from '../SupplierManagement/SupplierDetail';
import '../../styles/ModelManagement.css';
import api from '../../utils/api';

const ModelManagement = ({ selectedSupplier, onSupplierSelect, onSupplierUpdate }) => {
  const [currentModels, setCurrentModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentModel, setCurrentModel] = useState(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(null); // 成功消息状态
  // 供应商相关状态已移至SupplierDetail组件中
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

        try {
          setSaving(true);
          console.log('创建默认模型:', defaultModel);
          // 确保使用整数ID
          await api.modelApi.create(selectedSupplier.id, defaultModel);
          await loadModels();
        } catch (error) {
          console.error('Failed to add default model:', error);
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
      console.log('🔄 开始加载供应商模型列表，供应商ID:', selectedSupplier.id);
      // 使用selectedSupplier.id作为参数调用更新后的API方法
      const result = await api.modelApi.getBySupplier(selectedSupplier.id);
      
      // 从结果中提取models数组
      const models = result.models || [];
      console.log('✅ 成功加载到模型列表，数量:', models.length);
      setCurrentModels(models); // 使用models数组而不是整个返回对象
    } catch (err) {
      const errorMessage = err.message || '加载模型失败';
      console.error('❌ 加载模型失败:', errorMessage);
      setError(`加载模型失败: ${errorMessage}`);
      
      // 降级处理：如果是DeepSeek供应商，创建默认模型
      if (selectedSupplier.key === 'deepseek') {
        console.log('⚠️ 降级处理：为DeepSeek供应商创建默认模型');
        const defaultModel = {
          id: 'deepseek-chat',
          model_id: 'deepseek-chat',
          name: 'DeepSeek Chat',
          description: 'DeepSeek的默认聊天模型',
          contextWindow: 8000,
          isDefault: true,
          supplier_id: selectedSupplier.id,
          modelType: 'chat',
          maxTokens: 1000,
          is_active: true
        };
        setCurrentModels([defaultModel]);
      }
    } finally {
      setLoading(false);
    }
  };

  // 设置默认模型
  const handleSetDefault = async (modelId) => {
    if (!selectedSupplier || saving) return;

    try {
      setSaving(true);
      console.log('🔄 设置默认模型，供应商ID:', selectedSupplier.id, '模型ID:', modelId);
      // 使用selectedSupplier.id调用更新后的API方法
      await api.modelApi.setDefault(selectedSupplier.id, modelId);
      
      // 更新本地状态
      console.log('✅ 默认模型设置成功');
      const updatedModels = currentModels.map(model => ({
        ...model,
        isDefault: model.id === modelId
      }));
      setCurrentModels(updatedModels);
    } catch (err) {
      const errorMessage = err.message || '设置默认模型失败';
      console.error('❌ 设置默认模型失败:', errorMessage);
      setError(`设置默认模型失败: ${errorMessage}`);
      
      // 降级处理：本地更新
      console.log('⚠️ 降级处理：本地设置默认模型');
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

  // 保存模型数据（新增或更新）
  const handleSaveModelData = async (modelData) => {
    if (!selectedSupplier || saving) return;

    try {
      setSaving(true);
      
      // 根据模态框模式调用不同的API方法
      if (modelModalMode === 'add') {
        console.log('🔄 添加新模型，供应商ID:', selectedSupplier.id, '模型数据:', modelData);
        // 使用API的create方法并传入已格式化的数据
        await api.modelApi.create(selectedSupplier.id, modelData);
        console.log('✅ 模型添加成功');
      } else {
        console.log('🔄 更新模型，供应商ID:', selectedSupplier.id, '模型ID:', modelData.id);
        // 使用API的update方法
        await api.modelApi.update(selectedSupplier.id, modelData.id, modelData);
        console.log('✅ 模型更新成功');
      }
      
      // 重新加载模型列表
      await loadModels();
      // 关闭模态框
      handleCloseModelModal();
      // 显示成功消息
      setSuccess(modelModalMode === 'add' ? '模型创建成功' : '模型更新成功');
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      const action = modelModalMode === 'add' ? '添加' : '更新';
      const errorMessage = err.message || `${action}模型失败`;
      console.error(`❌ ${action}模型失败:`, errorMessage);
      setError(`模型${action}失败: ${errorMessage}`);
      
      // 降级处理：本地更新
      console.log('⚠️ 降级处理：本地更新模型数据');
      if (modelModalMode === 'add') {
        const localModel = {
          id: modelData.id || String(Date.now()),
          model_id: modelData.id,
          name: modelData.name || '未命名模型',
          description: modelData.description || '暂无描述',
          contextWindow: modelData.contextWindow || 8000,
          isDefault: modelData.isDefault || currentModels.length === 0,
          supplier_id: selectedSupplier.id,
          modelType: modelData.modelType || 'chat',
          maxTokens: modelData.maxTokens || 1000,
          is_active: true
        };
        setCurrentModels([...currentModels, localModel]);
      } else {
        const updatedModels = currentModels.map(model =>
          model.id === modelData.id ? {
            ...model,
            ...modelData
          } : model
        );
        setCurrentModels(updatedModels);
      }
      
      // 关闭模态框
      handleCloseModelModal();
    } finally {
      setSaving(false);
    }
  };

  // 添加新模型已整合到handleSaveModelData方法中，通过模态框处理

  // 删除模型
  const handleDeleteModel = async (modelId) => {
    if (!selectedSupplier || saving) return;

    if (!window.confirm('确定要删除这个模型吗？')) {
      return;
    }

    try {
      setSaving(true);
      console.log('🔄 删除模型，供应商ID:', selectedSupplier.id, '模型ID:', modelId);
      // 使用selectedSupplier.id调用更新后的API方法
      await api.modelApi.delete(selectedSupplier.id, modelId);
      console.log('✅ 模型删除成功');
      await loadModels();
    } catch (err) {
      const errorMessage = err.message || '删除模型失败';
      console.error('❌ 删除模型失败:', errorMessage);
      setError(`删除模型失败: ${errorMessage}`);
      
      // 降级处理：本地删除
      console.log('⚠️ 降级处理：本地删除模型');
      const modelToDelete = currentModels.find(model => model.id === modelId);
      const updatedModels = currentModels.filter(model => model.id !== modelId);

      // 如果删除的是默认模型，将第一个模型设为默认
      if (modelToDelete?.isDefault && updatedModels.length > 0) {
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
          {success && (
            <div className="success">{success}</div>
          )}
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

  // 供应商相关函数已移至SupplierDetail组件中
  // 为显示供应商logo保留必要的辅助函数
  const getSupplierLogo = (supplier) => {
    if (!supplier) return null;
    
    // 根据供应商key返回简单的logo或图标
    const logoStyles = {
      width: '24px',
      height: '24px',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f0f0f0',
      borderRadius: '4px',
      fontSize: '14px',
      fontWeight: 'bold'
    };
    
    // 返回供应商名称的首字母作为简单logo
    return <span style={logoStyles}>{supplier.name.charAt(0)}</span>;
  };

  // 供应商相关处理函数已移至SupplierDetail组件中
  
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

  // 供应商相关函数和处理逻辑已移至SupplierDetail组件中

  return (
    <div className="model-management">
      {/* 使用SupplierDetail组件显示供应商详情 */}
      <SupplierDetail 
        selectedSupplier={selectedSupplier} 
        onSupplierUpdate={onSupplierUpdate} 
        onSupplierSelect={onSupplierSelect}
      />

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
      {/* 供应商相关的模态窗口已移至SupplierDetail组件中 */}
      
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