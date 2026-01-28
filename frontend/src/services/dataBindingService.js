// 数据绑定服务

/**
 * 数据源类型
 */
export const DATA_SOURCE_TYPES = {
  STATIC: 'static',
  API: 'api',
  WEBSOCKET: 'websocket',
  DATABASE: 'database',
  FILE: 'file'
};

/**
 * 数据格式类型
 */
export const DATA_FORMATS = {
  JSON: 'json',
  CSV: 'csv',
  XML: 'xml',
  ARRAY: 'array',
  OBJECT: 'object'
};

/**
 * 数据转换器
 */
export const DATA_TRANSFORMERS = {
  FILTER: 'filter',
  SORT: 'sort',
  GROUP: 'group',
  AGGREGATE: 'aggregate',
  MAP: 'map',
  REDUCE: 'reduce'
};

/**
 * 数据绑定配置
 */
class DataBindingConfig {
  constructor(config = {}) {
    this.id = config.id || `binding-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this.name = config.name || '未命名数据绑定';
    this.description = config.description || '';
    this.dataSource = config.dataSource || DATA_SOURCE_TYPES.STATIC;
    this.dataFormat = config.dataFormat || DATA_FORMATS.JSON;
    this.sourceConfig = config.sourceConfig || {};
    this.transformers = config.transformers || [];
    this.refreshInterval = config.refreshInterval || 0; // 0表示不自动刷新
    this.cacheEnabled = config.cacheEnabled !== false;
    this.cacheDuration = config.cacheDuration || 300000; // 5分钟
    this.errorHandling = config.errorHandling || 'silent'; // silent, warn, throw
    this.validationRules = config.validationRules || [];
  }
}

/**
 * 数据绑定服务类
 */
class DataBindingService {
  constructor() {
    this.bindings = new Map();
    this.dataCache = new Map();
    this.subscribers = new Map();
    this.isInitialized = false;
  }

  /**
   * 初始化服务
   */
  async initialize() {
    if (this.isInitialized) return;
    
    console.log('数据绑定服务初始化');
    this.isInitialized = true;
    
    // 启动定时刷新任务
    this.startRefreshTasks();
  }

  /**
   * 创建数据绑定
   */
  createBinding(config) {
    const bindingConfig = new DataBindingConfig(config);
    
    const binding = {
      config: bindingConfig,
      data: null,
      isLoading: false,
      lastUpdated: null,
      error: null,
      subscribers: new Set()
    };
    
    this.bindings.set(bindingConfig.id, binding);
    
    console.log('创建数据绑定:', bindingConfig.id);
    
    // 立即加载数据
    this.refreshBinding(bindingConfig.id);
    
    return bindingConfig.id;
  }

  /**
   * 删除数据绑定
   */
  removeBinding(bindingId) {
    const binding = this.bindings.get(bindingId);
    if (!binding) return false;
    
    // 清理订阅者
    binding.subscribers.clear();
    
    // 从缓存中删除
    this.dataCache.delete(bindingId);
    
    // 删除绑定
    this.bindings.delete(bindingId);
    
    console.log('删除数据绑定:', bindingId);
    return true;
  }

  /**
   * 获取绑定数据
   */
  async getBindingData(bindingId) {
    const binding = this.bindings.get(bindingId);
    if (!binding) {
      throw new Error(`数据绑定不存在: ${bindingId}`);
    }
    
    // 检查缓存
    if (binding.config.cacheEnabled && this.isCacheValid(bindingId)) {
      console.log('使用缓存数据:', bindingId);
      return this.dataCache.get(bindingId);
    }
    
    // 如果正在加载，等待完成
    if (binding.isLoading) {
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!binding.isLoading) {
            clearInterval(checkInterval);
            resolve(binding.data);
          }
        }, 100);
      });
    }
    
    // 刷新数据
    await this.refreshBinding(bindingId);
    return binding.data;
  }

  /**
   * 刷新绑定数据
   */
  async refreshBinding(bindingId) {
    const binding = this.bindings.get(bindingId);
    if (!binding || binding.isLoading) return;
    
    binding.isLoading = true;
    binding.error = null;
    
    try {
      console.log('刷新数据绑定:', bindingId);
      
      // 根据数据源类型获取数据
      const rawData = await this.fetchDataFromSource(binding.config);
      
      // 数据验证
      if (!this.validateData(rawData, binding.config.validationRules)) {
        throw new Error('数据验证失败');
      }
      
      // 数据转换
      const transformedData = await this.transformData(rawData, binding.config.transformers);
      
      // 更新绑定数据
      binding.data = transformedData;
      binding.lastUpdated = new Date();
      binding.isLoading = false;
      
      // 更新缓存
      if (binding.config.cacheEnabled) {
        this.dataCache.set(bindingId, transformedData);
      }
      
      // 通知订阅者
      this.notifySubscribers(bindingId, transformedData);
      
      console.log('数据绑定刷新完成:', bindingId);
      
    } catch (error) {
      console.error('数据绑定刷新失败:', bindingId, error);
      binding.error = error;
      binding.isLoading = false;
      
      // 错误处理
      this.handleError(error, binding.config.errorHandling);
      
      // 通知订阅者错误
      this.notifySubscribers(bindingId, null, error);
    }
  }

  /**
   * 从数据源获取数据
   */
  async fetchDataFromSource(config) {
    switch (config.dataSource) {
      case DATA_SOURCE_TYPES.STATIC:
        return config.sourceConfig.data || [];
        
      case DATA_SOURCE_TYPES.API:
        return await this.fetchFromAPI(config.sourceConfig);
        
      case DATA_SOURCE_TYPES.WEBSOCKET:
        return await this.fetchFromWebSocket(config.sourceConfig);
        
      case DATA_SOURCE_TYPES.DATABASE:
        return await this.fetchFromDatabase(config.sourceConfig);
        
      case DATA_SOURCE_TYPES.FILE:
        return await this.fetchFromFile(config.sourceConfig);
        
      default:
        throw new Error(`不支持的数据源类型: ${config.dataSource}`);
    }
  }

  /**
   * 从API获取数据
   */
  async fetchFromAPI(config) {
    const { url, method = 'GET', headers = {}, body = null, timeout = 10000 } = config;
    
    if (!url) {
      throw new Error('API配置缺少URL');
    }
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body: body ? JSON.stringify(body) : null,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
      
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * 从WebSocket获取数据
   */
  async fetchFromWebSocket(config) {
    const { url, message, timeout = 10000 } = config;
    
    if (!url) {
      throw new Error('WebSocket配置缺少URL');
    }
    
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(url);
      const timeoutId = setTimeout(() => {
        ws.close();
        reject(new Error('WebSocket连接超时'));
      }, timeout);
      
      ws.onopen = () => {
        if (message) {
          ws.send(typeof message === 'string' ? message : JSON.stringify(message));
        }
      };
      
      ws.onmessage = (event) => {
        clearTimeout(timeoutId);
        try {
          const data = JSON.parse(event.data);
          ws.close();
          resolve(data);
        } catch (error) {
          ws.close();
          reject(error);
        }
      };
      
      ws.onerror = (error) => {
        clearTimeout(timeoutId);
        reject(error);
      };
    });
  }

  /**
   * 从数据库获取数据
   */
  async fetchFromDatabase(config) {
    // 这里需要根据具体的数据库API来实现
    // 暂时返回模拟数据
    console.warn('数据库数据源暂未实现，返回模拟数据');
    return config.mockData || [];
  }

  /**
   * 从文件获取数据
   */
  async fetchFromFile(config) {
    const { file, type = 'text' } = config;
    
    if (!file) {
      throw new Error('文件配置缺少文件对象');
    }
    
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        try {
          let data;
          if (type === 'json') {
            data = JSON.parse(event.target.result);
          } else if (type === 'csv') {
            data = this.parseCSV(event.target.result);
          } else {
            data = event.target.result;
          }
          resolve(data);
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('文件读取失败'));
      
      if (type === 'json' || type === 'text') {
        reader.readAsText(file);
      } else if (type === 'binary') {
        reader.readAsArrayBuffer(file);
      } else {
        reject(new Error(`不支持的文件类型: ${type}`));
      }
    });
  }

  /**
   * 解析CSV数据
   */
  parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',').map(header => header.trim());
    
    return lines.slice(1).map(line => {
      const values = line.split(',').map(value => value.trim());
      const obj = {};
      headers.forEach((header, index) => {
        obj[header] = values[index] || '';
      });
      return obj;
    });
  }

  /**
   * 数据转换
   */
  async transformData(data, transformers) {
    let transformedData = data;
    
    for (const transformer of transformers) {
      transformedData = await this.applyTransformer(transformedData, transformer);
    }
    
    return transformedData;
  }

  /**
   * 应用数据转换器
   */
  async applyTransformer(data, transformer) {
    const { type, config = {} } = transformer;
    
    switch (type) {
      case DATA_TRANSFORMERS.FILTER:
        return this.filterData(data, config);
        
      case DATA_TRANSFORMERS.SORT:
        return this.sortData(data, config);
        
      case DATA_TRANSFORMERS.GROUP:
        return this.groupData(data, config);
        
      case DATA_TRANSFORMERS.AGGREGATE:
        return this.aggregateData(data, config);
        
      case DATA_TRANSFORMERS.MAP:
        return this.mapData(data, config);
        
      case DATA_TRANSFORMERS.REDUCE:
        return this.reduceData(data, config);
        
      default:
        console.warn(`未知的转换器类型: ${type}`);
        return data;
    }
  }

  /**
   * 过滤数据
   */
  filterData(data, config) {
    const { condition } = config;
    
    if (typeof condition === 'function') {
      return data.filter(condition);
    }
    
    if (typeof condition === 'object') {
      return data.filter(item => {
        return Object.entries(condition).every(([key, value]) => {
          return item[key] === value;
        });
      });
    }
    
    return data;
  }

  /**
   * 排序数据
   */
  sortData(data, config) {
    const { key, order = 'asc' } = config;
    
    return [...data].sort((a, b) => {
      const aValue = a[key];
      const bValue = b[key];
      
      if (order === 'desc') {
        return bValue - aValue;
      }
      
      return aValue - bValue;
    });
  }

  /**
   * 分组数据
   */
  groupData(data, config) {
    const { key } = config;
    
    return data.reduce((groups, item) => {
      const groupKey = item[key];
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
      return groups;
    }, {});
  }

  /**
   * 聚合数据
   */
  aggregateData(data, config) {
    const { groupBy, operations } = config;
    
    const groups = this.groupData(data, { key: groupBy });
    
    return Object.entries(groups).map(([groupKey, groupData]) => {
      const aggregated = { [groupBy]: groupKey };
      
      operations.forEach(({ field, operation, as = field }) => {
        const values = groupData.map(item => item[field]).filter(val => val != null);
        
        switch (operation) {
          case 'sum':
            aggregated[as] = values.reduce((sum, val) => sum + val, 0);
            break;
          case 'avg':
            aggregated[as] = values.reduce((sum, val) => sum + val, 0) / values.length;
            break;
          case 'max':
            aggregated[as] = Math.max(...values);
            break;
          case 'min':
            aggregated[as] = Math.min(...values);
            break;
          case 'count':
            aggregated[as] = values.length;
            break;
          default:
            aggregated[as] = values[0];
        }
      });
      
      return aggregated;
    });
  }

  /**
   * 映射数据
   */
  mapData(data, config) {
    const { mapper } = config;
    
    if (typeof mapper === 'function') {
      return data.map(mapper);
    }
    
    if (typeof mapper === 'object') {
      return data.map(item => {
        const mapped = {};
        Object.entries(mapper).forEach(([newKey, oldKey]) => {
          mapped[newKey] = item[oldKey];
        });
        return { ...item, ...mapped };
      });
    }
    
    return data;
  }

  /**
   * 归约数据
   */
  reduceData(data, config) {
    const { reducer, initialValue } = config;
    
    if (typeof reducer === 'function') {
      return data.reduce(reducer, initialValue);
    }
    
    return data;
  }

  /**
   * 数据验证
   */
  validateData(data, rules) {
    if (!rules || rules.length === 0) return true;
    
    return rules.every(rule => {
      const { type, condition } = rule;
      
      switch (type) {
        case 'required':
          return data != null && data !== '';
        case 'type':
          return typeof data === condition;
        case 'min':
          return data >= condition;
        case 'max':
          return data <= condition;
        case 'pattern':
          return new RegExp(condition).test(data);
        case 'custom':
          return condition(data);
        default:
          return true;
      }
    });
  }

  /**
   * 检查缓存是否有效
   */
  isCacheValid(bindingId) {
    const binding = this.bindings.get(bindingId);
    if (!binding || !binding.lastUpdated) return false;
    
    const cacheAge = Date.now() - binding.lastUpdated.getTime();
    return cacheAge < binding.config.cacheDuration;
  }

  /**
   * 错误处理
   */
  handleError(error, handling) {
    switch (handling) {
      case 'warn':
        console.warn('数据绑定错误:', error);
        break;
      case 'throw':
        throw error;
      case 'silent':
      default:
        // 静默处理，不抛出错误
        break;
    }
  }

  /**
   * 订阅数据变化
   */
  subscribe(bindingId, callback) {
    const binding = this.bindings.get(bindingId);
    if (!binding) {
      throw new Error(`数据绑定不存在: ${bindingId}`);
    }
    
    binding.subscribers.add(callback);
    
    // 返回取消订阅函数
    return () => {
      binding.subscribers.delete(callback);
    };
  }

  /**
   * 通知订阅者
   */
  notifySubscribers(bindingId, data, error = null) {
    const binding = this.bindings.get(bindingId);
    if (!binding) return;
    
    binding.subscribers.forEach(callback => {
      try {
        callback(data, error);
      } catch (error) {
        console.error('订阅者回调错误:', error);
      }
    });
  }

  /**
   * 启动定时刷新任务
   */
  startRefreshTasks() {
    setInterval(() => {
      this.bindings.forEach((binding, bindingId) => {
        if (binding.config.refreshInterval > 0) {
          const timeSinceLastUpdate = Date.now() - (binding.lastUpdated?.getTime() || 0);
          if (timeSinceLastUpdate >= binding.config.refreshInterval) {
            this.refreshBinding(bindingId);
          }
        }
      });
    }, 60000); // 每分钟检查一次
  }

  /**
   * 获取绑定状态
   */
  getBindingStatus(bindingId) {
    const binding = this.bindings.get(bindingId);
    if (!binding) return null;
    
    return {
      id: bindingId,
      name: binding.config.name,
      isLoading: binding.isLoading,
      lastUpdated: binding.lastUpdated,
      error: binding.error,
      data: binding.data,
      subscribers: binding.subscribers.size
    };
  }

  /**
   * 获取所有绑定状态
   */
  getAllBindingsStatus() {
    const status = {};
    this.bindings.forEach((binding, bindingId) => {
      status[bindingId] = this.getBindingStatus(bindingId);
    });
    return status;
  }

  /**
   * 清理服务
   */
  cleanup() {
    this.bindings.clear();
    this.dataCache.clear();
    this.subscribers.clear();
    this.isInitialized = false;
    console.log('数据绑定服务已清理');
  }
}

// 创建单例实例
const dataBindingService = new DataBindingService();

export { DataBindingService, DataBindingConfig, DATA_SOURCE_TYPES, DATA_FORMATS, DATA_TRANSFORMERS };
export default dataBindingService;