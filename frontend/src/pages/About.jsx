
import './about.css';

const About = () => {
  return (
    <div className="help-content">
      <div className="content-header">
        <h2>关于我们</h2>
        <p>Py Copilot - 您的私人智能助手</p>
      </div>
      
      <div className="about-content">
        <section className="about-intro">
          <div className="about-logo">
            <div className="logo-container">
              <img src="/app-logo.png" alt="Py Copilot Logo" />
            </div>
          </div>
          <p className="about-description">
            Py Copilot 是一款功能强大的您的私人智能助手，旨在帮助您提高工作效率，解决复杂问题，
            并提供智能化的自定义体验。我们的目标是让工作、娱乐变得更加简单、高效和愉快。
          </p>
        </section>
        
        <section className="about-features">
          <h3>核心功能</h3>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">💬</div>
              <h4>智能对话</h4>
              <p>与AI进行自然语言交互，获取代码建议和解决方案</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h4>智能体管理</h4>
              <p>创建和管理专用智能体，满足不同场景需求</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📚</div>
              <h4>知识库</h4>
              <p>构建个性化知识库，增强AI对您项目的理解</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔄</div>
              <h4>工作流</h4>
              <p>自动化复杂任务流程，提高工作效率</p>
            </div>
          </div>
        </section>
        
        <section className="about-team">
          <h3>我们的团队</h3>
          <p>Py Copilot 团队由一群热爱技术、富有创新精神的开发者和AI专家组成。
          我们致力于打造最优秀的编程助手工具，帮助开发者实现更多可能性。</p>
        </section>
        
        <section className="about-contact">
          <h3>联系我们</h3>
          <p>如果您有任何问题、建议或反馈，欢迎随时联系我们。</p>
          <div className="contact-info">
            <p><strong>电子邮件：</strong>support@pycopilot.com</p>
            <p><strong>GitHub：</strong>https://github.com/pycopilot</p>
          </div>
        </section>
        
        <section className="about-version">
          <h3>版本信息</h3>
          <p><strong>当前版本：</strong>1.0.0</p>
          <p><strong>更新日期：</strong>2024年</p>
        </section>
      </div>
    </div>
  );
};

export default About;