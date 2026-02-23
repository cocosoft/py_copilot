import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './tool.css';

const Tool = () => {
  const [tools, setTools] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedTool, setSelectedTool] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [executingTool, setExecutingTool] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [activeTab, setActiveTab] = useState('tools'); // 'tools', 'history', 'settings'
  const [toolHistory, setToolHistory] = useState([]);
  const [toolSettings, setToolSettings] = useState({});

  const API_BASE = '/api/v1';

  useEffect(() => {
    loadTools();
    loadCategories();
    loadToolHistory();
    loadToolSettings();
  }, []);

  useEffect(() => {
    loadTools();
  }, [selectedCategory]);

  const loadTools = async () => {
    try {
      setLoading(true);
      const params = {};
      if (selectedCategory !== null) {
        params.category = selectedCategory;
      }
      
      const response = await axios.get(`${API_BASE}/tools`, { params });
      if (response.data.success) {
        setTools(response.data.data);
      }
    } catch (error) {
      console.error('加载工具列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await axios.get(`${API_BASE}/tools/categories`);
      if (response.data.success) {
        setCategories(['全部工具', ...response.data.data]);
      }
    } catch (error) {
      console.error('加载分类失败:', error);
    }
  };

  const loadToolHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/tools/history`);
      if (response.data.success) {
        setToolHistory(response.data.data);
      }
    } catch (error) {
      console.error('加载工具历史失败:', error);
    }
  };

  const loadToolSettings = async () => {
    try {
      const response = await axios.get(`${API_BASE}/tools/settings`);
      if (response.data.success) {
        setToolSettings(response.data.data);
      }
    } catch (error) {
      console.error('加载工具设置失败:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadTools();
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/tools/search`, {
        params: { keyword: searchQuery }
      });
      if (response.data.success) {
        setTools(response.data.data);
      }
    } catch (error) {
      console.error('搜索工具失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (category) => {
    setSelectedCategory(category === '全部工具' ? null : category);
  };

  const handleToolClick = async (tool) => {
    try {
      const response = await axios.get(`${API_BASE}/tools/${tool.name}`);
      if (response.data.success) {
        setSelectedTool(response.data.data);
        setShowDetail(true);
      }
    } catch (error) {
      console.error('获取工具详情失败:', error);
    }
  };

  const handleExecuteTool = async (toolName, parameters = {}) => {
    try {
      setExecutingTool(toolName);
      setExecutionResult(null);

      const response = await axios.post(
        `${API_BASE}/tools/${toolName}/execute`,
        parameters
      );

      if (response.data.success) {
        setExecutionResult({
          success: true,
          result: response.data.data.result,
          executionTime: response.data.data.execution_time
        });
        
        // 刷新工具历史
        loadToolHistory();
      } else {
        setExecutionResult({
          success: false,
          error: response.data.error
        });
      }
    } catch (error) {
      console.error('执行工具失败:', error);
      setExecutionResult({
        success: false,
        error: error.message || '执行工具失败'
      });
    } finally {
      setExecutingTool(null);
    }
  };

  const handleToggleToolActive = async (toolName, isActive) => {
    try {
      const response = await axios.patch(`${API_BASE}/tools/${toolName}/status`, {
        is_active: isActive
      });
      
      if (response.data.success) {
        setTools(prev => prev.map(tool => 
          tool.name === toolName 
            ? { ...tool, is_active: isActive }
            : tool
        ));
      }
    } catch (error) {
      console.error('切换工具状态失败:', error);
    }
  };

  const handleSaveToolSettings = async (settings) => {
    try {
      const response = await axios.put(`${API_BASE}/tools/settings`, settings);
      
      if (response.data.success) {
        setToolSettings(settings);
        alert('工具设置保存成功');
      }
    } catch (error) {
      console.error('保存工具设置失败:', error);
      alert('保存工具设置失败');
    }
  };

  const handleClearToolHistory = async () => {
    if (!confirm('确定要清空工具调用历史吗？')) {
      return;
    }

    try {
      const response = await axios.delete(`${API_BASE}/tools/history`);
      
      if (response.data.success) {
        setToolHistory([]);
      }
    } catch (error) {
      console.error('清空工具历史失败:', error);
      alert('清空工具历史失败');
    }
  };

  const handleResetToolSettings = () => {
    if (confirm('确定要重置工具设置吗？')) {
      setToolSettings({
        enable_auto_execution: true,
        show_tool_calls: true,
        enable_tool_logging: true,
        execution_timeout: 30,
        max_concurrent_calls: 5
      });
    }
  };

  const handleCloseDetail = () => {
    setShowDetail(false);
    setSelectedTool(null);
    setExecutionResult(null);
  };

  return (
    <div className="tool-container">
      <div className="content-header">
        <h2>工具管理</h2>
        <p>管理和配置Function Calling工具</p>
      </div>

      <div className="tool-tabs">
        <button 
          className={`tab-btn ${activeTab === 'tools' ? 'active' : ''}`}
          onClick={() => setActiveTab('tools')}
        >
          📋 工具列表
        </button>
        <button 
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📊 调用历史
        </button>
        <button 
          className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          ⚙️ 工具设置
        </button>
      </div>

      <div className="tool-content">
        {activeTab === 'tools' && (
          <>
            <div className="tool-sidebar">
              <div className="sidebar-header">
                <h3>工具分类</h3>
              </div>

              <div className="category-list">
                {categories.map((category) => (
                  <button
                    key={category}
                    className={`category-item ${
                      (selectedCategory === null && category === '全部工具') ||
                      selectedCategory === category
                        ? 'active'
                        : ''
                    }`}
                    onClick={() => handleCategoryChange(category)}
                  >
                    {category === '全部工具' ? '📋 全部工具' : category}
                  </button>
                ))}
              </div>
            </div>

            <div className="tool-main">
              <div className="tool-controls">
                <div className="search-bar">
                  <input
                    type="text"
                    placeholder="搜索工具..."
                    className="tool-search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                  <button className="search-icon" onClick={handleSearch}>
                    🔍
                  </button>
                </div>
              </div>

              {loading ? (
                <div className="loading-container">
                  <div className="loading-spinner"></div>
                  <p>加载中...</p>
                </div>
              ) : (
                <div className="tool-grid">
                  {tools.map((tool) => (
                    <div key={tool.name} className="tool-card">
                      <div className="tool-card-header">
                        <div className="tool-icon">{tool.icon}</div>
                        <div className="tool-status">
                          <span className={`status-indicator ${tool.is_active ? 'active' : 'inactive'}`}>
                            {tool.is_active ? '●' : '○'}
                          </span>
                        </div>
                      </div>

                      <div className="tool-card-content">
                        <h3 className="tool-name">{tool.display_name}</h3>
                        <p className="tool-description">{tool.description}</p>
                        <div className="tool-meta">
                          <span className="tool-category">{tool.category}</span>
                          <span className="tool-version">v{tool.version}</span>
                        </div>
                      </div>

                      <div className="tool-card-footer">
                        <button
                          className="use-tool-btn"
                          onClick={() => handleToolClick(tool)}
                          disabled={!tool.is_active}
                        >
                          使用工具
                        </button>
                        <button
                          className="toggle-tool-btn"
                          onClick={() => handleToggleToolActive(tool.name, !tool.is_active)}
                        >
                          {tool.is_active ? '禁用' : '启用'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {!loading && tools.length === 0 && (
                <div className="empty-state">
                  <p>没有找到工具</p>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'history' && (
          <div className="tool-history-container">
            <div className="history-header">
              <h3>工具调用历史</h3>
              <button 
                className="clear-history-btn"
                onClick={handleClearToolHistory}
              >
                清空历史
              </button>
            </div>

            {toolHistory.length > 0 ? (
              <div className="history-list">
                {toolHistory.map((record) => (
                  <div key={record.id} className="history-item">
                    <div className="history-item-header">
                      <span className="history-tool-name">{record.tool_name}</span>
                      <span className="history-time">
                        {new Date(record.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="history-item-content">
                      <p className="history-parameters">
                        <strong>参数:</strong> {JSON.stringify(record.parameters)}
                      </p>
                      <p className="history-result">
                        <strong>结果:</strong> {JSON.stringify(record.result).substring(0, 200)}...
                      </p>
                      {record.execution_time && (
                        <p className="history-execution-time">
                          <strong>执行时间:</strong> {record.execution_time.toFixed(2)}秒
                        </p>
                      )}
                      {record.success !== undefined && (
                        <span className={`history-status ${record.success ? 'success' : 'error'}`}>
                          {record.success ? '成功' : '失败'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>暂无工具调用历史</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="tool-settings-container">
            <h3>工具设置</h3>
            
            <div className="settings-section">
              <h4>全局设置</h4>
              
              <div className="setting-item">
                <label className="setting-label">
                  <input
                    type="checkbox"
                    checked={toolSettings.enable_auto_execution || false}
                    onChange={(e) => setToolSettings(prev => ({
                      ...prev,
                      enable_auto_execution: e.target.checked
                    }))}
                  />
                  <span>启用自动执行（LLM调用工具时自动执行）</span>
                </label>
              </div>

              <div className="setting-item">
                <label className="setting-label">
                  <input
                    type="checkbox"
                    checked={toolSettings.show_tool_calls || false}
                    onChange={(e) => setToolSettings(prev => ({
                      ...prev,
                      show_tool_calls: e.target.checked
                    }))}
                  />
                  <span>显示工具调用详情</span>
                </label>
              </div>

              <div className="setting-item">
                <label className="setting-label">
                  <input
                    type="checkbox"
                    checked={toolSettings.enable_tool_logging || false}
                    onChange={(e) => setToolSettings(prev => ({
                      ...prev,
                      enable_tool_logging: e.target.checked
                    }))}
                  />
                  <span>启用工具调用日志</span>
                </label>
              </div>

              <div className="setting-item">
                <label className="setting-label">
                  <span>工具执行超时（秒）</span>
                  <input
                    type="number"
                    className="setting-input"
                    value={toolSettings.execution_timeout || 30}
                    onChange={(e) => setToolSettings(prev => ({
                      ...prev,
                      execution_timeout: parseInt(e.target.value)
                    }))}
                    min="1"
                    max="300"
                  />
                </label>
              </div>

              <div className="setting-item">
                <label className="setting-label">
                  <span>最大并发工具调用数</span>
                  <input
                    type="number"
                    className="setting-input"
                    value={toolSettings.max_concurrent_calls || 5}
                    onChange={(e) => setToolSettings(prev => ({
                      ...prev,
                      max_concurrent_calls: parseInt(e.target.value)
                    }))}
                    min="1"
                    max="20"
                  />
                </label>
              </div>
            </div>

            <div className="settings-actions">
              <button 
                className="save-settings-btn"
                onClick={() => handleSaveToolSettings(toolSettings)}
              >
                保存设置
              </button>
              <button 
                className="reset-settings-btn"
                onClick={handleResetToolSettings}
              >
                重置设置
              </button>
            </div>
          </div>
        )}
      </div>

      {showDetail && selectedTool && (
        <div className="tool-detail-modal">
          <div className="modal-overlay" onClick={handleCloseDetail}></div>
          <div className="modal-content">
            <div className="modal-header">
              <h2>{selectedTool.icon} {selectedTool.display_name}</h2>
              <button className="close-btn" onClick={handleCloseDetail}>
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="tool-info">
                <h3>工具描述</h3>
                <p>{selectedTool.description}</p>

                <div className="tool-meta-info">
                  <span>分类: {selectedTool.category}</span>
                  <span>版本: {selectedTool.version}</span>
                  <span>状态: {selectedTool.is_active ? '启用' : '禁用'}</span>
                  {selectedTool.author && <span>作者: {selectedTool.author}</span>}
                </div>

                {selectedTool.tags && selectedTool.tags.length > 0 && (
                  <div className="tool-tags">
                    <h4>标签</h4>
                    <div className="tags-container">
                      {selectedTool.tags.map((tag) => (
                        <span key={tag} className="tag">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="tool-parameters">
                  <h3>参数</h3>
                  {selectedTool.parameters && selectedTool.parameters.length > 0 ? (
                    <div className="parameters-list">
                      {selectedTool.parameters.map((param) => (
                        <div key={param.name} className="parameter-item">
                          <div className="parameter-header">
                            <span className="parameter-name">{param.name}</span>
                            <span className="parameter-type">{param.type}</span>
                            {param.required && (
                              <span className="parameter-required">必填</span>
                            )}
                          </div>
                          <p className="parameter-description">
                            {param.description}
                          </p>
                          {param.default !== undefined && (
                            <span className="parameter-default">
                              默认值: {JSON.stringify(param.default)}
                            </span>
                          )}
                          {param.enum && (
                            <div className="parameter-enum">
                              可选值: {param.enum.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p>此工具无需参数</p>
                  )}
                </div>
              </div>

              {executionResult && (
                <div className="execution-result">
                  <h3>执行结果</h3>
                  {executionResult.success ? (
                    <div className="result-success">
                      <p>执行成功！</p>
                      <p>执行时间: {executionResult.executionTime.toFixed(2)}秒</p>
                      <pre className="result-data">
                        {JSON.stringify(executionResult.result, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <div className="result-error">
                      <p>执行失败</p>
                      <p className="error-message">{executionResult.error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="cancel-btn" onClick={handleCloseDetail}>
                关闭
              </button>
              <button
                className="execute-btn"
                onClick={() => handleExecuteTool(selectedTool.name)}
                disabled={executingTool === selectedTool.name || !selectedTool.is_active}
              >
                {executingTool === selectedTool.name ? '执行中...' : '执行工具'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tool;
