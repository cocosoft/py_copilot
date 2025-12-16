import React, { useState, useEffect } from 'react';
import './settings.css';
import IntegratedModelManagement from '../components/ModelManagement/IntegratedModelManagement';
import ParameterManagementMain from '../components/ModelManagement/ParameterManagementMain';
import Agent from './Agent';
import Knowledge from './Knowledge';
import Workflow from './Workflow';
import Tool from './Tool';
import About from './About';

const Settings = () => {
  // 状态管理当前选中的二级菜单
  const [activeSection, setActiveSection] = useState('model');
  
  // 新增：控制侧边栏是否展开的状态
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  
  // 监听URL的hash变化，当hash为"#personal"或"#help"时，自动设置对应的activeSection
  useEffect(() => {
    const hash = window.location.hash;
    if (hash === '#personal') {
      setActiveSection('personal');
    } else if (hash === '#help') {
      setActiveSection('help');
    }
    
    // 监听hash变化事件
    const handleHashChange = () => {
      const newHash = window.location.hash;
      if (newHash === '#personal') {
        setActiveSection('personal');
      } else if (newHash === '#help') {
        setActiveSection('help');
      }
    };
    
    window.addEventListener('hashchange', handleHashChange);
    
    // 清理事件监听器
    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);
  
  // 搜索设置的状态
  const [searchEngine, setSearchEngine] = useState('google');
  const [safeSearch, setSafeSearch] = useState(true);
  const [strictFilter, setStrictFilter] = useState(false);
  const [includeAdult, setIncludeAdult] = useState(false);
  const [saveHistory, setSaveHistory] = useState(true);
  const [historyDuration, setHistoryDuration] = useState('90');

  // 切换侧边栏展开/收缩状态
  const toggleSidebar = () => {
    setSidebarExpanded(!sidebarExpanded);
  };

  // 根据选中的二级菜单渲染对应内容
  const renderContent = () => {
    switch (activeSection) {
      case 'model':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>模型管理</h2>
              <p>管理AI供应商和模型配置，含模型分类与模型能力管理。</p>
            </div>
            
            <div className="model-management-container">
              <IntegratedModelManagement />
            </div>
          </div>
        );
        
      case 'agents':
        return (
          <div className="settings-content">
            <Agent />
          </div>
        );
        
      case 'knowledge':
        return (
          <div className="settings-content">
            <Knowledge />
          </div>
        );
        
      case 'workflow':
        return (
          <div className="settings-content">
            <Workflow />
          </div>
        );
        
      case 'tool':
        return (
          <div className="settings-content">
            <Tool />
          </div>
        );
      
      case 'parameters':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>参数管理</h2>
              <p>管理系统各层级的参数配置</p>
            </div>
            <div className="parameters-management-container">
              <ParameterManagementMain 
                selectedSupplier={null} 
                onBack={() => setActiveSection('model')} 
              />
            </div>
          </div>
        );
      
      case 'search':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>搜索管理</h2>
              <p>配置搜索偏好和搜索引擎</p>
            </div>
            
            <div className="search-section">
              <div className="setting-card">
                <div className="setting-header">
                  <h3>默认搜索引擎</h3>
                  <p>选择默认使用的搜索引擎</p>
                </div>
                <div className="setting-control">
                  <select 
                    className="search-select"
                    value={searchEngine}
                    onChange={(e) => setSearchEngine(e.target.value)}
                  >
                    <option value="google">Google</option>
                    <option value="bing">Bing</option>
                    <option value="duckduckgo">DuckDuckGo</option>
                    <option value="baidu">百度</option>
                  </select>
                </div>
              </div>
              
              <div className="setting-card">
                <div className="setting-header">
                  <h3>搜索过滤设置</h3>
                  <p>配置搜索结果的过滤选项</p>
                </div>
                <div className="filter-options">
                  <div className="filter-item">
                    <input 
                      type="checkbox" 
                      id="safe-search" 
                      checked={safeSearch}
                      onChange={(e) => setSafeSearch(e.target.checked)}
                    />
                    <label htmlFor="safe-search">启用安全搜索</label>
                  </div>
                  <div className="filter-item">
                    <input 
                      type="checkbox" 
                      id="strict-filter" 
                      checked={strictFilter}
                      onChange={(e) => setStrictFilter(e.target.checked)}
                    />
                    <label htmlFor="strict-filter">严格内容过滤</label>
                  </div>
                  <div className="filter-item">
                    <input 
                      type="checkbox" 
                      id="include-adult" 
                      checked={includeAdult}
                      onChange={(e) => setIncludeAdult(e.target.checked)}
                    />
                    <label htmlFor="include-adult">包含成人内容（需确认）</label>
                  </div>
                </div>
              </div>
              
              <div className="setting-card">
                <div className="setting-header">
                  <h3>搜索历史</h3>
                  <p>管理您的搜索历史记录</p>
                </div>
                <div className="history-settings">
                  <div className="history-option">
                    <input 
                      type="checkbox" 
                      id="save-history" 
                      checked={saveHistory}
                      onChange={(e) => setSaveHistory(e.target.checked)}
                    />
                    <label htmlFor="save-history">保存搜索历史</label>
                  </div>
                  <div className="history-option">
                    <select 
                      className="history-duration"
                      value={historyDuration}
                      onChange={(e) => setHistoryDuration(e.target.value)}
                    >
                      <option value="30">保留30天</option>
                      <option value="90">保留90天</option>
                      <option value="180">保留180天</option>
                      <option value="365">保留1年</option>
                      <option value="forever">永久保留</option>
                    </select>
                  </div>
                  <button className="clear-history-btn">清空搜索历史</button>
                </div>
              </div>
            </div>
          </div>
        );
      
      case 'personal':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>个人中心</h2>
              <p>管理您的账户、通知、隐私和账单设置</p>
            </div>
            <div className="personal-center-container">
              <div className="personal-section">
                <h3>账户设置</h3>
                <p className="placeholder-text">账户设置内容将在这里显示...</p>
              </div>
              <div className="personal-section">
                <h3>通知设置</h3>
                <p className="placeholder-text">通知设置内容将在这里显示...</p>
              </div>
              <div className="personal-section">
                <h3>隐私设置</h3>
                <p className="placeholder-text">隐私设置内容将在这里显示...</p>
              </div>
              <div className="personal-section">
                <h3>账单管理</h3>
                <p className="placeholder-text">账单管理内容将在这里显示...</p>
              </div>
            </div>
          </div>
        );
        
      case 'help':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>帮助中心</h2>
              <p>获取Py Copilot的使用帮助和常见问题解答</p>
            </div>
            <p className="placeholder-text">帮助中心内容将在这里显示...</p>
          </div>
        );
        
      case 'about':
        return (
          <About />
        );
        
      default:
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>设置</h2>
              <p>选择左侧菜单查看相应设置选项</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1>Py Copilot 设置</h1>
        <p>管理 Py Copilot 应用的各种配置选项</p>
      </div>
      
      <div className="settings-content-wrapper">
        {/* 左侧二级菜单 */}
        <div className={`settings-sidebar ${sidebarExpanded ? 'expanded' : 'collapsed'}`}>
          <nav className="settings-nav">
            <button 
              className={`nav-item ${activeSection === 'model' ? 'active' : ''}`}
              onClick={() => setActiveSection('model')}
            >
              <span className="nav-icon">🧠</span>
              <span className="nav-text">模型管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'agents' ? 'active' : ''}`}
              onClick={() => setActiveSection('agents')}
            >
              <span className="nav-icon">🤖</span>
              <span className="nav-text">智能体管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'knowledge' ? 'active' : ''}`}
              onClick={() => setActiveSection('knowledge')}
            >
              <span className="nav-icon">📚</span>
              <span className="nav-text">知识库管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'workflow' ? 'active' : ''}`}
              onClick={() => setActiveSection('workflow')}
            >
              <span className="nav-icon">🔄</span>
              <span className="nav-text">工作流管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'parameters' ? 'active' : ''}`}
              onClick={() => setActiveSection('parameters')}
            >
              <span className="nav-icon">⚙️</span>
              <span className="nav-text">参数管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'tool' ? 'active' : ''}`}
              onClick={() => setActiveSection('tool')}
            >
              <span className="nav-icon">🔧</span>
              <span className="nav-text">工具管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'search' ? 'active' : ''}`}
              onClick={() => setActiveSection('search')}
            >
              <span className="nav-icon">🔍</span>
              <span className="nav-text">搜索管理</span>
            </button>
            
            
            
            
            
            <button 
              className={`nav-item ${activeSection === 'about' ? 'active' : ''}`}
              onClick={() => setActiveSection('about')}
            >
              <span className="nav-icon">ℹ️</span>
              <span className="nav-text">关于我们</span>
            </button>
              

        </nav>
      </div>
        
        {/* 悬浮按钮 */}
        <button 
          className="sidebar-toggle-btn"
          onClick={toggleSidebar}
          title={sidebarExpanded ? "收缩导航栏" : "展开导航栏"}
        >
          {sidebarExpanded ? "◀" : "▶"}
        </button>
        
        {/* 右侧内容区域 */}
        <div className={`settings-main ${sidebarExpanded ? '' : 'expanded'}`}>
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default Settings;