/**
 * 简化版知识图谱组件
 * 
 * 用于显示知识图谱关系图，包含最基本的功能
 */

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const SimpleKnowledgeGraph = ({ data, width = 800, height = 600 }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data || !svgRef.current) {
      console.log('SimpleKnowledgeGraph: data or svgRef is null');
      console.log('data:', data);
      console.log('svgRef:', svgRef.current);
      return;
    }

    console.log('SimpleKnowledgeGraph data:', data);
    console.log('SimpleKnowledgeGraph width:', width);
    console.log('SimpleKnowledgeGraph height:', height);
    console.log('SimpleKnowledgeGraph svgRef:', svgRef.current);

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // 确保SVG尺寸正确
    svg.attr("width", width)
       .attr("height", height);

    const entities = data.entities || data.nodes || [];
    const relationships = data.relationships || data.links || [];

    console.log('Entities:', entities);
    console.log('Relationships:', relationships);
    console.log('Entities length:', entities.length);
    console.log('Relationships length:', relationships.length);

    if (entities.length === 0 || relationships.length === 0) {
      svg.append("text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#999")
        .text("暂无知识图谱数据");
      return;
    }

    // 预处理数据
    const processedEntities = entities.map((entity, index) => ({
      ...entity,
      id: entity.id || entity.entity_id || `entity_${index}`,
      name: entity.name || entity.label || entity.text || `实体${index}`,
      type: entity.type || entity.category || '默认',
      x: Math.random() * width,
      y: Math.random() * height
    }));

    const entityMap = {};
    processedEntities.forEach(entity => {
      entityMap[entity.id] = entity;
    });

    const processedRelationships = relationships.map(rel => {
      let source = rel.source;
      let target = rel.target;

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
        relation: rel.relation || rel.label || '相关'
      };
    }).filter(rel => rel.source && rel.target && rel.source.id && rel.target.id);

    console.log('Processed entities:', processedEntities);
    console.log('Processed relationships:', processedRelationships);

    // 创建力导向图模拟
    const simulation = d3.forceSimulation(processedEntities)
      .force("link", d3.forceLink(processedRelationships).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // 创建SVG元素
    const g = svg.append("g");

    // 创建连线
    const link = g.append("g").selectAll("line")
      .data(processedRelationships)
      .enter().append("line")
      .attr("stroke", "#94a3b8")
      .attr("stroke-width", 2);

    // 创建节点
    const node = g.append("g").selectAll("g")
      .data(processedEntities)
      .enter().append("g")
      .call(d3.drag()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // 节点圆圈
    node.append("circle")
      .attr("r", 15)
      .attr("fill", "#3498db")
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    // 节点标签
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 5)
      .attr("fill", "#fff")
      .text(d => d.name);

    // 关系标签
    const linkText = g.append("g").selectAll("text")
      .data(processedRelationships)
      .enter().append("text")
      .attr("text-anchor", "middle")
      .attr("fill", "#64748b")
      .text(d => d.relation);

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
        .attr("transform", d => {
          const x = (d.source.x + d.target.x) / 2;
          const y = (d.source.y + d.target.y) / 2;
          return `translate(${x},${y})`;
        });
    });

    // 组件卸载时停止模拟
    return () => {
      simulation.stop();
    };
  }, [data, width, height]);

  return (
    <div className="simple-knowledge-graph-container" style={{ width: '100%', height: '100%', minHeight: '600px' }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
      />
    </div>
  );
};

export default SimpleKnowledgeGraph;