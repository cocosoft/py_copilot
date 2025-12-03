import React, { useState, useEffect } from 'react';
import ModelModal from './ModelModal';
import ModelParameterModal from './ModelParameterModal';
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

  // 当选择的供应商改变时，加载对应模型列表
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
    } finally {
      setLoading(false);
    }
  };

  // 添加模型
  const handleAddModelClick = () => {
    setEditingModel(null);
    setModelModalMode('add');
    setIsModelModalOpen(true);
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
  const handleSaveModelData = async (modelData) => {
    try {
      setSaving(true);
      if (modelModalMode === 'add') {
        await api.modelApi.create(selectedSupplier.id, modelData);
        setSuccess('模型添加成功');
      } else {
        await api.modelApi.update(selectedSupplier.id, editingModel.id, modelData);
        setSuccess('模型更新成功');
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
      console.error('加载模型参数失败:', err);
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
      console.error('保存参数失败:', err);
      setError('保存参数失败');
    } finally {
      setSaving(false);
      setIsParameterModalOpen(false);
      setSuccess(null);
    }
  };

  const handleDeleteParameter = async (parameterId) => {
    if (window.confirm('确定要删除这个参数吗？')) {
      try {
        setSaving(true);
        await api.modelApi.deleteParameter(selectedSupplier.id, selectedModel.id, parameterId);
        setSuccess('参数删除成功');
        loadModelParameters(selectedModel.id);
      } catch (err) {
        console.error('删除参数失败:', err);
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
        />
      </div>

      {/* 供应商选择和模型管理界面 */}
      {selectedModel ? (
        <div className="model-parameters-section">
          <div className="section-header">
            <h2>{selectedModel.name} - 参数管理</h2>
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
                  {modelParameters.map((param) => (
                    <tr key={param.id}>
                      <td>{param.parameter_name}</td>
                      <td>{param.parameter_value}</td>
                      <td>{param.parameter_type}</td>
                      <td>{param.default_value}</td>
                      <td>{param.description}</td>
                      <td>{param.is_required ? '是' : '否'}</td>
                      <td>
                        <div className="parameter-actions">
                          <button
                            className="btn btn-secondary btn-small"
                            onClick={() => handleEditParameterClick(param)}
                            disabled={saving}
                          >
                            编辑
                          </button>
                          <button
                            className="btn btn-danger btn-small"
                            onClick={() => handleDeleteParameter(param.id)}
                            disabled={saving}
                          >
                            删除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="model-management-section">
          {/* 模型列表 */}
          <div className="model-section">
            <div className="section-header">
              <h2>模型列表</h2>
              <button
                className="btn btn-primary"
                onClick={() => handleAddModelClick()}
                disabled={saving || !selectedSupplier}
              >
                添加模型
              </button>
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
                      <h3 className="model-name">{model.name}</h3>
                      {model.is_default && <span className="default-badge">默认</span>}
                    </div>
                    <div className="model-desc">{model.description}</div>
                    <div className="model-meta">
                      <span className="context-window">上下文窗口: {model.contextWindow}</span>
                    </div>

                    <div className="model-actions">
                      {!model.is_default && (
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
                        className="btn btn-success btn-small"
                        onClick={() => handleViewParameters(model)}
                        disabled={saving}
                      >
                        管理参数
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
    </div>
  );
};

export default ModelManagement;