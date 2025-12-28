import React, { useState, useEffect, useCallback } from 'react';
import modelApi from '../../utils/api/modelApi';
import { capabilityApi } from '../../utils/api/capabilityApi';
import ModelSelectDropdown from '../ModelManagement/ModelSelectDropdown';

const ModelCapabilityAssociation = () => {
  const [models, setModels] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [modelCapabilities, setModelCapabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // 分页和筛选状态
  const [modelsPage, setModelsPage] = useState(1);
  const [modelsPerPage, setModelsPerPage] = useState(10);
  const [capabilitiesPage, setCapabilitiesPage] = useState(1);
  const [capabilitiesPerPage, setCapabilitiesPerPage] = useState(12);
  const [capabilityFilter, setCapabilityFilter] = useState('all');
  
  // 搜索状态
  const [modelSearch, setModelSearch] = useState('');
  const [capabilitySearch, setCapabilitySearch] = useState('');
  
  // 排序状态
  const [sortField, setSortField] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  // 加载所有模型
  const fetchModels = useCallback(async () => {
    try {
      // modelApi.getAll返回的是一个包含models数组的对象
      let response = await modelApi.getAll();
      // 确保response.models是数组类型
      const modelsData = Array.isArray(response.models) ? response.models : [];
      
      // 添加调试信息，查看模型数据结构
      if (modelsData.length > 0) {
        console.log('第一个模型的数据结构:', JSON.stringify(modelsData[0], null, 2));
        // 列出所有模型的键
        console.log('第一个模型的所有字段:', Object.keys(modelsData[0]));
      }
      
      setModels(modelsData);
    } catch (error) {
      console.error('获取模型列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      setError('获取模型列表失败');
      // 出错时设置为空数组，避免map错误
      setModels([]);
    }
  }, []);

  // 加载所有能力
  const fetchCapabilities = useCallback(async () => {
    try {
      const params = capabilityFilter !== 'all' ? { capability_type: capabilityFilter } : {};
      const capabilitiesData = await capabilityApi.getAll(params);
      // 直接使用capabilityApi返回的已经处理好的数据
      setCapabilities(Array.isArray(capabilitiesData) ? capabilitiesData : []);
      setCapabilitiesPage(1); // 重置分页
    } catch (error) {
      console.error('获取能力列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      setError('获取能力列表失败');
      // 出错时设置为空数组，避免map错误
      setCapabilities([]);
    }
  }, [capabilityFilter]);

  // 加载模型能力关联
  const fetchModelCapabilities = async (modelId) => {
    if (!modelId) return;
    
    setLoading(true);
    try {
      const modelCapabilitiesData = await capabilityApi.getCapabilitiesByModel(modelId);
      // 直接使用capabilityApi返回的已经处理好的数据
      const sortedCapabilities = [...(Array.isArray(modelCapabilitiesData) ? modelCapabilitiesData : [])]
        .sort((a, b) => {
          if (a[sortField] < b[sortField]) return sortOrder === 'asc' ? -1 : 1;
          if (a[sortField] > b[sortField]) return sortOrder === 'asc' ? 1 : -1;
          return 0;
        });
      setModelCapabilities(sortedCapabilities);
    } catch (error) {
      console.error('获取模型能力关联失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
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
    if (!selectedModel) {
      setError('请先选择模型');
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    if (!capabilityId) {
      setError('请选择有效的能力');
      setTimeout(() => setError(null), 3000);
      return;
    }

    setUpdateLoading(true);
    try {
      const associationData = {
        id: selectedModel.id,
        capability_id: capabilityId,
        config: configuration || {}
      };
      await capabilityApi.addCapabilityToModel(associationData);
      setSuccess('能力添加成功');
      setTimeout(() => setSuccess(null), 3000);
      fetchModelCapabilities(selectedModel.id);
    } catch (error) {
      console.error('添加能力失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      let errorMsg = '添加失败';
      if (error.response?.data?.detail) {
        errorMsg += `: ${error.response.data.detail}`;
      } else if (error.message) {
        errorMsg += `: ${error.message}`;
      } else {
        errorMsg += ': 未知错误';
      }
      setError(errorMsg);
      setTimeout(() => setError(null), 5000);
    } finally {
      setUpdateLoading(false);
    }
  };

  // 从模型移除能力
  const handleRemoveCapability = async (capabilityId) => {
    if (!selectedModel) {
      setError('请先选择模型');
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    if (!capabilityId) {
      setError('请选择有效的能力');
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    // 确认操作
    const confirmRemove = window.confirm('确定要移除该能力吗？此操作将永久删除该模型的此能力配置。');
    if (!confirmRemove) return;
    
    setUpdateLoading(true);
    try {
      // 调用API移除能力关联
      await capabilityApi.removeCapabilityFromModel(selectedModel.id, capabilityId);
      setSuccess('能力移除成功');
      setTimeout(() => setSuccess(null), 3000);
      fetchModelCapabilities(selectedModel.id);
    } catch (error) {
      console.error('移除能力失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      let errorMsg = '移除失败';
      if (error.response?.data?.detail) {
        errorMsg += `: ${error.response.data.detail}`;
      } else if (error.message) {
        errorMsg += `: ${error.message}`;
      } else {
        errorMsg += ': 未知错误';
      }
      setError(errorMsg);
      setTimeout(() => setError(null), 5000);
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
      console.error('更新配置失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      setError('更新失败：' + (error.message || '未知错误'));
    } finally {
      setUpdateLoading(false);
    }
  };

  // 获取模型尚未关联的能力
  const getAvailableCapabilities = () => {
    const associatedCapabilityIds = modelCapabilities.map(mc => mc.id);
    
    // 先过滤出未关联的能力
    let available = capabilities.filter(cap => !associatedCapabilityIds.includes(cap.id));
    
    // 应用搜索过滤
    if (capabilitySearch) {
      const searchLower = capabilitySearch.toLowerCase();
      available = available.filter(cap => 
        cap.name.toLowerCase().includes(searchLower) ||
        (cap.display_name && cap.display_name.toLowerCase().includes(searchLower)) ||
        (cap.description && cap.description.toLowerCase().includes(searchLower))
      );
    }
    
    return available;
  };
  
  // 处理排序
  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
    fetchModelCapabilities(selectedModel?.id);
  };
  
  // 获取过滤和分页后的模型列表
  const getFilteredModels = () => {
    let filtered = [...models];
    
    // 应用搜索过滤
    if (modelSearch) {
      const searchLower = modelSearch.toLowerCase();
      filtered = filtered.filter(model => 
        (model.model_name && model.model_name.toLowerCase().includes(searchLower)) ||
        (model.model_id && model.model_id.toLowerCase().includes(searchLower))
      );
    }
    
    return filtered;
  };
  
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
  




  return (
    <div className="model-capability-association">
      <h2>模型能力关联管理</h2>
      
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
              <div className="loading">加载中...</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th onClick={() => handleSort('name')} className="sortable">
                      能力名称
                      {sortField === 'name' && (
                        <span className="sort-indicator">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </th>
                    <th onClick={() => handleSort('display_name')} className="sortable">
                      显示名称
                      {sortField === 'display_name' && (
                        <span className="sort-indicator">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </th>
                    <th onClick={() => handleSort('capability_type')} className="sortable">
                      能力类型
                      {sortField === 'capability_type' && (
                        <span className="sort-indicator">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </th>
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
                        <td><span className={`capability-type-badge ${record.capability_type}`}>{record.capability_type}</span></td>
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

          {/* 添加新能力 */}
          <div style={{ marginTop: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3>添加新能力</h3>
              <div className="input-group" style={{ maxWidth: '300px' }}>
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
};

export default ModelCapabilityAssociation;