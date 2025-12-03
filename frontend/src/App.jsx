import ApiKeyUpdater from './components/ApiKeyUpdater';
import { BrowserRouter as Router } from 'react-router-dom';
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
            <a href="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
              <img src="/app-logo.png" alt="App Logo" className="app-logo" width="36" height="36" />
              <h1 style={{ marginLeft: '10px' }}>Py Copilot</h1>
            </a>
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