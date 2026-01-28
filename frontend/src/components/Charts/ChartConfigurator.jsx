import React, { useState, useEffect } from 'react';
import BaseChart from './BaseChart';
import AdvancedCharts from './AdvancedCharts';
import useDataBinding, { DATA_SOURCE_TYPES, DATA_FORMATS, DATA_TRANSFORMERS } from '../../hooks/useDataBinding';
import './ChartConfigurator.css';

/**
 * 图表配置器组件
 */
const ChartConfigurator = ({
  initialConfig = {},
  onConfigChange,
  onPreview,
  onSave,
  className = ''
}) => {
  const [config, setConfig] = useState({
    // 基础配置
    chartType: 'bar',
    title: '',
    description: '',
    width: 600,
    height: 400,
    
    // 数据绑定配置
    dataBinding: {
      dataSource: DATA_SOURCE_TYPES.STATIC,
      dataFormat: DATA_FORMATS.JSON,
      sourceConfig: {},
      transformers: [],
      refreshInterval: 0,
      cacheEnabled: true
    },
    
    // 图表样式配置
    style: {
      colors: ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'],
      margin: { top: 20, right: 20, bottom: 40, left: 40 },
      animation: true,
      interactive: true,
      responsive: true
    },
    
    // 图表特定配置
    chartSpecific: {},
    
    ...initialConfig
  });

  const [activeTab, setActiveTab] = useState('basic');
  const [previewData, setPreviewData] = useState([]);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  // 使用数据绑定Hook
  const dataBinding = useDataBinding(config.dataBinding);

  // 更新配置
  const updateConfig = (newConfig) => {
    const updatedConfig = { ...config, ...newConfig };
    setConfig(updatedConfig);
    onConfigChange?.(updatedConfig);
  };

  // 更新数据绑定配置
  const updateDataBinding = (dataBindingConfig) => {
    updateConfig({
      dataBinding: { ...config.dataBinding, ...dataBindingConfig }
    });
  };

  // 更新样式配置
  const updateStyle = (styleConfig) => {
    updateConfig({
      style: { ...config.style, ...styleConfig }
    });
  };

  // 更新图表特定配置
  const updateChartSpecific = (specificConfig) => {
    updateConfig({
      chartSpecific: { ...config.chartSpecific, ...specificConfig }
    });
  };

  // 加载预览数据
  useEffect(() => {
    if (dataBinding.data) {
      setPreviewData(dataBinding.data);
    }
  }, [dataBinding.data]);

  // 生成预览图表
  const renderPreviewChart = () => {
    if (!previewData || previewData.length === 0) {
      return (
        <div className="chart-configurator__preview-empty">
          <p>暂无预览数据</p>
          <p>请配置数据源并刷新数据</p>
        </div>
      );
    }

    const chartProps = {
      data: previewData,
      width: config.width,
      height: config.height,
      title: config.title,
      description: config.description,
      margin: config.style.margin,
      colors: config.style.colors,
      animation: config.style.animation,
      interactive: config.style.interactive,
      responsive: config.style.responsive,
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
        <div className="chart-configurator__preview-error">
          <p>图表渲染失败</p>
          <p>{error.message}</p>
        </div>
      );
    }
  };

  // 处理预览
  const handlePreview = () => {
    setIsPreviewLoading(true);
    dataBinding.refreshData().finally(() => {
      setIsPreviewLoading(false);
      onPreview?.(config);
    });
  };

  // 处理保存
  const handleSave = () => {
    onSave?.(config);
  };

  return (
    <div className={`chart-configurator ${className}`}>
      <div className="chart-configurator__layout">
        {/* 配置面板 */}
        <div className="chart-configurator__config-panel">
          <div className="chart-configurator__tabs">
            <button 
              className={`chart-configurator__tab ${activeTab === 'basic' ? 'chart-configurator__tab--active' : ''}`}
              onClick={() => setActiveTab('basic')}
            >
              基础配置
            </button>
            <button 
              className={`chart-configurator__tab ${activeTab === 'data' ? 'chart-configurator__tab--active' : ''}`}
              onClick={() => setActiveTab('data')}
            >
              数据配置
            </button>
            <button 
              className={`chart-configurator__tab ${activeTab === 'style' ? 'chart-configurator__tab--active' : ''}`}
              onClick={() => setActiveTab('style')}
            >
              样式配置
            </button>
            <button 
              className={`chart-configurator__tab ${activeTab === 'advanced' ? 'chart-configurator__tab--active' : ''}`}
              onClick={() => setActiveTab('advanced')}
            >
              高级配置
            </button>
          </div>

          <div className="chart-configurator__tab-content">
            {activeTab === 'basic' && (
              <BasicConfigPanel 
                config={config}
                onConfigChange={updateConfig}
              />
            )}

            {activeTab === 'data' && (
              <DataConfigPanel 
                config={config.dataBinding}
                onConfigChange={updateDataBinding}
                dataBinding={dataBinding}
              />
            )}

            {activeTab === 'style' && (
              <StyleConfigPanel 
                config={config.style}
                onConfigChange={updateStyle}
              />
            )}

            {activeTab === 'advanced' && (
              <AdvancedConfigPanel 
                config={config.chartSpecific}
                chartType={config.chartType}
                onConfigChange={updateChartSpecific}
              />
            )}
          </div>

          <div className="chart-configurator__actions">
            <button 
              className="chart-configurator__button chart-configurator__button--primary"
              onClick={handlePreview}
              disabled={isPreviewLoading}
            >
              {isPreviewLoading ? '加载中...' : '预览'}
            </button>
            <button 
              className="chart-configurator__button chart-configurator__button--secondary"
              onClick={handleSave}
            >
              保存配置
            </button>
          </div>
        </div>

        {/* 预览面板 */}
        <div className="chart-configurator__preview-panel">
          <div className="chart-configurator__preview-header">
            <h3>图表预览</h3>
            <div className="chart-configurator__preview-info">
              <span>数据量: {previewData.length}</span>
              {dataBinding.lastUpdated && (
                <span>最后更新: {dataBinding.lastUpdated.toLocaleTimeString()}</span>
              )}
            </div>
          </div>
          
          <div className="chart-configurator__preview-content">
            {renderPreviewChart()}
          </div>

          {dataBinding.error && (
            <div className="chart-configurator__error">
              <strong>错误:</strong> {dataBinding.error.message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * 基础配置面板
 */
const BasicConfigPanel = ({ config, onConfigChange }) => {
  const chartTypes = [
    { value: 'bar', label: '柱状图' },
    { value: 'line', label: '折线图' },
    { value: 'pie', label: '饼图' },
    { value: 'scatter', label: '散点图' },
    { value: 'area', label: '面积图' },
    { value: 'radar', label: '雷达图' },
    { value: 'gauge', label: '仪表盘' }
  ];

  return (
    <div className="config-panel">
      <div className="config-field">
        <label className="config-field__label">图表类型</label>
        <select 
          className="config-field__input"
          value={config.chartType}
          onChange={(e) => onConfigChange({ chartType: e.target.value })}
        >
          {chartTypes.map(type => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      <div className="config-field">
        <label className="config-field__label">图表标题</label>
        <input 
          type="text"
          className="config-field__input"
          value={config.title}
          onChange={(e) => onConfigChange({ title: e.target.value })}
          placeholder="请输入图表标题"
        />
      </div>

      <div className="config-field">
        <label className="config-field__label">图表描述</label>
        <textarea 
          className="config-field__input config-field__input--textarea"
          value={config.description}
          onChange={(e) => onConfigChange({ description: e.target.value })}
          placeholder="请输入图表描述"
          rows={3}
        />
      </div>

      <div className="config-row">
        <div className="config-field">
          <label className="config-field__label">宽度</label>
          <input 
            type="number"
            className="config-field__input"
            value={config.width}
            onChange={(e) => onConfigChange({ width: parseInt(e.target.value) || 600 })}
            min={100}
            max={2000}
          />
        </div>

        <div className="config-field">
          <label className="config-field__label">高度</label>
          <input 
            type="number"
            className="config-field__input"
            value={config.height}
            onChange={(e) => onConfigChange({ height: parseInt(e.target.value) || 400 })}
            min={100}
            max={2000}
          />
        </div>
      </div>
    </div>
  );
};

/**
 * 数据配置面板
 */
const DataConfigPanel = ({ config, onConfigChange, dataBinding }) => {
  const dataSourceTypes = [
    { value: DATA_SOURCE_TYPES.STATIC, label: '静态数据' },
    { value: DATA_SOURCE_TYPES.API, label: 'API接口' },
    { value: DATA_SOURCE_TYPES.WEBSOCKET, label: 'WebSocket' },
    { value: DATA_SOURCE_TYPES.DATABASE, label: '数据库' },
    { value: DATA_SOURCE_TYPES.FILE, label: '文件上传' }
  ];

  const dataFormats = [
    { value: DATA_FORMATS.JSON, label: 'JSON' },
    { value: DATA_FORMATS.CSV, label: 'CSV' },
    { value: DATA_FORMATS.ARRAY, label: '数组' },
    { value: DATA_FORMATS.OBJECT, label: '对象' }
  ];

  return (
    <div className="config-panel">
      <div className="config-field">
        <label className="config-field__label">数据源类型</label>
        <select 
          className="config-field__input"
          value={config.dataSource}
          onChange={(e) => onConfigChange({ dataSource: e.target.value })}
        >
          {dataSourceTypes.map(type => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      <div className="config-field">
        <label className="config-field__label">数据格式</label>
        <select 
          className="config-field__input"
          value={config.dataFormat}
          onChange={(e) => onConfigChange({ dataFormat: e.target.value })}
        >
          {dataFormats.map(format => (
            <option key={format.value} value={format.value}>
              {format.label}
            </option>
          ))}
        </select>
      </div>

      {/* 数据源特定配置 */}
      {config.dataSource === DATA_SOURCE_TYPES.STATIC && (
        <div className="config-field">
          <label className="config-field__label">静态数据</label>
          <textarea 
            className="config-field__input config-field__input--textarea"
            value={JSON.stringify(config.sourceConfig.data || [], null, 2)}
            onChange={(e) => {
              try {
                const data = JSON.parse(e.target.value);
                onConfigChange({ sourceConfig: { data } });
              } catch (error) {
                // 解析错误时保持原值
                console.error('JSON解析错误:', error);
              }
            }}
            placeholder="请输入JSON格式的数据"
            rows={8}
          />
        </div>
      )}

      {config.dataSource === DATA_SOURCE_TYPES.API && (
        <>
          <div className="config-field">
            <label className="config-field__label">API地址</label>
            <input 
              type="url"
              className="config-field__input"
              value={config.sourceConfig.url || ''}
              onChange={(e) => onConfigChange({ 
                sourceConfig: { ...config.sourceConfig, url: e.target.value }
              })}
              placeholder="https://api.example.com/data"
            />
          </div>

          <div className="config-field">
            <label className="config-field__label">请求方法</label>
            <select 
              className="config-field__input"
              value={config.sourceConfig.method || 'GET'}
              onChange={(e) => onConfigChange({ 
                sourceConfig: { ...config.sourceConfig, method: e.target.value }
              })}
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
        </>
      )}

      <div className="config-row">
        <div className="config-field">
          <label className="config-field__label">自动刷新间隔(秒)</label>
          <input 
            type="number"
            className="config-field__input"
            value={config.refreshInterval / 1000 || 0}
            onChange={(e) => onConfigChange({ 
              refreshInterval: parseInt(e.target.value) * 1000 || 0
            })}
            min={0}
            placeholder="0表示不自动刷新"
          />
        </div>

        <div className="config-field">
          <label className="config-field__label">
            <input 
              type="checkbox"
              checked={config.cacheEnabled}
              onChange={(e) => onConfigChange({ cacheEnabled: e.target.checked })}
            />
            启用缓存
          </label>
        </div>
      </div>

      <div className="config-field">
        <button 
          className="config-field__button"
          onClick={dataBinding.refreshData}
          disabled={dataBinding.isLoading}
        >
          {dataBinding.isLoading ? '加载中...' : '刷新数据'}
        </button>
      </div>
    </div>
  );
};

/**
 * 样式配置面板
 */
const StyleConfigPanel = ({ config, onConfigChange }) => {
  const defaultColors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'];

  return (
    <div className="config-panel">
      <div className="config-field">
        <label className="config-field__label">颜色方案</label>
        <div className="color-palette">
          {(config.colors || defaultColors).map((color, index) => (
            <div key={index} className="color-palette__item">
              <input 
                type="color"
                value={color}
                onChange={(e) => {
                  const newColors = [...(config.colors || defaultColors)];
                  newColors[index] = e.target.value;
                  onConfigChange({ colors: newColors });
                }}
              />
              <span>{color}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="config-row">
        <div className="config-field">
          <label className="config-field__label">
            <input 
              type="checkbox"
              checked={config.animation}
              onChange={(e) => onConfigChange({ animation: e.target.checked })}
            />
            启用动画
          </label>
        </div>

        <div className="config-field">
          <label className="config-field__label">
            <input 
              type="checkbox"
              checked={config.interactive}
              onChange={(e) => onConfigChange({ interactive: e.target.checked })}
            />
            交互式图表
          </label>
        </div>

        <div className="config-field">
          <label className="config-field__label">
            <input 
              type="checkbox"
              checked={config.responsive}
              onChange={(e) => onConfigChange({ responsive: e.target.checked })}
            />
            响应式布局
          </label>
        </div>
      </div>

      <div className="config-field">
        <label className="config-field__label">边距配置</label>
        <div className="margin-config">
          {['top', 'right', 'bottom', 'left'].map(position => (
            <div key={position} className="margin-config__item">
              <label>{position}</label>
              <input 
                type="number"
                value={config.margin?.[position] || 20}
                onChange={(e) => onConfigChange({
                  margin: { 
                    ...config.margin, 
                    [position]: parseInt(e.target.value) || 0 
                  }
                })}
                min={0}
                max={100}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * 高级配置面板
 */
const AdvancedConfigPanel = ({ config, chartType, onConfigChange }) => {
  // 根据图表类型显示不同的高级配置选项
  const renderChartSpecificConfig = () => {
    switch (chartType) {
      case 'bar':
        return (
          <>
            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.horizontal || false}
                  onChange={(e) => onConfigChange({ horizontal: e.target.checked })}
                />
                横向柱状图
              </label>
            </div>

            <div className="config-field">
              <label className="config-field__label">柱状图间距</label>
              <input 
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.barSpacing || 0.2}
                onChange={(e) => onConfigChange({ barSpacing: parseFloat(e.target.value) })}
              />
              <span>{((config.barSpacing || 0.2) * 100).toFixed(0)}%</span>
            </div>
          </>
        );

      case 'pie':
        return (
          <>
            <div className="config-field">
              <label className="config-field__label">内半径(环形图)</label>
              <input 
                type="range"
                min="0"
                max="100"
                value={config.innerRadius || 0}
                onChange={(e) => onConfigChange({ innerRadius: parseInt(e.target.value) })}
              />
              <span>{config.innerRadius || 0}%</span>
            </div>

            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.showLabels !== false}
                  onChange={(e) => onConfigChange({ showLabels: e.target.checked })}
                />
                显示标签
              </label>
            </div>

            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.showPercentages || false}
                  onChange={(e) => onConfigChange({ showPercentages: e.target.checked })}
                />
                显示百分比
              </label>
            </div>
          </>
        );

      case 'line':
        return (
          <>
            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.showPoints !== false}
                  onChange={(e) => onConfigChange({ showPoints: e.target.checked })}
                />
                显示数据点
              </label>
            </div>

            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.smooth || false}
                  onChange={(e) => onConfigChange({ smooth: e.target.checked })}
                />
                平滑曲线
              </label>
            </div>

            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.area || false}
                  onChange={(e) => onConfigChange({ area: e.target.checked })}
                />
                面积图
              </label>
            </div>
          </>
        );

      case 'scatter':
        return (
          <>
            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.showRegressionLine || false}
                  onChange={(e) => onConfigChange({ showRegressionLine: e.target.checked })}
                />
                显示回归线
              </label>
            </div>
          </>
        );

      case 'radar':
        return (
          <>
            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.showGrid !== false}
                  onChange={(e) => onConfigChange({ showGrid: e.target.checked })}
                />
                显示网格
              </label>
            </div>

            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.showPoints !== false}
                  onChange={(e) => onConfigChange({ showPoints: e.target.checked })}
                />
                显示数据点
              </label>
            </div>
          </>
        );

      case 'gauge':
        return (
          <>
            <div className="config-field">
              <label className="config-field__label">刻度数量</label>
              <input 
                type="number"
                min="3"
                max="20"
                value={config.segments || 5}
                onChange={(e) => onConfigChange({ segments: parseInt(e.target.value) || 5 })}
              />
            </div>

            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.showValue !== false}
                  onChange={(e) => onConfigChange({ showValue: e.target.checked })}
                />
                显示数值
              </label>
            </div>

            <div className="config-field">
              <label className="config-field__label">
                <input 
                  type="checkbox"
                  checked={config.showNeedle !== false}
                  onChange={(e) => onConfigChange({ showNeedle: e.target.checked })}
                />
                显示指针
              </label>
            </div>
          </>
        );

      default:
        return (
          <div className="config-field">
            <p>当前图表类型无特殊配置选项</p>
          </div>
        );
    }
  };

  return (
    <div className="config-panel">
      {renderChartSpecificConfig()}

      <div className="config-field">
        <label className="config-field__label">自定义配置(JSON)</label>
        <textarea 
          className="config-field__input config-field__input--textarea"
          value={JSON.stringify(config, null, 2)}
          onChange={(e) => {
            try {
              const customConfig = JSON.parse(e.target.value);
              onConfigChange(customConfig);
            } catch (error) {
              console.error('JSON解析错误:', error);
            }
          }}
          placeholder="请输入自定义配置JSON"
          rows={6}
        />
      </div>
    </div>
  );
};

export default ChartConfigurator;