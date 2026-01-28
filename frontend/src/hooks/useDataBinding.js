import { useState, useEffect, useCallback, useRef } from 'react';
import dataBindingService, { DATA_SOURCE_TYPES, DATA_FORMATS, DATA_TRANSFORMERS } from '../services/dataBindingService';

/**
 * 数据绑定Hook
 */
const useDataBinding = (bindingConfig) => {
  const [bindingState, setBindingState] = useState({
    data: null,
    isLoading: false,
    error: null,
    lastUpdated: null,
    bindingId: null
  });

  const bindingIdRef = useRef(null);
  const isMountedRef = useRef(true);

  /**
   * 创建数据绑定
   */
  const createBinding = useCallback(async (config) => {
    if (!isMountedRef.current) return;

    try {
      setBindingState(prev => ({ ...prev, isLoading: true, error: null }));

      // 确保服务已初始化
      await dataBindingService.initialize();

      // 创建绑定
      const bindingId = dataBindingService.createBinding(config);
      bindingIdRef.current = bindingId;

      // 订阅数据变化
      const unsubscribe = dataBindingService.subscribe(bindingId, (data, error) => {
        if (!isMountedRef.current) return;

        setBindingState({
          data,
          isLoading: false,
          error,
          lastUpdated: new Date(),
          bindingId
        });
      });

      // 获取初始数据
      const initialData = await dataBindingService.getBindingData(bindingId);
      
      if (isMountedRef.current) {
        setBindingState({
          data: initialData,
          isLoading: false,
          error: null,
          lastUpdated: new Date(),
          bindingId
        });
      }

      return unsubscribe;

    } catch (error) {
      if (isMountedRef.current) {
        setBindingState(prev => ({ ...prev, isLoading: false, error }));
      }
      console.error('创建数据绑定失败:', error);
    }
  }, []);

  /**
   * 刷新数据
   */
  const refreshData = useCallback(async () => {
    if (!bindingIdRef.current) return;

    try {
      setBindingState(prev => ({ ...prev, isLoading: true, error: null }));
      
      await dataBindingService.refreshBinding(bindingIdRef.current);
      
    } catch (error) {
      if (isMountedRef.current) {
        setBindingState(prev => ({ ...prev, isLoading: false, error }));
      }
      console.error('刷新数据失败:', error);
    }
  }, []);

  /**
   * 更新绑定配置
   */
  const updateBinding = useCallback(async (newConfig) => {
    if (!bindingIdRef.current) return;

    try {
      // 删除旧绑定
      dataBindingService.removeBinding(bindingIdRef.current);
      
      // 创建新绑定
      await createBinding(newConfig);
      
    } catch (error) {
      console.error('更新数据绑定失败:', error);
    }
  }, [createBinding]);

  /**
   * 删除绑定
   */
  const removeBinding = useCallback(() => {
    if (bindingIdRef.current) {
      dataBindingService.removeBinding(bindingIdRef.current);
      bindingIdRef.current = null;
      
      setBindingState({
        data: null,
        isLoading: false,
        error: null,
        lastUpdated: null,
        bindingId: null
      });
    }
  }, []);

  /**
   * 获取绑定状态
   */
  const getBindingStatus = useCallback(() => {
    if (!bindingIdRef.current) return null;
    return dataBindingService.getBindingStatus(bindingIdRef.current);
  }, []);

  // 初始化绑定
  useEffect(() => {
    if (bindingConfig) {
      createBinding(bindingConfig);
    }

    return () => {
      isMountedRef.current = false;
      if (bindingIdRef.current) {
        dataBindingService.removeBinding(bindingIdRef.current);
      }
    };
  }, [bindingConfig, createBinding]);

  /**
   * 手动触发数据刷新
   */
  const triggerRefresh = useCallback(() => {
    refreshData();
  }, [refreshData]);

  /**
   * 重置绑定状态
   */
  const resetBinding = useCallback(() => {
    removeBinding();
    if (bindingConfig) {
      createBinding(bindingConfig);
    }
  }, [bindingConfig, createBinding, removeBinding]);

  /**
   * 导出数据
   */
  const exportData = useCallback((format = 'json') => {
    if (!bindingState.data) return null;

    switch (format) {
      case 'json':
        return JSON.stringify(bindingState.data, null, 2);
      
      case 'csv':
        return convertToCSV(bindingState.data);
      
      case 'array':
        return bindingState.data;
      
      default:
        return bindingState.data;
    }
  }, [bindingState.data]);

  /**
   * 数据转换辅助函数
   */
  const convertToCSV = (data) => {
    if (!Array.isArray(data) || data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const csvRows = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => {
          const value = row[header];
          return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
        }).join(',')
      )
    ];

    return csvRows.join('\n');
  };

  /**
   * 数据统计信息
   */
  const getStats = useCallback(() => {
    if (!bindingState.data || !Array.isArray(bindingState.data)) {
      return null;
    }

    const data = bindingState.data;
    
    return {
      count: data.length,
      fields: data.length > 0 ? Object.keys(data[0]) : [],
      numericFields: data.length > 0 ? 
        Object.keys(data[0]).filter(key => 
          typeof data[0][key] === 'number'
        ) : [],
      sample: data.slice(0, 5)
    };
  }, [bindingState.data]);

  /**
   * 数据过滤
   */
  const filterData = useCallback((condition) => {
    if (!bindingState.data || !Array.isArray(bindingState.data)) {
      return [];
    }

    if (typeof condition === 'function') {
      return bindingState.data.filter(condition);
    }

    if (typeof condition === 'object') {
      return bindingState.data.filter(item => {
        return Object.entries(condition).every(([key, value]) => {
          return item[key] === value;
        });
      });
    }

    return bindingState.data;
  }, [bindingState.data]);

  /**
   * 数据排序
   */
  const sortData = useCallback((key, order = 'asc') => {
    if (!bindingState.data || !Array.isArray(bindingState.data)) {
      return [];
    }

    return [...bindingState.data].sort((a, b) => {
      const aValue = a[key];
      const bValue = b[key];
      
      if (order === 'desc') {
        return bValue - aValue;
      }
      
      return aValue - bValue;
    });
  }, [bindingState.data]);

  /**
   * 数据分组
   */
  const groupData = useCallback((key) => {
    if (!bindingState.data || !Array.isArray(bindingState.data)) {
      return {};
    }

    return bindingState.data.reduce((groups, item) => {
      const groupKey = item[key];
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
      return groups;
    }, {});
  }, [bindingState.data]);

  return {
    // 状态
    data: bindingState.data,
    isLoading: bindingState.isLoading,
    error: bindingState.error,
    lastUpdated: bindingState.lastUpdated,
    bindingId: bindingState.bindingId,

    // 操作方法
    createBinding,
    refreshData: triggerRefresh,
    updateBinding,
    removeBinding,
    resetBinding,
    
    // 数据操作
    exportData,
    getStats,
    filterData,
    sortData,
    groupData,
    
    // 状态查询
    getBindingStatus,

    // 常量
    DATA_SOURCE_TYPES,
    DATA_FORMATS,
    DATA_TRANSFORMERS
  };
};

/**
 * 快速创建静态数据绑定的Hook
 */
const useStaticData = (staticData, config = {}) => {
  const bindingConfig = {
    ...config,
    dataSource: DATA_SOURCE_TYPES.STATIC,
    sourceConfig: {
      data: staticData
    }
  };

  return useDataBinding(bindingConfig);
};

/**
 * 快速创建API数据绑定的Hook
 */
const useApiData = (apiConfig, config = {}) => {
  const bindingConfig = {
    ...config,
    dataSource: DATA_SOURCE_TYPES.API,
    sourceConfig: apiConfig
  };

  return useDataBinding(bindingConfig);
};

/**
 * 快速创建WebSocket数据绑定的Hook
 */
const useWebSocketData = (websocketConfig, config = {}) => {
  const bindingConfig = {
    ...config,
    dataSource: DATA_SOURCE_TYPES.WEBSOCKET,
    sourceConfig: websocketConfig
  };

  return useDataBinding(bindingConfig);
};

export default useDataBinding;
export { useStaticData, useApiData, useWebSocketData, DATA_SOURCE_TYPES, DATA_FORMATS, DATA_TRANSFORMERS };