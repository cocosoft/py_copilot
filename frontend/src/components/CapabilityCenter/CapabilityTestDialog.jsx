/**
 * 能力测试对话框组件
 *
 * 提供工具、技能、MCP能力的测试功能
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { capabilityCenterApi } from '../../services/capabilityCenterApi';
import './CapabilityTestDialog.css';

/**
 * 能力测试对话框组件
 *
 * @param {Object} props - 组件属性
 * @param {boolean} props.isOpen - 是否打开
 * @param {Object} props.capability - 能力数据
 * @param {Function} props.onClose - 关闭回调
 */
export function CapabilityTestDialog({ isOpen, capability, onClose }) {
  const { t } = useTranslation();
  const [parameters, setParameters] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // 加载能力详情获取参数定义
  useEffect(() => {
    if (isOpen && capability) {
      loadCapabilityDetail();
    }
  }, [isOpen, capability]);

  /**
   * 加载能力详情
   */
  const loadCapabilityDetail = async () => {
    if (!capability) return;

    setLoadingDetail(true);
    try {
      const response = await capabilityCenterApi.getCapabilityDetail(
        capability.type,
        capability.id
      );
      if (response.success) {
        setDetail(response.data);
        // 初始化参数
        const initialParams = {};
        if (response.data.parameters) {
          response.data.parameters.forEach(param => {
            initialParams[param.name] = param.default || '';
          });
        }
        // 技能测试添加默认input参数
        if (capability.type === 'skill') {
          initialParams.input = '';
        }
        setParameters(initialParams);
      }
    } catch (err) {
      console.error('加载能力详情失败:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  /**
   * 处理参数变化
   */
  const handleParamChange = (name, value) => {
    setParameters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  /**
   * 执行测试
   */
  const handleTest = async () => {
    if (!capability) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await capabilityCenterApi.testCapability(
        capability.type,
        capability.id,
        parameters
      );

      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message || t('capabilityCenter.test.failed'));
        if (response.data) {
          setResult(response.data);
        }
      }
    } catch (err) {
      setError(err.message || t('capabilityCenter.test.error'));
    } finally {
      setLoading(false);
    }
  };

  /**
   * 清空结果
   */
  const handleClear = () => {
    setResult(null);
    setError(null);
  };

  /**
   * 渲染参数输入
   */
  const renderParameterInputs = () => {
    if (!detail || !detail.parameters || detail.parameters.length === 0) {
      if (capability?.type === 'skill') {
        return (
          <div className="test-param-row">
            <label className="test-param-label">
              {t('capabilityCenter.test.inputLabel', '测试输入')}
            </label>
            <textarea
              className="test-param-input test-param-textarea"
              value={parameters.input || ''}
              onChange={(e) => handleParamChange('input', e.target.value)}
              placeholder={t('capabilityCenter.test.inputPlaceholder', '输入测试内容...')}
              rows={4}
            />
          </div>
        );
      }
      return (
        <div className="test-no-params">
          {t('capabilityCenter.test.noParams', '该能力无需配置参数')}
        </div>
      );
    }

    return detail.parameters.map((param, index) => (
      <div key={index} className="test-param-row">
        <label className="test-param-label">
          {param.name}
          {param.required && <span className="required-mark">*</span>}
          <span className="param-type">({param.type})</span>
        </label>
        {param.type === 'boolean' ? (
          <select
            className="test-param-input"
            value={parameters[param.name] || ''}
            onChange={(e) => handleParamChange(param.name, e.target.value === 'true')}
          >
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        ) : param.type === 'number' || param.type === 'integer' ? (
          <input
            type="number"
            className="test-param-input"
            value={parameters[param.name] || ''}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
            placeholder={param.description || ''}
          />
        ) : (
          <input
            type="text"
            className="test-param-input"
            value={parameters[param.name] || ''}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
            placeholder={param.description || ''}
          />
        )}
        {param.description && (
          <span className="param-description">{param.description}</span>
        )}
      </div>
    ));
  };

  /**
   * 渲染结果
   */
  const renderResult = () => {
    if (!result) return null;

    return (
      <div className={`test-result ${result.success ? 'success' : 'error'}`}>
        <div className="test-result-header">
          <span className="test-result-status">
            {result.success
              ? t('capabilityCenter.test.success', '测试成功')
              : t('capabilityCenter.test.failed', '测试失败')}
          </span>
          {result.execution_time && (
            <span className="test-execution-time">
              {t('capabilityCenter.test.executionTime', '执行时间')}: {result.execution_time}s
            </span>
          )}
        </div>

        {result.error && (
          <div className="test-error-message">
            <strong>{t('capabilityCenter.test.error', '错误')}:</strong> {result.error}
          </div>
        )}

        {result.result !== undefined && result.result !== null && (
          <div className="test-result-content">
            <div className="test-result-label">
              {t('capabilityCenter.test.result', '返回结果')}:
            </div>
            <pre className="test-result-json">
              {JSON.stringify(result.result, null, 2)}
            </pre>
          </div>
        )}

        {result.metadata && (
          <div className="test-result-metadata">
            <div className="test-result-label">
              {t('capabilityCenter.test.metadata', '元数据')}:
            </div>
            <pre className="test-result-json">
              {JSON.stringify(result.metadata, null, 2)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  if (!isOpen || !capability) return null;

  return (
    <div className="capability-test-dialog-overlay" onClick={onClose}>
      <div className="capability-test-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="test-dialog-header">
          <h3 className="test-dialog-title">
            {t('capabilityCenter.test.title', '测试能力')}: {capability.display_name || capability.name}
          </h3>
          <button className="test-dialog-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="test-dialog-content">
          {/* 参数配置区域 */}
          <div className="test-params-section">
            <h4 className="test-section-title">
              {t('capabilityCenter.test.parameters', '参数配置')}
            </h4>
            {loadingDetail ? (
              <div className="test-loading">
                {t('capabilityCenter.test.loadingDetail', '加载参数定义...')}
              </div>
            ) : (
              <div className="test-params-form">
                {renderParameterInputs()}
              </div>
            )}
          </div>

          {/* 操作按钮 */}
          <div className="test-actions">
            <button
              className="test-button test-button-primary"
              onClick={handleTest}
              disabled={loading || loadingDetail}
            >
              {loading
                ? t('capabilityCenter.test.testing', '测试中...')
                : t('capabilityCenter.test.runTest', '执行测试')}
            </button>
            <button
              className="test-button test-button-secondary"
              onClick={handleClear}
              disabled={!result && !error}
            >
              {t('capabilityCenter.test.clear', '清空结果')}
            </button>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="test-error-alert">
              {error}
            </div>
          )}

          {/* 测试结果 */}
          {(result || error) && (
            <div className="test-result-section">
              <h4 className="test-section-title">
                {t('capabilityCenter.test.resultTitle', '测试结果')}
              </h4>
              {renderResult()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CapabilityTestDialog;
