import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import TextHighlighter from './TextHighlighter';
import { getChunkEntities, getChunkGraph } from '../../utils/api/hierarchyApi';
import './FragmentLevelView.css';

/**
 * 片段级视图组件
 * 用于展示文本片段中的实体标注和关系
 * 
 * @param {Object} props - 组件属性
 * @param {string} props.knowledgeBaseId - 知识库ID（可选，优先于URL参数）
 */
const FragmentLevelView = ({ knowledgeBaseId: propKnowledgeBaseId }) => {
  const { knowledgeBaseId: urlKnowledgeBaseId, documentId, fragmentId } = useParams();
  
  // 优先使用props中的knowledgeBaseId，如果没有则使用URL参数
  const knowledgeBaseId = propKnowledgeBaseId || urlKnowledgeBaseId;
  
  const [fragment, setFragment] = useState(null);
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * 加载片段数据
   */
  useEffect(() => {
    const loadFragmentData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 如果没有知识库ID，直接显示默认数据
        if (!knowledgeBaseId) {
          console.warn('知识库ID为空，使用默认数据');
          setDefaultData();
          return;
        }
        
        // 调用真实API获取片段实体数据
        const entitiesResponse = await getChunkEntities(knowledgeBaseId, {
          page: 1,
          pageSize: 50,
          sortBy: 'index',
          sortOrder: 'asc'
        });
        
        // 处理API响应
        const entities = entitiesResponse.data || [];
        
        // 构建片段数据（如果API返回片段信息）
        const fragment = {
          id: fragmentId || '1',
          text: '加载中...', // 实际项目中应该从API获取
          documentId: documentId || '1',
          knowledgeBaseId: knowledgeBaseId,
          startPosition: 0,
          endPosition: 100
        };
        
        setFragment(fragment);
        setEntities(entities);
      } catch (err) {
        setError('加载片段数据失败');
        console.error('加载片段数据失败:', err);
        
        // 错误时使用默认数据
        setDefaultData();
      } finally {
        setLoading(false);
      }
    };
    
    /**
     * 设置默认数据
     */
    const setDefaultData = () => {
      const defaultFragment = {
        id: fragmentId || '1',
        text: '在人工智能领域，机器学习是一种让计算机从数据中学习的方法。深度学习是机器学习的一个分支，它使用多层神经网络来模拟人脑的学习过程。',
        documentId: documentId || '1',
        knowledgeBaseId: knowledgeBaseId,
        startPosition: 0,
        endPosition: 100
      };
      
      const defaultEntities = [
        {
          id: '1',
          text: '人工智能',
          type: '领域',
          start: 2,
          end: 6
        },
        {
          id: '2',
          text: '机器学习',
          type: '技术',
          start: 8,
          end: 12
        },
        {
          id: '3',
          text: '深度学习',
          type: '技术',
          start: 22,
          end: 26
        },
        {
          id: '4',
          text: '多层神经网络',
          type: '技术',
          start: 38,
          end: 44
        }
      ];
      
      setFragment(defaultFragment);
      setEntities(defaultEntities);
    };

    loadFragmentData();
  }, [fragmentId, documentId, knowledgeBaseId]);

  /**
   * 处理实体点击事件
   * @param {Object} entity - 点击的实体
   */
  const handleEntityClick = (entity) => {
    console.log('点击实体:', entity);
    // 可以实现跳转到实体详情页或其他操作
  };

  if (loading) {
    return (
      <div className="fragment-level-view">
        <div className="flv-loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fragment-level-view">
        <div className="flv-error">{error}</div>
      </div>
    );
  }

  if (!fragment) {
    return (
      <div className="fragment-level-view">
        <div className="flv-error">片段不存在</div>
      </div>
    );
  }

  return (
    <div className="fragment-level-view">
      <div className="flv-header">
        <h2>片段级视图</h2>
        <div className="flv-breadcrumb">
          <span>知识库</span> &gt; 
          <span>文档</span> &gt; 
          <span>片段</span>
        </div>
      </div>
      
      <div className="flv-content">
        <div className="flv-text-container">
          <h3>片段内容</h3>
          <TextHighlighter 
            text={fragment.text} 
            entities={entities} 
            onEntityClick={handleEntityClick} 
          />
        </div>
        
        <div className="flv-sidebar">
          <div className="flv-stats">
            <h3>片段统计</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">实体数量</span>
                <span className="stat-value">{entities.length}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">文本长度</span>
                <span className="stat-value">{fragment.text.length} 字符</span>
              </div>
            </div>
          </div>
          
          <div className="flv-entities">
            <h3>实体列表</h3>
            <ul className="entity-list">
              {entities.map(entity => (
                <li 
                  key={entity.id} 
                  className={`entity-item entity-type-${entity.type.toLowerCase()}`}
                  onClick={() => handleEntityClick(entity)}
                >
                  <span className="entity-text">{entity.text}</span>
                  <span className="entity-type">{entity.type}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FragmentLevelView;