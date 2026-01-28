import React, { useState } from 'react';
import ChartConfigurator from './ChartConfigurator';
import BaseChart from './BaseChart';
import AdvancedCharts from './AdvancedCharts';
import './ChartExample.css';

/**
 * 图表示例组件
 */
const ChartExample = () => {
  const [currentConfig, setCurrentConfig] = useState(null);
  const [savedConfigs, setSavedConfigs] = useState([]);
  const [activeTab, setActiveTab] = useState('configurator');

  // 示例数据
  const sampleData = [
    { id: 1, label: '一月', value: 120, category: 'A' },
    { id: 2, label: '二月', value: 200, category: 'A' },
    { id: 3, label: '三月', value: 150, category: 'B' },
    { id: 4, label: '四月', value: 80, category: 'B' },
    { id: 5, label: '五月', value: 300, category: 'C' },
    { id: 6, label: '六月', value: 250, category: 'C' }
  ];

  // 处理配置变化
  const handleConfigChange = (config) => {
    setCurrentConfig(config);
  };

  // 处理配置保存
  const handleSaveConfig = (config) => {
    const newConfig = {
      ...config,
      id: `config-${Date.now()}`,
      savedAt: new Date().toISOString()
    };
    
    setSavedConfigs(prev => [...prev, newConfig]);
    
    // 显示保存成功的消息
    alert('配置已保存！');
  };

  // 加载已保存的配置
  const loadSavedConfig = (config) => {
    setCurrentConfig(config);
    setActiveTab('configurator');
  };

  // 删除已保存的配置
  const deleteSavedConfig = (configId) => {
    setSavedConfigs(prev => prev.filter(config => config.id !== configId));
  };

  // 渲染图表
  const renderChart = (config) => {
    if (!config) return null;

    const chartProps = {
      data: sampleData, // 使用示例数据
      width: config.width || 600,
      height: config.height || 400,
      title: config.title,
      description: config.description,
      margin: config.style?.margin || { top: 20, right: 20, bottom: 40, left: 40 },
      colors: config.style?.colors || ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'],
      animation: config.style?.animation !== false,
      interactive: config.style?.interactive !== false,
      responsive: config.style?.responsive !== false,
      ...config.chartSpecific
    };

    try {
      switch (config.chartType) {
        case 'bar':
          return <BaseChart.Bar {...chartProps} />;
        
        case 'line':
          return <BaseChart.Line {...chartProps} />;
        
        case 'pie':
          return <AdvancedCharts.Pie {...chartProps} />;
        
        case 'scatter':
          return <AdvancedCharts.Scatter {...chartProps} />;
        
        case 'area':
          return <AdvancedCharts.Area {...chartProps} />;
        
        case 'radar':
          return <AdvancedCharts.Radar {...chartProps} />;
        
        case 'gauge':
          return <AdvancedCharts.Gauge {...chartProps} />;
        
        default:
          return <BaseChart.Bar {...chartProps} />;
      }
    } catch (error) {
      console.error('图表渲染错误:', error);
      return (
        <div className="chart-example__error">
          <p>图表渲染失败</p>
          <p>{error.message}</p>
        </div>
      );
    }
  };

  return (
    <div className="chart-example">
      <div className="chart-example__header">
        <h1>数据可视化示例</h1>
        <p>使用图表配置器创建和自定义各种图表</p>
      </div>

      <div className="chart-example__tabs">
        <button 
          className={`chart-example__tab ${activeTab === 'configurator' ? 'chart-example__tab--active' : ''}`}
          onClick={() => setActiveTab('configurator')}
        >
          图表配置器
        </button>
        <button 
          className={`chart-example__tab ${activeTab === 'saved' ? 'chart-example__tab--active' : ''}`}
          onClick={() => setActiveTab('saved')}
        >
          已保存配置
        </button>
        <button 
          className={`chart-example__tab ${activeTab === 'examples' ? 'chart-example__tab--active' : ''}`}
          onClick={() => setActiveTab('examples')}
        >
          示例图表
        </button>
      </div>

      <div className="chart-example__content">
        {activeTab === 'configurator' && (
          <div className="chart-example__configurator-section">
            <div className="chart-example__configurator">
              <ChartConfigurator
                initialConfig={currentConfig || {
                  chartType: 'bar',
                  title: '销售数据图表',
                  description: '展示月度销售数据',
                  width: 600,
                  height: 400,
                  dataBinding: {
                    dataSource: 'static',
                    dataFormat: 'json',
                    sourceConfig: { data: sampleData },
                    transformers: [],
                    refreshInterval: 0,
                    cacheEnabled: true
                  },
                  style: {
                    colors: ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'],
                    margin: { top: 20, right: 20, bottom: 40, left: 40 },
                    animation: true,
                    interactive: true,
                    responsive: true
                  }
                }}
                onConfigChange={handleConfigChange}
                onSave={handleSaveConfig}
              />
            </div>
          </div>
        )}

        {activeTab === 'saved' && (
          <div className="chart-example__saved-section">
            {savedConfigs.length === 0 ? (
              <div className="chart-example__empty">
                <p>暂无保存的配置</p>
                <p>请在配置器页面创建并保存图表配置</p>
              </div>
            ) : (
              <div className="chart-example__saved-list">
                {savedConfigs.map(config => (
                  <div key={config.id} className="chart-example__saved-item">
                    <div className="chart-example__saved-info">
                      <h4>{config.title || '未命名图表'}</h4>
                      <p>图表类型: {getChartTypeLabel(config.chartType)}</p>
                      <p>保存时间: {new Date(config.savedAt).toLocaleString()}</p>
                    </div>
                    <div className="chart-example__saved-actions">
                      <button 
                        className="chart-example__action-button chart-example__action-button--primary"
                        onClick={() => loadSavedConfig(config)}
                      >
                        加载
                      </button>
                      <button 
                        className="chart-example__action-button chart-example__action-button--danger"
                        onClick={() => deleteSavedConfig(config.id)}
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'examples' && (
          <div className="chart-example__examples-section">
            <div className="chart-example__examples-grid">
              {/* 柱状图示例 */}
              <div className="chart-example__example-item">
                <h3>柱状图示例</h3>
                <BaseChart.Bar
                  data={sampleData}
                  width={300}
                  height={200}
                  title="月度销售数据"
                  colors={['#3498db', '#2ecc71']}
                />
              </div>

              {/* 折线图示例 */}
              <div className="chart-example__example-item">
                <h3>折线图示例</h3>
                <BaseChart.Line
                  data={sampleData}
                  width={300}
                  height={200}
                  title="销售趋势"
                  showPoints={true}
                />
              </div>

              {/* 饼图示例 */}
              <div className="chart-example__example-item">
                <h3>饼图示例</h3>
                <AdvancedCharts.Pie
                  data={[
                    { label: '类别A', value: 40 },
                    { label: '类别B', value: 35 },
                    { label: '类别C', value: 25 }
                  ]}
                  width={300}
                  height={200}
                  title="类别分布"
                  showLabels={true}
                />
              </div>

              {/* 散点图示例 */}
              <div className="chart-example__example-item">
                <h3>散点图示例</h3>
                <AdvancedCharts.Scatter
                  data={[
                    { x: 10, y: 20, size: 5, label: '点1' },
                    { x: 30, y: 40, size: 8, label: '点2' },
                    { x: 50, y: 60, size: 12, label: '点3' },
                    { x: 70, y: 30, size: 6, label: '点4' }
                  ]}
                  width={300}
                  height={200}
                  title="散点分布"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 当前配置预览 */}
      {currentConfig && activeTab !== 'configurator' && (
        <div className="chart-example__preview">
          <h3>当前配置预览</h3>
          <div className="chart-example__preview-chart">
            {renderChart(currentConfig)}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * 获取图表类型标签
 */
const getChartTypeLabel = (chartType) => {
  const chartTypes = {
    bar: '柱状图',
    line: '折线图',
    pie: '饼图',
    scatter: '散点图',
    area: '面积图',
    radar: '雷达图',
    gauge: '仪表盘'
  };
  
  return chartTypes[chartType] || chartType;
};

export default ChartExample;