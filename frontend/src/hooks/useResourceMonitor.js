/**
 * 资源监控 Hooks - FE-008 实时资源监控
 *
 * 提供资源监控相关的数据获取和操作功能
 *
 * @task FE-008
 * @phase 前端功能拓展
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import apiClient from '../services/apiClient';

/**
 * 使用实时资源指标
 *
 * @param {Object} options - 配置选项
 * @returns {Object} 资源指标数据和操作
 */
export const useResourceMetrics = (options = {}) => {
  const { refreshInterval = 5000, enabled = true } = options;
  const [metrics, setMetrics] = useState([]);
  const intervalRef = useRef(null);

  // 获取资源指标
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/monitoring/metrics');
      return response.data;
    } catch (error) {
      console.error('获取资源指标失败:', error);
      return null;
    }
  }, []);

  // 启动实时监控
  const startMonitoring = useCallback(() => {
    if (intervalRef.current) return;

    intervalRef.current = setInterval(async () => {
      const data = await fetchMetrics();
      if (data) {
        setMetrics((prev) => {
          const newMetrics = [...prev, data];
          // 保留最近100个数据点
          if (newMetrics.length > 100) {
            return newMetrics.slice(-100);
          }
          return newMetrics;
        });
      }
    }, refreshInterval);
  }, [fetchMetrics, refreshInterval]);

  // 停止实时监控
  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // 手动刷新
  const refresh = useCallback(async () => {
    const data = await fetchMetrics();
    if (data) {
      setMetrics((prev) => [...prev, data]);
    }
    return data;
  }, [fetchMetrics]);

  // 清理
  useEffect(() => {
    if (enabled) {
      startMonitoring();
    }

    return () => {
      stopMonitoring();
    };
  }, [enabled, startMonitoring, stopMonitoring]);

  // 计算当前指标
  const currentMetrics = useMemo(() => {
    return metrics.length > 0 ? metrics[metrics.length - 1] : null;
  }, [metrics]);

  // 计算趋势
  const trends = useMemo(() => {
    if (metrics.length < 2) return null;

    const current = metrics[metrics.length - 1];
    const previous = metrics[metrics.length - 2];

    return {
      cpu: current.cpu - previous.cpu,
      memory: current.memory - previous.memory,
      disk: current.disk - previous.disk,
      queue: current.queueLength - previous.queueLength,
    };
  }, [metrics]);

  return useMemo(
    () => ({
      metrics,
      currentMetrics,
      trends,
      startMonitoring,
      stopMonitoring,
      refresh,
      isMonitoring: !!intervalRef.current,
    }),
    [metrics, currentMetrics, trends, startMonitoring, stopMonitoring, refresh]
  );
};

/**
 * 使用告警管理
 *
 * @returns {Object} 告警状态和操作
 */
export const useAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [dismissedIds, setDismissedIds] = useState(new Set());

  // 获取告警
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/monitoring/alerts');
      return response.data;
    } catch (error) {
      console.error('获取告警失败:', error);
      return [];
    }
  }, []);

  // 添加告警
  const addAlert = useCallback((alert) => {
    setAlerts((prev) => [
      {
        id: Date.now().toString(),
        timestamp: Date.now(),
        ...alert,
      },
      ...prev.slice(0, 49), // 最多保留50条
    ]);
  }, []);

  // 关闭告警
  const dismissAlert = useCallback((alertId) => {
    setDismissedIds((prev) => new Set([...prev, alertId]));
  }, []);

  // 清除所有告警
  const clearAlerts = useCallback(() => {
    setAlerts([]);
    setDismissedIds(new Set());
  }, []);

  // 可见告警
  const visibleAlerts = useMemo(() => {
    return alerts.filter((alert) => !dismissedIds.has(alert.id));
  }, [alerts, dismissedIds]);

  // 告警统计
  const alertStats = useMemo(() => {
    const stats = { critical: 0, warning: 0, info: 0 };
    visibleAlerts.forEach((alert) => {
      stats[alert.severity] = (stats[alert.severity] || 0) + 1;
    });
    return stats;
  }, [visibleAlerts]);

  return useMemo(
    () => ({
      alerts,
      visibleAlerts,
      dismissedIds,
      alertStats,
      fetchAlerts,
      addAlert,
      dismissAlert,
      clearAlerts,
    }),
    [alerts, visibleAlerts, dismissedIds, alertStats, fetchAlerts, addAlert, dismissAlert, clearAlerts]
  );
};

/**
 * 使用阈值配置
 *
 * @param {Object} initialThresholds - 初始阈值
 * @returns {Object} 阈值状态和操作
 */
export const useThresholds = (initialThresholds = {}) => {
  const [thresholds, setThresholds] = useState({
    cpu: 80,
    memory: 85,
    disk: 90,
    queue: 50,
    ...initialThresholds,
  });

  // 更新阈值
  const updateThreshold = useCallback((key, value) => {
    setThresholds((prev) => ({
      ...prev,
      [key]: Number(value),
    }));
  }, []);

  // 批量更新阈值
  const updateThresholds = useCallback((updates) => {
    setThresholds((prev) => ({
      ...prev,
      ...updates,
    }));
  }, []);

  // 重置阈值
  const resetThresholds = useCallback(() => {
    setThresholds({
      cpu: 80,
      memory: 85,
      disk: 90,
      queue: 50,
    });
  }, []);

  // 检查是否超过阈值
  const checkThreshold = useCallback(
    (metric, value) => {
      const threshold = thresholds[metric];
      if (!threshold) return { exceeded: false };

      return {
        exceeded: value > threshold,
        threshold,
        difference: value - threshold,
      };
    },
    [thresholds]
  );

  return useMemo(
    () => ({
      thresholds,
      updateThreshold,
      updateThresholds,
      resetThresholds,
      checkThreshold,
    }),
    [thresholds, updateThreshold, updateThresholds, resetThresholds, checkThreshold]
  );
};

/**
 * 使用历史趋势
 *
 * @param {string} metric - 指标名称
 * @param {Object} options - 配置选项
 * @returns {Object} 历史数据
 */
export const useMetricHistory = (metric, options = {}) => {
  const { timeRange = '1h', enabled = true } = options;

  const { data, isLoading, error } = useQuery({
    queryKey: ['monitoring', 'history', metric, timeRange],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/monitoring/history', {
        params: { metric, timeRange },
      });
      return response.data;
    },
    enabled: !!metric && enabled,
    refetchInterval: 60000, // 每分钟刷新
  });

  // 计算统计信息
  const stats = useMemo(() => {
    if (!data || data.length === 0) return null;

    const values = data.map((d) => d.value);
    const sum = values.reduce((a, b) => a + b, 0);
    const avg = sum / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);

    return {
      avg: avg.toFixed(2),
      min: min.toFixed(2),
      max: max.toFixed(2),
      count: values.length,
    };
  }, [data]);

  return useMemo(
    () => ({
      data: data || [],
      stats,
      isLoading,
      error,
    }),
    [data, stats, isLoading, error]
  );
};

/**
 * 使用系统状态
 *
 * @returns {Object} 系统状态
 */
export const useSystemStatus = () => {
  const [status, setStatus] = useState('unknown'); // unknown, healthy, warning, critical
  const [uptime, setUptime] = useState(0);

  const { currentMetrics } = useResourceMetrics();
  const { thresholds } = useThresholds();

  // 计算系统状态
  useEffect(() => {
    if (!currentMetrics) {
      setStatus('unknown');
      return;
    }

    const exceededThresholds = [];

    if (currentMetrics.cpu > thresholds.cpu) {
      exceededThresholds.push('cpu');
    }
    if (currentMetrics.memory > thresholds.memory) {
      exceededThresholds.push('memory');
    }
    if (currentMetrics.disk > thresholds.disk) {
      exceededThresholds.push('disk');
    }

    if (exceededThresholds.length >= 2) {
      setStatus('critical');
    } else if (exceededThresholds.length === 1) {
      setStatus('warning');
    } else {
      setStatus('healthy');
    }
  }, [currentMetrics, thresholds]);

  // 模拟系统运行时间
  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      setUptime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return useMemo(
    () => ({
      status,
      uptime,
      isHealthy: status === 'healthy',
      isWarning: status === 'warning',
      isCritical: status === 'critical',
    }),
    [status, uptime]
  );
};

/**
 * 使用数据导出
 *
 * @returns {Object} 导出功能
 */
export const useExportData = () => {
  /**
   * 导出为JSON
   */
  const exportAsJSON = useCallback((data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `monitoring-data-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, []);

  /**
   * 导出为CSV
   */
  const exportAsCSV = useCallback((data, filename) => {
    if (!data || data.length === 0) return;

    const headers = Object.keys(data[0]);
    const rows = data.map((row) => headers.map((h) => row[h]).join(','));
    const csv = [headers.join(','), ...rows].join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `monitoring-data-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, []);

  return useMemo(
    () => ({
      exportAsJSON,
      exportAsCSV,
    }),
    [exportAsJSON, exportAsCSV]
  );
};

/**
 * 使用完整的资源监控
 *
 * @returns {Object} 完整的资源监控状态
 */
export const useResourceMonitor = () => {
  const metrics = useResourceMetrics();
  const alerts = useAlerts();
  const thresholds = useThresholds();
  const systemStatus = useSystemStatus();
  const exportData = useExportData();

  // 检查阈值并生成告警
  useEffect(() => {
    if (!metrics.currentMetrics) return;

    const { currentMetrics } = metrics;

    // 检查CPU
    const cpuCheck = thresholds.checkThreshold('cpu', currentMetrics.cpu);
    if (cpuCheck.exceeded && Math.random() > 0.8) {
      alerts.addAlert({
        type: 'cpu',
        message: `CPU使用率 ${currentMetrics.cpu.toFixed(1)}% 超过阈值 ${cpuCheck.threshold}%`,
        severity: 'warning',
      });
    }

    // 检查内存
    const memoryCheck = thresholds.checkThreshold('memory', currentMetrics.memory);
    if (memoryCheck.exceeded && Math.random() > 0.8) {
      alerts.addAlert({
        type: 'memory',
        message: `内存使用率 ${currentMetrics.memory.toFixed(1)}% 超过阈值 ${memoryCheck.threshold}%`,
        severity: 'critical',
      });
    }

    // 检查磁盘
    const diskCheck = thresholds.checkThreshold('disk', currentMetrics.disk);
    if (diskCheck.exceeded && Math.random() > 0.8) {
      alerts.addAlert({
        type: 'disk',
        message: `磁盘使用率 ${currentMetrics.disk.toFixed(1)}% 超过阈值 ${diskCheck.threshold}%`,
        severity: 'warning',
      });
    }

    // 检查队列
    const queueCheck = thresholds.checkThreshold('queue', currentMetrics.queueLength);
    if (queueCheck.exceeded && Math.random() > 0.8) {
      alerts.addAlert({
        type: 'queue',
        message: `队列长度 ${currentMetrics.queueLength} 超过阈值 ${queueCheck.threshold}`,
        severity: 'warning',
      });
    }
  }, [metrics.currentMetrics, thresholds, alerts]);

  return useMemo(
    () => ({
      // 指标
      metrics: metrics.metrics,
      currentMetrics: metrics.currentMetrics,
      trends: metrics.trends,
      isMonitoring: metrics.isMonitoring,

      // 告警
      alerts: alerts.alerts,
      visibleAlerts: alerts.visibleAlerts,
      alertStats: alerts.alertStats,

      // 阈值
      thresholds: thresholds.thresholds,

      // 系统状态
      systemStatus,

      // 操作
      startMonitoring: metrics.startMonitoring,
      stopMonitoring: metrics.stopMonitoring,
      refresh: metrics.refresh,
      addAlert: alerts.addAlert,
      dismissAlert: alerts.dismissAlert,
      clearAlerts: alerts.clearAlerts,
      updateThreshold: thresholds.updateThreshold,
      exportAsJSON: exportData.exportAsJSON,
      exportAsCSV: exportData.exportAsCSV,
    }),
    [
      metrics,
      alerts,
      thresholds,
      systemStatus,
      exportData,
    ]
  );
};

// ==================== 工具函数 ====================

/**
 * 格式化字节大小
 *
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的字符串
 */
export const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 格式化持续时间
 *
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的字符串
 */
export const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`;
  }
  if (minutes > 0) {
    return `${minutes}分钟 ${secs}秒`;
  }
  return `${secs}秒`;
};

/**
 * 格式化时间戳
 *
 * @param {number} timestamp - 时间戳
 * @returns {string} 格式化后的字符串
 */
export const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/**
 * 计算平均值
 *
 * @param {Array} data - 数据数组
 * @param {string} key - 字段名
 * @returns {number} 平均值
 */
export const calculateAverage = (data, key) => {
  if (!data || data.length === 0) return 0;
  const sum = data.reduce((acc, item) => acc + (item[key] || 0), 0);
  return sum / data.length;
};

/**
 * 计算峰值
 *
 * @param {Array} data - 数据数组
 * @param {string} key - 字段名
 * @returns {number} 峰值
 */
export const calculatePeak = (data, key) => {
  if (!data || data.length === 0) return 0;
  return Math.max(...data.map((item) => item[key] || 0));
};
