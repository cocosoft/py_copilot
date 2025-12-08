import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  FaHome, FaComments, FaImage, FaVideo, FaMicrophoneAlt, 
  FaLanguage, FaCog, FaAngleLeft, FaAngleRight 
} from 'react-icons/fa';

// 简化的导航栏组件，确保图标能正确显示
const Navbar = () => {
  // 添加导航栏收缩/展开状态
  const [collapsed, setCollapsed] = useState(false);
  
  // 切换导航栏状态
  const toggleCollapse = () => {
    setCollapsed(!collapsed);
  };
  
  // 主要导航项，使用React Icons库
  const mainNavItems = [
    { 
      path: '/', 
      name: '首页', 
      icon: <FaHome className="nav-svg" />,
      iconCollapsed: <FaHome className="nav-svg" />
    },
    { 
      path: '/chat', 
      name: '聊天', 
      icon: <FaComments className="nav-svg" />,
      iconCollapsed: <FaComments className="nav-svg" />
    },
    { 
      path: '/image', 
      name: '图像', 
      icon: <FaImage className="nav-svg" />,
      iconCollapsed: <FaImage className="nav-svg" />
    },
    { 
      path: '/video', 
      name: '视频', 
      icon: <FaVideo className="nav-svg" />,
      iconCollapsed: <FaVideo className="nav-svg" />
    },
    { 
      path: '/voice', 
      name: '语音', 
      icon: <FaMicrophoneAlt className="nav-svg" />,
      iconCollapsed: <FaMicrophoneAlt className="nav-svg" />
    },
    { 
      path: '/translate', 
      name: '翻译', 
      icon: <FaLanguage className="nav-svg" />,
      iconCollapsed: <FaLanguage className="nav-svg" />
    }
  ];
  
  // 设置导航项
  const settingsItem = { 
    path: '/settings', 
    name: '设置', 
    icon: <FaCog className="nav-svg" />,
    iconCollapsed: <FaCog className="nav-svg" />
  };

  return (
    <nav className={`navbar ${collapsed ? 'collapsed' : ''}`}>
      <div className="navbar-header">
        <button 
          className="collapse-toggle" 
          onClick={toggleCollapse}
          title={collapsed ? '展开导航栏' : '收缩导航栏'}
        >
          {collapsed ? (
            <FaAngleRight className="nav-svg" />
          ) : (
            <FaAngleLeft className="nav-svg" />
          )}
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
                {collapsed ? item.iconCollapsed : item.icon}
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
              {collapsed ? settingsItem.iconCollapsed : settingsItem.icon}
              <span>{settingsItem.name}</span>
            </NavLink>
          </li>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;