/**
 * 能力配置对话框组件
 *
 * 提供工具、技能、MCP能力的配置功能
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { capabilityCenterApi } from '../../services/capabilityCenterApi';
import './CapabilityConfigDialog.css';

/**
 * 能力配置对话框组件
 *
 * @param {Object} props - 组件属性
 * @param {boolean} props.isOpen - 是否打开
 * @param {Object} props.capability - 能力数据
 * @param {Function} props.onClose - 关闭回调
 * @param {Function} props.onSave - 保存成功回调
 */
export function CapabilityConfigDialog({ isOpen, capability, onClose, onSave }) {
  const { t } = useTranslation();
  const [config, setConfig] = useState({});
  const [parameters, setParameters] = useState([]);
  const [originalData, setOriginalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('config');

  // 加载能力配置
  useEffect(() => {
    if (isOpen && capability) {
      loadCapabilityConfig();
    }
  }, [isOpen, capability]);

  /**
   * 加载能力配置
   */
  const loadCapabilityConfig = async () => {
    if (!capability) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await capabilityCenterApi.getCapabilityDetail(
        capability.type,
        capability.id
      );

      if (response.success) {
        const data = response.data;
        setOriginalData(data);
        setConfig(data.config || {});
        setParameters(data.parameters || []);
      } else {
        setError(response.message || t('capabilityCenter.config.loadError'));
      }
    } catch (err) {
      setError(err.message || t('capabilityCenter.config.loadError'));
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理配置项变化
   */
  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  /**
   * 处理配置项删除
   */
  const handleConfigDelete = (key) => {
    setConfig(prev => {
      const newConfig = { ...prev };
      delete newConfig[key];
      return newConfig;
    });
  };

  /**
   * 添加新配置项
   */
  const handleAddConfig = () => {
    const key = `new_key_${Date.now()}`;
    setConfig(prev => ({
      ...prev,
      [key]: ''
    }));
  };

  /**
   * 处理参数变化
   */
  const handleParamChange = (index, field, value) => {
    setParameters(prev => {
      const newParams = [...prev];
      newParams[index] = {
        ...newParams[index],
        [field]: value
      };
      return newParams;
    });
  };

  /**
   * 添加新参数
   */
  const handleAddParam = () => {
    setParameters(prev => [
      ...prev,
      {
        name: '',
        type: 'string',
        description: '',
        required: false,
        default: ''
      }
    ]);
  };

  /**
   * 删除参数
   */
  const handleDeleteParam = (index) => {
    setParameters(prev => prev.filter((_, i) => i !== index));
  };

  /**
   * 保存配置
   */
  const handleSave = async () => {
    if (!capability) return;

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      // 过滤掉名称为空的参数
      const validParams = parameters.filter(p => p.name.trim() !== '');

      const response = await capabilityCenterApi.updateCapabilityConfig(
        capability.type,
        capability.id,
        config,
        capability.type === 'tool' ? validParams : null
      );

      if (response.success) {
        setSuccess(t('capabilityCenter.config.saveSuccess'));
        if (onSave) {
          onSave(response.data);
        }
        // 延迟关闭
        setTimeout(() => {
          onClose();
        }, 1500);
      } else {
        setError(response.message || t('capabilityCenter.config.saveError'));
      }
    } catch (err) {
      setError(err.message || t('capabilityCenter.config.saveError'));
    } finally {
      setSaving(false);
    }
  };

  /**
   * 重置配置
   */
  const handleReset = () => {
    if (originalData) {
      setConfig(originalData.config || {});
      setParameters(originalData.parameters || []);
    }
    setError(null);
    setSuccess(null);
  };

  /**
   * 渲染配置编辑器
   */
  const renderConfigEditor = () => {
    const configEntries = Object.entries(config);

    return (
      <div className="config-editor">
        <div className="config-editor-header">
          <h4>{t('capabilityCenter.config.configItems', '配置项')}</h4>
          <button className="config-add-button" onClick={handleAddConfig}>
            + {t('capabilityCenter.config.addItem', '添加项')}
          </button>
        </div>

        {configEntries.length === 0 ? (
          <div className="config-empty">
            {t('capabilityCenter.config.noConfigItems', '暂无配置项，点击上方按钮添加')}
          </div>
        ) : (
          <div className="config-items-list">
            {configEntries.map(([key, value], index) => (
              <div key={index} className="config-item-row">
                <input
                  type="text"
                  className="config-item-key"
                  value={key}
                  onChange={(e) => {
                    const newKey = e.target.value;
                    const newConfig = {};
                    Object.entries(config).forEach(([k, v]) => {
                      if (k === key) {
                        newConfig[newKey] = v;
                      } else {
                        newConfig[k] = v;
                      }
                    });
                    setConfig(newConfig);
                  }}
                  placeholder={t('capabilityCenter.config.key', '键')}
                />
                <input
                  type="text"
                  className="config-item-value"
                  value={value}
                  onChange={(e) => handleConfigChange(key, e.target.value)}
                  placeholder={t('capabilityCenter.config.value', '值')}
                />
                <button
                  className="config-item-delete"
                  onClick={() => handleConfigDelete(key)}
                  title={t('capabilityCenter.config.delete', '删除')}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="config-preview">
          <h4>{t('capabilityCenter.config.preview', '配置预览')}</h4>
          <pre className="config-preview-json">
            {JSON.stringify(config, null, 2)}
          </pre>
        </div>
      </div>
    );
  };

  /**
   * 渲染参数编辑器
   */
  const renderParametersEditor = () => {
    if (capability?.type !== 'tool') {
      return (
        <div className="config-not-available">
          {t('capabilityCenter.config.paramsOnlyForTools', '参数编辑仅适用于工具类型')}
        </div>
      );
    }

    return (
      <div className="parameters-editor">
        <div className="parameters-editor-header">
          <h4>{t('capabilityCenter.config.parameters', '参数定义')}</h4>
          <button className="config-add-button" onClick={handleAddParam}>
            + {t('capabilityCenter.config.addParam', '添加参数')}
          </button>
        </div>

        {parameters.length === 0 ? (
          <div className="config-empty">
            {t('capabilityCenter.config.noParameters', '暂无参数定义，点击上方按钮添加')}
          </div>
        ) : (
          <div className="parameters-list">
            {parameters.map((param, index) => (
              <div key={index} className="parameter-editor-row">
                <div className="parameter-editor-header">
                  <input
                    type="text"
                    className="parameter-name-input"
                    value={param.name}
                    onChange={(e) => handleParamChange(index, 'name', e.target.value)}
                    placeholder={t('capabilityCenter.config.paramName', '参数名称')}
                  />
                  <select
                    className="parameter-type-select"
                    value={param.type}
                    onChange={(e) => handleParamChange(index, 'type', e.target.value)}
                  >
                    <option value="string">string</option>
                    <option value="number">number</option>
                    <option value="integer">integer</option>
                    <option value="boolean">boolean</option>
                    <option value="object">object</option>
                    <option value="array">array</option>
                  </select>
                  <label className="parameter-required-label">
                    <input
                      type="checkbox"
                      checked={param.required}
                      onChange={(e) => handleParamChange(index, 'required', e.target.checked)}
                    />
                    {t('capabilityCenter.config.required', '必填')}
                  </label>
                  <button
                    className="parameter-delete-button"
                    onClick={() => handleDeleteParam(index)}
                    title={t('capabilityCenter.config.delete', '删除')}
                  >
                    ×
                  </button>
                </div>
                <input
                  type="text"
                  className="parameter-description-input"
                  value={param.description || ''}
                  onChange={(e) => handleParamChange(index, 'description', e.target.value)}
                  placeholder={t('capabilityCenter.config.paramDescription', '参数描述')}
                />
                <input
                  type="text"
                  className="parameter-default-input"
                  value={param.default || ''}
                  onChange={(e) => handleParamChange(index, 'default', e.target.value)}
                  placeholder={t('capabilityCenter.config.paramDefault', '默认值')}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  /**
   * 渲染内容
   */
  const renderContent = () => {
    if (loading) {
      return (
        <div className="config-loading">
          <div className="loading-spinner"></div>
          <span>{t('capabilityCenter.config.loading', '加载中...')}</span>
        </div>
      );
    }

    if (error && !originalData) {
      return (
        <div className="config-error">
          <p>{error}</p>
          <button className="retry-button" onClick={loadCapabilityConfig}>
            {t('capabilityCenter.config.retry', '重试')}
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'config':
        return renderConfigEditor();
      case 'parameters':
        return renderParametersEditor();
      default:
        return renderConfigEditor();
    }
  };

  if (!isOpen || !capability) return null;

  const tabs = [
    { id: 'config', label: t('capabilityCenter.config.tabs.config', '配置项') },
  ];

  // 工具类型显示参数编辑
  if (capability.type === 'tool') {
    tabs.push({ id: 'parameters', label: t('capabilityCenter.config.tabs.parameters', '参数定义') });
  }

  return (
    <div className="capability-config-dialog-overlay" onClick={onClose}>
      <div className="capability-config-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="config-dialog-header">
          <h3 className="config-dialog-title">
            {t('capabilityCenter.config.title', '配置能力')}: {capability.display_name || capability.name}
          </h3>
          <button className="config-dialog-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="config-dialog-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`config-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="config-dialog-content">
          {/* 成功提示 */}
          {success && (
            <div className="config-success-alert">
              {success}
            </div>
          )}

          {/* 错误提示 */}
          {error && (
            <div className="config-error-alert">
              {error}
            </div>
          )}

          {renderContent()}
        </div>

        <div className="config-dialog-footer">
          <button
            className="config-button config-button-secondary"
            onClick={handleReset}
            disabled={loading || saving}
          >
            {t('capabilityCenter.config.reset', '重置')}
          </button>
          <div className="config-footer-actions">
            <button
              className="config-button config-button-secondary"
              onClick={onClose}
              disabled={saving}
            >
              {t('capabilityCenter.config.cancel', '取消')}
            </button>
            <button
              className="config-button config-button-primary"
              onClick={handleSave}
              disabled={loading || saving}
            >
              {saving
                ? t('capabilityCenter.config.saving', '保存中...')
                : t('capabilityCenter.config.save', '保存')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CapabilityConfigDialog;
