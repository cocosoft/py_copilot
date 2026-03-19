/**
 * 实体管理页面
 *
 * 整合实体识别和实体关系管理功能，提供统一的实体管理界面
 */

import React, { useState } from 'react';
import EntityRecognition from './EntityRecognition';
import RelationManagement from '../../components/KnowledgeGraph/RelationManagement';
import useKnowledgeStore from '@stores/knowledgeStore';
import './EntityManagement.css';

/**
 * 实体管理页面
 */
const EntityManagement = () => {
  const { currentKnowledgeBase } = useKnowledgeStore();
  const [activeTab, setActiveTab] = useState('recognition');

  return (
    <div className="entity-management">
      <div className="entity-management-header">
        <h2>实体管理</h2>
        <p>管理知识库中的实体和实体关系</p>
      </div>
      
      {/* 标签页导航 */}
      <div className="entity-management-tabs">
        <button 
          className={`tab-button ${activeTab === 'recognition' ? 'active' : ''}`}
          onClick={() => setActiveTab('recognition')}
        >
          实体识别
        </button>
        <button 
          className={`tab-button ${activeTab === 'relationships' ? 'active' : ''}`}
          onClick={() => setActiveTab('relationships')}
        >
          实体关系
        </button>
      </div>
      
      {/* 标签页内容 */}
      <div className="entity-management-content">
        {activeTab === 'recognition' && (
          <EntityRecognition />
        )}
        {activeTab === 'relationships' && (
          <RelationManagement knowledgeBaseId={currentKnowledgeBase?.id} />
        )}
      </div>
    </div>
  );
};

export default EntityManagement;