/**
 * 错误状态管理
 * 全局错误状态管理、错误队列和历史记录
 */
import { create } from 'zustand';
import errorService from '../services/errorService';

const useErrorStore = create((set, get) => ({
  // 当前错误
  currentError: null,
  
  // 错误队列
  errorQueue: [],
  
  // 错误历史
  errorHistory: [],
  
  // 最大历史记录数
  maxHistory: 50,
  
  /**
   * 设置当前错误
   * @param {Object} error - 错误对象
   */
  setError: (error) => {
    set({ currentError: error });
    
    // 添加到错误队列
    get().addErrorToQueue(error);
    
    // 添加到错误历史
    get().addErrorToHistory(error);
    
    // 显示错误提示
    errorService.showError(error);
  },
  
  /**
   * 清除当前错误
   */
  clearError: () => {
    set({ currentError: null });
  },
  
  /**
   * 添加错误到队列
   * @param {Object} error - 错误对象
   */
  addErrorToQueue: (error) => {
    set((state) => ({
      errorQueue: [...state.errorQueue, error].slice(-10) // 只保留最近10个错误
    }));
  },
  
  /**
   * 清除错误队列
   */
  clearErrorQueue: () => {
    set({ errorQueue: [] });
  },
  
  /**
   * 添加错误到历史记录
   * @param {Object} error - 错误对象
   */
  addErrorToHistory: (error) => {
    set((state) => {
      const newHistory = [
        {
          ...error,
          timestamp: new Date().toISOString()
        },
        ...state.errorHistory
      ].slice(0, state.maxHistory);
      
      return { errorHistory: newHistory };
    });
  },
  
  /**
   * 清除错误历史
   */
  clearErrorHistory: () => {
    set({ errorHistory: [] });
  },
  
  /**
   * 处理API错误
   * @param {Object} error - API错误对象
   * @returns {Object} 标准化的错误对象
   */
  handleApiError: (error) => {
    const normalizedError = errorService.handleApiError(error);
    get().setError(normalizedError);
    return normalizedError;
  },
  
  /**
   * 处理组件错误
   * @param {Error} error - 组件错误
   * @param {Object} context - 错误上下文
   * @returns {Object} 标准化的错误对象
   */
  handleComponentError: (error, context = {}) => {
    const normalizedError = {
      code: 'SYSTEM_001',
      message: error.message || '组件错误',
      details: error.stack || '',
      context: {
        ...context,
        component: context.component || 'Unknown',
        timestamp: new Date().toISOString()
      }
    };
    
    get().setError(normalizedError);
    errorService.logError(normalizedError);
    return normalizedError;
  }
}));

export default useErrorStore;
