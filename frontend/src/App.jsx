import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ApiKeyUpdater from './components/ApiKeyUpdater';
import { BrowserRouter as Router, NavLink, Route, Routes, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import { SupplierProvider } from './contexts/SupplierContext';
import AppRoutes from './routes';
import LoginForm from './components/LoginForm';
import { isAuthenticated } from './utils/authUtils';
import { StoreProvider, StoreMonitor, useStateManager } from './utils/storeManager';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GlobalErrorBoundary from './components/UI/GlobalErrorBoundary';
import ErrorNotification from './components/UI/ErrorNotification';
import Notification from './components/UI/Notification';
import { request } from './utils/apiUtils';
import WorkspaceSelector from './components/WorkspaceSelector';

// 创建React Query客户端实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5分钟
    },
    mutations: {
      retry: 1,
    },
  },
});

function App() {
  return (
    <GlobalErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <StoreProvider>
          <Router
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
            <SupplierProvider>
              <Routes>
                {/* 登录页面路由 */}
                <Route path="/login" element={<LoginForm />} />
                
                {/* 主应用路由 - 暂时取消认证要求 */}
                <Route path="/*" element={<MainApp />} />
              </Routes>
            </SupplierProvider>
          </Router>
          
          {/* 开发环境下的状态监控 */}
          {process.env.NODE_ENV === 'development' && <StoreMonitor enabled={false} />}
        </StoreProvider>
      </QueryClientProvider>
    </GlobalErrorBoundary>
  );
}

// 主应用组件（需要认证）
function MainApp() {
  const { t, i18n } = useTranslation();
  const { t: tNav } = useTranslation('nav');
  const [isLanguageLoaded, setIsLanguageLoaded] = useState(false);
  
  // 从后端加载语言设置（不阻塞页面加载）
  useEffect(() => {
    const loadLanguageFromBackend = async () => {
      try {
        const result = await request('/v1/settings', {
          method: 'GET',
          timeout: 10000 // 减少超时时间到10秒
        });
        
        if (result.success && result.data?.general?.language) {
          const backendLanguage = result.data.general.language;
          // 如果后端语言与当前语言不同，则切换
          if (backendLanguage !== i18n.language) {
            i18n.changeLanguage(backendLanguage);
            localStorage.setItem('app-language', backendLanguage);
          }
        }
      } catch (error) {
        console.error('从后端加载语言设置失败:', error);
        // 如果后端加载失败，使用 localStorage 中的语言设置
        const savedLanguage = localStorage.getItem('app-language');
        if (savedLanguage && savedLanguage !== i18n.language) {
          i18n.changeLanguage(savedLanguage);
        }
      }
    };
    
    // 先使用 localStorage 中的语言设置，然后异步加载后端设置
    const savedLanguage = localStorage.getItem('app-language');
    if (savedLanguage && savedLanguage !== i18n.language) {
      i18n.changeLanguage(savedLanguage);
    }
    setIsLanguageLoaded(true);
    
    // 异步加载后端语言设置
    loadLanguageFromBackend();
  }, [i18n]);
  
  // 语言设置加载完成前显示加载状态
  if (!isLanguageLoaded) {
    return (
      <div className="app-container" style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        height: '100vh'
      }}>
        <div>Loading...</div>
      </div>
    );
  }
  
  return (
    <div className="app-container">
      <ErrorNotification />
      <Notification />
      <ApiKeyUpdater />
      
      {/* 添加独立的顶部标题栏 */}
      <header className="app-header">
        <div className="app-header-left">
          <a href="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
            <img src="/app-logo.png" alt="App Logo" className="app-logo" width="36" height="36" />
            <h1 style={{ marginLeft: '10px' }}>Py Copilot</h1>
          </a>
        </div>
        <div className="app-header-right">
          <NavLink
            to="/personal"
            className="header-user-button"
            title={tNav('personal')}
          >
            <span className="user-icon">👤</span>
            <span className="user-text">{tNav('personal')}</span>
          </NavLink>
          {/* 工作空间选择器 */}
          <div className="header-workspace-selector">
            <WorkspaceSelector showStorage={false} />
          </div>
          <NavLink
            to="/settings"
            className="header-user-button"
            title={tNav('settings')}
          >
            <span className="user-icon">⚙️</span>
            <span className="user-text">{tNav('settings')}</span>
          </NavLink>
          <NavLink
            to="/help"
            className="header-user-button"
            title={tNav('help')}
          >
            <span className="user-icon">❓</span>
            <span className="user-text">{tNav('help')}</span>
          </NavLink>
        </div>
      </header>
      <div className="app-body">
        <Navbar />
        <main className="main-content">
          <AppRoutes />
        </main>
      </div>
    </div>
  );
}

export default App;