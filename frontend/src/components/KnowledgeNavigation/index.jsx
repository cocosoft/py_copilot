/**
 * 知识库导航组件
 *
 * 提供从现有知识库页面跳转到增强版功能的入口
 *
 * @module KnowledgeNavigation
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './styles.css';

/**
 * 知识库导航组件
 *
 * @component
 */
const KnowledgeNavigation = () => {
  const { t } = useTranslation(['knowledge', 'common']);
  const navigate = useNavigate();

  const navItems = [
    {
      key: 'documents',
      label: t('knowledge:documentManagement'),
      description: t('knowledge:documentManagementDesc'),
      icon: '📄',
      path: '/knowledge/enhanced',
      features: [t('knowledge:virtualList'), t('knowledge:stateManagement'), t('knowledge:requestCache')],
      color: '#4a90d9',
    },
    {
      key: 'vectorization',
      label: t('knowledge:vectorizationManagement'),
      description: t('knowledge:vectorizationManagementDesc'),
      icon: '🚀',
      path: '/knowledge/vectorization',
      features: [
        t('knowledge:qualityAssessment'),
        t('knowledge:batchWizard'),
        t('knowledge:vectorSpace3D'),
        t('knowledge:resourceMonitor'),
      ],
      color: '#52c41a',
    },
    {
      key: 'graph',
      label: t('knowledge:knowledgeGraph'),
      description: t('knowledge:knowledgeGraphDesc'),
      icon: '🕸️',
      path: '/knowledge/graph',
      features: [t('knowledge:unifiedViewer'), t('knowledge:associationNetwork')],
      color: '#722ed1',
    },
  ];

  return (
    <div className="knowledge-navigation">
      <div className="nav-header">
        <h2>{t('knowledge:enhancedFeatures')}</h2>
        <p className="nav-description">
          {t('knowledge:enhancedFeaturesDescription')}
        </p>
      </div>

      <div className="nav-grid">
        {navItems.map((item) => (
          <div
            key={item.key}
            className="nav-card"
            onClick={() => navigate(item.path)}
            style={{ '--card-color': item.color }}
          >
            <div className="nav-card-header">
              <span className="nav-icon">{item.icon}</span>
              <h3 className="nav-title">{item.label}</h3>
            </div>

            <p className="nav-description">{item.description}</p>

            <div className="nav-features">
              <span className="features-label">{t('knowledge:newFeatures')}:</span>
              <div className="features-list">
                {item.features.map((feature, index) => (
                  <span key={index} className="feature-tag">
                    {feature}
                  </span>
                ))}
              </div>
            </div>

            <div className="nav-action">
              <span className="action-text">{t('common:enter')} →</span>
            </div>
          </div>
        ))}
      </div>

      <div className="nav-footer">
        <p>{t('knowledge:optimizationComplete')}</p>
        <span className="version-badge">v2.0</span>
      </div>
    </div>
  );
};

export default KnowledgeNavigation;
