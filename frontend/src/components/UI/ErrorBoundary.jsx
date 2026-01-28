import React from 'react';
import './ErrorBoundary.css';

/**
 * 错误边界组件
 * 捕获子组件的JavaScript错误并显示降级UI
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
    // 更新state使下一次渲染能够显示降级UI
    return {
      hasError: true,
      error: error
    };
  }

  componentDidCatch(error, errorInfo) {
    // 捕获错误并记录错误信息
    this.setState({
      errorInfo: errorInfo
    });
    
    // 可以在这里将错误信息发送到错误监控服务
    console.error('组件错误:', error, errorInfo);
  }

  handleRetry = () => {
    // 重置错误状态
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
    
    // 调用父组件提供的重试函数
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  handleReport = () => {
    // 错误报告逻辑
    const errorData = {
      error: this.state.error?.toString(),
      componentStack: this.state.errorInfo?.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };
    
    console.log('错误报告:', errorData);
    
    // 这里可以发送错误报告到后端API
    if (this.props.onReport) {
      this.props.onReport(errorData);
    }
  };

  render() {
    if (this.state.hasError) {
      // 降级UI
      return (
        <div className="ui-error-boundary">
          <div className="ui-error-boundary__content">
            <div className="ui-error-boundary__icon">
              ⚠️
            </div>
            <h3 className="ui-error-boundary__title">
              组件加载失败
            </h3>
            <p className="ui-error-boundary__message">
              {this.props.fallbackMessage || '抱歉，组件出现了一些问题。'}
            </p>
            
            {this.props.showDetails && (
              <details className="ui-error-boundary__details">
                <summary>错误详情</summary>
                <div className="ui-error-boundary__error-info">
                  <p><strong>错误信息:</strong> {this.state.error?.toString()}</p>
                  <pre className="ui-error-boundary__stack">
                    {this.state.errorInfo?.componentStack}
                  </pre>
                </div>
              </details>
            )}
            
            <div className="ui-error-boundary__actions">
              <button
                className="ui-error-boundary__button ui-error-boundary__button--primary"
                onClick={this.handleRetry}
              >
                重试
              </button>
              
              {this.props.enableReporting && (
                <button
                  className="ui-error-boundary__button ui-error-boundary__button--secondary"
                  onClick={this.handleReport}
                >
                  报告错误
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * 错误提示组件
 */
const ErrorMessage = ({
  type = 'error', // error, warning, info
  title,
  message,
  showIcon = true,
  showClose = false,
  onClose,
  className = '',
  ...props
}) => {
  const baseClass = 'ui-error-message';
  const typeClass = `ui-error-message--${type}`;
  
  const classes = [
    baseClass,
    typeClass,
    className
  ].filter(Boolean).join(' ');

  const getIcon = () => {
    switch (type) {
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '❌';
    }
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className={classes} {...props}>
      {showIcon && (
        <div className="ui-error-message__icon">
          {getIcon()}
        </div>
      )}
      
      <div className="ui-error-message__content">
        {title && (
          <h4 className="ui-error-message__title">
            {title}
          </h4>
        )}
        
        <p className="ui-error-message__message">
          {message}
        </p>
      </div>
      
      {showClose && (
        <button
          className="ui-error-message__close"
          onClick={handleClose}
          aria-label="关闭"
        >
          ×
        </button>
      )}
    </div>
  );
};

// 导出所有组件
ErrorBoundary.Message = ErrorMessage;

export default ErrorBoundary;