import React, { useState } from 'react';

/**
 * 技能详情组件
 * 显示技能的详细信息和操作选项
 */
const SkillDetails = ({ skill, onClose, onInstall, onUninstall }) => {
  const [activeTab, setActiveTab] = useState('overview');

  // 处理安装/卸载操作
  const handleInstallClick = () => {
    if (skill.installed) {
      onUninstall(skill.id);
    } else {
      onInstall(skill.id);
    }
  };

  // 渲染评分星星
  const renderRatingStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;

    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(<span key={i} className="skill-details__star skill-details__star--full">★</span>);
      } else if (i === fullStars && hasHalfStar) {
        stars.push(<span key={i} className="skill-details__star skill-details__star--half">★</span>);
      } else {
        stars.push(<span key={i} className="skill-details__star skill-details__star--empty">★</span>);
      }
    }

    return (
      <div className="skill-details__rating">
        {stars}
        <span className="skill-details__rating-value">{rating.toFixed(1)}</span>
        <span className="skill-details__rating-count">({skill.reviewCount} 条评价)</span>
      </div>
    );
  };

  // 渲染统计信息
  const renderStats = () => (
    <div className="skill-details__stats">
      <div className="skill-details__stat">
        <span className="skill-details__stat-value">
          {skill.downloads >= 1000 
            ? `${(skill.downloads / 1000).toFixed(1)}k` 
            : skill.downloads
          }
        </span>
        <span className="skill-details__stat-label">下载次数</span>
      </div>
      
      <div className="skill-details__stat">
        <span className="skill-details__stat-value">{skill.version}</span>
        <span className="skill-details__stat-label">版本</span>
      </div>
      
      <div className="skill-details__stat">
        <span className="skill-details__stat-value">
          {new Date(skill.lastUpdated).toLocaleDateString()}
        </span>
        <span className="skill-details__stat-label">最后更新</span>
      </div>
      
      <div className="skill-details__stat">
        <span className="skill-details__stat-value">{skill.size}</span>
        <span className="skill-details__stat-label">大小</span>
      </div>
    </div>
  );

  // 渲染标签
  const renderTags = () => (
    <div className="skill-details__tags">
      {skill.tags?.map((tag, index) => (
        <span key={index} className="skill-details__tag">
          {tag}
        </span>
      ))}
    </div>
  );

  // 渲染依赖项
  const renderDependencies = () => (
    <div className="skill-details__dependencies">
      <h4 className="skill-details__dependencies-title">依赖项</h4>
      {skill.dependencies && skill.dependencies.length > 0 ? (
        <ul className="skill-details__dependencies-list">
          {skill.dependencies.map((dep, index) => (
            <li key={index} className="skill-details__dependency">
              <span className="skill-details__dependency-name">{dep.name}</span>
              <span className="skill-details__dependency-version">{dep.version}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="skill-details__no-dependencies">无外部依赖</p>
      )}
    </div>
  );

  // 渲染使用示例
  const renderExamples = () => (
    <div className="skill-details__examples">
      <h4 className="skill-details__examples-title">使用示例</h4>
      {skill.examples?.map((example, index) => (
        <div key={index} className="skill-details__example">
          <h5 className="skill-details__example-title">{example.title}</h5>
          <p className="skill-details__example-description">{example.description}</p>
          <pre className="skill-details__example-code">
            <code>{example.code}</code>
          </pre>
        </div>
      )) || (
        <p className="skill-details__no-examples">暂无使用示例</p>
      )}
    </div>
  );

  // 渲染评论
  const renderReviews = () => (
    <div className="skill-details__reviews">
      <h4 className="skill-details__reviews-title">用户评价</h4>
      {skill.reviews?.map((review, index) => (
        <div key={index} className="skill-details__review">
          <div className="skill-details__review-header">
            <span className="skill-details__review-author">{review.author}</span>
            <div className="skill-details__review-rating">
              {Array.from({ length: 5 }, (_, i) => (
                <span
                  key={i}
                  className={`skill-details__review-star ${i < review.rating ? 'skill-details__review-star--active' : ''}`}
                >
                  ★
                </span>
              ))}
            </div>
            <span className="skill-details__review-date">
              {new Date(review.date).toLocaleDateString()}
            </span>
          </div>
          <p className="skill-details__review-content">{review.content}</p>
        </div>
      )) || (
        <p className="skill-details__no-reviews">暂无用户评价</p>
      )}
    </div>
  );

  return (
    <div className="skill-details">
      {/* 头部 */}
      <div className="skill-details__header">
        <button 
          className="skill-details__close"
          onClick={onClose}
          title="关闭"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
        </button>
        
        <div className="skill-details__icon">
          {skill.icon ? (
            <img src={skill.icon} alt={skill.name} />
          ) : (
            <div className="skill-details__icon-placeholder">
              {skill.name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
        <div className="skill-details__title-section">
          <h2 className="skill-details__title">{skill.name}</h2>
          <p className="skill-details__author">由 {skill.author} 开发</p>
          
          <div className="skill-details__badges">
            {skill.installed && (
              <span className="skill-details__badge skill-details__badge--installed">
                已安装
              </span>
            )}
            {skill.official && (
              <span className="skill-details__badge skill-details__badge--official">
                官方认证
              </span>
            )}
            {skill.popular && (
              <span className="skill-details__badge skill-details__badge--popular">
                热门技能
              </span>
            )}
          </div>
        </div>
        
        <div className="skill-details__actions">
          <button 
            className={`skill-details__install-button ${skill.installed ? 'skill-details__install-button--uninstall' : 'skill-details__install-button--install'}`}
            onClick={handleInstallClick}
          >
            {skill.installed ? '卸载技能' : '安装技能'}
          </button>
          
          <button className="skill-details__secondary-button">
            添加到收藏
          </button>
        </div>
      </div>

      {/* 主要内容 */}
      <div className="skill-details__content">
        {/* 标签导航 */}
        <div className="skill-details__tabs">
          <button 
            className={`skill-details__tab ${activeTab === 'overview' ? 'skill-details__tab--active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            概览
          </button>
          <button 
            className={`skill-details__tab ${activeTab === 'examples' ? 'skill-details__tab--active' : ''}`}
            onClick={() => setActiveTab('examples')}
          >
            使用示例
          </button>
          <button 
            className={`skill-details__tab ${activeTab === 'reviews' ? 'skill-details__tab--active' : ''}`}
            onClick={() => setActiveTab('reviews')}
          >
            用户评价
          </button>
          <button 
            className={`skill-details__tab ${activeTab === 'details' ? 'skill-details__tab--active' : ''}`}
            onClick={() => setActiveTab('details')}
          >
            详细信息
          </button>
        </div>

        {/* 标签内容 */}
        <div className="skill-details__tab-content">
          {activeTab === 'overview' && (
            <div className="skill-details__overview">
              <div className="skill-details__description">
                <h3>技能描述</h3>
                <p>{skill.description}</p>
              </div>
              
              {skill.longDescription && (
                <div className="skill-details__long-description">
                  <p>{skill.longDescription}</p>
                </div>
              )}
              
              <div className="skill-details__overview-stats">
                {skill.rating && renderRatingStars(skill.rating)}
                {renderStats()}
              </div>
              
              {renderTags()}
              {renderDependencies()}
            </div>
          )}

          {activeTab === 'examples' && (
            <div className="skill-details__examples-tab">
              {renderExamples()}
            </div>
          )}

          {activeTab === 'reviews' && (
            <div className="skill-details__reviews-tab">
              {renderReviews()}
            </div>
          )}

          {activeTab === 'details' && (
            <div className="skill-details__details-tab">
              <div className="skill-details__technical-info">
                <h3>技术信息</h3>
                <dl className="skill-details__info-list">
                  <dt>技能ID</dt>
                  <dd>{skill.id}</dd>
                  
                  <dt>版本</dt>
                  <dd>{skill.version}</dd>
                  
                  <dt>兼容性</dt>
                  <dd>{skill.compatibility || 'Py Copilot 1.0+'}</dd>
                  
                  <dt>许可证</dt>
                  <dd>{skill.license || 'MIT'}</dd>
                  
                  <dt>最后更新</dt>
                  <dd>{new Date(skill.lastUpdated).toLocaleString()}</dd>
                  
                  <dt>文件大小</dt>
                  <dd>{skill.size}</dd>
                </dl>
              </div>
              
              <div className="skill-details__requirements">
                <h3>系统要求</h3>
                <ul className="skill-details__requirements-list">
                  {skill.requirements?.map((req, index) => (
                    <li key={index}>{req}</li>
                  )) || (
                    <li>无特殊系统要求</li>
                  )}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 底部操作栏 */}
      <div className="skill-details__footer">
        <div className="skill-details__footer-actions">
          <button className="skill-details__footer-button">
            分享技能
          </button>
          <button className="skill-details__footer-button">
            报告问题
          </button>
          <button className="skill-details__footer-button">
            查看文档
          </button>
        </div>
        
        <div className="skill-details__footer-info">
          <span>技能ID: {skill.id}</span>
          <span>版本: {skill.version}</span>
        </div>
      </div>
    </div>
  );
};

export default SkillDetails;