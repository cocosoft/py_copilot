/**
 * 能力详情对话框组件
 *
 * 展示工具、技能、MCP能力的详细信息
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { capabilityCenterApi } from '../../services/capabilityCenterApi';
import './CapabilityDetailDialog.css';

/**
 * 能力详情对话框组件
 *
 * @param {Object} props - 组件属性
 * @param {boolean} props.isOpen - 是否打开
 * @param {Object} props.capability - 能力数据
 * @param {Function} props.onClose - 关闭回调
 */
export function CapabilityDetailDialog({ isOpen, capability, onClose }) {
  const { t } = useTranslation();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('info');

  // 加载能力详情
  useEffect(() => {
    if (isOpen && capability) {
      loadDetail();
    }
  }, [isOpen, capability]);

  /**
   * 加载详情
   */
  const loadDetail = async () => {
    if (!capability) return;

    setLoading(true);
    setError(null);

    try {
      const response = await capabilityCenterApi.getCapabilityDetail(
        capability.type,
        capability.id
      );

      if (response.success) {
        setDetail(response.data);
      } else {
        setError(response.message || t('capabilityCenter.detail.loadError'));
      }
    } catch (err) {
      setError(err.message || t('capabilityCenter.detail.loadError'));
    } finally {
      setLoading(false);
    }
  };

  /**
   * 格式化日期
   */
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  /**
   * 渲染基本信息
   */
  const renderInfoTab = () => {
    if (!detail) return null;

    const infoItems = [
      { label: t('capabilityCenter.detail.name', '名称'), value: detail.name },
      { label: t('capabilityCenter.detail.displayName', '显示名称'), value: detail.display_name },
      { label: t('capabilityCenter.detail.type', '类型'), value: detail.type },
      { label: t('capabilityCenter.detail.category', '分类'), value: detail.category || detail.skill_type || '-' },
      { label: t('capabilityCenter.detail.version', '版本'), value: detail.version },
      { label: t('capabilityCenter.detail.author', '作者'), value: detail.author || '-' },
      { label: t('capabilityCenter.detail.source', '来源'), value: detail.source },
      { label: t('capabilityCenter.detail.status', '状态'), value: detail.status || (detail.is_active ? 'active' : 'disabled') },
      { label: t('capabilityCenter.detail.usageCount', '使用次数'), value: detail.usage_count || 0 },
      { label: t('capabilityCenter.detail.createdAt', '创建时间'), value: formatDate(detail.created_at) },
      { label: t('capabilityCenter.detail.updatedAt', '更新时间'), value: formatDate(detail.updated_at) },
    ];

    // MCP工具特殊字段
    if (detail.tool_type === 'mcp') {
      infoItems.push({
        label: t('capabilityCenter.detail.mcpServerId', 'MCP服务器ID'),
        value: detail.mcp_server_id || '-'
      });
    }

    return (
      <div className="detail-info-tab">
        <div className="detail-description">
          <h4>{t('capabilityCenter.detail.description', '描述')}</h4>
          <p>{detail.description || t('capabilityCenter.detail.noDescription', '暂无描述')}</p>
        </div>

        <div className="detail-info-grid">
          {infoItems.map((item, index) => (
            <div key={index} className="detail-info-item">
              <span className="detail-info-label">{item.label}</span>
              <span className="detail-info-value">{item.value || '-'}</span>
            </div>
          ))}
        </div>

        {detail.tags && detail.tags.length > 0 && (
          <div className="detail-tags-section">
            <h4>{t('capabilityCenter.detail.tags', '标签')}</h4>
            <div className="detail-tags-list">
              {detail.tags.map((tag, index) => (
                <span key={index} className="detail-tag">{tag}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  /**
   * 渲染参数定义
   */
  const renderParametersTab = () => {
    if (!detail || !detail.parameters || detail.parameters.length === 0) {
      return (
        <div className="detail-empty">
          {t('capabilityCenter.detail.noParameters', '该能力没有定义参数')}
        </div>
      );
    }

    return (
      <div className="detail-parameters-tab">
        <h4>{t('capabilityCenter.detail.parameters', '参数定义')}</h4>
        <div className="detail-parameters-list">
          {detail.parameters.map((param, index) => (
            <div key={index} className="detail-parameter-item">
              <div className="parameter-header">
                <span className="parameter-name">{param.name}</span>
                <span className={`parameter-type type-${param.type}`}>{param.type}</span>
                {param.required && (
                  <span className="parameter-required">{t('capabilityCenter.detail.required', '必填')}</span>
                )}
              </div>
              <div className="parameter-description">{param.description || '-'}</div>
              {param.default !== undefined && param.default !== null && (
                <div className="parameter-default">
                  {t('capabilityCenter.detail.default', '默认值')}: {String(param.default)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  /**
   * 渲染配置信息
   */
  const renderConfigTab = () => {
    if (!detail || !detail.config || Object.keys(detail.config).length === 0) {
      return (
        <div className="detail-empty">
          {t('capabilityCenter.detail.noConfig', '该能力没有配置项')}
        </div>
      );
    }

    return (
      <div className="detail-config-tab">
        <h4>{t('capabilityCenter.detail.config', '配置信息')}</h4>
        <pre className="detail-config-json">
          {JSON.stringify(detail.config, null, 2)}
        </pre>
      </div>
    );
  };

  /**
   * 渲染关联智能体
   */
  const renderAgentsTab = () => {
    if (!detail || !detail.linked_agents || detail.linked_agents.length === 0) {
      return (
        <div className="detail-empty">
          {t('capabilityCenter.detail.noAgents', '该能力未关联任何智能体')}
        </div>
      );
    }

    return (
      <div className="detail-agents-tab">
        <h4>{t('capabilityCenter.detail.linkedAgents', '关联智能体')}</h4>
        <div className="detail-agents-list">
          {detail.linked_agents.map((agent, index) => (
            <div key={index} className="detail-agent-item">
              <div className="agent-info">
                <span className="agent-name">{agent.name}</span>
                <span className={`agent-status ${agent.enabled ? 'enabled' : 'disabled'}`}>
                  {agent.enabled
                    ? t('capabilityCenter.detail.agentEnabled', '已启用')
                    : t('capabilityCenter.detail.agentDisabled', '已禁用')}
                </span>
              </div>
              <div className="agent-priority">
                {t('capabilityCenter.detail.priority', '优先级')}: {agent.priority}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  /**
   * 渲染代码预览（仅技能）
   */
  const renderCodeTab = () => {
    if (!detail || !detail.code_preview) {
      return (
        <div className="detail-empty">
          {t('capabilityCenter.detail.noCode', '该能力没有代码')}
        </div>
      );
    }

    return (
      <div className="detail-code-tab">
        <h4>{t('capabilityCenter.detail.codePreview', '代码预览')}</h4>
        <pre className="detail-code-block">
          <code>{detail.code_preview}</code>
        </pre>
      </div>
    );
  };

  /**
   * 渲染元数据
   */
  const renderMetadataTab = () => {
    if (!detail || !detail.metadata || Object.keys(detail.metadata).length === 0) {
      return (
        <div className="detail-empty">
          {t('capabilityCenter.detail.noMetadata', '该能力没有元数据')}
        </div>
      );
    }

    return (
      <div className="detail-metadata-tab">
        <h4>{t('capabilityCenter.detail.metadata', '元数据')}</h4>
        <pre className="detail-metadata-json">
          {JSON.stringify(detail.metadata, null, 2)}
        </pre>
      </div>
    );
  };

  /**
   * 渲染内容
   */
  const renderContent = () => {
    if (loading) {
      return (
        <div className="detail-loading">
          <div className="loading-spinner"></div>
          <span>{t('capabilityCenter.detail.loading', '加载中...')}</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="detail-error">
          <p>{error}</p>
          <button className="retry-button" onClick={loadDetail}>
            {t('capabilityCenter.detail.retry', '重试')}
          </button>
        </div>
      );
    }

    if (!detail) {
      return (
        <div className="detail-empty">
          {t('capabilityCenter.detail.noData', '暂无数据')}
        </div>
      );
    }

    switch (activeTab) {
      case 'info':
        return renderInfoTab();
      case 'parameters':
        return renderParametersTab();
      case 'config':
        return renderConfigTab();
      case 'agents':
        return renderAgentsTab();
      case 'code':
        return renderCodeTab();
      case 'metadata':
        return renderMetadataTab();
      default:
        return renderInfoTab();
    }
  };

  if (!isOpen || !capability) return null;

  const tabs = [
    { id: 'info', label: t('capabilityCenter.detail.tabs.info', '基本信息') },
    { id: 'parameters', label: t('capabilityCenter.detail.tabs.parameters', '参数') },
    { id: 'config', label: t('capabilityCenter.detail.tabs.config', '配置') },
    { id: 'agents', label: t('capabilityCenter.detail.tabs.agents', '关联智能体') },
  ];

  // 技能特有标签
  if (capability.type === 'skill') {
    tabs.push({ id: 'code', label: t('capabilityCenter.detail.tabs.code', '代码') });
    tabs.push({ id: 'metadata', label: t('capabilityCenter.detail.tabs.metadata', '元数据') });
  }

  return (
    <div className="capability-detail-dialog-overlay" onClick={onClose}>
      <div className="capability-detail-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="detail-dialog-header">
          <div className="detail-header-info">
            <span className="detail-icon">{capability.icon || (capability.type === 'tool' ? '🔧' : '🎯')}</span>
            <div>
              <h3 className="detail-title">
                {capability.display_name || capability.name}
              </h3>
              <span className={`detail-type-badge type-${capability.type}`}>
                {capability.type === 'tool'
                  ? t('capabilityCenter.types.tool')
                  : t('capabilityCenter.types.skill')}
              </span>
            </div>
          </div>
          <button className="detail-dialog-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="detail-dialog-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`detail-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="detail-dialog-content">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}

export default CapabilityDetailDialog;
