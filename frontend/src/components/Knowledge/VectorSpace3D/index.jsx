/**
 * 向量空间3D可视化组件 - FE-006 向量空间3D可视化
 *
 * 使用Canvas实现3D散点图展示、视角旋转缩放、聚类可视化、向量搜索高亮
 *
 * @task FE-006
 * @phase 前端功能拓展
 */

import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import {
  RotateCw,
  ZoomIn,
  ZoomOut,
  Move,
  Search,
  Filter,
  Grid3X3,
  Eye,
  EyeOff,
  RefreshCw,
  Download,
  Maximize2,
} from '../icons.jsx';
import './VectorSpace3D.css';

/**
 * 3D点数据结构
 * @typedef {Object} Point3D
 * @property {string} id - 点ID
 * @property {number} x - X坐标
 * @property {number} y - Y坐标
 * @property {number} z - Z坐标
 * @property {string} label - 标签
 * @property {number} cluster - 聚类ID
 * @property {string} color - 颜色
 * @property {number} size - 点大小
 * @property {Object} metadata - 元数据
 */

/**
 * 3D相机参数
 * @typedef {Object} Camera3D
 * @property {number} x - 相机X位置
 * @property {number} y - 相机Y位置
 * @property {number} z - 相机Z位置
 * @property {number} rotX - X轴旋转角度
 * @property {number} rotY - Y轴旋转角度
 * @property {number} zoom - 缩放比例
 */

/**
 * 默认相机参数
 */
const DEFAULT_CAMERA = {
  x: 0,
  y: 0,
  z: 500,
  rotX: 0.3,
  rotY: 0.5,
  zoom: 1,
};

/**
 * 聚类颜色配置
 */
const CLUSTER_COLORS = [
  '#1890ff', // 蓝色
  '#52c41a', // 绿色
  '#faad14', // 黄色
  '#f5222d', // 红色
  '#722ed1', // 紫色
  '#13c2c2', // 青色
  '#eb2f96', // 粉色
  '#fa8c16', // 橙色
];

/**
 * 3D到2D投影
 *
 * @param {Point3D} point - 3D点
 * @param {Camera3D} camera - 相机参数
 * @param {number} width - 画布宽度
 * @param {number} height - 画布高度
 * @returns {Object} 投影后的2D坐标和深度
 */
const project3DTo2D = (point, camera, width, height) => {
  // 应用相机旋转
  const cosX = Math.cos(camera.rotX);
  const sinX = Math.sin(camera.rotX);
  const cosY = Math.cos(camera.rotY);
  const sinY = Math.sin(camera.rotY);

  // 旋转点
  const x1 = point.x * cosY - point.z * sinY;
  const z1 = point.x * sinY + point.z * cosY;
  const y1 = point.y * cosX - z1 * sinX;
  const z2 = point.y * sinX + z1 * cosX;

  // 应用相机位置
  const x2 = x1 - camera.x;
  const y2 = y1 - camera.y;
  const z3 = z2 - camera.z;

  // 透视投影
  const fov = 800;
  const scale = (fov / (fov + z3)) * camera.zoom;

  return {
    x: width / 2 + x2 * scale,
    y: height / 2 - y2 * scale,
    scale,
    depth: z3,
  };
};

/**
 * 生成模拟向量数据
 *
 * @param {number} count - 数据点数量
 * @param {number} clusterCount - 聚类数量
 * @returns {Point3D[]} 3D点数组
 */
const generateMockData = (count = 500, clusterCount = 4) => {
  const points = [];
  const clusterCenters = [];

  // 生成聚类中心
  for (let i = 0; i < clusterCount; i++) {
    clusterCenters.push({
      x: (Math.random() - 0.5) * 300,
      y: (Math.random() - 0.5) * 300,
      z: (Math.random() - 0.5) * 300,
    });
  }

  // 生成数据点
  for (let i = 0; i < count; i++) {
    const clusterId = Math.floor(Math.random() * clusterCount);
    const center = clusterCenters[clusterId];
    const spread = 50 + Math.random() * 30;

    points.push({
      id: `point-${i}`,
      x: center.x + (Math.random() - 0.5) * spread,
      y: center.y + (Math.random() - 0.5) * spread,
      z: center.z + (Math.random() - 0.5) * spread,
      label: `Vector ${i}`,
      cluster: clusterId,
      color: CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length],
      size: 3 + Math.random() * 2,
      metadata: {
        documentId: `doc-${Math.floor(Math.random() * 10)}`,
        chunkId: `chunk-${i}`,
        score: Math.random(),
      },
    });
  }

  return points;
};

/**
 * 3D向量空间可视化组件
 */
const VectorSpace3D = ({
  data,
  width = 800,
  height = 600,
  onPointClick,
  onPointHover,
  highlightedPoints = [],
  searchQuery = '',
  showGrid = true,
  showAxes = true,
  clusterVisibility = {},
}) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const animationIdRef = useRef(null);
  const [camera, setCamera] = useState(DEFAULT_CAMERA);
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [isAutoRotating, setIsAutoRotating] = useState(false);

  // 使用传入的真实数据，如果没有则返回空数组
  const points = useMemo(() => {
    return data || [];
  }, [data]);

  // 过滤可见的点
  const visiblePoints = useMemo(() => {
    return points.filter((point) => {
      // 聚类可见性过滤
      if (clusterVisibility[point.cluster] === false) {
        return false;
      }
      return true;
    });
  }, [points, clusterVisibility]);

  // 搜索高亮点
  const highlightedIds = useMemo(() => {
    if (!searchQuery) return highlightedPoints;
    return points
      .filter((p) =>
        p.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
      .map((p) => p.id);
  }, [points, searchQuery, highlightedPoints]);

  // 绘制场景
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // 清空画布
    ctx.clearRect(0, 0, width, height);

    // 绘制背景
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, width, height);

    // 计算所有点的投影
    const projectedPoints = visiblePoints.map((point) => ({
      ...point,
      projected: project3DTo2D(point, camera, width, height),
    }));

    // 按深度排序（远到近）
    projectedPoints.sort((a, b) => b.projected.depth - a.projected.depth);

    // 绘制网格
    if (showGrid) {
      drawGrid(ctx, camera, width, height);
    }

    // 绘制坐标轴
    if (showAxes) {
      drawAxes(ctx, camera, width, height);
    }

    // 绘制点
    projectedPoints.forEach((point) => {
      const { x, y, scale } = point.projected;

      // 检查是否在视野内
      if (x < -50 || x > width + 50 || y < -50 || y > height + 50) return;

      const isHighlighted = highlightedIds.includes(point.id);
      const isHovered = hoveredPoint?.id === point.id;
      const pointSize = point.size * scale * (isHighlighted ? 1.5 : 1);

      // 绘制点
      ctx.beginPath();
      ctx.arc(x, y, Math.max(2, pointSize), 0, Math.PI * 2);
      ctx.fillStyle = point.color;
      ctx.fill();

      // 高亮效果
      if (isHighlighted || isHovered) {
        ctx.beginPath();
        ctx.arc(x, y, Math.max(4, pointSize + 4), 0, Math.PI * 2);
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 发光效果
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, pointSize * 3);
        gradient.addColorStop(0, point.color + '40');
        gradient.addColorStop(1, 'transparent');
        ctx.beginPath();
        ctx.arc(x, y, pointSize * 3, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();
      }

      // 绘制标签（仅高亮或悬停时）
      if (isHighlighted || isHovered) {
        ctx.fillStyle = '#fff';
        ctx.font = '12px sans-serif';
        ctx.fillText(point.label, x + pointSize + 5, y + 4);
      }
    });
  }, [visiblePoints, camera, highlightedIds, hoveredPoint, showGrid, showAxes]);

  // 绘制网格
  const drawGrid = (ctx, camera, width, height) => {
    const gridSize = 100;
    const gridCount = 5;
    ctx.strokeStyle = '#1a1a1a';
    ctx.lineWidth = 1;

    for (let i = -gridCount; i <= gridCount; i++) {
      // XZ平面网格线
      const start1 = project3DTo2D({ x: i * gridSize, y: 0, z: -gridCount * gridSize }, camera, width, height);
      const end1 = project3DTo2D({ x: i * gridSize, y: 0, z: gridCount * gridSize }, camera, width, height);
      ctx.beginPath();
      ctx.moveTo(start1.x, start1.y);
      ctx.lineTo(end1.x, end1.y);
      ctx.stroke();

      const start2 = project3DTo2D({ x: -gridCount * gridSize, y: 0, z: i * gridSize }, camera, width, height);
      const end2 = project3DTo2D({ x: gridCount * gridSize, y: 0, z: i * gridSize }, camera, width, height);
      ctx.beginPath();
      ctx.moveTo(start2.x, start2.y);
      ctx.lineTo(end2.x, end2.y);
      ctx.stroke();
    }
  };

  // 绘制坐标轴
  const drawAxes = (ctx, camera, width, height) => {
    const axisLength = 200;
    const origin = project3DTo2D({ x: 0, y: 0, z: 0 }, camera, width, height);

    // X轴 (红色)
    const xEnd = project3DTo2D({ x: axisLength, y: 0, z: 0 }, camera, width, height);
    ctx.strokeStyle = '#ff4d4f';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(xEnd.x, xEnd.y);
    ctx.stroke();

    // Y轴 (绿色)
    const yEnd = project3DTo2D({ x: 0, y: axisLength, z: 0 }, camera, width, height);
    ctx.strokeStyle = '#52c41a';
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(yEnd.x, yEnd.y);
    ctx.stroke();

    // Z轴 (蓝色)
    const zEnd = project3DTo2D({ x: 0, y: 0, z: axisLength }, camera, width, height);
    ctx.strokeStyle = '#1890ff';
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(zEnd.x, zEnd.y);
    ctx.stroke();

    // 轴标签
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 14px sans-serif';
    ctx.fillText('X', xEnd.x + 5, xEnd.y);
    ctx.fillText('Y', yEnd.x + 5, yEnd.y);
    ctx.fillText('Z', zEnd.x + 5, zEnd.y);
  };

  // 动画循环
  useEffect(() => {
    const animate = () => {
      draw();

      if (isAutoRotating) {
        setCamera((prev) => ({
          ...prev,
          rotY: prev.rotY + 0.005,
        }));
      }

      animationIdRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
    };
  }, [draw, isAutoRotating]);

  // 鼠标事件处理
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      const deltaX = e.clientX - lastMousePos.x;
      const deltaY = e.clientY - lastMousePos.y;

      setCamera((prev) => ({
        ...prev,
        rotY: prev.rotY + deltaX * 0.01,
        rotX: Math.max(-Math.PI / 2, Math.min(Math.PI / 2, prev.rotX - deltaY * 0.01)),
      }));

      setLastMousePos({ x: e.clientX, y: e.clientY });
    } else {
      // 检测悬停
      const canvas = canvasRef.current;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      let found = null;
      for (const point of visiblePoints) {
        const projected = project3DTo2D(point, camera, canvas.width, canvas.height);
        const distance = Math.sqrt(
          Math.pow(mouseX - projected.x, 2) + Math.pow(mouseY - projected.y, 2)
        );
        if (distance < 10) {
          found = point;
          break;
        }
      }

      setHoveredPoint(found);
      onPointHover?.(found);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setCamera((prev) => ({
      ...prev,
      zoom: Math.max(0.1, Math.min(5, prev.zoom * delta)),
    }));
  };

  const handleClick = (e) => {
    if (hoveredPoint) {
      onPointClick?.(hoveredPoint);
    }
  };

  // 控制函数
  const handleZoomIn = () => {
    setCamera((prev) => ({ ...prev, zoom: Math.min(5, prev.zoom * 1.2) }));
  };

  const handleZoomOut = () => {
    setCamera((prev) => ({ ...prev, zoom: Math.max(0.1, prev.zoom / 1.2) }));
  };

  const handleReset = () => {
    setCamera(DEFAULT_CAMERA);
  };

  const handleToggleAutoRotate = () => {
    setIsAutoRotating((prev) => !prev);
  };

  const handleExport = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = `vector-space-${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  return (
    <div className="vector-space-3d" ref={containerRef}>
      {/* 工具栏 */}
      <div className="toolbar">
        <button onClick={handleZoomIn} title="放大">
          <ZoomIn size={18} />
        </button>
        <button onClick={handleZoomOut} title="缩小">
          <ZoomOut size={18} />
        </button>
        <button onClick={handleReset} title="重置视角">
          <RefreshCw size={18} />
        </button>
        <button
          onClick={handleToggleAutoRotate}
          className={isAutoRotating ? 'active' : ''}
          title="自动旋转"
        >
          <RotateCw size={18} className={isAutoRotating ? 'spinning' : ''} />
        </button>
        <button onClick={handleExport} title="导出图片">
          <Download size={18} />
        </button>
      </div>

      {/* 信息面板 */}
      {hoveredPoint && (
        <div className="info-panel">
          <h4>{hoveredPoint.label}</h4>
          <p>聚类: {hoveredPoint.cluster}</p>
          <p>坐标: ({hoveredPoint.x.toFixed(1)}, {hoveredPoint.y.toFixed(1)}, {hoveredPoint.z.toFixed(1)})</p>
          {hoveredPoint.metadata && (
            <>
              <p>文档: {hoveredPoint.metadata.documentId}</p>
              <p>分数: {hoveredPoint.metadata.score.toFixed(3)}</p>
            </>
          )}
        </div>
      )}

      {/* 统计信息 */}
      <div className="stats-panel">
        <div>点数: {visiblePoints.length}</div>
        <div>聚类: {new Set(visiblePoints.map((p) => p.cluster)).size}</div>
        <div>缩放: {(camera.zoom * 100).toFixed(0)}%</div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        onClick={handleClick}
        style={{ cursor: isDragging ? 'grabbing' : hoveredPoint ? 'pointer' : 'grab' }}
      />
    </div>
  );
};

/**
 * 带控制面板的3D向量空间可视化
 */
export const VectorSpace3DWithControls = ({
  data,
  width = 800,
  height = 600,
  onPointClick,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showGrid, setShowGrid] = useState(true);
  const [showAxes, setShowAxes] = useState(true);
  const [clusterVisibility, setClusterVisibility] = useState({});

  // 使用传入的真实数据，如果没有则返回空数组
  const points = useMemo(() => {
    return data || [];
  }, [data]);

  // 获取所有聚类
  const clusters = useMemo(() => {
    const clusterSet = new Set(points.map((p) => p.cluster));
    return Array.from(clusterSet).sort((a, b) => a - b);
  }, [points]);

  // 切换聚类可见性
  const toggleCluster = (clusterId) => {
    setClusterVisibility((prev) => ({
      ...prev,
      [clusterId]: prev[clusterId] === false ? true : false,
    }));
  };

  return (
    <div className="vector-space-3d-container">
      {/* 控制面板 */}
      <div className="control-panel">
        <div className="control-section">
          <h4>搜索</h4>
          <div className="search-input">
            <Search size={16} />
            <input
              type="text"
              placeholder="搜索向量..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="control-section">
          <h4>显示选项</h4>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showGrid}
              onChange={(e) => setShowGrid(e.target.checked)}
            />
            <Grid3X3 size={16} />
            <span>显示网格</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showAxes}
              onChange={(e) => setShowAxes(e.target.checked)}
            />
            <Move size={16} />
            <span>显示坐标轴</span>
          </label>
        </div>

        <div className="control-section">
          <h4>聚类过滤</h4>
          {clusters.map((clusterId) => (
            <label key={clusterId} className="checkbox-label">
              <input
                type="checkbox"
                checked={clusterVisibility[clusterId] !== false}
                onChange={() => toggleCluster(clusterId)}
              />
              <span
                className="color-dot"
                style={{ backgroundColor: CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length] }}
              />
              <span>聚类 {clusterId}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 3D可视化 */}
      <VectorSpace3D
        data={points}
        width={width}
        height={height}
        onPointClick={onPointClick}
        searchQuery={searchQuery}
        showGrid={showGrid}
        showAxes={showAxes}
        clusterVisibility={clusterVisibility}
      />
    </div>
  );
};

export default VectorSpace3D;
export { generateMockData, CLUSTER_COLORS };
