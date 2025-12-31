import ApiKeyUpdater from './components/ApiKeyUpdater';
import { BrowserRouter as Router, NavLink, Route, Routes, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import { SupplierProvider } from './contexts/SupplierContext';
import AppRoutes from './routes';
import LoginForm from './components/LoginForm';
import { isAuthenticated } from './utils/authUtils';

function App() {
  return (
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
  );
}

// 主应用组件（需要认证）
function MainApp() {
  return (
    <div className="app-container">
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
            title="用户"
          >
            <span className="user-icon">👤</span>
            <span className="user-text">用户</span>
          </NavLink>
          <NavLink 
            to="/settings" 
            className="header-user-button"
            title="设置"
          >
            <span className="user-icon">⚙️</span>
            <span className="user-text">设置</span>
          </NavLink>
          <NavLink 
            to="/help" 
            className="header-user-button"
            title="帮助"
          >
            <span className="user-icon">❓</span>
            <span className="user-text">帮助</span>
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