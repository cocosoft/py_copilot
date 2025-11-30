import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';

// 简单的图标组件
const NavIcon = ({ name, isCollapsed = false }) => {
  // 这里使用简单的文本作为图标，实际项目中可以使用Font Awesome或Material Icons
  const iconMap = {
    home: '🏠',
    chat: '💬',
    agents: '🤖',
    image: '🖼️',
    video: '🎬',
    voice: '🎤',
    translation: '🌐',
    knowledge: '📚',
    workflow: '🔄',
    tools: '🔧',
    settings: '⚙️',
    model: '🧠',
    search: '🔍',
    collapse: '◀️',
    expand: '▶️'
  };
  
  // 确保图标始终显示，添加内联样式防止被隐藏
  return (
    <span 
      className="nav-icon" 
      style={{
        display: 'inline-block',
        visibility: 'visible',
        opacity: 1,
        minWidth: isCollapsed ? '36px' : '20px',
        textAlign: 'center',
        fontSize: isCollapsed ? '24px' : '18px',
        height: isCollapsed ? '36px' : 'auto',
        lineHeight: isCollapsed ? '36px' : 'auto',
        position: 'relative',
        zIndex: 10,
        flexShrink: 0, // 防止被压缩
        margin: isCollapsed ? '0 auto' : '0'
      }}
    >
      {iconMap[name] || '•'}
    </span>
  );
};

const Navbar = () => {
  // 添加导航栏收缩/展开状态
  const [collapsed, setCollapsed] = useState(false);
  
  // 切换导航栏状态
  const toggleCollapse = () => {
    setCollapsed(!collapsed);
  };
  
  // 主要导航项
  const mainNavItems = [
    { path: '/', name: '首页', icon: 'home' },
    { path: '/chat', name: '聊天', icon: 'chat' },
    { path: '/image', name: '图像', icon: 'image' },
    { path: '/video', name: '视频', icon: 'video' },
    { path: '/voice', name: '语音', icon: 'voice' },
    { path: '/translate', name: '翻译', icon: 'translation' }
  ];
  


  // 设置导航项
  const settingsItem = { path: '/settings', name: '设置', icon: 'settings' };

  return (
    <nav className={`navbar ${collapsed ? 'collapsed' : ''}`}>
      <div className="navbar-header">
        <button 
          className="collapse-toggle" 
          onClick={toggleCollapse}
          title={collapsed ? '展开导航栏' : '收缩导航栏'}
        >
          <NavIcon name={collapsed ? 'expand' : 'collapse'} />
        </button>
      </div>
      <div className="navbar-container">
        <ul className="nav-menu main-nav">
          {mainNavItems.map((item, index) => (
            <li key={index} className="nav-item">
              <NavLink 
                to={item.path} 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                title={collapsed ? item.name : ''}
              >
                <NavIcon name={item.icon} isCollapsed={collapsed} />
                <span>{item.name}</span>
              </NavLink>
            </li>
          ))}          
        </ul>
        
        {/* 底部设置项 */}
        <div className="nav-bottom">
          <li className="nav-item">
            <NavLink 
              to={settingsItem.path} 
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              title={collapsed ? settingsItem.name : ''}
            >
              <NavIcon name={settingsItem.icon} isCollapsed={collapsed} />
              <span>{settingsItem.name}</span>
            </NavLink>
            {/* 设置子菜单 */}
            {settingsItem.subItems && (
              <ul className="sub-menu">
                {settingsItem.subItems.map((subItem, subIndex) => (
                  <li key={subIndex} className="nav-item">
                    <NavLink 
                      to={subItem.path} 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                      title={collapsed ? subItem.name : ''}
                    >
                      <NavIcon name={subItem.icon} isCollapsed={collapsed} />
                      <span>{subItem.name}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            )}
          </li>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;