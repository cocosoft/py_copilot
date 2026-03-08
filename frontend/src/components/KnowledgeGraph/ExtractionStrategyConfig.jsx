/**
 * 提取策略配置组件
 *
 * 配置实体和关系的提取策略，包括：
 * - NLP模型选择（对接默认模型管理系统）
 * - 提取算法参数
 * - 置信度阈值
 * - 批处理设置
 */

import React, { useState, useEffect } from 'react';
import { defaultModelApi, supplierApi } from '../../utils/api';
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

  // 默认模型相关状态
  const [defaultModel, setDefaultModel] = useState(null);
  const [modelDetails, setModelDetails] = useState(null);
  const [isLoadingModel, setIsLoadingModel] = useState(false);

  // 策略配置状态
  const [config, setConfig] = useState({
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
   * 加载知识库场景的默认模型
   */
  const loadKnowledgeSceneModel = async () => {
    setIsLoadingModel(true);
    try {
      // 获取知识库场景的默认模型
      const response = await defaultModelApi.getSceneDefaultModel('knowledge');
      // API直接返回数据对象，不是 { data: ... } 格式
      if (response && response.model_id) {
        setDefaultModel(response);
        // 如果存在模型ID，获取模型详细信息
        await loadModelDetails(response.model_id);
      } else {
        // 如果场景模型不存在，尝试获取全局默认模型
        await loadGlobalDefaultModel();
      }
    } catch (error) {
      console.warn('获取知识库场景默认模型失败:', error);
      // 如果场景模型不存在，尝试获取全局默认模型
      await loadGlobalDefaultModel();
    } finally {
      setIsLoadingModel(false);
    }
  };

  /**
   * 加载全局默认模型
   */
  const loadGlobalDefaultModel = async () => {
    try {
      const globalResponse = await defaultModelApi.getGlobalDefaultModel();
      // API直接返回数据对象
      if (globalResponse && globalResponse.model_id) {
        setDefaultModel(globalResponse);
        await loadModelDetails(globalResponse.model_id);
      }
    } catch (globalError) {
      console.warn('获取全局默认模型失败:', globalError);
    }
  };

  /**
   * 加载模型详细信息
   * @param {number} modelId - 模型ID
   */
  const loadModelDetails = async (modelId) => {
    try {
      const response = await supplierApi.getModelById(modelId);
      // API直接返回数据对象
      if (response && response.id) {
        setModelDetails(response);
      }
    } catch (error) {
      console.warn('获取模型详细信息失败:', error);
    }
  };

  /**
   * 加载配置
   */
  useEffect(() => {
    setLoading(true);
    // 加载默认模型配置
    loadKnowledgeSceneModel();
    // TODO: 从API加载其他配置
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
   * 跳转到模型管理页面
   */
  const handleGoToModelManagement = () => {
    // 使用React Router导航到设置页面的模型管理标签
    window.location.href = '/settings?tab=modelManagement&section=defaultModel';
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

  /**
   * 获取模型显示名称
   * @returns {string} 模型显示名称
   */
  const getModelDisplayName = () => {
    if (modelDetails) {
      return modelDetails.name || modelDetails.model_id || '未命名模型';
    }
    if (defaultModel?.model_id) {
      return `模型ID: ${defaultModel.model_id}`;
    }
    return '未配置';
  };

  /**
   * 获取模型提供商信息
   * @returns {string} 提供商信息
   */
  const getModelProvider = () => {
    if (modelDetails?.supplier?.name) {
      return modelDetails.supplier.name;
    }
    if (modelDetails?.provider) {
      return modelDetails.provider;
    }
    return '未知提供商';
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
          {/* NLP模型配置 - 对接默认模型管理 */}
          <section className="config-section">
            <h4 className="section-title">
              <span className="section-icon">🤖</span>
              NLP模型配置
            </h4>
            <div className="section-content">
              {/* 默认模型信息卡片 */}
              <div className="default-model-info-card">
                <div className="model-info-header">
                  <h5>当前使用的模型</h5>
                  <span className="model-source-badge">
                    {defaultModel?.scope === 'scene' ? '场景默认' : '全局默认'}
                  </span>
                </div>
                
                {isLoadingModel ? (
                  <div className="model-loading">
                    <div className="loading-spinner-small"></div>
                    <span>加载模型信息...</span>
                  </div>
                ) : (
                  <div className="model-info-content">
                    <div className="model-info-row">
                      <span className="model-info-label">模型名称：</span>
                      <span className="model-info-value model-name">
                        {getModelDisplayName()}
                      </span>
                    </div>
                    <div className="model-info-row">
                      <span className="model-info-label">提供商：</span>
                      <span className="model-info-value">{getModelProvider()}</span>
                    </div>
                    {modelDetails?.context_window && (
                      <div className="model-info-row">
                        <span className="model-info-label">上下文窗口：</span>
                        <span className="model-info-value">
                          {modelDetails.context_window.toLocaleString()} tokens
                        </span>
                      </div>
                    )}
                    {modelDetails?.description && (
                      <div className="model-info-row">
                        <span className="model-info-label">描述：</span>
                        <span className="model-info-value description">
                          {modelDetails.description}
                        </span>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="model-info-actions">
                  <button 
                    className="btn-link"
                    onClick={handleGoToModelManagement}
                  >
                    <span className="link-icon">⚙️</span>
                    前往设置中心管理模型
                  </button>
                  <span className="hint-text">
                    在"设置 &gt; 模型管理 &gt; 默认模型"中配置知识库场景的默认模型
                  </span>
                </div>
              </div>

              {/* 模型配置提示 */}
              <div className="model-config-hint">
                <span className="hint-icon">💡</span>
                <div className="hint-content">
                  <p>系统将按照以下优先级选择模型：</p>
                  <ol>
                    <li>知识库场景默认模型（knowledge）</li>
                    <li>全局默认模型（global）</li>
                    <li>系统内置默认模型</li>
                  </ol>
                </div>
              </div>
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
