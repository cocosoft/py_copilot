/**
 * 提取策略配置组件
 *
 * 配置实体和关系的提取策略，包括：
 * - NLP模型选择
 * - 提取算法参数
 * - 置信度阈值
 * - 批处理设置
 */

import React, { useState, useEffect } from 'react';
import './ExtractionStrategyConfig.css';

/**
 * 提取策略配置主组件
 *
 * @returns {JSX.Element} 提取策略配置界面
 */
const ExtractionStrategyConfig = () => {
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 保存状态
  const [saving, setSaving] = useState(false);
  // 消息提示
  const [message, setMessage] = useState({ type: '', text: '' });

  // 策略配置状态
  const [config, setConfig] = useState({
    // NLP模型配置
    nlpModel: {
      provider: 'local', // local, openai, azure
      model: 'default',
      apiKey: '',
      endpoint: ''
    },
    // 实体提取配置
    entityExtraction: {
      algorithm: 'rule_based', // rule_based, ml, hybrid
      confidenceThreshold: 0.7,
      enableDictionary: true,
      enablePattern: true,
      enableNER: true,
      maxEntitiesPerDoc: 100
    },
    // 关系提取配置
    relationExtraction: {
      algorithm: 'pattern_based', // pattern_based, ml, hybrid
      confidenceThreshold: 0.6,
      maxRelationsPerEntity: 10,
      enableTransitive: false
    },
    // 批处理配置
    batchProcessing: {
      batchSize: 10,
      parallelJobs: 2,
      timeout: 300,
      retryAttempts: 3
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
      showMessage('配置保存成功');
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
    if (window.confirm('确定要重置为默认配置吗？')) {
      setConfig({
        nlpModel: {
          provider: 'local',
          model: 'default',
          apiKey: '',
          endpoint: ''
        },
        entityExtraction: {
          algorithm: 'rule_based',
          confidenceThreshold: 0.7,
          enableDictionary: true,
          enablePattern: true,
          enableNER: true,
          maxEntitiesPerDoc: 100
        },
        relationExtraction: {
          algorithm: 'pattern_based',
          confidenceThreshold: 0.6,
          maxRelationsPerEntity: 10,
          enableTransitive: false
        },
        batchProcessing: {
          batchSize: 10,
          parallelJobs: 2,
          timeout: 300,
          retryAttempts: 3
        }
      });
      showMessage('配置已重置');
    }
  };

  /**
   * 更新配置
   */
  const updateConfig = (section, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  return (
    <div className="extraction-strategy-config">
      {/* 消息提示 */}
      {message.text && (
        <div className={`strategy-message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 头部操作 */}
      <div className="strategy-header">
        <h3>提取策略配置</h3>
        <div className="header-actions">
          <button className="btn-secondary" onClick={handleReset}>
            重置默认
          </button>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? '保存中...' : '保存配置'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="strategy-loading">
          <div className="loading-spinner"></div>
          <span>加载配置中...</span>
        </div>
      ) : (
        <div className="strategy-content">
          {/* NLP模型配置 */}
          <section className="config-section">
            <h4 className="section-title">
              <span className="section-icon">🤖</span>
              NLP模型配置
            </h4>
            <div className="section-content">
              <div className="form-row">
                <div className="form-group">
                  <label>模型提供商</label>
                  <select
                    value={config.nlpModel.provider}
                    onChange={(e) => updateConfig('nlpModel', 'provider', e.target.value)}
                  >
                    <option value="local">本地模型</option>
                    <option value="openai">OpenAI</option>
                    <option value="azure">Azure OpenAI</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>模型名称</label>
                  <select
                    value={config.nlpModel.model}
                    onChange={(e) => updateConfig('nlpModel', 'model', e.target.value)}
                  >
                    <option value="default">默认模型</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    <option value="gpt-4">GPT-4</option>
                  </select>
                </div>
              </div>

              {config.nlpModel.provider !== 'local' && (
                <div className="form-row">
                  <div className="form-group flex-2">
                    <label>API端点</label>
                    <input
                      type="text"
                      value={config.nlpModel.endpoint}
                      onChange={(e) => updateConfig('nlpModel', 'endpoint', e.target.value)}
                      placeholder="https://api.openai.com/v1"
                    />
                  </div>
                  <div className="form-group flex-2">
                    <label>API密钥</label>
                    <input
                      type="password"
                      value={config.nlpModel.apiKey}
                      onChange={(e) => updateConfig('nlpModel', 'apiKey', e.target.value)}
                      placeholder="sk-..."
                    />
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* 实体提取配置 */}
          <section className="config-section">
            <h4 className="section-title">
              <span className="section-icon">🏷️</span>
              实体提取配置
            </h4>
            <div className="section-content">
              <div className="form-row">
                <div className="form-group">
                  <label>提取算法</label>
                  <select
                    value={config.entityExtraction.algorithm}
                    onChange={(e) => updateConfig('entityExtraction', 'algorithm', e.target.value)}
                  >
                    <option value="rule_based">基于规则</option>
                    <option value="ml">机器学习</option>
                    <option value="hybrid">混合模式</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>置信度阈值 ({config.entityExtraction.confidenceThreshold})</label>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.1"
                    value={config.entityExtraction.confidenceThreshold}
                    onChange={(e) => updateConfig('entityExtraction', 'confidenceThreshold', parseFloat(e.target.value))}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>每文档最大实体数</label>
                  <input
                    type="number"
                    min="10"
                    max="500"
                    value={config.entityExtraction.maxEntitiesPerDoc}
                    onChange={(e) => updateConfig('entityExtraction', 'maxEntitiesPerDoc', parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div className="form-row checkbox-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={config.entityExtraction.enableDictionary}
                    onChange={(e) => updateConfig('entityExtraction', 'enableDictionary', e.target.checked)}
                  />
                  <span>启用词典匹配</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={config.entityExtraction.enablePattern}
                    onChange={(e) => updateConfig('entityExtraction', 'enablePattern', e.target.checked)}
                  />
                  <span>启用正则模式</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={config.entityExtraction.enableNER}
                    onChange={(e) => updateConfig('entityExtraction', 'enableNER', e.target.checked)}
                  />
                  <span>启用NER模型</span>
                </label>
              </div>
            </div>
          </section>

          {/* 关系提取配置 */}
          <section className="config-section">
            <h4 className="section-title">
              <span className="section-icon">🔗</span>
              关系提取配置
            </h4>
            <div className="section-content">
              <div className="form-row">
                <div className="form-group">
                  <label>提取算法</label>
                  <select
                    value={config.relationExtraction.algorithm}
                    onChange={(e) => updateConfig('relationExtraction', 'algorithm', e.target.value)}
                  >
                    <option value="pattern_based">基于模式</option>
                    <option value="ml">机器学习</option>
                    <option value="hybrid">混合模式</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>置信度阈值 ({config.relationExtraction.confidenceThreshold})</label>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.1"
                    value={config.relationExtraction.confidenceThreshold}
                    onChange={(e) => updateConfig('relationExtraction', 'confidenceThreshold', parseFloat(e.target.value))}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>每实体最大关系数</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={config.relationExtraction.maxRelationsPerEntity}
                    onChange={(e) => updateConfig('relationExtraction', 'maxRelationsPerEntity', parseInt(e.target.value))}
                  />
                </div>
                <div className="form-group checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={config.relationExtraction.enableTransitive}
                      onChange={(e) => updateConfig('relationExtraction', 'enableTransitive', e.target.checked)}
                    />
                    <span>启用传递推理</span>
                  </label>
                </div>
              </div>
            </div>
          </section>

          {/* 批处理配置 */}
          <section className="config-section">
            <h4 className="section-title">
              <span className="section-icon">⚙️</span>
              批处理配置
            </h4>
            <div className="section-content">
              <div className="form-row">
                <div className="form-group">
                  <label>批处理大小</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={config.batchProcessing.batchSize}
                    onChange={(e) => updateConfig('batchProcessing', 'batchSize', parseInt(e.target.value))}
                  />
                </div>
                <div className="form-group">
                  <label>并行任务数</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={config.batchProcessing.parallelJobs}
                    onChange={(e) => updateConfig('batchProcessing', 'parallelJobs', parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>超时时间（秒）</label>
                  <input
                    type="number"
                    min="30"
                    max="1800"
                    value={config.batchProcessing.timeout}
                    onChange={(e) => updateConfig('batchProcessing', 'timeout', parseInt(e.target.value))}
                  />
                </div>
                <div className="form-group">
                  <label>重试次数</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={config.batchProcessing.retryAttempts}
                    onChange={(e) => updateConfig('batchProcessing', 'retryAttempts', parseInt(e.target.value))}
                  />
                </div>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
};

export default ExtractionStrategyConfig;
