import React, { useState } from 'react';
import ModelCapabilityManagement from './ModelCapabilityManagement';
import ModelCapabilityAssociation from './ModelCapabilityAssociation';
import '../../styles/CapabilityManagementTabs.css';

const CapabilityManagementTabs = () => {
  const [activeSubTab, setActiveSubTab] = useState('management'); // 'management' 或 'association'

  const handleSubTabChange = (subTab) => {
    setActiveSubTab(subTab);
  };

  return (
    <div className="capability-management-tabs">
      {/* 子Tab导航 */}
      <div className="sub-tab-navigation">
        <button 
          className={`sub-tab-button ${activeSubTab === 'management' ? 'active' : ''}`}
          onClick={() => handleSubTabChange('management')}
        >
          能力管理
        </button>
        <button 
          className={`sub-tab-button ${activeSubTab === 'association' ? 'active' : ''}`}
          onClick={() => handleSubTabChange('association')}
        >
          模型能力关联
        </button>
      </div>
      
      {/* 子Tab内容区域 */}
      <div className="sub-tab-content">
        {activeSubTab === 'management' && (
          <ModelCapabilityManagement />
        )}
        {activeSubTab === 'association' && (
          <ModelCapabilityAssociation />
        )}
      </div>
    </div>
  );
};

export default CapabilityManagementTabs;