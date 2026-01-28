import React, { useRef, useState, useCallback } from 'react';
import { useDrag } from '@use-gesture/react';
import './CanvasElement.css';

/**
 * 画布元素组件
 * 支持拖拽、选择、缩放等交互功能
 */
const CanvasElement = ({
  id,
  x = 0,
  y = 0,
  width = 100,
  height = 60,
  type = 'default',
  title,
  content,
  selected = false,
  resizable = false,
  rotatable = false,
  onSelect,
  onMove,
  onResize,
  onRotate,
  onDoubleClick,
  className = '',
  children,
  ...props
}) => {
  const elementRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [rotation, setRotation] = useState(0);

  // 处理元素选择
  const handleSelect = useCallback((event) => {
    event.stopPropagation();
    if (onSelect) {
      onSelect(id, event);
    }
  }, [id, onSelect]);

  // 处理元素移动
  const handleMove = useCallback((delta) => {
    if (onMove) {
      onMove(id, delta);
    }
  }, [id, onMove]);

  // 处理元素双击
  const handleDoubleClick = useCallback((event) => {
    event.stopPropagation();
    if (onDoubleClick) {
      onDoubleClick(id, event);
    }
  }, [id, onDoubleClick]);

  // 使用拖拽手势
  const bindDrag = useDrag(({ delta, event, first, last }) => {
    event?.stopPropagation();
    
    if (first) {
      setIsDragging(true);
    }
    
    if (last) {
      setIsDragging(false);
    }
    
    handleMove(delta);
  }, {
    filterTaps: true,
    bounds: { left: 0, top: 0, right: 2000, bottom: 2000 } // 画布边界
  });

  // 元素样式
  const elementStyle = {
    left: `${x}px`,
    top: `${y}px`,
    width: `${width}px`,
    height: `${height}px`,
    transform: `rotate(${rotation}deg)`
  };

  // 元素类名
  const elementClasses = [
    'canvas-element',
    `canvas-element--${type}`,
    selected && 'selected',
    isDragging && 'dragging',
    isResizing && 'resizing',
    className
  ].filter(Boolean).join(' ');

  return (
    <div
      ref={elementRef}
      className={elementClasses}
      style={elementStyle}
      onClick={handleSelect}
      onDoubleClick={handleDoubleClick}
      {...bindDrag()}
      {...props}
    >
      {/* 元素内容 */}
      <div className="canvas-element__content">
        {children || (
          <>
            {title && (
              <div className="canvas-element__title">
                {title}
              </div>
            )}
            {content && (
              <div className="canvas-element__body">
                {content}
              </div>
            )}
          </>
        )}
      </div>

      {/* 选择边框 */}
      {selected && (
        <div className="canvas-element__selection-border">
          {/* 调整手柄 */}
          {resizable && (
            <>
              <div className="canvas-element__resize-handle canvas-element__resize-handle--nw" />
              <div className="canvas-element__resize-handle canvas-element__resize-handle--ne" />
              <div className="canvas-element__resize-handle canvas-element__resize-handle--sw" />
              <div className="canvas-element__resize-handle canvas-element__resize-handle--se" />
              <div className="canvas-element__resize-handle canvas-element__resize-handle--n" />
              <div className="canvas-element__resize-handle canvas-element__resize-handle--s" />
              <div className="canvas-element__resize-handle canvas-element__resize-handle--w" />
              <div className="canvas-element__resize-handle canvas-element__resize-handle--e" />
            </>
          )}

          {/* 旋转手柄 */}
          {rotatable && (
            <div className="canvas-element__rotate-handle" />
          )}
        </div>
      )}
    </div>
  );
};

/**
 * 节点元素组件（用于工作流节点）
 */
const NodeElement = ({
  id,
  x,
  y,
  type = 'task',
  title,
  description,
  status = 'idle',
  inputs = [],
  outputs = [],
  ...props
}) => {
  const getNodeIcon = () => {
    switch (type) {
      case 'start':
        return '▶️';
      case 'end':
        return '⏹️';
      case 'decision':
        return '❓';
      case 'task':
        return '⚙️';
      case 'data':
        return '📊';
      case 'api':
        return '🌐';
      default:
        return '📄';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'var(--ui-color-warning-500)';
      case 'success':
        return 'var(--ui-color-success-500)';
      case 'error':
        return 'var(--ui-color-danger-500)';
      default:
        return 'var(--ui-color-gray-400)';
    }
  };

  return (
    <CanvasElement
      id={id}
      x={x}
      y={y}
      width={120}
      height={80}
      type="node"
      title={title}
      {...props}
    >
      <div className="node-element">
        <div className="node-element__header">
          <span className="node-element__icon">{getNodeIcon()}</span>
          <span className="node-element__title">{title}</span>
        </div>
        
        {description && (
          <div className="node-element__description">
            {description}
          </div>
        )}
        
        <div 
          className="node-element__status"
          style={{ backgroundColor: getStatusColor() }}
        />

        {/* 输入端口 */}
        {inputs.map((input, index) => (
          <div
            key={`input-${index}`}
            className="node-element__port node-element__port--input"
            style={{ top: `${(index + 1) * 20}px` }}
          />
        ))}

        {/* 输出端口 */}
        {outputs.map((output, index) => (
          <div
            key={`output-${index}`}
            className="node-element__port node-element__port--output"
            style={{ top: `${(index + 1) * 20}px` }}
          />
        ))}
      </div>
    </CanvasElement>
  );
};

/**
 * 文本元素组件
 */
const TextElement = ({
  id,
  x,
  y,
  text,
  fontSize = 14,
  fontWeight = 'normal',
  color = 'var(--ui-color-gray-900)',
  ...props
}) => {
  return (
    <CanvasElement
      id={id}
      x={x}
      y={y}
      width={200}
      height={40}
      type="text"
      resizable={true}
      {...props}
    >
      <div 
        className="text-element"
        style={{
          fontSize: `${fontSize}px`,
          fontWeight,
          color
        }}
      >
        {text}
      </div>
    </CanvasElement>
  );
};

/**
 * 连接线组件
 */
const ConnectionElement = ({
  id,
  from,
  to,
  type = 'straight',
  selected = false,
  onSelect,
  ...props
}) => {
  // 计算连接线路径
  const calculatePath = () => {
    if (!from || !to) return '';
    
    const fromX = from.x + (from.width || 0) / 2;
    const fromY = from.y + (from.height || 0) / 2;
    const toX = to.x + (to.width || 0) / 2;
    const toY = to.y + (to.height || 0) / 2;
    
    if (type === 'bezier') {
      // 贝塞尔曲线
      const controlX1 = fromX + (toX - fromX) * 0.5;
      const controlY1 = fromY;
      const controlX2 = fromX + (toX - fromX) * 0.5;
      const controlY2 = toY;
      
      return `M ${fromX} ${fromY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${toX} ${toY}`;
    } else {
      // 直线
      return `M ${fromX} ${fromY} L ${toX} ${toY}`;
    }
  };

  const handleClick = (event) => {
    event.stopPropagation();
    if (onSelect) {
      onSelect(id, event);
    }
  };

  return (
    <svg 
      className={`canvas-connection ${selected ? 'selected' : ''}`}
      onClick={handleClick}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none'
      }}
      {...props}
    >
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3.5, 0 7"
            className={`arrow-marker ${selected ? 'selected' : ''}`}
          />
        </marker>
      </defs>
      
      <path
        d={calculatePath()}
        fill="none"
        strokeWidth={selected ? 3 : 2}
        stroke={selected ? 'var(--ui-color-primary-500)' : 'var(--ui-color-gray-400)'}
        markerEnd="url(#arrowhead)"
        pointerEvents="stroke"
        style={{ cursor: 'pointer' }}
      />
    </svg>
  );
};

// 导出所有组件
CanvasElement.Node = NodeElement;
CanvasElement.Text = TextElement;
CanvasElement.Connection = ConnectionElement;

export default CanvasElement;