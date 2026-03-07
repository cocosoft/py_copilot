/**
 * 错误处理工具
 *
 * 提供统一的错误处理和用户友好的错误提示
 */

import React from 'react';

/**
 * 错误类型定义
 */
export const ErrorTypes = {
  NETWORK: 'network',
  VALIDATION: 'validation',
  AUTHENTICATION: 'authentication',
  PERMISSION: 'permission',
  SERVER: 'server',
  CLIENT: 'client',
  UNKNOWN: 'unknown'
};

/**
 * 错误消息映射
 */
const errorMessages = {
  [ErrorTypes.NETWORK]: {
    title: '网络错误',
    message: '网络连接失败，请检查您的网络设置后重试'
  },
  [ErrorTypes.VALIDATION]: {
    title: '验证错误',
    message: '输入数据验证失败，请检查您的输入'
  },
  [ErrorTypes.AUTHENTICATION]: {
    title: '认证错误',
    message: '您的登录已过期，请重新登录'
  },
  [ErrorTypes.PERMISSION]: {
    title: '权限错误',
    message: '您没有权限执行此操作'
  },
  [ErrorTypes.SERVER]: {
    title: '服务器错误',
    message: '服务器处理请求时出错，请稍后重试'
  },
  [ErrorTypes.CLIENT]: {
    title: '客户端错误',
    message: '客户端处理时出错，请刷新页面后重试'
  },
  [ErrorTypes.UNKNOWN]: {
    title: '未知错误',
    message: '发生未知错误，请稍后重试'
  }
};

/**
 * 错误处理器类
 */
class ErrorHandler {
  /**
   * 构造函数
   */
  constructor() {
    this.errorListeners = [];
  }

  /**
   * 注册错误监听器
   * @param {Function} listener - 错误监听器函数
   * @returns {Function} 取消注册函数
   */
  onError(listener) {
    this.errorListeners.push(listener);
    return () => {
      this.errorListeners = this.errorListeners.filter(l => l !== listener);
    };
  }

  /**
   * 处理错误
   * @param {Error} error - 错误对象
   * @param {Object} options - 选项
   * @param {string} options.type - 错误类型
   * @param {string} options.title - 错误标题
   * @param {string} options.message - 错误消息
   * @param {Object} options.context - 错误上下文
   * @returns {Object} 标准化的错误对象
   */
  handleError(error, options = {}) {
    // 标准化错误
    const normalizedError = this.normalizeError(error, options);

    // 通知所有监听器
    this.errorListeners.forEach(listener => {
      try {
        listener(normalizedError);
      } catch (listenerError) {
        console.error('Error listener failed:', listenerError);
      }
    });

    // 记录错误
    this.logError(normalizedError);

    return normalizedError;
  }

  /**
   * 标准化错误
   * @param {Error} error - 错误对象
   * @param {Object} options - 选项
   * @returns {Object} 标准化的错误对象
   */
  normalizeError(error, options = {}) {
    let type = options.type || ErrorTypes.UNKNOWN;
    let title = options.title;
    let message = options.message;
    let context = options.context || {};

    // 基于错误对象推断错误类型
    if (!options.type) {
      type = this.inferErrorType(error);
    }

    // 使用默认消息
    if (!title) {
      title = errorMessages[type].title;
    }

    if (!message) {
      message = this.getErrorMessage(error, type);
    }

    return {
      id: Date.now() + Math.random().toString(36).substr(2, 9),
      type,
      title,
      message,
      originalError: error,
      context,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * 推断错误类型
   * @param {Error} error - 错误对象
   * @returns {string} 错误类型
   */
  inferErrorType(error) {
    if (!error) {
      return ErrorTypes.UNKNOWN;
    }

    if (error.name === 'NetworkError' || 
        error.message.includes('network') ||
        error.message.includes('Network') ||
        error.message.includes('fetch') ||
        error.message.includes('timeout')) {
      return ErrorTypes.NETWORK;
    }

    if (error.name === 'ValidationError' ||
        error.message.includes('validation') ||
        error.message.includes('Validation') ||
        error.message.includes('invalid')) {
      return ErrorTypes.VALIDATION;
    }

    if (error.name === 'AuthenticationError' ||
        error.message.includes('auth') ||
        error.message.includes('login') ||
        error.message.includes('token')) {
      return ErrorTypes.AUTHENTICATION;
    }

    if (error.name === 'PermissionError' ||
        error.message.includes('permission') ||
        error.message.includes('Permission') ||
        error.message.includes('access')) {
      return ErrorTypes.PERMISSION;
    }

    if (error.status >= 500) {
      return ErrorTypes.SERVER;
    }

    if (error.status >= 400 && error.status < 500) {
      return ErrorTypes.CLIENT;
    }

    return ErrorTypes.UNKNOWN;
  }

  /**
   * 获取错误消息
   * @param {Error} error - 错误对象
   * @param {string} type - 错误类型
   * @returns {string} 错误消息
   */
  getErrorMessage(error, type) {
    if (error.message) {
      // 提取有意义的错误消息
      return this.extractErrorMessage(error.message) || errorMessages[type].message;
    }
    return errorMessages[type].message;
  }

  /**
   * 提取错误消息
   * @param {string} message - 原始错误消息
   * @returns {string} 提取的错误消息
   */
  extractErrorMessage(message) {
    // 简单的消息提取逻辑
    const trimmedMessage = message.trim();
    if (trimmedMessage.length > 0 && trimmedMessage.length < 100) {
      return trimmedMessage;
    }
    return null;
  }

  /**
   * 记录错误
   * @param {Object} error - 标准化的错误对象
   */
  logError(error) {
    console.error('[ErrorHandler]', error.type, error.message, error.originalError);

    // 可以在这里添加错误日志到服务器的逻辑
    // sendErrorToServer(error);
  }

  /**
   * 创建网络错误
   * @param {string} message - 错误消息
   * @returns {Error} 网络错误对象
   */
  createNetworkError(message = '网络连接失败') {
    const error = new Error(message);
    error.name = 'NetworkError';
    return error;
  }

  /**
   * 创建验证错误
   * @param {string} message - 错误消息
   * @returns {Error} 验证错误对象
   */
  createValidationError(message = '数据验证失败') {
    const error = new Error(message);
    error.name = 'ValidationError';
    return error;
  }

  /**
   * 创建认证错误
   * @param {string} message - 错误消息
   * @returns {Error} 认证错误对象
   */
  createAuthenticationError(message = '认证失败') {
    const error = new Error(message);
    error.name = 'AuthenticationError';
    return error;
  }

  /**
   * 创建权限错误
   * @param {string} message - 错误消息
   * @returns {Error} 权限错误对象
   */
  createPermissionError(message = '权限不足') {
    const error = new Error(message);
    error.name = 'PermissionError';
    return error;
  }
}

// 创建全局错误处理器实例
const errorHandler = new ErrorHandler();

/**
 * 错误处理高阶组件
 * @param {React.Component} WrappedComponent - 被包裹的组件
 * @returns {React.Component} 带有错误处理的组件
 */
export function withErrorHandling(WrappedComponent) {
  return class ErrorHandledComponent extends React.Component {
    componentDidCatch(error, errorInfo) {
      errorHandler.handleError(error, {
        context: {
          component: WrappedComponent.name,
          errorInfo
        }
      });
    }

    render() {
      return React.createElement(WrappedComponent, this.props);
    }
  };
}

/**
 * 错误边界组件
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    errorHandler.handleError(error, {
      context: {
        component: 'ErrorBoundary',
        errorInfo
      }
    });
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <div className="error-content">
            <div className="error-icon">⚠️</div>
            <h3>发生错误</h3>
            <p>页面加载过程中发生错误，请刷新页面重试</p>
            <button 
              className="btn-primary"
              onClick={() => window.location.reload()}
            >
              刷新页面
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * API 错误处理包装器
 * @param {Function} apiFunction - API 函数
 * @returns {Function} 带有错误处理的 API 函数
 */
export function withApiErrorHandling(apiFunction) {
  return async function(...args) {
    try {
      return await apiFunction(...args);
    } catch (error) {
      throw errorHandler.handleError(error);
    }
  };
}

export default errorHandler;
export { ErrorHandler };
