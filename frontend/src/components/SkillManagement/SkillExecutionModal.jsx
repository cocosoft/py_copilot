import React, { useState, useEffect } from 'react';
import { useSkillExecution } from '../../hooks/useSkills';
import './SkillManagement.css';

function SkillExecutionModal({ skill, onClose, onExecutionComplete }) {
  const { executing, result, error, executeSkill } = useSkillExecution();
  const [taskData, setTaskData] = useState('');
  const [showResult, setShowResult] = useState(false);
  const [parameters, setParameters] = useState({});

  useEffect(() => {
    if (result) {
      setShowResult(true);
    }
  }, [result]);

  const handleParameterChange = (paramName, value) => {
    setParameters(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  const renderParameterForm = () => {
    if (!skill.parameters_schema || !skill.parameters_schema.properties) {
      return null;
    }

    const { properties, required = [] } = skill.parameters_schema;

    return (
      <div className="skill-execution-parameters">
        <h3>技能参数</h3>
        <div className="parameter-form">
          {Object.entries(properties).map(([paramName, paramConfig]) => {
            const isRequired = required.includes(paramName);
            const displayName = paramConfig.title || paramName;
            const description = paramConfig.description;

            return (
              <div className="parameter-field" key={paramName}>
                <label>
                  {displayName}
                  {isRequired && <span className="required">*</span>}
                </label>
                {description && (
                  <p className="parameter-description">{description}</p>
                )}
                {renderParameterInput(paramName, paramConfig, isRequired)}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderParameterInput = (paramName, paramConfig, isRequired) => {
    const { type } = paramConfig;
    const value = parameters[paramName] || '';

    switch (type) {
      case 'string':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            placeholder={paramConfig.default || `请输入${paramConfig.title || paramName}`}
            disabled={executing}
            required={isRequired}
          />
        );
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleParameterChange(paramName, Number(e.target.value))}
            placeholder={paramConfig.default || `请输入${paramConfig.title || paramName}`}
            disabled={executing}
            required={isRequired}
            min={paramConfig.min}
            max={paramConfig.max}
            step={paramConfig.step || 1}
          />
        );
      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => handleParameterChange(paramName, e.target.checked)}
            disabled={executing}
          />
        );
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            disabled={executing}
            required={isRequired}
          >
            <option value="">请选择</option>
            {paramConfig.enum?.map(option => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            placeholder={paramConfig.default || `请输入${paramConfig.title || paramName}`}
            rows={3}
            disabled={executing}
            required={isRequired}
          />
        );
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            placeholder={`请输入${paramConfig.title || paramName}`}
            disabled={executing}
            required={isRequired}
          />
        );
    }
  };

  const handleExecute = async () => {
    if (!taskData.trim()) {
      alert('请输入任务内容');
      return;
    }
    
    try {
      await executeSkill(skill.id, taskData, parameters);
      if (onExecutionComplete) {
        onExecutionComplete();
      }
    } catch (err) {
      console.error('Failed to execute skill:', err);
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleReset = () => {
    setTaskData('');
    setParameters({});
    setShowResult(false);
  };

  return (
    <div className="skill-modal-backdrop" onClick={handleBackdropClick}>
      <div className="skill-modal skill-execution-modal">
        <div className="skill-modal-header">
          <h2>执行技能: {skill.name}</h2>
          <button className="close-btn" onClick={onClose} disabled={executing}>
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        
        <div className="skill-modal-body">
          <div className="skill-execution-section">
            <div className="skill-execution-info">
              <h3>技能信息</h3>
              <p><strong>版本:</strong> v{skill.version}</p>
              <p><strong>状态:</strong> {skill.status === 'enabled' ? '已启用' : '已禁用'}</p>
              {skill.tags && skill.tags.length > 0 && (
                <p><strong>标签:</strong> {skill.tags.join(', ')}</p>
              )}
            </div>
            
            <div className="skill-execution-task">
              <h3>任务内容</h3>
              <textarea
                value={taskData}
                onChange={(e) => setTaskData(e.target.value)}
                placeholder={`请输入要让 ${skill.name} 执行的任务...`}
                rows={6}
                disabled={executing}
                className="task-input"
              />
              
              {error && (
                <div className="execution-error">
                  <strong>执行失败:</strong> {error}
                </div>
              )}
              
              {result && !error && (
                <div className="execution-success">
                  <strong>执行成功!</strong> 技能已完成执行
                </div>
              )}
            </div>
            
            {renderParameterForm()}
            
            {showResult && result && (
              <div className="skill-execution-result">
                <h3>执行结果</h3>
                <div className="result-content">
                  {typeof result === 'object' ? (
                    <pre>{JSON.stringify(result, null, 2)}</pre>
                  ) : (
                    <p>{String(result)}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="skill-modal-footer execution-footer">
          {showResult && (
            <button
              className="reset-btn"
              onClick={handleReset}
              disabled={executing}
            >
              执行新任务
            </button>
          )}
          
          <div className="execution-buttons">
            <button
              className="cancel-btn"
              onClick={onClose}
              disabled={executing}
            >
              关闭
            </button>
            <button
              className="execute-btn"
              onClick={handleExecute}
              disabled={executing || !taskData.trim()}
            >
              {executing ? (
                <>
                  <span className="loading-spinner-small"></span>
                  执行中...
                </>
              ) : (
                '执行技能'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SkillExecutionModal;
