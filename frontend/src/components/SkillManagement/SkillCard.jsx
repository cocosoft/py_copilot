import React from 'react';
import SkillBadge from './SkillBadge';
import './SkillManagement.css';

function SkillCard({ skill, viewMode, onView, onToggleEnable, onEdit, onDelete, onExecute, onSelect, isSelected }) {
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
    <div className={`skill-card ${viewMode} ${isSelected ? 'selected' : ''}`} onClick={onView}>
      <div className="skill-card-header">
        {onSelect && (
          <div className="skill-select-checkbox">
            <input 
              type="checkbox" 
              checked={isSelected} 
              onChange={(e) => {
                e.stopPropagation();
                onSelect(skill.id, !isSelected);
              }}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}
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
        <div className="skill-card-actions">
          {onEdit && (
            <button
              className="skill-action-btn edit-btn"
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
              title="编辑技能"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
              </svg>
            </button>
          )}
          
          {onExecute && skill.status === 'enabled' && (
            <button
              className="skill-action-btn execute-btn"
              onClick={(e) => {
                e.stopPropagation();
                onExecute();
              }}
              title="执行技能"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </button>
          )}
          
          <button
            className={`skill-action-btn status-btn ${skill.status === 'enabled' ? 'enabled' : 'disabled'}`}
            onClick={(e) => {
              e.stopPropagation();
              onToggleEnable();
            }}
            title={skill.status === 'enabled' ? '禁用技能' : '启用技能'}
          >
            {skill.status === 'enabled' ? '禁用' : '启用'}
          </button>
          
          {onDelete && (
            <button
              className="skill-action-btn delete-btn"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              title="删除技能"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
            </button>
          )}
        </div>
        <span className="skill-usage">
          使用 {skill.usage_count || 0} 次
        </span>
      </div>
    </div>
  );
}

export default SkillCard;
