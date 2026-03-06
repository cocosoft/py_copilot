/**
 * 知识图谱配置组件
 * 
 * 设置入口的核心组件，提供实体类型配置、关系类型配置、提取策略配置、质量规则配置
 * 采用标签页设计，复用现有的 EntityConfigManagement 组件
 */

import React, { useState, useEffect } from 'react';
import EntityConfigManagement from '../EntityConfigManagement';
import RelationTypeConfig from './RelationTypeConfig';
import './KnowledgeGraphConfig.css';

/**
 * 知识图谱配置主组件
 * 
 * @returns {JSX.Element} 知识图谱配置界面
 */
const KnowledgeGraphConfig = () => {
  // 当前激活的标签页
  const [activeTab, setActiveTab] = useState('entity-types');
  
  // 标签页配置
  const tabs = [
    { id: 'entity-types', label: '实体类型', icon: '🏷️', description: '配置系统中可用的实体类型' },
    { id: 'relation-types', label: '关系类型', icon: '🔗', description: '配置实体间的关系类型' },
    { id: 'extraction', label: '提取策略', icon: '⚡', description: '配置实体和关系的提取策略' },
    { id: 'quality', label: '质量规则', icon: '✅', description: '配置知识图谱质量检查规则' }
  ];

  /**
   * 渲染标签页内容
   * @returns {JSX.Element} 当前标签页的内容
   */
  const renderTabContent = () => {
    switch (activeTab) {
      case 'entity-types':
        return <EntityConfigManagement />;
      
      case 'relation-types':
        return <RelationTypeConfig />;
      
      case 'extraction':
        return <ExtractionStrategyConfig />;
      
      case 'quality':
        return <QualityRuleConfig />;
      
      default:
        return <EntityConfigManagement />;
    }
  };

  return (
    <div className="knowledge-graph-config">
      {/* 标签页导航 */}
      <div className="config-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            title={tab.description}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* 标签页内容区域 */}
      <div className="config-content">
        {renderTabContent()}
      </div>
    </div>
  );
};

/**
 * 提取策略配置组件（占位实现）
 * 
 * @returns {JSX.Element} 提取策略配置界面
 */
const ExtractionStrategyConfig = () => {
  const [strategies, setStrategies] = useState([
    {
      id: 'llm-extraction',
      name: 'LLM智能提取',
      description: '使用大语言模型自动识别实体和关系',
      enabled: true,
      priority: 1,
      config: {
        model: 'deepseek-r1:1.5b',
        temperature: 0.3,
        maxTokens: 2000
      }
    },
    {
      id: 'rule-extraction',
      name: '规则提取',
      description: '基于预定义规则识别实体',
      enabled: true,
      priority: 2,
      config: {
        useRegex: true,
        useDictionary: true
      }
    },
    {
      id: 'statistical-extraction',
      name: '统计提取',
      description: '基于统计方法识别实体',
      enabled: false,
      priority: 3,
      config: {}
    }
  ]);

  const handleToggle = (id) => {
    setStrategies(prev => 
      prev.map(s => s.id === id ? { ...s, enabled: !s.enabled } : s)
    );
  };

  const handlePriorityChange = (id, delta) => {
    setStrategies(prev => {
      const index = prev.findIndex(s => s.id === id);
      if (index === -1) return prev;
      
      const newIndex = index + delta;
      if (newIndex < 0 || newIndex >= prev.length) return prev;
      
      const newStrategies = [...prev];
      [newStrategies[index], newStrategies[newIndex]] = 
        [newStrategies[newIndex], newStrategies[index]];
      
      // 更新优先级
      return newStrategies.map((s, i) => ({ ...s, priority: i + 1 }));
    });
  };

  return (
    <div className="extraction-strategy-config">
      <div className="config-section-header">
        <h3>提取策略配置</h3>
        <p className="section-description">
          配置实体和关系的提取策略，系统将按照优先级顺序依次应用
        </p>
      </div>

      <div className="strategy-list">
        {strategies
          .sort((a, b) => a.priority - b.priority)
          .map((strategy, index) => (
            <div 
              key={strategy.id} 
              className={`strategy-card ${strategy.enabled ? 'enabled' : 'disabled'}`}
            >
              <div className="strategy-header">
                <div className="strategy-info">
                  <span className="priority-badge">{strategy.priority}</span>
                  <h4 className="strategy-name">{strategy.name}</h4>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={strategy.enabled}
                      onChange={() => handleToggle(strategy.id)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
                <div className="strategy-actions">
                  <button 
                    className="action-btn"
                    onClick={() => handlePriorityChange(strategy.id, -1)}
                    disabled={index === 0}
                    title="上移"
                  >
                    ↑
                  </button>
                  <button 
                    className="action-btn"
                    onClick={() => handlePriorityChange(strategy.id, 1)}
                    disabled={index === strategies.length - 1}
                    title="下移"
                  >
                    ↓
                  </button>
                </div>
              </div>
              <p className="strategy-description">{strategy.description}</p>
              
              {strategy.enabled && Object.keys(strategy.config).length > 0 && (
                <div className="strategy-config">
                  <h5>配置参数</h5>
                  <div className="config-params">
                    {Object.entries(strategy.config).map(([key, value]) => (
                      <div key={key} className="config-param">
                        <label>{key}:</label>
                        <span className="param-value">
                          {typeof value === 'boolean' ? (value ? '是' : '否') : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
      </div>

      <div className="config-actions">
        <button className="btn btn-primary">
          保存配置
        </button>
        <button className="btn btn-secondary">
          重置默认
        </button>
      </div>
    </div>
  );
};

/**
 * 质量规则配置组件（占位实现）
 * 
 * @returns {JSX.Element} 质量规则配置界面
 */
const QualityRuleConfig = () => {
  const [rules, setRules] = useState([
    {
      id: 'min-confidence',
      name: '最小置信度',
      description: '实体和关系的置信度必须达到此阈值',
      enabled: true,
      value: 0.7,
      type: 'number',
      min: 0,
      max: 1,
      step: 0.1
    },
    {
      id: 'required-properties',
      name: '必填属性检查',
      description: '实体必须包含所有必填属性',
      enabled: true,
      value: true,
      type: 'boolean'
    },
    {
      id: 'duplicate-detection',
      name: '重复实体检测',
      description: '自动检测并标记相似实体',
      enabled: true,
      value: 0.85,
      type: 'number',
      min: 0,
      max: 1,
      step: 0.05
    },
    {
      id: 'relation-consistency',
      name: '关系一致性检查',
      description: '检查关系是否符合定义的规则',
      enabled: true,
      value: true,
      type: 'boolean'
    }
  ]);

  const handleToggle = (id) => {
    setRules(prev => 
      prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r)
    );
  };

  const handleValueChange = (id, value) => {
    setRules(prev => 
      prev.map(r => r.id === id ? { ...r, value } : r)
    );
  };

  const renderValueInput = (rule) => {
    if (rule.type === 'boolean') {
      return (
        <label className="toggle-switch small">
          <input
            type="checkbox"
            checked={rule.value}
            onChange={(e) => handleValueChange(rule.id, e.target.checked)}
            disabled={!rule.enabled}
          />
          <span className="toggle-slider"></span>
        </label>
      );
    }

    if (rule.type === 'number') {
      return (
        <div className="number-input-wrapper">
          <input
            type="range"
            min={rule.min}
            max={rule.max}
            step={rule.step}
            value={rule.value}
            onChange={(e) => handleValueChange(rule.id, parseFloat(e.target.value))}
            disabled={!rule.enabled}
          />
          <span className="number-value">{rule.value}</span>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="quality-rule-config">
      <div className="config-section-header">
        <h3>质量规则配置</h3>
        <p className="section-description">
          配置知识图谱的质量检查规则，确保数据质量
        </p>
      </div>

      <div className="rule-list">
        {rules.map(rule => (
          <div 
            key={rule.id} 
            className={`rule-card ${rule.enabled ? 'enabled' : 'disabled'}`}
          >
            <div className="rule-header">
              <div className="rule-info">
                <h4 className="rule-name">{rule.name}</h4>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={rule.enabled}
                    onChange={() => handleToggle(rule.id)}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              <div className="rule-value">
                {renderValueInput(rule)}
              </div>
            </div>
            <p className="rule-description">{rule.description}</p>
          </div>
        ))}
      </div>

      <div className="config-actions">
        <button className="btn btn-primary">
          保存配置
        </button>
        <button className="btn btn-secondary">
          重置默认
        </button>
      </div>
    </div>
  );
};

export default KnowledgeGraphConfig;
