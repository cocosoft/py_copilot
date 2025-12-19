import React, { useState, useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import './EnhancedKnowledgeGraph.css';

const EnhancedKnowledgeGraph = ({ 
  documentId, 
  textContent, 
  width = 800, 
  height = 600,
  onEntitySelect,
  onRelationshipSelect,
  searchQuery = ''
}) => {
  const svgRef = useRef();
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [selectedRelationship, setSelectedRelationship] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [filteredEntities, setFilteredEntities] = useState([]);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [simulation, setSimulation] = useState(null);

  // 加载知识图谱数据
  useEffect(() => {
    if (documentId || textContent) {
      loadGraphData();
    }
  }, [documentId, textContent]);

  // 处理搜索查询
  useEffect(() => {
    if (searchQuery && graphData) {
      performSemanticSearch(searchQuery);
    } else {
      setSearchResults([]);
      setFilteredEntities(graphData?.entities || []);
    }
  }, [searchQuery, graphData]);

  const loadGraphData = async () => {
    setLoading(true);
    setError('');
    
    try {
      let data;
      
      if (documentId) {
        const response = await fetch(`/api/v1/knowledge-graph/document/${documentId}/entities`);
        if (!response.ok) throw new Error('获取文档实体失败');
        data = await response.json();
      } else if (textContent) {
        const response = await fetch('/api/v1/knowledge-graph/extract-entities', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: textContent })
        });
        if (!response.ok) throw new Error('提取实体关系失败');
        data = await response.json();
      }
      
      setGraphData(data);
      setFilteredEntities(data?.entities || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const performSemanticSearch = async (query) => {
    try {
      const response = await fetch('/api/v1/knowledge-graph/semantic-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query, 
          document_id: documentId,
          limit: 20 
        })
      });
      
      if (response.ok) {
        const results = await response.json();
        setSearchResults(results);
        
        // 高亮匹配的实体
        const matchedEntityIds = results.map(result => result.entity_id);
        const filtered = graphData.entities.filter(entity => 
          matchedEntityIds.includes(entity.id) || 
          entity.text.toLowerCase().includes(query.toLowerCase())
        );
        setFilteredEntities(filtered);
      }
    } catch (err) {
      console.error('语义搜索失败:', err);
    }
  };

  // 渲染知识图谱
  useEffect(() => {
    if (!graphData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const { entities, relationships } = graphData;
    
    // 预处理数据
    const processedEntities = entities.map((entity, index) => ({
      ...entity,
      id: entity.id || index,
      name: entity.text || entity.name || `实体${index}`,
      isHighlighted: searchResults.some(result => result.entity_id === entity.id)
    }));
    
    const processedRelationships = relationships.map(rel => ({
      ...rel,
      source: processedEntities.find(e => e.text === rel.subject) || { id: -1 },
      target: processedEntities.find(e => e.text === rel.object) || { id: -1 }
    })).filter(rel => rel.source.id !== -1 && rel.target.id !== -1);

    // 创建力导向图模拟
    const newSimulation = d3.forceSimulation(processedEntities)
      .force("link", d3.forceLink(processedRelationships).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(50));

    setSimulation(newSimulation);

    // 创建缩放行为
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        svg.select(".graph-content").attr("transform", event.transform);
        setZoomLevel(event.transform.k);
      });

    svg.call(zoom);

    // 创建图形内容容器
    const graphContent = svg.append("g").attr("class", "graph-content");

    // 创建连线
    const link = graphContent.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(processedRelationships)
      .enter().append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", d => Math.sqrt(d.confidence || 1))
      .on("click", (event, d) => {
        setSelectedRelationship(d);
        if (onRelationshipSelect) onRelationshipSelect(d);
      });

    // 创建节点
    const node = graphContent.append("g")
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
      .attr("r", d => getEntityRadius(d))
      .attr("fill", d => getEntityColor(d))
      .attr("stroke", d => d.isHighlighted ? "#ff6b6b" : "#fff")
      .attr("stroke-width", d => d.isHighlighted ? 3 : 1.5)
      .on("click", (event, d) => {
        setSelectedEntity(d);
        if (onEntitySelect) onEntitySelect(d);
      });

    // 节点标签
    node.append("text")
      .text(d => d.name)
      .attr("font-size", "10px")
      .attr("dx", 12)
      .attr("dy", ".35em")
      .attr("fill", "#2c3e50")
      .attr("class", "entity-label");

    // 关系标签
    const linkText = graphContent.append("g")
      .attr("class", "link-labels")
      .selectAll("text")
      .data(processedRelationships)
      .enter().append("text")
      .text(d => d.relation || d.type)
      .attr("font-size", "8px")
      .attr("fill", "#7f8c8d");

    // 更新位置
    newSimulation.on("tick", () => {
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
      if (!event.active) newSimulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) newSimulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // 双击节点放大显示
    node.on("dblclick", (event, d) => {
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

    return () => {
      if (newSimulation) newSimulation.stop();
    };
  }, [graphData, width, height, searchResults]);

  const getEntityRadius = (entity) => {
    if (entity.isHighlighted) return 15;
    if (entity.type === 'PERSON') return 10;
    if (entity.type === 'ORGANIZATION' || entity.type === 'ORG') return 12;
    if (entity.type === 'LOCATION' || entity.type === 'LOC') return 8;
    return 6;
  };

  const getEntityColor = (entity) => {
    if (entity.isHighlighted) return '#ff6b6b';
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

  const resetView = () => {
    if (simulation) {
      simulation.alpha(1).restart();
    }
    setSelectedEntity(null);
    setSelectedRelationship(null);
  };

  const exportGraph = () => {
    const svgElement = svgRef.current;
    const svgData = new XMLSerializer().serializeToString(svgElement);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'knowledge-graph.svg';
    link.click();
  };

  if (loading) {
    return (
      <div className="enhanced-knowledge-graph-loading">
        <div className="loading-spinner"></div>
        <span>正在生成知识图谱...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="enhanced-knowledge-graph-error">
        <div className="error-icon">⚠️</div>
        <span>{error}</span>
        <button onClick={loadGraphData} className="retry-btn">重试</button>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="enhanced-knowledge-graph-empty">
        <div className="empty-icon">📊</div>
        <span>暂无知识图谱数据</span>
        <button onClick={loadGraphData} className="generate-btn">生成知识图谱</button>
      </div>
    );
  }

  return (
    <div className="enhanced-knowledge-graph-container">
      <div className="graph-header">
        <h3>增强知识图谱</h3>
        <div className="graph-stats">
          <span>实体: {graphData.entities?.length || 0}</span>
          <span>关系: {graphData.relationships?.length || 0}</span>
          {searchQuery && <span>搜索结果: {searchResults.length}</span>}
        </div>
        <div className="graph-controls">
          <button onClick={loadGraphData} className="refresh-btn">刷新</button>
          <button onClick={resetView} className="reset-btn">重置视图</button>
          <button onClick={exportGraph} className="export-btn">导出SVG</button>
          <span className="zoom-level">缩放: {Math.round(zoomLevel * 100)}%</span>
        </div>
      </div>
      
      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-color person"></span>
          <span>人物</span>
        </div>
        <div className="legend-item">
          <span className="legend-color organization"></span>
          <span>组织</span>
        </div>
        <div className="legend-item">
          <span className="legend-color location"></span>
          <span>地点</span>
        </div>
        <div className="legend-item">
          <span className="legend-color date"></span>
          <span>日期</span>
        </div>
        <div className="legend-item">
          <span className="legend-color money"></span>
          <span>金额</span>
        </div>
        <div className="legend-item">
          <span className="legend-color highlighted"></span>
          <span>搜索结果</span>
        </div>
      </div>

      <div className="graph-details">
        {selectedEntity && (
          <div className="entity-details">
            <h4>实体详情</h4>
            <p><strong>名称:</strong> {selectedEntity.name}</p>
            <p><strong>类型:</strong> {selectedEntity.type}</p>
            <p><strong>置信度:</strong> {selectedEntity.confidence || 'N/A'}</p>
            {selectedEntity.start && <p><strong>位置:</strong> {selectedEntity.start}-{selectedEntity.end}</p>}
          </div>
        )}
        
        {selectedRelationship && (
          <div className="relationship-details">
            <h4>关系详情</h4>
            <p><strong>关系:</strong> {selectedRelationship.relation}</p>
            <p><strong>主体:</strong> {selectedRelationship.subject}</p>
            <p><strong>客体:</strong> {selectedRelationship.object}</p>
            <p><strong>置信度:</strong> {selectedRelationship.confidence || 'N/A'}</p>
          </div>
        )}
      </div>

      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="enhanced-knowledge-graph-svg"
      />
    </div>
  );
};

export default EnhancedKnowledgeGraph;