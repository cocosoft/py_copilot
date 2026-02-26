import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  FaHome, FaComments, FaImage, FaVideo, FaMicrophoneAlt, 
  FaLanguage, FaCog, FaAngleLeft, FaAngleRight, FaTasks
} from 'react-icons/fa';

// 简化的导航栏组件，确保图标能正确显示
const Navbar = () => {
  // 使用 i18n 翻译
  const { t } = useTranslation();
  
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
      name: t('nav.home'), 
      icon: <FaHome className="nav-svg" />,
      iconCollapsed: <FaHome className="nav-svg" />
    },
    { 
      path: '/chat', 
      name: t('nav.chat'), 
      icon: <FaComments className="nav-svg" />,
      iconCollapsed: <FaComments className="nav-svg" />
    },
    { 
      path: '/task', 
      name: t('nav.tasks'), 
      icon: <FaTasks className="nav-svg" />,
      iconCollapsed: <FaTasks className="nav-svg" />
    },
    { 
      path: '/image', 
      name: t('nav.image'), 
      icon: <FaImage className="nav-svg" />,
      iconCollapsed: <FaImage className="nav-svg" />
    },
    { 
      path: '/video', 
      name: t('nav.video'), 
      icon: <FaVideo className="nav-svg" />,
      iconCollapsed: <FaVideo className="nav-svg" />
    },
    { 
      path: '/voice', 
      name: t('nav.voice'), 
      icon: <FaMicrophoneAlt className="nav-svg" />,
      iconCollapsed: <FaMicrophoneAlt className="nav-svg" />
    },
    { 
      path: '/translate', 
      name: t('nav.translate'), 
      icon: <FaLanguage className="nav-svg" />,
      iconCollapsed: <FaLanguage className="nav-svg" />
    }
  ];
  


  return (
    <nav className={`navbar ${collapsed ? 'collapsed' : ''}`}>
      <div className="navbar-header">
        <button 
          className="collapse-toggle" 
          onClick={toggleCollapse}
          title={collapsed ? t('nav.expand') : t('nav.collapse')}
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
        

      </div>
    </nav>
  );
};

export default Navbar;