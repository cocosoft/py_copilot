import React from 'react';
import { Link } from 'react-router-dom';
import './home.css';

const Home = () => {
  return (
    <div className="home-container">
      <h1 className="page-title">欢迎使用 Py Copilot</h1>
      <div className="home-content">
        <div className="welcome-section">
          <h2>智能助手中心</h2>
          <p>Py Copilot 是您的私人智能助手，提供多种AI功能，帮助您提高工作效率。</p>
          <p>请从左侧菜单选择您需要的功能。</p>
        </div>
        
        <div className="features-grid">
          <FeatureCard 
            icon="💬" 
            title="聊天"
            description="与智能体进行自然语言对话"
            link="/chat"
          />
          <FeatureCard 
            icon="🤖" 
            title="智能体"
            description="管理和使用不同的AI智能体"
            link="/agents"
          />
          <FeatureCard 
            icon="🖼️" 
            title="图像"
            description="生成和处理图像内容"
            link="/image"
          />
          <FeatureCard 
            icon="🎬" 
            title="视频"
            description="视频生成和编辑功能"
            link="/video"
          />
          <FeatureCard 
            icon="🎤" 
            title="语音"
            description="语音识别和合成功能"
            link="/voice"
          />
          <FeatureCard 
            icon="🌐" 
            title="翻译"
            description="多语言翻译和语言识别"
            link="/translation"
          />
          <FeatureCard 
            icon="📚" 
            title="知识库"
            description="管理和查询您的知识库"
            link="/knowledge-base"
          />
          <FeatureCard 
            icon="🔧" 
            title="工具"
            description="实用工具集和功能扩展"
            link="/tools"
          />
          <FeatureCard 
            icon="⚙️" 
            title="设置"
            description="个性化设置和模型管理"
            link="/settings"
          />
        </div>
      </div>
    </div>
  );
};

// 功能卡片组件
const FeatureCard = ({ icon, title, description, link }) => {
  return (
    <Link to={link} className="feature-card">
      <div className="feature-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </Link>
  );
};

export default Home;