/**
 * 统一实体配置组件
 *
 * 整合实体类型、提取规则、术语词典、提取测试为一个统一的界面
 * 采用左右布局：左侧实体类型列表，右侧详情和配置
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  getEntityTypes,
  addEntityType,
  updateEntityType,
  getExtractionRules,
  addExtractionRule,
  getDictionary,
  addToDictionary,
  testEntityExtraction,
  resetConfig
} from '../../utils/api/entityConfigApi';
import './EntityConfigUnified.css';

/**
 * 统一实体配置主组件
 *
 * @returns {JSX.Element} 实体配置界面
 */
const EntityConfigUnified = () => {
  // 实体类型列表
  const [entityTypes, setEntityTypes] = useState([]);
  // 当前选中的实体类型
  const [selectedType, setSelectedType] = useState(null);
  // 提取规则列表
  const [extractionRules, setExtractionRules] = useState([]);
  // 词典数据
  const [dictionaries, setDictionaries] = useState({});
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 消息提示
  const [message, setMessage] = useState({ type: '', text: '' });
  // 当前右侧面板标签
  const [rightPanelTab, setRightPanelTab] = useState('rules'); // 'rules', 'dictionary', 'test'

  // 模态框状态
  const [showTypeModal, setShowTypeModal] = useState(false);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [showDictModal, setShowDictModal] = useState(false);

  // 表单数据
  const [newType, setNewType] = useState({ name: '', description: '', color: '#4ECDC4', enabled: true });
  const [newRule, setNewRule] = useState({ name: '', pattern: '', description: '', enabled: true });
  const [newTerm, setNewTerm] = useState('');
  const [testText, setTestText] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [testing, setTesting] = useState(false);

  /**
   * 显示消息
   */
  const showMessage = useCallback((text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  }, []);

  /**
   * 加载实体配置数据
   */
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [typesRes, rulesRes] = await Promise.all([
        getEntityTypes(),
        getExtractionRules()
      ]);

      if (typesRes.success) {
        const types = Object.entries(typesRes.data.entity_types || {});
        setEntityTypes(types);
        if (types.length > 0 && !selectedType) {
          setSelectedType(types[0][0]);
        }
      }

      if (rulesRes.success) {
        setExtractionRules(rulesRes.data.rules || []);
      }
    } catch (error) {
      showMessage('加载数据失败', 'error');
    } finally {
      setLoading(false);
    }
  }, [selectedType, showMessage]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  /**
   * 加载词典
   */
  const loadDictionary = async (entityType) => {
    try {
      const response = await getDictionary(entityType);
      if (response.success) {
        setDictionaries(prev => ({
          ...prev,
          [entityType]: response.data.dictionary || []
        }));
      }
    } catch (error) {
      console.error('加载词典失败:', error);
    }
  };

  /**
   * 添加实体类型
   */
  const handleAddType = async () => {
    if (!newType.name || !newType.description) {
      showMessage('请填写名称和描述', 'error');
      return;
    }

    try {
      const response = await addEntityType(newType.name.toUpperCase(), newType);
      if (response.success) {
        showMessage('添加成功');
        setShowTypeModal(false);
        setNewType({ name: '', description: '', color: '#4ECDC4', enabled: true });
        loadData();
      }
    } catch (error) {
      showMessage('添加失败', 'error');
    }
  };

  /**
   * 切换实体类型启用状态
   */
  const handleToggleType = async (type, config) => {
    try {
      const response = await updateEntityType(type, { ...config, enabled: !config.enabled });
      if (response.success) {
        showMessage('更新成功');
        loadData();
      }
    } catch (error) {
      showMessage('更新失败', 'error');
    }
  };

  /**
   * 添加提取规则
   */
  const handleAddRule = async () => {
    if (!selectedType || !newRule.name || !newRule.pattern) {
      showMessage('请填写完整信息', 'error');
      return;
    }

    try {
      const response = await addExtractionRule(selectedType, newRule);
      if (response.success) {
        showMessage('添加规则成功');
        setShowRuleModal(false);
        setNewRule({ name: '', pattern: '', description: '', enabled: true });
        loadData();
      }
    } catch (error) {
      showMessage('添加失败', 'error');
    }
  };

  /**
   * 添加词典术语
   */
  const handleAddTerm = async () => {
    if (!selectedType || !newTerm.trim()) {
      showMessage('请填写术语', 'error');
      return;
    }

    try {
      const response = await addToDictionary(selectedType, [newTerm.trim()]);
      if (response.success) {
        showMessage('添加术语成功');
        setNewTerm('');
        loadDictionary(selectedType);
      }
    } catch (error) {
      showMessage('添加失败', 'error');
    }
  };

  /**
   * 测试实体提取
   */
  const handleTest = async () => {
    if (!testText.trim()) {
      showMessage('请输入测试文本', 'error');
      return;
    }

    setTesting(true);
    setTestResults(null);

    try {
      const response = await testEntityExtraction(testText);
      if (response.success) {
        setTestResults(response.data);
      }
    } catch (error) {
      showMessage('测试失败', 'error');
    } finally {
      setTesting(false);
    }
  };

  /**
   * 获取当前实体类型的规则
   */
  const getCurrentTypeRules = () => {
    return extractionRules.filter(rule => rule.entity_type === selectedType);
  };

  /**
   * 获取当前实体类型的词典
   */
  const getCurrentTypeDictionary = () => {
    return dictionaries[selectedType] || [];
  };

  return (
    <div className="entity-config-unified">
      {/* 消息提示 */}
      {message.text && (
        <div className={`unified-message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="unified-layout">
        {/* 左侧：实体类型列表 */}
        <div className="types-sidebar">
          <div className="sidebar-header">
            <h3>实体类型</h3>
            <button className="btn-icon" onClick={() => setShowTypeModal(true)} title="添加类型">
              +
            </button>
          </div>

          <div className="types-list">
            {entityTypes.map(([type, config]) => (
              <div
                key={type}
                className={`type-item ${selectedType === type ? 'active' : ''}`}
                onClick={() => setSelectedType(type)}
              >
                <div className="type-color" style={{ backgroundColor: config.color }}></div>
                <div className="type-info">
                  <span className="type-name">{type}</span>
                  <span className="type-desc">{config.description}</span>
                </div>
                <div className="type-status">
                  <span className={`status-badge ${config.enabled ? 'enabled' : 'disabled'}`}>
                    {config.enabled ? '启用' : '禁用'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 右侧：详情配置 */}
        <div className="config-detail">
          {selectedType ? (
            <>
              {/* 类型信息头部 */}
              <div className="detail-header">
                <div className="header-info">
                  <h2>{selectedType}</h2>
                  <span className="header-desc">
                    {entityTypes.find(([t]) => t === selectedType)?.[1]?.description}
                  </span>
                </div>
                <div className="header-actions">
                  <button
                    className="btn-secondary"
                    onClick={() => {
                      const config = entityTypes.find(([t]) => t === selectedType)?.[1];
                      handleToggleType(selectedType, config);
                    }}
                  >
                    {entityTypes.find(([t]) => t === selectedType)?.[1]?.enabled ? '禁用' : '启用'}
                  </button>
                </div>
              </div>

              {/* 子标签导航 */}
              <div className="detail-tabs">
                <button
                  className={`detail-tab ${rightPanelTab === 'rules' ? 'active' : ''}`}
                  onClick={() => setRightPanelTab('rules')}
                >
                  提取规则 ({getCurrentTypeRules().length})
                </button>
                <button
                  className={`detail-tab ${rightPanelTab === 'dictionary' ? 'active' : ''}`}
                  onClick={() => {
                    setRightPanelTab('dictionary');
                    loadDictionary(selectedType);
                  }}
                >
                  术语词典 ({getCurrentTypeDictionary().length})
                </button>
                <button
                  className={`detail-tab ${rightPanelTab === 'test' ? 'active' : ''}`}
                  onClick={() => setRightPanelTab('test')}
                >
                  提取测试
                </button>
              </div>

              {/* 内容区域 */}
              <div className="detail-content">
                {rightPanelTab === 'rules' && (
                  <div className="rules-section">
                    <div className="section-header">
                      <h4>提取规则</h4>
                      <button className="btn-primary" onClick={() => setShowRuleModal(true)}>
                        添加规则
                      </button>
                    </div>
                    <div className="rules-list">
                      {getCurrentTypeRules().length > 0 ? (
                        getCurrentTypeRules().map((rule, index) => (
                          <div key={index} className="rule-card">
                            <div className="rule-header">
                              <span className="rule-name">{rule.name}</span>
                              <span className={`rule-status ${rule.enabled ? 'enabled' : 'disabled'}`}>
                                {rule.enabled ? '启用' : '禁用'}
                              </span>
                            </div>
                            <code className="rule-pattern">{rule.pattern}</code>
                            <p className="rule-desc">{rule.description}</p>
                          </div>
                        ))
                      ) : (
                        <div className="empty-state">
                          <span className="empty-icon">📋</span>
                          <p>暂无提取规则</p>
                          <button className="btn-secondary" onClick={() => setShowRuleModal(true)}>
                            添加第一个规则
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {rightPanelTab === 'dictionary' && (
                  <div className="dictionary-section">
                    <div className="section-header">
                      <h4>术语词典</h4>
                      <div className="dict-input-group">
                        <input
                          type="text"
                          value={newTerm}
                          onChange={(e) => setNewTerm(e.target.value)}
                          placeholder="输入术语"
                          onKeyPress={(e) => e.key === 'Enter' && handleAddTerm()}
                        />
                        <button className="btn-primary" onClick={handleAddTerm}>
                          添加
                        </button>
                      </div>
                    </div>
                    <div className="terms-list">
                      {getCurrentTypeDictionary().length > 0 ? (
                        getCurrentTypeDictionary().map((term, index) => (
                          <span key={index} className="term-tag">{term}</span>
                        ))
                      ) : (
                        <div className="empty-state">
                          <span className="empty-icon">📚</span>
                          <p>暂无术语</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {rightPanelTab === 'test' && (
                  <div className="test-section">
                    <div className="test-input-area">
                      <textarea
                        value={testText}
                        onChange={(e) => setTestText(e.target.value)}
                        placeholder="输入要测试的文本..."
                        rows={6}
                      />
                      <button
                        className="btn-primary"
                        onClick={handleTest}
                        disabled={testing}
                      >
                        {testing ? '测试中...' : '测试提取'}
                      </button>
                    </div>

                    {testResults && (
                      <div className="test-results">
                        <h4>提取结果</h4>
                        <div className="results-stats">
                          找到 {testResults.total_entities || 0} 个实体
                        </div>
                        {testResults.entities && testResults.entities.length > 0 && (
                          <div className="results-list">
                            {testResults.entities.map((entity, index) => (
                              <div key={index} className="result-item">
                                <span className="result-text">{entity.text}</span>
                                <span className="result-type">{entity.type}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="empty-detail">
              <span className="empty-icon">🏷️</span>
              <p>请选择或创建一个实体类型</p>
              <button className="btn-primary" onClick={() => setShowTypeModal(true)}>
                创建实体类型
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 添加实体类型模态框 */}
      {showTypeModal && (
        <div className="modal-overlay" onClick={() => setShowTypeModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>添加实体类型</h3>
            <div className="form-group">
              <label>类型名称（英文大写）</label>
              <input
                type="text"
                value={newType.name}
                onChange={(e) => setNewType({ ...newType, name: e.target.value })}
                placeholder="例如：TECH"
              />
            </div>
            <div className="form-group">
              <label>描述</label>
              <input
                type="text"
                value={newType.description}
                onChange={(e) => setNewType({ ...newType, description: e.target.value })}
                placeholder="例如：技术术语"
              />
            </div>
            <div className="form-group">
              <label>颜色标识</label>
              <input
                type="color"
                value={newType.color}
                onChange={(e) => setNewType({ ...newType, color: e.target.value })}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={handleAddType}>添加</button>
              <button className="btn-secondary" onClick={() => setShowTypeModal(false)}>取消</button>
            </div>
          </div>
        </div>
      )}

      {/* 添加规则模态框 */}
      {showRuleModal && (
        <div className="modal-overlay" onClick={() => setShowRuleModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>添加提取规则</h3>
            <div className="form-group">
              <label>规则名称</label>
              <input
                type="text"
                value={newRule.name}
                onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                placeholder="例如：中文人名识别"
              />
            </div>
            <div className="form-group">
              <label>正则表达式</label>
              <input
                type="text"
                value={newRule.pattern}
                onChange={(e) => setNewRule({ ...newRule, pattern: e.target.value })}
                placeholder="例如：[张王李赵]\\w{1,2}"
              />
            </div>
            <div className="form-group">
              <label>描述</label>
              <input
                type="text"
                value={newRule.description}
                onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                placeholder="例如：基于常见姓氏的中文人名识别"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={handleAddRule}>添加</button>
              <button className="btn-secondary" onClick={() => setShowRuleModal(false)}>取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EntityConfigUnified;
