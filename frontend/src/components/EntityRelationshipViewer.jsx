import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import './EntityRelationshipViewer.css';

const EntityRelationshipViewer = ({ 
  entity, 
  relationships = [], 
  allEntities = [],
  width = 400,
  height = 300,
  onEntitySelect,
  onRelationshipSelect
}) => {
  const svgRef = useRef();
  const [expanded, setExpanded] = useState(false);
  const [selectedSubEntity, setSelectedSubEntity] = useState(null);
  const [graphData, setGraphData] = useState(null);

  // 构建子图数据
  useEffect(() => {
    if (!entity || !relationships.length) return;

    // 找到与当前实体相关的所有关系
    const relatedRelationships = relationships.filter(rel => 
      rel.subject === entity.text || rel.object === entity.text
    );

    // 找到相关的实体
    const relatedEntityIds = new Set();
    relatedRelationships.forEach(rel => {
      relatedEntityIds.add(rel.subject);
      relatedEntityIds.add(rel.object);
    });

    const relatedEntities = allEntities.filter(e => 
      relatedEntityIds.has(e.text) && e.text !== entity.text
    );

    // 构建子图数据
    const subGraphData = {
      entities: [entity, ...relatedEntities],
      relationships: relatedRelationships
    };

    setGraphData(subGraphData);
  }, [entity, relationships, allEntities]);

  // 渲染子图
  useEffect(() => {
    if (!graphData || !svgRef.current || !expanded) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const { entities, relationships } = graphData;

    // 预处理数据
    const processedEntities = entities.map((e, index) => ({
      ...e,
      id: index,
      name: e.text || e.name,
      isCenter: e.text === entity.text
    }));

    const processedRelationships = relationships.map(rel => ({
      ...rel,
      source: processedEntities.find(e => e.text === rel.subject),
      target: processedEntities.find(e => e.text === rel.object)
    })).filter(rel => rel.source && rel.target);

    // 创建力导向图模拟
    const simulation = d3.forceSimulation(processedEntities)
      .force("link", d3.forceLink(processedRelationships).id(d => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    // 创建连线
    const link = svg.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(processedRelationships)
      .enter().append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", d => Math.sqrt(d.confidence || 1))
      .on("click", (event, d) => {
        if (onRelationshipSelect) onRelationshipSelect(d);
      });

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
      .attr("r", d => d.isCenter ? 12 : 8)
      .attr("fill", d => getEntityColor(d))
      .attr("stroke", d => d.isCenter ? "#ff6b6b" : "#fff")
      .attr("stroke-width", d => d.isCenter ? 3 : 1.5)
      .on("click", (event, d) => {
        setSelectedSubEntity(d);
        if (onEntitySelect) onEntitySelect(d);
      });

    // 节点标签
    node.append("text")
      .text(d => d.name.length > 10 ? d.name.substring(0, 10) + '...' : d.name)
      .attr("font-size", "8px")
      .attr("dx", 10)
      .attr("dy", ".35em")
      .attr("fill", "#2c3e50");

    // 关系标签
    const linkText = svg.append("g")
      .attr("class", "link-labels")
      .selectAll("text")
      .data(processedRelationships)
      .enter().append("text")
      .text(d => d.relation)
      .attr("font-size", "6px")
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

    return () => {
      simulation.stop();
    };
  }, [graphData, width, height, expanded]);

  const getEntityColor = (entity) => {
    switch(entity.type) {
      case 'PERSON': return '#ff6b6b';
      case 'ORGANIZATION':
      case 'ORG': return '#4ecdc4';
      case 'LOCATION':
      case 'LOC': return '#45b7d1';
      case 'DATE': return '#96ceb4';
      case 'MONEY': return '#feca57';
      default: return '#a29bfe';
    }
  };

  if (!entity) {
    return (
      <div className="entity-relationship-viewer empty">
        <div className="empty-icon">👥</div>
        <p>选择实体查看关系网络</p>
      </div>
    );
  }

  const directRelationships = relationships.filter(rel => 
    rel.subject === entity.text || rel.object === entity.text
  );

  const incomingRelationships = directRelationships.filter(rel => rel.object === entity.text);
  const outgoingRelationships = directRelationships.filter(rel => rel.subject === entity.text);

  return (
    <div className="entity-relationship-viewer">
      <div className="viewer-header">
        <h4>实体关系网络</h4>
        <div className="entity-badge">
          <span 
            className="entity-color"
            style={{ backgroundColor: getEntityColor(entity) }}
          ></span>
          <span className="entity-name">{entity.name || entity.text}</span>
          <span className="entity-type">{entity.type}</span>
        </div>
      </div>

      <div className="relationship-stats">
        <div className="stat-item">
          <span className="stat-label">总关系数:</span>
          <span className="stat-value">{directRelationships.length}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">入度关系:</span>
          <span className="stat-value">{incomingRelationships.length}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">出度关系:</span>
          <span className="stat-value">{outgoingRelationships.length}</span>
        </div>
      </div>

      <div className="relationship-list">
        <h5>直接关系</h5>
        <div className="relationships">
          {directRelationships.map((rel, index) => (
            <div 
              key={index} 
              className="relationship-item"
              onClick={() => onRelationshipSelect && onRelationshipSelect(rel)}
            >
              <div className="relationship-direction">
                {rel.subject === entity.text ? '→' : '←'}
              </div>
              <div className="relationship-content">
                <span className="relation-type">{rel.relation}</span>
                <span className="related-entity">
                  {rel.subject === entity.text ? rel.object : rel.subject}
                </span>
                {rel.confidence && (
                  <span className="confidence">
                    {(rel.confidence * 100).toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="graph-section">
        <div className="graph-header">
          <h5>关系网络图</h5>
          <button 
            className="toggle-btn"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? '收起' : '展开'}
          </button>
        </div>

        {expanded && (
          <div className="graph-container">
            <svg
              ref={svgRef}
              width={width}
              height={height}
              className="relationship-graph"
            />
            
            {selectedSubEntity && (
              <div className="sub-entity-details">
                <h6>选中实体</h6>
                <p><strong>名称:</strong> {selectedSubEntity.name}</p>
                <p><strong>类型:</strong> {selectedSubEntity.type}</p>
                <button 
                  className="close-btn"
                  onClick={() => setSelectedSubEntity(null)}
                >
                  关闭
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {directRelationships.length > 0 && (
        <div className="relationship-analysis">
          <h5>关系分析</h5>
          <div className="analysis-items">
            <div className="analysis-item">
              <span className="analysis-label">最频繁关系:</span>
              <span className="analysis-value">
                {getMostFrequentRelation(directRelationships)}
              </span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">平均置信度:</span>
              <span className="analysis-value">
                {getAverageConfidence(directRelationships)}%
              </span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">关联实体数:</span>
              <span className="analysis-value">
                {getUniqueRelatedEntities(directRelationships, entity.text)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// 辅助函数
const getMostFrequentRelation = (relationships) => {
  const relationCounts = {};
  relationships.forEach(rel => {
    relationCounts[rel.relation] = (relationCounts[rel.relation] || 0) + 1;
  });
  
  const mostFrequent = Object.keys(relationCounts).reduce((a, b) => 
    relationCounts[a] > relationCounts[b] ? a : b
  );
  
  return mostFrequent;
};

const getAverageConfidence = (relationships) => {
  const validRelationships = relationships.filter(rel => rel.confidence);
  if (validRelationships.length === 0) return 'N/A';
  
  const sum = validRelationships.reduce((acc, rel) => acc + rel.confidence, 0);
  return (sum / validRelationships.length * 100).toFixed(1);
};

const getUniqueRelatedEntities = (relationships, entityText) => {
  const entities = new Set();
  relationships.forEach(rel => {
    if (rel.subject !== entityText) entities.add(rel.subject);
    if (rel.object !== entityText) entities.add(rel.object);
  });
  return entities.size;
};

export default EntityRelationshipViewer;