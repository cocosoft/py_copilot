/**
 * 统一导航结构组件
 *
 * 设计统一的导航结构，保持现有设计风格
 *
 * 任务编号: Phase2-Week5
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import React, { useState, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { create } from 'zustand';
import { Button, Badge } from '../../UnifiedComponentLibrary';

/**
 * 导航状态管理
 */
export const useNavigationStore = create((set, get) => ({
  // 导航配置
  navigationConfig: {
    collapsed: false,
    activeItem: null,
    expandedGroups: [],
  },

  // 通知
  notifications: [],

  // 设置导航配置
  setNavigationConfig: (config) => {
    set((state) => ({
      navigationConfig: { ...state.navigationConfig, ...config },
    }));
  },

  // 切换侧边栏
  toggleSidebar: () => {
    set((state) => ({
      navigationConfig: {
        ...state.navigationConfig,
        collapsed: !state.navigationConfig.collapsed,
      },
    }));
  },

  // 展开/收起分组
  toggleGroup: (groupId) => {
    set((state) => {
      const expanded = state.navigationConfig.expandedGroups;
      const newExpanded = expanded.includes(groupId)
        ? expanded.filter((id) => id !== groupId)
        : [...expanded, groupId];

      return {
        navigationConfig: {
          ...state.navigationConfig,
          expandedGroups: newExpanded,
        },
      };
    });
  },

  // 添加通知
  addNotification: (notification) => {
    set((state) => ({
      notifications: [
        ...state.notifications,
        {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          read: false,
          ...notification,
        },
      ],
    }));
  },

  // 标记通知为已读
  markNotificationAsRead: (id) => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    }));
  },

  // 清除所有通知
  clearNotifications: () => {
    set({ notifications: [] });
  },

  // 未读通知数
  getUnreadCount: () => {
    return get().notifications.filter((n) => !n.read).length;
  },
}));

/**
 * 导航菜单配置
 */
const navigationMenuConfig = [
  {
    id: 'dashboard',
    label: '仪表盘',
    icon: '📊',
    path: '/',
    exact: true,
  },
  {
    id: 'documents',
    label: '文档管理',
    icon: '📄',
    path: '/documents',
    badge: null,
  },
  {
    id: 'knowledge',
    label: '知识库',
    icon: '🧠',
    children: [
      { id: 'knowledge-graph', label: '知识图谱', path: '/knowledge/graph', icon: '🕸️' },
      { id: 'knowledge-search', label: '语义搜索', path: '/knowledge/search', icon: '🔍' },
      { id: 'knowledge-hierarchy', label: '层次管理', path: '/knowledge/hierarchy', icon: '📁' },
    ],
  },
  {
    id: 'entities',
    label: '实体管理',
    icon: '🏷️',
    children: [
      { id: 'entity-recognition', label: '实体识别', path: '/entities/recognition', icon: '🔍' },
      { id: 'entity-list', label: '实体列表', path: '/entities/list', icon: '📋' },
      { id: 'entity-relations', label: '关系管理', path: '/entities/relations', icon: '🔗' },
    ],
  },
  {
    id: 'analytics',
    label: '数据分析',
    icon: '📈',
    children: [
      { id: 'analytics-overview', label: '概览', path: '/analytics/overview', icon: '📊' },
      { id: 'analytics-reports', label: '报告', path: '/analytics/reports', icon: '📑' },
    ],
  },
  {
    id: 'settings',
    label: '系统设置',
    icon: '⚙️',
    path: '/settings',
  },
];

/**
 * 导航项组件
 * @param {Object} props - 组件属性
 * @param {Object} props.item - 导航项数据
 * @param {boolean} props.collapsed - 是否折叠
 * @param {boolean} props.active - 是否激活
 * @param {Function} props.onClick - 点击回调
 */
const NavigationItem = ({ item, collapsed, active, onClick }) => {
  const hasChildren = item.children && item.children.length > 0;
  const { navigationConfig, toggleGroup } = useNavigationStore();
  const isExpanded = navigationConfig.expandedGroups.includes(item.id);

  const handleClick = useCallback(() => {
    if (hasChildren) {
      toggleGroup(item.id);
    } else {
      onClick?.(item);
    }
  }, [hasChildren, item, onClick, toggleGroup]);

  return (
    <div className={`navigation-item ${active ? 'active' : ''} ${hasChildren ? 'has-children' : ''}`}>
      <Link
        to={item.path || '#'}
        className="nav-link"
        onClick={handleClick}
        title={collapsed ? item.label : undefined}
      >
        <span className="nav-icon">{item.icon}</span>
        {!collapsed && (
          <>
            <span className="nav-label">{item.label}</span>
            {item.badge && (
              <Badge variant="danger" size="sm">
                {item.badge}
              </Badge>
            )}
            {hasChildren && (
              <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>
                ▼
              </span>
            )}
          </>
        )}
      </Link>

      {/* 子菜单 */}
      {hasChildren && !collapsed && isExpanded && (
        <div className="sub-menu">
          {item.children.map((child) => (
            <Link
              key={child.id}
              to={child.path}
              className="sub-nav-link"
              title={child.label}
            >
              <span className="sub-nav-icon">{child.icon}</span>
              <span className="sub-nav-label">{child.label}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * 面包屑组件
 * @param {Object} props - 组件属性
 * @param {Array} props.items - 面包屑项
 */
const Breadcrumb = ({ items = [] }) => {
  return (
    <nav className="breadcrumb">
      {items.map((item, index) => (
        <span key={index} className="breadcrumb-item">
          {index > 0 && <span className="breadcrumb-separator">/</span>}
          {item.path ? (
            <Link to={item.path}>{item.label}</Link>
          ) : (
            <span className="breadcrumb-current">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
};

/**
 * 顶部导航栏组件
 * @param {Object} props - 组件属性
 * @param {Function} props.onMenuToggle - 菜单切换回调
 * @param {Function} props.onSearch - 搜索回调
 * @param {Function} props.onProfile - 个人资料回调
 */
const TopNavigation = ({ onMenuToggle, onSearch, onProfile }) => {
  const { notifications, getUnreadCount, toggleSidebar } = useNavigationStore();
  const unreadCount = getUnreadCount();
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <header className="top-navigation">
      <div className="nav-left">
        <button
          className="menu-toggle"
          onClick={() => {
            toggleSidebar();
            onMenuToggle?.();
          }}
        >
          ☰
        </button>
        <div className="logo">
          <span className="logo-icon">🧠</span>
          <span className="logo-text">知识库系统</span>
        </div>
      </div>

      <div className="nav-center">
        <div className="global-search">
          <input
            type="text"
            placeholder="全局搜索..."
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                onSearch?.(e.target.value);
              }
            }}
          />
          <button className="search-button">🔍</button>
        </div>
      </div>

      <div className="nav-right">
        {/* 通知 */}
        <div className="notification-wrapper">
          <button
            className="notification-button"
            onClick={() => setShowNotifications(!showNotifications)}
          >
            🔔
            {unreadCount > 0 && (
              <span className="notification-badge">{unreadCount}</span>
            )}
          </button>

          {showNotifications && (
            <div className="notification-dropdown">
              <div className="notification-header">
                <span>通知</span>
                <button onClick={() => useNavigationStore.getState().clearNotifications()}>
                  清除全部
                </button>
              </div>
              <div className="notification-list">
                {notifications.length === 0 ? (
                  <div className="notification-empty">暂无通知</div>
                ) : (
                  notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`notification-item ${notification.read ? 'read' : 'unread'}`}
                      onClick={() =>
                        useNavigationStore.getState().markNotificationAsRead(notification.id)
                      }
                    >
                      <div className="notification-title">{notification.title}</div>
                      <div className="notification-message">{notification.message}</div>
                      <div className="notification-time">
                        {new Date(notification.timestamp).toLocaleString()}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* 用户菜单 */}
        <div className="user-menu">
          <button className="user-button" onClick={onProfile}>
            <span className="user-avatar">👤</span>
            <span className="user-name">管理员</span>
          </button>
        </div>
      </div>
    </header>
  );
};

/**
 * 侧边导航栏组件
 * @param {Object} props - 组件属性
 * @param {Function} props.onItemClick - 项点击回调
 */
const SidebarNavigation = ({ onItemClick }) => {
  const location = useLocation();
  const { navigationConfig } = useNavigationStore();
  const { collapsed } = navigationConfig;

  const isActive = useCallback(
    (item) => {
      if (item.exact) {
        return location.pathname === item.path;
      }
      if (item.path) {
        return location.pathname.startsWith(item.path);
      }
      if (item.children) {
        return item.children.some((child) =>
          location.pathname.startsWith(child.path)
        );
      }
      return false;
    },
    [location]
  );

  return (
    <aside className={`sidebar-navigation ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-content">
        {navigationMenuConfig.map((item) => (
          <NavigationItem
            key={item.id}
            item={item}
            collapsed={collapsed}
            active={isActive(item)}
            onClick={onItemClick}
          />
        ))}
      </div>

      {/* 侧边栏底部 */}
      <div className="sidebar-footer">
        {!collapsed && (
          <div className="version-info">
            <span>版本 2.0.0</span>
          </div>
        )}
      </div>
    </aside>
  );
};

/**
 * 统一导航结构组件
 * @param {Object} props - 组件属性
 * @param {React.ReactNode} props.children - 子内容
 * @param {Array} props.breadcrumbItems - 面包屑项
 */
const UnifiedNavigation = ({ children, breadcrumbItems = [] }) => {
  const { navigationConfig } = useNavigationStore();

  return (
    <div className={`app-layout ${navigationConfig.collapsed ? 'sidebar-collapsed' : ''}`}>
      <TopNavigation />

      <div className="app-body">
        <SidebarNavigation />

        <main className="app-main">
          {breadcrumbItems.length > 0 && <Breadcrumb items={breadcrumbItems} />}
          <div className="main-content">{children}</div>
        </main>
      </div>
    </div>
  );
};

export default UnifiedNavigation;
export {
  useNavigationStore,
  TopNavigation,
  SidebarNavigation,
  Breadcrumb,
  NavigationItem,
  navigationMenuConfig,
};
