import React, { useState, useEffect, useCallback, useMemo } from 'react';
import modelApi from '../../utils/api/modelApi';
import { capabilityApi } from '../../utils/api/capabilityApi';
import ModelSelectDropdown from '../ModelManagement/ModelSelectDropdown';
import { request } from '../../utils/apiUtils';
import './ModelCapabilityAssociation.css';

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

  // 使用useMemo缓存筛选后的能力列表
  const filteredCapabilities = useMemo(() => {
    return capabilities.filter(capability =>
      (capability.display_name?.toLowerCase().includes(capabilitySearch.toLowerCase()) ||
       capability.name?.toLowerCase().includes(capabilitySearch.toLowerCase())) &&
      (capabilityFilter === 'all' || capability.capability_type === capabilityFilter)
    );
  }, [capabilities, capabilitySearch, capabilityFilter]);

  // 使用useMemo缓存当前模型未关联的能力
  const availableCapabilities = useMemo(() => {
    if (!selectedModel) return [];
    
    // 确保modelCapabilities和capabilities数据正确
    const associatedCapabilityIds = new Set(
      modelCapabilities
        .filter(mc => mc && mc.capability_id) // 过滤掉无效数据
        .map(mc => mc.capability_id)
    );
    
    const filtered = filteredCapabilities.filter(cap => 
      cap && cap.id && !associatedCapabilityIds.has(cap.id)
    );
    
    return filtered;
  }, [selectedModel, modelCapabilities, filteredCapabilities]);

  // 获取分页后的可用能力
  const getPagedAvailableCapabilities = () => {
    const startIndex = (capabilitiesPage - 1) * capabilitiesPerPage;
    const endIndex = startIndex + capabilitiesPerPage;
    return availableCapabilities.slice(startIndex, endIndex);
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
  const fetchModelCapabilities = async (modelId, skipLoadingState = false) => {
    try {
      if (!skipLoadingState) {
        setLoading(true);
      }
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
      if (!skipLoadingState) {
        setLoading(false);
      }
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
        
        // 使用完整的刷新功能来确保所有数据都正确更新
        await handleRefreshAll();
        
        // 添加延迟确保UI完全更新
        setTimeout(() => {
          // UI更新完成
        }, 100);
      } else if (response && Object.keys(response).length === 0) {
        // 空对象表示409错误（关联已存在）
        setSuccess('该能力已关联到此模型');
      } else {
        setError(response.message || '添加能力失败');
      }
    } catch (error) {
      // 对于409错误（关联已存在），不显示错误信息
      if (error && (error.status === 409 || (error.message && error.message.includes('409')))) {
        setSuccess('该能力已关联到此模型');
      } else {
        setError('添加能力时发生错误: ' + (error && error.message ? error.message : '未知错误'));
        console.error('添加能力错误:', error);
      }
    } finally {
      setUpdateLoading(false);
    }
  };

  // 完整的刷新功能 - 刷新所有相关数据
  const handleRefreshAll = async () => {
    try {
      setError(null);
      setSuccess(null);
      
      // 串行刷新所有数据，确保状态正确更新
      
      // 首先刷新能力列表
      await fetchCapabilities();
      
      // 然后刷新模型能力关联（跳过loading状态）
      if (selectedModel) {
        await fetchModelCapabilities(selectedModel.id, true);
      }
      
      // 重置分页到第一页并强制重新计算可用能力
      setCapabilitiesPage(1);
      
      // 强制重新渲染组件，确保状态更新
      setCapabilities(prev => [...prev]);
      setModelCapabilities(prev => [...prev]);
    } catch (err) {
      setError('刷新时发生错误');
      console.error('刷新错误:', err);
    }
  };

  // 移除能力时的完整刷新
  const handleRemoveCapability = async (modelCapabilityId) => {
    try {
      setUpdateLoading(true);
      const response = await capabilityApi.removeCapabilityFromModel(modelCapabilityId);
      
      if (response.success) {
        setSuccess('能力移除成功');
        // 使用完整的刷新功能
        await handleRefreshAll();
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
          <div className="section-container">
            <div className="section-header">
              <h3 className="section-title">已关联的能力</h3>
              <button
                onClick={handleRefreshAll}
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
                      <td colSpan="4" className="table-empty-cell">
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
          <div className="section-container">
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
              {availableCapabilities.length === 0 ? (
                <p>所有能力已关联到此模型</p>
              ) : (
                <>
                  <div className="capability-grid">
                    {getPagedAvailableCapabilities().map(capability => (
                      <div
                        key={capability.id}
                        className="capability-card capability-card-flex"
                      >
                        <h4>{capability.display_name || capability.name}</h4>
                        <p className="text-sm">能力类型: <span className={`capability-type-badge ${capability.capability_type}`}>{capability.capability_type}</span></p>
                        <p className="description-truncate">{capability.description || '无描述'}</p>
                        <button
                          onClick={() => handleAddCapability(capability.id, {})}
                          disabled={updateLoading}
                          className="btn btn-primary btn-full-width"
                        >
                          {updateLoading ? '添加中...' : '添加到模型'}
                        </button>
                      </div>
                    ))}
                  </div>
                  
                  {/* 分页控件 */}
                  {availableCapabilities.length > capabilitiesPerPage && (
                    <div className="pagination pagination-container">
                      <button
                        onClick={() => setCapabilitiesPage(prev => Math.max(prev - 1, 1))}
                        disabled={capabilitiesPage === 1}
                        className="btn btn-secondary"
                      >
                        上一页
                      </button>
                      <span className="page-info">
                        第 {capabilitiesPage} 页 / 共 {Math.ceil(availableCapabilities.length / capabilitiesPerPage)} 页
                      </span>
                      <button
                        onClick={() => setCapabilitiesPage(prev => Math.min(prev + 1, Math.ceil(availableCapabilities.length / capabilitiesPerPage)))}
                        disabled={capabilitiesPage >= Math.ceil(availableCapabilities.length / capabilitiesPerPage)}
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
                        className="form-control form-control-small"
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
              <span className="text-muted text-muted-with-margin">
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
              <div className="section-container">
                <div className="section-header">
                  <h3 className="section-title">已关联的能力</h3>
                  <button
                    onClick={handleRefreshAll}
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
                          <td colSpan="4" className="table-empty-cell">
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
              <div className="section-container">
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
                  {availableCapabilities.length === 0 ? (
                    <p>所有能力已关联到此模型</p>
                  ) : (
                    <>
                      <div className="capability-grid">
                        {getPagedAvailableCapabilities().map(capability => (
                          <div
                            key={capability.id}
                            className="capability-card capability-card-flex"
                          >
                            <h4>{capability.display_name || capability.name}</h4>
                            <p className="text-sm">能力类型: <span className={`capability-type-badge ${capability.capability_type}`}>{capability.capability_type}</span></p>
                            <p className="description-truncate">{capability.description || '无描述'}</p>
                            <button
                              onClick={() => handleAddCapability(capability.id, {})}
                              disabled={updateLoading}
                              className="btn btn-primary btn-full-width"
                            >
                              {updateLoading ? '添加中...' : '添加到模型'}
                            </button>
                          </div>
                        ))}
                      </div>
                      
                      {/* 分页控件 */}
                      {availableCapabilities.length > capabilitiesPerPage && (
                        <div className="pagination pagination-container">
                          <button
                            onClick={() => setCapabilitiesPage(prev => Math.max(prev - 1, 1))}
                            disabled={capabilitiesPage === 1}
                            className="btn btn-secondary"
                          >
                            上一页
                          </button>
                          <span className="page-info">
                            第 {capabilitiesPage} 页 / 共 {Math.ceil(availableCapabilities.length / capabilitiesPerPage)} 页
                          </span>
                          <button
                            onClick={() => setCapabilitiesPage(prev => Math.min(prev + 1, Math.ceil(availableCapabilities.length / capabilitiesPerPage)))}
                            disabled={capabilitiesPage >= Math.ceil(availableCapabilities.length / capabilitiesPerPage)}
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
                            className="form-control form-control-small"
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