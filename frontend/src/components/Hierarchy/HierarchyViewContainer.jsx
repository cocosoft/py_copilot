import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import HierarchyNavigator from './HierarchyNavigator';
import FragmentLevelView from './FragmentLevelView';
import DocumentLevelView from './DocumentLevelView';
import KnowledgeBaseLevelView from './KnowledgeBaseLevelView';
import GlobalLevelView from './GlobalLevelView';
import useKnowledgeStore from '../../stores/knowledgeStore';
import {
  getFragmentLevelStats,
  getDocumentLevelStats,
  getKnowledgeBaseLevelStats,
  getGlobalLevelStats,
  getEntityHierarchy
} from '../../utils/api/hierarchyApi';
import './HierarchyViewContainer.css';

const HierarchyViewContainer = () => {
  const { knowledgeBaseId } = useParams();
  const { 
    currentHierarchyLevel, 
    setHierarchyLevel,
    hierarchyData,
    cacheHierarchyData,
    setCurrentEntity,
    setCurrentKnowledgeBase
  } = useKnowledgeStore();
  const navigate = useNavigate();
  
  const [levelStats, setLevelStats] = useState({});

  // 加载各层级统计数据
  useEffect(() => {
    if (knowledgeBaseId) {
      loadAllLevelStats();
    }
  }, [knowledgeBaseId]);

  const loadAllLevelStats = async () => {
    try {
      // 尝试获取各层级统计数据
      const statsPromises = [
        getFragmentLevelStats(knowledgeBaseId).catch(() => ({ entityCount: 0 })),
        getDocumentLevelStats(knowledgeBaseId).catch(() => ({ entityCount: 0 })),
        getKnowledgeBaseLevelStats(knowledgeBaseId).catch(() => ({ entityCount: 0 })),
        getGlobalLevelStats().catch(() => ({ entityCount: 0 }))
      ];
      
      const [fragmentStats, documentStats, kbStats, globalStats] = await Promise.all(statsPromises);
      
      setLevelStats({
        fragment: fragmentStats.entityCount || 0,
        document: documentStats.entityCount || 0,
        knowledge_base: kbStats.entityCount || 0,
        global: globalStats.entityCount || 0
      });
    } catch (error) {
      console.error('加载层级统计失败:', error);
      // 设置默认值
      setLevelStats({
        fragment: 0,
        document: 0,
        knowledge_base: 0,
        global: 0
      });
    }
  };

  const handleLevelChange = (newLevel) => {
    setHierarchyLevel(newLevel);
    
    // 更新URL
    navigate(`/knowledge/${knowledgeBaseId}/hierarchy/${newLevel}`);
  };

  /**
   * 处理层级间数据关联
   */
  const handleDataAssociation = async (entity, targetLevel) => {
    try {
      // 调用API获取实体的层级信息
      const hierarchyData = await getEntityHierarchy(entity.id, targetLevel);
      
      // 根据目标层级设置相应的状态
      setCurrentEntity(entity);
      setHierarchyLevel(targetLevel);
      
      // 如果目标层级是知识库级，设置当前知识库
      if (targetLevel === 'knowledge_base' && entity.knowledgeBaseId) {
        setCurrentKnowledgeBase({ id: entity.knowledgeBaseId, name: entity.knowledgeBaseName || '知识库' });
      }
      
      // 更新URL
      navigate(`/knowledge/${knowledgeBaseId || entity.knowledgeBaseId}/hierarchy/${targetLevel}`);
      
      console.log('层级间数据关联成功:', hierarchyData);
    } catch (error) {
      console.error('层级间数据关联失败:', error);
    }
  };

  // 根据当前层级渲染对应视图
  const renderCurrentView = () => {
    switch (currentHierarchyLevel) {
      case 'fragment':
        return <FragmentLevelView knowledgeBaseId={knowledgeBaseId} />;
      case 'document':
        return <DocumentLevelView knowledgeBaseId={knowledgeBaseId} />;
      case 'knowledge_base':
        return <KnowledgeBaseLevelView knowledgeBaseId={knowledgeBaseId} />;
      case 'global':
        return <GlobalLevelView />;
      default:
        return <KnowledgeBaseLevelView knowledgeBaseId={knowledgeBaseId} />;
    }
  };

  return (
    <div className="hierarchy-view-container">
      <HierarchyNavigator 
        currentLevel={currentHierarchyLevel}
        onLevelChange={handleLevelChange}
        levelStats={levelStats}
      />
      
      <div className="hierarchy-content">
        {renderCurrentView()}
      </div>
    </div>
  );
};

export default HierarchyViewContainer;