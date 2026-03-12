/**
 * 错误边界组件
 * 
 * 捕获子组件的错误，防止整个应用崩溃
 */

import React from 'react';
import { FiAlertTriangle, FiRefreshCw } from 'react-icons/fi';
import Button from '../Button';
import './styles.css';

/**
 * 错误边界组件
 * 
 * @example
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // 更新 state 使下一次渲染显示降级 UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // 记录错误信息
    this.setState({ errorInfo });
    
    // 可以在这里发送错误日志到服务器
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // 调用外部错误处理回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * 重置错误状态
   */
  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
    
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  /**
   * 刷新页面
   */
  handleReload = () => {
    window.location.reload();
  };

  render() {
    const { hasError, error, errorInfo } = this.state;
    const { fallback, children } = this.props;

    if (hasError) {
      // 自定义降级 UI
      if (fallback) {
        return fallback({
          error,
          errorInfo,
          onReset: this.handleReset,
          onReload: this.handleReload,
        });
      }

      // 默认降级 UI
      return (
        <div className="error-boundary-fallback">
          <div className="error-icon">
            <FiAlertTriangle size={48} />
          </div>
          <h2>出错了</h2>
          <p className="error-message">
            {error?.message || '组件渲染发生错误'}
          </p>
          
          {process.env.NODE_ENV === 'development' && errorInfo && (
            <details className="error-details">
              <summary>查看错误详情</summary>
              <pre>{errorInfo.componentStack}</pre>
            </details>
          )}
          
          <div className="error-actions">
            <Button
              variant="primary"
              icon={<FiRefreshCw />}
              onClick={this.handleReset}
            >
              重试
            </Button>
            <Button
              variant="secondary"
              onClick={this.handleReload}
            >
              刷新页面
            </Button>
          </div>
        </div>
      );
    }

    return children;
  }
}

/**
 * 异步错误边界
 * 
 * 用于捕获异步操作中的错误
 */
export const AsyncErrorBoundary = ({ children, onError }) => {
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const handleError = (event) => {
      setError(event.error);
      if (onError) {
        onError(event.error);
      }
      event.preventDefault();
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleError);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleError);
    };
  }, [onError]);

  if (error) {
    return (
      <div className="async-error-fallback">
        <FiAlertTriangle size={32} />
        <p>发生错误: {error.message}</p>
        <Button onClick={() => setError(null)}>重试</Button>
      </div>
    );
  }

  return children;
};

/**
 * 知识库模块专用错误边界
 */
export const KnowledgeErrorBoundary = ({ children }) => (
  <ErrorBoundary
    fallback={({ error, onReset, onReload }) => (
      <div className="knowledge-error-fallback">
        <div className="knowledge-error-content">
          <div className="error-icon">⚠️</div>
          <h3>知识库加载失败</h3>
          <p>{error?.message || '请检查网络连接后重试'}</p>
          <div className="error-actions">
            <Button variant="primary" onClick={onReset}>
              重试
            </Button>
            <Button variant="secondary" onClick={onReload}>
              刷新页面
            </Button>
          </div>
        </div>
      </div>
    )}
  >
    {children}
  </ErrorBoundary>
);

export default ErrorBoundary;
