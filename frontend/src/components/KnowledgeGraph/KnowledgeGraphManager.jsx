/**
 * 知识图谱管理组件
 *
 * 知识库入口的核心组件，提供概览、实体管理、关系管理、可视化分析、批量构建等功能
 * 采用标签页设计，集成多个子组件
 */

import React, { useState, useEffect } from 'react';
import KnowledgeGraphDashboard from './KnowledgeGraphDashboard';
import EntityManagement from './EntityManagement';
import BatchBuildPanel from './BatchBuildPanel';
import GraphVisualization from './GraphVisualization';
import './KnowledgeGraphManager.css';

/**
 * 知识图谱管理主组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @param {string} props.knowledgeBaseName - 知识库名称
 * @returns {JSX.Element} 知识图谱管理界面
 */
const KnowledgeGraphManager = ({ knowledgeBaseId, knowledgeBaseName }) => {
  // 当前激活的标签页
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // 知识图谱统计信息
  const [graphStats, setGraphStats] = useState(null);
  
  // 加载状态
  const [loading, setLoading] = useState(false);

  // 标签页配置
  const tabs = [
    { 
      id: 'dashboard', 
      label: '概览', 
      icon: '📊',
      description: '查看知识图谱整体统计信息'
    },
    { 
      id: 'entities', 
      label: '实体管理', 
      icon: '🏷️',
      description: '管理知识库中的实体'
    },
    { 
      id: 'relations', 
      label: '关系管理', 
      icon: '🔗',
      description: '管理实体间的关系',
      disabled: true // 暂不实现
    },
    { 
      id: 'visualization', 
      label: '可视化', 
      icon: '🕸️',
      description: '可视化展示知识图谱'
    },
    { 
      id: 'batch-build', 
      label: '批量构建', 
      icon: '⚡',
      description: '批量为多个文档构建知识图谱'
    }
  ];

  /**
   * 加载知识图谱统计信息
   */
  const loadGraphStats = async () => {
    if (!knowledgeBaseId) return;
    
    setLoading(true);
    try {
      // TODO: 调用API获取统计信息
      // const response = await getKnowledgeBaseGraphStats(knowledgeBaseId);
      // setGraphStats(response.data);
      
      // Mock数据
      setTimeout(() => {
        setGraphStats({
          entities_count: 156,
          relationships_count: 289,
          entity_types_count: 8,
          relationship_types_count: 12,
          coverage: 0.78,
          last_updated: new Date().toISOString()
        });
        setLoading(false);
      }, 500);
    } catch (error) {
      console.error('加载统计信息失败:', error);
      setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadGraphStats();
  }, [knowledgeBaseId]);

  /**
   * 渲染标签页内容
   * @returns {JSX.Element} 当前标签页的内容
   */
  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <KnowledgeGraphDashboard 
            knowledgeBaseId={knowledgeBaseId}
            knowledgeBaseName={knowledgeBaseName}
            stats={graphStats}
            loading={loading}
            onRefresh={loadGraphStats}
          />
        );
      
      case 'entities':
        return (
          <EntityManagement 
            knowledgeBaseId={knowledgeBaseId}
          />
        );
      
      case 'relations':
        return (
          <div className="placeholder-panel">
            <span className="placeholder-icon">🔗</span>
            <h3>关系管理</h3>
            <p>功能开发中，敬请期待...</p>
          </div>
        );
      
      case 'visualization':
        return (
          <GraphVisualization 
            knowledgeBaseId={knowledgeBaseId}
          />
        );
      
      case 'batch-build':
        return (
          <BatchBuildPanel 
            knowledgeBaseId={knowledgeBaseId}
            onBuildComplete={loadGraphStats}
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="knowledge-graph-manager">
      {/* 头部区域 */}
      <div className="manager-header">
        <div className="header-info">
          <h2 className="kb-name">{knowledgeBaseName}</h2>
          <p className="kb-subtitle">知识图谱管理</p>
        </div>
        
        {graphStats && (
          <div className="header-stats">
            <div className="stat-item">
              <span className="stat-value">{graphStats.entities_count}</span>
              <span className="stat-label">实体</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{graphStats.relationships_count}</span>
              <span className="stat-label">关系</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{Math.round(graphStats.coverage * 100)}%</span>
              <span className="stat-label">覆盖率</span>
            </div>
          </div>
        )}
      </div>

      {/* 标签页导航 */}
      <div className="manager-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''} ${tab.disabled ? 'disabled' : ''}`}
            onClick={() => !tab.disabled && setActiveTab(tab.id)}
            title={tab.description}
            disabled={tab.disabled}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
            {tab.disabled && <span className="coming-soon">开发中</span>}
          </button>
        ))}
      </div>

      {/* 标签页内容区域 */}
      <div className="manager-content">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default KnowledgeGraphManager;
