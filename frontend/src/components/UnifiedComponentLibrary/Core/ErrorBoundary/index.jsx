/**
 * 统一错误边界组件
 * 
 * 整合项目中多个错误边界实现，提供统一的错误处理机制
 * 支持错误捕获、错误展示和错误恢复功能
 */

import React, { Component } from 'react';
import './ErrorBoundary.css';

/**
 * 错误边界组件属性定义
 * @typedef {Object} ErrorBoundaryProps
 * @property {React.ReactNode} children - 子组件
 * @property {React.ReactNode} fallback - 错误回退组件
 * @property {Function} onError - 错误回调
 * @property {boolean} showDetails - 是否显示错误详情
 * @property {string} className - 自定义类名
 */

/**
 * 错误边界组件状态定义
 * @typedef {Object} ErrorBoundaryState
 * @property {boolean} hasError - 是否有错误
 * @property {Error|null} error - 错误对象
 * @property {string} errorInfo - 错误信息
 */

class ErrorBoundary extends Component {
  /**
   * 构造函数
   * @param {ErrorBoundaryProps} props - 组件属性
   */
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: ''
    };
  }

  /**
   * 静态方法：当子组件抛出错误时调用
   * @param {Error} error - 错误对象
   * @returns {ErrorBoundaryState} 新的状态
   */
  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      error: error
    };
  }

  /**
   * 生命周期方法：捕获错误
   * @param {Error} error - 错误对象
   * @param {Object} errorInfo - 错误信息
   */
  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      errorInfo: errorInfo.componentStack
    });

    // 调用错误回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 可以在这里发送错误报告
    this.reportError(error, errorInfo);
  }

  /**
   * 报告错误
   * @param {Error} error - 错误对象
   * @param {Object} errorInfo - 错误信息
   */
  reportError(error, errorInfo) {
    // 在实际项目中，这里可以集成错误报告服务
    // 如 Sentry、LogRocket 等
    console.group('Error Report');
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.groupEnd();
  }

  /**
   * 重置错误状态
   */
  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: ''
    });
  };

  /**
   * 渲染方法
   * @returns {React.ReactNode}
   */
  render() {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback, showDetails = false, className = '' } = this.props;

    if (hasError) {
      // 如果提供了自定义回退组件，使用自定义组件
      if (fallback) {
        return React.isValidElement(fallback) 
          ? React.cloneElement(fallback, { error, resetError: this.resetError })
          : fallback;
      }

      // 默认错误回退界面
      return (
        <div className={`ucl-error-boundary ${className}`}>
          <div className="ucl-error-boundary__content">
            <div className="ucl-error-boundary__icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10" strokeWidth="2" />
                <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2" />
                <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2" />
              </svg>
            </div>
            
            <h2 className="ucl-error-boundary__title">
              组件加载失败
            </h2>
            
            <p className="ucl-error-boundary__message">
              抱歉，当前组件出现了一些问题。
            </p>
            
            {showDetails && error && (
              <details className="ucl-error-boundary__details">
                <summary>错误详情</summary>
                <div className="ucl-error-boundary__error-info">
                  <strong>错误信息:</strong>
                  <pre>{error.toString()}</pre>
                  
                  {errorInfo && (
                    <>
                      <strong>组件堆栈:</strong>
                      <pre>{errorInfo}</pre>
                    </>
                  )}
                </div>
              </details>
            )}
            
            <div className="ucl-error-boundary__actions">
              <button
                className="ucl-error-boundary__retry-button"
                onClick={this.resetError}
              >
                重试
              </button>
              
              <button
                className="ucl-error-boundary__reload-button"
                onClick={() => window.location.reload()}
              >
                刷新页面
              </button>
            </div>
          </div>
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;