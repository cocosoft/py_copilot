import React, { useState, useEffect } from 'react';
import { modelApi } from '../../utils/api/modelApi';
import { capabilityApi } from '../../utils/api/capabilityApi';

const ModelCapabilityAssociation = () => {
  const [models, setModels] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [modelCapabilities, setModelCapabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [error, setError] = useState(null);

  // 加载所有模型
  const fetchModels = async () => {
    try {
      // modelApi.getAll返回的是一个包含models数组的对象
      let response = await modelApi.getAll();
      // 确保response.models是数组类型
      const modelsData = Array.isArray(response.models) ? response.models : [];
      
      // 添加调试信息，查看模型数据结构
      console.log('获取的模型列表:', modelsData);
      console.log('第一个模型的供应商信息:', modelsData[0]?.supplier);
      
      setModels(modelsData);
    } catch (error) {
      console.error('获取模型列表失败:', error);
      setError('获取模型列表失败');
      // 出错时设置为空数组，避免map错误
      setModels([]);
    }
  };

  // 加载所有能力
  const fetchCapabilities = async () => {
    try {
      const capabilitiesData = await capabilityApi.getAll();
      // 直接使用capabilityApi返回的已经处理好的数据
      setCapabilities(Array.isArray(capabilitiesData) ? capabilitiesData : []);
    } catch (error) {
      console.error('获取能力列表失败:', error);
      setError('获取能力列表失败');
      // 出错时设置为空数组，避免map错误
      setCapabilities([]);
    }
  };

  // 加载模型能力关联
  const fetchModelCapabilities = async (modelId) => {
    if (!modelId) return;
    
    setLoading(true);
    try {
      const modelCapabilitiesData = await capabilityApi.getCapabilitiesByModel(modelId);
      // 直接使用capabilityApi返回的已经处理好的数据
      setModelCapabilities(Array.isArray(modelCapabilitiesData) ? modelCapabilitiesData : []);
    } catch (error) {
      console.error('获取模型能力关联失败:', error);
      setError('获取模型能力关联失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载数据
  useEffect(() => {
    fetchModels();
    fetchCapabilities();
  }, []);

  // 模型选择变化
  const handleModelChange = (modelId) => {
    const model = models.find(m => m.id === modelId);
    setSelectedModel(model);
    fetchModelCapabilities(modelId);
  };

  // 添加能力到模型
  const handleAddCapability = async (capabilityId, configuration) => {
    if (!selectedModel) return;

    setUpdateLoading(true);
    try {
      const associationData = {
        model_id: selectedModel.id,
        capability_id: capabilityId,
        config: configuration
      };
      await capabilityApi.addCapabilityToModel(associationData);
      setError('能力添加成功');
      setTimeout(() => setError(null), 3000);
      fetchModelCapabilities(selectedModel.id);
    } catch (error) {
      console.error('添加能力失败:', error);
      setError('添加失败：' + (error.message || '未知错误'));
    } finally {
      setUpdateLoading(false);
    }
  };

  // 从模型移除能力
  const handleRemoveCapability = async (capabilityId) => {
    if (!selectedModel) return;
    
    // 确认操作
    const confirmRemove = window.confirm('确定要移除该能力吗？');
    if (!confirmRemove) return;
    
    setUpdateLoading(true);
    try {
      // 调用API移除能力关联
      await capabilityApi.removeCapabilityFromModel(selectedModel.id, capabilityId);
      setError('能力移除成功');
      setTimeout(() => setError(null), 3000);
      fetchModelCapabilities(selectedModel.id);
    } catch (error) {
      console.error('移除能力失败:', error);
      setError('移除失败：' + (error.message || '未知错误'));
    } finally {
      setUpdateLoading(false);
    }
  };

  // 更新模型能力配置
  const handleUpdateConfiguration = async (associationId, configuration) => {
    setUpdateLoading(true);
    try {
      // 注意：后端可能没有提供此功能，暂时注释掉
      // await capabilityApi.updateModelCapabilityAssociation(selectedModel.id, null, { config: configuration });
      setError('配置更新功能暂未实现');
      setTimeout(() => setError(null), 3000);
    } catch (error) {
      console.error('更新配置失败:', error);
      setError('更新失败：' + (error.message || '未知错误'));
    } finally {
      setUpdateLoading(false);
    }
  };

  // 获取模型尚未关联的能力
  const getAvailableCapabilities = () => {
    const associatedCapabilityIds = modelCapabilities.map(mc => mc.id);
    return capabilities.filter(cap => !associatedCapabilityIds.includes(cap.id));
  };

  // 关联的能力表格列定义（仅用于参考，实际使用原生表格）
  const associationColumns = [
    {
      title: '能力名称',
      dataIndex: ['capability', 'name'],
      key: 'capability_name'
    },
    {
      title: '显示名称',
      dataIndex: ['capability', 'display_name'],
      key: 'capability_display_name'
    },
    {
      title: '能力类型',
      dataIndex: ['capability', 'capability_type'],
      key: 'capability_type'
    },
    {
      title: '操作',
      key: 'action'
    }
  ];

  // 添加自定义下拉列表状态
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredModels, setFilteredModels] = useState(models);

  // 当输入框获得焦点时显示下拉列表
  const handleFocus = () => {
    setFilteredModels(models);
    setShowDropdown(true);
  };

  // 当输入框失去焦点时隐藏下拉列表
  const handleBlur = () => {
    setTimeout(() => setShowDropdown(false), 200); // 延迟隐藏，以便点击选项时能触发事件
  };

  // 处理输入框变化
  const handleInputChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    // 过滤模型列表
    if (value) {
      const filtered = models.filter(model => 
        model.name.toLowerCase().includes(value.toLowerCase()) ||
        (model.displayName && model.displayName.toLowerCase().includes(value.toLowerCase()))
      );
      setFilteredModels(filtered);
    } else {
      setFilteredModels(models);
    }
  };

  // 选择模型
  const handleSelectModel = (model) => {
    setSearchTerm(model.displayName ? `${model.displayName} (${model.name})` : model.name);
    handleModelChange(model.id);
    setShowDropdown(false);
  };

  return (
    <div className="model-capability-association">
      <h2>模型能力关联管理</h2>
      
      {error && (
        <div className="alert alert-info">
          {error}
          <button onClick={() => setError(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      <div className="card">
        <div className="form-group">
          <label htmlFor="model-input">选择或输入模型名称 *</label>
          <div className="model-datalist-container">
            <input
              type="text"
              id="model-input"
              value={searchTerm}
              onFocus={handleFocus}
              onBlur={handleBlur}
              onChange={handleInputChange}
              placeholder="输入模型名称或选择"
              className="form-control"
            />
            {showDropdown && filteredModels.length > 0 && (
              <div className="custom-datalist-dropdown">
                {filteredModels.map(model => (
                  <div
                    key={model.id}
                    className="custom-datalist-option"
                    onClick={() => handleSelectModel(model)}
                  >
                    {model.displayName ? `${model.displayName} (${model.name})` : model.name} - {model.supplierDisplayName || model.supplierName || '未知供应商'}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedModel && (
        <>
          <div style={{ marginTop: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3>已关联的能力</h3>
              <button
                onClick={() => fetchModelCapabilities(selectedModel.id)}
                disabled={loading}
                className="btn btn-secondary"
              >
                {loading ? '刷新中...' : '刷新'}
              </button>
            </div>
            
            {loading ? (
              <div>加载中...</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>能力名称</th>
                    <th>显示名称</th>
                    <th>能力类型</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {modelCapabilities.length === 0 ? (
                    <tr>
                      <td colSpan={4} style={{ textAlign: 'center' }}>暂无关联的能力</td>
                    </tr>
                  ) : (
                    modelCapabilities.map(record => (
                      <tr key={record.id}>
                        <td>{record.name}</td>
                        <td>{record.display_name}</td>
                        <td>{record.capability_type}</td>
                        <td>
                          <button
                            onClick={() => handleRemoveCapability(record.id)}
                            disabled={updateLoading}
                            className="btn btn-danger btn-small"
                          >
                            {updateLoading ? '移除中...' : '移除'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}
          </div>

          <hr />

          <div style={{ marginTop: 16 }}>
            <h3>添加新能力</h3>
            <div className="card">
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
                {getAvailableCapabilities().length === 0 ? (
                  <p>所有能力已关联到此模型</p>
                ) : (
                  getAvailableCapabilities().map(capability => (
                    <div
                      key={capability.id}
                      className="capability-card"
                    >
                      <h4>{capability.display_name || capability.name}</h4>
                      <p className="text-sm">能力类型: {capability.capability_type}</p>
                      <p>{capability.description || '无描述'}</p>
                      <button
                        onClick={() => handleAddCapability(capability.id, {})}
                        disabled={updateLoading}
                        className="btn btn-primary"
                      >
                        {updateLoading ? '添加中...' : '添加到模型'}
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelCapabilityAssociation;