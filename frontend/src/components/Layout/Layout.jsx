import React, { useState } from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import PropTypes from 'prop-types';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = ({
  children,
  sidebar,
  header,
  sidebarWidth = 240,
  sidebarCollapsedWidth = 64,
  sidebarCollapsed = false,
  headerHeight = 64,
  theme = 'light',
  className,
  ...props
}) => {
  const [collapsed, setCollapsed] = useState(sidebarCollapsed);

  const themeClasses = {
    light: 'bg-gray-50 text-gray-900',
    dark: 'bg-gray-900 text-white',
  };

  const headerComponent = header || (
    <Header>
      <h1 className="text-xl font-semibold">应用标题</h1>
    </Header>
  );

  const sidebarComponent = sidebar || (
    <Sidebar>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">A</span>
          </div>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h2 className="font-semibold text-gray-900">应用名称</h2>
              <p className="text-xs text-gray-500">副标题</p>
            </motion.div>
          )}
        </div>
      </div>
      
      <div className="flex-1 p-4">
        <nav className="space-y-2">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
            {!collapsed ? '菜单' : 'M'}
          </div>
          {[
            { icon: '🏠', label: '首页', active: true },
            { icon: '💬', label: '聊天' },
            { icon: '🤖', label: '模型' },
            { icon: '🛠️', label: '工具' },
            { icon: '⚙️', label: '设置' },
          ].map((item, index) => (
            <button
              key={index}
              className={classNames(
                'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                item.active
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <span className="text-lg">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </button>
          ))}
        </nav>
      </div>
    </Sidebar>
  );

  return (
    <div className={classNames('min-h-screen flex', themeClasses[theme], className)} {...props}>
      {/* Sidebar */}
      <div style={{ width: sidebarCollapsed ? sidebarCollapsedWidth : sidebarWidth }}>
        {sidebarComponent}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div style={{ height: headerHeight }}>
          {headerComponent}
        </div>

        {/* Page Content */}
        <motion.main
          className="flex-1 p-6 overflow-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {children}
        </motion.main>
      </div>
    </div>
  );
};

Layout.propTypes = {
  children: PropTypes.node,
  sidebar: PropTypes.node,
  header: PropTypes.node,
  sidebarWidth: PropTypes.number,
  sidebarCollapsedWidth: PropTypes.number,
  sidebarCollapsed: PropTypes.bool,
  headerHeight: PropTypes.number,
  theme: PropTypes.oneOf(['light', 'dark']),
  className: PropTypes.string,
};

export default Layout;