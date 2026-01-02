import React, { useState, useEffect, useCallback } from 'react';
import modelApi from '../../utils/api/modelApi';
import { capabilityApi } from '../../utils/api/capabilityApi';
import ModelSelectDropdown from '../ModelManagement/ModelSelectDropdown';
import { request } from '../../utils/apiUtils';

// 定义全局样式
const globalStyles = `
  .model-capability-association {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #333;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .modal-large {
    max-width: 90vw;
    width: 1200px;
    max-height: 90vh;
  }
  
  .modal-body {
    max-height: calc(90vh - 120px);
    overflow-y: auto;
  }
  
  .association-title {
    color: #1e88e5;
    font-size: 24px;
    margin-bottom: 20px;
    font-weight: 600;
    text-align: center;
  }
  
  .modal-title {
    color: #1e88e5;
    font-size: 20px;
    margin: 0;
    font-weight: 600;
  }
  
  .card {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    padding: 20px;
    margin-bottom: 20px;
    transition: box-shadow 0.3s ease;
  }
  
  .card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.12);
  }
  
  .form-group {
    margin-bottom: 20px;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #555;
  }
  
  .input-group {
    display: flex;
    gap: 10px;
    align-items: center;
  }
  
  .form-control {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    transition: border-color 0.3s;
  }
  
  .form-control:focus {
    outline: none;
    border-color: #409eff;
    box-shadow: 0 0 5px rgba(64, 158, 255, 0.2);
  }
  
  .btn {
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
    border: none;
    outline: none;
    text-decoration: none;
    display: inline-block;
    text-align: center;
  }
  
  .btn-primary {
    background-color: #409eff;
    color: white;
  }
  
  .btn-primary:hover {
    background-color: #66b1ff;
  }
  
  .btn-secondary {
    background-color: #ffffff;
    color: #606266;
    border: 1px solid #dcdfe6;
  }
  
  .btn-secondary:hover {
    color: #409eff;
    border-color: #c6e2ff;
  }
  
  .btn-danger {
    background-color: #f56c6c;
    color: white;
  }
  
  .btn-danger:hover {
    background-color: #f78989;
  }
  
  .btn-small {
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .alert {
    padding: 12px 16px;
    border-radius: 4px;
    margin-bottom: 16px;
    position: relative;
  }
  
  .alert-error {
    background-color: #fef0f0;
    color: #f56c6c;
    border: 1px solid #fde2e2;
  }
  
  .alert-success {
    background-color: #f0f9eb;
    color: #67c23a;
    border: 1px solid #e1f3d8;
  }
  
  .section-title {
    color: #1e88e5;
    font-size: 18px;
    margin-bottom: 16px;
    font-weight: 600;
  }
  
  .text-muted {
    color: #909399;
    font-size: 12px;
  }
  
  .table-container {
    overflow-x: auto;
    margin-top: 16px;
  }
  
  .capability-table {
    width: 100%;
    border-collapse: collapse;
    background-color: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  }
  
  .capability-table th,
  .capability-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ebeef5;
  }
  
  .capability-table th {
    background-color: #f5f7fa;
    color: #606266;
    font-weight: 600;
  }
  
  .capability-table tr:hover {
    background-color: #f5f7fa;
  }
  
  .capability-card {
    border: 1px solid #ebeef5;
    border-radius: 6px;
    padding: 16px;
    background-color: white;
    transition: all 0.3s ease;
  }
  
  .capability-card:hover {
    border-color: #409eff;
    box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  }
  
  .capability-type-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 12px;
    background-color: #f0f9eb;
    color: #67c23a;
  }
  
  .status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 12px;
  }
  
  .status-badge.active {
    background-color: #f0f9eb;
    color: #67c23a;
  }
  
  .status-badge.inactive {
    background-color: #fef0f0;
    color: #f56c6c;
  }
  
  .pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
  }
  
  .page-info {
    color: #606266;
    font-size: 14px;
  }
  
  .search-filter {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    align-items: center;
  }
  
  .search-filter .form-control {
    flex: 1;
  }
  
  .text-sm {
    font-size: 12px;
    color: #606266;
  }
`;

const ModelCapabilityAssociation = ({ isOpen, onClose, model: presetModel }) => {
  const [models, setModels] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [modelCapabilities, setModelCapabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // 判断是否为模态模式
  const isModalMode = isOpen !== undefined;
  
  // 分页和筛选状态
  const [modelsPage, setModelsPage] = useState(1);
  const [capabilitiesPage, setCapabilitiesPage] = useState(1);
  const [capabilitiesPerPage, setCapabilitiesPerPage] = useState(12);
  const [modelSearch, setModelSearch] = useState('');
  const [capabilitySearch, setCapabilitySearch] = useState('');
  const [capabilityFilter, setCapabilityFilter] = useState('all');

  // 筛选后的模型列表
  const getFilteredModels = useCallback(() => {
    return models.filter(model =>
      model.model_name?.toLowerCase().includes(modelSearch.toLowerCase()) ||
      model.id?.toString().includes(modelSearch)
    );
  }, [models, modelSearch]);

  // 筛选后的能力列表
  const getFilteredCapabilities = useCallback(() => {
    return capabilities.filter(capability =>
      (capability.display_name?.toLowerCase().includes(capabilitySearch.toLowerCase()) ||
       capability.name?.toLowerCase().includes(capabilitySearch.toLowerCase())) &&
      (capabilityFilter === 'all' || capability.capability_type === capabilityFilter)
    );
  }, [capabilities, capabilitySearch, capabilityFilter]);

  // 获取当前模型未关联的能力
  const getAvailableCapabilities = useCallback(() => {
    if (!selectedModel) return [];
    
    const associatedCapabilityIds = new Set(modelCapabilities.map(mc => mc.capability_id));
    return getFilteredCapabilities().filter(cap => !associatedCapabilityIds.has(cap.id));
  }, [selectedModel, modelCapabilities, getFilteredCapabilities]);

  // 获取分页后的可用能力
  const getPagedAvailableCapabilities = () => {
    const available = getAvailableCapabilities();
    const startIndex = (capabilitiesPage - 1) * capabilitiesPerPage;
    const endIndex = startIndex + capabilitiesPerPage;
    return available.slice(startIndex, endIndex);
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
  

  // 加载模型列表
  const fetchModels = async () => {
    try {
      setLoading(true);
      const response = await modelApi.getAll();
      
      // 处理多种响应格式
      if (response.success) {
        // 格式: {success: true, models: [...]}
        setModels(response.models || []);
      } else if (Array.isArray(response)) {
        // 格式: [...]
        setModels(response);
      } else if (response.models && Array.isArray(response.models)) {
        // 格式: {models: [...], total: n}
        setModels(response.models);
      } else {
        // 其他情况都视为错误
        console.warn('获取模型列表格式不符合预期:', response);
        setError('获取模型列表失败：格式错误');
      }
    } catch (err) {
      setError('获取模型列表时发生错误');
      console.error('获取模型列表错误:', err);
    } finally {
      setLoading(false);
    }
  };

  // 加载能力列表
  const fetchCapabilities = async () => {
    try {
      const response = await capabilityApi.getAll();
      
      // 处理两种响应格式：带success字段的对象和直接数组
      if (response.success) {
        setCapabilities(response.capabilities || []);
      } else if (Array.isArray(response)) {
        // 直接返回数组的情况
        setCapabilities(response);
      } else {
        // 其他情况都视为错误
        console.warn('获取能力列表格式不符合预期:', response);
        setError('获取能力列表失败：格式错误');
      }
    } catch (err) {
      setError('获取能力列表时发生错误');
      console.error('获取能力列表错误:', err);
    }
  };

  // 加载模型能力关联
  const fetchModelCapabilities = async (modelId) => {
    try {
      setLoading(true);
      const response = await capabilityApi.getModelCapabilities(modelId);
      
      // 处理多种响应格式
      let associations = [];
      if (response.success) {
        // 格式: {success: true, data: [...]}
        associations = response.data || [];
      } else if (Array.isArray(response)) {
        // 格式: [...]
        associations = response;
      } else if (response.data && Array.isArray(response.data)) {
        // 格式: {data: [...]}
        associations = response.data;
      } else {
        // 其他情况视为空数据（不是错误）
        console.warn('获取模型能力关联格式不符合预期:', response);
        associations = [];
      }
      
      // 确保返回的是关联对象数组（包含capability字段）
      setModelCapabilities(associations);
    } catch (err) {
      // 网络错误或其他异常才设置错误
      setError('获取模型能力关联时发生错误');
      console.error('获取模型能力关联错误:', err);
      setModelCapabilities([]);
    } finally {
      setLoading(false);
    }
  };

  // 添加能力到模型
  const handleAddCapability = async (capabilityId, additionalData = {}) => {
    if (!selectedModel) return;
    
    try {
      setUpdateLoading(true);
      
      // 使用capabilityApi.addModelCapability方法而不是直接调用request
      const value = Object.keys(additionalData).length > 0 
        ? additionalData 
        : null;
      
      const response = await capabilityApi.addModelCapability(
        selectedModel.id,
        capabilityId,
        value
      );
      
      if (response && response.success) {
        setSuccess('能力添加成功');
        // 重新加载模型能力
        await fetchModelCapabilities(selectedModel.id);
      } else {
        // 对于409错误（关联已存在），不显示错误信息
        if (error && error.message && error.message.includes('409')) {
          setSuccess('该能力已关联到此模型');
        } else {
          setError(error.message || '添加能力失败');
        }
      }
    } catch (error) {
      // 对于409错误（关联已存在），不显示错误信息
      if (error && error.status === 409 || error.message && error.message.includes('409')) {
        setSuccess('该能力已关联到此模型');
      } else {
        setError('添加能力时发生错误: ' + error.message);
        console.error('添加能力错误:', error);
      }
    } finally {
      setUpdateLoading(false);
    }
  };

  // 从模型移除能力
  const handleRemoveCapability = async (modelCapabilityId) => {
    try {
      setUpdateLoading(true);
      const response = await capabilityApi.removeCapabilityFromModel(modelCapabilityId);
      
      if (response.success) {
        setSuccess('能力移除成功');
        // 重新加载模型能力
        if (selectedModel) {
          await fetchModelCapabilities(selectedModel.id);
        }
      } else {
        setError(response.message || '移除能力失败');
      }
    } catch (err) {
      setError('移除能力时发生错误');
      console.error('移除能力错误:', err);
    } finally {
      setUpdateLoading(false);
    }
  };

  // 初始化加载数据
  useEffect(() => {
    // 在非模态模式或未提供预设模型时，获取完整模型列表
    if (!isModalMode || !presetModel) {
      fetchModels();
    }
    // 总是获取能力列表
    fetchCapabilities();
  }, [isModalMode, presetModel]);

  // 如果提供了预设模型，自动选择它
  useEffect(() => {
    if (presetModel) {
      // 如果是在模态模式下且提供了预设模型，直接使用预设模型
      if (isModalMode) {
        setSelectedModel(presetModel);
        fetchModelCapabilities(presetModel.id);
      } else if (models.length > 0) {
        // 在页面模式下，从已加载的模型列表中查找匹配的模型
        const foundModel = models.find(m => m.id === presetModel.id);
        if (foundModel) {
          setSelectedModel(foundModel);
          fetchModelCapabilities(foundModel.id);
        }
      }
    }
  }, [presetModel, models, isModalMode]);

  // 模型选择变化
  const handleModelChange = (modelId) => {
    const model = models.find(m => m.id === modelId);
    setSelectedModel(model);
    fetchModelCapabilities(modelId);
  };

  // 渲染页面模式的内容
  const renderPageMode = () => (
    <div className="model-capability-association">
      <h2 className="association-title">模型能力关联管理</h2>
      
      {/* 注入样式 */}
      <style>{globalStyles}</style>
      
      {/* 消息提示 */}
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="btn btn-small">×</button>
        </div>
      )}
      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => setSuccess(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      {/* 模型选择 */}
      <div className="card">
        <div className="form-group">
          <label>选择模型 *</label>
          <div className="input-group">
            <input
              type="text"
              id="model-search"
              value={modelSearch}
              onChange={(e) => setModelSearch(e.target.value)}
              placeholder="搜索模型..."
              className="form-control"
            />
            <ModelSelectDropdown
              models={getFilteredModels()}
              selectedModel={selectedModel}
              onModelSelect={(model) => {
                setSelectedModel(model);
                fetchModelCapabilities(model.id);
              }}
              placeholder="-- 请选择模型 --"
            />
          </div>
          {getFilteredModels().length > 0 && (
            <small className="text-muted">共找到 {getFilteredModels().length} 个模型</small>
          )}
        </div>
      </div>

      {selectedModel && (
        <>
          {/* 已关联的能力 */}
          <div style={{ marginTop: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 className="section-title">已关联的能力</h3>
              <button
                onClick={() => fetchModelCapabilities(selectedModel.id)}
                disabled={loading}
                className="btn btn-secondary"
              >
                {loading ? '刷新中...' : '刷新'}
              </button>
            </div>
            
            <div className="table-container">
              <table className="capability-table">
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
                      <td colSpan="4" style={{ textAlign: 'center', padding: '20px' }}>
                        暂无关联的能力
                      </td>
                    </tr>
                  ) : (
                    modelCapabilities.map(modelCapability => (
                      <tr key={modelCapability.id}>
                        <td>{modelCapability.capability?.name || '-'}</td>
                        <td>{modelCapability.capability?.display_name || '-'}</td>
                        <td>
                          <span className={`capability-type-badge ${modelCapability.capability?.capability_type}`}>
                            {modelCapability.capability?.capability_type || '-'}
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={() => handleRemoveCapability(modelCapability.id)}
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
            </div>
          </div>

          {/* 可添加的能力 */}
          <div style={{ marginTop: 24 }}>
            <h3 className="section-title">可添加的能力</h3>
            
            <div className="search-filter">
              <input
                type="text"
                value={capabilitySearch}
                onChange={(e) => setCapabilitySearch(e.target.value)}
                placeholder="搜索能力..."
                className="form-control"
              />
              <select
                value={capabilityFilter}
                onChange={(e) => setCapabilityFilter(e.target.value)}
                className="form-control"
              >
                <option value="all">所有类型</option>
                {Array.from(new Set(capabilities.map(cap => cap.capability_type))).map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div className="card">
              {getAvailableCapabilities().length === 0 ? (
                <p>所有能力已关联到此模型</p>
              ) : (
                <>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 16 }}>
                    {getPagedAvailableCapabilities().map(capability => (
                      <div
                        key={capability.id}
                        className="capability-card"
                        style={{ flex: '1 1 calc(33.333% - 16px)', minWidth: '250px' }}
                      >
                        <h4>{capability.display_name || capability.name}</h4>
                        <p className="text-sm">能力类型: <span className={`capability-type-badge ${capability.capability_type}`}>{capability.capability_type}</span></p>
                        <p style={{ height: '60px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{capability.description || '无描述'}</p>
                        <button
                          onClick={() => handleAddCapability(capability.id, {})}
                          disabled={updateLoading}
                          className="btn btn-primary"
                          style={{ width: '100%' }}
                        >
                          {updateLoading ? '添加中...' : '添加到模型'}
                        </button>
                      </div>
                    ))}
                  </div>
                  
                  {/* 分页控件 */}
                  {getAvailableCapabilities().length > capabilitiesPerPage && (
                    <div className="pagination" style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '16px' }}>
                      <button
                        onClick={() => setCapabilitiesPage(prev => Math.max(prev - 1, 1))}
                        disabled={capabilitiesPage === 1}
                        className="btn btn-secondary"
                      >
                        上一页
                      </button>
                      <span className="page-info">
                        第 {capabilitiesPage} 页 / 共 {Math.ceil(getAvailableCapabilities().length / capabilitiesPerPage)} 页
                      </span>
                      <button
                        onClick={() => setCapabilitiesPage(prev => Math.min(prev + 1, Math.ceil(getAvailableCapabilities().length / capabilitiesPerPage)))}
                        disabled={capabilitiesPage >= Math.ceil(getAvailableCapabilities().length / capabilitiesPerPage)}
                        className="btn btn-secondary"
                      >
                        下一页
                      </button>
                      <select
                        value={capabilitiesPerPage}
                        onChange={(e) => {
                          setCapabilitiesPerPage(parseInt(e.target.value));
                          setCapabilitiesPage(1);
                        }}
                        className="form-control"
                        style={{ width: '80px' }}
                      >
                        <option value={6}>6条/页</option>
                        <option value={12}>12条/页</option>
                        <option value={24}>24条/页</option>
                        <option value={48}>48条/页</option>
                      </select>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );

  // 渲染模态模式的内容
  const renderModalMode = () => (
    <div className="modal-overlay">
      <div className="modal-content modal-large">
        <div className="modal-header">
          <h2 className="modal-title">
            模型能力关联管理 
            {selectedModel && (
              <span className="text-muted" style={{ fontSize: '14px', marginLeft: '10px' }}>
                - {selectedModel.model_name || selectedModel.name || `模型ID: ${selectedModel.id}`}
              </span>
            )}
          </h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        
        <div className="modal-body">
          {/* 消息提示 */}
          {error && (
            <div className="alert alert-error">
              {error}
              <button onClick={() => setError(null)} className="btn btn-small">×</button>
            </div>
          )}
          {success && (
            <div className="alert alert-success">
              {success}
              <button onClick={() => setSuccess(null)} className="btn btn-small">×</button>
            </div>
          )}
          
          {/* 模型选择 - 如果没有预设模型才显示 */}
          {!presetModel && (
            <div className="card">
              <div className="form-group">
                <label>选择模型 *</label>
                <div className="input-group">
                  <input
                    type="text"
                    id="model-search"
                    value={modelSearch}
                    onChange={(e) => setModelSearch(e.target.value)}
                    placeholder="搜索模型..."
                    className="form-control"
                  />
                  <ModelSelectDropdown
                    models={getFilteredModels()}
                    selectedModel={selectedModel}
                    onModelSelect={(model) => {
                      setSelectedModel(model);
                      fetchModelCapabilities(model.id);
                    }}
                    placeholder="-- 请选择模型 --"
                  />
                </div>
                {getFilteredModels().length > 0 && (
                  <small className="text-muted">共找到 {getFilteredModels().length} 个模型</small>
                )}
              </div>
            </div>
          )}

          {selectedModel && (
            <>
              {/* 已关联的能力 */}
              <div style={{ marginTop: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <h3 className="section-title">已关联的能力</h3>
                  <button
                    onClick={() => fetchModelCapabilities(selectedModel.id)}
                    disabled={loading}
                    className="btn btn-secondary"
                  >
                    {loading ? '刷新中...' : '刷新'}
                  </button>
                </div>
                
                <div className="table-container">
                  <table className="capability-table">
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
                          <td colSpan="4" style={{ textAlign: 'center', padding: '20px' }}>
                            暂无关联的能力
                          </td>
                        </tr>
                      ) : (
                        modelCapabilities.map(modelCapability => (
                          <tr key={modelCapability.id}>
                            <td>{modelCapability.capability?.name || '-'}</td>
                            <td>{modelCapability.capability?.display_name || '-'}</td>
                            <td>
                              <span className={`capability-type-badge ${modelCapability.capability?.capability_type}`}>
                                {modelCapability.capability?.capability_type || '-'}
                              </span>
                            </td>
                            <td>
                              <button
                                onClick={() => handleRemoveCapability(modelCapability.id)}
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
                </div>
              </div>

              {/* 可添加的能力 */}
              <div style={{ marginTop: 24 }}>
                <h3 className="section-title">可添加的能力</h3>
                
                <div className="search-filter">
                  <input
                    type="text"
                    value={capabilitySearch}
                    onChange={(e) => setCapabilitySearch(e.target.value)}
                    placeholder="搜索能力..."
                    className="form-control"
                  />
                  <select
                    value={capabilityFilter}
                    onChange={(e) => setCapabilityFilter(e.target.value)}
                    className="form-control"
                  >
                    <option value="all">所有类型</option>
                    {Array.from(new Set(capabilities.map(cap => cap.capability_type))).map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
                
                <div className="card">
                  {getAvailableCapabilities().length === 0 ? (
                    <p>所有能力已关联到此模型</p>
                  ) : (
                    <>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 16 }}>
                        {getPagedAvailableCapabilities().map(capability => (
                          <div
                            key={capability.id}
                            className="capability-card"
                            style={{ flex: '1 1 calc(33.333% - 16px)', minWidth: '250px' }}
                          >
                            <h4>{capability.display_name || capability.name}</h4>
                            <p className="text-sm">能力类型: <span className={`capability-type-badge ${capability.capability_type}`}>{capability.capability_type}</span></p>
                            <p style={{ height: '60px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{capability.description || '无描述'}</p>
                            <button
                              onClick={() => handleAddCapability(capability.id, {})}
                              disabled={updateLoading}
                              className="btn btn-primary"
                              style={{ width: '100%' }}
                            >
                              {updateLoading ? '添加中...' : '添加到模型'}
                            </button>
                          </div>
                        ))}
                      </div>
                      
                      {/* 分页控件 */}
                      {getAvailableCapabilities().length > capabilitiesPerPage && (
                        <div className="pagination" style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '16px' }}>
                          <button
                            onClick={() => setCapabilitiesPage(prev => Math.max(prev - 1, 1))}
                            disabled={capabilitiesPage === 1}
                            className="btn btn-secondary"
                          >
                            上一页
                          </button>
                          <span className="page-info">
                            第 {capabilitiesPage} 页 / 共 {Math.ceil(getAvailableCapabilities().length / capabilitiesPerPage)} 页
                          </span>
                          <button
                            onClick={() => setCapabilitiesPage(prev => Math.min(prev + 1, Math.ceil(getAvailableCapabilities().length / capabilitiesPerPage)))}
                            disabled={capabilitiesPage >= Math.ceil(getAvailableCapabilities().length / capabilitiesPerPage)}
                            className="btn btn-secondary"
                          >
                            下一页
                          </button>
                          <select
                            value={capabilitiesPerPage}
                            onChange={(e) => {
                              setCapabilitiesPerPage(parseInt(e.target.value));
                              setCapabilitiesPage(1);
                            }}
                            className="form-control"
                            style={{ width: '80px' }}
                          >
                            <option value={6}>6条/页</option>
                            <option value={12}>12条/页</option>
                            <option value={24}>24条/页</option>
                            <option value={48}>48条/页</option>
                          </select>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  // 如果是模态模式且未打开，则不渲染任何内容
  if (isModalMode && !isOpen) return null;

  // 根据模式返回不同的内容
  return isModalMode ? renderModalMode() : renderPageMode();
};

export default ModelCapabilityAssociation;