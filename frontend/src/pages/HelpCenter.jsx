
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import './help-center.css';
import About from './About';
import ApiManagement from './ApiManagement';

const HelpCenterMain = () => {
  return (
    <div className="help-content">
      <div className="content-header">
        <h2>帮助中心</h2>
        <p>获取Py Copilot的使用帮助和常见问题解答</p>
      </div>
      <div className="help-center-content">
        <section className="help-section">
          <h3>使用指南</h3>
          <p>帮助文件内容正在建设中...</p>
        </section>
        
        <section className="help-section">
          <h3>常见问题</h3>
          <p>常见问题内容正在建设中...</p>
        </section>
      </div>
    </div>
  );
};

const UpdateLogs = () => {
  // 模拟GitHub提交记录
  const mockCommits = [
    {
      id: '1',
      date: '2024-12-19',
      message: '完善帮助中心功能，添加四个子页面',
      author: '开发者团队',
      hash: 'abc123'
    },
    {
      id: '2',
      date: '2024-12-18',
      message: '优化模型管理界面，提升用户体验',
      author: '开发者团队',
      hash: 'def456'
    },
    {
      id: '3',
      date: '2024-12-17',
      message: '修复聊天功能的已知问题',
      author: '开发者团队',
      hash: 'ghi789'
    }
  ];

  return (
    <div className="help-content">
      <div className="content-header">
        <h2>更新日志</h2>
        <p>查看Py Copilot的最新功能更新和修复记录</p>
      </div>
      <div className="update-logs-container">
        {mockCommits.map((commit) => (
          <div key={commit.id} className="commit-item">
            <div className="commit-header">
              <span className="commit-hash">#{commit.hash}</span>
              <span className="commit-date">{commit.date}</span>
            </div>
            <div className="commit-message">{commit.message}</div>
            <div className="commit-author">{commit.author}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const Feedback = () => {
  return (
    <div className="help-content">
      <div className="content-header">
        <h2>问题反馈</h2>
        <p>有任何问题或建议，欢迎随时向我们反馈</p>
      </div>
      <div className="feedback-container">
        <form className="feedback-form">
          <div className="form-group">
            <label htmlFor="feedback-type">反馈类型</label>
            <select id="feedback-type" className="form-input">
              <option value="bug">功能异常</option>
              <option value="suggestion">功能建议</option>
              <option value="other">其他问题</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="feedback-content">反馈内容</label>
            <textarea id="feedback-content" className="form-input" rows="5" placeholder="请详细描述您遇到的问题或建议..."></textarea>
          </div>
          <div className="form-group">
            <label htmlFor="feedback-email">联系方式（选填）</label>
            <input type="email" id="feedback-email" className="form-input" placeholder="您的邮箱地址" />
          </div>
          <button type="submit" className="submit-btn">提交反馈</button>
        </form>
      </div>
    </div>
  );
};

const HelpCenter = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;

  const menuItems = [
    { path: '/help', label: '帮助中心', component: HelpCenterMain, icon: '📖' },
    { path: '/help/logs', label: '更新日志', component: UpdateLogs, icon: '📝' },
    { path: '/help/feedback', label: '问题反馈', component: Feedback, icon: '💬' },
    { path: '/help/api', label: 'API管理', component: ApiManagement, icon: '🔌' },
    { path: '/help/about', label: '关于我们', component: About, icon: 'ℹ️' },
  ];

  const isActive = (path) => {
    return currentPath === path;
  };

  return (
    <div className="help-center-container">
      <div className="help-header">
        <h1>帮助中心</h1>
        <p>欢迎来到Py Copilot的帮助中心，在这里，你可以找到有关如何使用Py Copilot的帮助文件和常见问题解答。</p>
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
            <Route path="/" element={<HelpCenterMain />} />
            <Route path="logs" element={<UpdateLogs />} />
            <Route path="feedback" element={<Feedback />} />
            <Route path="api" element={<ApiManagement />} />
            <Route path="about" element={<About />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

export default HelpCenter;