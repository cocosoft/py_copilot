import React, { useState, useEffect } from 'react';
import './EntityConfigManagement.css';
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
} from '../utils/api/entityConfigApi';

const EntityConfigManagement = () => {
  // 状态管理
  const [activeTab, setActiveTab] = useState('entity-types');
  const [entityTypes, setEntityTypes] = useState([]);
  const [extractionRules, setExtractionRules] = useState([]);
  const [dictionaries, setDictionaries] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // 实体类型管理相关状态
  const [showEntityTypeModal, setShowEntityTypeModal] = useState(false);
  const [editingEntityType, setEditingEntityType] = useState(null);
  const [newEntityType, setNewEntityType] = useState({ 
    name: '', 
    description: '', 
    color: '#4ECDC4', 
    enabled: true 
  });
  
  // 提取规则管理相关状态
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [selectedEntityType, setSelectedEntityType] = useState('');
  const [newRule, setNewRule] = useState({ 
    name: '', 
    pattern: '', 
    description: '', 
    enabled: true 
  });
  
  // 词典管理相关状态
  const [showDictionaryModal, setShowDictionaryModal] = useState(false);
  const [newTerm, setNewTerm] = useState('');
  const [selectedDictEntityType, setSelectedDictEntityType] = useState('');
  
  // 实体提取测试相关状态
  const [testText, setTestText] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [testing, setTesting] = useState(false);

  // 加载实体配置数据
  const loadEntityConfig = async () => {
    setLoading(true);
    setError('');
    try {
      // 加载实体类型
      const entityTypesResponse = await getEntityTypes();
      if (entityTypesResponse.success && entityTypesResponse.data) {
        setEntityTypes(Object.entries(entityTypesResponse.data.entity_types || {}));
      }
      
      // 加载提取规则
      const rulesResponse = await getExtractionRules();
      if (rulesResponse.success && rulesResponse.data) {
        setExtractionRules(rulesResponse.data.rules || []);
      }
      
    } catch (error) {
      setError(`加载配置失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    loadEntityConfig();
  }, []);

  // 添加新的实体类型
  const handleAddEntityType = async () => {
    if (!newEntityType.name || !newEntityType.description) {
      setError('请填写实体类型名称和描述');
      return;
    }

    try {
      const response = await addEntityType(newEntityType.name.toUpperCase(), newEntityType);
      if (response.success) {
        setSuccess(`成功添加实体类型: ${newEntityType.name}`);
        setShowEntityTypeModal(false);
        setNewEntityType({ name: '', description: '', color: '#4ECDC4', enabled: true });
        loadEntityConfig();
      } else {
        setError('添加实体类型失败');
      }
    } catch (error) {
      setError(`添加实体类型失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 更新实体类型
  const handleUpdateEntityType = async (entityType, config) => {
    try {
      const response = await updateEntityType(entityType, config);
      if (response.success) {
        setSuccess(`成功更新实体类型: ${entityType}`);
        loadEntityConfig();
      } else {
        setError('更新实体类型失败');
      }
    } catch (error) {
      setError(`更新实体类型失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 添加提取规则
  const handleAddExtractionRule = async () => {
    if (!selectedEntityType || !newRule.name || !newRule.pattern) {
      setError('请选择实体类型并填写规则名称和模式');
      return;
    }

    try {
      const response = await addExtractionRule(selectedEntityType, newRule);
      if (response.success) {
        setSuccess(`成功为 ${selectedEntityType} 添加提取规则`);
        setShowRuleModal(false);
        setNewRule({ name: '', pattern: '', description: '', enabled: true });
        setSelectedEntityType('');
        loadEntityConfig();
      } else {
        setError('添加提取规则失败');
      }
    } catch (error) {
      setError(`添加提取规则失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 加载指定实体类型的词典
  const loadDictionary = async (entityType) => {
    try {
      const response = await getDictionary(entityType);
      if (response.success && response.data) {
        setDictionaries(prev => ({
          ...prev,
          [entityType]: response.data.dictionary || []
        }));
      }
    } catch (error) {
      console.error(`加载词典失败: ${error}`);
    }
  };

  // 向词典添加术语
  const handleAddToDictionary = async () => {
    if (!selectedDictEntityType || !newTerm.trim()) {
      setError('请选择实体类型并填写术语');
      return;
    }

    try {
      const response = await addToDictionary(selectedDictEntityType, [newTerm.trim()]);
      if (response.success) {
        setSuccess(`成功向 ${selectedDictEntityType} 词典添加术语`);
        setNewTerm('');
        loadDictionary(selectedDictEntityType);
      } else {
        setError('添加术语失败');
      }
    } catch (error) {
      setError(`添加术语失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 测试实体提取
  const handleTestExtraction = async () => {
    if (!testText.trim()) {
      setError('请输入要测试的文本');
      return;
    }

    setTesting(true);
    setError('');
    try {
      const response = await testEntityExtraction(testText);
      if (response.success && response.data) {
        setTestResults(response.data);
        setSuccess('实体提取测试成功');
      } else {
        setError('实体提取测试失败');
      }
    } catch (error) {
      setError(`实体提取测试失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTesting(false);
    }
  };

  // 重置配置
  const handleResetConfig = async () => {
    if (!window.confirm('确定要重置为默认配置吗？此操作不可撤销。')) {
      return;
    }

    try {
      const response = await resetConfig();
      if (response.success) {
        setSuccess('配置已重置为默认值');
        loadEntityConfig();
      } else {
        setError('重置配置失败');
      }
    } catch (error) {
      setError(`重置配置失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 清空消息
  const clearMessages = () => {
    setError('');
    setSuccess('');
  };

  // 渲染实体类型管理界面
  const renderEntityTypesTab = () => (
    <div className="entity-types-tab">
      <div className="tab-header">
        <h3>实体类型管理</h3>
        <button 
          className="btn btn-primary"
          onClick={() => setShowEntityTypeModal(true)}
        >
          添加实体类型
        </button>
      </div>
      
      <div className="entity-types-list">
        {entityTypes.map(([type, config]) => (
          <div key={type} className="entity-type-card" style={{ borderLeftColor: config.color || '#4ECDC4' }}>
            <div className="entity-type-header">
              <span className="entity-type-name">{type}</span>
              <span className="entity-type-status">{config.enabled ? '启用' : '禁用'}</span>
            </div>
            <div className="entity-type-description">{config.description}</div>
            <div className="entity-type-actions">
              <button 
                className="btn btn-small"
                onClick={() => handleUpdateEntityType(type, { ...config, enabled: !config.enabled })}
              >
                {config.enabled ? '禁用' : '启用'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染提取规则管理界面
  const renderExtractionRulesTab = () => (
    <div className="extraction-rules-tab">
      <div className="tab-header">
        <h3>提取规则管理</h3>
        <button 
          className="btn btn-primary"
          onClick={() => setShowRuleModal(true)}
        >
          添加提取规则
        </button>
      </div>
      
      <div className="rules-list">
        {extractionRules.map((rule, index) => (
          <div key={index} className="rule-card">
            <div className="rule-header">
              <span className="rule-name">{rule.name}</span>
              <span className="rule-status">{rule.enabled ? '启用' : '禁用'}</span>
            </div>
            <div className="rule-pattern">{rule.pattern}</div>
            <div className="rule-description">{rule.description}</div>
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染词典管理界面
  const renderDictionariesTab = () => (
    <div className="dictionaries-tab">
      <div className="tab-header">
        <h3>术语词典管理</h3>
        <button 
          className="btn btn-primary"
          onClick={() => setShowDictionaryModal(true)}
        >
          添加术语
        </button>
      </div>
      
      <div className="dictionaries-list">
        {entityTypes.map(([type]) => (
          <div key={type} className="dictionary-section">
            <h4>{type} 词典</h4>
            <button 
              className="btn btn-small"
              onClick={() => {
                setSelectedDictEntityType(type);
                loadDictionary(type);
              }}
            >
              加载词典
            </button>
            {dictionaries[type] && (
              <div className="terms-list">
                {dictionaries[type].map((term, index) => (
                  <span key={index} className="term-tag">{term}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染实体提取测试界面
  const renderTestExtractionTab = () => (
    <div className="test-extraction-tab">
      <div className="tab-header">
        <h3>实体提取测试</h3>
      </div>
      
      <div className="test-input-section">
        <textarea
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          placeholder="请输入要测试的文本..."
          rows={6}
          className="test-textarea"
        />
        <button 
          className="btn btn-primary"
          onClick={handleTestExtraction}
          disabled={testing || !testText.trim()}
        >
          {testing ? '测试中...' : '测试提取'}
        </button>
      </div>
      
      {testResults && (
        <div className="test-results">
          <h4>提取结果</h4>
          <div className="results-summary">
            提取到 {testResults.total_entities || 0} 个实体，
            {testResults.total_relationships || 0} 个关系
          </div>
          
          {testResults.entities && testResults.entities.length > 0 && (
            <div className="entities-list">
              <h5>提取到的实体：</h5>
              {testResults.entities.map((entity, index) => (
                <div key={index} className="entity-item">
                  <span className="entity-text">{entity.text}</span>
                  <span className="entity-type">{entity.type}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="entity-config-management">
      <div className="config-header">
        <h2>实体配置管理</h2>
        <div className="config-actions">
          <button className="btn btn-secondary" onClick={handleResetConfig}>
            重置配置
          </button>
        </div>
      </div>

      {/* 消息显示 */}
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={clearMessages}>×</button>
        </div>
      )}
      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={clearMessages}>×</button>
        </div>
      )}

      {/* 标签页导航 */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'entity-types' ? 'active' : ''}`}
          onClick={() => setActiveTab('entity-types')}
        >
          实体类型
        </button>
        <button 
          className={`tab-btn ${activeTab === 'extraction-rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('extraction-rules')}
        >
          提取规则
        </button>
        <button 
          className={`tab-btn ${activeTab === 'dictionaries' ? 'active' : ''}`}
          onClick={() => setActiveTab('dictionaries')}
        >
          术语词典
        </button>
        <button 
          className={`tab-btn ${activeTab === 'test-extraction' ? 'active' : ''}`}
          onClick={() => setActiveTab('test-extraction')}
        >
          提取测试
        </button>
      </div>

      {/* 标签页内容 */}
      <div className="tab-content">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <>
            {activeTab === 'entity-types' && renderEntityTypesTab()}
            {activeTab === 'extraction-rules' && renderExtractionRulesTab()}
            {activeTab === 'dictionaries' && renderDictionariesTab()}
            {activeTab === 'test-extraction' && renderTestExtractionTab()}
          </>
        )}
      </div>

      {/* 添加实体类型模态框 */}
      {showEntityTypeModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>添加实体类型</h3>
            <div className="modal-content">
              <div className="form-group">
                <label>实体类型名称（英文大写）</label>
                <input
                  type="text"
                  value={newEntityType.name}
                  onChange={(e) => setNewEntityType({...newEntityType, name: e.target.value})}
                  placeholder="例如：TECH"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <input
                  type="text"
                  value={newEntityType.description}
                  onChange={(e) => setNewEntityType({...newEntityType, description: e.target.value})}
                  placeholder="例如：技术术语"
                />
              </div>
              <div className="form-group">
                <label>颜色</label>
                <input
                  type="color"
                  value={newEntityType.color}
                  onChange={(e) => setNewEntityType({...newEntityType, color: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={newEntityType.enabled}
                    onChange={(e) => setNewEntityType({...newEntityType, enabled: e.target.checked})}
                  />
                  启用
                </label>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary" onClick={handleAddEntityType}>
                添加
              </button>
              <button className="btn btn-secondary" onClick={() => setShowEntityTypeModal(false)}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 添加提取规则模态框 */}
      {showRuleModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>添加提取规则</h3>
            <div className="modal-content">
              <div className="form-group">
                <label>选择实体类型</label>
                <select
                  value={selectedEntityType}
                  onChange={(e) => setSelectedEntityType(e.target.value)}
                >
                  <option value="">请选择实体类型</option>
                  {entityTypes.map(([type]) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>规则名称</label>
                <input
                  type="text"
                  value={newRule.name}
                  onChange={(e) => setNewRule({...newRule, name: e.target.value})}
                  placeholder="例如：中文人名识别"
                />
              </div>
              <div className="form-group">
                <label>正则表达式模式</label>
                <input
                  type="text"
                  value={newRule.pattern}
                  onChange={(e) => setNewRule({...newRule, pattern: e.target.value})}
                  placeholder="例如：r'[张王李赵]\\w{1,2}'"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <input
                  type="text"
                  value={newRule.description}
                  onChange={(e) => setNewRule({...newRule, description: e.target.value})}
                  placeholder="例如：基于常见姓氏的中文人名识别"
                />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={newRule.enabled}
                    onChange={(e) => setNewRule({...newRule, enabled: e.target.checked})}
                  />
                  启用
                </label>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary" onClick={handleAddExtractionRule}>
                添加
              </button>
              <button className="btn btn-secondary" onClick={() => setShowRuleModal(false)}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 添加术语模态框 */}
      {showDictionaryModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>添加术语</h3>
            <div className="modal-content">
              <div className="form-group">
                <label>选择实体类型</label>
                <select
                  value={selectedDictEntityType}
                  onChange={(e) => setSelectedDictEntityType(e.target.value)}
                >
                  <option value="">请选择实体类型</option>
                  {entityTypes.map(([type]) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>术语</label>
                <input
                  type="text"
                  value={newTerm}
                  onChange={(e) => setNewTerm(e.target.value)}
                  placeholder="例如：人工智能"
                />
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary" onClick={handleAddToDictionary}>
                添加
              </button>
              <button className="btn btn-secondary" onClick={() => setShowDictionaryModal(false)}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EntityConfigManagement;