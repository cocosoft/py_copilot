/**
 * 实体配置弹窗组件
 *
 * 提供实体类型、提取规则、词典的配置管理功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { FiPlus, FiEdit2, FiTrash2, FiSettings, FiPlay, FiDownload, FiUpload, FiRefreshCw } from 'react-icons/fi';
import Modal from '../../UI/Modal';
import Button from '../../UI/Button';
import { message } from '../../UI/Message/Message';
import * as entityConfigApi from '../../../utils/api/entityConfigApi';
import './EntityConfigModal.css';

/**
 * Tab 配置
 */
const TABS = [
  { key: 'types', label: '实体类型', icon: '🏷️' },
  { key: 'rules', label: '提取规则', icon: '📋' },
  { key: 'dictionary', label: '词典管理', icon: '📚' },
  { key: 'test', label: '测试', icon: '🧪' },
  { key: 'advanced', label: '高级', icon: '⚙️' },
];

/**
 * 默认颜色列表
 */
const DEFAULT_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
  '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43',
];

/**
 * 实体配置弹窗组件
 */
const EntityConfigModal = ({ isOpen, onClose, knowledgeBaseId }) => {
  console.log('EntityConfigModal 组件渲染, isOpen:', isOpen, 'knowledgeBaseId:', knowledgeBaseId);
  
  // 监听 isOpen 属性变化
  React.useEffect(() => {
    console.log('EntityConfigModal isOpen 属性变化:', isOpen);
  }, [isOpen]);
    
    const [activeTab, setActiveTab] = useState('types');
  const [loading, setLoading] = useState(false);

  // 实体类型状态
  const [entityTypes, setEntityTypes] = useState([]);
  const [editingType, setEditingType] = useState(null);
  const [typeForm, setTypeForm] = useState({ name: '', description: '', color: '#FF6B6B', enabled: true });

  // 提取规则状态
  const [selectedEntityType, setSelectedEntityType] = useState('');
  const [extractionRules, setExtractionRules] = useState([]);
  const [editingRule, setEditingRule] = useState(null);
  const [ruleForm, setRuleForm] = useState({ name: '', pattern: '', description: '', enabled: true });

  // 词典状态
  const [selectedDictType, setSelectedDictType] = useState('');
  const [dictionary, setDictionary] = useState([]);
  const [newTerm, setNewTerm] = useState('');

  // 测试状态
  const [testText, setTestText] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [testing, setTesting] = useState(false);

  /**
   * 加载实体类型列表
   */
  const loadEntityTypes = useCallback(async () => {
    console.log('开始加载实体类型');
    setLoading(true);
    try {
      const response = await entityConfigApi.getEntityTypes();
      console.log('API 响应:', response);
      const types = Object.entries(response.data.entity_types || {}).map(([key, value]) => ({
        key,
        ...value,
      }));
      console.log('处理后的实体类型:', types);
      setEntityTypes(types);
      
      if (types.length > 0 && !selectedEntityType) {
        setSelectedEntityType(types[0].key);
        setSelectedDictType(types[0].key);
      }
    } catch (error) {
      console.error('加载实体类型失败:', error);
      message.error('加载实体类型失败');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 加载提取规则
   */
  const loadExtractionRules = useCallback(async (entityType) => {
    if (!entityType) return;
    
    setLoading(true);
    try {
      const response = await entityConfigApi.getExtractionRules(entityType);
      setExtractionRules(response.data.rules || []);
    } catch (error) {
      message.error('加载提取规则失败');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 加载词典
   */
  const loadDictionary = useCallback(async (entityType) => {
    if (!entityType) return;
    
    setLoading(true);
    try {
      const response = await entityConfigApi.getDictionary(entityType);
      setDictionaryTerms(response.data.terms || []);
    } catch (error) {
      message.error('加载词典失败');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 初始化加载
   */
  useEffect(() => {
    if (isOpen) {
      loadEntityTypes();
    }
  }, [isOpen, loadEntityTypes]);

  /**
   * 切换实体类型时加载规则和词典
   */
  useEffect(() => {
    if (activeTab === 'rules' && selectedEntityType) {
      loadExtractionRules(selectedEntityType);
    }
    if (activeTab === 'dictionary' && selectedDictType) {
      loadDictionary(selectedDictType);
    }
  }, [activeTab, selectedEntityType, selectedDictType, loadExtractionRules, loadDictionary]);

  /**
   * 切换实体类型启用状态
   */
  const handleToggleEntityType = async (entityType, enabled) => {
    try {
      await entityConfigApi.updateEntityType(entityType, { enabled });
      message.success(`已${enabled ? '启用' : '禁用'}实体类型`);
      loadEntityTypes();
    } catch (error) {
      message.error('更新失败');
    }
  };

  /**
   * 保存实体类型
   */
  const handleSaveEntityType = async () => {
    if (!typeForm.name.trim()) {
      message.warning('请输入实体类型名称');
      return;
    }

    try {
      if (editingType) {
        await entityConfigApi.updateEntityType(editingType, typeForm);
        message.success('实体类型已更新');
      } else {
        const key = typeForm.name.toUpperCase().replace(/\s+/g, '_');
        await entityConfigApi.addEntityType(key, typeForm);
        message.success('实体类型已添加');
      }
      setEditingType(null);
      setTypeForm({ name: '', description: '', color: '#FF6B6B', enabled: true });
      loadEntityTypes();
    } catch (error) {
      message.error('保存失败');
    }
  };

  /**
   * 删除实体类型
   */
  const handleDeleteEntityType = async (entityType) => {
    if (!window.confirm(`确定要删除实体类型 "${entityType}" 吗？`)) return;
    
    try {
      await entityConfigApi.updateEntityType(entityType, { enabled: false });
      message.success('实体类型已禁用');
      loadEntityTypes();
    } catch (error) {
      message.error('删除失败');
    }
  };

  /**
   * 添加提取规则
   */
  const handleAddRule = async () => {
    if (!ruleForm.name.trim() || !ruleForm.pattern.trim()) {
      message.warning('请填写规则名称和正则表达式');
      return;
    }

    try {
      await entityConfigApi.addExtractionRule(selectedEntityType, {
        ...ruleForm,
        id: `rule_${Date.now()}`,
      });
      message.success('提取规则已添加');
      setRuleForm({ name: '', pattern: '', description: '', enabled: true });
      loadExtractionRules(selectedEntityType);
    } catch (error) {
      message.error('添加规则失败');
    }
  };

  /**
   * 添加词典术语
   */
  const handleAddTerm = async () => {
    if (!newTerm.trim()) {
      message.warning('请输入术语');
      return;
    }

    try {
      await entityConfigApi.addToDictionary(selectedDictType, [newTerm.trim()]);
      message.success('术语已添加');
      setNewTerm('');
      loadDictionary(selectedDictType);
    } catch (error) {
      message.error('添加术语失败');
    }
  };

  /**
   * 批量添加术语
   */
  const handleBatchAddTerms = async () => {
    const terms = newTerm.split(/[,，\n]/).map(t => t.trim()).filter(Boolean);
    if (terms.length === 0) {
      message.warning('请输入术语');
      return;
    }

    try {
      await entityConfigApi.addToDictionary(selectedDictType, terms);
      message.success(`已添加 ${terms.length} 个术语`);
      setNewTerm('');
      loadDictionary(selectedDictType);
    } catch (error) {
      message.error('批量添加失败');
    }
  };

  /**
   * 测试实体提取
   */
  const handleTestExtraction = async () => {
    if (!testText.trim()) {
      message.warning('请输入测试文本');
      return;
    }

    setTesting(true);
    try {
      const response = await entityConfigApi.testEntityExtraction(testText);
      setTestResults(response.data);
    } catch (error) {
      message.error('测试失败');
    } finally {
      setTesting(false);
    }
  };

  /**
   * 导出配置
   */
  const handleExportConfig = async () => {
    try {
      const timestamp = new Date().toISOString().slice(0, 10);
      await entityConfigApi.exportConfig(`entity_config_backup_${timestamp}.json`);
      message.success('配置已导出');
    } catch (error) {
      message.error('导出失败');
    }
  };

  /**
   * 重置配置
   */
  const handleResetConfig = async () => {
    if (!window.confirm('确定要重置为默认配置吗？此操作不可撤销。')) return;
    
    try {
      await entityConfigApi.resetConfig();
      message.success('配置已重置');
      loadEntityTypes();
    } catch (error) {
      message.error('重置失败');
    }
  };

  /**
   * 渲染实体类型配置
   */
  const renderTypesTab = () => (
    <div className="config-section">
      <div className="config-header">
        <h4>实体类型管理</h4>
        <Button
          variant="primary"
          size="small"
          icon={<FiPlus />}
          onClick={() => {
            setEditingType('new');
            setTypeForm({ name: '', description: '', color: DEFAULT_COLORS[entityTypes.length % DEFAULT_COLORS.length], enabled: true });
          }}
        >
          添加实体类型
        </Button>
      </div>

      {editingType && (
        <div className="type-form">
          <div className="form-row">
            <label>名称</label>
            <input
              type="text"
              value={typeForm.name}
              onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })}
              placeholder="如：人物、组织、地点"
            />
          </div>
          <div className="form-row">
            <label>描述</label>
            <input
              type="text"
              value={typeForm.description}
              onChange={(e) => setTypeForm({ ...typeForm, description: e.target.value })}
              placeholder="实体类型描述"
            />
          </div>
          <div className="form-row">
            <label>颜色</label>
            <div className="color-picker">
              {DEFAULT_COLORS.map(color => (
                <button
                  key={color}
                  className={`color-option ${typeForm.color === color ? 'selected' : ''}`}
                  style={{ backgroundColor: color }}
                  onClick={() => setTypeForm({ ...typeForm, color })}
                />
              ))}
            </div>
          </div>
          <div className="form-actions">
            <Button variant="primary" size="small" onClick={handleSaveEntityType}>
              保存
            </Button>
            <Button variant="ghost" size="small" onClick={() => setEditingType(null)}>
              取消
            </Button>
          </div>
        </div>
      )}

      <div className="entity-types-list">
        {entityTypes.map(type => (
          <div key={type.key} className="entity-type-item">
            <div className="type-info">
              <span className="type-color" style={{ backgroundColor: type.color }} />
              <span className="type-name">{type.name}</span>
              <span className="type-key">({type.key})</span>
              <span className="type-desc">{type.description}</span>
            </div>
            <div className="type-actions">
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={type.enabled}
                  onChange={(e) => handleToggleEntityType(type.key, e.target.checked)}
                />
                <span className="toggle-slider" />
              </label>
              <Button
                variant="ghost"
                size="small"
                icon={<FiEdit2 />}
                onClick={() => {
                  setEditingType(type.key);
                  setTypeForm({
                    name: type.name,
                    description: type.description || '',
                    color: type.color,
                    enabled: type.enabled,
                  });
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  /**
   * 渲染提取规则配置
   */
  const renderRulesTab = () => (
    <div className="config-section">
      <div className="config-header">
        <h4>提取规则配置</h4>
        <div className="header-select">
          <select
            value={selectedEntityType}
            onChange={(e) => setSelectedEntityType(e.target.value)}
          >
            <option value="">选择实体类型</option>
            {entityTypes.filter(t => t.enabled).map(type => (
              <option key={type.key} value={type.key}>{type.name}</option>
            ))}
          </select>
        </div>
      </div>

      {selectedEntityType && (
        <>
          <div className="rule-form">
            <div className="form-row">
              <label>规则名称</label>
              <input
                type="text"
                value={ruleForm.name}
                onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                placeholder="如：中文人名识别"
              />
            </div>
            <div className="form-row">
              <label>正则表达式</label>
              <input
                type="text"
                value={ruleForm.pattern}
                onChange={(e) => setRuleForm({ ...ruleForm, pattern: e.target.value })}
                placeholder="如：[张王李赵][\u4e00-\u9fff]{1,2}"
              />
            </div>
            <div className="form-row">
              <label>描述</label>
              <input
                type="text"
                value={ruleForm.description}
                onChange={(e) => setRuleForm({ ...ruleForm, description: e.target.value })}
                placeholder="规则说明"
              />
            </div>
            <div className="form-actions">
              <Button variant="primary" size="small" onClick={handleAddRule}>
                添加规则
              </Button>
            </div>
          </div>

          <div className="rules-list">
            {extractionRules.map((rule, index) => (
              <div key={rule.id || index} className="rule-item">
                <div className="rule-info">
                  <span className="rule-name">{rule.name}</span>
                  <code className="rule-pattern">{rule.pattern}</code>
                  <span className="rule-desc">{rule.description}</span>
                </div>
                <div className="rule-actions">
                  <label className="toggle-switch">
                    <input type="checkbox" checked={rule.enabled} readOnly />
                    <span className="toggle-slider" />
                  </label>
                </div>
              </div>
            ))}
            {extractionRules.length === 0 && (
              <div className="empty-hint">暂无提取规则，请添加</div>
            )}
          </div>
        </>
      )}

      {!selectedEntityType && (
        <div className="empty-hint">请先选择实体类型</div>
      )}
    </div>
  );

  /**
   * 渲染词典管理
   */
  const renderDictionaryTab = () => (
    <div className="config-section">
      <div className="config-header">
        <h4>词典管理</h4>
        <div className="header-select">
          <select
            value={selectedDictType}
            onChange={(e) => setSelectedDictType(e.target.value)}
          >
            <option value="">选择实体类型</option>
            {entityTypes.filter(t => t.enabled).map(type => (
              <option key={type.key} value={type.key}>{type.name}</option>
            ))}
          </select>
        </div>
      </div>

      {selectedDictType && (
        <>
          <div className="dict-input">
            <textarea
              value={newTerm}
              onChange={(e) => setNewTerm(e.target.value)}
              placeholder="输入术语，多个术语用逗号或换行分隔"
              rows={3}
            />
            <div className="dict-actions">
              <Button variant="primary" size="small" onClick={handleAddTerm}>
                添加
              </Button>
              <Button variant="secondary" size="small" onClick={handleBatchAddTerms}>
                批量添加
              </Button>
            </div>
          </div>

          <div className="dictionary-tags">
            {dictionary.map((term, index) => (
              <span key={index} className="dict-tag">
                {term}
                <button className="tag-remove" onClick={() => {
                  setDictionary(prev => prev.filter((_, i) => i !== index));
                }}>×</button>
              </span>
            ))}
            {dictionary.length === 0 && (
              <div className="empty-hint">暂无词典术语，请添加</div>
            )}
          </div>

          <div className="dict-stats">
            共 {dictionary.length} 个术语
          </div>
        </>
      )}

      {!selectedDictType && (
        <div className="empty-hint">请先选择实体类型</div>
      )}
    </div>
  );

  /**
   * 渲染测试提取
   */
  const renderTestTab = () => (
    <div className="config-section">
      <div className="config-header">
        <h4>测试实体提取</h4>
      </div>

      <div className="test-section">
        <textarea
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          placeholder="输入测试文本，点击测试按钮查看提取效果..."
          rows={6}
          className="test-textarea"
        />

        <Button
          variant="primary"
          icon={<FiPlay />}
          loading={testing}
          onClick={handleTestExtraction}
        >
          测试提取
        </Button>

        {testResults && (
          <div className="test-results">
            <h5>提取结果</h5>
            <div className="result-stats">
              <span>实体数量: {testResults.data?.summary?.total_entities || 0}</span>
              <span>关系数量: {testResults.data?.summary?.total_relationships || 0}</span>
            </div>
            
            {testResults.data?.entities?.length > 0 && (
              <div className="result-entities">
                <h6>识别的实体：</h6>
                <div className="entity-tags">
                  {testResults.data.entities.map((entity, index) => (
                    <span key={index} className="entity-tag">
                      <span className="entity-type">{entity.type}</span>
                      <span className="entity-name">{entity.name || entity.text}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  /**
   * 渲染高级设置
   */
  const renderAdvancedTab = () => (
    <div className="config-section">
      <div className="config-header">
        <h4>高级设置</h4>
      </div>

      <div className="advanced-options">
        <div className="option-row">
          <div className="option-info">
            <span className="option-label">导出配置</span>
            <span className="option-desc">将当前配置导出为 JSON 文件</span>
          </div>
          <Button variant="secondary" icon={<FiDownload />} onClick={handleExportConfig}>
            导出
          </Button>
        </div>

        <div className="option-row">
          <div className="option-info">
            <span className="option-label">导入配置</span>
            <span className="option-desc">从 JSON 文件导入配置</span>
          </div>
          <Button variant="secondary" icon={<FiUpload />}>
            导入
          </Button>
        </div>

        <div className="option-row danger">
          <div className="option-info">
            <span className="option-label">重置配置</span>
            <span className="option-desc">恢复为默认配置，此操作不可撤销</span>
          </div>
          <Button variant="danger" icon={<FiRefreshCw />} onClick={handleResetConfig}>
            重置
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="实体识别配置"
      size="large"
    >
      <div className="entity-config-modal">
        {/* 提示信息 */}
        <div className="config-header" style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '4px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px' }}>
            <span style={{ fontSize: '16px' }}>💡</span>
            <div>
              <p style={{ margin: 0, fontSize: '14px', color: '#262626' }}>配置说明</p>
              <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#595959' }}>所有配置会实时保存，无需手动点击保存按钮</p>
            </div>
          </div>
        </div>
        
        {/* Tab 导航 */}
        <div className="config-tabs">
          {TABS.map(tab => (
            <button
              key={tab.key}
              className={`config-tab ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab 内容 */}
        <div className="config-content">
          {loading && <div className="loading-overlay">加载中...</div>}
          
          {activeTab === 'types' && renderTypesTab()}
          {activeTab === 'rules' && renderRulesTab()}
          {activeTab === 'dictionary' && renderDictionaryTab()}
          {activeTab === 'test' && renderTestTab()}
          {activeTab === 'advanced' && renderAdvancedTab()}
        </div>
      </div>
    </Modal>
  );
};

export default EntityConfigModal;
