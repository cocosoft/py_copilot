/**
 * 实体识别配置面板
 *
 * 优化实体识别配置界面，简化操作流程
 *
 * 任务编号: Phase2-Week5
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Switch, Select, Slider, Input, Badge } from '../../UnifiedComponentLibrary';

/**
 * 实体识别配置面板组件
 * @param {Object} props - 组件属性
 * @param {Object} props.initialConfig - 初始配置
 * @param {Function} props.onConfigChange - 配置变更回调
 * @param {Function} props.onSave - 保存回调
 */
const EntityConfigPanel = ({
  initialConfig = {},
  onConfigChange,
  onSave,
}) => {
  const [config, setConfig] = useState({
    // 实体类型配置
    entityTypes: {
      person: { enabled: true, priority: 5 },
      organization: { enabled: true, priority: 4 },
      location: { enabled: true, priority: 4 },
      date: { enabled: true, priority: 3 },
      email: { enabled: true, priority: 2 },
      phone: { enabled: true, priority: 2 },
      url: { enabled: false, priority: 1 },
      custom: { enabled: false, priority: 1, patterns: [] },
    },
    // 识别参数
    recognitionParams: {
      confidenceThreshold: 0.7,
      maxEntities: 50,
      enableContextAnalysis: true,
      enableFuzzyMatch: false,
    },
    // 处理选项
    processingOptions: {
      autoSave: true,
      realTimePreview: true,
      highlightEntities: true,
      showConfidence: true,
    },
    ...initialConfig,
  });

  const [activeTab, setActiveTab] = useState('types');
  const [hasChanges, setHasChanges] = useState(false);

  // 实体类型选项
  const entityTypeOptions = [
    { key: 'person', label: '人物', description: '识别人名、称谓等' },
    { key: 'organization', label: '组织', description: '识别公司、机构等' },
    { key: 'location', label: '地点', description: '识别地名、地址等' },
    { key: 'date', label: '日期', description: '识别日期、时间等' },
    { key: 'email', label: '邮箱', description: '识别电子邮件地址' },
    { key: 'phone', label: '电话', description: '识别电话号码' },
    { key: 'url', label: '链接', description: '识别URL链接' },
    { key: 'custom', label: '自定义', description: '自定义实体模式' },
  ];

  // 更新配置
  const updateConfig = (path, value) => {
    const newConfig = { ...config };
    const keys = path.split('.');
    let current = newConfig;

    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }

    current[keys[keys.length - 1]] = value;
    setConfig(newConfig);
    setHasChanges(true);

    if (onConfigChange) {
      onConfigChange(newConfig);
    }
  };

  // 切换实体类型启用状态
  const toggleEntityType = (typeKey) => {
    const currentType = config.entityTypes[typeKey];
    updateConfig(`entityTypes.${typeKey}.enabled`, !currentType.enabled);
  };

  // 更新实体类型优先级
  const updateEntityPriority = (typeKey, priority) => {
    updateConfig(`entityTypes.${typeKey}.priority`, priority);
  };

  // 保存配置
  const handleSave = () => {
    if (onSave) {
      onSave(config);
    }
    setHasChanges(false);
  };

  // 重置配置
  const handleReset = () => {
    setConfig({
      entityTypes: {
        person: { enabled: true, priority: 5 },
        organization: { enabled: true, priority: 4 },
        location: { enabled: true, priority: 4 },
        date: { enabled: true, priority: 3 },
        email: { enabled: true, priority: 2 },
        phone: { enabled: true, priority: 2 },
        url: { enabled: false, priority: 1 },
        custom: { enabled: false, priority: 1, patterns: [] },
      },
      recognitionParams: {
        confidenceThreshold: 0.7,
        maxEntities: 50,
        enableContextAnalysis: true,
        enableFuzzyMatch: false,
      },
      processingOptions: {
        autoSave: true,
        realTimePreview: true,
        highlightEntities: true,
        showConfidence: true,
      },
    });
    setHasChanges(true);
  };

  // 快速预设配置
  const applyPreset = (preset) => {
    const presets = {
      minimal: {
        entityTypes: {
          person: { enabled: true, priority: 5 },
          organization: { enabled: false, priority: 4 },
          location: { enabled: false, priority: 4 },
          date: { enabled: false, priority: 3 },
          email: { enabled: false, priority: 2 },
          phone: { enabled: false, priority: 2 },
          url: { enabled: false, priority: 1 },
          custom: { enabled: false, priority: 1, patterns: [] },
        },
      },
      standard: {
        entityTypes: {
          person: { enabled: true, priority: 5 },
          organization: { enabled: true, priority: 4 },
          location: { enabled: true, priority: 4 },
          date: { enabled: true, priority: 3 },
          email: { enabled: true, priority: 2 },
          phone: { enabled: true, priority: 2 },
          url: { enabled: false, priority: 1 },
          custom: { enabled: false, priority: 1, patterns: [] },
        },
      },
      comprehensive: {
        entityTypes: {
          person: { enabled: true, priority: 5 },
          organization: { enabled: true, priority: 4 },
          location: { enabled: true, priority: 4 },
          date: { enabled: true, priority: 3 },
          email: { enabled: true, priority: 2 },
          phone: { enabled: true, priority: 2 },
          url: { enabled: true, priority: 1 },
          custom: { enabled: true, priority: 1, patterns: [] },
        },
      },
    };

    if (presets[preset]) {
      setConfig((prev) => ({
        ...prev,
        entityTypes: { ...prev.entityTypes, ...presets[preset].entityTypes },
      }));
      setHasChanges(true);
    }
  };

  // 计算启用的实体类型数量
  const enabledCount = Object.values(config.entityTypes).filter((t) => t.enabled).length;

  return (
    <Card className="entity-config-panel">
      <div className="panel-header">
        <h3>实体识别配置</h3>
        <div className="header-actions">
          <Badge variant="info">{enabledCount} 种类型已启用</Badge>
          {hasChanges && <Badge variant="warning">有未保存的更改</Badge>}
        </div>
      </div>

      {/* 快速预设 */}
      <div className="preset-section">
        <label>快速配置</label>
        <div className="preset-buttons">
          <Button size="sm" variant="outline" onClick={() => applyPreset('minimal')}>
            精简模式
          </Button>
          <Button size="sm" variant="outline" onClick={() => applyPreset('standard')}>
            标准模式
          </Button>
          <Button size="sm" variant="outline" onClick={() => applyPreset('comprehensive')}>
            全面模式
          </Button>
        </div>
      </div>

      {/* 标签页切换 */}
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'types' ? 'active' : ''}`}
          onClick={() => setActiveTab('types')}
        >
          实体类型
        </button>
        <button
          className={`tab-button ${activeTab === 'params' ? 'active' : ''}`}
          onClick={() => setActiveTab('params')}
        >
          识别参数
        </button>
        <button
          className={`tab-button ${activeTab === 'options' ? 'active' : ''}`}
          onClick={() => setActiveTab('options')}
        >
          处理选项
        </button>
      </div>

      {/* 实体类型配置 */}
      {activeTab === 'types' && (
        <div className="entity-types-section">
          <div className="section-description">
            选择要识别的实体类型并设置优先级
          </div>

          <div className="entity-types-list">
            {entityTypeOptions.map((type) => {
              const typeConfig = config.entityTypes[type.key];
              return (
                <div
                  key={type.key}
                  className={`entity-type-item ${typeConfig.enabled ? 'enabled' : ''}`}
                >
                  <div className="type-header">
                    <div className="type-info">
                      <span className="type-label">{type.label}</span>
                      <span className="type-description">{type.description}</span>
                    </div>
                    <Switch
                      checked={typeConfig.enabled}
                      onChange={() => toggleEntityType(type.key)}
                    />
                  </div>

                  {typeConfig.enabled && (
                    <div className="type-priority">
                      <label>优先级</label>
                      <Slider
                        min={1}
                        max={5}
                        step={1}
                        value={typeConfig.priority}
                        onChange={(value) => updateEntityPriority(type.key, value)}
                      />
                      <span className="priority-value">{typeConfig.priority}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 识别参数配置 */}
      {activeTab === 'params' && (
        <div className="recognition-params-section">
          <div className="param-item">
            <div className="param-header">
              <label>置信度阈值</label>
              <span className="param-value">
                {(config.recognitionParams.confidenceThreshold * 100).toFixed(0)}%
              </span>
            </div>
            <Slider
              min={0.1}
              max={1.0}
              step={0.05}
              value={config.recognitionParams.confidenceThreshold}
              onChange={(value) => updateConfig('recognitionParams.confidenceThreshold', value)}
            />
            <div className="param-hint">
              较高的阈值会提高识别准确性，但可能漏掉一些实体
            </div>
          </div>

          <div className="param-item">
            <div className="param-header">
              <label>最大实体数</label>
              <span className="param-value">{config.recognitionParams.maxEntities}</span>
            </div>
            <Slider
              min={10}
              max={200}
              step={10}
              value={config.recognitionParams.maxEntities}
              onChange={(value) => updateConfig('recognitionParams.maxEntities', value)}
            />
          </div>

          <div className="param-item switch-item">
            <div className="switch-info">
              <label>启用上下文分析</label>
              <span className="switch-description">
                使用上下文信息提高识别准确性
              </span>
            </div>
            <Switch
              checked={config.recognitionParams.enableContextAnalysis}
              onChange={(checked) =>
                updateConfig('recognitionParams.enableContextAnalysis', checked)
              }
            />
          </div>

          <div className="param-item switch-item">
            <div className="switch-info">
              <label>启用模糊匹配</label>
              <span className="switch-description">
                允许一定程度的拼写错误匹配
              </span>
            </div>
            <Switch
              checked={config.recognitionParams.enableFuzzyMatch}
              onChange={(checked) =>
                updateConfig('recognitionParams.enableFuzzyMatch', checked)
              }
            />
          </div>
        </div>
      )}

      {/* 处理选项配置 */}
      {activeTab === 'options' && (
        <div className="processing-options-section">
          <div className="option-item">
            <div className="option-info">
              <label>自动保存</label>
              <span className="option-description">
                自动保存识别结果到知识库
              </span>
            </div>
            <Switch
              checked={config.processingOptions.autoSave}
              onChange={(checked) => updateConfig('processingOptions.autoSave', checked)}
            />
          </div>

          <div className="option-item">
            <div className="option-info">
              <label>实时预览</label>
              <span className="option-description">
                输入时实时显示识别结果
              </span>
            </div>
            <Switch
              checked={config.processingOptions.realTimePreview}
              onChange={(checked) =>
                updateConfig('processingOptions.realTimePreview', checked)
              }
            />
          </div>

          <div className="option-item">
            <div className="option-info">
              <label>高亮显示实体</label>
              <span className="option-description">
                在文本中高亮显示识别到的实体
              </span>
            </div>
            <Switch
              checked={config.processingOptions.highlightEntities}
              onChange={(checked) =>
                updateConfig('processingOptions.highlightEntities', checked)
              }
            />
          </div>

          <div className="option-item">
            <div className="option-info">
              <label>显示置信度</label>
              <span className="option-description">
                显示每个实体的识别置信度
              </span>
            </div>
            <Switch
              checked={config.processingOptions.showConfidence}
              onChange={(checked) =>
                updateConfig('processingOptions.showConfidence', checked)
              }
            />
          </div>
        </div>
      )}

      {/* 操作按钮 */}
      <div className="panel-actions">
        <Button variant="secondary" onClick={handleReset}>
          重置
        </Button>
        <Button variant="primary" onClick={handleSave} disabled={!hasChanges}>
          保存配置
        </Button>
      </div>
    </Card>
  );
};

export default EntityConfigPanel;
