/**
 * 实时资源监控组件 - FE-008 实时资源监控
 *
 * 提供CPU/内存监控、队列长度监控、告警通知、历史趋势功能
 *
 * @task FE-008
 * @phase 前端功能拓展
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getProcessingQueueStatus, getKnowledgeStats } from '../../../utils/api/knowledgeApi';
import './ResourceMonitor.css';

/**
 * 生成模拟资源数据
 */
const generateMockMetrics = (count = 60) => {
  const data = [];
  const now = Date.now();

  for (let i = count - 1; i >= 0; i--) {
    data.push({
      timestamp: now - i * 1000,
      cpu: 30 + Math.random() * 40 + Math.sin(i * 0.1) * 10,
      memory: 50 + Math.random() * 30 + Math.cos(i * 0.15) * 10,
      disk: 60 + Math.random() * 10,
      queueLength: Math.floor(Math.random() * 20) + 5,
      activeTasks: Math.floor(Math.random() * 10) + 1,
    });
  }

  return data;
};

/**
 * 生成模拟告警
 */
const generateMockAlerts = () => {
  return [
    {
      id: '1',
      type: 'cpu',
      message: 'CPU使用率超过80%',
      severity: 'warning',
      timestamp: Date.now() - 300000,
    },
    {
      id: '2',
      type: 'memory',
      message: '内存使用率超过85%',
      severity: 'warning',
      timestamp: Date.now() - 600000,
    },
    {
      id: '3',
      type: 'queue',
      message: '队列长度超过50',
      severity: 'info',
      timestamp: Date.now() - 900000,
    },
  ];
};

/**
 * 指标卡片组件
 */
const MetricCard = ({ title, value, unit, trend, color, icon }) => {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        <span className="metric-icon">{icon}</span>
      </div>
      <div className="metric-value" style={{ color }}>
        {Math.round(value)}
        <span className="metric-unit">{unit}</span>
      </div>
      <div className="metric-trend">
        {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend).toFixed(1)}%
      </div>
    </div>
  );
};

/**
 * 趋势图表组件（简化版）
 */
const TrendChart = ({ data, dataKey, color, title }) => {
  const maxValue = Math.max(...data.map(d => d[dataKey]));
  const minValue = Math.min(...data.map(d => d[dataKey]));
  const range = maxValue - minValue || 1;

  return (
    <div className="trend-chart">
      <h4 className="chart-title">{title}</h4>
      <div className="chart-container">
        <svg viewBox="0 0 300 100" className="trend-svg">
          {/* 网格线 */}
          {[0, 25, 50, 75, 100].map(y => (
            <line
              key={y}
              x1="0"
              y1={y}
              x2="300"
              y2={y}
              stroke="#e8e8e8"
              strokeWidth="0.5"
            />
          ))}
          {/* 数据线 */}
          <polyline
            fill="none"
            stroke={color}
            strokeWidth="2"
            points={data.map((d, i) => {
              const x = (i / (data.length - 1)) * 300;
              const y = 100 - ((d[dataKey] - minValue) / range) * 100;
              return `${x},${y}`;
            }).join(' ')}
          />
          {/* 填充区域 */}
          <polygon
            fill={color}
            fillOpacity="0.1"
            points={`
              0,100
              ${data.map((d, i) => {
                const x = (i / (data.length - 1)) * 300;
                const y = 100 - ((d[dataKey] - minValue) / range) * 100;
                return `${x},${y}`;
              }).join(' ')}
              300,100
            `}
          />
        </svg>
      </div>
    </div>
  );
};

/**
 * 告警列表组件
 */
const AlertList = ({ alerts, onDismiss }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#ff4d4f';
      case 'warning': return '#faad14';
      case 'info': return '#1890ff';
      default: return '#8c8c8c';
    }
  };

  const formatTime = (timestamp) => {
    const diff = Date.now() - timestamp;
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    return `${Math.floor(diff / 3600000)}小时前`;
  };

  return (
    <div className="alert-list">
      <h4 className="alert-title">告警通知</h4>
      {alerts.length === 0 ? (
        <div className="alert-empty">暂无告警</div>
      ) : (
        alerts.map(alert => (
          <div
            key={alert.id}
            className={`alert-item alert-${alert.severity}`}
            style={{ borderLeftColor: getSeverityColor(alert.severity) }}
          >
            <div className="alert-content">
              <span className="alert-message">{alert.message}</span>
              <span className="alert-time">{formatTime(alert.timestamp)}</span>
            </div>
            <button
              className="alert-dismiss"
              onClick={() => onDismiss(alert.id)}
            >
              ×
            </button>
          </div>
        ))
      )}
    </div>
  );
};

/**
 * 资源监控面板主组件
 */
const ResourceMonitor = ({
  autoUpdate = true,
  updateInterval = 5000,
  onAlert,
  className = '',
  initialMetrics = null,
  initialAlerts = null
}) => {
  // 使用外部传入的数据或空数组
  const [metrics, setMetrics] = useState(initialMetrics || []);
  const [alerts, setAlerts] = useState(initialAlerts || []);
  const [isRunning, setIsRunning] = useState(autoUpdate);
  const [showAlerts, setShowAlerts] = useState(true);

  // 计算当前指标
  const currentMetrics = useMemo(() => {
    const latest = metrics[metrics.length - 1];
    const previous = metrics[metrics.length - 2];
    
    return {
      cpu: {
        value: latest?.cpu || 0,
        trend: previous ? ((latest.cpu - previous.cpu) / previous.cpu) * 100 : 0
      },
      memory: {
        value: latest?.memory || 0,
        trend: previous ? ((latest.memory - previous.memory) / previous.memory) * 100 : 0
      },
      disk: {
        value: latest?.disk || 0,
        trend: 0
      },
      queue: {
        value: latest?.queueLength || 0,
        trend: previous ? ((latest.queueLength - previous.queueLength) / Math.max(previous.queueLength, 1)) * 100 : 0
      }
    };
  }, [metrics]);

  // 从API获取真实数据
  const fetchMetrics = useCallback(async () => {
    try {
      const [queueStatus, stats] = await Promise.all([
        getProcessingQueueStatus(),
        getKnowledgeStats()
      ]);

      const newMetric = {
        timestamp: Date.now(),
        cpu: queueStatus?.system_load?.cpu || 0,
        memory: queueStatus?.system_load?.memory || 0,
        disk: queueStatus?.system_load?.disk || 0,
        queueLength: queueStatus?.pending_count || 0,
        activeTasks: queueStatus?.processing_count || 0,
      };

      setMetrics(prev => {
        const updated = [...prev, newMetric];
        // 保持最多60个数据点
        if (updated.length > 60) {
          return updated.slice(updated.length - 60);
        }
        return updated;
      });

      // 更新告警
      const newAlerts = [];
      if (newMetric.cpu > 80) {
        newAlerts.push({
          id: `cpu-${Date.now()}`,
          type: 'cpu',
          message: `CPU使用率超过80% (当前: ${newMetric.cpu.toFixed(1)}%)`,
          severity: 'warning',
          timestamp: Date.now(),
        });
      }
      if (newMetric.memory > 85) {
        newAlerts.push({
          id: `memory-${Date.now()}`,
          type: 'memory',
          message: `内存使用率超过85% (当前: ${newMetric.memory.toFixed(1)}%)`,
          severity: 'warning',
          timestamp: Date.now(),
        });
      }
      if (newMetric.queueLength > 50) {
        newAlerts.push({
          id: `queue-${Date.now()}`,
          type: 'queue',
          message: `处理队列堆积 (${newMetric.queueLength}个任务)`,
          severity: 'warning',
          timestamp: Date.now(),
        });
      }
      
      if (newAlerts.length > 0) {
        setAlerts(prev => [...newAlerts, ...prev].slice(0, 10));
      }
    } catch (error) {
      console.error('获取监控数据失败:', error);
    }
  }, []);

  // 自动更新
  useEffect(() => {
    if (!isRunning) return;
    
    // 立即获取一次数据
    fetchMetrics();
    
    const interval = setInterval(fetchMetrics, updateInterval);
    return () => clearInterval(interval);
  }, [isRunning, updateInterval, fetchMetrics]);

  // 处理告警
  const handleDismissAlert = useCallback((alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  }, []);

  // 清空所有告警
  const handleClearAllAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  return (
    <div className={`resource-monitor ${className}`}>
      {/* 头部 */}
      <div className="monitor-header">
        <h3>资源监控</h3>
        <div className="header-actions">
          <button
            className={`btn-toggle ${isRunning ? 'active' : ''}`}
            onClick={() => setIsRunning(!isRunning)}
          >
            {isRunning ? '暂停' : '开始'}
          </button>
          <button
            className={`btn-toggle ${showAlerts ? 'active' : ''}`}
            onClick={() => setShowAlerts(!showAlerts)}
          >
            告警
          </button>
          <button className="btn-refresh" onClick={fetchMetrics}>
            刷新
          </button>
        </div>
      </div>

      {/* 指标卡片 */}
      <div className="metrics-grid">
        <MetricCard
          title="CPU 使用率"
          value={currentMetrics.cpu.value}
          unit="%"
          trend={currentMetrics.cpu.trend}
          color="#1890ff"
          icon="🖥️"
        />
        <MetricCard
          title="内存使用率"
          value={currentMetrics.memory.value}
          unit="%"
          trend={currentMetrics.memory.trend}
          color="#52c41a"
          icon="💾"
        />
        <MetricCard
          title="磁盘使用率"
          value={currentMetrics.disk.value}
          unit="%"
          trend={currentMetrics.disk.trend}
          color="#faad14"
          icon="💿"
        />
        <MetricCard
          title="队列长度"
          value={currentMetrics.queue.value}
          unit=""
          trend={currentMetrics.queue.trend}
          color="#722ed1"
          icon="📋"
        />
      </div>

      {/* 图表区域 */}
      <div className="charts-section">
        <TrendChart
          data={metrics}
          dataKey="cpu"
          color="#1890ff"
          title="CPU 趋势"
        />
        <TrendChart
          data={metrics}
          dataKey="memory"
          color="#52c41a"
          title="内存趋势"
        />
      </div>

      {/* 告警区域 */}
      {showAlerts && (
        <div className="alerts-section">
          <div className="alerts-header">
            <h4>告警通知 ({alerts.length})</h4>
            {alerts.length > 0 && (
              <button className="btn-clear" onClick={handleClearAllAlerts}>
                清空全部
              </button>
            )}
          </div>
          <AlertList alerts={alerts} onDismiss={handleDismissAlert} />
        </div>
      )}
    </div>
  );
};

export default ResourceMonitor;
