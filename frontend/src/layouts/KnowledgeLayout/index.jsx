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
  FiChevronLeft,
  FiTag,
  FiLink,
  FiRefreshCw,
  FiPieChart
} from 'react-icons/fi';
import useKnowledgeStore from '../../stores/knowledgeStore';
import KnowledgeBaseSidebar from '../../components/Knowledge/KnowledgeBaseSidebar';
import SmartSearch from '../../components/Knowledge/SmartSearch/SmartSearch';
import './styles.css';

/**
 * Tab 配置 - 按照优化方案中的顺序
 * 文档管理（包含向量化）- 实体管理（包含实体识别和实体关系）- 知识图谱 - 高级功能（包含重排序、高级搜索、数据仪表盘）- 设置
 */
const TABS = [
  { key: 'documents', label: '文档管理', icon: FiFileText, path: '/knowledge/documents' },
  { key: 'entity-management', label: '实体管理', icon: FiTag, path: '/knowledge/entity-management' },
  { key: 'knowledge-graph', label: '知识图谱', icon: FiShare2, path: '/knowledge/knowledge-graph' },
  { key: 'advanced', label: '高级功能', icon: FiZap, path: '/knowledge/search' },
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
    let tabKey = path;
    
    // 高级功能相关页面都设置为 advanced tab
    if (['search', 'reranking', 'dashboard'].includes(path)) {
      tabKey = 'advanced';
    }
    
    const validTabs = TABS.map(t => t.key);
    if (tabKey && validTabs.includes(tabKey) && tabKey !== activeTab) {
      setActiveTab(tabKey);
    }
  }, [location, activeTab, setActiveTab]);

  /**
   * 处理 Tab 切换
   */
  const handleTabChange = (tab) => {
    setActiveTab(tab.key);
    if (tab.key === 'advanced') {
      // 高级功能默认导航到高级搜索页面
      navigate('/knowledge/search');
    } else {
      navigate(tab.path);
    }
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
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default KnowledgeLayout;
