import React from 'react';
import SkillBadge from './SkillBadge';
import './SkillManagement.css';

function SkillCard({ skill, viewMode, onView, onToggleEnable }) {
  const statusLabels = {
    enabled: '已启用',
    disabled: '已禁用',
    installed: '已安装',
    updating: '更新中',
  };

  const statusColors = {
    enabled: 'success',
    disabled: 'default',
    installed: 'info',
    updating: 'warning',
  };

  return (
    <div className={`skill-card ${viewMode}`} onClick={onView}>
      <div className="skill-card-header">
        <h3 className="skill-name">{skill.name}</h3>
        <SkillBadge 
          status={skill.status} 
          label={statusLabels[skill.status]}
          color={statusColors[skill.status]}
        />
      </div>
      
      <p className="skill-description">{skill.description}</p>
      
      <div className="skill-meta">
        <span className="skill-version">v{skill.version}</span>
        {skill.license && (
          <span className="skill-license">{skill.license}</span>
        )}
      </div>
      
      {skill.tags && skill.tags.length > 0 && (
        <div className="skill-tags">
          {skill.tags.slice(0, 3).map(tag => (
            <span key={tag} className="skill-tag">{tag}</span>
          ))}
          {skill.tags.length > 3 && (
            <span className="skill-tag-more">+{skill.tags.length - 3}</span>
          )}
        </div>
      )}
      
      <div className="skill-card-footer">
        <button
          className={`skill-action-btn ${skill.status === 'enabled' ? 'enabled' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            onToggleEnable();
          }}
        >
          {skill.status === 'enabled' ? '禁用' : '启用'}
        </button>
        <span className="skill-usage">
          使用 {skill.usage_count || 0} 次
        </span>
      </div>
    </div>
  );
}

export default SkillCard;
