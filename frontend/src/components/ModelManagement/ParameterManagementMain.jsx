import React, { useState, useEffect } from 'react';
import '../../styles/ParameterManagement.css';
import api from '../../utils/api';
import ParameterModal from './ModelParameterModal';
import BatchParameterModal from './BatchParameterModal';

const ParameterManagementMain = ({ selectedSupplier, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [parameters, setParameters] = useState([]);
  const [selectedLevel, setSelectedLevel] = useState('supplier'); // 系统/供应商/模型类型/模型能力/模型/代理
  const [selectedParameterTemplate, setSelectedParameterTemplate] = useState(null);
  const [parameterTemplates, setParameterTemplates] = useState([]); // 参数模板列表
  const [isParameterModalOpen, setIsParameterModalOpen] = useState(false);
  const [parameterModalMode, setParameterModalMode] = useState('add');
  const [editingParameter, setEditingParameter] = useState(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState({});
  const [inheritanceTree, setInheritanceTree] = useState(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [selectedParameters, setSelectedParameters] = useState([]); // 批量选择的参数ID数组
  const [showBatchActions, setShowBatchActions] = useState(false); // 是否显示批量操作按钮
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false); // 批量编辑模态框开关
  const [applyingTemplate, setApplyingTemplate] = useState(false); // 模板应用状态

  // 层级选项
  const levelOptions = [
    { value: 'system', label: '系统级别' },
    { value: 'supplier', label: '供应商级别' },
    { value: 'model_type', label: '模型类型级别' },
    { value: 'model_capability', label: '模型能力级别' },
    { value: 'model', label: '模型级别' },
    { value: 'agent', label: '代理级别' }
  ];

  // 加载参数模板
  const loadParameters = async () => {
    try {
      setLoading(true);
      setError(null);
      let params = [];
      
      switch (selectedLevel) {
        case 'supplier':
          if (selectedSupplier) {
            params = await api.modelApi.getParameters(selectedSupplier.id, null, 'supplier');
          }
          break;
        case 'model_type':
          // 加载模型类型参数模板
          params = await api.modelApi.getParameters(null, null, 'model_type');
          break;
        case 'model_capability':
          // 加载模型能力参数模板
          params = await api.modelApi.getParameters(null, null, 'model_capability');
          break;
        case 'model':
          // 加载模型参数模板
          params = await api.modelApi.getParameters(null, null, 'model');
          break;
        case 'agent':
          // 加载代理参数模板
          params = await api.modelApi.getParameters(null, null, 'agent');
          break;
        default:
          // 加载系统参数模板
          params = await api.modelApi.getParameters(null, null, 'system');
      }
      
      setParameters(params);
    } catch (err) {
      console.error('加载参数模板失败:', err);
      setError('加载参数模板失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 当选择的层级或供应商改变时，重新加载参数
  useEffect(() => {
    loadParameters();
  }, [selectedLevel, selectedSupplier]);

  // 切换节点展开状态
  const toggleNode = (nodeId) => {
    setExpandedNodes(prev => ({
      ...prev,
      [nodeId]: !prev[nodeId]
    }));
  };

  // 打开参数编辑模态框
  const handleAddParameterClick = () => {
    setEditingParameter(null);
    setParameterModalMode('add');
    setIsParameterModalOpen(true);
  };

  const handleEditParameterClick = (parameter) => {
    if (parameter.inherited) {
      setError('继承参数不能被编辑');
      return;
    }
    
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
        await api.modelApi.createParameter(selectedSupplier?.id, null, parameterData, selectedLevel);
        setSuccess('参数添加成功');
      } else {
        await api.modelApi.updateParameter(selectedSupplier?.id, null, editingParameter.id, parameterData, selectedLevel);
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
  const handleDeleteParameter = async (parameterId) => {
    const parameter = parameters.find(p => p.id === parameterId);
    
    if (parameter && parameter.inherited) {
      setError('继承参数不能被删除');
      return;
    }
    
    if (window.confirm('确定要删除这个参数吗？')) {
      try {
        setSaving(true);
        setError(null);
        
        await api.modelApi.deleteParameter(selectedSupplier?.id, null, parameterId, selectedLevel);
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

  // 批量操作相关函数
  // 选择/取消选择单个参数
  const handleSelectParameter = (parameterId) => {
    const parameter = parameters.find(p => p.id === parameterId);
    if (parameter && parameter.inherited) {
      setError('继承参数不能被选择');
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

  // 全选/取消全选
  const handleSelectAllParameters = () => {
    const selectableParameters = parameters.filter(p => !p.inherited).map(p => p.id);
    
    if (selectedParameters.length === selectableParameters.length) {
      setSelectedParameters([]);
    } else {
      setSelectedParameters(selectableParameters);
    }
  };

  // 批量删除参数
  const handleBatchDeleteParameters = async () => {
    if (selectedParameters.length === 0) {
      setError('请先选择要删除的参数');
      return;
    }
    
    if (window.confirm(`确定要删除选中的${selectedParameters.length}个参数吗？`)) {
      try {
        setSaving(true);
        setError(null);
        
        // 批量删除参数
        for (const parameterId of selectedParameters) {
          await api.modelApi.deleteParameter(selectedSupplier?.id, null, parameterId, selectedLevel);
        }
        
        setSuccess(`成功删除${selectedParameters.length}个参数`);
        setSelectedParameters([]);
        loadParameters();
        loadInheritanceTree();
      } catch (err) {
        console.error('批量删除参数失败:', err);
        setError('批量删除参数失败，请重试');
      } finally {
        setSaving(false);
        // 3秒后清除成功消息
        setTimeout(() => setSuccess(null), 3000);
      }
    }
  };

  // 批量编辑参数模态框
  const handleBatchEditParameters = () => {
    if (selectedParameters.length === 0) {
      setError('请先选择要编辑的参数');
      return;
    }
    
    setIsBatchModalOpen(true);
  };

  // 保存批量编辑数据
  const handleSaveBatchParameterData = async (updateData) => {
    try {
      setSaving(true);
      setError(null);
      
      // 批量更新参数
      for (const parameterId of selectedParameters) {
        await api.modelApi.updateParameter(selectedSupplier?.id, null, parameterId, updateData, selectedLevel);
      }
      
      setSuccess(`成功更新${selectedParameters.length}个参数`);
      setSelectedParameters([]);
      loadParameters();
    } catch (err) {
      console.error('批量更新参数失败:', err);
      setError('批量更新参数失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  const handleCloseBatchModal = () => {
    setIsBatchModalOpen(false);
  };

  // 当参数加载完成后，检查是否有可选择的参数
  useEffect(() => {
    const hasSelectableParameters = parameters.some(p => !p.inherited);
    setShowBatchActions(hasSelectableParameters);
  }, [parameters]);

  // 获取继承来源的显示名称
  const getInheritanceSourceName = (sourceType, sourceId) => {
    switch (sourceType) {
      case 'system':
        return '系统默认';
      case 'supplier':
        return selectedSupplier?.name || '供应商';
      case 'model_type':
        return '模型类型';
      case 'model_capability':
        return '模型能力';
      case 'model':
        return '模型';
      case 'agent':
        return '代理';
      default:
        return '未知来源';
    }
  };

  // 模拟继承树数据
  const getMockInheritanceTree = () => {
    return {
      level: 'system',
      name: '系统级别',
      parameters: [
        { id: 'sys-param-1', parameter_name: 'max_tokens', parameter_value: 1000, parameter_type: 'integer', inherited: false, override: false },
        { id: 'sys-param-2', parameter_name: 'temperature', parameter_value: 0.5, parameter_type: 'float', inherited: false, override: false },
        { id: 'sys-param-3', parameter_name: 'top_p', parameter_value: 0.9, parameter_type: 'float', inherited: false, override: false }
      ],
      children: [
        {
          level: 'supplier',
          name: selectedSupplier?.name || '供应商',
          parameters: [
            { id: 'sup-param-1', parameter_name: 'max_tokens', parameter_value: 2000, parameter_type: 'integer', inherited: true, override: true, source: 'system' },
            { id: 'sup-param-2', parameter_name: 'temperature', parameter_value: 0.6, parameter_type: 'float', inherited: true, override: true, source: 'system' },
            { id: 'sup-param-3', parameter_name: 'top_p', parameter_value: 0.95, parameter_type: 'float', inherited: true, override: true, source: 'system' },
            { id: 'sup-param-4', parameter_name: 'stop_sequences', parameter_value: '["\n"]', parameter_type: 'array', inherited: false, override: false }
          ],
          children: [
            {
              level: 'model_type',
              name: '聊天模型',
              parameters: [
                { id: 'mt-param-1', parameter_name: 'max_tokens', parameter_value: 3000, parameter_type: 'integer', inherited: true, override: true, source: 'supplier' },
                { id: 'mt-param-2', parameter_name: 'temperature', parameter_value: 0.7, parameter_type: 'float', inherited: true, override: true, source: 'supplier' },
                { id: 'mt-param-3', parameter_name: 'top_p', parameter_value: 0.95, parameter_type: 'float', inherited: true, override: false, source: 'supplier' },
                { id: 'mt-param-4', parameter_name: 'stop_sequences', parameter_value: '["\n", "\n\n"]', parameter_type: 'array', inherited: true, override: true, source: 'supplier' },
                { id: 'mt-param-5', parameter_name: 'chat_history_window', parameter_value: 10, parameter_type: 'integer', inherited: false, override: false }
              ],
              children: [
                {
                  level: 'model_capability',
                  name: '文本生成',
                  parameters: [
                    { id: 'mc-param-1', parameter_name: 'max_tokens', parameter_value: 4000, parameter_type: 'integer', inherited: true, override: true, source: 'model_type' },
                    { id: 'mc-param-2', parameter_name: 'temperature', parameter_value: 0.8, parameter_type: 'float', inherited: true, override: true, source: 'model_type' },
                    { id: 'mc-param-3', parameter_name: 'top_p', parameter_value: 0.95, parameter_type: 'float', inherited: true, override: false, source: 'model_type' },
                    { id: 'mc-param-4', parameter_name: 'stop_sequences', parameter_value: '["\n", "\n\n"]', parameter_type: 'array', inherited: true, override: false, source: 'model_type' },
                    { id: 'mc-param-5', parameter_name: 'chat_history_window', parameter_value: 10, parameter_type: 'integer', inherited: true, override: false, source: 'model_type' },
                    { id: 'mc-param-6', parameter_name: 'response_format', parameter_value: 'json', parameter_type: 'string', inherited: false, override: false }
                  ],
                  children: [
                    {
                      level: 'model',
                      name: 'GPT-4',
                      parameters: [
                        { id: 'md-param-1', parameter_name: 'max_tokens', parameter_value: 8000, parameter_type: 'integer', inherited: true, override: true, source: 'model_capability' },
                        { id: 'md-param-2', parameter_name: 'temperature', parameter_value: 0.7, parameter_type: 'float', inherited: true, override: true, source: 'model_capability' },
                        { id: 'md-param-3', parameter_name: 'top_p', parameter_value: 0.95, parameter_type: 'float', inherited: true, override: false, source: 'model_capability' },
                        { id: 'md-param-4', parameter_name: 'stop_sequences', parameter_value: '["\n", "\n\n"]', parameter_type: 'array', inherited: true, override: false, source: 'model_capability' },
                        { id: 'md-param-5', parameter_name: 'chat_history_window', parameter_value: 15, parameter_type: 'integer', inherited: true, override: true, source: 'model_capability' },
                        { id: 'md-param-6', parameter_name: 'response_format', parameter_value: 'json', parameter_type: 'string', inherited: true, override: false, source: 'model_capability' },
                        { id: 'md-param-7', parameter_name: 'function_calling', parameter_value: 'auto', parameter_type: 'string', inherited: false, override: false }
                      ],
                      children: [
                        {
                          level: 'agent',
                          name: '客服代理',
                          parameters: [
                            { id: 'ag-param-1', parameter_name: 'max_tokens', parameter_value: 6000, parameter_type: 'integer', inherited: true, override: true, source: 'model' },
                            { id: 'ag-param-2', parameter_name: 'temperature', parameter_value: 0.3, parameter_type: 'float', inherited: true, override: true, source: 'model' },
                            { id: 'ag-param-3', parameter_name: 'top_p', parameter_value: 0.9, parameter_type: 'float', inherited: true, override: true, source: 'model' },
                            { id: 'ag-param-4', parameter_name: 'stop_sequences', parameter_value: '["\n", "\n\n"]', parameter_type: 'array', inherited: true, override: false, source: 'model' },
                            { id: 'ag-param-5', parameter_name: 'chat_history_window', parameter_value: 15, parameter_type: 'integer', inherited: true, override: false, source: 'model' },
                            { id: 'ag-param-6', parameter_name: 'response_format', parameter_value: 'json', parameter_type: 'string', inherited: true, override: false, source: 'model' },
                            { id: 'ag-param-7', parameter_name: 'function_calling', parameter_value: 'auto', parameter_type: 'string', inherited: true, override: false, source: 'model' },
                            { id: 'ag-param-8', parameter_name: 'custom_greeting', parameter_value: '您好，有什么可以帮助您的？', parameter_type: 'string', inherited: false, override: false }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    };
  };

  // 加载参数继承树
  const loadInheritanceTree = async () => {
    try {
      setTreeLoading(true);
      setError(null);
      
      // TODO: 替换为真实API调用
      // const treeData = await api.modelApi.getParameterInheritanceTree(selectedSupplier?.id);
      const treeData = getMockInheritanceTree();
      
      setInheritanceTree(treeData);
    } catch (err) {
      console.error('加载参数继承树失败:', err);
      setError('加载参数继承树失败，请重试');
    } finally {
      setTreeLoading(false);
    }
  };

  // 加载参数模板列表
  const loadParameterTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 根据当前层级获取可用的模板
      let templateLevel;
      switch (selectedLevel) {
        case 'system':
          templateLevel = 'system'; // 系统级使用系统级模板
          break;
        case 'supplier':
          templateLevel = 'system'; // 供应商级使用系统级模板
          break;
        case 'model_type':
          templateLevel = 'supplier'; // 模型类型级使用供应商级模板
          break;
        case 'model_capability':
          templateLevel = 'model_type'; // 模型能力级使用模型类型级模板
          break;
        case 'model':
          templateLevel = 'model_capability'; // 模型级使用模型能力级模板
          break;
        case 'agent':
          templateLevel = 'model'; // 代理级使用模型级模板
          break;
        default:
          templateLevel = 'system';
      }
      
      const templates = await api.modelApi.getParameterTemplates(templateLevel);
      setParameterTemplates(templates);
    } catch (err) {
      console.error('加载参数模板列表失败:', err);
      setError('加载参数模板列表失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 当选择的层级或供应商改变时，重新加载继承树
  useEffect(() => {
    loadInheritanceTree();
  }, [selectedLevel, selectedSupplier]);

  // 应用参数模板
  const handleApplyTemplate = async () => {
    if (!selectedParameterTemplate) {
      setError('请先选择要应用的参数模板');
      return;
    }

    try {
      setApplyingTemplate(true);
      setError(null);
      
      // 根据当前层级调用不同的API
      switch (selectedLevel) {
        case 'system':
          // 系统级参数模板应用
          await api.modelApi.applyParameterTemplate(null, selectedParameterTemplate, 'system');
          break;
        case 'supplier':
          if (!selectedSupplier) {
            setError('请先选择供应商');
            return;
          }
          // 供应商级参数模板应用
          await api.modelApi.applyParameterTemplate(selectedSupplier.id, selectedParameterTemplate, 'supplier');
          break;
        case 'model_type':
          if (!selectedSupplier) {
            setError('请先选择供应商');
            return;
          }
          // 模型类型级参数模板应用
          await api.modelApi.applyParameterTemplate(selectedSupplier.id, selectedParameterTemplate, 'model_type');
          break;
        case 'model_capability':
          if (!selectedSupplier) {
            setError('请先选择供应商');
            return;
          }
          // 模型能力级参数模板应用
          await api.modelApi.applyParameterTemplate(selectedSupplier.id, selectedParameterTemplate, 'model_capability');
          break;
        case 'model':
          if (!selectedSupplier) {
            setError('请先选择供应商');
            return;
          }
          // 模型级参数模板应用
          await api.modelApi.applyParameterTemplate(selectedSupplier.id, selectedParameterTemplate, 'model');
          break;
        case 'agent':
          if (!selectedSupplier) {
            setError('请先选择供应商');
            return;
          }
          // 代理级参数模板应用
          await api.modelApi.applyParameterTemplate(selectedSupplier.id, selectedParameterTemplate, 'agent');
          break;
        default:
          setError('不支持的参数层级');
          return;
      }
      
      setSuccess('参数模板应用成功');
      
      // 重新加载参数列表和继承树
      loadParameters();
      loadInheritanceTree();
      
      // 重置选择的模板
      setSelectedParameterTemplate(null);
    } catch (err) {
      console.error('应用参数模板失败:', err);
      setError('应用参数模板失败，请重试');
    } finally {
      setApplyingTemplate(false);
      
      // 3秒后清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    }
  };

  // 当组件挂载或选择的层级改变时，加载参数模板列表
  useEffect(() => {
    if (selectedLevel === 'system' || 
        (selectedSupplier && 
         (selectedLevel === 'supplier' || 
          selectedLevel === 'model_type' || 
          selectedLevel === 'model_capability' || 
          selectedLevel === 'model' || 
          selectedLevel === 'agent'))) {
      loadParameterTemplates();
    }
  }, [selectedLevel, selectedSupplier]);

  // 渲染继承树节点
  const renderInheritanceTree = (node, level = 0) => {
    return (
      <div className="inheritance-tree-node" style={{ marginLeft: `${level * 20}px` }}>
        <div className="inheritance-tree-node-header">
          <div 
            className="inheritance-tree-node-toggle"
            onClick={() => toggleNode(node.level)}
            style={{ cursor: 'pointer', marginRight: '8px' }}
          >
            {node.children?.length > 0 ? (expandedNodes[node.level] ? '▼' : '▶') : null}
          </div>
          <div className="inheritance-tree-node-title">
            {node.name}
            <span className="node-level-badge">{levelOptions.find(opt => opt.value === node.level)?.label}</span>
          </div>
        </div>
        
        <div className="inheritance-tree-parameters">
          {node.parameters.map((param) => (
            <div 
              key={param.id} 
              className={`inheritance-tree-parameter ${param.inherited ? 'inherited' : 'custom'} ${param.override ? 'override' : ''}`}
            >
              <div className="parameter-name">
                {param.parameter_name}
                {param.inherited && (
                  <span className="inheritance-badge">
                    {param.override ? '已覆盖' : '已继承'} ({param.source})
                  </span>
                )}
              </div>
              <div className="parameter-value">{typeof param.parameter_value === 'object' ? JSON.stringify(param.parameter_value) : param.parameter_value}</div>
              <div className="parameter-type">{param.parameter_type}</div>
            </div>
          ))}
        </div>
        
        {node.children?.length > 0 && expandedNodes[node.level] && (
          <div className="inheritance-tree-children">
            {node.children.map(child => renderInheritanceTree(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="parameter-management-main">
      {/* 头部 */}
      <div className="section-header">
        <div className="header-left">
          <h2>参数管理主界面</h2>
          <button className="btn btn-secondary" onClick={onBack}>
            返回
          </button>
        </div>
        <div className="header-right">
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="level-selector"
            disabled={loading}
          >
            {levelOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 状态消息 */}
      {success && <div className="success-message">{success}</div>}
      {error && <div className="error-message">{error}</div>}

      {/* 参数模板列表 */}
      <div className="parameter-templates-section">
        <div className="section-title">
          <h3>{levelOptions.find(option => option.value === selectedLevel)?.label}参数模板</h3>
          <div className="template-actions">
            {((selectedLevel === 'system') || 
              (selectedSupplier && 
               (selectedLevel === 'supplier' || 
                selectedLevel === 'model_type' || 
                selectedLevel === 'model_capability' || 
                selectedLevel === 'model' || 
                selectedLevel === 'agent'))) && 
             parameterTemplates.length > 0 && (
              <div className="template-selection">
                <select
                  value={selectedParameterTemplate || ''}
                  onChange={(e) => setSelectedParameterTemplate(e.target.value)}
                  disabled={loading || applyingTemplate}
                  className="template-select"
                >
                  <option value="">选择参数模板</option>
                  {parameterTemplates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.template_name || `模板 ${template.id}`}
                    </option>
                  ))}
                </select>
                <button
                  className="btn btn-primary"
                  onClick={handleApplyTemplate}
                  disabled={loading || applyingTemplate || !selectedParameterTemplate}
                >
                  {applyingTemplate ? '应用中...' : '应用模板'}
                </button>
              </div>
            )}
            <button
              className="btn btn-primary"
              onClick={handleAddParameterClick}
              disabled={loading || saving}
            >
              添加参数
            </button>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">加载参数模板中...</div>
        ) : parameters.length === 0 ? (
          <div className="empty-state">暂无参数模板，请添加参数</div>
        ) : (
          <div className="parameters-tree-container">
            {/* 批量操作按钮 */}
            {showBatchActions && (
              <div className="batch-actions-bar">
                <div className="batch-selection-info">
                  <span>已选择 {selectedParameters.length} 个参数</span>
                </div>
                <div className="batch-actions-buttons">
                  <button 
                    className="btn btn-primary btn-small"
                    onClick={handleBatchEditParameters}
                    disabled={saving || selectedParameters.length === 0}
                  >
                    批量编辑
                  </button>
                  <button 
                    className="btn btn-danger btn-small"
                    onClick={handleBatchDeleteParameters}
                    disabled={saving || selectedParameters.length === 0}
                  >
                    批量删除
                  </button>
                </div>
              </div>
            )}
            
            <div className="parameters-table-container">
              <table className="parameters-table">
                <thead>
                  <tr>
                    <th className="checkbox-column">
                      {showBatchActions && (
                        <input
                          type="checkbox"
                          checked={parameters.filter(p => !p.inherited).length > 0 && selectedParameters.length === parameters.filter(p => !p.inherited).length}
                          onChange={handleSelectAllParameters}
                          disabled={saving || parameters.filter(p => !p.inherited).length === 0}
                        />
                      )}
                    </th>
                    <th>参数名称</th>
                    <th>参数值</th>
                    <th>类型</th>
                    <th>默认值</th>
                    <th>描述</th>
                    <th>必填</th>
                    <th>继承来源</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {parameters.map((param) => (
                    <tr key={param.id} className={param.inherited ? 'inherited-parameter' : 'custom-parameter'}>
                      <td className="checkbox-column">
                        {showBatchActions && (
                          <input
                            type="checkbox"
                            checked={selectedParameters.includes(param.id)}
                            onChange={() => handleSelectParameter(param.id)}
                            disabled={saving || param.inherited}
                          />
                        )}
                      </td>
                      <td>
                        {param.parameter_name}
                        {param.inherited && <span className="inherited-badge">继承</span>}
                      </td>
                      <td>{typeof param.parameter_value === 'object' ? JSON.stringify(param.parameter_value) : param.parameter_value}</td>
                      <td>{param.parameter_type}</td>
                      <td>{typeof param.default_value === 'object' ? JSON.stringify(param.default_value) : param.default_value}</td>
                      <td>{param.description || '-'}</td>
                      <td>{param.is_required ? '是' : '否'}</td>
                      <td>
                        {param.inherited ? getInheritanceSourceName(param.inheritance_source_type, param.inheritance_source_id) : '-'}
                      </td>
                      <td>
                        <div className="parameter-actions">
                          <button
                            className="btn btn-secondary btn-small"
                            onClick={() => handleEditParameterClick(param)}
                            disabled={saving || param.inherited}
                          >
                            编辑
                          </button>
                          <button
                            className="btn btn-danger btn-small"
                            onClick={() => handleDeleteParameter(param.id)}
                            disabled={saving || param.inherited}
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
          </div>
        )}
      </div>

      {/* 继承关系可视化 */}
      <div className="inheritance-visualization-section">
        <div className="section-title">
          <h3>参数继承关系可视化</h3>
          <button 
            className="btn btn-secondary"
            onClick={loadInheritanceTree}
            disabled={treeLoading}
          >
            刷新继承树
          </button>
        </div>
        
        {treeLoading ? (
          <div className="loading-state">加载参数继承树中...</div>
        ) : inheritanceTree ? (
          <div className="inheritance-tree-container">
            <div className="inheritance-tree">
              {renderInheritanceTree(inheritanceTree)}
            </div>
            
            <div className="inheritance-legend">
              <h4>图例：</h4>
              <div className="legend-item">
                <div className="legend-color custom"></div>
                <span>自定义参数</span>
              </div>
              <div className="legend-item">
                <div className="legend-color inherited"></div>
                <span>继承参数</span>
              </div>
              <div className="legend-item">
                <div className="legend-color override"></div>
                <span>已覆盖参数</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">暂无参数继承关系数据</div>
        )}
        
        <div className="inheritance-description">
          <p>参数继承规则：</p>
          <ul>
            <li>高级别参数会自动继承到低级别</li>
            <li>低级别可以覆盖高级别的参数值</li>
            <li>继承的参数会显示为灰色，不可直接编辑</li>
            <li>可在低级别添加新的自定义参数</li>
          </ul>
        </div>
      </div>

      {/* 参数编辑模态框 */}
      <ParameterModal
        isOpen={isParameterModalOpen}
        onClose={handleCloseParameterModal}
        onSave={handleSaveParameterData}
        parameter={editingParameter}
        mode={parameterModalMode}
      />

      {/* 批量参数编辑模态框 */}
      <BatchParameterModal
        isOpen={isBatchModalOpen}
        onClose={handleCloseBatchModal}
        onSave={handleSaveBatchParameterData}
        selectedParameters={parameters.filter(p => selectedParameters.includes(p.id))}
      />
    </div>
  );
};

export default ParameterManagementMain;
