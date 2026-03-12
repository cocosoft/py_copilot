/**
 * 知识库布局组件
 * 
 * 提供知识库模块的整体布局结构，包括侧边栏、顶部工具栏和内容区域
 */

import React, { useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  FiFileText, 
  FiShare2, 
  FiZap, 
  FiSearch, 
  FiSettings,
  FiMenu,
  FiChevronLeft
} from 'react-icons/fi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import KnowledgeBaseSidebar from '../../components/Knowledge/KnowledgeBaseSidebar';
import SmartSearch from '../../components/Knowledge/SmartSearch/SmartSearch';
import './styles.css';

/**
 * Tab 配置
 */
const TABS = [
  { key: 'documents', label: '文档管理', icon: FiFileText, path: '/knowledge/documents' },
  { key: 'graph', label: '知识图谱', icon: FiShare2, path: '/knowledge/graph' },
  { key: 'vectorization', label: '向量化', icon: FiZap, path: '/knowledge/vectorization' },
  { key: 'search', label: '高级搜索', icon: FiSearch, path: '/knowledge/search' },
  { key: 'settings', label: '设置', icon: FiSettings, path: '/knowledge/settings' },
];

/**
 * 知识库布局组件
 */
const KnowledgeLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const { 
    activeTab, 
    setActiveTab, 
    sidebarCollapsed, 
    setSidebarCollapsed,
    currentKnowledgeBase,
  } = useKnowledgeStore();

  // 根据 URL 同步 tab 状态
  useEffect(() => {
    const path = location.pathname.split('/').pop();
    const validTabs = TABS.map(t => t.key);
    if (path && validTabs.includes(path) && path !== activeTab) {
      setActiveTab(path);
    }
  }, [location, activeTab, setActiveTab]);

  /**
   * 处理 Tab 切换
   */
  const handleTabChange = (tab) => {
    setActiveTab(tab.key);
    navigate(tab.path);
  };

  /**
   * 切换侧边栏折叠状态
   */
  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <div className={`knowledge-layout ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      {/* 左侧边栏 - 知识库列表 */}
      <aside className="knowledge-sidebar">
        <div className="knowledge-sidebar-header">
          <button 
            className="sidebar-toggle-btn"
            onClick={toggleSidebar}
            title={sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'}
          >
            {sidebarCollapsed ? <FiMenu /> : <FiChevronLeft />}
          </button>
          {!sidebarCollapsed && <h2 className="sidebar-title">知识库</h2>}
        </div>
        
        <div className="knowledge-sidebar-content">
          <KnowledgeBaseSidebar collapsed={sidebarCollapsed} />
        </div>
      </aside>

      {/* 主内容区域 */}
      <div className="knowledge-main">
        {/* 顶部工具栏 */}
        <header className="knowledge-header">
          {/* 左侧：Tab 导航 */}
          <nav className="knowledge-tabs">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.key;
              
              return (
                <button
                  key={tab.key}
                  className={`knowledge-tab ${isActive ? 'active' : ''}`}
                  onClick={() => handleTabChange(tab)}
                >
                  <Icon className="tab-icon" />
                  <span className="tab-label">{tab.label}</span>
                  {isActive && (
                    <motion.div
                      className="tab-indicator"
                      layoutId="activeTab"
                      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                    />
                  )}
                </button>
              );
            })}
          </nav>

          {/* 右侧：搜索 */}
          <div className="knowledge-header-actions">
            <SmartSearch />
          </div>
        </header>

        {/* 内容区域 */}
        <main className="knowledge-content">
          {currentKnowledgeBase ? (
            <Outlet />
          ) : (
            <div className="knowledge-empty-state">
              <div className="empty-state-icon">📚</div>
              <h3>请选择一个知识库</h3>
              <p>从左侧边栏选择一个知识库开始管理文档</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default KnowledgeLayout;
