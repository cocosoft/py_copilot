/**
 * 能力中心页面
 *
 * 统一管理工具、技能和MCP能力的中心页面
 * 提供统一的展示、筛选、启用/禁用、测试、配置、查看详情功能
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { capabilityCenterApi } from '../services/capabilityCenterApi';
import { CapabilityCard } from '../components/CapabilityCenter/CapabilityCard';
import { CapabilityTestDialog } from '../components/CapabilityCenter/CapabilityTestDialog';
import { CapabilityConfigDialog } from '../components/CapabilityCenter/CapabilityConfigDialog';
import { CapabilityDetailDialog } from '../components/CapabilityCenter/CapabilityDetailDialog';
import './capability-center.css';

/**
 * 能力中心主组件
 */
export function CapabilityCenter() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // 状态管理
  const [activeTab, setActiveTab] = useState(0);
  const [capabilities, setCapabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  });

  // 筛选状态
  const [filters, setFilters] = useState({
    type: 'all',
    source: 'all',
    status: 'all',
    category: 'all',
    search: ''
  });

  // 通知状态
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

  // 分类列表
  const [categories, setCategories] = useState([]);

  // 对话框状态
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedCapability, setSelectedCapability] = useState(null);

  /**
   * 加载能力列表
   */
  const loadCapabilities = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const typeMap = ['all', 'tool', 'skill', 'mcp'];
      const params = {
        type: typeMap[activeTab] === 'all' ? undefined : typeMap[activeTab],
        source: filters.source === 'all' ? undefined : filters.source,
        status: filters.status === 'all' ? undefined : filters.status,
        category: filters.category === 'all' ? undefined : filters.category,
        search: filters.search || undefined,
        page: pagination.page,
        page_size: pagination.pageSize
      };

      const response = await capabilityCenterApi.getCapabilities(params);

      if (response.success) {
        setCapabilities(response.data.items || []);
        setPagination(prev => ({
          ...prev,
          total: response.data.total || 0,
          totalPages: response.data.total_pages || 0
        }));
      } else {
        setError(response.message || t('capabilityCenter.loadError'));
      }
    } catch (err) {
      setError(err.message || t('capabilityCenter.loadError'));
    } finally {
      setLoading(false);
    }
  }, [activeTab, filters, pagination.page, pagination.pageSize, t]);

  /**
   * 加载分类列表
   */
  const loadCategories = useCallback(async () => {
    try {
      const response = await capabilityCenterApi.getCategories();
      if (response.success) {
        setCategories(response.data || []);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    loadCapabilities();
    loadCategories();
  }, [loadCapabilities, loadCategories]);

  /**
   * 处理Tab切换
   */
  const handleTabChange = (index) => {
    setActiveTab(index);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  /**
   * 处理筛选变化
   */
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  /**
   * 处理搜索
   */
  const handleSearch = (e) => {
    e.preventDefault();
    loadCapabilities();
  };

  /**
   * 处理页码变化
   */
  const handlePageChange = (page) => {
    setPagination(prev => ({ ...prev, page }));
  };

  /**
   * 处理启用/禁用能力
   */
  const handleToggleCapability = async (capability) => {
    try {
      const newStatus = capability.status === 'active' ? 'disabled' : 'active';
      const enabled = newStatus === 'active';
      const response = await capabilityCenterApi.toggleCapability(
        capability.type,
        capability.id,
        enabled
      );

      if (response.success) {
        setSnackbar({
          open: true,
          message: t(`capabilityCenter.toggleSuccess.${newStatus}`),
          severity: 'success'
        });
        loadCapabilities();
      } else {
        setSnackbar({
          open: true,
          message: response.message || t('capabilityCenter.toggleError'),
          severity: 'error'
        });
      }
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message || t('capabilityCenter.toggleError'),
        severity: 'error'
      });
    }
  };

  /**
   * 处理测试能力
   */
  const handleTestCapability = (capability) => {
    setSelectedCapability(capability);
    setTestDialogOpen(true);
  };

  /**
   * 处理配置能力
   */
  const handleConfigCapability = (capability) => {
    setSelectedCapability(capability);
    setConfigDialogOpen(true);
  };

  /**
   * 处理查看详情
   */
  const handleDetailCapability = (capability) => {
    setSelectedCapability(capability);
    setDetailDialogOpen(true);
  };

  /**
   * 关闭测试对话框
   */
  const handleCloseTestDialog = () => {
    setTestDialogOpen(false);
    setSelectedCapability(null);
  };

  /**
   * 关闭配置对话框
   */
  const handleCloseConfigDialog = () => {
    setConfigDialogOpen(false);
    setSelectedCapability(null);
  };

  /**
   * 关闭详情对话框
   */
  const handleCloseDetailDialog = () => {
    setDetailDialogOpen(false);
    setSelectedCapability(null);
  };

  /**
   * 处理配置保存成功
   */
  const handleConfigSave = () => {
    loadCapabilities();
  };

  /**
   * 关闭通知
   */
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const tabs = [
    { id: 'all', label: t('capabilityCenter.tabs.all') },
    { id: 'tool', label: t('capabilityCenter.tabs.tools') },
    { id: 'skill', label: t('capabilityCenter.tabs.skills') },
    { id: 'mcp', label: t('capabilityCenter.tabs.mcp') }
  ];

  return (
    <div className="capability-center-container">
      <div className="capability-center-header">
        <div className="header-content">
          <div>
            <h1 className="page-title">{t('capabilityCenter.title')}</h1>
            <p className="page-description">{t('capabilityCenter.description')}</p>
          </div>
          <button
            className="dev-center-button"
            onClick={() => navigate('/dev-center')}
          >
            <span className="dev-center-icon">⚡</span>
            {t('devCenter.title')}
          </button>
        </div>
      </div>

      {/* Tab导航 */}
      <div className="capability-tabs">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            className={`capability-tab ${activeTab === index ? 'active' : ''}`}
            onClick={() => handleTabChange(index)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 筛选栏 */}
      <div className="capability-filters">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            className="search-input"
            placeholder={t('capabilityCenter.searchPlaceholder')}
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
          />
          <button type="submit" className="search-button">
            {t('search')}
          </button>
        </form>

        <div className="filter-controls">
          <select
            className="filter-select"
            value={filters.source}
            onChange={(e) => handleFilterChange('source', e.target.value)}
          >
            <option value="all">{t('capabilityCenter.filters.allSources')}</option>
            <option value="official">{t('capabilityCenter.filters.official')}</option>
            <option value="user">{t('capabilityCenter.filters.user')}</option>
            <option value="marketplace">{t('capabilityCenter.filters.marketplace')}</option>
          </select>

          <select
            className="filter-select"
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
          >
            <option value="all">{t('capabilityCenter.filters.allStatus')}</option>
            <option value="active">{t('capabilityCenter.filters.active')}</option>
            <option value="disabled">{t('capabilityCenter.filters.disabled')}</option>
          </select>

          <select
            className="filter-select"
            value={filters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
          >
            <option value="all">{t('capabilityCenter.filters.allCategories')}</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>

          <button
            className="refresh-button"
            onClick={loadCapabilities}
            disabled={loading}
          >
            {loading ? t('loading') : t('refresh')}
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="error-alert">
          {error}
        </div>
      )}

      {/* 能力列表 */}
      <div className="capabilities-grid">
        {loading ? (
          <div className="loading-state">{t('loading')}</div>
        ) : capabilities.length === 0 ? (
          <div className="empty-state">{t('capabilityCenter.noCapabilities')}</div>
        ) : (
          capabilities.map((capability, index) => (
            <CapabilityCard
              key={`${capability.type}-${capability.id}-${capability.name || ''}-${index}`}
              capability={capability}
              onToggle={handleToggleCapability}
              onTest={handleTestCapability}
              onConfig={handleConfigCapability}
              onDetail={handleDetailCapability}
            />
          ))
        )}
      </div>

      {/* 分页 */}
      {pagination.totalPages > 1 && (
        <div className="pagination">
          <button
            className="pagination-button"
            disabled={pagination.page === 1}
            onClick={() => handlePageChange(pagination.page - 1)}
          >
            {t('previous')}
          </button>
          <span className="pagination-info">
            {pagination.page} / {pagination.totalPages}
          </span>
          <button
            className="pagination-button"
            disabled={pagination.page === pagination.totalPages}
            onClick={() => handlePageChange(pagination.page + 1)}
          >
            {t('next')}
          </button>
        </div>
      )}

      {/* 通知 */}
      {snackbar.open && (
        <div className={`snackbar ${snackbar.severity}`}>
          {snackbar.message}
          <button className="snackbar-close" onClick={handleCloseSnackbar}>
            ×
          </button>
        </div>
      )}

      {/* 测试对话框 */}
      <CapabilityTestDialog
        isOpen={testDialogOpen}
        capability={selectedCapability}
        onClose={handleCloseTestDialog}
      />

      {/* 配置对话框 */}
      <CapabilityConfigDialog
        isOpen={configDialogOpen}
        capability={selectedCapability}
        onClose={handleCloseConfigDialog}
        onSave={handleConfigSave}
      />

      {/* 详情对话框 */}
      <CapabilityDetailDialog
        isOpen={detailDialogOpen}
        capability={selectedCapability}
        onClose={handleCloseDetailDialog}
      />
    </div>
  );
}

export default CapabilityCenter;
