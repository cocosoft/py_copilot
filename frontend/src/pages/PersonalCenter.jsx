import React from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import './help-center.css';

// 个人中心主页面
const PersonalCenterMain = () => {
  return (
    <div className="help-content">
      <div className="content-header">
        <h2>个人信息</h2>
        <p>管理您的个人资料和账户信息</p>
      </div>
      <div className="help-center-content">
        <div className="personal-info-section">
          <h3>个人资料</h3>
          <p>个人信息页面内容正在建设中...</p>
        </div>
      </div>
    </div>
  );
};

// 账单中心页面
const BillCenter = () => {
  return (
    <div className="help-content">
      <div className="content-header">
        <h2>账单中心</h2>
        <p>查看和管理您的账户账单</p>
      </div>
      <div className="bill-center-content">
        <div className="bill-section">
          <h3>账单信息</h3>
          <p>账单中心页面内容正在建设中...</p>
        </div>
      </div>
    </div>
  );
};

// 隐私设置页面
const PrivacySettings = () => {
  return (
    <div className="help-content">
      <div className="content-header">
        <h2>隐私设置</h2>
        <p>管理您的隐私偏好和数据保护设置</p>
      </div>
      <div className="privacy-settings-content">
        <div className="privacy-section">
          <h3>隐私选项</h3>
          <p>隐私设置页面内容正在建设中...</p>
        </div>
      </div>
    </div>
  );
};

// 通知设置页面
const NotificationSettings = () => {
  return (
    <div className="help-content">
      <div className="content-header">
        <h2>通知设置</h2>
        <p>配置您的通知偏好和接收方式</p>
      </div>
      <div className="notification-settings-content">
        <div className="notification-section">
          <h3>通知选项</h3>
          <p>通知设置页面内容正在建设中...</p>
        </div>
      </div>
    </div>
  );
};

// 主个人中心组件，包含侧边栏和路由
const PersonalCenter = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;

  const menuItems = [
    { path: '/personal', label: '个人信息', component: PersonalCenterMain, icon: '👤' },
    { path: '/personal/bill', label: '账单中心', component: BillCenter, icon: '💳' },
    { path: '/personal/privacy', label: '隐私设置', component: PrivacySettings, icon: '🔒' },
    { path: '/personal/notification', label: '通知设置', component: NotificationSettings, icon: '🔔' },
  ];

  const isActive = (path) => {
    return currentPath === path;
  };

  return (
    <div className="help-center-container">
      <div className="help-header">
        <h1>个人中心</h1>
        <p>管理您的账户、通知、隐私和账单设置</p>
      </div>
      <div className="help-content-wrapper">
        {/* 左侧导航菜单 */}
        <div className="help-sidebar">
          <nav className="help-nav">
            {menuItems.map((item) => (
              <button
                key={item.path}
                className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
                onClick={() => navigate(item.path)}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-text">{item.label}</span>
              </button>
            ))}
          </nav>
        </div>
        {/* 右侧内容区域 */}
        <div className="help-main">
          <Routes>
            {menuItems.map((item) => (
              <Route key={item.path} path={item.path.replace('/personal', '')} element={<item.component />} />
            ))}
          </Routes>
        </div>
      </div>
    </div>
  );
};

export default PersonalCenter;