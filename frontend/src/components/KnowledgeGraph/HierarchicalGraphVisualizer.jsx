/**
 * 分层知识图谱可视化组件
 * 
 * 支持三层架构可视化：
 * 1. 文档层 (Document Layer)
 * 2. 知识库层 (Knowledge Base Layer)
 * 3. 全局层 (Global Layer)
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';
import * as echarts from 'echarts';
import './HierarchicalGraphVisualizer.css';

/**
 * 图层类型枚举
 */
export const LayerType = {
  DOCUMENT: 'document',
  KNOWLEDGE_BASE: 'knowledge_base',
  GLOBAL: 'global'
};

/**
 * 分层知识图谱可视化组件
 * 
 * @param {Object} props - 组件属性
 * @param {string} props.knowledgeBaseId - 知识库ID
 * @param {string} props.currentLayer - 当前显示的图层
 * @param {Object} props.graphData - 图谱数据
 * @param {Function} props.onNodeClick - 节点点击回调
 * @param {Function} props.onLayerChange - 图层切换回调
 */
const HierarchicalGraphVisualizer = ({
  knowledgeBaseId,
  currentLayer = LayerType.DOCUMENT,
  graphData = null,
  onNodeClick,
  onLayerChange,
  width = '100%',
  height = '600px'
}) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [localGraphData, setLocalGraphData] = useState(null);

  /**
   * 初始化图表实例
   */
  useEffect(() => {
    if (chartRef.current && !chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
      
      // 添加点击事件监听
      chartInstance.current.on('click', (params) => {
        if (params.dataType === 'node' && onNodeClick) {
          onNodeClick(params.data);
        }
      });

      // 响应式调整
      const handleResize = () => {
        chartInstance.current && chartInstance.current.resize();
      };
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        chartInstance.current && chartInstance.current.dispose();
        chartInstance.current = null;
      };
    }
  }, [onNodeClick]);

  /**
   * 加载图谱数据
   */
  const loadGraphData = useCallback(async () => {
    if (!knowledgeBaseId) return;

    setLoading(true);
    setError(null);

    try {
      // 实际项目中应该调用API
      // const response = await fetch(`/api/v1/hierarchical-graph/${knowledgeBaseId}?layer=${currentLayer}`);
      // const data = await response.json();
      
      // 模拟数据
      const mockData = generateMockData(currentLayer);
      setLocalGraphData(mockData);
    } catch (err) {
      setError(`加载图谱数据失败: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, currentLayer]);

  /**
   * 当图层或知识库变化时重新加载数据
   */
  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  /**
   * 更新图表配置
   */
  useEffect(() => {
    if (!chartInstance.current || !localGraphData) return;

    const option = generateChartOption(localGraphData, currentLayer);
    chartInstance.current.setOption(option, true);
  }, [localGraphData, currentLayer]);

  /**
   * 生成图表配置
   */
  const generateChartOption = (data, layer) => {
    const isDark = document.body.classList.contains('dark-theme');
    const textColor = isDark ? '#e0e0e0' : '#333';
    const lineColor = isDark ? '#555' : '#ccc';

    return {
      backgroundColor: 'transparent',
      title: {
        text: getLayerTitle(layer),
        subtext: `知识库: ${knowledgeBaseId}`,
        left: 'center',
        textStyle: {
          color: textColor,
          fontSize: 18
        },
        subtextStyle: {
          color: isDark ? '#999' : '#666'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          if (params.dataType === 'node') {
            return `
              <div style="padding: 10px;">
                <strong>${params.data.name}</strong><br/>
                类型: ${params.data.entityType || '未知'}<br/>
                ${params.data.confidence ? `置信度: ${(params.data.confidence * 100).toFixed(1)}%` : ''}
              </div>
            `;
          }
          return `${params.data.source} → ${params.data.target}`;
        }
      },
      legend: {
        data: data.categories?.map(c => c.name) || [],
        bottom: 10,
        textStyle: { color: textColor }
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: data.nodes || [],
          links: data.links || [],
          categories: data.categories || [],
          roam: true,
          draggable: true,
          focusNodeAdjacency: true,
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 1,
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          },
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
            color: textColor
          },
          lineStyle: {
            color: lineColor,
            curveness: 0.3,
            width: 2
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4
            }
          },
          force: {
            repulsion: 300,
            gravity: 0.1,
            edgeLength: 150,
            layoutAnimation: true
          },
          symbolSize: (value, params) => {
            // 根据重要性调整节点大小
            return params.data.importance ? params.data.importance * 20 + 20 : 30;
          }
        }
      ]
    };
  };

  /**
   * 获取图层标题
   */
  const getLayerTitle = (layer) => {
    const titles = {
      [LayerType.DOCUMENT]: '文档层 - 原始实体关系',
      [LayerType.KNOWLEDGE_BASE]: '知识库层 - 对齐实体',
      [LayerType.GLOBAL]: '全局层 - 跨库链接'
    };
    return titles[layer] || '知识图谱';
  };

  /**
   * 处理图层切换
   */
  const handleLayerChange = (layer) => {
    if (onLayerChange) {
      onLayerChange(layer);
    }
  };

  return (
    <div className="hierarchical-graph-visualizer">
      {/* 图层切换控制 */}
      <div className="layer-controls">
        <button
          className={`layer-btn ${currentLayer === LayerType.DOCUMENT ? 'active' : ''}`}
          onClick={() => handleLayerChange(LayerType.DOCUMENT)}
        >
          <span className="layer-icon">📄</span>
          <span className="layer-name">文档层</span>
          <span className="layer-desc">原始实体关系</span>
        </button>
        <button
          className={`layer-btn ${currentLayer === LayerType.KNOWLEDGE_BASE ? 'active' : ''}`}
          onClick={() => handleLayerChange(LayerType.KNOWLEDGE_BASE)}
        >
          <span className="layer-icon">📚</span>
          <span className="layer-name">知识库层</span>
          <span className="layer-desc">对齐实体</span>
        </button>
        <button
          className={`layer-btn ${currentLayer === LayerType.GLOBAL ? 'active' : ''}`}
          onClick={() => handleLayerChange(LayerType.GLOBAL)}
        >
          <span className="layer-icon">🌐</span>
          <span className="layer-name">全局层</span>
          <span className="layer-desc">跨库链接</span>
        </button>
      </div>

      {/* 统计信息 */}
      {localGraphData && (
        <div className="graph-stats">
          <div className="stat-item">
            <span className="stat-value">{localGraphData.nodes?.length || 0}</span>
            <span className="stat-label">实体</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{localGraphData.links?.length || 0}</span>
            <span className="stat-label">关系</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{localGraphData.categories?.length || 0}</span>
            <span className="stat-label">类型</span>
          </div>
        </div>
      )}

      {/* 图表容器 */}
      <div className="chart-container" style={{ width, height }}>
        {loading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <span>加载图谱数据...</span>
          </div>
        )}
        
        {error && (
          <div className="error-overlay">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{error}</span>
            <button onClick={loadGraphData} className="retry-btn">
              重试
            </button>
          </div>
        )}
        
        <div ref={chartRef} style={{ width: '100%', height: '100%' }} />
      </div>

      {/* 图例说明 */}
      <div className="legend-panel">
        <h4>图层说明</h4>
        <ul>
          <li>
            <strong>文档层：</strong>显示从文档中提取的原始实体和关系
          </li>
          <li>
            <strong>知识库层：</strong>显示对齐后的实体和聚合的关系
          </li>
          <li>
            <strong>全局层：</strong>显示跨知识库的实体链接
          </li>
        </ul>
      </div>
    </div>
  );
};

/**
 * 生成模拟数据
 */
const generateMockData = (layer) => {
  const categories = [
    { name: '人物', itemStyle: { color: '#5470c6' } },
    { name: '组织', itemStyle: { color: '#91cc75' } },
    { name: '地点', itemStyle: { color: '#fac858' } },
    { name: '产品', itemStyle: { color: '#ee6666' } },
    { name: '事件', itemStyle: { color: '#73c0de' } }
  ];

  const nodes = [];
  const links = [];

  // 根据图层生成不同的数据
  if (layer === LayerType.DOCUMENT) {
    // 文档层：更多节点，更分散
    for (let i = 0; i < 30; i++) {
      nodes.push({
        id: `doc_node_${i}`,
        name: `实体${i + 1}`,
        entityType: categories[i % 5].name,
        category: i % 5,
        importance: Math.random(),
        confidence: 0.7 + Math.random() * 0.3,
        documentId: `doc_${Math.floor(i / 5)}`
      });
    }
    // 生成关系
    for (let i = 0; i < 40; i++) {
      const source = Math.floor(Math.random() * 30);
      let target = Math.floor(Math.random() * 30);
      while (target === source) {
        target = Math.floor(Math.random() * 30);
      }
      links.push({
        source: `doc_node_${source}`,
        target: `doc_node_${target}`,
        relation: '关联',
        confidence: 0.6 + Math.random() * 0.4
      });
    }
  } else if (layer === LayerType.KNOWLEDGE_BASE) {
    // 知识库层：对齐后的实体，更少但更准确
    for (let i = 0; i < 20; i++) {
      nodes.push({
        id: `kb_node_${i}`,
        name: `对齐实体${i + 1}`,
        entityType: categories[i % 5].name,
        category: i % 5,
        importance: 0.5 + Math.random() * 0.5,
        confidence: 0.85 + Math.random() * 0.15,
        alignedEntities: [`doc_node_${i}`, `doc_node_${i + 20}`]
      });
    }
    for (let i = 0; i < 25; i++) {
      const source = Math.floor(Math.random() * 20);
      let target = Math.floor(Math.random() * 20);
      while (target === source) {
        target = Math.floor(Math.random() * 20);
      }
      links.push({
        source: `kb_node_${source}`,
        target: `kb_node_${target}`,
        relation: '聚合关系',
        confidence: 0.8 + Math.random() * 0.2
      });
    }
  } else {
    // 全局层：跨知识库链接
    for (let i = 0; i < 15; i++) {
      nodes.push({
        id: `global_node_${i}`,
        name: `全局实体${i + 1}`,
        entityType: categories[i % 5].name,
        category: i % 5,
        importance: 0.7 + Math.random() * 0.3,
        knowledgeBaseId: `kb_${Math.floor(i / 5)}`
      });
    }
    for (let i = 0; i < 20; i++) {
      const source = Math.floor(Math.random() * 15);
      let target = Math.floor(Math.random() * 15);
      while (target === source) {
        target = Math.floor(Math.random() * 15);
      }
      links.push({
        source: `global_node_${source}`,
        target: `global_node_${target}`,
        relation: '跨库链接',
        confidence: 0.75 + Math.random() * 0.25
      });
    }
  }

  return { nodes, links, categories };
};

HierarchicalGraphVisualizer.propTypes = {
  knowledgeBaseId: PropTypes.string.isRequired,
  currentLayer: PropTypes.oneOf(Object.values(LayerType)),
  graphData: PropTypes.object,
  onNodeClick: PropTypes.func,
  onLayerChange: PropTypes.func,
  width: PropTypes.string,
  height: PropTypes.string
};

export default HierarchicalGraphVisualizer;
