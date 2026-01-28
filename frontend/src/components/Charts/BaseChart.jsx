import React, { useRef, useEffect, useState } from 'react';
import './BaseChart.css';

/**
 * 基础图表组件
 * 提供通用的图表功能和配置
 */
const BaseChart = ({
  data = [],
  width = 400,
  height = 300,
  title,
  description,
  margin = { top: 20, right: 20, bottom: 40, left: 40 },
  colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'],
  animation = true,
  interactive = true,
  responsive = true,
  className = '',
  children,
  ...props
}) => {
  const chartRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width, height });
  const [isHovered, setIsHovered] = useState(false);

  // 响应式尺寸调整
  useEffect(() => {
    if (!responsive || !chartRef.current) return;

    const updateDimensions = () => {
      const container = chartRef.current.parentElement;
      if (container) {
        const containerWidth = container.clientWidth;
        const newWidth = Math.min(containerWidth, width);
        setDimensions({ width: newWidth, height: (newWidth / width) * height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    
    return () => window.removeEventListener('resize', updateDimensions);
  }, [width, height, responsive]);

  // 计算图表区域尺寸
  const chartArea = {
    width: dimensions.width - margin.left - margin.right,
    height: dimensions.height - margin.top - margin.bottom
  };

  // 图表样式
  const chartStyle = {
    width: dimensions.width,
    height: dimensions.height
  };

  const handleMouseEnter = () => {
    if (interactive) {
      setIsHovered(true);
    }
  };

  const handleMouseLeave = () => {
    if (interactive) {
      setIsHovered(false);
    }
  };

  return (
    <div 
      ref={chartRef}
      className={`base-chart ${className} ${isHovered ? 'base-chart--hovered' : ''}`}
      style={chartStyle}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      {...props}
    >
      {/* 图表标题和描述 */}
      {(title || description) && (
        <div className="base-chart__header">
          {title && <h3 className="base-chart__title">{title}</h3>}
          {description && <p className="base-chart__description">{description}</p>}
        </div>
      )}

      {/* 图表容器 */}
      <div className="base-chart__container">
        <svg 
          width={dimensions.width} 
          height={dimensions.height}
          className="base-chart__svg"
        >
          {/* 图表区域 */}
          <g 
            className="base-chart__area"
            transform={`translate(${margin.left}, ${margin.top})`}
          >
            {children}
          </g>
        </svg>
      </div>

      {/* 图表图例 */}
      {data.length > 0 && (
        <div className="base-chart__legend">
          {data.map((item, index) => (
            <div key={item.id || index} className="base-chart__legend-item">
              <span 
                className="base-chart__legend-color"
                style={{ backgroundColor: item.color || colors[index % colors.length] }}
              />
              <span className="base-chart__legend-label">{item.label || item.name}</span>
              {item.value !== undefined && (
                <span className="base-chart__legend-value">{item.value}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 图表工具栏 */}
      {interactive && (
        <div className="base-chart__toolbar">
          <button className="base-chart__toolbar-button" title="放大">🔍</button>
          <button className="base-chart__toolbar-button" title="下载">📥</button>
          <button className="base-chart__toolbar-button" title="刷新">🔄</button>
        </div>
      )}
    </div>
  );
};

/**
 * 柱状图组件
 */
const BarChart = ({
  data,
  xKey = 'label',
  yKey = 'value',
  horizontal = false,
  stacked = false,
  ...props
}) => {
  if (!data || data.length === 0) {
    return <div className="chart-empty">暂无数据</div>;
  }

  // 计算数据范围
  const values = data.map(item => item[yKey]);
  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  
  // 计算柱状图尺寸
  const barWidth = horizontal ? 
    props.chartArea.height / data.length * 0.6 : 
    props.chartArea.width / data.length * 0.6;
  
  const scale = horizontal ? 
    value => (value - minValue) / (maxValue - minValue) * props.chartArea.width :
    value => (value - minValue) / (maxValue - minValue) * props.chartArea.height;

  return (
    <BaseChart data={data} {...props}>
      {/* 坐标轴 */}
      {!horizontal && (
        <g className="base-chart__axis base-chart__axis--x">
          <line 
            x1={0} y1={props.chartArea.height}
            x2={props.chartArea.width} y2={props.chartArea.height}
            stroke="#ccc"
            strokeWidth={1}
          />
        </g>
      )}
      
      {horizontal && (
        <g className="base-chart__axis base-chart__axis--y">
          <line 
            x1={0} y1={0}
            x2={0} y2={props.chartArea.height}
            stroke="#ccc"
            strokeWidth={1}
          />
        </g>
      )}

      {/* 柱状图 */}
      {data.map((item, index) => {
        const x = horizontal ? 0 : index * (props.chartArea.width / data.length) + barWidth * 0.2;
        const y = horizontal ? index * (props.chartArea.height / data.length) + barWidth * 0.2 : props.chartArea.height - scale(item[yKey]);
        const width = horizontal ? scale(item[yKey]) : barWidth;
        const height = horizontal ? barWidth : scale(item[yKey]);
        
        return (
          <rect
            key={item.id || index}
            className="base-chart__bar"
            x={x}
            y={y}
            width={width}
            height={height}
            fill={item.color || props.colors[index % props.colors.length]}
            rx={4}
            ry={4}
          />
        );
      })}

      {/* 数据标签 */}
      {data.map((item, index) => {
        const x = horizontal ? 
          scale(item[yKey]) + 5 : 
          index * (props.chartArea.width / data.length) + barWidth * 0.2 + barWidth / 2;
        const y = horizontal ? 
          index * (props.chartArea.height / data.length) + barWidth * 0.2 + barWidth / 2 : 
          props.chartArea.height - scale(item[yKey]) - 5;
        
        return (
          <text
            key={`label-${index}`}
            x={x}
            y={y}
            textAnchor={horizontal ? 'start' : 'middle'}
            dominantBaseline={horizontal ? 'middle' : 'auto'}
            className="base-chart__label"
            fontSize={12}
            fill="#666"
          >
            {item[yKey]}
          </text>
        );
      })}
    </BaseChart>
  );
};

/**
 * 折线图组件
 */
const LineChart = ({
  data,
  xKey = 'label',
  yKey = 'value',
  showPoints = true,
  smooth = false,
  area = false,
  ...props
}) => {
  if (!data || data.length === 0) {
    return <div className="chart-empty">暂无数据</div>;
  }

  // 计算数据范围
  const values = data.map(item => item[yKey]);
  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  
  // 计算点位置
  const points = data.map((item, index) => ({
    x: (index / (data.length - 1)) * props.chartArea.width,
    y: props.chartArea.height - ((item[yKey] - minValue) / (maxValue - minValue)) * props.chartArea.height
  }));

  // 生成折线路径
  const linePath = points.map((point, index) => 
    `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
  ).join(' ');

  // 生成区域路径
  const areaPath = points.length > 0 ? 
    `${linePath} L ${points[points.length - 1].x} ${props.chartArea.height} L ${points[0].x} ${props.chartArea.height} Z` : 
    '';

  return (
    <BaseChart data={data} {...props}>
      {/* 坐标轴 */}
      <g className="base-chart__axis base-chart__axis--x">
        <line 
          x1={0} y1={props.chartArea.height}
          x2={props.chartArea.width} y2={props.chartArea.height}
          stroke="#ccc"
          strokeWidth={1}
        />
      </g>
      
      <g className="base-chart__axis base-chart__axis--y">
        <line 
          x1={0} y1={0}
          x2={0} y2={props.chartArea.height}
          stroke="#ccc"
          strokeWidth={1}
        />
      </g>

      {/* 区域填充 */}
      {area && (
        <path
          d={areaPath}
          fill="rgba(52, 152, 219, 0.2)"
          className="base-chart__area-fill"
        />
      )}

      {/* 折线 */}
      <path
        d={linePath}
        fill="none"
        stroke="#3498db"
        strokeWidth={2}
        className="base-chart__line"
      />

      {/* 数据点 */}
      {showPoints && points.map((point, index) => (
        <circle
          key={index}
          cx={point.x}
          cy={point.y}
          r={4}
          fill="#3498db"
          className="base-chart__point"
        />
      ))}

      {/* 数据标签 */}
      {points.map((point, index) => (
        <text
          key={`label-${index}`}
          x={point.x}
          y={point.y - 10}
          textAnchor="middle"
          className="base-chart__label"
          fontSize={10}
          fill="#666"
        >
          {data[index][yKey]}
        </text>
      ))}
    </BaseChart>
  );
};

// 导出所有组件
BaseChart.Bar = BarChart;
BaseChart.Line = LineChart;

export default BaseChart;