/**
 * 能力卡片组件
 *
 * 展示单个能力的详细信息，包括名称、描述、分类、状态等
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
 */
export function CapabilityCard({ capability, onToggle }) {
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
    icon,
    version,
    author,
    tags = []
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
    if (is_builtin) return t('capabilityCenter.sources.builtin');
    if (is_official) return t('capabilityCenter.sources.official');
    return t('capabilityCenter.sources.user');
  };

  /**
   * 获取来源样式类
   */
  const getSourceClass = () => {
    if (is_builtin) return 'source-builtin';
    if (is_official) return 'source-official';
    return 'source-user';
  };

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

      {/* 操作按钮 */}
      <div className="capability-actions">
        <button
          className={`action-button toggle-button ${status === 'active' ? 'disable' : 'enable'}`}
          onClick={onToggle}
        >
          {status === 'active' 
            ? t('capabilityCenter.actions.disable') 
            : t('capabilityCenter.actions.enable')}
        </button>
        <button className="action-button config-button">
          {t('capabilityCenter.actions.configure')}
        </button>
      </div>
    </div>
  );
}

export default CapabilityCard;
