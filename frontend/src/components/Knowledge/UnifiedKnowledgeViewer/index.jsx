/**
 * 一体化知识查看器组件 - FE-009 一体化知识查看器
 *
 * 提供知识图谱展示、向量空间展示、文本片段列表、实体列表、关联网络、统计信息面板
 *
 * @task FE-009
 * @phase 前端功能拓展
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  Network,
  Box,
  FileText,
  Users,
  BarChart3,
  Layers,
  LayoutGrid,
  List,
  ChevronLeft,
  ChevronRight,
  Search,
  Filter,
  Download,
  Eye,
  Link,
  Clock,
  Activity,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Minimize2,
  Settings,
  Tag,
} from '../icons.jsx';
import './UnifiedKnowledgeViewer.css';

/**
 * 知识单元类型
 * @typedef {Object} KnowledgeUnit
 * @property {string} id - 单元ID
 * @property {string} type - 单元类型
 * @property {string} title - 标题
 * @property {string} content - 内容
 * @property {Object} metadata - 元数据
 */

/**
 * 关联关系类型
 * @typedef {Object} Association
 * @property {string} id - 关联ID
 * @property {string} sourceId - 源单元ID
 * @property {string} targetId - 目标单元ID
 * @property {string} type - 关联类型
 * @property {number} strength - 关联强度
 */

/**
 * 生成模拟知识单元
 *
 * @param {number} count - 数量
 * @returns {KnowledgeUnit[]} 知识单元数组
 */
const generateMockUnits = (count = 50) => {
  const types = ['DOCUMENT', 'CHUNK', 'ENTITY', 'RELATIONSHIP', 'CONCEPT'];
  const units = [];

  for (let i = 0; i < count; i++) {
    const type = types[Math.floor(Math.random() * types.length)];
    units.push({
      id: `unit-${i}`,
      type,
      title: `${type} ${i + 1}`,
      content: `这是${type}类型的知识单元内容示例，包含相关的知识和信息。`,
      metadata: {
        createdAt: new Date(Date.now() - Math.random() * 86400000 * 30).toISOString(),
        updatedAt: new Date().toISOString(),
        quality: Math.random() * 100,
        vectorCount: Math.floor(Math.random() * 10),
        entityCount: Math.floor(Math.random() * 5),
      },
    });
  }

  return units;
};

/**
 * 生成模拟关联
 *
 * @param {number} count - 数量
 * @returns {Association[]} 关联数组
 */
const generateMockAssociations = (count = 30) => {
  const types = ['CONTAINS', 'REFERENCES', 'SIMILAR_TO', 'RELATED_TO', 'PART_OF'];
  const associations = [];

  for (let i = 0; i < count; i++) {
    associations.push({
      id: `assoc-${i}`,
      sourceId: `unit-${Math.floor(Math.random() * 50)}`,
      targetId: `unit-${Math.floor(Math.random() * 50)}`,
      type: types[Math.floor(Math.random() * types.length)],
      strength: Math.random(),
    });
  }

  return associations;
};

/**
 * 统计面板组件
 */
const StatisticsPanel = ({ units }) => {
  const stats = useMemo(() => {
    const typeCount = {};
    let totalQuality = 0;
    let totalVectors = 0;
    let totalEntities = 0;

    units.forEach((unit) => {
      typeCount[unit.type] = (typeCount[unit.type] || 0) + 1;
      totalQuality += unit.metadata.quality;
      totalVectors += unit.metadata.vectorCount;
      totalEntities += unit.metadata.entityCount;
    });

    return {
      total: units.length,
      typeCount,
      avgQuality: units.length > 0 ? (totalQuality / units.length).toFixed(1) : 0,
      totalVectors,
      totalEntities,
    };
  }, [units]);

  const typeColors = {
    DOCUMENT: '#1890ff',
    CHUNK: '#52c41a',
    ENTITY: '#faad14',
    RELATIONSHIP: '#722ed1',
    CONCEPT: '#eb2f96',
  };

  return (
    <div className="statistics-panel">
      <h4>统计概览</h4>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#1890ff20', color: '#1890ff' }}>
            <Layers size={20} />
          </div>
          <div className="stat-info">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">知识单元总数</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#52c41a20', color: '#52c41a' }}>
            <Activity size={20} />
          </div>
          <div className="stat-info">
            <div className="stat-value">{stats.avgQuality}</div>
            <div className="stat-label">平均质量分</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#722ed120', color: '#722ed1' }}>
            <Box size={20} />
          </div>
          <div className="stat-info">
            <div className="stat-value">{stats.totalVectors}</div>
            <div className="stat-label">向量总数</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#faad1420', color: '#faad14' }}>
            <Tag size={20} />
          </div>
          <div className="stat-info">
            <div className="stat-value">{stats.totalEntities}</div>
            <div className="stat-label">实体总数</div>
          </div>
        </div>
      </div>

      <div className="type-distribution">
        <h5>类型分布</h5>
        {Object.entries(stats.typeCount).map(([type, count]) => (
          <div key={type} className="type-item">
            <div className="type-label">
              <span
                className="type-dot"
                style={{ background: typeColors[type] || '#8c8c8c' }}
              />
              {type}
            </div>
            <div className="type-bar">
              <div
                className="type-fill"
                style={{
                  width: `${(count / stats.total) * 100}%`,
                  background: typeColors[type] || '#8c8c8c',
                }}
              />
            </div>
            <div className="type-count">{count}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * 知识单元列表组件
 */
const UnitList = ({ units, selectedUnit, onSelect, viewMode }) => {
  const getTypeIcon = (type) => {
    switch (type) {
      case 'DOCUMENT':
        return <FileText size={16} />;
      case 'CHUNK':
        return <Layers size={16} />;
      case 'ENTITY':
        return <Tag size={16} />;
      case 'RELATIONSHIP':
        return <Link size={16} />;
      case 'CONCEPT':
        return <Box size={16} />;
      default:
        return <Layers size={16} />;
    }
  };

  const getTypeColor = (type) => {
    const colors = {
      DOCUMENT: '#1890ff',
      CHUNK: '#52c41a',
      ENTITY: '#faad14',
      RELATIONSHIP: '#722ed1',
      CONCEPT: '#eb2f96',
    };
    return colors[type] || '#8c8c8c';
  };

  if (viewMode === 'grid') {
    return (
      <div className="unit-grid">
        {units.map((unit) => (
          <div
            key={unit.id}
            className={`unit-card ${selectedUnit?.id === unit.id ? 'selected' : ''}`}
            onClick={() => onSelect(unit)}
          >
            <div className="unit-card-header">
              <div
                className="unit-type-icon"
                style={{ color: getTypeColor(unit.type) }}
              >
                {getTypeIcon(unit.type)}
              </div>
              <span className="unit-type-label">{unit.type}</span>
            </div>
            <h5 className="unit-title">{unit.title}</h5>
            <p className="unit-content">{unit.content}</p>
            <div className="unit-meta">
              <span className="quality-badge">
                质量: {unit.metadata.quality.toFixed(0)}
              </span>
              <span className="date-badge">
                {new Date(unit.metadata.updatedAt).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="unit-list">
      {units.map((unit) => (
        <div
          key={unit.id}
          className={`unit-list-item ${selectedUnit?.id === unit.id ? 'selected' : ''}`}
          onClick={() => onSelect(unit)}
        >
          <div
            className="unit-type-icon"
            style={{ color: getTypeColor(unit.type) }}
          >
            {getTypeIcon(unit.type)}
          </div>
          <div className="unit-info">
            <h5 className="unit-title">{unit.title}</h5>
            <p className="unit-content">{unit.content}</p>
          </div>
          <div className="unit-stats">
            <span className="quality-score">
              {unit.metadata.quality.toFixed(0)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * 知识图谱可视化组件（简化版）
 */
const KnowledgeGraph = ({ units, associations, onNodeClick }) => {
  const [zoom, setZoom] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // 计算节点位置（力导向布局简化版）
  const nodePositions = useMemo(() => {
    const positions = {};
    const centerX = 400;
    const centerY = 300;
    const radius = 200;

    units.forEach((unit, index) => {
      const angle = (index / units.length) * 2 * Math.PI;
      positions[unit.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    return positions;
  }, [units]);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const getNodeColor = (type) => {
    const colors = {
      DOCUMENT: '#1890ff',
      CHUNK: '#52c41a',
      ENTITY: '#faad14',
      RELATIONSHIP: '#722ed1',
      CONCEPT: '#eb2f96',
    };
    return colors[type] || '#8c8c8c';
  };

  return (
    <div
      className="knowledge-graph"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="graph-controls">
        <button onClick={() => setZoom((z) => Math.min(z * 1.2, 3))}>+</button>
        <button onClick={() => setZoom((z) => Math.max(z / 1.2, 0.5))}>-</button>
        <button onClick={() => { setZoom(1); setPosition({ x: 0, y: 0 }); }}>
          重置
        </button>
      </div>

      <svg
        width="100%"
        height="100%"
        viewBox="0 0 800 600"
        style={{
          transform: `translate(${position.x}px, ${position.y}px) scale(${zoom})`,
          cursor: isDragging ? 'grabbing' : 'grab',
        }}
      >
        {/* 连线 */}
        {associations.map((assoc) => {
          const source = nodePositions[assoc.sourceId];
          const target = nodePositions[assoc.targetId];
          if (!source || !target) return null;

          return (
            <line
              key={assoc.id}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke="#d9d9d9"
              strokeWidth={assoc.strength * 3}
              opacity={0.6}
            />
          );
        })}

        {/* 节点 */}
        {units.map((unit) => {
          const pos = nodePositions[unit.id];
          if (!pos) return null;

          return (
            <g
              key={unit.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              onClick={() => onNodeClick?.(unit)}
              style={{ cursor: 'pointer' }}
            >
              <circle
                r={20}
                fill={getNodeColor(unit.type)}
                stroke="#fff"
                strokeWidth={2}
              />
              <text
                y={35}
                textAnchor="middle"
                fontSize={12}
                fill="#262626"
              >
                {unit.title}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

/**
 * 实体列表组件
 */
const EntityList = ({ entities, onSelect }) => {
  return (
    <div className="entity-list">
      {entities.map((entity) => (
        <div
          key={entity.id}
          className="entity-item"
          onClick={() => onSelect?.(entity)}
        >
          <div className="entity-header">
            <Tag size={16} className="entity-icon" />
            <span className="entity-name">{entity.title}</span>
            <span className="entity-type">{entity.type}</span>
          </div>
          <p className="entity-description">{entity.content}</p>
          <div className="entity-meta">
            <span>质量: {entity.metadata.quality.toFixed(0)}</span>
            <span>向量: {entity.metadata.vectorCount}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * 关联网络组件
 */
const AssociationNetwork = ({ associations, units }) => {
  const unitMap = useMemo(() => {
    const map = {};
    units.forEach((unit) => {
      map[unit.id] = unit;
    });
    return map;
  }, [units]);

  const getTypeLabel = (type) => {
    const labels = {
      CONTAINS: '包含',
      REFERENCES: '引用',
      SIMILAR_TO: '相似',
      RELATED_TO: '相关',
      PART_OF: '属于',
    };
    return labels[type] || type;
  };

  return (
    <div className="association-network">
      {associations.map((assoc) => {
        const source = unitMap[assoc.sourceId];
        const target = unitMap[assoc.targetId];
        if (!source || !target) return null;

        return (
          <div key={assoc.id} className="association-item">
            <div className="association-nodes">
              <span className="node-name">{source.title}</span>
              <span className="association-arrow">→</span>
              <span className="node-name">{target.title}</span>
            </div>
            <div className="association-info">
              <span className="association-type">{getTypeLabel(assoc.type)}</span>
              <div className="strength-bar">
                <div
                  className="strength-fill"
                  style={{ width: `${assoc.strength * 100}%` }}
                />
              </div>
              <span className="strength-value">
                {(assoc.strength * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

/**
 * 详情面板组件
 */
const DetailPanel = ({ unit, onClose }) => {
  if (!unit) {
    return (
      <div className="detail-panel empty">
        <Eye size={48} color="#d9d9d9" />
        <p>选择一个知识单元查看详情</p>
      </div>
    );
  }

  return (
    <div className="detail-panel">
      <div className="detail-header">
        <h4>{unit.title}</h4>
        <button className="close-btn" onClick={onClose}>
          <ChevronRight size={20} />
        </button>
      </div>

      <div className="detail-content">
        <div className="detail-section">
          <h5>基本信息</h5>
          <div className="detail-row">
            <span className="detail-label">类型</span>
            <span className="detail-value">{unit.type}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">ID</span>
            <span className="detail-value">{unit.id}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">质量分数</span>
            <span className="detail-value">{unit.metadata.quality.toFixed(1)}</span>
          </div>
        </div>

        <div className="detail-section">
          <h5>内容</h5>
          <p className="detail-text">{unit.content}</p>
        </div>

        <div className="detail-section">
          <h5>元数据</h5>
          <div className="detail-row">
            <span className="detail-label">创建时间</span>
            <span className="detail-value">
              {new Date(unit.metadata.createdAt).toLocaleString()}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">更新时间</span>
            <span className="detail-value">
              {new Date(unit.metadata.updatedAt).toLocaleString()}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">向量数量</span>
            <span className="detail-value">{unit.metadata.vectorCount}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">实体数量</span>
            <span className="detail-value">{unit.metadata.entityCount}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 一体化知识查看器组件
 */
const UnifiedKnowledgeViewer = ({
  units: initialUnits,
  associations: initialAssociations,
  onUnitSelect,
  onExport,
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [viewMode, setViewMode] = useState('list');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('ALL');

  // 使用真实数据，如果没有则返回空数组
  const units = initialUnits || [];
  const associations = initialAssociations || [];

  // 过滤单元
  const filteredUnits = useMemo(() => {
    return units.filter((unit) => {
      const matchesSearch =
        !searchQuery ||
        unit.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        unit.content.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = filterType === 'ALL' || unit.type === filterType;
      return matchesSearch && matchesType;
    });
  }, [units, searchQuery, filterType]);

  // 实体列表
  const entities = useMemo(() => {
    return units.filter((unit) => unit.type === 'ENTITY');
  }, [units]);

  // 处理单元选择
  const handleUnitSelect = useCallback((unit) => {
    setSelectedUnit(unit);
    onUnitSelect?.(unit);
  }, [onUnitSelect]);

  // Tab配置
  const tabs = [
    { id: 'overview', label: '概览', icon: BarChart3 },
    { id: 'graph', label: '知识图谱', icon: Network },
    { id: 'units', label: '知识单元', icon: Layers },
    { id: 'entities', label: '实体列表', icon: Users },
    { id: 'associations', label: '关联网络', icon: Link },
  ];

  // 渲染内容区域
  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="tab-content overview">
            <StatisticsPanel units={filteredUnits} />
            <div className="recent-units">
              <h4>最近更新</h4>
              <UnitList
                units={filteredUnits.slice(0, 5)}
                selectedUnit={selectedUnit}
                onSelect={handleUnitSelect}
                viewMode="list"
              />
            </div>
          </div>
        );

      case 'graph':
        return (
          <div className="tab-content graph">
            <KnowledgeGraph
              units={filteredUnits}
              associations={associations}
              onNodeClick={handleUnitSelect}
            />
          </div>
        );

      case 'units':
        return (
          <div className="tab-content units">
            <div className="content-toolbar">
              <div className="view-toggle">
                <button
                  className={viewMode === 'list' ? 'active' : ''}
                  onClick={() => setViewMode('list')}
                >
                  <List size={16} />
                </button>
                <button
                  className={viewMode === 'grid' ? 'active' : ''}
                  onClick={() => setViewMode('grid')}
                >
                  <Grid size={16} />
                </button>
              </div>
            </div>
            <UnitList
              units={filteredUnits}
              selectedUnit={selectedUnit}
              onSelect={handleUnitSelect}
              viewMode={viewMode}
            />
          </div>
        );

      case 'entities':
        return (
          <div className="tab-content entities">
            <EntityList entities={entities} onSelect={handleUnitSelect} />
          </div>
        );

      case 'associations':
        return (
          <div className="tab-content associations">
            <AssociationNetwork associations={associations} units={units} />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="unified-knowledge-viewer">
      {/* 侧边栏 */}
      <div className={`viewer-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <Box size={24} />
          {!sidebarCollapsed && <span>知识查看器</span>}
        </div>

        {!sidebarCollapsed && (
          <>
            {/* 搜索 */}
            <div className="search-box">
              <Search size={16} />
              <input
                type="text"
                placeholder="搜索知识单元..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* 过滤器 */}
            <div className="filter-section">
              <div className="filter-header">
                <Filter size={14} />
                <span>类型过滤</span>
              </div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="ALL">全部类型</option>
                <option value="DOCUMENT">文档</option>
                <option value="CHUNK">片段</option>
                <option value="ENTITY">实体</option>
                <option value="RELATIONSHIP">关系</option>
                <option value="CONCEPT">概念</option>
              </select>
            </div>
          </>
        )}

        {/* Tab导航 */}
        <nav className="tab-nav">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon size={18} />
              {!sidebarCollapsed && <span>{tab.label}</span>}
            </button>
          ))}
        </nav>

        {/* 折叠按钮 */}
        <button
          className="collapse-btn"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          {sidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      {/* 主内容区 */}
      <div className="viewer-main">
        {/* 工具栏 */}
        <div className="viewer-toolbar">
          <h3>{tabs.find((t) => t.id === activeTab)?.label}</h3>
          <div className="toolbar-actions">
            <button className="toolbar-btn" onClick={onExport}>
              <Download size={16} />
              导出
            </button>
            <button className="toolbar-btn">
              <Settings size={16} />
              设置
            </button>
          </div>
        </div>

        {/* 内容 */}
        {renderContent()}
      </div>

      {/* 详情面板 */}
      <DetailPanel unit={selectedUnit} onClose={() => setSelectedUnit(null)} />
    </div>
  );
};

export default UnifiedKnowledgeViewer;
