import React, { useState } from 'react';
import TopicSidebar from './TopicSidebar';
import './LeftSidebar.css';

const LeftSidebar = ({
  conversationId,
  activeTopic,
  setActiveTopic,
  refreshFlag,
  setRefreshFlag,
  collapsed,
  setCollapsed
}) => {
  const [activeTab, setActiveTab] = useState('topics');

  return (
    <div className={`left-sidebar ${collapsed ? 'collapsed' : ''}`}>
      {!collapsed && (
        <div className="sidebar-tabs">
          <button 
            className={`sidebar-tab ${activeTab === 'topics' ? 'active' : ''}`}
            onClick={() => setActiveTab('topics')}
          >
            话题
          </button>
          <button 
            className={`sidebar-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            设置
          </button>
        </div>
      )}
      
      <div className="sidebar-content">
        {activeTab === 'topics' && (
          <TopicSidebar
            conversationId={conversationId}
            activeTopic={activeTopic}
            setActiveTopic={setActiveTopic}
            refreshFlag={refreshFlag}
            setRefreshFlag={setRefreshFlag}
            collapsed={collapsed}
            setCollapsed={setCollapsed}
          />
        )}
        
        {activeTab === 'settings' && (
          <div className="settings-content">
            <div className="settings-header">
              <h3>设置</h3>
            </div>
            <div className="settings-placeholder">
              <p>设置内容将在下一个对话中讨论</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LeftSidebar;