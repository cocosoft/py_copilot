import React, { useState, useEffect, useCallback } from 'react';
import '../../styles/AgentParameterManagement.css';
import { agentParameterApi } from '../../services/agentParameterService';
import AgentParameterModal from './AgentParameterModal';

const AgentParameterManagement = ({ agent, onBack, onRefreshAgent }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [parameters, setParameters] = useState([]);
  const [effectiveParameters, setEffectiveParameters] = useState(null);
  const [selectedParameters, setSelectedParameters] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [editingParameter, setEditingParameter] = useState(null);
  const [saving, setSaving] = useState(false);
  const [filterGroup, setFilterGroup] = useState('');
  const [parameterGroups, setParameterGroups] = useState([]);

  const loadParameters = useCallback(async () => {
    if (!agent?.id) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const result = await agentParameterApi.getParameters(
        agent.id,
        0,
        1000,
        filterGroup || null
      );
      
      setParameters(result.parameters || []);
      setParameterGroups(result.parameters?.reduce((groups, param) => {
        if (param.parameter_group && !groups.includes(param.parameter_group)) {
          groups.push(param.parameter_group);
        }
        return groups;
      }, []) || []);
    } catch (err) {
      console.error('加载参数失败:', err);
      // 提供更详细的错误信息
      if (err.message && err.message.includes('Failed to fetch')) {
        setError('无法连接到服务器，请检查网络连接或服务器状态');
      } else if (err.message && err.message.includes('500')) {
        setError('服务器内部错误，请稍后重试');
      } else {
        setError('加载参数失败，请重试');
      }
    } finally {
      setLoading(false);
    }
  }, [agent?.id, filterGroup]);

  const loadEffectiveParameters = useCallback(async () => {
    if (!agent?.id) return;
    
    try {
      const result = await agentParameterApi.getEffectiveParameters(agent.id);
      setEffectiveParameters(result);
    } catch (err) {
      console.error('加载有效参数失败:', err);
      // 提供更详细的错误信息
      if (err.message && err.message.includes('Failed to fetch')) {
        setError('无法连接到服务器，请检查网络连接或服务器状态');
      } else if (err.message && err.message.includes('500')) {
        setError('服务器内部错误，请稍后重试');
      }
    }
  }, [agent?.id]);

  useEffect(() => {
    loadParameters();
    loadEffectiveParameters();
  }, [loadParameters, loadEffectiveParameters]);

  useEffect(() => {
    if (parameters.length > 0) {
      const hasSelectable = parameters.some(p => !p.is_default && !p.inherited);
      setShowBulkActions(hasSelectable);
    } else {
      setShowBulkActions(false);
    }
  }, [parameters]);

  const handleAddParameter = () => {
    setModalMode('add');
    setEditingParameter(null);
    setIsModalOpen(true);
  };

  const handleEditParameter = (parameter) => {
    if (parameter.inherited || parameter.is_default) {
      setError('继承参数或默认参数不能被编辑');
      return;
    }
    
    setModalMode('edit');
    setEditingParameter(parameter);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingParameter(null);
  };

  const handleSaveParameter = async (parameterData) => {
    try {
      setSaving(true);
      setError(null);
      
      if (modalMode === 'add') {
        await agentParameterApi.createParameter(agent.id, parameterData);
        setSuccess('参数添加成功');
      } else {
        await agentParameterApi.updateParameter(agent.id, editingParameter.parameter_name, parameterData);
        setSuccess('参数更新成功');
      }
      
      loadParameters();
      loadEffectiveParameters();
    } catch (err) {
      console.error('保存参数失败:', err);
      setError(modalMode === 'add' ? '添加参数失败，请重试' : '更新参数失败，请重试');
    } finally {
      setSaving(false);
      setIsModalOpen(false);
      setTimeout(() => setSuccess(null), 3000);
    }
  };

  const handleDeleteParameter = async (parameter) => {
    if (parameter.inherited || parameter.is_default) {
      setError('继承参数或默认参数不能被删除');
      return;
    }
    
    if (window.confirm(`确定要删除参数 "${parameter.parameter_name}" 吗？`)) {
      try {
        setSaving(true);
        setError(null);
        
        await agentParameterApi.deleteParameter(agent.id, parameter.parameter_name);
        setSuccess('参数删除成功');
        loadParameters();
        loadEffectiveParameters();
      } catch (err) {
        console.error('删除参数失败:', err);
        setError('删除参数失败，请重试');
      } finally {
        setSaving(false);
        setTimeout(() => setSuccess(null), 3000);
      }
    }
  };

  const handleSelectParameter = (parameterId) => {
    const parameter = parameters.find(p => p.id === parameterId);
    if (parameter && (parameter.inherited || parameter.is_default)) {
      setError('继承参数或默认参数不能被选择');
      return;
    }
    
    setSelectedParameters(prev => {
      if (prev.includes(parameterId)) {
        return prev.filter(id => id !== parameterId);
      } else {
        return [...prev, parameterId];
      }
    });
  };

  const handleSelectAll = () => {
    const selectableParams = parameters
      .filter(p => !p.inherited && !p.is_default)
      .map(p => p.id);
    
    if (selectedParameters.length === selectableParams.length && selectableParams.length > 0) {
      setSelectedParameters([]);
    } else {
      setSelectedParameters(selectableParams);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedParameters.length === 0) {
      setError('请先选择要删除的参数');
      return;
    }
    
    if (window.confirm(`确定要删除选中的 ${selectedParameters.length} 个参数吗？`)) {
      try {
        setSaving(true);
        setError(null);
        
        for (const paramId of selectedParameters) {
          const param = parameters.find(p => p.id === paramId);
          if (param) {
            await agentParameterApi.deleteParameter(agent.id, param.parameter_name);
          }
        }
        
        setSuccess(`成功删除 ${selectedParameters.length} 个参数`);
        setSelectedParameters([]);
        loadParameters();
        loadEffectiveParameters();
      } catch (err) {
        console.error('批量删除参数失败:', err);
        setError('批量删除参数失败，请重试');
      } finally {
        setSaving(false);
        setTimeout(() => setSuccess(null), 3000);
      }
    }
  };

  const handleBulkCreate = async () => {
    setModalMode('bulk');
    setEditingParameter(null);
    setIsModalOpen(true);
  };

  const getParameterTypeLabel = (type) => {
    const typeMap = {
      'string': '字符串',
      'integer': '整数',
      'number': '数值',
      'boolean': '布尔值',
      'array': '数组',
      'object': '对象'
    };
    return typeMap[type] || type;
  };

  const getInheritedFromLabel = (param) => {
    if (param.inherited_from_model) {
      return '模型继承';
    }
    if (param.inherited_from_model_type) {
      return '模型类型继承';
    }
    if (param.parameter_source) {
      const sourceMap = {
        'model': '模型',
        'model_type': '模型类型',
        'system': '系统'
      };
      return sourceMap[param.parameter_source] || param.parameter_source;
    }
    return null;
  };

  const formatParameterValue = (value) => {
    if (value === null || value === undefined) {
      return '-';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  if (!agent) {
    return (
      <div className="agent-parameter-management">
        <div className="error-message">未选择智能体</div>
      </div>
    );
  }

  return (
    <div className="agent-parameter-management">
      <div className="apm-header">
        <div className="apm-header-left">
          <button className="back-btn" onClick={onBack}>
            ← 返回
          </button>
          <div className="agent-info">
            <h2>参数管理</h2>
            <p className="agent-name">{agent.name}</p>
          </div>
        </div>
        <div className="apm-header-right">
          <button className="apm-btn apm-btn-secondary" onClick={loadParameters}>
            刷新
          </button>
          <button className="apm-btn apm-btn-primary" onClick={handleAddParameter}>
            添加参数
          </button>
        </div>
      </div>

      {error && (
        <div className="apm-message apm-message-error">
          {error}
          <button className="apm-message-close" onClick={() => setError(null)}>×</button>
        </div>
      )}
      
      {success && (
        <div className="apm-message apm-message-success">
          {success}
          <button className="apm-message-close" onClick={() => setSuccess(null)}>×</button>
        </div>
      )}

      <div className="apm-content">
        <div className="apm-main-panel">
          <div className="apm-panel-header">
            <h3>智能体参数</h3>
            <div className="apm-panel-actions">
              <select 
                className="apm-select"
                value={filterGroup}
                onChange={(e) => setFilterGroup(e.target.value)}
              >
                <option value="">所有分组</option>
                {parameterGroups.map(group => (
                  <option key={group} value={group}>{group}</option>
                ))}
              </select>
              
              {showBulkActions && (
                <>
                  <button 
                    className="apm-btn apm-btn-sm"
                    onClick={handleSelectAll}
                  >
                    {selectedParameters.length === parameters.filter(p => !p.inherited && !p.is_default).length 
                      && selectedParameters.length > 0 ? '取消全选' : '全选'}
                  </button>
                  <button 
                    className="apm-btn apm-btn-sm apm-btn-danger"
                    onClick={handleBulkDelete}
                    disabled={selectedParameters.length === 0}
                  >
                    批量删除 ({selectedParameters.length})
                  </button>
                  <button 
                    className="apm-btn apm-btn-sm apm-btn-secondary"
                    onClick={handleBulkCreate}
                  >
                    批量添加
                  </button>
                </>
              )}
            </div>
          </div>

          {loading ? (
            <div className="apm-loading">加载中...</div>
          ) : parameters.length === 0 ? (
            <div className="apm-empty">
              <p>暂无参数</p>
              <button className="apm-btn apm-btn-primary" onClick={handleAddParameter}>
                添加第一个参数
              </button>
            </div>
          ) : (
            <div className="apm-parameters-table-container">
              <table className="apm-parameters-table">
                <thead>
                  <tr>
                    <th className="apm-checkbox-cell">
                      <input
                        type="checkbox"
                        checked={selectedParameters.length === parameters.filter(p => !p.inherited && !p.is_default).length 
                          && selectedParameters.length > 0}
                        onChange={handleSelectAll}
                      />
                    </th>
                    <th>参数名称</th>
                    <th>参数值</th>
                    <th>类型</th>
                    <th>分组</th>
                    <th>来源</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {parameters.map(param => (
                    <tr 
                      key={param.id} 
                      className={`${param.inherited ? 'apm-inherited' : ''} ${param.is_default ? 'apm-default' : ''}`}
                    >
                      <td className="apm-checkbox-cell">
                        <input
                          type="checkbox"
                          checked={selectedParameters.includes(param.id)}
                          onChange={() => handleSelectParameter(param.id)}
                          disabled={param.inherited || param.is_default}
                        />
                      </td>
                      <td className="apm-param-name">
                        {param.parameter_name}
                        {param.inherited && <span className="apm-badge apm-badge-inherited">继承</span>}
                        {param.is_default && <span className="apm-badge apm-badge-default">默认</span>}
                        {param.is_override && <span className="apm-badge apm-badge-override">覆盖</span>}
                      </td>
                      <td className="apm-param-value">
                        <code>{formatParameterValue(param.parameter_value)}</code>
                      </td>
                      <td>{getParameterTypeLabel(param.parameter_type)}</td>
                      <td>{param.parameter_group || '-'}</td>
                      <td>{getInheritedFromLabel(param) || '-'}</td>
                      <td className="apm-actions-cell">
                        {!param.inherited && !param.is_default && (
                          <>
                            <button 
                              className="apm-action-btn apm-action-edit"
                              onClick={() => handleEditParameter(param)}
                              title="编辑"
                            >
                              ✏️
                            </button>
                            <button 
                              className="apm-action-btn apm-action-delete"
                              onClick={() => handleDeleteParameter(param)}
                              title="删除"
                            >
                              🗑️
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="apm-sidebar">
          <div className="apm-panel">
            <h3>有效参数</h3>
            {effectiveParameters ? (
              <div className="apm-effective-params">
                <div className="apm-effective-summary">
                  <span className="apm-effective-count">
                    {effectiveParameters.parameters?.length || 0} 个参数
                  </span>
                  {effectiveParameters.inherited_from_model && (
                    <span className="apm-effective-source">
                      继承自模型 #{effectiveParameters.model_id}
                    </span>
                  )}
                </div>
                
                {effectiveParameters.parameters && effectiveParameters.parameters.length > 0 && (
                  <ul className="apm-effective-list">
                    {effectiveParameters.parameters.slice(0, 10).map((param, index) => (
                      <li key={index} className="apm-effective-item">
                        <span className="apm-effective-name">{param.parameter_name}</span>
                        <span className="apm-effective-value">{formatParameterValue(param.parameter_value)}</span>
                        {param.is_default && <span className="apm-badge apm-badge-small">默认</span>}
                      </li>
                    ))}
                    {effectiveParameters.parameters.length > 10 && (
                      <li className="apm-effective-more">
                        ... 还有 {effectiveParameters.parameters.length - 10} 个参数
                      </li>
                    )}
                  </ul>
                )}
              </div>
            ) : (
              <div className="apm-loading">加载中...</div>
            )}
          </div>

          <div className="apm-panel">
            <h3>帮助</h3>
            <div className="apm-help-content">
              <p><strong>参数说明：</strong></p>
              <ul>
                <li><span className="apm-badge apm-badge-default">默认</span> 继承自模型的参数</li>
                <li><span className="apm-badge apm-badge-inherited">继承</span> 来自上层的参数</li>
                <li><span className="apm-badge apm-badge-override">覆盖</span> 被当前智能体覆盖的参数</li>
              </ul>
              <p><strong>提示：</strong></p>
              <ul>
                <li>智能体参数会继承自关联的模型</li>
                <li>可以直接在智能体中覆盖继承的参数值</li>
                <li>继承的参数不能直接编辑或删除</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {isModalOpen && (
        <AgentParameterModal
          mode={modalMode}
          parameter={editingParameter}
          onSave={handleSaveParameter}
          onClose={handleCloseModal}
          saving={saving}
        />
      )}
    </div>
  );
};

export default AgentParameterManagement;
