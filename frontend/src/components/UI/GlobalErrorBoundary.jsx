import React from 'react';
import useErrorStore from '../../stores/errorStore';
import errorService from '../../services/errorService';
import './GlobalErrorBoundary.css';

/**
 * 全局错误边界组件
 * 捕获应用级别的错误，提供统一的错误处理
 */
class GlobalErrorBoundary extends React.Component {
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
    
    // 使用错误处理服务处理错误
    const errorStore = useErrorStore.getState();
    errorStore.handleComponentError(error, {
      component: this.props.name || 'Global',
      errorInfo: errorInfo
    });
  }

  handleRetry = () => {
    // 重置错误状态
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
    
    // 清除全局错误
    useErrorStore.getState().clearError();
    
    // 调用父组件提供的重试函数
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  handleReport = async () => {
    // 错误报告逻辑
    const errorData = {
      error: this.state.error?.toString(),
      componentStack: this.state.errorInfo?.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      component: this.props.name || 'Global'
    };
    
    // 报告错误
    const result = await errorService.reportError(errorData);
    
    if (result.success) {
      alert(`错误报告成功，报告ID: ${result.reportId}`);
    } else {
      alert(`错误报告失败: ${result.error}`);
    }
  };

  render() {
    if (this.state.hasError) {
      // 降级UI
      return (
        <div className="global-error-boundary">
          <div className="global-error-boundary__content">
            <div className="global-error-boundary__icon">
              ⚠️
            </div>
            <h2 className="global-error-boundary__title">
              应用发生错误
            </h2>
            <p className="global-error-boundary__message">
              {this.props.fallbackMessage || '抱歉，应用出现了一些问题。'}
            </p>
            
            {import.meta.env.DEV && (
              <details className="global-error-boundary__details">
                <summary>错误详情</summary>
                <div className="global-error-boundary__error-info">
                  <p><strong>错误信息:</strong> {this.state.error?.toString()}</p>
                  <pre className="global-error-boundary__stack">
                    {this.state.errorInfo?.componentStack}
                  </pre>
                </div>
              </details>
            )}
            
            <div className="global-error-boundary__actions">
              <button
                className="global-error-boundary__button global-error-boundary__button--primary"
                onClick={this.handleRetry}
              >
                重试
              </button>
              
              <button
                className="global-error-boundary__button global-error-boundary__button--secondary"
                onClick={this.handleReport}
              >
                报告错误
              </button>
              
              <button
                className="global-error-boundary__button global-error-boundary__button--secondary"
                onClick={() => window.location.reload()}
              >
                刷新页面
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default GlobalErrorBoundary;
