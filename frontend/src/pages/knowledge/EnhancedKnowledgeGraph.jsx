/**
 * 增强版知识图谱页面
 *
 * 集成了以下优化功能：
 * - 一体化知识查看器 (FE-009): 统一展示知识单元、实体、关联
 * - 关联网络可视化 (FE-010): 强大的网络关系可视化
 *
 * @module EnhancedKnowledgeGraph
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';

// 导入新功能组件
import {
  UnifiedKnowledgeViewer,
  AssociationNetwork
} from '../../components/Knowledge';

// 导入原知识图谱组件
import KnowledgeGraph from '../../components/KnowledgeGraph';

// 导入状态管理
import useKnowledge from '../../hooks/useKnowledge';

// 导入 API
import {
  getKnowledgeBases,
  getKnowledgeBaseGraphData,
  buildKnowledgeGraph,
  extractEntities,
  getGraphStatistics
} from '../../utils/api/knowledgeApi';
import defaultModelApi from '../../utils/api/defaultModelApi';

// 导入样式
import './EnhancedKnowledgeGraph.css';

/**
 * 图谱统计组件
 *
 * @param {Object} props - 组件属性
 * @param {Object} props.stats - 统计数据
 */
const GraphStats = ({ stats }) => {
  const { t } = useTranslation(['knowledge', 'common']);

  return (
    <div className="graph-stats">
      <div className="stat-item">
        <span className="stat-value">{stats.entityCount || 0}</span>
        <span className="stat-label">{t('knowledge:entities')}</span>
      </div>
      <div className="stat-item">
        <span className="stat-value">{stats.relationCount || 0}</span>
        <span className="stat-label">{t('knowledge:relations')}</span>
      </div>
      <div className="stat-item">
        <span className="stat-value">{stats.documentCount || 0}</span>
        <span className="stat-label">{t('knowledge:documents')}</span>
      </div>
      <div className="stat-item">
        <span className="stat-value">{stats.coverage || 0}%</span>
        <span className="stat-label">{t('knowledge:coverage')}</span>
      </div>
    </div>
  );
};

/**
 * 传统图谱视图组件
 *
 * @param {Object} props - 组件属性
 * @param {string} props.knowledgeBaseId - 知识库ID
 * @param {Object} props.graphData - 图谱数据
 */
const TraditionalGraphView = ({ knowledgeBaseId, graphData }) => {
  const { t } = useTranslation(['knowledge', 'common']);
  const [isBuilding, setIsBuilding] = useState(false);

  const handleBuildGraph = useCallback(async () => {
    setIsBuilding(true);
    try {
      await buildKnowledgeGraph(knowledgeBaseId);
      // 刷新数据
      window.location.reload();
    } catch (error) {
      console.error('构建图谱失败:', error);
    } finally {
      setIsBuilding(false);
    }
  }, [knowledgeBaseId]);

  return (
    <div className="traditional-graph-view">
      <div className="graph-toolbar">
        <button
          className="btn-primary"
          onClick={handleBuildGraph}
          disabled={isBuilding}
        >
          {isBuilding ? (
            <>
              <span className="spinner-small" />
              {t('knowledge:buildingGraph')}
            </>
          ) : (
            <>
              🔄 {t('knowledge:rebuildGraph')}
            </>
          )}
        </button>
      </div>
      <div className="graph-container">
        {graphData ? (
          <KnowledgeGraph data={graphData} />
        ) : (
          <div className="empty-graph">
            <p>{t('knowledge:noGraphData')}</p>
            <button className="btn-primary" onClick={handleBuildGraph}>
              {t('knowledge:buildGraph')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * 增强版知识图谱页面组件
 *
 * @component
 */
const EnhancedKnowledgeGraph = () => {
  const { t } = useTranslation(['knowledge', 'common']);

  // 使用状态管理
  const { currentKnowledgeBase, setCurrentKnowledgeBase } = useKnowledge();

  // 兼容旧代码的别名
  const selectedKnowledgeBase = currentKnowledgeBase;
  const setSelectedKnowledgeBase = setCurrentKnowledgeBase;

  // 视图状态
  const [activeView, setActiveView] = useState('network'); // network, unified, traditional

  // 实体识别状态
  const [showEntityRecognition, setShowEntityRecognition] = useState(false);
  const [recognitionText, setRecognitionText] = useState('');
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [recognizedEntities, setRecognizedEntities] = useState([]);
  const [recognitionError, setRecognitionError] = useState('');
  const [selectedEntityTypes, setSelectedEntityTypes] = useState(['PERSON', 'ORG', 'LOC', 'TIME']);
  const [recognitionThreshold, setRecognitionThreshold] = useState(0.7);

  // 获取知识库场景的默认模型
  const { data: knowledgeSceneModel } = useQuery({
    queryKey: ['sceneDefaultModel', 'knowledge'],
    queryFn: () => defaultModelApi.getSceneDefaultModel('knowledge'),
    staleTime: 5 * 60 * 1000,
  });

  // 获取知识库列表
  const { data: knowledgeBasesData, isLoading: isLoadingKBs } = useQuery({
    queryKey: ['knowledgeBases'],
    queryFn: () => getKnowledgeBases(0, 50),
    staleTime: 5 * 60 * 1000,
  });

  // 支持两种数据结构：response.knowledge_bases 或 response.data
  const knowledgeBases = knowledgeBasesData?.knowledge_bases || knowledgeBasesData?.data || knowledgeBasesData || [];

  // 获取图谱数据
  const {
    data: graphData,
    isLoading: isLoadingGraph,
    error: graphError,
    refetch: refetchGraph
  } = useQuery({
    queryKey: ['graphData', selectedKnowledgeBase],
    queryFn: () => getKnowledgeBaseGraphData(selectedKnowledgeBase),
    enabled: !!selectedKnowledgeBase,
    staleTime: 5 * 60 * 1000,
  });

  // 视图配置
  const views = [
    { key: 'network', label: t('knowledge:associationNetwork'), icon: '🕸️' },
    { key: 'unified', label: t('knowledge:unifiedViewer'), icon: '📚' },
    { key: 'traditional', label: t('knowledge:traditionalGraph'), icon: '📊' },
  ];

  // 处理实体点击
  const handleEntityClick = useCallback((entity) => {
    console.log('点击实体:', entity);
    // 可以打开实体详情面板
  }, []);

  // 处理关系点击
  const handleRelationClick = useCallback((relation) => {
    console.log('点击关系:', relation);
  }, []);

  // 处理网络选择
  const handleNetworkSelect = useCallback((selectedItems) => {
    console.log('选择项目:', selectedItems);
  }, []);

  // 处理实体识别
  const handleEntityRecognition = useCallback(async () => {
    if (!recognitionText.trim()) {
      setRecognitionError(t('knowledge:pleaseEnterText'));
      return;
    }

    setIsRecognizing(true);
    setRecognitionError('');
    setRecognizedEntities([]);

    try {
      // 构建请求参数，包含模型配置和识别选项
      const requestParams = {
        text: recognitionText,
        entity_types: selectedEntityTypes,
        threshold: recognitionThreshold,
        model_id: (knowledgeSceneModel?.model_id || knowledgeSceneModel?.model?.id)?.toString(),
        model_configuration: {
          temperature: 0.1,
          max_tokens: 2000,
        }
      };

      console.log('实体识别请求参数:', requestParams);
      
      const response = await extractEntities(requestParams);
      // 支持多种数据结构
      const entities = response?.entities || response?.data?.entities || response || [];
      
      // 根据阈值过滤实体
      const filteredEntities = entities.filter(entity => 
        (entity.confidence || entity.score || 1) >= recognitionThreshold
      );
      
      setRecognizedEntities(filteredEntities);
      if (filteredEntities.length === 0) {
        setRecognitionError(t('knowledge:noEntitiesFound'));
      }
    } catch (error) {
      console.error('实体识别错误:', error);
      setRecognitionError(error.message || t('knowledge:recognitionFailed'));
    } finally {
      setIsRecognizing(false);
    }
  }, [recognitionText, selectedEntityTypes, recognitionThreshold, knowledgeSceneModel, t]);

  // 清空实体识别结果
  const clearRecognition = useCallback(() => {
    setRecognitionText('');
    setRecognizedEntities([]);
    setRecognitionError('');
  }, []);

  return (
    <div className="enhanced-knowledge-graph-page">
      {/* 页面头部 */}
      <div className="page-header">
        <div className="header-left">
          <h1>{t('knowledge:knowledgeGraph')}</h1>

          {/* 知识库选择器 */}
          <div className="knowledge-base-selector">
            <select
              value={selectedKnowledgeBase || ''}
              onChange={(e) => setSelectedKnowledgeBase(e.target.value)}
              disabled={isLoadingKBs}
            >
              <option value="">{t('knowledge:selectKnowledgeBase')}</option>
              {knowledgeBases.map(kb => (
                <option key={kb.id} value={kb.id}>{kb.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* 统计信息 */}
        {graphData?.statistics && (
          <GraphStats stats={graphData.statistics} />
        )}

        {/* 实体识别按钮 */}
        <button
          className={`btn-entity-recognition ${showEntityRecognition ? 'active' : ''}`}
          onClick={() => setShowEntityRecognition(!showEntityRecognition)}
        >
          {t('knowledge:entityRecognition')}
        </button>
      </div>

      {/* 实体识别面板 */}
      {showEntityRecognition && (
        <div className="entity-recognition-panel">
          <div className="panel-header">
            <h3>{t('knowledge:entityRecognition')}</h3>
            <button className="btn-close" onClick={() => setShowEntityRecognition(false)}>×</button>
          </div>
          <div className="panel-content">
            {/* 模型信息 */}
            {knowledgeSceneModel && (
              <div className="model-info">
                <span className="model-label">使用模型:</span>
                <span className="model-name">
                  {knowledgeSceneModel.model_name || knowledgeSceneModel.model?.name || '默认模型'}
                </span>
              </div>
            )}

            {/* 实体类型选择 */}
            <div className="entity-types-selection">
              <label>识别实体类型:</label>
              <div className="entity-types-checkboxes">
                {[
                  { key: 'PERSON', label: '人物' },
                  { key: 'ORG', label: '组织' },
                  { key: 'LOC', label: '地点' },
                  { key: 'TIME', label: '时间' },
                  { key: 'MONEY', label: '金额' },
                  { key: 'PRODUCT', label: '产品' },
                ].map(type => (
                  <label key={type.key} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedEntityTypes.includes(type.key)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedEntityTypes([...selectedEntityTypes, type.key]);
                        } else {
                          setSelectedEntityTypes(selectedEntityTypes.filter(t => t !== type.key));
                        }
                      }}
                    />
                    {type.label}
                  </label>
                ))}
              </div>
            </div>

            {/* 置信度阈值 */}
            <div className="threshold-control">
              <label>置信度阈值: {recognitionThreshold}</label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={recognitionThreshold}
                onChange={(e) => setRecognitionThreshold(parseFloat(e.target.value))}
              />
            </div>

            <textarea
              value={recognitionText}
              onChange={(e) => setRecognitionText(e.target.value)}
              placeholder={t('knowledge:enterTextForRecognition')}
              rows={4}
            />
            <div className="panel-actions">
              <button
                className="btn-primary"
                onClick={handleEntityRecognition}
                disabled={isRecognizing || !recognitionText.trim() || selectedEntityTypes.length === 0}
              >
                {isRecognizing ? (
                  <>
                    <span className="spinner-small" />
                    {t('common:processing')}
                  </>
                ) : (
                  t('knowledge:startRecognition')
                )}
              </button>
              <button className="btn-secondary" onClick={clearRecognition}>
                {t('common:clear')}
              </button>
            </div>
            {recognitionError && (
              <div className="error-message">{recognitionError}</div>
            )}
            {recognizedEntities.length > 0 && (
              <div className="recognized-entities">
                <h4>{t('knowledge:recognizedEntities')} ({recognizedEntities.length})</h4>
                <div className="entities-list">
                  {recognizedEntities.map((entity, index) => (
                    <span key={index} className={`entity-tag ${entity.type || 'unknown'}`}>
                      {entity.text || entity.name}
                      <small>{entity.type} ({Math.round((entity.confidence || entity.score || 1) * 100)}%)</small>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 视图切换栏 */}
      <div className="view-switcher">
        {views.map(view => (
          <button
            key={view.key}
            className={`view-button ${activeView === view.key ? 'active' : ''}`}
            onClick={() => setActiveView(view.key)}
          >
            <span className="view-icon">{view.icon}</span>
            <span className="view-label">{view.label}</span>
          </button>
        ))}
      </div>

      {/* 视图内容 */}
      <div className="view-content">
        {isLoadingGraph ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>{t('common:loading')}</p>
          </div>
        ) : graphError ? (
          <div className="error-state">
            <p>{t('knowledge:loadGraphError')}</p>
            <button onClick={() => refetchGraph()}>{t('common:retry')}</button>
          </div>
        ) : !selectedKnowledgeBase ? (
          <div className="empty-state">
            <p>{t('knowledge:pleaseSelectKnowledgeBase')}</p>
          </div>
        ) : (
          <>
            {/* 关联网络视图 - FE-010 */}
            {activeView === 'network' && (
              <AssociationNetwork
                initialNodes={graphData?.entities || graphData?.nodes || []}
                initialLinks={graphData?.relationships || graphData?.links || []}
                width={1200}
                height={700}
                enableClustering={true}
                enableFiltering={true}
                onNodeClick={handleEntityClick}
                onLinkClick={handleRelationClick}
                onSelect={handleNetworkSelect}
              />
            )}

            {/* 一体化知识查看器 - FE-009 */}
            {activeView === 'unified' && (
              <UnifiedKnowledgeViewer
                initialUnits={graphData?.entities || graphData?.nodes || []}
                initialAssociations={graphData?.relationships || graphData?.links || []}
                defaultView="overview"
                enableSearch={true}
                enableExport={true}
              />
            )}

            {/* 传统图谱视图 */}
            {activeView === 'traditional' && (
              <TraditionalGraphView
                knowledgeBaseId={selectedKnowledgeBase}
                graphData={graphData}
              />
            )}
          </>
        )}
      </div>

      {/* 底部工具栏 */}
      <div className="bottom-toolbar">
        <div className="toolbar-left">
          <button className="btn-icon" title={t('knowledge:zoomIn')}>
            🔍+
          </button>
          <button className="btn-icon" title={t('knowledge:zoomOut')}>
            🔍-
          </button>
          <button className="btn-icon" title={t('knowledge:fitView')}>
            ⬜
          </button>
        </div>

        <div className="toolbar-right">
          <button className="btn-secondary">
            💾 {t('knowledge:exportGraph')}
          </button>
          <button className="btn-secondary">
            📤 {t('knowledge:shareGraph')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EnhancedKnowledgeGraph;
