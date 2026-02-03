import React, { useState } from 'react';
import TopicSidebar from './TopicSidebar';
import './LeftSidebar.css';

const LeftSidebar = ({
  conversationId,
  activeTopic,
  onTopicSelect,
  onTopicCreate,
  onTopicDelete,
  refreshFlag,
  onCollapseChange,
  models,
  selectedModel,
  onModelChange,
  collapsed
}) => {
  const [activeTab, setActiveTab] = useState('topics'); // 'topics' 或 'settings'

  return (
    <div className={`left-sidebar ${collapsed ? 'collapsed' : ''}`}>
      {!collapsed && (
        <div className="sidebar-tabs">
          <button
            className={`sidebar-tab ${activeTab === 'topics' ? 'active' : ''}`}
            onClick={() => setActiveTab('topics')}
            title="话题管理"
          >
            📋 话题
          </button>
          <button
            className={`sidebar-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
            title="设置"
          >
            ⚙️ 设置
          </button>
        </div>
      )}

      <div className="sidebar-content">
        {!collapsed && activeTab === 'topics' && (
          <TopicSidebar
            conversationId={conversationId}
            activeTopic={activeTopic}
            onTopicSelect={onTopicSelect}
            onTopicCreate={onTopicCreate}
            onTopicDelete={onTopicDelete}
            refreshFlag={refreshFlag}
            onCollapseChange={onCollapseChange}
          />
        )}

        {!collapsed && activeTab === 'settings' && (
          <div className="settings-panel">
          </div>
        )}
      </div>
    </div>
  );
};

export default LeftSidebar;