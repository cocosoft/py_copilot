import React, { useState } from 'react';
import SkillBadge from './SkillBadge';
import SkillDependencyManagement from './SkillDependencyManagement';
import SkillExecutionFlow from './SkillExecutionFlow';
import SkillArtifactsViewer from './SkillArtifactsViewer';
import './SkillManagement.css';

function SkillDetailModal({ skill, onClose, onToggleEnable }) {
  const [activeTab, setActiveTab] = useState('details');
  const statusLabels = {
    enabled: '已启用',
    disabled: '已禁用',
    installed: '已安装',
    updating: '更新中',
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="skill-modal-backdrop" onClick={handleBackdropClick}>
      <div className="skill-modal">
        <div className="skill-modal-header">
          <h2>{skill.name}</h2>
          <button className="close-btn" onClick={onClose}>
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        
        <div className="skill-modal-body">
          {/* 标签页导航 */}
          <div className="skill-tabs">
            <button 
              className={`tab-button ${activeTab === 'details' ? 'active' : ''}`}
              onClick={() => setActiveTab('details')}
            >
              基本信息
            </button>
            <button 
              className={`tab-button ${activeTab === 'dependencies' ? 'active' : ''}`}
              onClick={() => setActiveTab('dependencies')}
            >
              依赖管理
            </button>
            <button 
              className={`tab-button ${activeTab === 'execution' ? 'active' : ''}`}
              onClick={() => setActiveTab('execution')}
            >
              执行流程
            </button>
            <button 
              className={`tab-button ${activeTab === 'artifacts' ? 'active' : ''}`}
              onClick={() => setActiveTab('artifacts')}
            >
              执行结果
            </button>
          </div>

          {/* 标签页内容 */}
          <div className="tab-content">
            {activeTab === 'details' && (
              <div className="skill-detail-content">
                <div className="skill-detail-section">
                  <div className="skill-detail-row">
                    <span className="detail-label">状态:</span>
                    <SkillBadge 
                      status={skill.status} 
                      label={statusLabels[skill.status]}
                    />
                  </div>
                  <div className="skill-detail-row">
                    <span className="detail-label">版本:</span>
                    <span>{skill.version}</span>
                  </div>
                  {skill.license && (
                    <div className="skill-detail-row">
                      <span className="detail-label">许可证:</span>
                      <span>{skill.license}</span>
                    </div>
                  )}
                  <div className="skill-detail-row">
                    <span className="detail-label">使用次数:</span>
                    <span>{skill.usage_count || 0}</span>
                  </div>
                  <div className="skill-detail-row">
                    <span className="detail-label">最后使用:</span>
                    <span>
                      {skill.last_used_at 
                        ? new Date(skill.last_used_at).toLocaleString()
                        : '从未使用'
                      }
                    </span>
                  </div>
                </div>
                
                <div className="skill-detail-section">
                  <h3>描述</h3>
                  <p className="skill-description-full">{skill.description}</p>
                </div>
                
                {skill.tags && skill.tags.length > 0 && (
                  <div className="skill-detail-section">
                    <h3>标签</h3>
                    <div className="skill-tags-list">
                      {skill.tags.map(tag => (
                        <span key={tag} className="skill-tag">{tag}</span>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="skill-detail-section">
                  <h3>资源文件</h3>
                  {skill.resources && Object.keys(skill.resources).length > 0 ? (
                    <ul className="skill-resources-list">
                      {Object.entries(skill.resources).map(([path, info]) => (
                        <li key={path}>
                          <span className="resource-path">{path}</span>
                          <span className="resource-type">{info.type}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="no-resources">无资源文件</p>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'dependencies' && (
              <div className="skill-detail-content">
                <SkillDependencyManagement 
                  skillId={skill.id} 
                  skillName={skill.name}
                />
              </div>
            )}

            {activeTab === 'execution' && (
              <div className="skill-detail-content">
                <SkillExecutionFlow 
                  skillId={skill.id} 
                  skillName={skill.name}
                />
              </div>
            )}

            {activeTab === 'artifacts' && (
              <div className="skill-detail-content">
                <SkillArtifactsViewer 
                  skillId={skill.id}
                />
              </div>
            )}
          </div>
        </div>
        
        <div className="skill-modal-footer">
          <button
            className="toggle-btn"
            onClick={onToggleEnable}
          >
            {skill.status === 'enabled' ? '禁用技能' : '启用技能'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SkillDetailModal;
