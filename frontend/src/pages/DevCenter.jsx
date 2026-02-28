/**
 * 维护中心页面
 *
 * 提供创建Skill、创建Tool、配置MCP的统一入口
 * 支持从主流市场获取技能、工具和MCP服务
 * 是能力中心的子功能模块
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import SkillFormModal from '../components/SkillManagement/SkillFormModal';
import { mcpService } from '../services/mcpService';
import './dev-center.css';

/**
 * 维护中心主组件
 */
function DevCenter() {
  const { t } = useTranslation();
  const [activeModal, setActiveModal] = useState(null);
  const [activeTab, setActiveTab] = useState('create'); // 'create' | 'market'

  // MCP市场数据
  const [mcpServers, setMcpServers] = useState([]);
  const [mcpCategories, setMcpCategories] = useState([]);
  const [selectedMcpCategory, setSelectedMcpCategory] = useState('');
  const [mcpLoading, setMcpLoading] = useState(false);
  const [installingMcp, setInstallingMcp] = useState(null);
  const [mcpMarketplaces, setMcpMarketplaces] = useState([]);
  const [selectedMcpMarketplace, setSelectedMcpMarketplace] = useState('mcpmarket');
  const [showAddMcpMarketplaceForm, setShowAddMcpMarketplaceForm] = useState(false);

  /**
   * 开发选项配置 - 创建
   */
  const devOptions = [
    {
      id: 'skill',
      title: t('devCenter.createSkill'),
      description: t('devCenter.createSkillDesc'),
      icon: '🎯',
      color: '#52c41a',
      action: () => setActiveModal('skill')
    },
    {
      id: 'tool',
      title: t('devCenter.createTool'),
      description: t('devCenter.createToolDesc'),
      icon: '🔧',
      color: '#1890ff',
      action: () => setActiveModal('tool')
    },
    {
      id: 'mcp',
      title: t('devCenter.configMCP'),
      description: t('devCenter.configMCPDesc'),
      icon: '🔗',
      color: '#fa8c16',
      action: () => setActiveModal('mcp')
    }
  ];

  /**
   * 市场选项配置
   */
  const marketOptions = [
    {
      id: 'skill-market',
      title: t('devCenter.skillMarket', '技能市场'),
      description: t('devCenter.skillMarketDesc', '从主流市场浏览和安装技能'),
      icon: '🏪',
      color: '#52c41a',
      action: () => setActiveModal('skill-market')
    },
    {
      id: 'tool-market',
      title: t('devCenter.toolMarket', '工具市场'),
      description: t('devCenter.toolMarketDesc', '从主流市场浏览和安装工具'),
      icon: '🛠️',
      color: '#1890ff',
      action: () => setActiveModal('tool-market')
    },
    {
      id: 'mcp-market',
      title: t('devCenter.mcpMarket', 'MCP市场'),
      description: t('devCenter.mcpMarketDesc', '从主流市场浏览和安装MCP服务'),
      icon: '🌐',
      color: '#fa8c16',
      action: () => setActiveModal('mcp-market')
    }
  ];

  /**
   * 加载MCP市场数据
   */
  useEffect(() => {
    if (activeModal === 'mcp-market') {
      loadMcpMarketData();
      loadMcpMarketplaces();
    }
  }, [activeModal, selectedMcpCategory, selectedMcpMarketplace]);

  const loadMcpMarketData = async () => {
    setMcpLoading(true);
    try {
      const [serversRes, categoriesRes] = await Promise.all([
        mcpService.getMarketplaceServers(selectedMcpMarketplace, selectedMcpCategory || null),
        mcpService.getMarketplaceCategories(selectedMcpMarketplace)
      ]);

      if (serversRes.success) {
        setMcpServers(serversRes.data.servers || []);
      }

      if (categoriesRes.success) {
        setMcpCategories(categoriesRes.data.categories || []);
      }
    } catch (err) {
      console.error('加载MCP市场数据失败:', err);
    } finally {
      setMcpLoading(false);
    }
  };

  /**
   * 加载MCP市场列表
   */
  const loadMcpMarketplaces = async () => {
    try {
      const response = await mcpService.getMarketplaceList();
      if (response.success) {
        setMcpMarketplaces(response.data || []);
      }
    } catch (err) {
      console.error('加载MCP市场列表失败:', err);
    }
  };

  /**
   * 添加自定义MCP市场
   */
  const handleAddCustomMcpMarketplace = async (formData) => {
    try {
      const response = await mcpService.addCustomMarketplace({
        id: formData.id,
        name: formData.name,
        name_zh: formData.name_zh,
        url: formData.url,
        description: formData.description,
        description_zh: formData.description_zh,
        icon: formData.icon,
        supports_search: formData.supports_search,
        supports_install: formData.supports_install,
        categories: []
      });

      if (response.success) {
        setShowAddMcpMarketplaceForm(false);
        await loadMcpMarketplaces();
        alert(t('devCenter.addMarketplaceSuccess', '添加市场成功'));
      }
    } catch (err) {
      console.error('添加自定义MCP市场失败:', err);
      alert(t('devCenter.addMarketplaceError', '添加市场失败'));
    }
  };

  /**
   * 安装MCP服务
   */
  const handleInstallMcp = async (server) => {
    setInstallingMcp(server.id);
    try {
      const response = await mcpService.installMarketplaceServer(
        server.id,
        'mcpmarket',
        server.name
      );

      if (response.success) {
        alert(`服务 "${server.name}" 安装成功！`);
      } else {
        alert('安装失败: ' + (response.message || '未知错误'));
      }
    } catch (err) {
      alert('安装失败: ' + err.message);
    } finally {
      setInstallingMcp(null);
    }
  };

  /**
   * 处理创建技能
   */
  const handleCreateSkill = async (skillData) => {
    try {
      const response = await fetch('/api/v1/skills', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(skillData)
      });

      if (response.ok) {
        setActiveModal(null);
        alert(t('devCenter.createSkillSuccess'));
      } else {
        const error = await response.json();
        alert(error.message || t('devCenter.createSkillError'));
      }
    } catch (err) {
      console.error('Failed to create skill:', err);
      alert(t('devCenter.createSkillError'));
    }
  };

  /**
   * 处理创建工具
   */
  const handleCreateTool = async (toolData) => {
    try {
      const response = await fetch('/api/v1/tools', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(toolData)
      });

      if (response.ok) {
        setActiveModal(null);
        alert(t('devCenter.createToolSuccess'));
      } else {
        const error = await response.json();
        alert(error.message || t('devCenter.createToolError'));
      }
    } catch (err) {
      console.error('Failed to create tool:', err);
      alert(t('devCenter.createToolError'));
    }
  };

  /**
   * 处理配置MCP
   */
  const handleConfigMCP = async (mcpData) => {
    try {
      const response = await fetch('/api/v1/mcp/clients', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(mcpData)
      });

      if (response.ok) {
        setActiveModal(null);
        alert(t('devCenter.configMCPSuccess'));
      } else {
        const error = await response.json();
        alert(error.message || t('devCenter.configMCPError'));
      }
    } catch (err) {
      console.error('Failed to config MCP:', err);
      alert(t('devCenter.configMCPError'));
    }
  };

  /**
   * 渲染工具创建表单
   */
  const renderToolForm = () => (
    <div className="modal-overlay" onClick={() => setActiveModal(null)}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('devCenter.createTool')}</h2>
          <button className="close-button" onClick={() => setActiveModal(null)}>×</button>
        </div>
        <div className="modal-body">
          <ToolForm onSubmit={handleCreateTool} onCancel={() => setActiveModal(null)} />
        </div>
      </div>
    </div>
  );

  /**
   * 渲染MCP配置表单
   */
  const renderMCPForm = () => (
    <div className="modal-overlay" onClick={() => setActiveModal(null)}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('devCenter.configMCP')}</h2>
          <button className="close-button" onClick={() => setActiveModal(null)}>×</button>
        </div>
        <div className="modal-body">
          <MCPForm onSubmit={handleConfigMCP} onCancel={() => setActiveModal(null)} />
        </div>
      </div>
    </div>
  );

  // 技能市场状态
  const [skillMarketplaces, setSkillMarketplaces] = useState([]);
  const [skillMarketplaceSkills, setSkillMarketplaceSkills] = useState([]);
  const [selectedSkillMarketplace, setSelectedSkillMarketplace] = useState('');
  const [selectedSkillCategory, setSelectedSkillCategory] = useState('');
  const [skillSearchQuery, setSkillSearchQuery] = useState('');
  const [skillLoading, setSkillLoading] = useState(false);
  const [showAddMarketplaceForm, setShowAddMarketplaceForm] = useState(false);

  /**
   * 加载技能市场数据
   */
  useEffect(() => {
    if (activeModal === 'skill-market') {
      loadSkillMarketplaces();
    }
  }, [activeModal]);

  useEffect(() => {
    if (activeModal === 'skill-market') {
      loadSkillMarketplaceSkills();
    }
  }, [activeModal, selectedSkillMarketplace, selectedSkillCategory, skillSearchQuery]);

  const loadSkillMarketplaces = async () => {
    try {
      const response = await fetch('/api/v1/skills/marketplace/list');
      const data = await response.json();
      if (data.success) {
        setSkillMarketplaces(data.data || []);
      }
    } catch (err) {
      console.error('加载技能市场列表失败:', err);
    }
  };

  const loadSkillMarketplaceSkills = async () => {
    setSkillLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedSkillMarketplace) params.append('marketplace', selectedSkillMarketplace);
      if (selectedSkillCategory) params.append('category', selectedSkillCategory);
      if (skillSearchQuery) params.append('search', skillSearchQuery);

      const response = await fetch(`/api/v1/skills/marketplace/skills?${params}`);
      const data = await response.json();
      if (data.success) {
        setSkillMarketplaceSkills(data.data || []);
      }
    } catch (err) {
      console.error('加载技能市场技能失败:', err);
    } finally {
      setSkillLoading(false);
    }
  };

  const handleAddCustomMarketplace = async (marketplaceData) => {
    try {
      const response = await fetch('/api/v1/skills/marketplace/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(marketplaceData)
      });
      const data = await response.json();
      if (data.success) {
        alert(`成功添加市场: ${data.data.name}`);
        setShowAddMarketplaceForm(false);
        loadSkillMarketplaces();
      } else {
        alert('添加失败: ' + data.message);
      }
    } catch (err) {
      alert('添加失败: ' + err.message);
    }
  };

  /**
   * 渲染技能市场
   */
  const renderSkillMarket = () => (
    <div className="modal-overlay" onClick={() => setActiveModal(null)}>
      <div className="modal-content market-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('devCenter.skillMarket', '技能市场')}</h2>
          <button className="close-button" onClick={() => setActiveModal(null)}>×</button>
        </div>
        <div className="modal-body">
          {/* 市场筛选 */}
          <div className="market-filters">
            <select
              value={selectedSkillMarketplace}
              onChange={(e) => setSelectedSkillMarketplace(e.target.value)}
              className="category-select"
            >
              <option value="">{t('devCenter.allMarketplaces', '所有市场')}</option>
              {skillMarketplaces.map((mp) => (
                <option key={mp.id} value={mp.id}>
                  {mp.icon} {mp.name_zh || mp.name}
                </option>
              ))}
            </select>

            <input
              type="text"
              value={skillSearchQuery}
              onChange={(e) => setSkillSearchQuery(e.target.value)}
              placeholder={t('devCenter.searchSkills', '搜索技能...')}
              className="search-input"
            />

            <button
              className="add-marketplace-btn"
              onClick={() => setShowAddMarketplaceForm(true)}
            >
              + {t('devCenter.addMarketplace', '添加市场')}
            </button>
          </div>

          {/* 添加市场表单 */}
          {showAddMarketplaceForm && (
            <AddMarketplaceForm
              onSubmit={handleAddCustomMarketplace}
              onCancel={() => setShowAddMarketplaceForm(false)}
            />
          )}

          {/* 技能列表 */}
          {skillLoading ? (
            <div className="market-loading">{t('devCenter.loading', '加载中...')}</div>
          ) : (
            <div className="market-skills-grid">
              {skillMarketplaceSkills.map((skill) => (
                <div key={skill.id} className="market-skill-card">
                  <div className="skill-header">
                    <div className="skill-icon">{skill.icon || '🎯'}</div>
                    <div className="skill-info">
                      <h3 className="skill-name">{skill.name}</h3>
                      <span className="skill-category">{skill.category}</span>
                    </div>
                  </div>
                  <p className="skill-description">{skill.description}</p>
                  <div className="skill-meta">
                    <span className="skill-rating">⭐ {skill.rating}</span>
                    <span className="skill-downloads">📥 {skill.downloads?.toLocaleString()}</span>
                    {skill.official && <span className="skill-official">✅ {t('devCenter.official', '官方')}</span>}
                  </div>
                  <div className="skill-footer">
                    <span className="skill-author">{t('devCenter.author', '作者')}: {skill.author}</span>
                    <span className="skill-marketplace">
                      <a href={skill.marketplace_url} target="_blank" rel="noopener noreferrer">
                        {skillMarketplaces.find(mp => mp.id === skill.marketplace)?.name_zh || skill.marketplace}
                      </a>
                    </span>
                  </div>
                  <button className="install-button" disabled={skill.installed}>
                    {skill.installed ? t('devCenter.installed', '已安装') : t('devCenter.install', '安装')}
                  </button>
                </div>
              ))}
            </div>
          )}

          {!skillLoading && skillMarketplaceSkills.length === 0 && (
            <div className="market-empty">
              {t('devCenter.noSkills', '暂无可用技能')}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  /**
   * 渲染工具市场
   */
  const [toolMarketplaces, setToolMarketplaces] = useState([]);
  const [selectedToolMarketplace, setSelectedToolMarketplace] = useState('');
  const [toolCategories, setToolCategories] = useState([]);
  const [selectedToolCategory, setSelectedToolCategory] = useState('');
  const [toolSearchQuery, setToolSearchQuery] = useState('');
  const [toolLoading, setToolLoading] = useState(false);
  const [showAddToolMarketplaceForm, setShowAddToolMarketplaceForm] = useState(false);
  const [marketplaceTools, setMarketplaceTools] = useState([]);

  useEffect(() => {
    if (activeModal === 'tool-market') {
      loadToolMarketplaces();
    }
  }, [activeModal]);

  const loadToolMarketplaces = async () => {
    try {
      const response = await fetch('/api/v1/skills/marketplace/list?type=tool', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setToolMarketplaces(data.data || []);
      }
    } catch (err) {
      console.error('加载工具市场列表失败:', err);
    }
  };

  const handleAddCustomToolMarketplace = async (formData) => {
    try {
      const response = await fetch('/api/v1/skills/marketplace', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...formData,
          marketplace_type: 'tool'
        })
      });

      const data = await response.json();
      if (data.success) {
        setShowAddToolMarketplaceForm(false);
        await loadToolMarketplaces();
        alert(t('devCenter.addMarketplaceSuccess', '添加市场成功'));
      }
    } catch (err) {
      console.error('添加自定义工具市场失败:', err);
      alert(t('devCenter.addMarketplaceError', '添加市场失败'));
    }
  };

  const renderToolMarket = () => (
    <div className="modal-overlay" onClick={() => setActiveModal(null)}>
      <div className="modal-content market-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('devCenter.toolMarket', '工具市场')}</h2>
          <button className="close-button" onClick={() => setActiveModal(null)}>×</button>
        </div>
        <div className="modal-body">
          {/* 市场筛选 */}
          <div className="market-filters">
            <select
              value={selectedToolMarketplace}
              onChange={(e) => setSelectedToolMarketplace(e.target.value)}
              className="category-select"
            >
              <option value="">{t('devCenter.allMarketplaces', '所有市场')}</option>
              {toolMarketplaces.map((mp) => (
                <option key={mp.id} value={mp.id}>
                  {mp.icon} {mp.name_zh || mp.name}
                </option>
              ))}
            </select>

            <select
              value={selectedToolCategory}
              onChange={(e) => setSelectedToolCategory(e.target.value)}
              className="category-select"
            >
              <option value="">{t('devCenter.allCategories', '所有分类')}</option>
              {toolCategories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>

            <input
              type="text"
              value={toolSearchQuery}
              onChange={(e) => setToolSearchQuery(e.target.value)}
              placeholder={t('devCenter.searchTools', '搜索工具...')}
              className="search-input"
            />

            <button
              className="add-marketplace-btn"
              onClick={() => setShowAddToolMarketplaceForm(true)}
            >
              + {t('devCenter.addMarketplace', '添加市场')}
            </button>
          </div>

          {/* 添加市场表单 */}
          {showAddToolMarketplaceForm && (
            <AddMarketplaceForm
              onSubmit={handleAddCustomToolMarketplace}
              onCancel={() => setShowAddToolMarketplaceForm(false)}
            />
          )}

          {/* 工具列表 */}
          {toolLoading ? (
            <div className="market-loading">{t('devCenter.loading', '加载中...')}</div>
          ) : (
            <div className="market-tools-grid">
              {marketplaceTools.map((tool) => (
                <div key={tool.id} className="market-tool-card">
                  <div className="tool-header">
                    <div className="tool-icon">{tool.icon || '🔧'}</div>
                    <div className="tool-info">
                      <h3 className="tool-name">{tool.name}</h3>
                      <span className="tool-category">{tool.category}</span>
                    </div>
                  </div>
                  <p className="tool-description">{tool.description}</p>
                  <div className="tool-meta">
                    <span className="tool-rating">⭐ {tool.rating}</span>
                    <span className="tool-downloads">📥 {tool.downloads?.toLocaleString()}</span>
                    {tool.official && <span className="tool-official">✅ {t('devCenter.official', '官方')}</span>}
                  </div>
                  <div className="tool-footer">
                    <span className="tool-author">{t('devCenter.author', '作者')}: {tool.author}</span>
                    <span className="tool-marketplace">
                      <a href={tool.marketplace_url} target="_blank" rel="noopener noreferrer">
                        {toolMarketplaces.find(mp => mp.id === tool.marketplace)?.name_zh || tool.marketplace}
                      </a>
                    </span>
                  </div>
                  <button className="install-button" disabled={tool.installed}>
                    {tool.installed ? t('devCenter.installed', '已安装') : t('devCenter.install', '安装')}
                  </button>
                </div>
              ))}
            </div>
          )}

          {!toolLoading && marketplaceTools.length === 0 && (
            <div className="market-placeholder">
              <div className="placeholder-icon">🛠️</div>
              <h3>{t('devCenter.comingSoon', '即将推出')}</h3>
              <p>{t('devCenter.toolMarketComingSoon', '工具市场功能正在开发中，敬请期待！')}</p>
              <div className="market-preview">
                <h4>{t('devCenter.previewFeatures', '预览功能')}</h4>
                <ul>
                  <li>🔧 {t('devCenter.toolFeature1', '浏览社区工具')}</li>
                  <li>📥 {t('devCenter.toolFeature2', '快速安装工具')}</li>
                  <li>⚙️ {t('devCenter.toolFeature3', '配置工具参数')}</li>
                  <li>🔍 {t('devCenter.toolFeature4', '按类别筛选工具')}</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  /**
   * 渲染MCP市场
   */
  const renderMcpMarket = () => (
    <div className="modal-overlay" onClick={() => setActiveModal(null)}>
      <div className="modal-content market-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('devCenter.mcpMarket', 'MCP市场')}</h2>
          <button className="close-button" onClick={() => setActiveModal(null)}>×</button>
        </div>
        <div className="modal-body">
          {/* 市场和分类筛选 */}
          <div className="market-filters">
            <select
              value={selectedMcpMarketplace}
              onChange={(e) => setSelectedMcpMarketplace(e.target.value)}
              className="category-select"
            >
              {mcpMarketplaces.map((mp) => (
                <option key={mp.id} value={mp.id}>
                  {mp.icon} {mp.name_zh || mp.name}
                </option>
              ))}
            </select>

            <select
              value={selectedMcpCategory}
              onChange={(e) => setSelectedMcpCategory(e.target.value)}
              className="category-select"
            >
              <option value="">{t('devCenter.allCategories', '所有分类')}</option>
              {mcpCategories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name} ({cat.count})
                </option>
              ))}
            </select>

            <button
              className="add-marketplace-btn"
              onClick={() => setShowAddMcpMarketplaceForm(true)}
            >
              + {t('devCenter.addMarketplace', '添加市场')}
            </button>
          </div>

          {/* 添加市场表单 */}
          {showAddMcpMarketplaceForm && (
            <AddMarketplaceForm
              onSubmit={handleAddCustomMcpMarketplace}
              onCancel={() => setShowAddMcpMarketplaceForm(false)}
            />
          )}

          {/* MCP服务列表 */}
          {mcpLoading ? (
            <div className="market-loading">{t('devCenter.loading', '加载中...')}</div>
          ) : (
            <div className="market-servers-grid">
              {mcpServers.map((server) => (
                <div key={server.id} className="market-server-card">
                  <div className="server-header">
                    <h3 className="server-name">{server.name}</h3>
                    <span className="server-category">{server.category}</span>
                  </div>
                  <p className="server-description">{server.description}</p>
                  <div className="server-meta">
                    <span className="server-popularity">
                      🔥 {server.popularity?.toLocaleString() || 0}
                    </span>
                    {server.auth_required && (
                      <span className="server-auth">🔒 {t('devCenter.authRequired', '需要认证')}</span>
                    )}
                  </div>
                  {server.env_vars && server.env_vars.length > 0 && (
                    <div className="server-env-vars">
                      <small>{t('devCenter.envVars', '环境变量')}:</small>
                      <code>{server.env_vars.join(', ')}</code>
                    </div>
                  )}
                  <button
                    className="install-button"
                    onClick={() => handleInstallMcp(server)}
                    disabled={installingMcp === server.id}
                  >
                    {installingMcp === server.id
                      ? t('devCenter.installing', '安装中...')
                      : t('devCenter.install', '安装')}
                  </button>
                </div>
              ))}
            </div>
          )}

          {!mcpLoading && mcpServers.length === 0 && (
            <div className="market-empty">
              {t('devCenter.noServers', '暂无可用服务')}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="dev-center-container">
      <div className="dev-center-header">
        <h1 className="page-title">{t('devCenter.title')}</h1>
        <p className="page-description">{t('devCenter.description')}</p>
      </div>

      {/* 标签切换 */}
      <div className="dev-tabs">
        <button
          className={`dev-tab ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          {t('devCenter.createTab', '创建')}
        </button>
        <button
          className={`dev-tab ${activeTab === 'market' ? 'active' : ''}`}
          onClick={() => setActiveTab('market')}
        >
          {t('devCenter.marketTab', '市场')}
        </button>
      </div>

      {/* 创建选项 */}
      {activeTab === 'create' && (
        <div className="dev-options-grid">
          {devOptions.map((option) => (
            <div
              key={option.id}
              className="dev-option-card"
              onClick={option.action}
              style={{ '--card-color': option.color }}
            >
              <div className="option-icon" style={{ backgroundColor: `${option.color}15` }}>
                <span style={{ color: option.color }}>{option.icon}</span>
              </div>
              <div className="option-content">
                <h3 className="option-title">{option.title}</h3>
                <p className="option-description">{option.description}</p>
              </div>
              <div className="option-arrow">→</div>
            </div>
          ))}
        </div>
      )}

      {/* 市场选项 */}
      {activeTab === 'market' && (
        <div className="dev-options-grid">
          {marketOptions.map((option) => (
            <div
              key={option.id}
              className="dev-option-card"
              onClick={option.action}
              style={{ '--card-color': option.color }}
            >
              <div className="option-icon" style={{ backgroundColor: `${option.color}15` }}>
                <span style={{ color: option.color }}>{option.icon}</span>
              </div>
              <div className="option-content">
                <h3 className="option-title">{option.title}</h3>
                <p className="option-description">{option.description}</p>
              </div>
              <div className="option-arrow">→</div>
            </div>
          ))}
        </div>
      )}

      {/* 模态框 */}
      {activeModal === 'skill' && (
        <SkillFormModal
          onClose={() => setActiveModal(null)}
          onSubmit={handleCreateSkill}
        />
      )}
      {activeModal === 'tool' && renderToolForm()}
      {activeModal === 'mcp' && renderMCPForm()}
      {activeModal === 'skill-market' && renderSkillMarket()}
      {activeModal === 'tool-market' && renderToolMarket()}
      {activeModal === 'mcp-market' && renderMcpMarket()}
    </div>
  );
}

/**
 * 工具创建表单组件
 */
function ToolForm({ onSubmit, onCancel }) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    category: 'general',
    tool_type: 'local',
    parameters_schema: {},
    config: {},
    icon: '🔧',
    version: '1.0.0'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="dev-form">
      <div className="form-group">
        <label>{t('devCenter.toolName')}</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder={t('devCenter.toolNamePlaceholder')}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.displayName')}</label>
        <input
          type="text"
          value={formData.display_name}
          onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
          placeholder={t('devCenter.displayNamePlaceholder')}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.description')}</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder={t('devCenter.descriptionPlaceholder')}
          rows={3}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.category')}</label>
        <select
          value={formData.category}
          onChange={(e) => setFormData({ ...formData, category: e.target.value })}
        >
          <option value="general">{t('devCenter.categories.general')}</option>
          <option value="search">{t('devCenter.categories.search')}</option>
          <option value="file">{t('devCenter.categories.file')}</option>
          <option value="data">{t('devCenter.categories.data')}</option>
          <option value="api">{t('devCenter.categories.api')}</option>
        </select>
      </div>

      <div className="form-group">
        <label>{t('devCenter.toolType')}</label>
        <select
          value={formData.tool_type}
          onChange={(e) => setFormData({ ...formData, tool_type: e.target.value })}
        >
          <option value="local">{t('devCenter.toolTypes.local')}</option>
          <option value="api">{t('devCenter.toolTypes.api')}</option>
          <option value="script">{t('devCenter.toolTypes.script')}</option>
        </select>
      </div>

      <div className="form-group">
        <label>{t('devCenter.icon')}</label>
        <input
          type="text"
          value={formData.icon}
          onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
          placeholder="🔧"
        />
      </div>

      <div className="form-actions">
        <button type="button" className="btn-cancel" onClick={onCancel}>
          {t('cancel')}
        </button>
        <button type="submit" className="btn-submit">
          {t('create')}
        </button>
      </div>
    </form>
  );
}

/**
 * MCP配置表单组件
 */
function MCPForm({ onSubmit, onCancel }) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    server_url: '',
    api_key: '',
    timeout: 30,
    enabled: true
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="dev-form">
      <div className="form-group">
        <label>{t('devCenter.mcpName')}</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder={t('devCenter.mcpNamePlaceholder')}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.mcpDescription')}</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder={t('devCenter.mcpDescriptionPlaceholder')}
          rows={2}
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.mcpServerUrl')}</label>
        <input
          type="url"
          value={formData.server_url}
          onChange={(e) => setFormData({ ...formData, server_url: e.target.value })}
          placeholder={t('devCenter.mcpServerUrlPlaceholder')}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.mcpApiKey')}</label>
        <input
          type="password"
          value={formData.api_key}
          onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
          placeholder={t('devCenter.mcpApiKeyPlaceholder')}
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.mcpTimeout')}</label>
        <input
          type="number"
          value={formData.timeout}
          onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) })}
          min={5}
          max={300}
        />
      </div>

      <div className="form-group checkbox-group">
        <label>
          <input
            type="checkbox"
            checked={formData.enabled}
            onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
          />
          {t('devCenter.mcpEnabled')}
        </label>
      </div>

      <div className="form-actions">
        <button type="button" className="btn-cancel" onClick={onCancel}>
          {t('cancel')}
        </button>
        <button type="submit" className="btn-submit">
          {t('save')}
        </button>
      </div>
    </form>
  );
}

/**
 * 添加市场表单组件
 */
function AddMarketplaceForm({ onSubmit, onCancel }) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    name_zh: '',
    url: '',
    description: '',
    description_zh: '',
    icon: '🌐',
    supports_search: false,
    supports_install: false
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="add-marketplace-form">
      <h4>{t('devCenter.addMarketplaceTitle', '添加自定义市场')}</h4>

      <div className="form-row">
        <div className="form-group">
          <label>{t('devCenter.marketplaceId', '市场ID')}</label>
          <input
            type="text"
            value={formData.id}
            onChange={(e) => setFormData({ ...formData, id: e.target.value })}
            placeholder="my-marketplace"
            required
          />
        </div>

        <div className="form-group">
          <label>{t('devCenter.marketplaceIcon', '图标')}</label>
          <input
            type="text"
            value={formData.icon}
            onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
            placeholder="🌐"
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>{t('devCenter.marketplaceName', '英文名称')}</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="My Marketplace"
            required
          />
        </div>

        <div className="form-group">
          <label>{t('devCenter.marketplaceNameZh', '中文名称')}</label>
          <input
            type="text"
            value={formData.name_zh}
            onChange={(e) => setFormData({ ...formData, name_zh: e.target.value })}
            placeholder="我的市场"
          />
        </div>
      </div>

      <div className="form-group">
        <label>{t('devCenter.marketplaceUrl', '市场URL')}</label>
        <input
          type="url"
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          placeholder="https://example.com/marketplace"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>{t('devCenter.marketplaceDesc', '英文描述')}</label>
          <input
            type="text"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Description of the marketplace"
          />
        </div>

        <div className="form-group">
          <label>{t('devCenter.marketplaceDescZh', '中文描述')}</label>
          <input
            type="text"
            value={formData.description_zh}
            onChange={(e) => setFormData({ ...formData, description_zh: e.target.value })}
            placeholder="市场描述"
          />
        </div>
      </div>

      <div className="form-group checkbox-group">
        <label>
          <input
            type="checkbox"
            checked={formData.supports_search}
            onChange={(e) => setFormData({ ...formData, supports_search: e.target.checked })}
          />
          {t('devCenter.supportsSearch', '支持搜索')}
        </label>
      </div>

      <div className="form-actions">
        <button type="button" className="btn-cancel" onClick={onCancel}>
          {t('cancel')}
        </button>
        <button type="submit" className="btn-submit">
          {t('add')}
        </button>
      </div>
    </form>
  );
}

export default DevCenter;
