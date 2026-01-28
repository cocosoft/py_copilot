import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useGesture } from '@use-gesture/react';
import './Canvas.css';

/**
 * 画布基础组件
 * 支持拖拽、缩放、导航等基础功能
 */
const Canvas = ({
  children,
  width = 2000,
  height = 2000,
  scale = 1,
  minScale = 0.1,
  maxScale = 3,
  panEnabled = true,
  zoomEnabled = true,
  gridEnabled = true,
  gridSize = 20,
  backgroundColor = '#f8f9fa',
  onScaleChange,
  onPositionChange,
  className = '',
  ...props
}) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  
  const [canvasState, setCanvasState] = useState({
    scale: scale,
    position: { x: 0, y: 0 },
    isDragging: false,
    isPanning: false
  });

  // 更新画布状态
  const updateCanvasState = useCallback((updates) => {
    setCanvasState(prev => {
      const newState = { ...prev, ...updates };
      
      // 限制缩放范围
      if (newState.scale !== undefined) {
        newState.scale = Math.max(minScale, Math.min(maxScale, newState.scale));
      }
      
      return newState;
    });
  }, [minScale, maxScale]);

  // 处理缩放
  const handleZoom = useCallback((delta, center) => {
    if (!zoomEnabled) return;
    
    const zoomFactor = delta > 0 ? 1.1 : 0.9;
    const newScale = canvasState.scale * zoomFactor;
    
    // 计算缩放中心相对于画布的位置
    const containerRect = containerRef.current?.getBoundingClientRect();
    if (!containerRect) return;
    
    const centerX = (center.x - containerRect.left) / canvasState.scale - canvasState.position.x;
    const centerY = (center.y - containerRect.top) / canvasState.scale - canvasState.position.y;
    
    // 计算新的位置以保持缩放中心不变
    const newPosition = {
      x: canvasState.position.x - (centerX * (newScale - canvasState.scale)) / newScale,
      y: canvasState.position.y - (centerY * (newScale - canvasState.scale)) / newScale
    };
    
    updateCanvasState({
      scale: newScale,
      position: newPosition
    });
    
    if (onScaleChange) onScaleChange(newScale);
    if (onPositionChange) onPositionChange(newPosition);
  }, [canvasState, zoomEnabled, updateCanvasChange]);

  // 处理拖拽
  const handleDrag = useCallback((delta) => {
    if (!panEnabled || !canvasState.isPanning) return;
    
    const newPosition = {
      x: canvasState.position.x + delta[0] / canvasState.scale,
      y: canvasState.position.y + delta[1] / canvasState.scale
    };
    
    updateCanvasState({ position: newPosition });
    if (onPositionChange) onPositionChange(newPosition);
  }, [canvasState, panEnabled, updateCanvasState, onPositionChange]);

  // 使用手势库处理交互
  const bind = useGesture({
    onDrag: ({ delta, event }) => {
      event.preventDefault();
      handleDrag(delta);
    },
    
    onDragStart: () => {
      updateCanvasState({ isPanning: true });
    },
    
    onDragEnd: () => {
      updateCanvasState({ isPanning: false });
    },
    
    onWheel: ({ delta: [_, deltaY], event }) => {
      event.preventDefault();
      handleZoom(deltaY, { x: event.clientX, y: event.clientY });
    },
    
    onPinch: ({ delta: [d], origin, event }) => {
      event.preventDefault();
      handleZoom(d > 0 ? 1 : -1, { x: origin[0], y: origin[1] });
    }
  }, {
    drag: {
      filterTaps: true,
      bounds: containerRef
    },
    wheel: {
      eventOptions: { passive: false }
    },
    pinch: {
      eventOptions: { passive: false }
    }
  });

  // 重置画布视图
  const resetView = useCallback(() => {
    updateCanvasState({
      scale: scale,
      position: { x: 0, y: 0 }
    });
    
    if (onScaleChange) onScaleChange(scale);
    if (onPositionChange) onPositionChange({ x: 0, y: 0 });
  }, [scale, updateCanvasState, onScaleChange, onPositionChange]);

  // 缩放到适合视图
  const fitToView = useCallback(() => {
    if (!containerRef.current) return;
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const containerWidth = containerRect.width;
    const containerHeight = containerRect.height;
    
    const scaleX = containerWidth / width;
    const scaleY = containerHeight / height;
    const newScale = Math.min(scaleX, scaleY, maxScale) * 0.9; // 留出边距
    
    const newPosition = {
      x: (containerWidth - width * newScale) / (2 * newScale),
      y: (containerHeight - height * newScale) / (2 * newScale)
    };
    
    updateCanvasState({
      scale: newScale,
      position: newPosition
    });
    
    if (onScaleChange) onScaleChange(newScale);
    if (onPositionChange) onPositionChange(newPosition);
  }, [width, height, maxScale, updateCanvasState, onScaleChange, onPositionChange]);

  // 画布变换样式
  const canvasStyle = {
    width: `${width}px`,
    height: `${height}px`,
    backgroundColor,
    transform: `scale(${canvasState.scale}) translate(${canvasState.position.x}px, ${canvasState.position.y}px)`,
    transformOrigin: '0 0'
  };

  // 网格背景
  const gridStyle = {
    backgroundSize: `${gridSize}px ${gridSize}px`,
    backgroundImage: `
      linear-gradient(to right, rgba(0, 0, 0, 0.1) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0, 0, 0, 0.1) 1px, transparent 1px)
    `
  };

  return (
    <div 
      className={`ui-canvas-container ${className}`}
      ref={containerRef}
      {...bind()}
      {...props}
    >
      {/* 画布导航控件 */}
      <div className="ui-canvas-controls">
        <button
          className="ui-canvas-control"
          onClick={() => handleZoom(1, { x: 0, y: 0 })}
          title="放大"
        >
          +
        </button>
        <button
          className="ui-canvas-control"
          onClick={() => handleZoom(-1, { x: 0, y: 0 })}
          title="缩小"
        >
          -
        </button>
        <button
          className="ui-canvas-control"
          onClick={resetView}
          title="重置视图"
        >
          ↺
        </button>
        <button
          className="ui-canvas-control"
          onClick={fitToView}
          title="适应视图"
        >
          ⤢
        </button>
        <span className="ui-canvas-scale">
          {Math.round(canvasState.scale * 100)}%
        </span>
      </div>

      {/* 画布内容 */}
      <div 
        ref={canvasRef}
        className="ui-canvas"
        style={{
          ...canvasStyle,
          ...(gridEnabled ? gridStyle : {})
        }}
      >
        {children}
      </div>

      {/* 画布状态指示器 */}
      <div className="ui-canvas-status">
        <span>位置: {Math.round(canvasState.position.x)}, {Math.round(canvasState.position.y)}</span>
        <span>缩放: {Math.round(canvasState.scale * 100)}%</span>
      </div>
    </div>
  );
};

export default Canvas;