/**
 * MCP 设置组件
 * 
 * 提供 MCP 服务端和客户端配置的管理界面。
 */

import React, { useState, useEffect } from 'react';
import { mcpService } from '../../services/mcpService';
import './MCPSettings.css';

/**
 * MCP 设置主组件
 * 
 * @returns {JSX.Element} MCP 设置界面
 */
const MCPSettings = () => {
  // 状态管理
  const [activeTab, setActiveTab] = useState('server');
  const [serverConfigs, setServerConfigs] = useState([]);
  const [clientConfigs, setClientConfigs] = useState([]);
  const [mcpTools, setMcpTools] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [expandedClient, setExpandedClient] = useState(null);
  
  // 市场相关状态
  const [marketplaceServers, setMarketplaceServers] = useState([]);
  const [marketplaceCategories, setMarketplaceCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSource, setSelectedSource] = useState('mcpmarket');
  const [marketplaceLoading, setMarketplaceLoading] = useState(false);
  const [installingServer, setInstallingServer] = useState(null);
  const [installedServerIds, setInstalledServerIds] = useState(new Set());
  
  // 对话框状态
  const [showDialog, setShowDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState('create');
  const [configType, setConfigType] = useState('server');
  const [editingConfig, setEditingConfig] = useState(null);
  
  // 表单状态
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    transport: 'sse',
    host: '127.0.0.1',
    port: 8008,
    enabled: true,
    auth_type: 'none',
    connection_url: '',
    command: '',
    auto_connect: true
  });

  // 加载配置数据
  useEffect(() => {
    loadConfigs();
  }, []);
  
  // 加载市场数据
  useEffect(() => {
    if (activeTab === 'marketplace') {
      loadMarketplaceData();
    }
  }, [activeTab, selectedSource, selectedCategory]);
  
  /**
   * 加载市场数据
   */
  const loadMarketplaceData = async () => {
    setMarketplaceLoading(true);
    try {
      const [serversRes, categoriesRes] = await Promise.all([
        mcpService.getMarketplaceServers(selectedSource, selectedCategory || null),
        mcpService.getMarketplaceCategories(selectedSource)
      ]);
      
      if (serversRes.success) {
        setMarketplaceServers(serversRes.data.servers);
      }
      
      if (categoriesRes.success) {
        setMarketplaceCategories(categoriesRes.data.categories);
      }
    } catch (err) {
      setError('加载市场数据失败: ' + err.message);
    } finally {
      setMarketplaceLoading(false);
    }
  };
  
  /**
   * 安装市场服务
   * 
   * @param {Object} server - 服务信息
   */
  const handleInstallServer = async (server) => {
    setInstallingServer(server.id);
    try {
      const response = await mcpService.installMarketplaceServer(
        server.id,
        selectedSource,
        server.name
      );
      
      if (response.success) {
        setSuccessMessage(`服务 "${server.name}" 安装成功！`);
        setInstalledServerIds(prev => new Set([...prev, server.id]));
        // 刷新客户端配置列表
        const clientsRes = await mcpService.getClientConfigs();
        if (clientsRes.success) {
          setClientConfigs(clientsRes.data);
        }
      } else {
        setError('安装失败: ' + (response.error?.message || '未知错误'));
      }
    } catch (err) {
      setError('安装失败: ' + err.message);
    } finally {
      setInstallingServer(null);
    }
  };

  /**
   * 加载所有配置
   */
  const loadConfigs = async () => {
    setLoading(true);
    try {
      const [serversRes, clientsRes, toolsRes] = await Promise.all([
        mcpService.getServerConfigs(),
        mcpService.getClientConfigs(),
        mcpService.getTools()
      ]);
      
      if (serversRes.success) {
        setServerConfigs(serversRes.data);
      }
      
      if (clientsRes.success) {
        setClientConfigs(clientsRes.data);
      }
      
      if (toolsRes.success) {
        setMcpTools(toolsRes.data);
      }
    } catch (err) {
      setError('加载配置失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取客户端关联的工具
   * 
   * @param {number} clientId - 客户端ID
   * @returns {Array} 工具列表
   */
  const getClientTools = (clientId) => {
    return mcpTools.filter(tool => tool.client_id === clientId);
  };

  /**
   * 处理标签切换
   * 
   * @param {string} tab - 标签名称
   */
  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  /**
   * 打开创建对话框
   * 
   * @param {string} type - 配置类型
   */
  const handleOpenCreate = (type) => {
    setConfigType(type);
    setDialogMode('create');
    setEditingConfig(null);
    setFormData({
      name: '',
      description: '',
      transport: 'sse',
      host: '127.0.0.1',
      port: 8008,
      enabled: true,
      auth_type: 'none',
      connection_url: '',
      command: '',
      auto_connect: true
    });
    setShowDialog(true);
  };

  /**
   * 打开编辑对话框
   * 
   * @param {string} type - 配置类型
   * @param {Object} config - 配置对象
   */
  const handleOpenEdit = (type, config) => {
    setConfigType(type);
    setDialogMode('edit');
    setEditingConfig(config);
    setFormData({
      name: config.name || '',
      description: config.description || '',
      transport: config.transport || 'sse',
      host: config.host || '127.0.0.1',
      port: config.port || 8008,
      enabled: config.enabled !== false,
      auth_type: config.auth_type || 'none',
      connection_url: config.connection_url || '',
      command: config.command || '',
      auto_connect: config.auto_connect !== false
    });
    setShowDialog(true);
  };

  /**
   * 关闭对话框
   */
  const handleCloseDialog = () => {
    setShowDialog(false);
    setEditingConfig(null);
  };

  /**
   * 处理表单字段变化
   * 
   * @param {string} field - 字段名
   * @param {*} value - 字段值
   */
  const handleFieldChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  /**
   * 保存配置
   */
  const handleSave = async () => {
    setLoading(true);
    try {
      let response;
      
      if (configType === 'server') {
        const data = {
          name: formData.name,
          description: formData.description,
          transport: formData.transport,
          host: formData.host,
          port: formData.port,
          enabled: formData.enabled,
          auth_type: formData.auth_type,
          config: {}
        };
        
        if (dialogMode === 'create') {
          response = await mcpService.createServerConfig(data);
        } else {
          response = await mcpService.updateServerConfig(editingConfig.id, data);
        }
      } else {
        const data = {
          name: formData.name,
          description: formData.description,
          transport: formData.transport,
          connection_url: formData.connection_url,
          command: formData.command,
          enabled: formData.enabled,
          auto_connect: formData.auto_connect,
          config: {}
        };
        
        if (dialogMode === 'create') {
          response = await mcpService.createClientConfig(data);
        } else {
          response = await mcpService.updateClientConfig(editingConfig.id, data);
        }
      }
      
      if (response.success) {
        setSuccessMessage(dialogMode === 'create' ? '创建成功' : '更新成功');
        handleCloseDialog();
        loadConfigs();
      } else {
        setError(response.message || '保存失败');
      }
    } catch (err) {
      setError('保存失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 删除配置
   * 
   * @param {string} type - 配置类型
   * @param {number} id - 配置ID
   */
  const handleDelete = async (type, id) => {
    if (!window.confirm('确定要删除此配置吗？')) {
      return;
    }
    
    setLoading(true);
    try {
      let response;
      
      if (type === 'server') {
        response = await mcpService.deleteServerConfig(id);
      } else {
        response = await mcpService.deleteClientConfig(id);
      }
      
      if (response.success) {
        setSuccessMessage('删除成功');
        loadConfigs();
      } else {
        setError(response.message || '删除失败');
      }
    } catch (err) {
      setError('删除失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 连接客户端
   * 
   * @param {number} id - 客户端ID
   */
  const handleConnect = async (id) => {
    setLoading(true);
    try {
      const response = await mcpService.connectClient(id);
      if (response.success) {
        setSuccessMessage('连接成功');
        loadConfigs();
      } else {
        setError(response.message || '连接失败');
      }
    } catch (err) {
      setError('连接失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 断开客户端连接
   * 
   * @param {number} id - 客户端ID
   */
  const handleDisconnect = async (id) => {
    setLoading(true);
    try {
      const response = await mcpService.disconnectClient(id);
      if (response.success) {
        setSuccessMessage('断开成功');
        loadConfigs();
      } else {
        setError(response.message || '断开失败');
      }
    } catch (err) {
      setError('断开失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取状态颜色样式
   * 
   * @param {string} status - 状态
   * @returns {string} CSS 类名
   */
  const getStatusColorClass = (status) => {
    switch (status) {
      case 'connected':
        return 'status-connected';
      case 'connecting':
        return 'status-connecting';
      case 'disconnected':
        return 'status-disconnected';
      case 'error':
        return 'status-error';
      default:
        return 'status-unknown';
    }
  };

  /**
   * 获取状态文本
   * 
   * @param {string} status - 状态
   * @returns {string} 状态文本
   */
  const getStatusText = (status) => {
    switch (status) {
      case 'connected':
        return '已连接';
      case 'connecting':
        return '连接中';
      case 'disconnected':
        return '已断开';
      case 'error':
        return '错误';
      default:
        return '未知';
    }
  };

  return (
    <div className="mcp-settings-container">
      {/* 页面头部 */}
      <div className="content-header">
        <h2>MCP 服务</h2>
        <p>管理 MCP 服务的配置和连接</p>
      </div>

      {/* 标签页 */}
      <div className="mcp-tabs">
        <button
          className={`tab-btn ${activeTab === 'server' ? 'active' : ''}`}
          onClick={() => handleTabChange('server')}
        >
          <span className="tab-icon">🖥️</span>
          服务端配置
        </button>
        <button
          className={`tab-btn ${activeTab === 'client' ? 'active' : ''}`}
          onClick={() => handleTabChange('client')}
        >
          <span className="tab-icon">🔗</span>
          客户端连接
        </button>
        <button
          className={`tab-btn ${activeTab === 'marketplace' ? 'active' : ''}`}
          onClick={() => handleTabChange('marketplace')}
        >
          <span className="tab-icon">🛒</span>
          服务市场
        </button>
      </div>

      {/* 服务端配置标签 */}
      {activeTab === 'server' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>MCP 服务端配置</h3>
            <button
              className="add-btn"
              onClick={() => handleOpenCreate('server')}
              disabled={loading}
            >
              <span className="btn-icon">+</span>
              添加服务端
            </button>
          </div>

          <div className="config-list">
            {serverConfigs.map((config) => (
              <div key={config.id} className="config-card">
                <div className="config-info">
                  <div className="config-name">{config.name}</div>
                  <div className="config-description">{config.description || '无描述'}</div>
                  <div className="config-details">
                    <span className="config-tag">{config.transport.toUpperCase()}</span>
                    <span className="config-address">{config.host}:{config.port}</span>
                    <span className={`status-badge ${getStatusColorClass(config.status)}`}>
                      {getStatusText(config.status)}
                    </span>
                    <span className={`enable-badge ${config.enabled ? 'enabled' : 'disabled'}`}>
                      {config.enabled ? '启用' : '禁用'}
                    </span>
                  </div>
                </div>
                <div className="config-actions">
                  <button
                    className="action-btn edit-btn"
                    onClick={() => handleOpenEdit('server', config)}
                    disabled={loading}
                  >
                    编辑
                  </button>
                  <button
                    className="action-btn delete-btn"
                    onClick={() => handleDelete('server', config.id)}
                    disabled={loading}
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
            
            {serverConfigs.length === 0 && (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <p>暂无服务端配置，点击"添加服务端"创建</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 客户端连接标签 */}
      {activeTab === 'client' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>MCP 客户端连接</h3>
            <button
              className="add-btn"
              onClick={() => handleOpenCreate('client')}
              disabled={loading}
            >
              <span className="btn-icon">+</span>
              添加连接
            </button>
          </div>

          <div className="config-list">
            {clientConfigs.map((config) => {
              const clientTools = getClientTools(config.id);
              const isExpanded = expandedClient === config.id;
              
              return (
                <div key={config.id} className="config-card expandable">
                  <div 
                    className="config-header"
                    onClick={() => setExpandedClient(isExpanded ? null : config.id)}
                  >
                    <div className="config-info">
                      <div className="config-name">{config.name}</div>
                      <div className="config-description">{config.description || '无描述'}</div>
                      <div className="config-details">
                        <span className="config-tag">{config.transport.toUpperCase()}</span>
                        <span className="config-address">
                          {config.connection_url || config.command || 'N/A'}
                        </span>
                        <span className={`status-badge ${getStatusColorClass(config.status)}`}>
                          {getStatusText(config.status)}
                        </span>
                        <span className={`enable-badge ${config.enabled ? 'enabled' : 'disabled'}`}>
                          {config.enabled ? '启用' : '禁用'}
                        </span>
                      </div>
                    </div>
                    <div className="config-actions">
                      {config.status === 'connected' ? (
                        <button
                          className="action-btn disconnect-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDisconnect(config.id);
                          }}
                          disabled={loading}
                        >
                          断开
                        </button>
                      ) : (
                        <button
                          className="action-btn connect-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleConnect(config.id);
                          }}
                          disabled={loading || !config.enabled}
                        >
                          连接
                        </button>
                      )}
                      <button
                        className="action-btn edit-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenEdit('client', config);
                        }}
                        disabled={loading}
                      >
                        编辑
                      </button>
                      <button
                        className="action-btn delete-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete('client', config.id);
                        }}
                        disabled={loading}
                      >
                        删除
                      </button>
                      <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <div className="config-expanded">
                      <div className="expanded-divider"></div>
                      <div className="tools-section">
                        <h4>
                          <span className="tool-icon">🔧</span>
                          可用工具 ({clientTools.length})
                        </h4>
                        
                        {clientTools.length > 0 ? (
                          <div className="tools-list">
                            {clientTools.map((tool) => (
                              <span
                                key={tool.name}
                                className="tool-chip"
                                title={tool.description || '无描述'}
                              >
                                {tool.name}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="no-tools">
                            {config.status === 'connected' 
                              ? '该客户端没有提供工具' 
                              : '连接后可查看可用工具'}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            
            {clientConfigs.length === 0 && (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <p>暂无客户端连接配置，点击"添加连接"创建</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 服务市场标签 */}
      {activeTab === 'marketplace' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>MCP 服务市场</h3>
            <p className="section-description">浏览并安装第三方 MCP 服务</p>
          </div>
          
          {/* 筛选器 */}
          <div className="marketplace-filters">
            <div className="filter-group">
              <label>市场源</label>
              <select
                value={selectedSource}
                onChange={(e) => {
                  setSelectedSource(e.target.value);
                  setSelectedCategory('');
                }}
                disabled={marketplaceLoading}
              >
                <option value="mcpmarket">MCP Market</option>
                <option value="modelscope">ModelScope</option>
              </select>
            </div>
            
            <div className="filter-group">
              <label>类别</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                disabled={marketplaceLoading}
              >
                <option value="">全部类别</option>
                {marketplaceCategories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name} ({cat.count})
                  </option>
                ))}
              </select>
            </div>
            
            <button
              className="refresh-btn"
              onClick={loadMarketplaceData}
              disabled={marketplaceLoading}
            >
              <span className="btn-icon">🔄</span>
              {marketplaceLoading ? '加载中...' : '刷新'}
            </button>
          </div>
          
          {/* 服务列表 */}
          <div className="marketplace-list">
            {marketplaceLoading ? (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <p>正在加载服务列表...</p>
              </div>
            ) : (
              <>
                {marketplaceServers.map((server) => {
                  const isInstalled = installedServerIds.has(server.id);
                  const isInstalling = installingServer === server.id;
                  
                  return (
                    <div key={server.id} className="marketplace-card">
                      <div className="marketplace-card-header">
                        <div className="server-info">
                          <div className="server-name">
                            {server.name}
                            {server.popularity > 20000 && (
                              <span className="popular-badge" title="热门服务">🔥</span>
                            )}
                          </div>
                          <div className="server-category">{server.category}</div>
                        </div>
                        <div className="server-meta">
                          <span className="transport-tag">{server.transport.toUpperCase()}</span>
                          {server.auth_required && (
                            <span className="auth-badge" title="需要认证">🔒</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="server-description">
                        {server.description}
                      </div>
                      
                      {server.auth_required && server.env_vars && (
                        <div className="server-env-vars">
                          <span className="env-label">需要环境变量:</span>
                          <div className="env-list">
                            {server.env_vars.map((env) => (
                              <code key={env} className="env-var">{env}</code>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div className="marketplace-card-footer">
                        <div className="popularity">
                          <span className="popularity-icon">⭐</span>
                          {server.popularity?.toLocaleString() || 0}
                        </div>
                        <button
                          className={`install-btn ${isInstalled ? 'installed' : ''}`}
                          onClick={() => handleInstallServer(server)}
                          disabled={isInstalling || isInstalled}
                        >
                          {isInstalling ? (
                            <>
                              <span className="btn-icon">⏳</span>
                              安装中...
                            </>
                          ) : isInstalled ? (
                            <>
                              <span className="btn-icon">✅</span>
                              已安装
                            </>
                          ) : (
                            <>
                              <span className="btn-icon">⬇️</span>
                              安装
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
                
                {marketplaceServers.length === 0 && !marketplaceLoading && (
                  <div className="empty-state">
                    <div className="empty-icon">📭</div>
                    <p>暂无可用服务</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* 配置对话框 */}
      {showDialog && (
        <div className="modal-overlay">
          <div className="modal-content mcp-config-modal">
            <div className="modal-header">
              <h3>
                {dialogMode === 'create' ? '创建' : '编辑'} 
                {configType === 'server' ? '服务端配置' : '客户端连接'}
              </h3>
              <button className="close-btn" onClick={handleCloseDialog}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label>名称 *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleFieldChange('name', e.target.value)}
                  placeholder="输入配置名称"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleFieldChange('description', e.target.value)}
                  placeholder="输入配置描述"
                  rows="2"
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>传输类型</label>
                  <select
                    value={formData.transport}
                    onChange={(e) => handleFieldChange('transport', e.target.value)}
                  >
                    <option value="sse">SSE (Server-Sent Events)</option>
                    <option value="stdio">Stdio (标准输入输出)</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>认证类型</label>
                  <select
                    value={formData.auth_type}
                    onChange={(e) => handleFieldChange('auth_type', e.target.value)}
                  >
                    <option value="none">无认证</option>
                    <option value="api_key">API Key</option>
                    <option value="jwt">JWT</option>
                  </select>
                </div>
              </div>
              
              {configType === 'server' && formData.transport === 'sse' && (
                <div className="form-row">
                  <div className="form-group">
                    <label>监听地址</label>
                    <input
                      type="text"
                      value={formData.host}
                      onChange={(e) => handleFieldChange('host', e.target.value)}
                      placeholder="127.0.0.1"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>端口</label>
                    <input
                      type="number"
                      value={formData.port}
                      onChange={(e) => handleFieldChange('port', parseInt(e.target.value))}
                      min="1"
                      max="65535"
                    />
                  </div>
                </div>
              )}
              
              {configType === 'client' && (
                <>
                  {formData.transport === 'sse' && (
                    <div className="form-group">
                      <label>连接 URL</label>
                      <input
                        type="text"
                        value={formData.connection_url}
                        onChange={(e) => handleFieldChange('connection_url', e.target.value)}
                        placeholder="http://localhost:8008/sse"
                      />
                    </div>
                  )}
                  
                  {formData.transport === 'stdio' && (
                    <div className="form-group">
                      <label>启动命令</label>
                      <input
                        type="text"
                        value={formData.command}
                        onChange={(e) => handleFieldChange('command', e.target.value)}
                        placeholder="python -m mcp_server"
                      />
                    </div>
                  )}
                  
                  <div className="form-group checkbox-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.auto_connect}
                        onChange={(e) => handleFieldChange('auto_connect', e.target.checked)}
                      />
                      自动连接
                    </label>
                  </div>
                </>
              )}
              
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => handleFieldChange('enabled', e.target.checked)}
                  />
                  启用
                </label>
              </div>
            </div>
            
            <div className="modal-footer">
              <button className="cancel-btn" onClick={handleCloseDialog}>
                取消
              </button>
              <button 
                className="save-btn" 
                onClick={handleSave} 
                disabled={loading || !formData.name}
              >
                {loading ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 消息提示 */}
      {error && (
        <div className="message-toast error">
          <span className="message-icon">❌</span>
          {error}
          <button className="close-toast" onClick={() => setError(null)}>×</button>
        </div>
      )}
      
      {successMessage && (
        <div className="message-toast success">
          <span className="message-icon">✅</span>
          {successMessage}
          <button className="close-toast" onClick={() => setSuccessMessage(null)}>×</button>
        </div>
      )}
    </div>
  );
};

export default MCPSettings;
