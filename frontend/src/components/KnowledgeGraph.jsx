import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { request } from '../utils/apiUtils';
import './KnowledgeGraph.css';

const KnowledgeGraph = ({ documentId, textContent, graphData, width = 800, height = 600 }) => {
  const svgRef = useRef();
  const [internalGraphData, setInternalGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 加载知识图谱数据
  useEffect(() => {
    if (graphData) {
      // 如果提供了graphData，直接使用
      setInternalGraphData(graphData);
    } else if (documentId || textContent) {
      // 否则从API加载数据
      loadGraphData();
    }
  }, [documentId, textContent, graphData]);

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
      }
      
      setInternalGraphData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 渲染知识图谱
  useEffect(() => {
    // 使用internalGraphData作为主要数据源，如果外部提供了graphData则优先使用
    const dataToRender = graphData || internalGraphData;
    if (!dataToRender || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // 清空SVG

    // 确保dataToRender有必要的字段，兼容nodes/links和entities/relationships两种格式
    const entities = dataToRender.nodes || dataToRender.entities || [];
    const relationships = dataToRender.links || dataToRender.relationships || [];
    
    // 检查数据是否为空
    if (entities.length === 0 && relationships.length === 0) {
      // 显示空状态消息
      svg.append("text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#999")
        .text("暂无知识图谱数据");
      return;
    }
    
    // 预处理数据：为实体添加id和name字段
    const processedEntities = entities.map((entity, index) => ({
      ...entity,
      id: entity.id || `entity_${entity.entity_id || index}`,
      name: entity.label || entity.text || entity.name || `实体${index}`
    }));
    
    // 预处理关系：确保source和target是对象引用
    const entityMap = {};
    processedEntities.forEach(entity => {
      entityMap[entity.id] = entity;
    });
    
    const processedRelationships = relationships.map(rel => {
      let source = rel.source;
      let target = rel.target;
      
      // 如果source/target是字符串ID，查找对应的实体对象
      if (typeof source === 'string' || typeof source === 'number') {
        source = entityMap[source] || null;
      }
      if (typeof target === 'string' || typeof target === 'number') {
        target = entityMap[target] || null;
      }
      
      return {
        ...rel,
        source,
        target,
        relation: rel.label || rel.relation || '相关'
      };
    }).filter(rel => rel.source && rel.target);
    
    // 创建力导向图模拟
    const simulation = d3.forceSimulation(processedEntities)
      .force("link", d3.forceLink(processedRelationships).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(50));

    // 创建连线
    const link = svg.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(processedRelationships)
      .enter().append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", d => Math.sqrt(d.confidence || 1));

    // 创建节点
    const node = svg.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(processedEntities)
      .enter().append("g")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // 节点圆圈
    node.append("circle")
      .attr("r", d => {
        // 根据实体重要性调整大小
        if (d.type === 'PERSON') return 10;
        if (d.type === 'ORGANIZATION' || d.type === 'ORG') return 12;
        if (d.type === 'LOCATION' || d.type === 'LOC') return 8;
        return 6;
      })
      .attr("fill", d => {
        // 根据实体类型设置颜色
        switch(d.type) {
          case 'PERSON': return '#ff6b6b';
          case 'ORGANIZATION':
          case 'ORG': return '#4ecdc4';
          case 'LOCATION':
          case 'LOC': return '#45b7d1';
          case 'DATE': return '#96ceb4';
          case 'MONEY': return '#feca57';
          default: return '#a29bfe';
        }
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);

    // 节点标签
    node.append("text")
      .text(d => d.name)
      .attr("font-size", "10px")
      .attr("dx", 12)
      .attr("dy", ".35em")
      .attr("fill", "#2c3e50");

    // 关系标签
    const linkText = svg.append("g")
      .attr("class", "link-labels")
      .selectAll("text")
      .data(processedRelationships)
      .enter().append("text")
      .text(d => d.relation || d.type)
      .attr("font-size", "8px")
      .attr("fill", "#7f8c8d");

    // 更新位置
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("transform", d => `translate(${d.x},${d.y})`);

      linkText
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2);
    });

    // 拖拽函数
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // 双击节点放大显示
    node.on("dblclick", (event, d) => {
      // 放大显示该节点及其关联节点
      const connectedNodes = new Set([d.id]);
      relationships.forEach(rel => {
        if (rel.source.id === d.id) connectedNodes.add(rel.target.id);
        if (rel.target.id === d.id) connectedNodes.add(rel.source.id);
      });

      node.style("opacity", n => connectedNodes.has(n.id) ? 1 : 0.1);
      link.style("opacity", l => 
        connectedNodes.has(l.source.id) && connectedNodes.has(l.target.id) ? 1 : 0.1
      );
    });

    // 双击空白处重置视图
    svg.on("dblclick", () => {
      node.style("opacity", 1);
      link.style("opacity", 1);
    });

  }, [graphData, width, height]);

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
  const dataToRender = graphData || internalGraphData;
  
  if (!dataToRender) {
    return (
      <div className="knowledge-graph-empty">
        <div className="empty-icon">📊</div>
        <span>暂无知识图谱数据</span>
        <button onClick={loadGraphData} className="generate-btn">生成知识图谱</button>
      </div>
    );
  }

  // 获取实际的实体类型
  const getActualEntityTypes = () => {
    if (!dataToRender) return [];
    
    const entities = dataToRender.nodes || dataToRender.entities || [];
    const entityTypes = [...new Set(entities.map(entity => entity.type || entity.group || '未知'))];
    
    // 实体类型映射到中文显示名称
    const typeMapping = {
      'PERSON': '人物',
      'ORG': '组织',
      'ORGANIZATION': '组织',
      'LOC': '地点',
      'LOCATION': '地点',
      'TECH': '技术术语',
      'PRODUCT': '产品',
      'EVENT': '事件',
      'CONCEPT': '概念',
      'DATE': '日期',
      'MONEY': '金额',
      '未知': '未知类型'
    };
    
    return entityTypes.map(type => ({
      type,
      displayName: typeMapping[type] || type,
      cssClass: type.toLowerCase()
    }));
  };

  return (
    <div className="knowledge-graph-container">
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
          <div key={entityType.type} className="legend-item">
            <span className={`legend-color ${entityType.cssClass}`}></span>
            <span>{entityType.displayName}</span>
          </div>
        ))}
      </div>

      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="knowledge-graph-svg"
      />
    </div>
  );
};

export default KnowledgeGraph;