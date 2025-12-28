import React, { useState, useEffect } from 'react';
import { capabilityApi } from '../../utils/api/capabilityApi';
import { categoryApi } from '../../utils/api/categoryApi';
import '../../styles/CapabilityManagement.css';

const CategoryDefaultCapabilityManagement = () => {
  const [categories, setCategories] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [defaultCapabilities, setDefaultCapabilities] = useState([]);
  const [availableCapabilities, setAvailableCapabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // 加载分类和能力数据
  useEffect(() => {
    loadCategoriesAndCapabilities();
  }, []);

  const loadCategoriesAndCapabilities = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 并行加载分类和能力数据
      const [categoriesByDimensionResponse, capabilitiesResponse] = await Promise.all([
        categoryApi.getCategoriesByDimension(),
        capabilityApi.getAll()
      ]);
      
      // 直接获取tasks维度的分类
      const taskTypeCategories = categoriesByDimensionResponse.tasks || [];
      
      setCategories(taskTypeCategories);
      
      // 处理能力数据
      const processedCapabilities = Array.isArray(capabilitiesResponse?.capabilities)
        ? capabilitiesResponse.capabilities
        : Array.isArray(capabilitiesResponse) ? capabilitiesResponse : [];
      setCapabilities(processedCapabilities);
      
      // 默认选择第一个分类
      if (taskTypeCategories.length > 0) {
        handleCategorySelect(taskTypeCategories[0].id);
      }
    } catch (err) {
      console.error('加载数据失败:', err);
      setError('加载分类和能力数据失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 处理分类选择
  const handleCategorySelect = async (categoryId) => {
    try {
      setLoading(true);
      setError(null);
      setSelectedCategory(categoryId);
      
      // 获取该分类的默认能力
      const defaultCapabilitiesResponse = await capabilityApi.getDefaultCapabilitiesByCategory(categoryId);
      const processedDefaults = Array.isArray(defaultCapabilitiesResponse?.data)
        ? defaultCapabilitiesResponse.data
        : Array.isArray(defaultCapabilitiesResponse) ? defaultCapabilitiesResponse : [];
      setDefaultCapabilities(processedDefaults);
      
      // 更新可用能力列表（排除已选的默认能力）
      updateAvailableCapabilities(processedDefaults);
    } catch (err) {
      console.error(`获取分类 ${categoryId} 的默认能力失败:`, err);
      setError('获取默认能力失败，请重试');
      setDefaultCapabilities([]);
      updateAvailableCapabilities([]);
    } finally {
      setLoading(false);
    }
  };

  // 更新可用能力列表
  const updateAvailableCapabilities = (selectedDefaults) => {
    const defaultIds = selectedDefaults.map(cap => cap.id);
    const available = capabilities.filter(cap => !defaultIds.includes(cap.id));
    setAvailableCapabilities(available);
  };

  // 搜索能力
  const filteredAvailableCapabilities = availableCapabilities.filter(capability => {
    const searchLower = searchTerm.toLowerCase();
    return (
      capability.display_name?.toLowerCase().includes(searchLower) ||
      capability.name?.toLowerCase().includes(searchLower) ||
      capability.capability_type?.toLowerCase().includes(searchLower)
    );
  });

  // 高亮搜索结果
  const highlightSearchTerm = (text, searchTerm) => {
    if (!searchTerm || !text) return text;
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.split(regex).map((part, index) =>
      regex.test(part) ? <mark key={index} className="search-highlight">{part}</mark> : part
    );
  };

  // 清空搜索
  const clearSearch = () => {
    setSearchTerm('');
  };

  // 添加能力到默认列表
  const addToDefault = (capability) => {
    const newDefaultCapabilities = [...defaultCapabilities, capability];
    setDefaultCapabilities(newDefaultCapabilities);
    updateAvailableCapabilities(newDefaultCapabilities);
    setSearchTerm('');
  };

  // 从默认列表移除能力
  const removeFromDefault = (capabilityId) => {
    const newDefaultCapabilities = defaultCapabilities.filter(cap => cap.id !== capabilityId);
    setDefaultCapabilities(newDefaultCapabilities);
    updateAvailableCapabilities(newDefaultCapabilities);
  };

  // 保存默认能力设置
  const saveDefaultCapabilities = async () => {
    if (!selectedCategory) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // 获取默认能力的ID列表
      const defaultCapabilityIds = defaultCapabilities.map(cap => cap.id);
      
      // 调用API保存设置
      await capabilityApi.setDefaultCapabilities(selectedCategory, defaultCapabilityIds);
      
      setSuccess('保存默认能力设置成功');
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('保存默认能力设置失败:', err);
      setError('保存默认能力设置失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !categories.length && !capabilities.length) {
    return (
      <div className="category-default-capability-management">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>正在加载分类和能力数据...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="category-default-capability-management">
      <div className="section-header">
        <h3>分类默认能力管理</h3>
        <div className="category-count">
          共 {categories.length} 个分类
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          ⚠️ {error}
          <button onClick={() => setError(null)} className="btn btn-small">×</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          ✅ {success}
          <button onClick={() => setSuccess(null)} className="btn btn-small">×</button>
        </div>
      )}

      {/* 加载指示器 */}
      {loading && categories.length === 0 && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>加载中，请稍候...</p>
        </div>
      )}

      {/* 分类选择器 */}
      {categories.length > 0 && (
        <div className="category-selector">
          <label htmlFor="category-select">选择分类:</label>
          <select
            id="category-select"
            value={selectedCategory || ''}
            onChange={(e) => handleCategorySelect(parseInt(e.target.value))}
          >
            <option value="">请选择分类</option>
            {categories.map(category => (
              <option key={category.id} value={category.id}>
                {category.display_name || category.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {selectedCategory && (
        <div className="default-capability-config">
          <div className="config-header">
            <div>
              <h4>默认能力配置</h4>
              <div className="capability-count-info">
                当前已设置 {defaultCapabilities.length} 个默认能力
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={saveDefaultCapabilities}
              disabled={loading || defaultCapabilities.length === 0}
            >
              {loading ? (
                <>
                  <div className="spinner-small"></div>
                  保存中...
                </>
              ) : '保存设置'}
            </button>
          </div>

          <div className="config-content">
            {/* 可用能力列表 */}
            <div className="capability-section">
              <h5>可用能力 ({filteredAvailableCapabilities.length})</h5>
              <div className="search-box">
                <input
                  type="text"
                  placeholder="搜索能力名称、类型..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  autoComplete="off"
                  aria-label="搜索能力"
                />
                {searchTerm && (
                  <button
                    className="search-clear-btn"
                    onClick={clearSearch}
                    title="清空搜索"
                    aria-label="清空搜索"
                  >
                    ×
                  </button>
                )}
              </div>
              <div className="capability-list">
                {filteredAvailableCapabilities.length === 0 ? (
                  <div className="empty-state">
                    {searchTerm ? '没有匹配的能力' : '没有更多可用能力'}
                  </div>
                ) : (
                  filteredAvailableCapabilities.map(capability => (
                    <div key={capability.id} className="capability-item">
                      <div className="capability-info">
                        <span className="capability-name">
                          {highlightSearchTerm(capability.display_name || capability.name, searchTerm)}
                        </span>
                        <span className="capability-type">
                          {highlightSearchTerm(capability.capability_type || '默认类型', searchTerm)}
                        </span>
                      </div>
                      <button
                        className="btn btn-small btn-primary"
                        onClick={() => addToDefault(capability)}
                        title="添加到默认能力"
                      >
                        + 添加
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* 默认能力列表 */}
            <div className="capability-section">
              <h5>默认能力 ({defaultCapabilities.length})</h5>
              <div className="capability-list">
                {defaultCapabilities.length === 0 ? (
                  <div className="empty-state">
                    <p>暂无默认能力</p>
                    <p className="hint-text">从左侧选择能力添加到默认列表</p>
                  </div>
                ) : (
                  defaultCapabilities.map(capability => (
                    <div key={capability.id} className="capability-item">
                      <div className="capability-info">
                        <span className="capability-name">{capability.display_name || capability.name}</span>
                        <span className="capability-type">{capability.capability_type || '默认类型'}</span>
                      </div>
                      <button
                        className="btn btn-small btn-danger"
                        onClick={() => removeFromDefault(capability.id)}
                        title="从默认能力中移除"
                      >
                        × 移除
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 空状态提示 */}
      {categories.length === 0 && !loading && (
        <div className="empty-state">
          <p>暂无分类数据</p>
          <p className="hint-text">请先创建分类后再进行配置</p>
        </div>
      )}
    </div>
  );
};

export default CategoryDefaultCapabilityManagement;