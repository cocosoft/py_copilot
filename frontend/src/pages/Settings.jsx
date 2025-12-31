import React, { useState, useEffect } from 'react';
import { request } from '../utils/apiUtils';
import './settings.css';
import IntegratedModelManagement from '../components/ModelManagement/IntegratedModelManagement';
import Agent from './Agent';
import Knowledge from './Knowledge';
import Workflow from './Workflow';
import Tool from './Tool';
import ModelSelectDropdown from '../components/ModelManagement/ModelSelectDropdown';


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
  const [isLoadingSearch, setIsLoadingSearch] = useState(false);
  const [isSavingSearch, setIsSavingSearch] = useState(false);

  // 默认模型管理的状态 - 移到组件顶层
  const [globalDefaultModel, setGlobalDefaultModel] = useState('');
  const [sceneDefaultModels, setSceneDefaultModels] = useState({
    chat: '',
    image: '',
    video: '',
    voice: '',
    translate: '',
    knowledge: '',
    workflow: '',
    tool: '',
    search: '',
    mcp: ''
  });
  const [isSavingDefaultModel, setIsSavingDefaultModel] = useState(false);
  const [models, setModels] = useState([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  // 模拟模型数据 - 移到组件顶层
  useEffect(() => {
    setIsLoadingModels(true);
    // 模拟从API获取模型列表
    setTimeout(() => {
      const mockModels = [
        { id: 'model-123', name: '通用聊天模型', supplier: 'openai', type: 'chat' },
        { id: 'model-456', name: '高级推理模型', supplier: 'anthropic', type: 'chat' },
        { id: 'model-789', name: '图像生成模型', supplier: 'openai', type: 'image' },
        { id: 'model-101', name: '视频分析模型', supplier: 'google', type: 'video' },
        { id: 'model-102', name: '语音识别模型', supplier: 'baidu', type: 'voice' },
        { id: 'model-103', name: '多语言翻译模型', supplier: 'microsoft', type: 'translate' },
        { id: 'model-104', name: '知识库模型', supplier: 'openai', type: 'knowledge' },
        { id: 'model-105', name: '工作流模型', supplier: 'anthropic', type: 'workflow' },
        { id: 'model-106', name: '工具调用模型', supplier: 'openai', type: 'tool' },
        { id: 'model-107', name: '搜索增强模型', supplier: 'google', type: 'search' },
        { id: 'model-108', name: 'MCP上下文模型', supplier: 'openai', type: 'mcp' }
      ];
      setModels(mockModels);
      setIsLoadingModels(false);
    }, 500);
  }, []);

  // 保存默认模型设置 - 移到组件顶层
  const handleSaveDefaultModel = () => {
    setIsSavingDefaultModel(true);
    // 模拟保存操作
    setTimeout(() => {
      alert('默认模型设置已保存');
      setIsSavingDefaultModel(false);
    }, 800);
  };

  // 根据场景类型过滤模型 - 移到组件顶层
  const getModelsByType = (type) => {
    return models.filter(model => model.type === type || model.type === 'chat');
  };

  // 切换侧边栏展开/收缩状态
  const toggleSidebar = () => {
    setSidebarExpanded(!sidebarExpanded);
  };

  // 加载搜索设置
  const loadSearchSettings = async () => {
    setIsLoadingSearch(true);
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
      setIsLoadingSearch(false);
    }
  };

  // 保存搜索设置
  const saveSearchSettings = async () => {
    setIsSavingSearch(true);
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
      setIsSavingSearch(false);
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
      
      case 'search':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>搜索管理</h2>
              <p>配置联网搜索的基础选项</p>
            </div>
            
            {isLoadingSearch ? (
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
                      disabled={isSavingSearch}
                    >
                      {isSavingSearch ? '保存中...' : '保存设置'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
        
      case 'defaultModel':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>默认模型</h2>
              <p>设置系统默认使用的AI模型</p>
            </div>
            
            {/* 全局默认模型 */}
            <div className="setting-card">
              <div className="setting-header">
                <h3>全局默认模型</h3>
                <p>系统级别的默认AI模型，作为所有场景的基础默认值</p>
              </div>
              
              <div className="setting-item">
                <label htmlFor="globalDefaultModel">选择全局默认模型</label>
                <ModelSelectDropdown
                  models={models}
                  selectedModel={models.find(model => model.id === globalDefaultModel) || null}
                  onModelSelect={(model) => setGlobalDefaultModel(model.id)}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => {
                    // 根据供应商返回不同的LOGO URL
                    return `/logos/providers/${model.supplier || 'default'}.png`;
                  }}
                />
              </div>
            </div>
            
            {/* 场景默认模型 */}
            <div className="setting-card">
              <div className="setting-header">
                <h3>场景默认模型</h3>
                <p>为特定业务场景设置专属默认模型</p>
              </div>
              
              {/* 聊天场景 */}
              <div className="setting-item">
                <label htmlFor="chatModel">聊天场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('chat')}
                  selectedModel={getModelsByType('chat').find(model => model.id === sceneDefaultModels.chat) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, chat: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 图像场景 */}
              <div className="setting-item">
                <label htmlFor="imageModel">图像场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('image')}
                  selectedModel={getModelsByType('image').find(model => model.id === sceneDefaultModels.image) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, image: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 视频场景 */}
              <div className="setting-item">
                <label htmlFor="videoModel">视频场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('video')}
                  selectedModel={getModelsByType('video').find(model => model.id === sceneDefaultModels.video) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, video: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 语音场景 */}
              <div className="setting-item">
                <label htmlFor="voiceModel">语音场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('voice')}
                  selectedModel={getModelsByType('voice').find(model => model.id === sceneDefaultModels.voice) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, voice: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 翻译场景 */}
              <div className="setting-item">
                <label htmlFor="translateModel">翻译场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('translate')}
                  selectedModel={getModelsByType('translate').find(model => model.id === sceneDefaultModels.translate) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, translate: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 知识库场景 */}
              <div className="setting-item">
                <label htmlFor="knowledgeModel">知识库场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('knowledge')}
                  selectedModel={getModelsByType('knowledge').find(model => model.id === sceneDefaultModels.knowledge) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, knowledge: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 工作流场景 */}
              <div className="setting-item">
                <label htmlFor="workflowModel">工作流场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('workflow')}
                  selectedModel={getModelsByType('workflow').find(model => model.id === sceneDefaultModels.workflow) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, workflow: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 工具调用场景 */}
              <div className="setting-item">
                <label htmlFor="toolModel">工具调用场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('tool')}
                  selectedModel={getModelsByType('tool').find(model => model.id === sceneDefaultModels.tool) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, tool: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 搜索场景 */}
              <div className="setting-item">
                <label htmlFor="searchModel">搜索场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('search')}
                  selectedModel={getModelsByType('search').find(model => model.id === sceneDefaultModels.search) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, search: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* MCP场景 */}
              <div className="setting-item">
                <label htmlFor="mcpModel">MCP场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('mcp')}
                  selectedModel={getModelsByType('mcp').find(model => model.id === sceneDefaultModels.mcp) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, mcp: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              <div className="setting-actions">
                <button 
                  className="save-btn" 
                  onClick={handleSaveDefaultModel}
                  disabled={isSavingDefaultModel || isLoadingModels}
                >
                  {isSavingDefaultModel ? '保存中...' : '保存设置'}
                </button>
              </div>
            </div>
          </div>
        );
        
      case 'system':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>系统功能管理</h2>
              <p>管理系统功能和模块的启用状态</p>
            </div>
            
            <div className="system-management-container">
              <div className="coming-soon-placeholder">
                <div className="placeholder-icon">🚧</div>
                <h3>功能开发中</h3>
                <p>系统功能管理模块正在设计中，敬请期待...</p>
              </div>
            </div>
          </div>
        );
        
      case 'globalMemory':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>全局记忆</h2>
              <p>管理系统全局记忆和上下文信息</p>
            </div>
            
            <div className="global-memory-container">
              <div className="coming-soon-placeholder">
                <div className="placeholder-icon">🧠</div>
                <h3>功能开发中</h3>
                <p>全局记忆模块正在设计中，敬请期待...</p>
              </div>
            </div>
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
              <span className="nav-icon">🎛️</span>
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
              className={`nav-item ${activeSection === 'system' ? 'active' : ''}`}
              onClick={() => setActiveSection('system')}
            >
              <span className="nav-icon">⚙️</span>
              <span className="nav-text">系统功能管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'globalMemory' ? 'active' : ''}`}
              onClick={() => setActiveSection('globalMemory')}
            >
              <span className="nav-icon">💾</span>
              <span className="nav-text">全局记忆</span>
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