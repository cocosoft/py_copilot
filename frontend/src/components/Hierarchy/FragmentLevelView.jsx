/**
 * 片段级视图组件（重构版）
 *
 * 用于展示文本片段中的实体标注和关系
 * 支持文档选择和片段选择
 *
 * @task Phase3-Week10
 * @phase 层级视图逻辑修复
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import TextHighlighter from './TextHighlighter';
import DocumentSelector from './DocumentSelector';
import ChunkSelector from './ChunkSelector';
import useKnowledgeStore from '../../stores/knowledgeStore';
import { 
  getChunkEntitiesDetail, 
  getDocumentEntitiesDetail,
  extractChunkEntities 
} from '../../utils/api/hierarchyApi';
import { useNotification } from '../../hooks/useNotification';
import './FragmentLevelView.css';

/**
 * 片段级视图组件
 *
 * @param {Object} props - 组件属性
 * @param {string} props.knowledgeBaseId - 知识库ID（可选，优先于URL参数）
 * @param {string} props.documentId - 文档ID（可选，优先于URL参数）
 * @param {string} props.fragmentId - 片段ID（可选，优先于URL参数）
 */
const FragmentLevelView = ({
  knowledgeBaseId: propKnowledgeBaseId,
  documentId: propDocumentId,
  fragmentId: propFragmentId
}) => {
  const { knowledgeBaseId: urlKnowledgeBaseId, documentId: urlDocumentId, fragmentId: urlFragmentId } = useParams();

  // 优先使用props中的ID，如果没有则使用URL参数
  const knowledgeBaseId = propKnowledgeBaseId || urlKnowledgeBaseId;
  const initialDocumentId = propDocumentId || urlDocumentId;
  const initialFragmentId = propFragmentId || urlFragmentId;

  // 从状态管理获取层级相关状态
  const {
    hierarchySelection,
    setHierarchySelectedDocument,
    setHierarchySelectedChunk,
    setHierarchyEntities,
    setHierarchyEntitiesLoading,
    setHierarchyEntitiesError
  } = useKnowledgeStore();

  // 本地状态
  const [selectedDocumentId, setSelectedDocumentId] = useState(initialDocumentId || null);
  const [selectedChunkId, setSelectedChunkId] = useState(initialFragmentId || null);
  const [selectedChunk, setSelectedChunk] = useState(null); // 存储选中的片段完整信息
  const [fragment, setFragment] = useState(null);
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [extracting, setExtracting] = useState(false); // 实体识别中状态

  // 通知钩子
  const { showNotification } = useNotification();

  /**
   * 加载片段数据
   */
  const loadFragmentData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setHierarchyEntitiesLoading(true);

      // 如果没有知识库ID，清空数据
      if (!knowledgeBaseId) {
        clearData();
        setLoading(false);
        setHierarchyEntitiesLoading(false);
        return;
      }

      // 如果没有选择文档，清空数据（静默处理，不输出警告）
      if (!selectedDocumentId) {
        clearData();
        setLoading(false);
        setHierarchyEntitiesLoading(false);
        return;
      }

      let entitiesData = [];

      // 如果选择了具体片段，加载片段实体
      if (selectedChunkId) {
        const response = await getChunkEntitiesDetail(knowledgeBaseId, selectedChunkId, {
          page: 1,
          pageSize: 100
        });
        entitiesData = response.data?.list || [];
      } else {
        // 否则加载文档的所有实体
        const response = await getDocumentEntitiesDetail(knowledgeBaseId, selectedDocumentId, {
          page: 1,
          pageSize: 100
        });
        entitiesData = response.data?.list || [];
      }

      // 更新状态管理
      setHierarchyEntities(entitiesData, entitiesData.length);
      setEntities(entitiesData);

    } catch (err) {
      setError('加载片段数据失败');
      setHierarchyEntitiesError(err.message);
      console.error('加载片段数据失败:', err);
      clearData();
    } finally {
      setLoading(false);
      setHierarchyEntitiesLoading(false);
    }
  }, [knowledgeBaseId, selectedDocumentId, selectedChunkId, setHierarchyEntities, setHierarchyEntitiesLoading, setHierarchyEntitiesError]);

  /**
   * 清空数据 - 当未选择文档或片段时使用
   */
  const clearData = () => {
    setFragment(null);
    setEntities([]);
    setHierarchyEntities([], 0);
  };

  // 初始加载
  useEffect(() => {
    loadFragmentData();
  }, [loadFragmentData]);

  /**
   * 处理文档选择变更
   */
  const handleDocumentChange = useCallback((document) => {
    if (document) {
      setSelectedDocumentId(document.id);
      setSelectedChunkId(null); // 切换文档时清空片段选择
      setSelectedChunk(null); // 清空片段信息
      setFragment(null); // 清空片段数据
      setEntities([]); // 清空实体数据
      setHierarchySelectedDocument(document.id);
      setHierarchySelectedChunk(null);
    }
  }, [setHierarchySelectedDocument, setHierarchySelectedChunk]);

  /**
   * 处理片段选择变更
   */
  const handleChunkChange = useCallback((chunk) => {
    if (chunk) {
      setSelectedChunkId(chunk.id);
      setSelectedChunk(chunk); // 保存片段完整信息，包括文本内容
      setHierarchySelectedChunk(chunk.id);

      // 设置片段数据
      const fragmentData = {
        id: chunk.id,
        text: chunk.text,
        documentId: selectedDocumentId,
        knowledgeBaseId: knowledgeBaseId,
        startPosition: chunk.start_position || 0,
        endPosition: chunk.end_position || 0
      };
      setFragment(fragmentData);
    }
  }, [setHierarchySelectedChunk, selectedDocumentId, knowledgeBaseId]);

  /**
   * 处理实体点击事件
   */
  const handleEntityClick = useCallback((entity) => {
    console.log('点击实体:', entity);
    // 可以实现跳转到实体详情页或其他操作
  }, []);

  /**
   * 重新识别当前片段实体
   */
  const handleReExtractEntities = useCallback(async () => {
    if (!selectedChunkId) {
      showNotification({
        type: 'warning',
        message: '请先选择一个片段'
      });
      return;
    }

    setExtracting(true);
    try {
      const result = await extractChunkEntities(knowledgeBaseId, selectedChunkId);
      
      if (result.code === 200) {
        const entityCount = result.data?.entity_count || 0;
        showNotification({
          type: 'success',
          message: `实体识别成功！共识别 ${entityCount} 个实体`
        });
        
        // 刷新实体列表
        await loadFragmentData();
      } else {
        showNotification({
          type: 'error',
          message: result.message || '实体识别失败'
        });
      }
    } catch (err) {
      console.error('实体识别失败:', err);
      showNotification({
        type: 'error',
        message: '实体识别失败: ' + (err.message || '未知错误')
      });
    } finally {
      setExtracting(false);
    }
  }, [knowledgeBaseId, selectedChunkId, loadFragmentData, showNotification]);

  // 渲染加载状态
  if (loading && !fragment) {
    return (
      <div className="fragment-level-view">
        <div className="flv-loading">
          <div className="loading-spinner"></div>
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  // 渲染错误状态
  if (error && !fragment) {
    return (
      <div className="fragment-level-view">
        <div className="flv-error">
          <span className="error-icon">⚠</span>
          <span>{error}</span>
          <button onClick={loadFragmentData}>重试</button>
        </div>
      </div>
    );
  }

  return (
    <div className="fragment-level-view">
      {/* 头部区域 */}
      <div className="flv-header">
        <h2>片段级视图</h2>
        <div className="flv-breadcrumb">
          <span>知识库</span>
          <span className="separator">&gt;</span>
          <span>文档</span>
          <span className="separator">&gt;</span>
          <span>片段</span>
        </div>
      </div>

      {/* 选择器区域 */}
      <div className="flv-selectors">
        <div className="selector-group">
          <label className="selector-label">选择文档:</label>
          <DocumentSelector
            knowledgeBaseId={knowledgeBaseId}
            value={selectedDocumentId}
            onChange={handleDocumentChange}
            placeholder="请选择文档"
          />
        </div>

        <div className="selector-group">
          <label className="selector-label">选择片段:</label>
          <ChunkSelector
            knowledgeBaseId={knowledgeBaseId}
            documentId={selectedDocumentId}
            value={selectedChunkId}
            onChange={handleChunkChange}
            placeholder={selectedDocumentId ? "请选择片段" : "请先选择文档"}
            disabled={!selectedDocumentId}
          />
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flv-content">
        <div className="flv-text-container">
          <div className="section-header">
            <h3>片段内容</h3>
            {selectedDocumentId && (
              <span className="section-info">
                {selectedChunkId ? '显示选中片段' : '显示文档所有实体'}
              </span>
            )}
          </div>

          {fragment ? (
            <>
              <TextHighlighter
                text={fragment.text}
                entities={entities}
                onEntityClick={handleEntityClick}
              />
              {/* 重新识别按钮 */}
              {selectedChunkId && (
                <div className="re-extract-section">
                  <button
                    className="re-extract-button"
                    onClick={handleReExtractEntities}
                    disabled={extracting}
                    title="重新识别当前片段的实体"
                  >
                    {extracting ? (
                      <>
                        <span className="loading-icon">⏳</span>
                        <span>识别中...</span>
                      </>
                    ) : (
                      <>
                        <span>🔄</span>
                        <span>重新识别实体</span>
                      </>
                    )}
                  </button>
                  <span className="re-extract-hint">
                    如果当前片段实体识别失败或需要更新，可点击重新识别
                  </span>
                </div>
              )}
            </>
          ) : (
            <div className="empty-content">
              <span className="empty-icon">📄</span>
              <span>请选择文档和片段查看内容</span>
            </div>
          )}
        </div>

        <div className="flv-sidebar">
          {/* 统计信息 - 只在选择了片段时显示 */}
          {selectedChunkId && fragment && (
            <div className="flv-stats">
              <h3>片段统计</h3>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-label">实体数量</span>
                  <span className="stat-value">{entities.length}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">文本长度</span>
                  <span className="stat-value">
                    {fragment.text.length} 字符
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">选中文档</span>
                  <span className="stat-value">{selectedDocumentId}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">选中片段</span>
                  <span className="stat-value">{selectedChunkId}</span>
                </div>
              </div>
            </div>
          )}

          {/* 实体列表 - 只在选择了片段时显示 */}
          {selectedChunkId && (
            <div className="flv-entities">
              <h3>实体列表</h3>
              {entities.length > 0 ? (
                <ul className="entity-list">
                  {entities.map((entity, index) => (
                    <li
                      key={`entity-${entity.id || index}`}
                      className={`entity-item entity-type-${(entity.type || 'default').toLowerCase()}`}
                      onClick={() => handleEntityClick(entity)}
                    >
                      <span className="entity-text">{entity.text}</span>
                      <span className="entity-type">{entity.type || '未知'}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="empty-entities">
                  <span>暂无实体数据</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FragmentLevelView;
