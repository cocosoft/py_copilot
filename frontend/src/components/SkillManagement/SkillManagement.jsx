import React, { useState } from 'react';
import SkillList from './SkillList';
import SkillMarket from '../SkillMarket/SkillMarket';
import './SkillManagement.css';

/**
 * 技能管理组件 - 作为设置页面中技能管理的主要入口
 * 包含已安装技能管理和技能市场发现功能
 */
function SkillManagement() {
  const [activeTab, setActiveTab] = useState('installed'); // 'installed' | 'market'

  return (
    <div className="skill-management">
      <div className="skill-management-header">
        <h2>技能管理</h2>
        <p>管理系统中的技能和发现新技能</p>
      </div>
      
      {/* 标签页导航 */}
      <div className="skill-management-tabs">
        <button 
          className={`skill-management-tab ${activeTab === 'installed' ? 'active' : ''}`}
          onClick={() => setActiveTab('installed')}
        >
          <span className="tab-icon">📋</span>
          <span className="tab-text">已安装技能</span>
        </button>
        <button 
          className={`skill-management-tab ${activeTab === 'market' ? 'active' : ''}`}
          onClick={() => setActiveTab('market')}
        >
          <span className="tab-icon">🛒</span>
          <span className="tab-text">技能市场</span>
        </button>
      </div>
      
      <div className="skill-management-content">
        {activeTab === 'installed' ? <SkillList /> : <SkillMarket />}
      </div>
    </div>
  );
}

export default SkillManagement;