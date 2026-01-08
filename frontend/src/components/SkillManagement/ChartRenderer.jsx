import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';

function ChartRenderer({ data, name, metadata = {} }) {
  const svgRef = useRef();
  const tooltipRef = useRef();
  const [chartType, setChartType] = useState('bar');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // 创建工具提示
  const createTooltip = useCallback(() => {
    if (!tooltipRef.current) {
      tooltipRef.current = d3.select('body')
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.8)')
        .style('color', 'white')
        .style('padding', '8px 12px')
        .style('border-radius', '4px')
        .style('font-size', '12px')
        .style('pointer-events', 'none')
        .style('z-index', '1000');
    }
    return tooltipRef.current;
  }, []);

  // 清理工具提示
  const cleanupTooltip = useCallback(() => {
    if (tooltipRef.current) {
      tooltipRef.current.remove();
      tooltipRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!svgRef.current) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      // 清空之前的图表
      d3.select(svgRef.current).selectAll("*").remove();
      
      // 解析图表数据
      const chartData = parseChartData(data, metadata);
      
      if (!chartData || chartData.length === 0) {
        setError('无效的图表数据');
        setIsLoading(false);
        return;
      }
      
      // 根据数据类型选择合适的图表类型
      const detectedType = detectChartType(chartData, metadata);
      setChartType(detectedType);
      
      // 渲染图表
      renderChart(chartData, detectedType, metadata);
      
    } catch (err) {
      setError(`图表渲染错误: ${err.message}`);
      console.error('图表渲染错误:', err);
    } finally {
      setIsLoading(false);
    }
  }, [data, metadata]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      cleanupTooltip();
    };
  }, [cleanupTooltip]);

  const parseChartData = (rawData, meta) => {
    try {
      // 如果数据是字符串，尝试解析为JSON
      if (typeof rawData === 'string') {
        return JSON.parse(rawData);
      }
      
      // 如果已经是对象或数组，直接返回
      if (Array.isArray(rawData) || typeof rawData === 'object') {
        return rawData;
      }
      
      return null;
    } catch (err) {
      console.error('数据解析错误:', err);
      return null;
    }
  };

  const detectChartType = (data, meta) => {
    // 优先使用元数据中指定的类型
    if (meta.chartType) {
      return meta.chartType;
    }
    
    // 根据数据结构自动检测
    if (Array.isArray(data)) {
      if (data.length === 0) return 'bar';
      
      const firstItem = data[0];
      
      // 如果是简单数值数组，使用柱状图
      if (typeof firstItem === 'number') {
        return 'bar';
      }
      
      // 如果是对象数组，检查字段
      if (typeof firstItem === 'object') {
        const keys = Object.keys(firstItem);
        
        // 如果有x和y字段，可能是散点图或折线图
        if (keys.includes('x') && keys.includes('y')) {
          return 'line';
        }
        
        // 如果有类别和值字段，可能是柱状图
        if (keys.includes('category') && keys.includes('value')) {
          return 'bar';
        }
        
        // 如果有标签和值字段，可能是饼图
        if (keys.includes('label') && keys.includes('value')) {
          return 'pie';
        }
      }
    }
    
    return 'bar'; // 默认柱状图
  };

  const renderChart = (data, type, meta) => {
    const svg = d3.select(svgRef.current);
    const width = 400;
    const height = 300;
    const margin = { top: 20, right: 30, bottom: 40, left: 40 };
    
    svg.attr("width", width).attr("height", height);
    
    const chartGroup = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    switch (type) {
      case 'bar':
        renderBarChart(chartGroup, data, chartWidth, chartHeight, meta);
        break;
      case 'line':
        renderLineChart(chartGroup, data, chartWidth, chartHeight, meta);
        break;
      case 'pie':
        renderPieChart(chartGroup, data, chartWidth, chartHeight, meta);
        break;
      case 'scatter':
        renderScatterChart(chartGroup, data, chartWidth, chartHeight, meta);
        break;
      default:
        renderBarChart(chartGroup, data, chartWidth, chartHeight, meta);
    }
  };

  const renderBarChart = (group, data, width, height, meta) => {
    // 准备数据
    const chartData = Array.isArray(data) && data.length > 0 ? data : 
      [{ label: '数据1', value: 10 }, { label: '数据2', value: 20 }];
    
    // 创建比例尺
    const xScale = d3.scaleBand()
      .domain(chartData.map(d => d.label || d.category || d.name || d.x))
      .range([0, width])
      .padding(0.1);
    
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(chartData, d => d.value || d.y || d)])
      .range([height, 0]);
    
    // 添加坐标轴
    group.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale));
    
    group.append("g")
      .call(d3.axisLeft(yScale));
    
    // 添加网格线
    group.append("g")
      .attr("class", "grid")
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat("")
      );
    
    // 添加柱状图
    const bars = group.selectAll(".bar")
      .data(chartData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", d => xScale(d.label || d.category || d.name || d.x))
      .attr("y", height)
      .attr("width", xScale.bandwidth())
      .attr("height", 0)
      .attr("fill", "steelblue");
    
    // 添加动画效果
    bars.transition()
      .duration(800)
      .attr("y", d => yScale(d.value || d.y || d))
      .attr("height", d => height - yScale(d.value || d.y || d));
    
    // 添加工具提示
    const tooltip = createTooltip();
    bars.on("mouseover", function(event, d) {
        tooltip.style("opacity", 1)
          .html(`<strong>${d.label || d.category || d.name || d.x}</strong><br/>值: ${d.value || d.y || d}`)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function() {
        tooltip.style("opacity", 0);
      });
  };

  const renderLineChart = (group, data, width, height, meta) => {
    // 准备数据
    const chartData = Array.isArray(data) && data.length > 0 ? data : 
      [{ x: 1, y: 10 }, { x: 2, y: 20 }, { x: 3, y: 15 }];
    
    // 创建比例尺
    const xScale = d3.scaleLinear()
      .domain(d3.extent(chartData, d => d.x))
      .range([0, width]);
    
    const yScale = d3.scaleLinear()
      .domain(d3.extent(chartData, d => d.y))
      .range([height, 0]);
    
    // 创建折线生成器
    const line = d3.line()
      .x(d => xScale(d.x))
      .y(d => yScale(d.y))
      .curve(d3.curveMonotoneX);
    
    // 添加坐标轴
    group.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale));
    
    group.append("g")
      .call(d3.axisLeft(yScale));
    
    // 添加网格线
    group.append("g")
      .attr("class", "grid")
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat("")
      );
    
    // 添加折线（带动画）
    const path = group.append("path")
      .datum(chartData)
      .attr("class", "line")
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", function() {
        const length = this.getTotalLength();
        return length + " " + length;
      })
      .attr("stroke-dashoffset", function() {
        return this.getTotalLength();
      });
    
    // 折线动画
    path.transition()
      .duration(1000)
      .attr("stroke-dashoffset", 0);
    
    // 添加数据点
    const dots = group.selectAll(".dot")
      .data(chartData)
      .enter()
      .append("circle")
      .attr("class", "dot")
      .attr("cx", d => xScale(d.x))
      .attr("cy", d => yScale(d.y))
      .attr("r", 0)
      .attr("fill", "steelblue");
    
    // 数据点动画
    dots.transition()
      .delay(800)
      .duration(300)
      .attr("r", 3);
    
    // 添加工具提示
    const tooltip = createTooltip();
    dots.on("mouseover", function(event, d) {
        tooltip.style("opacity", 1)
          .html(`<strong>X: ${d.x}</strong><br/>Y: ${d.y}`)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function() {
        tooltip.style("opacity", 0);
      });
  };

  const renderPieChart = (group, data, width, height, meta) => {
    // 准备数据
    const chartData = Array.isArray(data) && data.length > 0 ? data : 
      [{ label: '类别A', value: 30 }, { label: '类别B', value: 50 }, { label: '类别C', value: 20 }];
    
    const radius = Math.min(width, height) / 2;
    
    // 创建饼图生成器
    const pie = d3.pie()
      .value(d => d.value)
      .sort(null);
    
    const arc = d3.arc()
      .innerRadius(0)
      .outerRadius(radius);
    
    const color = d3.scaleOrdinal()
      .domain(chartData.map(d => d.label))
      .range(d3.schemeCategory10);
    
    // 移动到中心
    const pieGroup = group.append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);
    
    // 添加扇形（带动画）
    const paths = pieGroup.selectAll("path")
      .data(pie(chartData))
      .enter()
      .append("path")
      .attr("d", arc)
      .attr("fill", d => color(d.data.label))
      .attr("stroke", "white")
      .attr("stroke-width", 2)
      .attr("opacity", 0);
    
    // 扇形动画
    paths.transition()
      .duration(1000)
      .attr("opacity", 1)
      .attrTween("d", function(d) {
        const interpolate = d3.interpolate(
          { startAngle: 0, endAngle: 0 },
          d
        );
        return function(t) {
          return arc(interpolate(t));
        };
      });
    
    // 添加工具提示
    const tooltip = createTooltip();
    paths.on("mouseover", function(event, d) {
        d3.select(this).attr("stroke-width", 3);
        tooltip.style("opacity", 1)
          .html(`<strong>${d.data.label}</strong><br/>值: ${d.data.value}<br/>占比: ${((d.data.value / d3.sum(chartData, d => d.value)) * 100).toFixed(1)}%`)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function() {
        d3.select(this).attr("stroke-width", 2);
        tooltip.style("opacity", 0);
      });
    
    // 添加标签
    pieGroup.selectAll("text")
      .data(pie(chartData))
      .enter()
      .append("text")
      .attr("transform", d => `translate(${arc.centroid(d)})`)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "white")
      .attr("font-weight", "bold")
      .text(d => d.data.label);
  };

  const renderScatterChart = (group, data, width, height, meta) => {
    // 准备数据
    const chartData = Array.isArray(data) && data.length > 0 ? data : 
      [{ x: 1, y: 10 }, { x: 2, y: 20 }, { x: 3, y: 15 }];
    
    // 创建比例尺
    const xScale = d3.scaleLinear()
      .domain(d3.extent(chartData, d => d.x))
      .range([0, width]);
    
    const yScale = d3.scaleLinear()
      .domain(d3.extent(chartData, d => d.y))
      .range([height, 0]);
    
    // 添加坐标轴
    group.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale));
    
    group.append("g")
      .call(d3.axisLeft(yScale));
    
    // 添加网格线
    group.append("g")
      .attr("class", "grid")
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat("")
      );
    
    // 添加散点（带动画）
    const dots = group.selectAll(".dot")
      .data(chartData)
      .enter()
      .append("circle")
      .attr("class", "dot")
      .attr("cx", d => xScale(d.x))
      .attr("cy", height)
      .attr("r", 0)
      .attr("fill", "steelblue");
    
    // 散点动画
    dots.transition()
      .duration(800)
      .attr("cy", d => yScale(d.y))
      .attr("r", 5);
    
    // 添加工具提示
    const tooltip = createTooltip();
    dots.on("mouseover", function(event, d) {
        d3.select(this).attr("r", 8);
        tooltip.style("opacity", 1)
          .html(`<strong>X: ${d.x}</strong><br/>Y: ${d.y}`)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function() {
        d3.select(this).attr("r", 5);
        tooltip.style("opacity", 0);
      });
    
    // 添加趋势线（如果数据适合）
    if (chartData.length >= 3) {
      const linearRegression = d3.regressionLinear()
        .x(d => d.x)
        .y(d => d.y)
        .domain(xScale.domain());
      
      const trendLine = linearRegression(chartData);
      
      const line = d3.line()
        .x(d => xScale(d[0]))
        .y(d => yScale(d[1]));
      
      group.append("path")
        .datum(trendLine)
        .attr("class", "trend-line")
        .attr("d", line)
        .attr("fill", "none")
        .attr("stroke", "red")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "5,5");
    }
  };

  if (isLoading) {
    return (
      <div className="chart-renderer" style={{
        padding: '16px',
        background: 'white',
        borderRadius: '8px',
        border: '1px solid #e1e5e9',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '300px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '4px solid #f3f4f6',
            borderTop: '4px solid #3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p style={{ margin: 0, color: '#6b7280' }}>正在加载图表数据...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-error" style={{
        padding: '16px',
        background: '#fef2f2',
        borderRadius: '8px',
        border: '1px solid #fecaca',
        color: '#dc2626'
      }}>
        <p style={{ margin: '0 0 12px 0', fontWeight: '600' }}>图表渲染失败: {error}</p>
        <details style={{ fontSize: '12px' }}>
          <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>查看原始数据</summary>
          <pre style={{
            background: '#f8fafc',
            padding: '8px',
            borderRadius: '4px',
            overflow: 'auto',
            fontSize: '10px',
            maxHeight: '200px'
          }}>{JSON.stringify(data, null, 2)}</pre>
        </details>
      </div>
    );
  }

  return (
    <div className="chart-renderer" style={{
      padding: '16px',
      background: 'white',
      borderRadius: '8px',
      border: '1px solid #e1e5e9'
    }}>
      <div className="chart-header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>{name}</h4>
        <span className="chart-type" style={{
          fontSize: '12px',
          color: '#6b7280',
          padding: '4px 8px',
          background: '#f3f4f6',
          borderRadius: '4px'
        }}>图表类型: {chartType}</span>
      </div>
      <svg ref={svgRef} className="d3-chart" style={{
        width: '100%',
        height: '250px',
        background: '#f8fafc',
        borderRadius: '4px'
      }}></svg>
      <div className="chart-controls" style={{
        display: 'flex',
        gap: '8px',
        marginTop: '16px',
        justifyContent: 'center'
      }}>
        <button 
          onClick={() => setChartType('bar')}
          style={{
            padding: '6px 12px',
            border: '1px solid #d1d5db',
            background: chartType === 'bar' ? '#3b82f6' : 'white',
            color: chartType === 'bar' ? 'white' : '#374151',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >柱状图</button>
        <button 
          onClick={() => setChartType('line')}
          style={{
            padding: '6px 12px',
            border: '1px solid #d1d5db',
            background: chartType === 'line' ? '#3b82f6' : 'white',
            color: chartType === 'line' ? 'white' : '#374151',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >折线图</button>
        <button 
          onClick={() => setChartType('pie')}
          style={{
            padding: '6px 12px',
            border: '1px solid #d1d5db',
            background: chartType === 'pie' ? '#3b82f6' : 'white',
            color: chartType === 'pie' ? 'white' : '#374151',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >饼图</button>
        <button 
          onClick={() => setChartType('scatter')}
          style={{
            padding: '6px 12px',
            border: '1px solid #d1d5db',
            background: chartType === 'scatter' ? '#3b82f6' : 'white',
            color: chartType === 'scatter' ? 'white' : '#374151',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >散点图</button>
      </div>
    </div>
  );
}

export default ChartRenderer;