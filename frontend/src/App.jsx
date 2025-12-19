import ApiKeyUpdater from './components/ApiKeyUpdater';
import { BrowserRouter as Router, NavLink } from 'react-router-dom';
import Navbar from './components/Navbar';
import { SupplierProvider } from './contexts/SupplierContext';
import AppRoutes from './routes';

function App() {
  return (
    <Router>
      <SupplierProvider>
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
      </SupplierProvider>
    </Router>
  );
}

export default App;