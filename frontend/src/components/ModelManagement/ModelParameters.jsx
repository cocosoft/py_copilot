import React, { useState, useEffect } from 'react';
import '../../styles/ParameterManagement.css';
import api from '../../utils/api';
import ModelParameterModal from './ModelParameterModal';

const ModelParameters = ({ supplierId, modelId, modelName, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [parameters, setParameters] = useState([]);
  const [isParameterModalOpen, setIsParameterModalOpen] = useState(false);
  const [parameterModalMode, setParameterModalMode] = useState('add');
  const [editingParameter, setEditingParameter] = useState(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(null);

  // 加载模型参数
  const loadParameters = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = await api.modelApi.getModelParameters(supplierId, modelId);
      setParameters(params);
    } catch (err) {
      console.error('加载模型参数失败:', err);
      setError('加载模型参数失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    if (supplierId && modelId) {
      loadParameters();
    }
  }, [supplierId, modelId]);

  // 打开参数编辑模态框
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

  // 保存参数数据
  const handleSaveParameterData = async (parameterData) => {
    try {
      setSaving(true);
      setError(null);
      
      if (parameterModalMode === 'add') {
        await api.modelApi.createModelParameter(supplierId, modelId, parameterData);
        setSuccess('参数添加成功');
      } else {
        await api.modelApi.updateModelParameter(supplierId, modelId, editingParameter.parameter_name, parameterData);
        setSuccess('参数更新成功');
      }
      
      loadParameters();
    } catch (err) {
      console.error('保存参数失败:', err);
      setError('保存参数失败，请重试');
    } finally {
      setSaving(false);
      setIsParameterModalOpen(false);
      // 3秒后清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    }
  };

  // 删除参数
  const handleDeleteParameter = async (parameterName) => {
    const parameter = parameters.find(p => p.parameter_name === parameterName);
    
    if (parameter && parameter.parameter_source === 'model_type' && !parameter.is_override) {
      setError('继承参数不能被删除');
      return;
    }
    
    if (window.confirm('确定要删除这个参数吗？')) {
      try {
        setSaving(true);
        setError(null);
        
        await api.modelApi.deleteModelParameter(supplierId, modelId, parameterName);
        setSuccess('参数删除成功');
        loadParameters();
      } catch (err) {
        console.error('删除参数失败:', err);
        setError('删除参数失败，请重试');
      } finally {
        setSaving(false);
        // 3秒后清除成功消息
        setTimeout(() => setSuccess(null), 3000);
      }
    }
  };

  // 获取参数来源的显示名称
  const getParameterSourceName = (source, isOverride) => {
    if (source === 'model_type') {
      return isOverride ? '继承（已覆盖）' : '继承（模型类型）';
    } else {
      return '自定义';
    }
  };

  // 渲染参数表格
  const renderParametersTable = () => {
    if (loading) {
      return <div className="loading">加载中...</div>;
    }

    if (parameters.length === 0) {
      return <div className="empty-state">暂无参数</div>;
    }

    return (
      <div className="parameters-table-container">
        <table className="parameters-table">
          <thead>
            <tr>
              <th>参数名称</th>
              <th>参数值</th>
              <th>参数类型</th>
              <th>来源</th>
              <th>描述</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {parameters.map((param) => (
              <tr key={param.parameter_name} className={param.parameter_source === 'model_type' ? 'inherited-parameter' : ''}>
                <td>
                  <span className="parameter-name">{param.parameter_name}</span>
                  {param.parameter_source === 'model_type' && !param.is_override && (
                    <span className="inherited-badge">继承</span>
                  )}
                  {param.parameter_source === 'model_type' && param.is_override && (
                    <span className="overridden-badge">已覆盖</span>
                  )}
                </td>
                <td>
                  <div className="parameter-value">
                    {typeof param.parameter_value === 'object' 
                      ? JSON.stringify(param.parameter_value)
                      : param.parameter_value}
                  </div>
                </td>
                <td>
                  <span className={`parameter-type-badge ${param.parameter_type}`}>
                    {param.parameter_type}
                  </span>
                </td>
                <td>
                  <span className="parameter-source">
                    {getParameterSourceName(param.parameter_source, param.is_override)}
                  </span>
                </td>
                <td>{param.description || '-'}</td>
                <td>
                  <div className="action-buttons">
                    <button 
                      className="btn btn-sm btn-primary"
                      onClick={() => handleEditParameterClick(param)}
                      disabled={param.parameter_source === 'model_type' && !param.is_override}
                    >
                      {param.parameter_source === 'model_type' && !param.is_override ? '覆盖' : '编辑'}
                    </button>
                    <button 
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDeleteParameter(param.parameter_name)}
                      disabled={param.parameter_source === 'model_type' && !param.is_override}
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
    );
  };

  return (
    <div className="model-parameters">
      <div className="page-header">
        <button className="btn btn-secondary" onClick={onBack}>
          返回
        </button>
        <h2>模型参数管理 - {modelName}</h2>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="parameters-actions">
        <button 
          className="btn btn-primary"
          onClick={handleAddParameterClick}
          disabled={loading}
        >
          添加自定义参数
        </button>
      </div>

      <div className="parameters-info">
        <p><strong>提示：</strong>灰色行表示继承的参数，带有"继承"标记的参数不能直接编辑或删除，需要点击"覆盖"按钮来修改。</p>
      </div>

      {renderParametersTable()}

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

export default ModelParameters;