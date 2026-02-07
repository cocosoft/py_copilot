import React, { useState, useEffect } from 'react';
import { apiDocsService } from '../services/apiDocsService';
import './api-management.css';

const ApiManagement = () => {
  const [apiList, setApiList] = useState([]);
  const [filteredApiList, setFilteredApiList] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedModule, setSelectedModule] = useState('all');
  const [selectedMethod, setSelectedMethod] = useState('all');
  const [selectedApi, setSelectedApi] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [testParams, setTestParams] = useState('');
  const [pathParams, setPathParams] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [testError, setTestError] = useState(null);
  const [activeTab, setActiveTab] = useState('detail');
  const [favorites, setFavorites] = useState([]);
  const [showFavorites, setShowFavorites] = useState(false);
  const [favoriteStatus, setFavoriteStatus] = useState({});

  useEffect(() => {
    loadApiList();
    loadStats();
    loadFavorites();
  }, []);

  useEffect(() => {
    filterApiList();
  }, [apiList, searchKeyword, selectedModule, selectedMethod]);

  useEffect(() => {
    if (selectedApi) {
      checkFavoriteStatus(selectedApi);
    }
  }, [selectedApi]);

  const loadApiList = async () => {
    try {
      setLoading(true);
      const data = await apiDocsService.getApiList();
      setApiList(data);
    } catch (error) {
      console.error('加载API列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await apiDocsService.getApiStats();
      setStats(data);
    } catch (error) {
      console.error('加载统计信息失败:', error);
    }
  };

  const filterApiList = () => {
    let filtered = [...apiList];

    if (searchKeyword) {
      const keyword = searchKeyword.toLowerCase();
      filtered = filtered.filter(api =>
        api.path.toLowerCase().includes(keyword) ||
        api.summary.toLowerCase().includes(keyword) ||
        api.tags.some(tag => tag.toLowerCase().includes(keyword))
      );
    }

    if (selectedModule !== 'all') {
      filtered = filtered.filter(api => api.module === selectedModule);
    }

    if (selectedMethod !== 'all') {
      filtered = filtered.filter(api => api.method === selectedMethod);
    }

    setFilteredApiList(filtered);
  };

  const getMethodColor = (method) => {
    const colors = {
      GET: '#61affe',
      POST: '#49cc90',
      PUT: '#fca130',
      DELETE: '#f93e3e',
      PATCH: '#50e3c2'
    };
    return colors[method] || '#999';
  };

  const modules = ['all', ...new Set(apiList.map(api => api.module))];
  const methods = ['all', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

  const handleTestApi = async () => {
    if (!selectedApi) return;

    setTestLoading(true);
    setTestError(null);
    setTestResult(null);

    try {
      let requestData = null;
      if (testParams.trim()) {
        try {
          requestData = JSON.parse(testParams);
        } catch (e) {
          setTestError('JSON格式错误: ' + e.message);
          setTestLoading(false);
          return;
        }
      }

      let finalPath = selectedApi.path;

      if (pathParams.trim()) {
        try {
          const pathParamsObj = JSON.parse(pathParams);
          for (const [key, value] of Object.entries(pathParamsObj)) {
            finalPath = finalPath.replace(`{${key}}`, value);
          }
        } catch (e) {
          setTestError('路径参数JSON格式错误: ' + e.message);
          setTestLoading(false);
          return;
        }
      }

      const result = await apiDocsService.testApi(
        finalPath,
        selectedApi.method,
        requestData
      );
      setTestResult(result);
    } catch (error) {
      setTestError(error.message || '请求失败');
    } finally {
      setTestLoading(false);
    }
  };

  const handleResetTest = () => {
    setTestParams('');
    setPathParams('');
    setTestResult(null);
    setTestError(null);
  };

  const loadFavorites = async () => {
    try {
      const result = await apiDocsService.getFavorites();
      setFavorites(result.data || []);
    } catch (error) {
      console.error('加载收藏列表失败:', error);
    }
  };

  const checkFavoriteStatus = async (api) => {
    try {
      const result = await apiDocsService.checkFavorite(api.path, api.method);
      setFavoriteStatus(prev => ({
        ...prev,
        [`${api.path}-${api.method}`]: result.is_favorite
      }));
    } catch (error) {
      console.error('检查收藏状态失败:', error);
    }
  };

  const handleToggleFavorite = async (api) => {
    const key = `${api.path}-${api.method}`;
    const isFavorite = favoriteStatus[key];

    try {
      if (isFavorite) {
        await apiDocsService.removeFavorite(api.path, api.method);
        setFavoriteStatus(prev => ({
          ...prev,
          [key]: false
        }));
        loadFavorites();
      } else {
        await apiDocsService.addFavorite({
          api_path: api.path,
          api_method: api.method,
          api_summary: api.summary,
          api_module: api.module
        });
        setFavoriteStatus(prev => ({
          ...prev,
          [key]: true
        }));
        loadFavorites();
      }
    } catch (error) {
      console.error('切换收藏状态失败:', error);
      alert('操作失败，请重试');
    }
  };

  const handleSelectFavorite = (favorite) => {
    const api = apiList.find(a => a.path === favorite.api_path && a.method === favorite.api_method);
    if (api) {
      setSelectedApi(api);
      setActiveTab('detail');
      setShowFavorites(false);
    }
  };

  const exportToMarkdown = () => {
    const dataToExport = showFavorites ? favorites : filteredApiList;
    
    let markdown = '# API 文档\n\n';
    markdown += `导出时间: ${new Date().toLocaleString()}\n\n`;
    markdown += `总计: ${dataToExport.length} 个API\n\n---\n\n`;

    dataToExport.forEach((api, index) => {
      const apiData = api.path ? api : apiList.find(a => a.path === api.api_path && a.method === api.api_method);
      if (!apiData) return;

      markdown += `## ${index + 1}. ${apiData.method} ${apiData.path}\n\n`;
      
      if (apiData.summary) {
        markdown += `**描述**: ${apiData.summary}\n\n`;
      }
      
      if (apiData.description) {
        markdown += `**详细说明**: ${apiData.description}\n\n`;
      }
      
      markdown += `**模块**: ${apiData.module}\n\n`;
      
      if (apiData.tags && apiData.tags.length > 0) {
        markdown += `**标签**: ${apiData.tags.join(', ')}\n\n`;
      }
      
      if (apiData.request_params && Object.keys(apiData.request_params).length > 0) {
        markdown += `**请求参数**:\n\`\`\`json\n${JSON.stringify(apiData.request_params, null, 2)}\n\`\`\`\n\n`;
      }
      
      if (apiData.response_model && Object.keys(apiData.response_model).length > 0) {
        markdown += `**响应模型**:\n\`\`\`json\n${JSON.stringify(apiData.response_model, null, 2)}\n\`\`\`\n\n`;
      }
      
      markdown += '---\n\n';
    });

    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `api-docs-${Date.now()}.md`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToJSON = () => {
    const dataToExport = showFavorites ? favorites : filteredApiList;
    
    const exportData = {
      export_time: new Date().toISOString(),
      total: dataToExport.length,
      apis: dataToExport.map(api => {
        const apiData = api.path ? api : apiList.find(a => a.path === api.api_path && a.method === api.api_method);
        return apiData;
      }).filter(Boolean)
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `api-docs-${Date.now()}.json`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="api-management">
      <div className="api-header">
        <h2>API管理</h2>
        <div className="api-stats">
          <button
            className="favorite-toggle-button"
            onClick={() => setShowFavorites(!showFavorites)}
          >
            {showFavorites ? '显示全部' : `收藏 (${favorites.length})`}
          </button>
          {stats && (
            <span className="stat-item">
              总计: {stats.total} 个API
            </span>
          )}
        </div>
      </div>

      <div className="api-filters">
        <input
          type="text"
          className="search-input"
          placeholder="搜索API路径、描述或标签..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
        />
        <select
          className="filter-select"
          value={selectedModule}
          onChange={(e) => setSelectedModule(e.target.value)}
        >
          {modules.map(module => (
            <option key={module} value={module}>
              {module === 'all' ? '所有模块' : module}
            </option>
          ))}
        </select>
        <select
          className="filter-select"
          value={selectedMethod}
          onChange={(e) => setSelectedMethod(e.target.value)}
        >
          {methods.map(method => (
            <option key={method} value={method}>
              {method === 'all' ? '所有方法' : method}
            </option>
          ))}
        </select>
        <div className="export-buttons">
          <button className="export-button" onClick={exportToMarkdown}>
            导出 Markdown
          </button>
          <button className="export-button" onClick={exportToJSON}>
            导出 JSON
          </button>
        </div>
      </div>

      <div className="api-content">
        <div className="api-list">
          {loading ? (
            <div className="loading">加载中...</div>
          ) : (
            (showFavorites ? favorites.map((fav, index) => {
              const api = apiList.find(a => a.path === fav.api_path && a.method === fav.api_method);
              if (!api) return null;
              return (
                <div
                  key={index}
                  className={`api-item ${selectedApi === api ? 'active' : ''}`}
                  onClick={() => setSelectedApi(api)}
                >
                  <span
                    className="api-method"
                    style={{ backgroundColor: getMethodColor(api.method) }}
                  >
                    {api.method}
                  </span>
                  <span className="api-path">{api.path}</span>
                  <span className="api-summary">{api.summary}</span>
                  <button
                    className="favorite-button favorite-button-active"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleFavorite(api);
                    }}
                  >
                    ★
                  </button>
                </div>
              );
            }) : filteredApiList.map((api, index) => {
              const key = `${api.path}-${api.method}`;
              const isFavorite = favoriteStatus[key];
              return (
                <div
                  key={index}
                  className={`api-item ${selectedApi === api ? 'active' : ''}`}
                  onClick={() => setSelectedApi(api)}
                >
                  <span
                    className="api-method"
                    style={{ backgroundColor: getMethodColor(api.method) }}
                  >
                    {api.method}
                  </span>
                  <span className="api-path">{api.path}</span>
                  <span className="api-summary">{api.summary}</span>
                  <button
                    className={`favorite-button ${isFavorite ? 'favorite-button-active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleFavorite(api);
                    }}
                  >
                    {isFavorite ? '★' : '☆'}
                  </button>
                </div>
              );
            }))
          )}
        </div>

        {selectedApi && (
          <div className="api-detail">
            <div className="api-detail-tabs">
              <button
                className={`tab-button ${activeTab === 'detail' ? 'active' : ''}`}
                onClick={() => setActiveTab('detail')}
              >
                API详情
              </button>
              <button
                className={`tab-button ${activeTab === 'test' ? 'active' : ''}`}
                onClick={() => setActiveTab('test')}
              >
                API测试
              </button>
            </div>

            {activeTab === 'detail' && (
              <div className="tab-content">
                <h3>API详情</h3>
                <div className="detail-section">
                  <h4>基本信息</h4>
                  <div className="info-row">
                    <label>路径:</label>
                    <code>{selectedApi.path}</code>
                  </div>
                  <div className="info-row">
                    <label>方法:</label>
                    <span
                      className="method-badge"
                      style={{ backgroundColor: getMethodColor(selectedApi.method) }}
                    >
                      {selectedApi.method}
                    </span>
                  </div>
                  <div className="info-row">
                    <label>模块:</label>
                    <span>{selectedApi.module}</span>
                  </div>
                  <div className="info-row">
                    <label>标签:</label>
                    <div className="tags">
                      {selectedApi.tags && selectedApi.tags.length > 0 ? (
                        selectedApi.tags.map((tag, i) => (
                          <span key={i} className="tag">{tag}</span>
                        ))
                      ) : (
                        <span className="no-tags">无标签</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h4>描述</h4>
                  <p>{selectedApi.summary || '暂无描述'}</p>
                  {selectedApi.description && (
                    <p className="description-text">{selectedApi.description}</p>
                  )}
                </div>

                {selectedApi.request_params && Object.keys(selectedApi.request_params).length > 0 && (
                  <div className="detail-section">
                    <h4>请求参数</h4>
                    <pre>{JSON.stringify(selectedApi.request_params, null, 2)}</pre>
                  </div>
                )}

                {selectedApi.response_model && Object.keys(selectedApi.response_model).length > 0 && (
                  <div className="detail-section">
                    <h4>响应模型</h4>
                    <pre>{JSON.stringify(selectedApi.response_model, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'test' && (
              <div className="tab-content">
                <h3>API测试</h3>
                <div className="test-section">
                  <div className="test-info">
                    <div className="info-row">
                      <label>路径:</label>
                      <code>{selectedApi.path}</code>
                    </div>
                    <div className="info-row">
                      <label>方法:</label>
                      <span
                        className="method-badge"
                        style={{ backgroundColor: getMethodColor(selectedApi.method) }}
                      >
                        {selectedApi.method}
                      </span>
                    </div>
                  </div>

                  {selectedApi.path.includes('{') && (
                    <div className="test-params">
                      <label>路径参数 (JSON格式，用于替换路径中的 {'{xxx}'}):</label>
                      <textarea
                        className="test-params-input"
                        value={pathParams}
                        onChange={(e) => setPathParams(e.target.value)}
                        placeholder='{"supplier_id": 1}'
                        rows={3}
                      />
                    </div>
                  )}

                  <div className="test-params">
                    <label>请求参数 (JSON格式):</label>
                    <textarea
                      className="test-params-input"
                      value={testParams}
                      onChange={(e) => setTestParams(e.target.value)}
                      placeholder='{"key": "value"}'
                      rows={8}
                    />
                  </div>

                  <div className="test-actions">
                    <button
                      className="test-button test-button-primary"
                      onClick={handleTestApi}
                      disabled={testLoading}
                    >
                      {testLoading ? '测试中...' : '发送请求'}
                    </button>
                    <button
                      className="test-button test-button-secondary"
                      onClick={handleResetTest}
                      disabled={testLoading}
                    >
                      重置
                    </button>
                  </div>

                  {testError && (
                    <div className="test-result test-error">
                      <h4>错误信息</h4>
                      <pre>{testError}</pre>
                    </div>
                  )}

                  {testResult && (
                    <div className="test-result test-success">
                      <h4>响应结果</h4>
                      <pre>{JSON.stringify(testResult, null, 2)}</pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiManagement;
