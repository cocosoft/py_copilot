import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import HierarchyNavigator from './HierarchyNavigator';
import FragmentLevelView from './FragmentLevelView';
import DocumentLevelView from './DocumentLevelView';
import KnowledgeBaseLevelView from './KnowledgeBaseLevelView';
import GlobalLevelView from './GlobalLevelView';
import EntityExtractionManager from './EntityExtractionManager';
import useKnowledgeStore from '../../stores/knowledgeStore';
import {
  getFragmentLevelStats,
  getDocumentLevelStats,
  getKnowledgeBaseLevelStats,
  getGlobalLevelStats,
  getEntityHierarchy
} from '../../utils/api/hierarchyApi';
import './HierarchyViewContainer.css';

/**
 * 层级视图容器组件
 * 
 * @param {Object} props - 组件属性
 * @param {string|number} props.knowledgeBaseId - 知识库ID（可选，优先于URL参数）
 */
const HierarchyViewContainer = ({ knowledgeBaseId: propKnowledgeBaseId }) => {
  const { knowledgeBaseId: urlKnowledgeBaseId, '*': splatPath } = useParams();
  const location = useLocation();

  // 优先使用props中的knowledgeBaseId，如果没有则使用URL参数
  const knowledgeBaseId = propKnowledgeBaseId || urlKnowledgeBaseId;

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
  const lastStatsUpdateRef = useRef(0);
  const pendingStatsUpdateRef = useRef(false);

  // 从 URL 路径解析当前层级
  useEffect(() => {
    const pathParts = location.pathname.split('/');
    const levelIndex = pathParts.indexOf('hierarchy');
    if (levelIndex !== -1 && pathParts[levelIndex + 1]) {
      const levelFromUrl = pathParts[levelIndex + 1];
      // 映射 URL 路径到层级状态
      const levelMap = {
        'fragment': 'fragment',
        'document': 'document',
        'knowledge_base': 'knowledge_base',
        'global': 'global',
        'extraction_manager': 'extraction_manager'
      };
      const mappedLevel = levelMap[levelFromUrl];
      if (mappedLevel && mappedLevel !== currentHierarchyLevel) {
        setHierarchyLevel(mappedLevel);
      }
    }
  }, [location.pathname, currentHierarchyLevel, setHierarchyLevel]);

  // 加载各层级统计数据
  useEffect(() => {
    if (knowledgeBaseId) {
      loadAllLevelStats();
    }
  }, [knowledgeBaseId]);

  const loadAllLevelStats = useCallback(async (force = false) => {
    // 防抖机制：30秒内只能刷新一次，除非强制刷新
    const now = Date.now();
    const minInterval = 30000; // 30秒
    
    if (!force && now - lastStatsUpdateRef.current < minInterval) {
      // 如果距离上次更新不足30秒，标记为待更新，延迟执行
      if (!pendingStatsUpdateRef.current) {
        pendingStatsUpdateRef.current = true;
        const delay = minInterval - (now - lastStatsUpdateRef.current);
        setTimeout(() => {
          pendingStatsUpdateRef.current = false;
          loadAllLevelStats(true);
        }, delay);
      }
      return;
    }

    lastStatsUpdateRef.current = now;
    pendingStatsUpdateRef.current = false;

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
  }, [knowledgeBaseId]);

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
    console.log('[HierarchyViewContainer] 渲染层级:', currentHierarchyLevel, 'knowledgeBaseId:', knowledgeBaseId);
    switch (currentHierarchyLevel) {
      case 'fragment':
        return <FragmentLevelView knowledgeBaseId={knowledgeBaseId} />;
      case 'document':
        return <DocumentLevelView knowledgeBaseId={knowledgeBaseId} />;
      case 'knowledge_base':
        return <KnowledgeBaseLevelView knowledgeBaseId={knowledgeBaseId} />;
      case 'global':
        return <GlobalLevelView />;
      case 'extraction_manager':
        console.log('[HierarchyViewContainer] 渲染 EntityExtractionManager');
        return (
          <EntityExtractionManager 
            knowledgeBaseId={knowledgeBaseId} 
            onStatsUpdate={loadAllLevelStats}
          />
        );
      default:
        console.log('[HierarchyViewContainer] 默认渲染 KnowledgeBaseLevelView');
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