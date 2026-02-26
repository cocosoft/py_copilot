import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './home.css';

const Home = () => {
  const { t } = useTranslation();
  
  return (
    <div className="home-container">
      <h1 className="page-title">{t('common.home.welcome')}</h1>
      <div className="home-content">
        <div className="welcome-section">
          <h2>{t('common.home.subtitle')}</h2>
          <p>{t('common.home.description1')}</p>
          <p>{t('common.home.description2')}</p>
        </div>
        
        <div className="features-grid">
          <FeatureCard 
            icon="💬" 
            title={t('common.home.features.chat.title')}
            description={t('common.home.features.chat.description')}
            link="/chat"
          />
          <FeatureCard 
            icon="🤖" 
            title={t('common.home.features.agents.title')}
            description={t('common.home.features.agents.description')}
            link="/agents"
          />
          <FeatureCard 
            icon="🖼️" 
            title={t('common.home.features.image.title')}
            description={t('common.home.features.image.description')}
            link="/image"
          />
          <FeatureCard 
            icon="🎬" 
            title={t('common.home.features.video.title')}
            description={t('common.home.features.video.description')}
            link="/video"
          />
          <FeatureCard 
            icon="🎤" 
            title={t('common.home.features.voice.title')}
            description={t('common.home.features.voice.description')}
            link="/voice"
          />
          <FeatureCard 
            icon="🌐" 
            title={t('common.home.features.translate.title')}
            description={t('common.home.features.translate.description')}
            link="/translate"
          />
          <FeatureCard 
            icon="⚙️" 
            title={t('common.home.features.settings.title')}
            description={t('common.home.features.settings.description')}
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