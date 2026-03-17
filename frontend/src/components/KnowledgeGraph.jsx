import React, { useState, useEffect, useRef } from 'react';
import SimpleKnowledgeGraph from './SimpleKnowledgeGraph';
import { request } from '../utils/apiUtils';
import './KnowledgeGraph.css';

/**
 * 实体类型配置 - 包含颜色、图标、大小等视觉属性
 * 增大节点尺寸以提高可见性
 */
const ENTITY_CONFIG = {
  'PERSON': {
    color: '#FF6B6B',
    gradient: ['#FF6B6B', '#EE5A5A'],
    icon: '👤',
    size: 35,
    label: '人物'
  },
  'ORGANIZATION': {
    color: '#4ECDC4',
    gradient: ['#4ECDC4', '#3DBDB5'],
    icon: '🏢',
    size: 40,
    label: '组织'
  },
  'ORG': {
    color: '#4ECDC4',
    gradient: ['#4ECDC4', '#3DBDB5'],
    icon: '🏢',
    size: 40,
    label: '组织'
  },
  'LOCATION': {
    color: '#45B7D1',
    gradient: ['#45B7D1', '#3AA0B9'],
    icon: '📍',
    size: 32,
    label: '地点'
  },
  'LOC': {
    color: '#45B7D1',
    gradient: ['#45B7D1', '#3AA0B9'],
    icon: '📍',
    size: 32,
    label: '地点'
  },
  'DATE': {
    color: '#96CEB4',
    gradient: ['#96CEB4', '#7FB8A0'],
    icon: '📅',
    size: 28,
    label: '日期'
  },
  'MONEY': {
    color: '#FECA57',
    gradient: ['#FECA57', '#E5B548'],
    icon: '💰',
    size: 30,
    label: '金额'
  },
  'TECH': {
    color: '#A29BFE',
    gradient: ['#A29BFE', '#8B84E8'],
    icon: '💻',
    size: 32,
    label: '技术'
  },
  'PRODUCT': {
    color: '#FD79A8',
    gradient: ['#FD79A8', '#E86796'],
    icon: '📦',
    size: 32,
    label: '产品'
  },
  'EVENT': {
    color: '#FDCB6E',
    gradient: ['#FDCB6E', '#E8B85F'],
    icon: '📢',
    size: 32,
    label: '事件'
  },
  'CONCEPT': {
    color: '#6C5CE7',
    gradient: ['#6C5CE7', '#5B4BD4'],
    icon: '💡',
    size: 32,
    label: '概念'
  },
  'default': {
    color: '#A29BFE',
    gradient: ['#A29BFE', '#8B84E8'],
    icon: '🔹',
    size: 30,
    label: '实体'
  }
};

/**
 * 获取实体配置
 * 
 * @param {string} type - 实体类型
 * @returns {Object} 实体配置对象
 */
const getEntityConfig = (type) => {
  return ENTITY_CONFIG[type] || ENTITY_CONFIG['default'];
};

const KnowledgeGraph = ({ documentId, textContent, graphData, data, viewMode = 'force', filters = {}, onNodeClick, width = 800, height = 600, responsive = true, style = {} }) => {
  const svgRef = useRef();
  const containerRef = useRef();
  const graphContentRef = useRef();
  const [internalGraphData, setInternalGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  
  // 响应式调整SVG尺寸
  useEffect(() => {
    if (!responsive) return;
    
    // 获取容器尺寸
    const updateDimensions = () => {
      const container = graphContentRef.current;
      if (container) {
        const { clientWidth, clientHeight } = container;
        console.log('Graph content dimensions:', { clientWidth, clientHeight });
        const newDimensions = {
          width: clientWidth || 800,
          height: clientHeight || 600
        };
        console.log('New dimensions:', newDimensions);
        setDimensions(newDimensions);
      }
    };
    
    // 初始设置
    updateDimensions();
    
    // 监听窗口大小变化
    window.addEventListener('resize', updateDimensions);
    
    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  }, [responsive]);
  
  // 当传入的width或height变化时更新
  useEffect(() => {
    if (!responsive) {
      setDimensions({ width, height });
    }
  }, [width, height, responsive]);

  // 加载知识图谱数据
  useEffect(() => {
    if (data) {
      // 如果提供了data，直接使用
      setInternalGraphData(data);
    } else if (graphData) {
      // 如果提供了graphData，直接使用
      setInternalGraphData(graphData);
    } else if (documentId || textContent) {
      // 否则从API加载数据
      loadGraphData();
    }
  }, [documentId, textContent, graphData, data]);

  const loadGraphData = async () => {
    setLoading(true);
    setError('');
    
    try {
      let data;
      
      if (documentId) {
        // 从文档ID获取知识图谱数据
        data = await request(`/v1/knowledge-graph/documents/${documentId}/graph`, {
          method: 'GET'
        });
      } else if (textContent) {
        // 从文本内容提取知识图谱数据
        data = await request('/v1/knowledge-graph/extract-entities', {
          method: 'POST',
          data: { text: textContent }
        });
      } else {
        // 生成示例知识图谱数据
        data = {
          entities: [
            { id: 1, name: 'Python', type: 'TECH', properties: {} },
            { id: 2, name: 'JavaScript', type: 'TECH', properties: {} },
            { id: 3, name: 'React', type: 'TECH', properties: {} },
            { id: 4, name: 'D3.js', type: 'TECH', properties: {} },
            { id: 5, name: '知识图谱', type: 'CONCEPT', properties: {} }
          ],
          relationships: [
            { id: 1, source: 1, target: 5, type: '相关', properties: {} },
            { id: 2, source: 2, target: 5, type: '相关', properties: {} },
            { id: 3, source: 3, target: 2, type: '基于', properties: {} },
            { id: 4, source: 4, target: 2, type: '基于', properties: {} },
            { id: 5, source: 4, target: 5, type: '用于', properties: {} }
          ]
        };
      }
      
      setInternalGraphData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="knowledge-graph-loading">
        <div className="loading-spinner"></div>
        <span>正在生成知识图谱...</span>
      </div>
    );
  }

  if (error) {
    // 优化错误信息显示
    let friendlyError = error;
    
    if (error.includes('获取文档实体失败') || error.includes('提取实体关系失败')) {
      friendlyError = '知识图谱生成失败，请检查网络连接或稍后重试';
    } else if (error.includes('Failed to fetch') || error.includes('Network Error')) {
      friendlyError = '网络连接失败，请检查网络连接后重试';
    } else if (error.includes('Unexpected token') || error.includes('JSON')) {
      friendlyError = '数据格式错误，请刷新页面后重试';
    }
    
    return (
      <div className="knowledge-graph-error">
        <div className="error-icon">⚠️</div>
        <div className="error-content">
          <h4>知识图谱加载失败</h4>
          <p>{friendlyError}</p>
          <div className="error-actions">
            <button onClick={loadGraphData} className="retry-btn">重试</button>
            <button onClick={() => window.location.reload()} className="refresh-btn">刷新页面</button>
          </div>
        </div>
      </div>
    );
  }

  // 使用internalGraphData作为主要数据源，如果外部提供了graphData则优先使用
  const dataToRender = internalGraphData;
  
  console.log('KnowledgeGraph dataToRender:', dataToRender);
  console.log('KnowledgeGraph dimensions:', dimensions);
  
  if (!dataToRender) {
    return (
      <div className="knowledge-graph-empty">
        <div className="empty-icon">📊</div>
        <span>暂无知识图谱数据</span>
        <button onClick={loadGraphData} className="generate-btn">生成知识图谱</button>
      </div>
    );
  }

  /**
   * 获取实际的实体类型
   *
   * @returns {Array} 实体类型列表
   */
  const getActualEntityTypes = () => {
    if (!dataToRender) return [];

    const entities = dataToRender.nodes || dataToRender.entities || [];
    const entityTypes = [...new Set(entities.map(entity => entity.type || entity.group || 'default'))];

    return entityTypes.map(type => {
      const config = getEntityConfig(type);
      return {
        type,
        displayName: config.label,
        cssClass: type.toLowerCase(),
        icon: config.icon,
        color: config.color
      };
    });
  };

  // 缩放控制函数
  const handleZoomIn = () => {
    if (svgRef.current) {
      d3.select(svgRef.current).transition().call(
        d3.zoom().scaleBy, 1.2
      );
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current) {
      d3.select(svgRef.current).transition().call(
        d3.zoom().scaleBy, 0.8
      );
    }
  };

  const handleZoomReset = () => {
    if (svgRef.current) {
      d3.select(svgRef.current).transition().call(
        d3.zoom().transform, d3.zoomIdentity
      );
    }
  };

  return (
    <div className="knowledge-graph-container" ref={containerRef} style={style}>
      <div className="graph-header">
        <h3>知识图谱</h3>
        <div className="graph-stats">
          <span>实体: {(dataToRender.entities || dataToRender.nodes || []).length || 0}</span>
          <span>关系: {(dataToRender.relationships || dataToRender.links || []).length || 0}</span>
        </div>
        <div className="graph-controls">
          <button onClick={loadGraphData} className="refresh-btn">刷新</button>
          <button onClick={() => window.print()} className="export-btn">导出</button>
        </div>
      </div>
      
      <div className="graph-legend">
        {getActualEntityTypes().map(entityType => (
          <div key={entityType.type} className="legend-item" title={entityType.displayName}>
            <span className="legend-icon">{entityType.icon}</span>
            <span className={`legend-color ${entityType.cssClass}`} style={{ background: entityType.color }}></span>
            <span>{entityType.displayName}</span>
          </div>
        ))}
      </div>

      <div className="knowledge-graph-content" ref={graphContentRef} style={{
        minWidth: '400px',
        minHeight: '600px',
        width: responsive ? '100%' : dimensions.width,
        height: responsive ? '100%' : dimensions.height
      }}>
        <SimpleKnowledgeGraph 
          data={dataToRender} 
          width={dimensions.width} 
          height={dimensions.height} 
        />
      </div>
    </div>
  );
};

export default KnowledgeGraph;