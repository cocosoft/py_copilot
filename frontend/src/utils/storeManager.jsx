import React, { createContext, useContext, useEffect } from 'react';
import { useRootStore } from '../stores';

/**
 * 状态管理上下文
 * 提供全局状态访问和订阅功能
 */
const StoreContext = createContext();

/**
 * Store Provider 组件
 * 为应用提供状态管理功能
 */
export const StoreProvider = ({ children }) => {
  const rootStore = useRootStore();

  return (
    <StoreContext.Provider value={rootStore}>
      {children}
    </StoreContext.Provider>
  );
};

/**
 * 使用Store上下文
 */
export const useStoreContext = () => {
  const context = useContext(StoreContext);
  if (!context) {
    throw new Error('useStoreContext must be used within a StoreProvider');
  }
  return context;
};

/**
 * 状态监控组件
 * 用于调试和监控状态变化
 */
export const StoreMonitor = ({ enabled = false, maxEntries = 50 }) => {
  const rootStore = useStoreContext();
  const [entries, setEntries] = React.useState([]);

  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = rootStore.subscribe((state, prevState) => {
      // 记录状态变化
      const entry = {
        timestamp: new Date().toISOString(),
        changes: {},
      };

      // 检测变化
      Object.keys(state).forEach(key => {
        if (state[key] !== prevState[key]) {
          entry.changes[key] = {
            from: prevState[key],
            to: state[key],
          };
        }
      });

      setEntries(prev => {
        const newEntries = [entry, ...prev].slice(0, maxEntries);
        return newEntries;
      });
    });

    return unsubscribe;
  }, [enabled, rootStore, maxEntries]);

  if (!enabled) return null;

  return (
    <div className="fixed bottom-4 right-4 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-50">
      <h3 className="font-semibold mb-2">状态监控</h3>
      <div className="max-h-60 overflow-y-auto space-y-2">
        {entries.map((entry, index) => (
          <div key={index} className="text-xs">
            <div className="font-mono text-gray-500">{entry.timestamp}</div>
            <div className="text-red-600">
              {Object.keys(entry.changes).map(key => (
                <div key={key}>
                  {key}: {JSON.stringify(entry.changes[key].from)} → {JSON.stringify(entry.changes[key].to)}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * 状态持久化管理
 */
export class StatePersistence {
  constructor() {
    this.storageKey = 'app-state-backup';
    this.autoSaveInterval = null;
  }

  // 备份当前状态
  backupState = () => {
    try {
      const state = useRootStore.getState();
      const backup = {
        timestamp: Date.now(),
        state: state.getSnapshot(),
        version: '1.0.0',
      };
      
      localStorage.setItem(this.storageKey, JSON.stringify(backup));
      return backup;
    } catch (error) {
      return null;
    }
  };

  // 恢复状态
  restoreState = () => {
    try {
      const backupData = localStorage.getItem(this.storageKey);
      if (!backupData) {
        return null;
      }

      const backup = JSON.parse(backupData);
      
      // 验证备份数据格式
      if (!backup.timestamp || !backup.state) {
        return null;
      }

      // 检查备份是否过期（7天）
      const sevenDays = 7 * 24 * 60 * 60 * 1000;
      if (Date.now() - backup.timestamp > sevenDays) {
        localStorage.removeItem(this.storageKey);
        return null;
      }

      // 恢复各个store的状态
      const { app, auth, model, supplier, api } = backup.state;
      
      if (app) {
        Object.assign(useRootStore.getState(), app);
      }
      return backup;
    } catch (error) {
      return null;
    }
  };

  // 清除备份
  clearBackup = () => {
    localStorage.removeItem(this.storageKey);
  };

  // 启动自动备份
  startAutoBackup = (intervalMs = 30000) => {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
    }

    this.autoSaveInterval = setInterval(() => {
      this.backupState();
    }, intervalMs);
  };

  // 停止自动备份
  stopAutoBackup = () => {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }
  };
}

// 全局状态持久化管理器实例
export const statePersistence = new StatePersistence();

/**
 * 状态管理器Hook
 * 提供便捷的状态操作方法
 */
export const useStateManager = () => {
  const rootStore = useStoreContext();

  return {
    // 基础操作
    initialize: rootStore.initializeApp,
    reset: rootStore.resetAll,
    setError: rootStore.setGlobalError,
    clearError: rootStore.clearGlobalError,

    // 状态快照
    getSnapshot: rootStore.getSnapshot,
    
    // 批量更新
    batchUpdate: rootStore.batchUpdate,

    // 订阅管理
    subscribe: rootStore.subscribeToStore,

    // 持久化操作
    backup: statePersistence.backupState,
    restore: statePersistence.restoreState,
    clearBackup: statePersistence.clearBackup,
    startAutoBackup: statePersistence.startAutoBackup,
    stopAutoBackup: statePersistence.stopAutoBackup,

    // Store访问
    app: useRootStore(state => state.app),
    auth: useRootStore(state => state.auth),
    model: useRootStore(state => state.model),
    supplier: useRootStore(state => state.supplier),
    api: useRootStore(state => state.api),
  };
};

/**
 * 状态性能监控Hook
 */
export const useStatePerformance = () => {
  const [metrics, setMetrics] = React.useState({
    renderCount: 0,
    lastUpdate: null,
    updateDuration: 0,
  });

  const rootStore = useStoreContext();
  const renderStartTime = React.useRef(Date.now());

  useEffect(() => {
    const startTime = performance.now();
    
    const unsubscribe = rootStore.subscribe(() => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      setMetrics(prev => ({
        renderCount: prev.renderCount + 1,
        lastUpdate: new Date().toISOString(),
        updateDuration: duration,
      }));
    });

    return unsubscribe;
  }, [rootStore]);

  return metrics;
};

export default {
  StoreProvider,
  StoreMonitor,
  StatePersistence,
  statePersistence,
  useStateManager,
  useStatePerformance,
};