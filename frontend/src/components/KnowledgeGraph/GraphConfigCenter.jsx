/**
 * 知识图谱配置中心组件
 *
 * 整合所有知识图谱相关的配置功能：
 * - 实体类型配置
 * - 关系类型配置
 * - 提取策略配置
 * - 术语词典配置
 * - 质量规则配置
 * - 提取测试
 */

import React, { useState } from 'react';
import EntityConfigUnified from './EntityConfigUnified';
import RelationTypeConfig from './RelationTypeConfig';
import ExtractionStrategyConfig from './ExtractionStrategyConfig';
import QualityRuleConfig from './QualityRuleConfig';
import './GraphConfigCenter.css';



/**
 * 知识图谱配置中心主组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @returns {JSX.Element} 配置中心界面
 */
const GraphConfigCenter = ({ knowledgeBaseId }) => {
  // 当前激活的配置标签页
  const [activeConfigTab, setActiveConfigTab] = useState('entity-types');

  // 配置标签页配置
  const configTabs = [
    {
      id: 'entity-types',
      label: '实体配置',
      icon: '🏷️',
      description: '配置实体类型、提取规则和术语词典'
    },
    {
      id: 'relation-types',
      label: '关系配置',
      icon: '🔗',
      description: '配置实体间的关系类型'
    },
    {
      id: 'extraction',
      label: '提取策略',
      icon: '⚡',
      description: '配置实体和关系的提取策略'
    },
    {
      id: 'quality',
      label: '质量规则',
      icon: '✅',
      description: '配置知识图谱质量检查规则'
    }
  ];

  /**
   * 渲染配置标签页内容
   * @returns {JSX.Element} 当前配置标签页的内容
   */
  const renderConfigContent = () => {
    switch (activeConfigTab) {
      case 'entity-types':
        return <EntityConfigUnified />;

      case 'relation-types':
        return <RelationTypeConfig knowledgeBaseId={knowledgeBaseId} />;

      case 'extraction':
        return <ExtractionStrategyConfig />;

      case 'quality':
        return <QualityRuleConfig />;

      default:
        return <EntityConfigUnified />;
    }
  };

  return (
    <div className="graph-config-center">
      {/* 配置标签页导航 */}
      <div className="config-tabs-nav">
        {configTabs.map(tab => (
          <button
            key={tab.id}
            className={`config-tab-btn ${activeConfigTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveConfigTab(tab.id)}
            title={tab.description}
          >
            <span className="config-tab-icon">{tab.icon}</span>
            <span className="config-tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* 配置内容区域 */}
      <div className="config-content-area">
        {renderConfigContent()}
      </div>
    </div>
  );
};

export default GraphConfigCenter;
