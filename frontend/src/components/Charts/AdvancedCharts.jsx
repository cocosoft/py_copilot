import React from 'react';
import BaseChart from './BaseChart';
import './AdvancedCharts.css';

/**
 * 饼图组件
 */
const PieChart = ({
  data,
  innerRadius = 0, // 内半径，用于创建环形图
  showLabels = true,
  showPercentages = true,
  ...props
}) => {
  if (!data || data.length === 0) {
    return <div className="chart-empty">暂无数据</div>;
  }

  // 计算总和
  const total = data.reduce((sum, item) => sum + (item.value || 0), 0);
  
  // 计算每个扇区的角度
  let currentAngle = 0;
  const sectors = data.map((item, index) => {
    const angle = (item.value / total) * 360;
    const sector = {
      ...item,
      angle,
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
      percentage: (item.value / total) * 100
    };
    currentAngle += angle;
    return sector;
  });

  // 计算饼图半径
  const radius = Math.min(props.chartArea.width, props.chartArea.height) / 2 - 10;
  const centerX = props.chartArea.width / 2;
  const centerY = props.chartArea.height / 2;

  // 生成扇形路径
  const generateSectorPath = (sector) => {
    const startRad = (sector.startAngle - 90) * Math.PI / 180;
    const endRad = (sector.endAngle - 90) * Math.PI / 180;
    
    const x1 = centerX + Math.cos(startRad) * radius;
    const y1 = centerY + Math.sin(startRad) * radius;
    const x2 = centerX + Math.cos(endRad) * radius;
    const y2 = centerY + Math.sin(endRad) * radius;
    
    const innerX1 = centerX + Math.cos(startRad) * innerRadius;
    const innerY1 = centerY + Math.sin(startRad) * innerRadius;
    const innerX2 = centerX + Math.cos(endRad) * innerRadius;
    const innerY2 = centerY + Math.sin(endRad) * innerRadius;
    
    const largeArc = sector.angle > 180 ? 1 : 0;
    
    if (innerRadius > 0) {
      // 环形图路径
      return `
        M ${innerX1} ${innerY1}
        L ${x1} ${y1}
        A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
        L ${innerX2} ${innerY2}
        A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${innerX1} ${innerY1}
        Z
      `;
    } else {
      // 饼图路径
      return `
        M ${centerX} ${centerY}
        L ${x1} ${y1}
        A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
        Z
      `;
    }
  };

  return (
    <BaseChart data={data} {...props}>
      {/* 扇形 */}
      {sectors.map((sector, index) => (
        <g key={sector.id || index} className="pie-chart__sector-group">
          <path
            d={generateSectorPath(sector)}
            fill={sector.color || props.colors[index % props.colors.length]}
            className="pie-chart__sector"
            data-value={sector.value}
            data-percentage={sector.percentage}
          />
          
          {/* 标签 */}
          {showLabels && (
            <text
              x={centerX + Math.cos((sector.startAngle + sector.angle / 2 - 90) * Math.PI / 180) * (radius * 0.7)}
              y={centerY + Math.sin((sector.startAngle + sector.angle / 2 - 90) * Math.PI / 180) * (radius * 0.7)}
              textAnchor="middle"
              dominantBaseline="middle"
              className="pie-chart__label"
              fontSize={10}
              fill="#fff"
              fontWeight="bold"
            >
              {showPercentages ? `${sector.percentage.toFixed(1)}%` : sector.label}
            </text>
          )}
        </g>
      ))}
      
      {/* 中心文本（环形图） */}
      {innerRadius > 0 && (
        <text
          x={centerX}
          y={centerY}
          textAnchor="middle"
          dominantBaseline="middle"
          className="pie-chart__center-text"
          fontSize={12}
          fill="#666"
          fontWeight="bold"
        >
          总计\n{total}
        </text>
      )}
    </BaseChart>
  );
};

/**
 * 散点图组件
 */
const ScatterChart = ({
  data,
  xKey = 'x',
  yKey = 'y',
  sizeKey = 'size',
  colorKey = 'color',
  showRegressionLine = false,
  ...props
}) => {
  if (!data || data.length === 0) {
    return <div className="chart-empty">暂无数据</div>;
  }

  // 计算数据范围
  const xValues = data.map(item => item[xKey]);
  const yValues = data.map(item => item[yKey]);
  const sizes = data.map(item => item[sizeKey] || 1);
  
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  const minY = Math.min(...yValues);
  const maxY = Math.max(...yValues);
  const minSize = Math.min(...sizes);
  const maxSize = Math.max(...sizes);
  
  // 计算缩放比例
  const scaleX = value => ((value - minX) / (maxX - minX)) * props.chartArea.width;
  const scaleY = value => props.chartArea.height - ((value - minY) / (maxY - minY)) * props.chartArea.height;
  const scaleSize = value => ((value - minSize) / (maxSize - minSize)) * 20 + 5; // 5-25像素

  // 计算回归线（简单线性回归）
  const calculateRegressionLine = () => {
    const n = data.length;
    const sumX = xValues.reduce((sum, x) => sum + x, 0);
    const sumY = yValues.reduce((sum, y) => sum + y, 0);
    const sumXY = data.reduce((sum, item) => sum + item[xKey] * item[yKey], 0);
    const sumXX = xValues.reduce((sum, x) => sum + x * x, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    return {
      slope,
      intercept,
      x1: minX,
      y1: slope * minX + intercept,
      x2: maxX,
      y2: slope * maxX + intercept
    };
  };

  const regressionLine = showRegressionLine ? calculateRegressionLine() : null;

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

      {/* 回归线 */}
      {regressionLine && (
        <line
          x1={scaleX(regressionLine.x1)}
          y1={scaleY(regressionLine.y1)}
          x2={scaleX(regressionLine.x2)}
          y2={scaleY(regressionLine.y2)}
          stroke="#e74c3c"
          strokeWidth={2}
          strokeDasharray="5,5"
          className="scatter-chart__regression-line"
        />
      )}

      {/* 散点 */}
      {data.map((item, index) => (
        <g key={item.id || index} className="scatter-chart__point-group">
          <circle
            cx={scaleX(item[xKey])}
            cy={scaleY(item[yKey])}
            r={scaleSize(item[sizeKey] || 1)}
            fill={item[colorKey] || props.colors[index % props.colors.length]}
            className="scatter-chart__point"
            data-x={item[xKey]}
            data-y={item[yKey]}
          />
          
          {/* 数据标签 */}
          <text
            x={scaleX(item[xKey])}
            y={scaleY(item[yKey]) - scaleSize(item[sizeKey] || 1) - 5}
            textAnchor="middle"
            className="scatter-chart__label"
            fontSize={8}
            fill="#666"
          >
            {item.label || `(${item[xKey]}, ${item[yKey]})`}
          </text>
        </g>
      ))}
    </BaseChart>
  );
};

/**
 * 面积图组件
 */
const AreaChart = ({
  data,
  xKey = 'label',
  yKey = 'value',
  stacked = false,
  gradient = true,
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

  // 生成面积路径
  const areaPath = points.length > 0 ? 
    `M ${points[0].x} ${props.chartArea.height} ` +
    points.map(point => `L ${point.x} ${point.y}`).join(' ') +
    ` L ${points[points.length - 1].x} ${props.chartArea.height} Z` : 
    '';

  // 生成折线路径
  const linePath = points.map((point, index) => 
    `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
  ).join(' ');

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

      {/* 渐变填充 */}
      {gradient && (
        <defs>
          <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3498db" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#3498db" stopOpacity="0.2" />
          </linearGradient>
        </defs>
      )}

      {/* 面积填充 */}
      <path
        d={areaPath}
        fill={gradient ? 'url(#areaGradient)' : 'rgba(52, 152, 219, 0.3)'}
        className="area-chart__fill"
      />

      {/* 折线 */}
      <path
        d={linePath}
        fill="none"
        stroke="#3498db"
        strokeWidth={2}
        className="area-chart__line"
      />

      {/* 数据点 */}
      {points.map((point, index) => (
        <circle
          key={index}
          cx={point.x}
          cy={point.y}
          r={3}
          fill="#3498db"
          className="area-chart__point"
        />
      ))}

      {/* 数据标签 */}
      {points.map((point, index) => (
        <text
          key={`label-${index}`}
          x={point.x}
          y={point.y - 8}
          textAnchor="middle"
          className="area-chart__label"
          fontSize={9}
          fill="#666"
        >
          {data[index][yKey]}
        </text>
      ))}
    </BaseChart>
  );
};

/**
 * 雷达图组件
 */
const RadarChart = ({
  data,
  dimensions = [], // 维度配置
  maxValue = 100,
  showGrid = true,
  showPoints = true,
  ...props
}) => {
  if (!data || data.length === 0 || dimensions.length === 0) {
    return <div className="chart-empty">暂无数据</div>;
  }

  // 计算雷达图参数
  const centerX = props.chartArea.width / 2;
  const centerY = props.chartArea.height / 2;
  const radius = Math.min(centerX, centerY) - 20;
  const angleStep = (2 * Math.PI) / dimensions.length;

  // 生成网格线
  const gridLevels = 5;
  const gridCircles = [];
  for (let i = 1; i <= gridLevels; i++) {
    const levelRadius = (radius * i) / gridLevels;
    gridCircles.push(levelRadius);
  }

  // 生成维度轴
  const axes = dimensions.map((dim, index) => {
    const angle = index * angleStep;
    const x = centerX + Math.cos(angle) * radius;
    const y = centerY + Math.sin(angle) * radius;
    return { ...dim, angle, x, y };
  });

  // 生成数据点
  const dataPoints = data.map(item => {
    const points = dimensions.map((dim, index) => {
      const value = item[dim.key] || 0;
      const scaledValue = (value / maxValue) * radius;
      const angle = index * angleStep;
      return {
        x: centerX + Math.cos(angle) * scaledValue,
        y: centerY + Math.sin(angle) * scaledValue,
        value
      };
    });
    return { ...item, points };
  });

  // 生成数据路径
  const generateDataPath = (points) => {
    if (points.length < 2) return '';
    
    const path = points.map((point, index) => 
      `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
    ).join(' ');
    
    return `${path} Z`;
  };

  return (
    <BaseChart data={data} {...props}>
      {/* 网格线 */}
      {showGrid && gridCircles.map((circleRadius, index) => (
        <circle
          key={index}
          cx={centerX}
          cy={centerY}
          r={circleRadius}
          fill="none"
          stroke="#f0f0f0"
          strokeWidth={1}
          className="radar-chart__grid-circle"
        />
      ))}

      {/* 维度轴 */}
      {axes.map((axis, index) => (
        <line
          key={index}
          x1={centerX}
          y1={centerY}
          x2={axis.x}
          y2={axis.y}
          stroke="#ccc"
          strokeWidth={1}
          className="radar-chart__axis"
        />
      ))}

      {/* 维度标签 */}
      {axes.map((axis, index) => (
        <text
          key={index}
          x={centerX + Math.cos(axis.angle) * (radius + 15)}
          y={centerY + Math.sin(axis.angle) * (radius + 15)}
          textAnchor="middle"
          dominantBaseline="middle"
          className="radar-chart__dimension-label"
          fontSize={10}
          fill="#666"
        >
          {axis.label}
        </text>
      ))}

      {/* 数据区域 */}
      {dataPoints.map((item, dataIndex) => (
        <g key={item.id || dataIndex} className="radar-chart__data-group">
          <path
            d={generateDataPath(item.points)}
            fill={item.color || props.colors[dataIndex % props.colors.length]}
            fillOpacity={0.3}
            stroke={item.color || props.colors[dataIndex % props.colors.length]}
            strokeWidth={2}
            className="radar-chart__data-area"
          />
          
          {/* 数据点 */}
          {showPoints && item.points.map((point, pointIndex) => (
            <circle
              key={pointIndex}
              cx={point.x}
              cy={point.y}
              r={4}
              fill={item.color || props.colors[dataIndex % props.colors.length]}
              className="radar-chart__data-point"
            />
          ))}
        </g>
      ))}
    </BaseChart>
  );
};

/**
 * 仪表盘组件
 */
const GaugeChart = ({
  value = 0,
  maxValue = 100,
  minValue = 0,
  segments = 5,
  showValue = true,
  showNeedle = true,
  ...props
}) => {
  // 计算仪表盘参数
  const centerX = props.chartArea.width / 2;
  const centerY = props.chartArea.height / 2;
  const radius = Math.min(centerX, centerY) - 10;
  
  // 计算角度范围（240度圆弧）
  const startAngle = -120;
  const endAngle = 60;
  const angleRange = endAngle - startAngle;
  
  // 计算当前值对应的角度
  const normalizedValue = Math.max(minValue, Math.min(value, maxValue));
  const valueAngle = startAngle + (normalizedValue / maxValue) * angleRange;
  
  // 生成刻度
  const generateTickMarks = () => {
    const ticks = [];
    for (let i = 0; i <= segments; i++) {
      const tickValue = minValue + (i / segments) * (maxValue - minValue);
      const tickAngle = startAngle + (i / segments) * angleRange;
      const isMajor = i % (segments / 5) === 0;
      
      ticks.push({
        value: tickValue,
        angle: tickAngle,
        isMajor,
        length: isMajor ? 10 : 5
      });
    }
    return ticks;
  };

  const ticks = generateTickMarks();

  // 生成圆弧路径
  const generateArcPath = (startAngle, endAngle, innerRadius = 0) => {
    const startRad = (startAngle - 90) * Math.PI / 180;
    const endRad = (endAngle - 90) * Math.PI / 180;
    
    const x1 = centerX + Math.cos(startRad) * radius;
    const y1 = centerY + Math.sin(startRad) * radius;
    const x2 = centerX + Math.cos(endRad) * radius;
    const y2 = centerY + Math.sin(endRad) * radius;
    
    const innerX1 = centerX + Math.cos(startRad) * innerRadius;
    const innerY1 = centerY + Math.sin(startRad) * innerRadius;
    const innerX2 = centerX + Math.cos(endRad) * innerRadius;
    const innerY2 = centerY + Math.sin(endRad) * innerRadius;
    
    const largeArc = (endAngle - startAngle) > 180 ? 1 : 0;
    
    if (innerRadius > 0) {
      return `
        M ${innerX1} ${innerY1}
        L ${x1} ${y1}
        A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
        L ${innerX2} ${innerY2}
        A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${innerX1} ${innerY1}
        Z
      `;
    } else {
      return `
        M ${centerX} ${centerY}
        L ${x1} ${y1}
        A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
        Z
      `;
    }
  };

  return (
    <BaseChart data={[{ value }]} {...props}>
      {/* 背景圆弧 */}
      <path
        d={generateArcPath(startAngle, endAngle)}
        fill="#f0f0f0"
        className="gauge-chart__background"
      />
      
      {/* 值圆弧 */}
      <path
        d={generateArcPath(startAngle, valueAngle)}
        fill="#3498db"
        className="gauge-chart__value-arc"
      />
      
      {/* 刻度线 */}
      {ticks.map((tick, index) => {
        const angleRad = (tick.angle - 90) * Math.PI / 180;
        const x1 = centerX + Math.cos(angleRad) * (radius - tick.length);
        const y1 = centerY + Math.sin(angleRad) * (radius - tick.length);
        const x2 = centerX + Math.cos(angleRad) * radius;
        const y2 = centerY + Math.sin(angleRad) * radius;
        
        return (
          <g key={index}>
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#666"
              strokeWidth={tick.isMajor ? 2 : 1}
              className="gauge-chart__tick"
            />
            
            {/* 刻度标签 */}
            {tick.isMajor && (
              <text
                x={centerX + Math.cos(angleRad) * (radius - 20)}
                y={centerY + Math.sin(angleRad) * (radius - 20)}
                textAnchor="middle"
                dominantBaseline="middle"
                className="gauge-chart__tick-label"
                fontSize={9}
                fill="#666"
              >
                {tick.value}
              </text>
            )}
          </g>
        );
      })}
      
      {/* 指针 */}
      {showNeedle && (
        <line
          x1={centerX}
          y1={centerY}
          x2={centerX + Math.cos((valueAngle - 90) * Math.PI / 180) * (radius - 10)}
          y2={centerY + Math.sin((valueAngle - 90) * Math.PI / 180) * (radius - 10)}
          stroke="#e74c3c"
          strokeWidth={3}
          className="gauge-chart__needle"
        />
      )}
      
      {/* 中心值显示 */}
      {showValue && (
        <text
          x={centerX}
          y={centerY + 20}
          textAnchor="middle"
          dominantBaseline="middle"
          className="gauge-chart__value-text"
          fontSize={16}
          fill="#333"
          fontWeight="bold"
        >
          {value}
        </text>
      )}
    </BaseChart>
  );
};

// 导出所有高级图表组件
const AdvancedCharts = {
  Pie: PieChart,
  Scatter: ScatterChart,
  Area: AreaChart,
  Radar: RadarChart,
  Gauge: GaugeChart
};

export default AdvancedCharts;