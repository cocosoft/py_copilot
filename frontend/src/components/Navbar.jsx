import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FaHome, FaComments, FaAngleLeft, FaAngleRight,
  FaToolbox, FaRobot, FaProjectDiagram, FaBrain, FaTasks
} from 'react-icons/fa';

// 简化的导航栏组件，确保图标能正确显示
const Navbar = () => {
  // 使用 i18n 翻译
  const { t } = useTranslation('nav');

  // 添加导航栏收缩/展开状态
  const [collapsed, setCollapsed] = useState(false);

  // 切换导航栏状态
  const toggleCollapse = () => {
    setCollapsed(!collapsed);
  };
  
  // 主要导航项，使用React Icons库
  // 根据 SETTINGS_MERGE_PROPOSAL_V8.md 的导航结构重构规划
  const mainNavItems = [
    {
      path: '/',
      name: t('home'),
      icon: <FaHome className="nav-svg" />,
      iconCollapsed: <FaHome className="nav-svg" />
    },
    {
      path: '/chat',
      name: t('chat'),
      icon: <FaComments className="nav-svg" />,
      iconCollapsed: <FaComments className="nav-svg" />
    },
    {
      path: '/task',
      name: t('tasks'),
      icon: <FaTasks className="nav-svg" />,
      iconCollapsed: <FaTasks className="nav-svg" />
    },
    {
      path: '/capability-center',
      name: t('capabilityCenter'),
      icon: <FaToolbox className="nav-svg" />,
      iconCollapsed: <FaToolbox className="nav-svg" />
    },
    {
      path: '/agents',
      name: t('agents'),
      icon: <FaRobot className="nav-svg" />,
      iconCollapsed: <FaRobot className="nav-svg" />
    },
    {
      path: '/workflow',
      name: t('workflow'),
      icon: <FaProjectDiagram className="nav-svg" />,
      iconCollapsed: <FaProjectDiagram className="nav-svg" />
    },
    {
      path: '/knowledge',
      name: t('knowledge'),
      icon: <FaBrain className="nav-svg" />,
      iconCollapsed: <FaBrain className="nav-svg" />
    }
    // 注意：设置已在顶部标题栏中，不在导航栏重复显示
  ];
  


  return (
    <nav className={`navbar ${collapsed ? 'collapsed' : ''}`}>
      <div className="navbar-header">
        <button 
          className="collapse-toggle" 
          onClick={toggleCollapse}
          title={collapsed ? t('expand') : t('collapse')}
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
                <span className="nav-icon">
                  {collapsed ? item.iconCollapsed : item.icon}
                </span>
                <span className="nav-text">{item.name}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
