import React, { useState, useEffect } from 'react';
import './AgentParameterConfig.css';

const AgentParameterConfig = ({ 
  agent = null, 
  onParametersChange,
  initialParameters = {}
}) => {
  const [parameters, setParameters] = useState(initialParameters);
  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  // 默认参数配置
  const defaultParameters = {
    temperature: 0.7,
    max_tokens: 2000,
    top_p: 0.9,
    frequency_penalty: 0,
    presence_penalty: 0,
    stop_sequences: [],
    system_prompt: '',
    response_format: 'text'
  };

  // 参数预设
  const parameterPresets = [
    {
      id: 'balanced',
      name: '平衡模式',
      description: '适合大多数翻译场景',
      parameters: {
        temperature: 0.7,
        max_tokens: 2000,
        top_p: 0.9,
        frequency_penalty: 0,
        presence_penalty: 0
      }
    },
    {
      id: 'creative',
      name: '创意模式',
      description: '适合文学翻译和创意内容',
      parameters: {
        temperature: 0.9,
        max_tokens: 3000,
        top_p: 0.95,
        frequency_penalty: 0.1,
        presence_penalty: 0.1
      }
    },
    {
      id: 'precise',
      name: '精确模式',
      description: '适合技术文档和精确翻译',
      parameters: {
        temperature: 0.3,
        max_tokens: 1500,
        top_p: 0.8,
        frequency_penalty: 0,
        presence_penalty: 0
      }
    },
    {
      id: 'fast',
      name: '快速模式',
      description: '适合快速响应和简单翻译',
      parameters: {
        temperature: 0.5,
        max_tokens: 1000,
        top_p: 0.85,
        frequency_penalty: 0,
        presence_penalty: 0
      }
    }
  ];

  // 初始化参数
  useEffect(() => {
    setPresets(parameterPresets);
    
    // 如果没有初始参数，使用默认参数
    if (Object.keys(initialParameters).length === 0) {
      setParameters(defaultParameters);
      if (onParametersChange) {
        onParametersChange(defaultParameters);
      }
    }
  }, [initialParameters]);

  // 处理参数变化
  const handleParameterChange = (paramName, value) => {
    const newParameters = {
      ...parameters,
      [paramName]: value
    };
    
    setParameters(newParameters);
    
    if (onParametersChange) {
      onParametersChange(newParameters);
    }
  };

  // 应用预设
  const applyPreset = (presetId) => {
    const preset = presets.find(p => p.id === presetId);
    if (preset) {
      const newParameters = {
        ...parameters,
        ...preset.parameters
      };
      
      setParameters(newParameters);
      setSelectedPreset(presetId);
      
      if (onParametersChange) {
        onParametersChange(newParameters);
      }
    }
  };

  // 重置为默认参数
  const resetToDefault = () => {
    setParameters(defaultParameters);
    setSelectedPreset('');
    
    if (onParametersChange) {
      onParametersChange(defaultParameters);
    }
  };

  // 渲染参数输入控件
  const renderParameterInput = (paramName, paramConfig) => {
    const value = parameters[paramName] ?? paramConfig.default;
    
    switch (paramConfig.type) {
      case 'range':
        return (
          <div className="parameter-input">
            <input
              type="range"
              min={paramConfig.min}
              max={paramConfig.max}
              step={paramConfig.step}
              value={value}
              onChange={(e) => handleParameterChange(paramName, parseFloat(e.target.value))}
            />
            <span className="parameter-value">{value}</span>
          </div>
        );
        
      case 'number':
        return (
          <div className="parameter-input">
            <input
              type="number"
              min={paramConfig.min}
              max={paramConfig.max}
              step={paramConfig.step}
              value={value}
              onChange={(e) => handleParameterChange(paramName, parseInt(e.target.value))}
            />
          </div>
        );
        
      case 'textarea':
        return (
          <div className="parameter-input">
            <textarea
              value={value}
              onChange={(e) => handleParameterChange(paramName, e.target.value)}
              placeholder={paramConfig.placeholder}
              rows={3}
            />
          </div>
        );
        
      default:
        return (
          <div className="parameter-input">
            <input
              type="text"
              value={value}
              onChange={(e) => handleParameterChange(paramName, e.target.value)}
              placeholder={paramConfig.placeholder}
            />
          </div>
        );
    }
  };

  // 参数配置定义
  const parameterConfigs = {
    temperature: {
      label: '温度 (Temperature)',
      type: 'range',
      min: 0,
      max: 2,
      step: 0.1,
      default: 0.7,
      description: '控制输出的随机性，值越高输出越随机'
    },
    max_tokens: {
      label: '最大令牌数 (Max Tokens)',
      type: 'number',
      min: 100,
      max: 4000,
      step: 100,
      default: 2000,
      description: '控制生成文本的最大长度'
    },
    top_p: {
      label: 'Top P',
      type: 'range',
      min: 0,
      max: 1,
      step: 0.05,
      default: 0.9,
      description: '控制输出的多样性，值越小输出越集中'
    },
    frequency_penalty: {
      label: '频率惩罚 (Frequency Penalty)',
      type: 'range',
      min: -2,
      max: 2,
      step: 0.1,
      default: 0,
      description: '降低重复词汇的使用频率'
    },
    presence_penalty: {
      label: '存在惩罚 (Presence Penalty)',
      type: 'range',
      min: -2,
      max: 2,
      step: 0.1,
      default: 0,
      description: '降低重复主题的出现频率'
    },
    system_prompt: {
      label: '系统提示 (System Prompt)',
      type: 'textarea',
      default: '',
      placeholder: '输入系统提示，指导智能体的行为',
      description: '系统级别的提示，影响智能体的整体行为'
    }
  };

  if (!agent) {
    return (
      <div className="agent-parameter-config empty">
        <div className="empty-state">
          <div className="empty-icon">⚙️</div>
          <p>请选择一个智能体进行参数配置</p>
        </div>
      </div>
    );
  }

  return (
    <div className="agent-parameter-config">
      {/* 头部 */}
      <div className="config-header">
        <div className="agent-info">
          <h4>{agent.name || agent.id}</h4>
          <span className="agent-type">{agent.type || '通用智能体'}</span>
        </div>
        <button 
          className="expand-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '收起' : '展开'}参数配置
        </button>
      </div>

      {/* 预设选择 */}
      <div className="preset-section">
        <label>快速预设：</label>
        <div className="preset-buttons">
          {presets.map(preset => (
            <button
              key={preset.id}
              className={`preset-button ${selectedPreset === preset.id ? 'active' : ''}`}
              onClick={() => applyPreset(preset.id)}
              title={preset.description}
            >
              {preset.name}
            </button>
          ))}
          <button
            className="preset-button reset"
            onClick={resetToDefault}
            title="重置为默认参数"
          >
            重置
          </button>
        </div>
      </div>

      {/* 详细参数配置 */}
      {isExpanded && (
        <div className="detailed-parameters">
          <h5>详细参数配置</h5>
          
          {Object.entries(parameterConfigs).map(([paramName, config]) => (
            <div key={paramName} className="parameter-item">
              <div className="parameter-label">
                <span>{config.label}</span>
                {config.description && (
                  <span className="parameter-description">{config.description}</span>
                )}
              </div>
              {renderParameterInput(paramName, config)}
            </div>
          ))}
        </div>
      )}

      {/* 当前参数摘要 */}
      <div className="parameter-summary">
        <h5>当前参数设置</h5>
        <div className="summary-grid">
          <div className="summary-item">
            <span>温度:</span>
            <span>{parameters.temperature}</span>
          </div>
          <div className="summary-item">
            <span>最大令牌:</span>
            <span>{parameters.max_tokens}</span>
          </div>
          <div className="summary-item">
            <span>Top P:</span>
            <span>{parameters.top_p}</span>
          </div>
          <div className="summary-item">
            <span>频率惩罚:</span>
            <span>{parameters.frequency_penalty}</span>
          </div>
          <div className="summary-item">
            <span>存在惩罚:</span>
            <span>{parameters.presence_penalty}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentParameterConfig;