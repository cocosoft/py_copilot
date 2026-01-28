import React from 'react';

/**
 * 技能卡片组件
 * 显示单个技能的摘要信息和操作按钮
 */
const SkillCard = ({ 
  skill, 
  viewMode = 'grid', 
  onSelect, 
  onInstall, 
  onUninstall 
}) => {
  // 处理安装/卸载操作
  const handleInstallClick = (e) => {
    e.stopPropagation();
    if (skill.installed) {
      onUninstall(skill.id);
    } else {
      onInstall(skill.id);
    }
  };

  // 处理卡片点击
  const handleCardClick = () => {
    onSelect(skill);
  };

  // 渲染评分星星
  const renderRatingStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;

    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(<span key={i} className="skill-card__star skill-card__star--full">★</span>);
      } else if (i === fullStars && hasHalfStar) {
        stars.push(<span key={i} className="skill-card__star skill-card__star--half">★</span>);
      } else {
        stars.push(<span key={i} className="skill-card__star skill-card__star--empty">★</span>);
      }
    }

    return (
      <div className="skill-card__rating">
        {stars}
        <span className="skill-card__rating-value">{rating.toFixed(1)}</span>
      </div>
    );
  };

  // 渲染标签
  const renderTags = (tags, maxTags = 3) => {
    if (!tags || tags.length === 0) return null;

    const displayedTags = tags.slice(0, maxTags);
    const remainingTags = tags.length - maxTags;

    return (
      <div className="skill-card__tags">
        {displayedTags.map((tag, index) => (
          <span key={index} className="skill-card__tag">
            {tag}
          </span>
        ))}
        {remainingTags > 0 && (
          <span className="skill-card__tag skill-card__tag--more">
            +{remainingTags}
          </span>
        )}
      </div>
    );
  };

  // 网格视图
  if (viewMode === 'grid') {
    return (
      <div 
        className={`skill-card skill-card--grid ${skill.installed ? 'skill-card--installed' : ''}`}
        onClick={handleCardClick}
      >
        {/* 技能图标 */}
        <div className="skill-card__header">
          <div className="skill-card__icon">
            {skill.icon ? (
              <img src={skill.icon} alt={skill.name} />
            ) : (
              <div className="skill-card__icon-placeholder">
                {skill.name.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          
          {/* 安装状态徽章 */}
          {skill.installed && (
            <div className="skill-card__badge skill-card__badge--installed">
              已安装
            </div>
          )}
          
          {/* 热门徽章 */}
          {skill.popular && (
            <div className="skill-card__badge skill-card__badge--popular">
              热门
            </div>
          )}
        </div>

        {/* 技能信息 */}
        <div className="skill-card__content">
          <h3 className="skill-card__title" title={skill.name}>
            {skill.name}
          </h3>
          
          <p className="skill-card__description" title={skill.description}>
            {skill.description}
          </p>
          
          {/* 技能分类 */}
          {skill.category && (
            <div className="skill-card__category">
              <span className="skill-card__category-label">{skill.category}</span>
            </div>
          )}
          
          {/* 评分和下载量 */}
          <div className="skill-card__stats">
            {skill.rating && renderRatingStars(skill.rating)}
            {skill.downloads && (
              <span className="skill-card__downloads">
                {skill.downloads >= 1000 
                  ? `${(skill.downloads / 1000).toFixed(1)}k` 
                  : skill.downloads
                } 次下载
              </span>
            )}
          </div>
          
          {/* 标签 */}
          {renderTags(skill.tags)}
        </div>

        {/* 操作按钮 */}
        <div className="skill-card__actions">
          <button 
            className={`skill-card__install-button ${skill.installed ? 'skill-card__install-button--uninstall' : 'skill-card__install-button--install'}`}
            onClick={handleInstallClick}
          >
            {skill.installed ? '卸载' : '安装'}
          </button>
          
          <button 
            className="skill-card__details-button"
            onClick={handleCardClick}
          >
            详情
          </button>
        </div>
      </div>
    );
  }

  // 列表视图
  return (
    <div 
      className={`skill-card skill-card--list ${skill.installed ? 'skill-card--installed' : ''}`}
      onClick={handleCardClick}
    >
      <div className="skill-card__list-content">
        {/* 左侧：图标和基本信息 */}
        <div className="skill-card__list-left">
          <div className="skill-card__icon skill-card__icon--list">
            {skill.icon ? (
              <img src={skill.icon} alt={skill.name} />
            ) : (
              <div className="skill-card__icon-placeholder">
                {skill.name.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          
          <div className="skill-card__list-info">
            <h3 className="skill-card__title" title={skill.name}>
              {skill.name}
              {skill.installed && (
                <span className="skill-card__installed-badge">已安装</span>
              )}
              {skill.popular && (
                <span className="skill-card__popular-badge">热门</span>
              )}
            </h3>
            
            <p className="skill-card__description" title={skill.description}>
              {skill.description}
            </p>
            
            {/* 分类和标签 */}
            <div className="skill-card__list-meta">
              {skill.category && (
                <span className="skill-card__category">{skill.category}</span>
              )}
              {renderTags(skill.tags, 2)}
            </div>
          </div>
        </div>

        {/* 右侧：统计信息和操作 */}
        <div className="skill-card__list-right">
          {/* 统计信息 */}
          <div className="skill-card__list-stats">
            {skill.rating && (
              <div className="skill-card__rating-container">
                {renderRatingStars(skill.rating)}
              </div>
            )}
            
            {skill.downloads && (
              <div className="skill-card__downloads-container">
                <span className="skill-card__downloads-count">
                  {skill.downloads >= 1000 
                    ? `${(skill.downloads / 1000).toFixed(1)}k` 
                    : skill.downloads
                  }
                </span>
                <span className="skill-card__downloads-label">下载</span>
              </div>
            )}
            
            {skill.lastUpdated && (
              <div className="skill-card__update-container">
                <span className="skill-card__update-label">
                  更新于 {new Date(skill.lastUpdated).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>

          {/* 操作按钮 */}
          <div className="skill-card__list-actions">
            <button 
              className={`skill-card__install-button ${skill.installed ? 'skill-card__install-button--uninstall' : 'skill-card__install-button--install'}`}
              onClick={handleInstallClick}
            >
              {skill.installed ? '卸载' : '安装'}
            </button>
            
            <button 
              className="skill-card__details-button"
              onClick={handleCardClick}
            >
              查看详情
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillCard;