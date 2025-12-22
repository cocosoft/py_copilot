import React, { useState, useEffect } from 'react';
import { request } from '../utils/apiUtils';
import './settings.css';
import IntegratedModelManagement from '../components/ModelManagement/IntegratedModelManagement';
import ParameterManagementMain from '../components/ModelManagement/ParameterManagementMain';
import Agent from './Agent';
import Knowledge from './Knowledge';
import Workflow from './Workflow';
import Tool from './Tool';


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
  
  // 搜索设置的状态（仅保留基础配置）
  const [defaultSearchEngine, setDefaultSearchEngine] = useState('google');
  const [safeSearch, setSafeSearch] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // 切换侧边栏展开/收缩状态
  const toggleSidebar = () => {
    setSidebarExpanded(!sidebarExpanded);
  };

  // 加载搜索设置
  const loadSearchSettings = async () => {
    setIsLoading(true);
    try {
      // 这里只需要使用/v1/search/settings路径，因为request函数会自动添加API_BASE_URL（即/api）
      // 所以实际请求的URL是/api/v1/search/settings，与后端的路由匹配
      const data = await request('/v1/search/settings', { method: 'GET' });
      setDefaultSearchEngine(data.default_search_engine);
      setSafeSearch(data.safe_search);
    } catch (error) {
      console.error('加载搜索设置失败:', error);
      // 加载失败时使用默认值
      setDefaultSearchEngine('google');
      setSafeSearch(true);
    } finally {
      setIsLoading(false);
    }
  };

  // 保存搜索设置
  const saveSearchSettings = async () => {
    setIsSaving(true);
    try {
      // 这里只需要使用/v1/search/settings路径，因为request函数会自动添加API_BASE_URL（即/api）
      // 所以实际请求的URL是/api/v1/search/settings，与后端的路由匹配
      await request('/v1/search/settings', {
        method: 'PUT',
        data: {
          default_search_engine: defaultSearchEngine,
          safe_search: safeSearch
        }
      });
      alert('搜索设置已保存');
    } catch (error) {
      console.error('保存搜索设置失败:', error);
      alert('保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  // 页面加载时获取搜索设置
  useEffect(() => {
    if (activeSection === 'search') {
      loadSearchSettings();
    }
  }, [activeSection]);

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
              <p>配置联网搜索的基础选项</p>
            </div>
            
            {isLoading ? (
              <div className="loading">加载中...</div>
            ) : (
              <div className="search-section">
                <div className="setting-card">
                  <div className="setting-item">
                    <label htmlFor="defaultSearchEngine">默认搜索引擎</label>
                    <select 
                      id="defaultSearchEngine"
                      className="search-select"
                      value={defaultSearchEngine}
                      onChange={(e) => setDefaultSearchEngine(e.target.value)}
                    >
                      <option value="google">Google</option>
                      <option value="bing">Bing</option>
                      <option value="baidu">百度</option>
                    </select>
                  </div>
                  
                  <div className="setting-item">
                    <label htmlFor="safeSearch">启用安全搜索</label>
                    <input 
                      type="checkbox" 
                      id="safeSearch" 
                      checked={safeSearch}
                      onChange={(e) => setSafeSearch(e.target.checked)}
                    />
                  </div>
                  
                  <div className="setting-actions">
                    <button 
                      className="save-btn" 
                      onClick={saveSearchSettings}
                      disabled={isSaving}
                    >
                      {isSaving ? '保存中...' : '保存设置'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
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