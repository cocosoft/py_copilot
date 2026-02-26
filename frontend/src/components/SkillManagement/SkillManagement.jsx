import React, { useState } from 'react';
import SkillList from './SkillList';
import SkillMarket from '../SkillMarket/SkillMarket';
import { useI18n } from '../../hooks/useI18n';
import './SkillManagement.css';

/**
 * 技能管理组件 - 作为设置页面中技能管理的主要入口
 * 包含已安装技能管理和技能市场发现功能
 */
function SkillManagement() {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState('installed'); // 'installed' | 'market'

  return (
    <div className="skill-management">
      <div className="skill-management-header">
        <h2>{t('settings.skillManagement.title')}</h2>
        <p>{t('settings.skillManagement.description')}</p>
      </div>

      {/* 标签页导航 */}
      <div className="skill-management-tabs">
        <button
          className={`skill-management-tab ${activeTab === 'installed' ? 'active' : ''}`}
          onClick={() => setActiveTab('installed')}
        >
          <span className="tab-icon">📋</span>
          <span className="tab-text">{t('settings.skillManagement.tabs.installed')}</span>
        </button>
        <button
          className={`skill-management-tab ${activeTab === 'market' ? 'active' : ''}`}
          onClick={() => setActiveTab('market')}
        >
          <span className="tab-icon">🛒</span>
          <span className="tab-text">{t('settings.skillManagement.tabs.market')}</span>
        </button>
      </div>

      <div className="skill-management-content">
        {activeTab === 'installed' ? <SkillList /> : <SkillMarket />}
      </div>
    </div>
  );
}

export default SkillManagement;