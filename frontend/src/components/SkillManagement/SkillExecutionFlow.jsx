import React, { useState, useEffect } from 'react';
import { skillApi } from '../../services/skillApi';

function SkillExecutionFlow({ skillId, skillName }) {
  const [executionFlow, setExecutionFlow] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingFlow, setEditingFlow] = useState(false);
  const [newFlow, setNewFlow] = useState([]);

  useEffect(() => {
    loadExecutionFlow();
  }, [skillId]);

  const loadExecutionFlow = async () => {
    try {
      setLoading(true);
      const data = await skillApi.getExecutionFlow(skillId);
      setExecutionFlow(data.steps || []);
      setNewFlow(data.steps || []);
    } catch (err) {
      console.error('加载执行流程失败:', err);
      setExecutionFlow([]);
      setNewFlow([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveFlow = async () => {
    try {
      await skillApi.updateExecutionFlow(skillId, { steps: newFlow });
      setExecutionFlow(newFlow);
      setEditingFlow(false);
      setError('');
    } catch (err) {
      setError('保存执行流程失败: ' + err.message);
    }
  };

  const handleAddStep = () => {
    setNewFlow([...newFlow, {
      type: 'script',
      name: '',
      description: '',
      parameters: {},
      order: newFlow.length + 1
    }]);
  };

  const handleRemoveStep = (index) => {
    const updatedFlow = newFlow.filter((_, i) => i !== index);
    // 重新排序
    const reorderedFlow = updatedFlow.map((step, i) => ({
      ...step,
      order: i + 1
    }));
    setNewFlow(reorderedFlow);
  };

  const handleStepChange = (index, field, value) => {
    const updatedFlow = [...newFlow];
    updatedFlow[index] = {
      ...updatedFlow[index],
      [field]: value
    };
    setNewFlow(updatedFlow);
  };

  const handleParameterChange = (index, paramKey, paramValue) => {
    const updatedFlow = [...newFlow];
    updatedFlow[index].parameters = {
      ...updatedFlow[index].parameters,
      [paramKey]: paramValue
    };
    setNewFlow(updatedFlow);
  };

  const getStepIcon = (type) => {
    const icons = {
      script: '📜',
      template: '📝',
      api_call: '🌐',
      database: '🗄️',
      file: '📁',
      condition: '⚖️',
      loop: '🔄'
    };
    return icons[type] || '⚙️';
  };

  if (loading) {
    return <div className="execution-flow"><div className="loading-spinner"></div> 加载执行流程中...</div>;
  }

  return (
    <div className="execution-flow">
      <div className="flow-header">
        <h3>执行流程管理 - {skillName}</h3>
        <div className="flow-actions">
          {!editingFlow ? (
            <button 
              className="btn btn-primary"
              onClick={() => setEditingFlow(true)}
            >
              编辑流程
            </button>
          ) : (
            <>
              <button 
                className="btn btn-success"
                onClick={handleSaveFlow}
              >
                保存
              </button>
              <button 
                className="btn btn-outline"
                onClick={() => {
                  setNewFlow(executionFlow);
                  setEditingFlow(false);
                }}
              >
                取消
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {editingFlow ? (
        <div className="flow-editor">
          <div className="flow-header" style={{marginBottom: '16px'}}>
            <h4>编辑执行流程</h4>
            <button 
              className="btn btn-primary btn-sm"
              onClick={handleAddStep}
            >
              + 添加步骤
            </button>
          </div>

          {newFlow.length === 0 ? (
            <div className="empty-state">暂无执行步骤，点击"添加步骤"开始配置</div>
          ) : (
            <div>
              {newFlow.map((step, index) => (
                <div key={index} className="flow-step" style={{marginBottom: '16px'}}>
                  <div className="step-number">{step.order}</div>
                  <div className="step-info" style={{flex: 1}}>
                    <div style={{display: 'flex', gap: '12px', marginBottom: '8px'}}>
                      <div className="form-field" style={{flex: 1}}>
                        <label>类型:</label>
                        <select 
                          value={step.type}
                          onChange={e => handleStepChange(index, 'type', e.target.value)}
                        >
                          <option value="script">脚本</option>
                          <option value="template">模板</option>
                          <option value="api_call">API调用</option>
                          <option value="database">数据库操作</option>
                          <option value="file">文件操作</option>
                          <option value="condition">条件判断</option>
                          <option value="loop">循环</option>
                        </select>
                      </div>
                      
                      <div className="form-field" style={{flex: 2}}>
                        <label>名称:</label>
                        <input 
                          type="text"
                          value={step.name}
                          onChange={e => handleStepChange(index, 'name', e.target.value)}
                          placeholder="步骤名称"
                        />
                      </div>
                    </div>
                    
                    <div className="form-field">
                      <label>描述:</label>
                      <textarea 
                        value={step.description}
                        onChange={e => handleStepChange(index, 'description', e.target.value)}
                        placeholder="步骤描述"
                        rows="2"
                        style={{width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '6px'}}
                      />
                    </div>
                    
                    <div style={{marginTop: '8px'}}>
                      <label>参数:</label>
                      <div style={{display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px'}}>
                        {Object.entries(step.parameters || {}).map(([key, value]) => (
                          <div key={key} style={{display: 'flex', gap: '8px'}}>
                            <input 
                              type="text"
                              value={key}
                              onChange={e => {
                                const newParams = { ...step.parameters };
                                delete newParams[key];
                                newParams[e.target.value] = value;
                                handleStepChange(index, 'parameters', newParams);
                              }}
                              placeholder="参数名"
                              style={{flex: 1, padding: '6px 8px', border: '1px solid #d1d5db', borderRadius: '4px'}}
                            />
                            <input 
                              type="text"
                              value={value}
                              onChange={e => handleParameterChange(index, key, e.target.value)}
                              placeholder="参数值"
                              style={{flex: 2, padding: '6px 8px', border: '1px solid #d1d5db', borderRadius: '4px'}}
                            />
                          </div>
                        ))}
                        <button 
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleParameterChange(index, `param_${Date.now()}`, '')}
                          style={{alignSelf: 'flex-start'}}
                        >
                          + 添加参数
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="step-actions">
                    <button 
                      className="btn btn-danger btn-sm"
                      onClick={() => handleRemoveStep(index)}
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="flow-steps">
          {executionFlow.length === 0 ? (
            <div className="empty-state">暂无执行流程配置</div>
          ) : (
            <div>
              {executionFlow.map((step, index) => (
                <div key={index} className="flow-step">
                  <div className="step-number">{step.order}</div>
                  <div className="step-info">
                    <div className="step-name">{step.name || `步骤 ${step.order}`}</div>
                    <div className="step-description">
                      <span style={{fontWeight: '600', color: '#3b82f6'}}>{step.type}</span>
                      {step.description && (
                        <span style={{marginLeft: '8px', color: '#6b7280'}}>{step.description}</span>
                      )}
                    </div>
                    {step.parameters && Object.keys(step.parameters).length > 0 && (
                      <div style={{marginTop: '4px', fontSize: '12px', color: '#9ca3af'}}>
                        参数: {Object.entries(step.parameters).map(([key, value]) => (
                          <span key={key} style={{marginRight: '8px'}}>
                            {key}: {value}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  {index < executionFlow.length - 1 && (
                    <div style={{textAlign: 'center', color: '#d1d5db', fontSize: '16px', margin: '8px 0'}}>↓</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SkillExecutionFlow;