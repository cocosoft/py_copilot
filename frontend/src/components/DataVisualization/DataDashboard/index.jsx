/**
 * 数据可视化仪表板组件
 *
 * 基于现有组件开发数据可视化功能
 *
 * 任务编号: Phase2-Week6
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import React, { useState, useEffect, useMemo } from 'react';
import * as d3 from 'd3';
import { Card, Button, Badge } from '../../UnifiedComponentLibrary';

/**
 * 柱状图组件
 * @param {Object} props - 组件属性
 * @param {Array} props.data - 数据
 * @param {string} props.xKey - X轴键
 * @param {string} props.yKey - Y轴键
 * @param {Object} props.options - 图表选项
 */
const BarChart = ({ data, xKey, yKey, options = {} }) => {
  const svgRef = React.useRef(null);

  useEffect(() => {
    if (!data || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 20, bottom: 40, left: 40 };
    const width = (options.width || 400) - margin.left - margin.right;
    const height = (options.height || 300) - margin.top - margin.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // X轴
    const x = d3
      .scaleBand()
      .domain(data.map((d) => d[xKey]))
      .range([0, width])
      .padding(0.1);

    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end');

    // Y轴
    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d[yKey])])
      .nice()
      .range([height, 0]);

    g.append('g').call(d3.axisLeft(y));

    // 柱状图
    g.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', (d) => x(d[xKey]))
      .attr('width', x.bandwidth())
      .attr('y', (d) => y(d[yKey]))
      .attr('height', (d) => height - y(d[yKey]))
      .attr('fill', options.color || '#3b82f6');

    // 数值标签
    g.selectAll('.label')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'label')
      .attr('x', (d) => x(d[xKey]) + x.bandwidth() / 2)
      .attr('y', (d) => y(d[yKey]) - 5)
      .attr('text-anchor', 'middle')
      .text((d) => d[yKey]);
  }, [data, xKey, yKey, options]);

  return (
    <svg
      ref={svgRef}
      width={options.width || 400}
      height={options.height || 300}
      className="bar-chart"
    />
  );
};

/**
 * 饼图组件
 * @param {Object} props - 组件属性
 * @param {Array} props.data - 数据
 * @param {string} props.labelKey - 标签键
 * @param {string} props.valueKey - 值键
 * @param {Object} props.options - 图表选项
 */
const PieChart = ({ data, labelKey, valueKey, options = {} }) => {
  const svgRef = React.useRef(null);

  useEffect(() => {
    if (!data || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = options.width || 400;
    const height = options.height || 300;
    const radius = Math.min(width, height) / 2 - 20;

    const g = svg
      .append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`);

    // 颜色比例尺
    const color = d3
      .scaleOrdinal()
      .domain(data.map((d) => d[labelKey]))
      .range(d3.schemeCategory10);

    // 饼图生成器
    const pie = d3
      .pie()
      .value((d) => d[valueKey])
      .sort(null);

    // 弧生成器
    const arc = d3.arc().innerRadius(0).outerRadius(radius);

    // 绘制饼图
    const arcs = g.selectAll('.arc').data(pie(data)).enter().append('g').attr('class', 'arc');

    arcs
      .append('path')
      .attr('d', arc)
      .attr('fill', (d) => color(d.data[labelKey]))
      .attr('stroke', 'white')
      .attr('stroke-width', 2);

    // 标签
    const labelArc = d3.arc().innerRadius(radius * 0.6).outerRadius(radius * 0.6);

    arcs
      .append('text')
      .attr('transform', (d) => `translate(${labelArc.centroid(d)})`)
      .attr('text-anchor', 'middle')
      .text((d) => {
        const percentage = ((d.endAngle - d.startAngle) / (2 * Math.PI)) * 100;
        return percentage > 5 ? `${percentage.toFixed(1)}%` : '';
      });

    // 图例
    const legend = svg
      .append('g')
      .attr('transform', `translate(${width - 100}, 20)`);

    data.forEach((d, i) => {
      const legendRow = legend.append('g').attr('transform', `translate(0, ${i * 20})`);

      legendRow.append('rect').attr('width', 10).attr('height', 10).attr('fill', color(d[labelKey]));

      legendRow
        .append('text')
        .attr('x', 15)
        .attr('y', 10)
        .text(d[labelKey])
        .style('font-size', '12px');
    });
  }, [data, labelKey, valueKey, options]);

  return (
    <svg
      ref={svgRef}
      width={options.width || 400}
      height={options.height || 300}
      className="pie-chart"
    />
  );
};

/**
 * 折线图组件
 * @param {Object} props - 组件属性
 * @param {Array} props.data - 数据
 * @param {string} props.xKey - X轴键
 * @param {string} props.yKey - Y轴键
 * @param {Object} props.options - 图表选项
 */
const LineChart = ({ data, xKey, yKey, options = {} }) => {
  const svgRef = React.useRef(null);

  useEffect(() => {
    if (!data || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 20, bottom: 40, left: 40 };
    const width = (options.width || 400) - margin.left - margin.right;
    const height = (options.height || 300) - margin.top - margin.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // X轴
    const x = d3
      .scalePoint()
      .domain(data.map((d) => d[xKey]))
      .range([0, width]);

    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end');

    // Y轴
    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d[yKey])])
      .nice()
      .range([height, 0]);

    g.append('g').call(d3.axisLeft(y));

    // 折线
    const line = d3
      .line()
      .x((d) => x(d[xKey]))
      .y((d) => y(d[yKey]))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', options.color || '#3b82f6')
      .attr('stroke-width', 2)
      .attr('d', line);

    // 数据点
    g.selectAll('.dot')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'dot')
      .attr('cx', (d) => x(d[xKey]))
      .attr('cy', (d) => y(d[yKey]))
      .attr('r', 4)
      .attr('fill', options.color || '#3b82f6');
  }, [data, xKey, yKey, options]);

  return (
    <svg
      ref={svgRef}
      width={options.width || 400}
      height={options.height || 300}
      className="line-chart"
    />
  );
};

/**
 * 统计卡片组件
 * @param {Object} props - 组件属性
 * @param {string} props.title - 标题
 * @param {string|number} props.value - 值
 * @param {string} props.trend - 趋势
 * @param {string} props.icon - 图标
 */
const StatCard = ({ title, value, trend, icon }) => {
  const trendColor = trend?.startsWith('+') ? 'green' : trend?.startsWith('-') ? 'red' : 'gray';

  return (
    <Card className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <div className="stat-title">{title}</div>
        <div className="stat-value">{value}</div>
        {trend && (
          <div className="stat-trend" style={{ color: trendColor }}>
            {trend}
          </div>
        )}
      </div>
    </Card>
  );
};

/**
 * 数据仪表板组件
 * @param {Object} props - 组件属性
 * @param {Object} props.data - 数据
 */
const DataDashboard = ({ data }) => {
  const [activeTab, setActiveTab] = useState('overview');

  // 模拟数据
  const mockData = useMemo(
    () => ({
      stats: {
        totalDocuments: 1234,
        totalEntities: 5678,
        totalRelations: 9876,
        activeUsers: 42,
      },
      documentTypes: [
        { type: 'PDF', count: 450 },
        { type: 'DOC', count: 320 },
        { type: 'TXT', count: 280 },
        { type: 'HTML', count: 184 },
      ],
      entityTypes: [
        { type: '人物', count: 2345 },
        { type: '组织', count: 1234 },
        { type: '地点', count: 987 },
        { type: '事件', count: 654 },
        { type: '概念', count: 458 },
      ],
      activityTrend: [
        { date: '周一', count: 120 },
        { date: '周二', count: 145 },
        { date: '周三', count: 132 },
        { date: '周四', count: 167 },
        { date: '周五', count: 189 },
        { date: '周六', count: 98 },
        { date: '周日', count: 87 },
      ],
    }),
    []
  );

  const dashboardData = data || mockData;

  const tabs = [
    { key: 'overview', label: '概览' },
    { key: 'documents', label: '文档' },
    { key: 'entities', label: '实体' },
    { key: 'activity', label: '活动' },
  ];

  return (
    <div className="data-dashboard">
      <div className="dashboard-header">
        <h2>数据仪表板</h2>
        <div className="dashboard-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'overview' && (
        <div className="dashboard-overview">
          <div className="stats-grid">
            <StatCard
              title="文档总数"
              value={dashboardData.stats.totalDocuments}
              trend="+12%"
              icon="📄"
            />
            <StatCard
              title="实体总数"
              value={dashboardData.stats.totalEntities}
              trend="+8%"
              icon="🏷️"
            />
            <StatCard
              title="关系总数"
              value={dashboardData.stats.totalRelations}
              trend="+15%"
              icon="🔗"
            />
            <StatCard
              title="活跃用户"
              value={dashboardData.stats.activeUsers}
              trend="-3%"
              icon="👥"
            />
          </div>

          <div className="charts-grid">
            <Card className="chart-card">
              <h4>文档类型分布</h4>
              <PieChart
                data={dashboardData.documentTypes}
                labelKey="type"
                valueKey="count"
                options={{ width: 350, height: 250 }}
              />
            </Card>

            <Card className="chart-card">
              <h4>实体类型分布</h4>
              <BarChart
                data={dashboardData.entityTypes}
                xKey="type"
                yKey="count"
                options={{ width: 350, height: 250 }}
              />
            </Card>

            <Card className="chart-card full-width">
              <h4>活动趋势</h4>
              <LineChart
                data={dashboardData.activityTrend}
                xKey="date"
                yKey="count"
                options={{ width: 700, height: 250 }}
              />
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'documents' && (
        <div className="dashboard-documents">
          <Card>
            <h4>文档统计</h4>
            <BarChart
              data={dashboardData.documentTypes}
              xKey="type"
              yKey="count"
              options={{ width: 700, height: 300 }}
            />
          </Card>
        </div>
      )}

      {activeTab === 'entities' && (
        <div className="dashboard-entities">
          <Card>
            <h4>实体统计</h4>
            <PieChart
              data={dashboardData.entityTypes}
              labelKey="type"
              valueKey="count"
              options={{ width: 400, height: 300 }}
            />
          </Card>
        </div>
      )}

      {activeTab === 'activity' && (
        <div className="dashboard-activity">
          <Card>
            <h4>活动趋势</h4>
            <LineChart
              data={dashboardData.activityTrend}
              xKey="date"
              yKey="count"
              options={{ width: 700, height: 300 }}
            />
          </Card>
        </div>
      )}
    </div>
  );
};

export default DataDashboard;
export { BarChart, PieChart, LineChart, StatCard };
