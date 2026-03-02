/**
 * 能力卡片组件
 *
 * 展示单个能力的详细信息，包括名称、描述、分类、状态、来源市场等
 * 支持测试、配置、查看详情等操作
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import './CapabilityCard.css';

/**
 * 能力卡片组件
 *
 * @param {Object} props - 组件属性
 * @param {Object} props.capability - 能力数据对象
 * @param {Function} props.onToggle - 切换启用/禁用状态的回调函数
 * @param {Function} props.onTest - 测试能力的回调函数
 * @param {Function} props.onConfig - 配置能力的回调函数
 * @param {Function} props.onDetail - 查看详情的回调函数
 */
export function CapabilityCard({ capability, onToggle, onTest, onConfig, onDetail }) {
  const { t } = useTranslation();

  const {
    id,
    name,
    display_name,
    description,
    type,
    category,
    status,
    is_official,
    is_builtin,
    source,
    marketplace,
    marketplace_url,
    icon,
    version,
    author,
    tags = [],
    is_protected,
    allow_disable,
    allow_edit
  } = capability;

  /**
   * 获取类型标签
   */
  const getTypeLabel = () => {
    switch (type) {
      case 'tool':
        return t('capabilityCenter.types.tool');
      case 'skill':
        return t('capabilityCenter.types.skill');
      case 'mcp':
        return t('capabilityCenter.types.mcp');
      default:
        return type;
    }
  };

  /**
   * 获取类型样式类
   */
  const getTypeClass = () => {
    switch (type) {
      case 'tool':
        return 'type-tool';
      case 'skill':
        return 'type-skill';
      case 'mcp':
        return 'type-mcp';
      default:
        return 'type-default';
    }
  };

  /**
   * 获取状态样式类
   */
  const getStatusClass = () => {
    switch (status) {
      case 'active':
        return 'status-active';
      case 'disabled':
        return 'status-disabled';
      default:
        return 'status-default';
    }
  };

  /**
   * 获取来源标签
   */
  const getSourceLabel = () => {
    if (source) return source;
    if (is_builtin) return t('capabilityCenter.sources.builtin');
    if (is_official) return t('capabilityCenter.sources.official');
    return t('capabilityCenter.sources.user');
  };

  /**
   * 获取来源样式类
   */
  const getSourceClass = () => {
    if (source === 'marketplace') return 'source-marketplace';
    if (is_builtin) return 'source-builtin';
    if (is_official) return 'source-official';
    return 'source-user';
  };

  /**
   * 获取市场名称
   */
  const getMarketplaceName = () => {
    if (!marketplace) return null;

    const marketplaceNames = {
      'mcpmarket': 'MCP Market',
      'modelscope': 'ModelScope',
      'claude': 'Claude Skills',
      'skillsmp': 'Skills MP',
      'skillhub': 'SkillHub',
      'github': 'GitHub',
      'custom': t('capabilityCenter.sources.custom', '自定义')
    };

    return marketplaceNames[marketplace] || marketplace;
  };

  /**
   * 处理测试按钮点击
   */
  const handleTest = (e) => {
    e.stopPropagation();
    if (onTest) {
      onTest(capability);
    }
  };

  /**
   * 处理配置按钮点击
   */
  const handleConfig = (e) => {
    e.stopPropagation();
    if (onConfig) {
      onConfig(capability);
    }
  };

  /**
   * 处理详情按钮点击
   */
  const handleDetail = (e) => {
    e.stopPropagation();
    if (onDetail) {
      onDetail(capability);
    }
  };

  /**
   * 处理切换按钮点击
   */
  const handleToggle = (e) => {
    e.stopPropagation();
    if (onToggle) {
      onToggle(capability);
    }
  };

  // 判断是否允许操作
  const canDisable = allow_disable !== false && !is_protected;
  const canEdit = allow_edit !== false && !is_protected;
  const isActive = status === 'active';

  return (
    <div className={`capability-card ${getStatusClass()}`}>
      {/* 头部：图标和名称 */}
      <div className="capability-card-header">
        <div className="capability-icon">
          {icon || (type === 'tool' ? '🔧' : type === 'skill' ? '🎯' : '📦')}
        </div>
        <div className="capability-title-section">
          <h3 className="capability-name">
            {display_name || name}
            {version && <span className="capability-version">v{version}</span>}
          </h3>
          <div className="capability-badges">
            <span className={`badge type-badge ${getTypeClass()}`}>
              {getTypeLabel()}
            </span>
            <span className={`badge source-badge ${getSourceClass()}`}>
              {getSourceLabel()}
            </span>
            <span className={`badge status-badge ${getStatusClass()}`}>
              {status === 'active'
                ? t('capabilityCenter.status.active')
                : t('capabilityCenter.status.disabled')}
            </span>
          </div>
        </div>
      </div>

      {/* 描述 */}
      {description && (
        <p className="capability-description">{description}</p>
      )}

      {/* 分类 */}
      {category && (
        <div className="capability-category">
          <span className="category-label">{t('capabilityCenter.category')}:</span>
          <span className="category-value">{category}</span>
        </div>
      )}

      {/* 标签 */}
      {tags.length > 0 && (
        <div className="capability-tags">
          {tags.map((tag, index) => (
            <span key={index} className="capability-tag">
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* 作者信息 */}
      {author && (
        <div className="capability-author">
          <span className="author-label">{t('capabilityCenter.author')}:</span>
          <span className="author-value">{author}</span>
        </div>
      )}

      {/* 来源市场信息 */}
      {marketplace && (
        <div className="capability-marketplace">
          <span className="marketplace-label">{t('capabilityCenter.marketplace', '来源市场')}:</span>
          <span className="marketplace-value">
            {marketplace_url ? (
              <a
                href={marketplace_url}
                target="_blank"
                rel="noopener noreferrer"
                className="marketplace-link"
              >
                {getMarketplaceName()}
              </a>
            ) : (
              getMarketplaceName()
            )}
          </span>
        </div>
      )}

      {/* 操作按钮区域 */}
      <div className="capability-actions">
        {/* 主要操作按钮 */}
        <div className="capability-main-actions">
          {/* 测试按钮 - 仅启用状态下可用 */}
          <button
            className="action-button test-button"
            onClick={handleTest}
            disabled={!isActive}
            title={isActive ? t('capabilityCenter.actions.test', '测试') : t('capabilityCenter.actions.testDisabled', '请先启用能力后再测试')}
          >
            <span className="action-icon">▶️</span>
            <span className="action-text">{t('capabilityCenter.actions.test', '测试')}</span>
          </button>

          {/* 配置按钮 */}
          <button
            className="action-button config-button"
            onClick={handleConfig}
            disabled={!canEdit}
            title={canEdit ? t('capabilityCenter.actions.configure', '配置') : t('capabilityCenter.actions.configDisabled', '该能力不允许配置')}
          >
            <span className="action-icon">⚙️</span>
            <span className="action-text">{t('capabilityCenter.actions.configure', '配置')}</span>
          </button>

          {/* 详情按钮 */}
          <button
            className="action-button detail-button"
            onClick={handleDetail}
            title={t('capabilityCenter.actions.detail', '查看详情')}
          >
            <span className="action-icon">📋</span>
            <span className="action-text">{t('capabilityCenter.actions.detail', '详情')}</span>
          </button>
        </div>

        {/* 启用/禁用切换按钮 */}
        <button
          className={`action-button toggle-button ${status === 'active' ? 'disable' : 'enable'}`}
          onClick={handleToggle}
          disabled={!canDisable}
          title={!canDisable ? t('capabilityCenter.actions.toggleDisabled', '该能力不允许禁用') : ''}
        >
          {status === 'active'
            ? t('capabilityCenter.actions.disable')
            : t('capabilityCenter.actions.enable')}
        </button>
      </div>
    </div>
  );
}

export default CapabilityCard;
