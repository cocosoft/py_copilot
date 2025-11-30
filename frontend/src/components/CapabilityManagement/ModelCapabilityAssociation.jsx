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
      // 由于modelApi.getAll需要supplierId参数，但我们需要所有模型
      // 这里使用null或空字符串作为默认值，并确保返回的是数组
      let response = await modelApi.getAll(null);
      // 确保response是数组类型
      if (!Array.isArray(response)) {
        response = [];
      }
      setModels(response);
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
      const response = await capabilityApi.getAll();
        // 确保response是数组类型
        const capabilitiesData = Array.isArray(response) ? response : [];
        setCapabilities(capabilitiesData);
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
      const response = await capabilityApi.getCapabilitiesByModel(modelId);
        // 确保response是数组类型
        const modelCapabilitiesData = Array.isArray(response) ? response : [];
        setModelCapabilities(modelCapabilitiesData);
    } catch (error) {
      console.error('获取模型能力关联失败:', error);
      setError('获取模型能力关联失败');
    } finally {
      setLoading(false);
    }
  };

  // 组件初始化
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
  const handleRemoveCapability = async (associationId) => {
    setUpdateLoading(true);
    try {
      // 注意：根据后端实现，我们需要先获取association_id
      // 这里暂时使用模拟的删除方式
      await capabilityApi.removeCapabilityFromModel(selectedModel.id, null);
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
    const associatedCapabilityIds = modelCapabilities.map(mc => mc.capability_id);
    return capabilities.filter(cap => !associatedCapabilityIds.includes(cap.id));
  };

  // 关联的能力表格列
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
      key: 'action',
      render: (_, record) => (
        <Button
          danger
          icon={<MinusOutlined />}
          onClick={() => handleRemoveCapability(record.id)}
          loading={updateLoading}
        >
          移除
        </Button>
      )
    }
  ];

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
          <label htmlFor="model-select">选择模型 *</label>
          <select
            id="model-select"
            onChange={(e) => handleModelChange(Number(e.target.value))}
            value={selectedModel?.id || ''}
            className="form-control"
          >
            <option value="">请选择一个模型</option>
            {models.map(model => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
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
                        <td>{record.capability?.name}</td>
                        <td>{record.capability?.display_name}</td>
                        <td>{record.capability?.capability_type}</td>
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