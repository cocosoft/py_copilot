import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import './DataVisualization.css';

/**
 * 数据可视化组件
 * 提供多种图表类型：折线图、柱状图、饼图、雷达图
 */
const DataVisualization = ({ 
  data = [], 
  chartType = 'line', 
  title = '数据可视化',
  height = 400,
  width = 800,
  margin = { top: 40, right: 30, bottom: 60, left: 60 }
}) => {
  const svgRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!data || data.length === 0) return;

    try {
      setError(null);
      renderChart();
    } catch (err) {
      setError(`图表渲染失败: ${err.message}`);
      console.error('Chart rendering error:', err);
    }
  }, [data, chartType, height, width, margin]);

  /**
   * 渲染图表
   */
  const renderChart = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // 清空现有内容

    // 设置图表尺寸
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // 创建主容器
    const g = svg
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // 根据图表类型渲染
    switch (chartType) {
      case 'line':
        renderLineChart(g, innerWidth, innerHeight);
        break;
      case 'bar':
        renderBarChart(g, innerWidth, innerHeight);
        break;
      case 'pie':
        renderPieChart(g, innerWidth, innerHeight);
        break;
      case 'radar':
        renderRadarChart(g, innerWidth, innerHeight);
        break;
      default:
        throw new Error(`不支持的图表类型: ${chartType}`);
    }

    // 添加标题
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', margin.top / 2)
      .attr('text-anchor', 'middle')
      .attr('class', 'chart-title')
      .text(title);
  };

  /**
   * 渲染折线图
   */
  const renderLineChart = (g, width, height) => {
    // 准备数据
    const parseDate = d3.timeParse('%Y-%m-%d');
    const processedData = data.map(d => ({
      date: parseDate(d.date) || new Date(d.date),
      value: Number(d.value)
    })).filter(d => !isNaN(d.value) && d.date);

    if (processedData.length === 0) {
      throw new Error('无效的折线图数据');
    }

    // 比例尺
    const x = d3.scaleTime()
      .domain(d3.extent(processedData, d => d.date))
      .range([0, width]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(processedData, d => d.value) * 1.1])
      .range([height, 0]);

    // 线条生成器
    const line = d3.line()
      .x(d => x(d.date))
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX);

    // 添加X轴
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(5))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .attr('text-anchor', 'end')
      .attr('font-size', '12px');

    // 添加Y轴
    g.append('g')
      .call(d3.axisLeft(y));

    // 添加线条
    g.append('path')
      .datum(processedData)
      .attr('fill', 'none')
      .attr('stroke', '#1890ff')
      .attr('stroke-width', 2)
      .attr('d', line);

    // 添加数据点
    g.selectAll('.dot')
      .data(processedData)
      .enter()
      .append('circle')
      .attr('class', 'dot')
      .attr('cx', d => x(d.date))
      .attr('cy', d => y(d.value))
      .attr('r', 4)
      .attr('fill', '#1890ff')
      .on('mouseover', function(event, d) {
        d3.select(this).attr('r', 6).attr('fill', '#096dd9');
        // 显示 tooltip
        g.append('text')
          .attr('class', 'tooltip')
          .attr('x', x(d.date))
          .attr('y', y(d.value) - 10)
          .attr('text-anchor', 'middle')
          .attr('fill', 'black')
          .text(`${d.value}`);
      })
      .on('mouseout', function() {
        d3.select(this).attr('r', 4).attr('fill', '#1890ff');
        g.select('.tooltip').remove();
      });
  };

  /**
   * 渲染柱状图
   */
  const renderBarChart = (g, width, height) => {
    // 准备数据
    const processedData = data.map(d => ({
      name: d.name || d.label,
      value: Number(d.value)
    })).filter(d => !isNaN(d.value) && d.name);

    if (processedData.length === 0) {
      throw new Error('无效的柱状图数据');
    }

    // 比例尺
    const x = d3.scaleBand()
      .domain(processedData.map(d => d.name))
      .range([0, width])
      .padding(0.2);

    const y = d3.scaleLinear()
      .domain([0, d3.max(processedData, d => d.value) * 1.1])
      .range([height, 0]);

    // 添加X轴
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .attr('text-anchor', 'end')
      .attr('font-size', '12px');

    // 添加Y轴
    g.append('g')
      .call(d3.axisLeft(y));

    // 添加柱子
    g.selectAll('.bar')
      .data(processedData)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.name))
      .attr('y', d => y(d.value))
      .attr('width', x.bandwidth())
      .attr('height', d => height - y(d.value))
      .attr('fill', '#1890ff')
      .on('mouseover', function(event, d) {
        d3.select(this).attr('fill', '#096dd9');
        // 显示 tooltip
        g.append('text')
          .attr('class', 'tooltip')
          .attr('x', x(d.name) + x.bandwidth() / 2)
          .attr('y', y(d.value) - 10)
          .attr('text-anchor', 'middle')
          .attr('fill', 'black')
          .text(`${d.value}`);
      })
      .on('mouseout', function() {
        d3.select(this).attr('fill', '#1890ff');
        g.select('.tooltip').remove();
      });
  };

  /**
   * 渲染饼图
   */
  const renderPieChart = (g, width, height) => {
    // 准备数据
    const processedData = data.map(d => ({
      name: d.name || d.label,
      value: Number(d.value)
    })).filter(d => !isNaN(d.value) && d.name);

    if (processedData.length === 0) {
      throw new Error('无效的饼图数据');
    }

    const radius = Math.min(width, height) / 2;

    // 创建饼图布局
    const pie = d3.pie()
      .sort(null)
      .value(d => d.value);

    // 创建弧生成器
    const arc = d3.arc()
      .innerRadius(0)
      .outerRadius(radius);

    // 创建标签弧生成器
    const labelArc = d3.arc()
      .innerRadius(radius * 0.7)
      .outerRadius(radius * 0.9);

    // 颜色比例尺
    const color = d3.scaleOrdinal()
      .domain(processedData.map(d => d.name))
      .range(['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2']);

    // 添加饼图
    const arcs = g.selectAll('.arc')
      .data(pie(processedData))
      .enter()
      .append('g')
      .attr('class', 'arc')
      .attr('transform', `translate(${width / 2},${height / 2})`);

    // 添加路径
    arcs.append('path')
      .attr('d', arc)
      .attr('fill', d => color(d.data.name))
      .on('mouseover', function(event, d) {
        d3.select(this)
          .attr('stroke', '#000')
          .attr('stroke-width', 2);
        // 显示 tooltip
        g.append('text')
          .attr('class', 'tooltip')
          .attr('x', width / 2)
          .attr('y', height / 2)
          .attr('text-anchor', 'middle')
          .attr('fill', 'black')
          .text(`${d.data.name}: ${d.data.value}`);
      })
      .on('mouseout', function() {
        d3.select(this)
          .attr('stroke', 'none');
        g.select('.tooltip').remove();
      });

    // 添加标签
    arcs.append('text')
      .attr('transform', d => `translate(${labelArc.centroid(d)})`)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .text(d => d.data.name);
  };

  /**
   * 渲染雷达图
   */
  const renderRadarChart = (g, width, height) => {
    // 准备数据
    if (!data || data.length === 0) {
      throw new Error('无效的雷达图数据');
    }

    const keys = Object.keys(data[0]).filter(key => key !== 'name' && key !== 'label');
    if (keys.length === 0) {
      throw new Error('雷达图数据缺少指标');
    }

    // 计算角度
    const angleSlice = (Math.PI * 2) / keys.length;

    // 计算半径
    const radius = Math.min(width, height) / 2 - 20;

    // 比例尺
    const r = d3.scaleLinear()
      .domain([0, d3.max(data, d => Math.max(...keys.map(key => Number(d[key]))))])
      .range([0, radius]);

    // 创建多边形生成器
    const line = d3.line()
      .x(d => Math.cos(d.angle) * d.radius)
      .y(d => Math.sin(d.angle) * d.radius)
      .curve(d3.curveLinearClosed);

    // 添加网格
    for (let i = 1; i <= 5; i++) {
      const rValue = radius * (i / 5);
      g.append('circle')
        .attr('cx', width / 2)
        .attr('cy', height / 2)
        .attr('r', rValue)
        .attr('fill', 'none')
        .attr('stroke', '#e8e8e8')
        .attr('stroke-width', 1);
    }

    // 添加轴线
    keys.forEach((key, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const x1 = width / 2;
      const y1 = height / 2;
      const x2 = x1 + Math.cos(angle) * radius;
      const y2 = y1 + Math.sin(angle) * radius;

      g.append('line')
        .attr('x1', x1)
        .attr('y1', y1)
        .attr('x2', x2)
        .attr('y2', y2)
        .attr('stroke', '#e8e8e8')
        .attr('stroke-width', 1);

      // 添加标签
      const labelX = x1 + Math.cos(angle) * (radius + 20);
      const labelY = y1 + Math.sin(angle) * (radius + 20);
      g.append('text')
        .attr('x', labelX)
        .attr('y', labelY)
        .attr('text-anchor', angle > Math.PI / 2 && angle < Math.PI * 3 / 2 ? 'end' : 'start')
        .attr('font-size', '12px')
        .text(key);
    });

    // 颜色比例尺
    const color = d3.scaleOrdinal()
      .domain(data.map(d => d.name || d.label))
      .range(['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2']);

    // 添加数据系列
    data.forEach((series, seriesIndex) => {
      const seriesData = keys.map((key, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        return {
          angle,
          radius: r(Number(series[key]))
        };
      });

      // 添加多边形
      g.append('path')
        .datum(seriesData)
        .attr('fill', color(series.name || series.label))
        .attr('fill-opacity', 0.3)
        .attr('stroke', color(series.name || series.label))
        .attr('stroke-width', 2)
        .attr('transform', `translate(${width / 2},${height / 2})`)
        .attr('d', line);

      // 添加数据点
      g.selectAll(`.point-${seriesIndex}`)
        .data(seriesData)
        .enter()
        .append('circle')
        .attr('class', `point-${seriesIndex}`)
        .attr('cx', d => width / 2 + Math.cos(d.angle) * d.radius)
        .attr('cy', d => height / 2 + Math.sin(d.angle) * d.radius)
        .attr('r', 4)
        .attr('fill', color(series.name || series.label));
    });
  };

  if (error) {
    return (
      <div className="data-visualization error">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="data-visualization">
      <svg ref={svgRef} className="chart-svg"></svg>
    </div>
  );
};

export default DataVisualization;