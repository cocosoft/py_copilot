/**
 * 性能监控工具
 * 
 * 用于监控应用性能指标
 */

/**
 * 性能指标配置
 */
const PERFORMANCE_CONFIG = {
  // 性能指标阈值（毫秒）
  thresholds: {
    FCP: 1800,    // First Contentful Paint
    LCP: 2500,    // Largest Contentful Paint
    FID: 100,     // First Input Delay
    CLS: 0.1,     // Cumulative Layout Shift
    TTFB: 600,    // Time to First Byte
  },
  
  // 采样率（0-1）
  sampleRate: 1.0,
  
  // 是否启用调试日志
  debug: process.env.NODE_ENV === 'development',
};

/**
 * 日志级别
 */
const LogLevel = {
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error',
};

/**
 * 性能日志类
 */
class PerformanceLogger {
  constructor() {
    this.metrics = [];
    this.observers = [];
    this.isMonitoring = false;
  }

  /**
   * 开始性能监控
   */
  start() {
    if (this.isMonitoring) return;
    this.isMonitoring = true;

    // 监控 Web Vitals
    this.observeWebVitals();
    
    // 监控资源加载
    this.observeResourceTiming();
    
    // 监控长任务
    this.observeLongTasks();
    
    // 监控内存使用
    this.observeMemoryUsage();

    this.log(LogLevel.INFO, '性能监控已启动');
  }

  /**
   * 停止性能监控
   */
  stop() {
    this.isMonitoring = false;
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.log(LogLevel.INFO, '性能监控已停止');
  }

  /**
   * 监控 Web Vitals 指标
   */
  observeWebVitals() {
    // First Contentful Paint (FCP)
    if ('PerformanceObserver' in window) {
      try {
        const fcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach(entry => {
            if (entry.name === 'first-contentful-paint') {
              this.recordMetric('FCP', entry.startTime);
            }
          });
        });
        fcpObserver.observe({ entryTypes: ['paint'] });
        this.observers.push(fcpObserver);
      } catch (e) {
        this.log(LogLevel.WARN, 'FCP 监控不支持', e);
      }
    }

    // Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.recordMetric('LCP', lastEntry.startTime);
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);
      } catch (e) {
        this.log(LogLevel.WARN, 'LCP 监控不支持', e);
      }
    }

    // First Input Delay (FID)
    if ('PerformanceObserver' in window) {
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach(entry => {
            this.recordMetric('FID', entry.processingStart - entry.startTime);
          });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.push(fidObserver);
      } catch (e) {
        this.log(LogLevel.WARN, 'FID 监控不支持', e);
      }
    }

    // Cumulative Layout Shift (CLS)
    if ('PerformanceObserver' in window) {
      try {
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach(entry => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
          this.recordMetric('CLS', clsValue);
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(clsObserver);
      } catch (e) {
        this.log(LogLevel.WARN, 'CLS 监控不支持', e);
      }
    }
  }

  /**
   * 监控资源加载性能
   */
  observeResourceTiming() {
    if ('PerformanceObserver' in window) {
      try {
        const resourceObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach(entry => {
            // 只监控慢资源（>1s）
            if (entry.duration > 1000) {
              this.recordMetric('SlowResource', {
                name: entry.name,
                duration: entry.duration,
                type: entry.initiatorType,
              });
            }
          });
        });
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.push(resourceObserver);
      } catch (e) {
        this.log(LogLevel.WARN, '资源监控不支持', e);
      }
    }
  }

  /**
   * 监控长任务
   */
  observeLongTasks() {
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach(entry => {
            this.recordMetric('LongTask', {
              duration: entry.duration,
              startTime: entry.startTime,
            });
            this.log(LogLevel.WARN, '检测到长任务', {
              duration: entry.duration,
              startTime: entry.startTime,
            });
          });
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (e) {
        this.log(LogLevel.WARN, '长任务监控不支持', e);
      }
    }
  }

  /**
   * 监控内存使用
   */
  observeMemoryUsage() {
    if (performance.memory) {
      setInterval(() => {
        const memory = performance.memory;
        this.recordMetric('Memory', {
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit,
        });
      }, 30000); // 每30秒记录一次
    }
  }

  /**
   * 记录性能指标
   */
  recordMetric(name, value) {
    const metric = {
      name,
      value,
      timestamp: Date.now(),
      url: window.location.href,
    };

    this.metrics.push(metric);

    // 检查是否超过阈值
    const threshold = PERFORMANCE_CONFIG.thresholds[name];
    if (threshold && typeof value === 'number' && value > threshold) {
      this.log(LogLevel.WARN, `性能指标 ${name} 超过阈值`, {
        value,
        threshold,
      });
    }

    // 调试日志
    if (PERFORMANCE_CONFIG.debug) {
      this.log(LogLevel.DEBUG, `性能指标: ${name}`, metric);
    }

    // 触发回调
    this.notifyObservers(metric);
  }

  /**
   * 测量函数执行时间
   */
  measureFunction(fn, name) {
    return (...args) => {
      const start = performance.now();
      const result = fn(...args);
      
      // 处理异步函数
      if (result instanceof Promise) {
        return result.finally(() => {
          const duration = performance.now() - start;
          this.recordMetric(`Function_${name}`, duration);
        });
      }
      
      const duration = performance.now() - start;
      this.recordMetric(`Function_${name}`, duration);
      return result;
    };
  }

  /**
   * 测量组件渲染时间
   */
  measureRender(componentName) {
    return {
      start: () => {
        this[`_renderStart_${componentName}`] = performance.now();
      },
      end: () => {
        const start = this[`_renderStart_${componentName}`];
        if (start) {
          const duration = performance.now() - start;
          this.recordMetric(`Render_${componentName}`, duration);
          delete this[`_renderStart_${componentName}`];
        }
      },
    };
  }

  /**
   * 添加观察者回调
   */
  addObserver(callback) {
    this.observers.push(callback);
  }

  /**
   * 通知观察者
   */
  notifyObservers(metric) {
    this.observers.forEach(callback => {
      if (typeof callback === 'function') {
        try {
          callback(metric);
        } catch (e) {
          this.log(LogLevel.ERROR, '观察者回调错误', e);
        }
      }
    });
  }

  /**
   * 获取所有指标
   */
  getMetrics() {
    return [...this.metrics];
  }

  /**
   * 获取指标统计
   */
  getStats() {
    const stats = {};
    
    this.metrics.forEach(metric => {
      if (!stats[metric.name]) {
        stats[metric.name] = {
          count: 0,
          total: 0,
          min: Infinity,
          max: 0,
          avg: 0,
        };
      }
      
      const s = stats[metric.name];
      s.count++;
      
      if (typeof metric.value === 'number') {
        s.total += metric.value;
        s.min = Math.min(s.min, metric.value);
        s.max = Math.max(s.max, metric.value);
        s.avg = s.total / s.count;
      }
    });
    
    return stats;
  }

  /**
   * 清除指标
   */
  clear() {
    this.metrics = [];
  }

  /**
   * 记录日志
   */
  log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data,
    };

    // 控制台输出
    if (PERFORMANCE_CONFIG.debug || level === LogLevel.ERROR || level === LogLevel.WARN) {
      const consoleMethod = level === LogLevel.ERROR ? 'error' : 
                           level === LogLevel.WARN ? 'warn' : 'log';
      console[consoleMethod](`[Performance] ${message}`, data || '');
    }

    return logEntry;
  }
}

// 创建单例实例
const performanceLogger = new PerformanceLogger();

/**
 * React Hook: 使用性能监控
 */
export const usePerformance = () => {
  return {
    measureRender: (componentName) => performanceLogger.measureRender(componentName),
    recordMetric: (name, value) => performanceLogger.recordMetric(name, value),
    getMetrics: () => performanceLogger.getMetrics(),
    getStats: () => performanceLogger.getStats(),
  };
};

/**
 * React Hook: 测量组件渲染性能
 */
export const useRenderPerformance = (componentName) => {
  React.useEffect(() => {
    const measure = performanceLogger.measureRender(componentName);
    measure.start();
    
    return () => {
      measure.end();
    };
  }, [componentName]);
};

export default performanceLogger;
export { LogLevel, PERFORMANCE_CONFIG };
