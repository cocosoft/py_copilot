import React from 'react';
import { NavLink } from 'react-router-dom';

// 简单的图标组件
const NavIcon = ({ name }) => {
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
    search: '🔍'
  };
  
  return <span className="nav-icon">{iconMap[name] || '•'}</span>;
};

const Navbar = () => {
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
    <nav className="navbar">
      <h2>Py Copilot</h2>
      <div className="navbar-container">
        <ul className="nav-menu main-nav">
          {mainNavItems.map((item, index) => (
            <li key={index} className="nav-item">
              <NavLink 
                to={item.path} 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <NavIcon name={item.icon} />
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
            >
              <NavIcon name={settingsItem.icon} />
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
                    >
                      <NavIcon name={subItem.icon} />
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