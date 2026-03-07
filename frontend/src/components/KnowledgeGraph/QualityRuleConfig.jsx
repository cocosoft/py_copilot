/**
 * 质量规则配置组件
 *
 * 配置知识图谱质量检查规则，包括：
 * - 实体质量规则
 * - 关系质量规则
 * - 图谱完整性规则
 * - 冲突检测规则
 */

import React, { useState, useEffect } from 'react';
import './QualityRuleConfig.css';

/**
 * 质量规则配置主组件
 *
 * @returns {JSX.Element} 质量规则配置界面
 */
const QualityRuleConfig = () => {
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 保存状态
  const [saving, setSaving] = useState(false);
  // 消息提示
  const [message, setMessage] = useState({ type: '', text: '' });
  // 当前标签页
  const [activeTab, setActiveTab] = useState('entity'); // entity, relation, integrity, conflict

  // 规则配置状态
  const [rules, setRules] = useState({
    // 实体质量规则
    entity: {
      enabled: true,
      minNameLength: 2,
      maxNameLength: 100,
      requireDescription: false,
      checkDuplicates: true,
      similarityThreshold: 0.85,
      forbiddenCharacters: '<>{}[]',
      maxAliases: 10
    },
    // 关系质量规则
    relation: {
      enabled: true,
      requireBidirectional: false,
      maxRelationsPerEntity: 50,
      checkCircular: true,
      confidenceThreshold: 0.6
    },
    // 图谱完整性规则
    integrity: {
      enabled: true,
      checkOrphanEntities: true,
      checkOrphanRelations: true,
      requireEntityType: true,
      requireRelationType: true,
      minEntityProperties: 1
    },
    // 冲突检测规则
    conflict: {
      enabled: true,
      detectContradictoryRelations: true,
      detectDuplicateEntities: true,
      detectTypeConflicts: true,
      autoResolve: false
    }
  });

  /**
   * 显示消息
   */
  const showMessage = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  };

  /**
   * 加载配置
   */
  useEffect(() => {
    // TODO: 从API加载配置
    setLoading(false);
  }, []);

  /**
   * 保存配置
   */
  const handleSave = async () => {
    setSaving(true);
    try {
      // TODO: 调用API保存配置
      await new Promise(resolve => setTimeout(resolve, 500));
      showMessage('规则保存成功');
    } catch (error) {
      showMessage('保存失败', 'error');
    } finally {
      setSaving(false);
    }
  };

  /**
   * 重置配置
   */
  const handleReset = () => {
    if (window.confirm('确定要重置为默认规则吗？')) {
      setRules({
        entity: {
          enabled: true,
          minNameLength: 2,
          maxNameLength: 100,
          requireDescription: false,
          checkDuplicates: true,
          similarityThreshold: 0.85,
          forbiddenCharacters: '<>{}[]',
          maxAliases: 10
        },
        relation: {
          enabled: true,
          requireBidirectional: false,
          maxRelationsPerEntity: 50,
          checkCircular: true,
          confidenceThreshold: 0.6
        },
        integrity: {
          enabled: true,
          checkOrphanEntities: true,
          checkOrphanRelations: true,
          requireEntityType: true,
          requireRelationType: true,
          minEntityProperties: 1
        },
        conflict: {
          enabled: true,
          detectContradictoryRelations: true,
          detectDuplicateEntities: true,
          detectTypeConflicts: true,
          autoResolve: false
        }
      });
      showMessage('规则已重置');
    }
  };

  /**
   * 更新规则
   */
  const updateRule = (category, field, value) => {
    setRules(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [field]: value
      }
    }));
  };

  /**
   * 渲染实体质量规则
   */
  const renderEntityRules = () => (
    <div className="rules-panel">
      <div className="panel-header">
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={rules.entity.enabled}
            onChange={(e) => updateRule('entity', 'enabled', e.target.checked)}
          />
          <span className="toggle-slider"></span>
          <span className="toggle-label">启用实体质量检查</span>
        </label>
      </div>

      {rules.entity.enabled && (
        <div className="panel-content">
          <div className="form-row">
            <div className="form-group">
              <label>最小名称长度</label>
              <input
                type="number"
                min="1"
                max="10"
                value={rules.entity.minNameLength}
                onChange={(e) => updateRule('entity', 'minNameLength', parseInt(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>最大名称长度</label>
              <input
                type="number"
                min="10"
                max="500"
                value={rules.entity.maxNameLength}
                onChange={(e) => updateRule('entity', 'maxNameLength', parseInt(e.target.value))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>最大别名数量</label>
              <input
                type="number"
                min="0"
                max="50"
                value={rules.entity.maxAliases}
                onChange={(e) => updateRule('entity', 'maxAliases', parseInt(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>相似度阈值 ({rules.entity.similarityThreshold})</label>
              <input
                type="range"
                min="0.5"
                max="1"
                step="0.05"
                value={rules.entity.similarityThreshold}
                onChange={(e) => updateRule('entity', 'similarityThreshold', parseFloat(e.target.value))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>禁止字符</label>
              <input
                type="text"
                value={rules.entity.forbiddenCharacters}
                onChange={(e) => updateRule('entity', 'forbiddenCharacters', e.target.value)}
                placeholder="<>{}[]"
              />
            </div>
          </div>

          <div className="form-row checkbox-row">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.entity.requireDescription}
                onChange={(e) => updateRule('entity', 'requireDescription', e.target.checked)}
              />
              <span>要求实体描述</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.entity.checkDuplicates}
                onChange={(e) => updateRule('entity', 'checkDuplicates', e.target.checked)}
              />
              <span>检查重复实体</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );

  /**
   * 渲染关系质量规则
   */
  const renderRelationRules = () => (
    <div className="rules-panel">
      <div className="panel-header">
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={rules.relation.enabled}
            onChange={(e) => updateRule('relation', 'enabled', e.target.checked)}
          />
          <span className="toggle-slider"></span>
          <span className="toggle-label">启用关系质量检查</span>
        </label>
      </div>

      {rules.relation.enabled && (
        <div className="panel-content">
          <div className="form-row">
            <div className="form-group">
              <label>每实体最大关系数</label>
              <input
                type="number"
                min="1"
                max="200"
                value={rules.relation.maxRelationsPerEntity}
                onChange={(e) => updateRule('relation', 'maxRelationsPerEntity', parseInt(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>置信度阈值 ({rules.relation.confidenceThreshold})</label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={rules.relation.confidenceThreshold}
                onChange={(e) => updateRule('relation', 'confidenceThreshold', parseFloat(e.target.value))}
              />
            </div>
          </div>

          <div className="form-row checkbox-row">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.relation.requireBidirectional}
                onChange={(e) => updateRule('relation', 'requireBidirectional', e.target.checked)}
              />
              <span>要求双向关系</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.relation.checkCircular}
                onChange={(e) => updateRule('relation', 'checkCircular', e.target.checked)}
              />
              <span>检查循环关系</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );

  /**
   * 渲染完整性规则
   */
  const renderIntegrityRules = () => (
    <div className="rules-panel">
      <div className="panel-header">
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={rules.integrity.enabled}
            onChange={(e) => updateRule('integrity', 'enabled', e.target.checked)}
          />
          <span className="toggle-slider"></span>
          <span className="toggle-label">启用完整性检查</span>
        </label>
      </div>

      {rules.integrity.enabled && (
        <div className="panel-content">
          <div className="form-row">
            <div className="form-group">
              <label>最小实体属性数</label>
              <input
                type="number"
                min="0"
                max="10"
                value={rules.integrity.minEntityProperties}
                onChange={(e) => updateRule('integrity', 'minEntityProperties', parseInt(e.target.value))}
              />
            </div>
          </div>

          <div className="form-row checkbox-row">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.integrity.checkOrphanEntities}
                onChange={(e) => updateRule('integrity', 'checkOrphanEntities', e.target.checked)}
              />
              <span>检查孤立实体</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.integrity.checkOrphanRelations}
                onChange={(e) => updateRule('integrity', 'checkOrphanRelations', e.target.checked)}
              />
              <span>检查孤立关系</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.integrity.requireEntityType}
                onChange={(e) => updateRule('integrity', 'requireEntityType', e.target.checked)}
              />
              <span>要求实体类型</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.integrity.requireRelationType}
                onChange={(e) => updateRule('integrity', 'requireRelationType', e.target.checked)}
              />
              <span>要求关系类型</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );

  /**
   * 渲染冲突检测规则
   */
  const renderConflictRules = () => (
    <div className="rules-panel">
      <div className="panel-header">
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={rules.conflict.enabled}
            onChange={(e) => updateRule('conflict', 'enabled', e.target.checked)}
          />
          <span className="toggle-slider"></span>
          <span className="toggle-label">启用冲突检测</span>
        </label>
      </div>

      {rules.conflict.enabled && (
        <div className="panel-content">
          <div className="form-row checkbox-row">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.conflict.detectContradictoryRelations}
                onChange={(e) => updateRule('conflict', 'detectContradictoryRelations', e.target.checked)}
              />
              <span>检测矛盾关系</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.conflict.detectDuplicateEntities}
                onChange={(e) => updateRule('conflict', 'detectDuplicateEntities', e.target.checked)}
              />
              <span>检测重复实体</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.conflict.detectTypeConflicts}
                onChange={(e) => updateRule('conflict', 'detectTypeConflicts', e.target.checked)}
              />
              <span>检测类型冲突</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rules.conflict.autoResolve}
                onChange={(e) => updateRule('conflict', 'autoResolve', e.target.checked)}
              />
              <span>自动解决冲突</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );

  const tabs = [
    { id: 'entity', label: '实体质量', icon: '🏷️' },
    { id: 'relation', label: '关系质量', icon: '🔗' },
    { id: 'integrity', label: '完整性', icon: '✓' },
    { id: 'conflict', label: '冲突检测', icon: '⚠️' }
  ];

  return (
    <div className="quality-rule-config">
      {/* 消息提示 */}
      {message.text && (
        <div className={`quality-message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 头部 */}
      <div className="quality-header">
        <h3>质量规则配置</h3>
        <div className="header-actions">
          <button className="btn-secondary" onClick={handleReset}>
            重置默认
          </button>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? '保存中...' : '保存规则'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="quality-loading">
          <div className="loading-spinner"></div>
          <span>加载配置中...</span>
        </div>
      ) : (
        <div className="quality-content">
          {/* 标签导航 */}
          <div className="quality-tabs">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`quality-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-label">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* 规则内容 */}
          <div className="quality-panel">
            {activeTab === 'entity' && renderEntityRules()}
            {activeTab === 'relation' && renderRelationRules()}
            {activeTab === 'integrity' && renderIntegrityRules()}
            {activeTab === 'conflict' && renderConflictRules()}
          </div>
        </div>
      )}
    </div>
  );
};

export default QualityRuleConfig;
