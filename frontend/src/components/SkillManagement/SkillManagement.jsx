import React from 'react';
import SkillList from './SkillList';
import './SkillManagement.css';

/**
 * 技能管理组件 - 作为设置页面中技能管理的主要入口
 * 包含页面标题和技能列表组件
 */
function SkillManagement() {
  return (
    <div className="skill-management">
      <div className="skill-management-header">
        <h2>技能管理</h2>
        <p>管理系统中的技能，包括创建、编辑、启用/禁用和批量操作</p>
      </div>
      
      <div className="skill-management-content">
        <SkillList />
      </div>
    </div>
  );
}

export default SkillManagement;