/**
 * 性能监控工具
 *
 * 功能：监控知识图谱组件的性能指标
 */

/**
 * 性能监控类
 */
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      renderTimes: [],
      memoryUsage: [],
      apiCallTimes: [],
      userInteractions: []
    };
    this.isRecording = false;
  }

  /**
   * 开始记录性能数据
   */
  startRecording() {
    this.isRecording = true;
    this.metrics = {
      renderTimes: [],
      memoryUsage: [],
      apiCallTimes: [],
      userInteractions: []
    };

    // 开始内存监控
    this.startMemoryMonitoring();
  }

  /**
   * 停止记录性能数据
   */
  stopRecording() {
    this.isRecording = false;
    this.stopMemoryMonitoring();
    return this.getReport();
  }

  /**
   * 记录渲染时间
   * @param {string} componentName - 组件名称
   * @param {number} duration - 渲染耗时（毫秒）
   */
  recordRenderTime(componentName, duration) {
    if (!this.isRecording) return;

    this.metrics.renderTimes.push({
      component: componentName,
      duration: duration,
      timestamp: Date.now()
    });

    // 如果渲染时间超过阈值，输出警告
    if (duration > 100) {
      console.warn(`[性能警告] ${componentName} 渲染耗时 ${duration.toFixed(2)}ms，超过 100ms 阈值`);
    }
  }

  /**
   * 记录 API 调用时间
   * @param {string} apiName - API 名称
   * @param {number} duration - 调用耗时（毫秒）
   * @param {boolean} success - 是否成功
   */
  recordApiCall(apiName, duration, success = true) {
    if (!this.isRecording) return;

    this.metrics.apiCallTimes.push({
      api: apiName,
      duration: duration,
      success: success,
      timestamp: Date.now()
    });

    // 如果 API 调用时间超过阈值，输出警告
    if (duration > 1000) {
      console.warn(`[性能警告] API ${apiName} 调用耗时 ${duration.toFixed(2)}ms，超过 1000ms 阈值`);
    }
  }

  /**
   * 记录用户交互
   * @param {string} action - 交互动作
   * @param {number} responseTime - 响应时间（毫秒）
   */
  recordUserInteraction(action, responseTime) {
    if (!this.isRecording) return;

    this.metrics.userInteractions.push({
      action: action,
      responseTime: responseTime,
      timestamp: Date.now()
    });

    // 如果响应时间超过阈值，输出警告
    if (responseTime > 200) {
      console.warn(`[性能警告] 用户交互 ${action} 响应时间 ${responseTime.toFixed(2)}ms，超过 200ms 阈值`);
    }
  }

  /**
   * 开始内存监控
   */
  startMemoryMonitoring() {
    if (!performance.memory) {
      console.warn('[性能监控] 当前浏览器不支持内存监控');
      return;
    }

    this.memoryInterval = setInterval(() => {
      if (!this.isRecording) return;

      const memory = performance.memory;
      this.metrics.memoryUsage.push({
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit,
        timestamp: Date.now()
      });
    }, 5000); // 每5秒记录一次
  }

  /**
   * 停止内存监控
   */
  stopMemoryMonitoring() {
    if (this.memoryInterval) {
      clearInterval(this.memoryInterval);
      this.memoryInterval = null;
    }
  }

  /**
   * 获取性能报告
   * @returns {Object} 性能报告
   */
  getReport() {
    const report = {
      summary: {
        totalRenderCalls: this.metrics.renderTimes.length,
        totalApiCalls: this.metrics.apiCallTimes.length,
        totalUserInteractions: this.metrics.userInteractions.length,
        averageRenderTime: this.calculateAverage(this.metrics.renderTimes, 'duration'),
        averageApiCallTime: this.calculateAverage(this.metrics.apiCallTimes, 'duration'),
        averageInteractionTime: this.calculateAverage(this.metrics.userInteractions, 'responseTime'),
        maxMemoryUsage: this.calculateMaxMemoryUsage()
      },
      details: this.metrics
    };

    return report;
  }

  /**
   * 计算平均值
   * @param {Array} data - 数据数组
   * @param {string} field - 字段名
   * @returns {number} 平均值
   */
  calculateAverage(data, field) {
    if (data.length === 0) return 0;
    const sum = data.reduce((acc, item) => acc + item[field], 0);
    return sum / data.length;
  }

  /**
   * 计算最大内存使用量
   * @returns {number} 最大内存使用量（MB）
   */
  calculateMaxMemoryUsage() {
    if (this.metrics.memoryUsage.length === 0) return 0;
    const maxBytes = Math.max(...this.metrics.memoryUsage.map(m => m.usedJSHeapSize));
    return maxBytes / (1024 * 1024); // 转换为 MB
  }

  /**
   * 导出性能报告
   * @returns {string} JSON 格式的报告
   */
  exportReport() {
    const report = this.getReport();
    return JSON.stringify(report, null, 2);
  }

  /**
   * 打印性能报告到控制台
   */
  printReport() {
    const report = this.getReport();

    console.group('📊 性能监控报告');
    console.log('渲染统计:');
    console.log(`  - 总渲染次数: ${report.summary.totalRenderCalls}`);
    console.log(`  - 平均渲染时间: ${report.summary.averageRenderTime.toFixed(2)}ms`);

    console.log('API 调用统计:');
    console.log(`  - 总调用次数: ${report.summary.totalApiCalls}`);
    console.log(`  - 平均调用时间: ${report.summary.averageApiCallTime.toFixed(2)}ms`);

    console.log('用户交互统计:');
    console.log(`  - 总交互次数: ${report.summary.totalUserInteractions}`);
    console.log(`  - 平均响应时间: ${report.summary.averageInteractionTime.toFixed(2)}ms`);

    console.log('内存使用统计:');
    console.log(`  - 最大内存使用: ${report.summary.maxMemoryUsage.toFixed(2)}MB`);

    console.groupEnd();
  }
}

// 创建全局性能监控实例
const performanceMonitor = new PerformanceMonitor();

/**
 * React 组件性能监控高阶组件
 * @param {React.Component} WrappedComponent - 被包裹的组件
 * @param {string} componentName - 组件名称
 * @returns {React.Component} 带有性能监控的组件
 */
export function withPerformanceMonitoring(WrappedComponent, componentName) {
  return function PerformanceMonitoredComponent(props) {
    const startTime = performance.now();

    React.useEffect(() => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      performanceMonitor.recordRenderTime(componentName, duration);
    });

    return React.createElement(WrappedComponent, props);
  };
}

/**
 * 监控 API 调用性能
 * @param {Function} apiFunction - API 函数
 * @param {string} apiName - API 名称
 * @returns {Function} 带有性能监控的 API 函数
 */
export function monitorApiCall(apiFunction, apiName) {
  return async function(...args) {
    const startTime = performance.now();

    try {
      const result = await apiFunction(...args);
      const endTime = performance.now();
      performanceMonitor.recordApiCall(apiName, endTime - startTime, true);
      return result;
    } catch (error) {
      const endTime = performance.now();
      performanceMonitor.recordApiCall(apiName, endTime - startTime, false);
      throw error;
    }
  };
}

/**
 * 监控用户交互性能
 * @param {Function} handler - 事件处理函数
 * @param {string} actionName - 动作名称
 * @returns {Function} 带有性能监控的事件处理函数
 */
export function monitorUserInteraction(handler, actionName) {
  return function(event) {
    const startTime = performance.now();

    const result = handler(event);

    // 处理 Promise 情况
    if (result && typeof result.then === 'function') {
      return result.finally(() => {
        const endTime = performance.now();
        performanceMonitor.recordUserInteraction(actionName, endTime - startTime);
      });
    } else {
      const endTime = performance.now();
      performanceMonitor.recordUserInteraction(actionName, endTime - startTime);
      return result;
    }
  };
}

export default performanceMonitor;
export { PerformanceMonitor };
