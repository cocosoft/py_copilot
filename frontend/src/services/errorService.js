/**
 * 错误处理服务
 * 提供统一的错误处理、报告和日志功能
 */

// 错误码映射
const ERROR_CODES = {
  // 认证错误
  AUTH_001: '认证失败，请重新登录',
  AUTH_002: '令牌过期，请重新登录',
  AUTH_003: '无效的认证令牌',
  
  // 授权错误
  PERMISSION_001: '权限不足，无法访问该资源',
  
  // 验证错误
  VALIDATION_001: '数据验证失败',
  VALIDATION_002: '必填字段不能为空',
  VALIDATION_003: '字段格式错误',
  
  // 数据库错误
  DATABASE_001: '数据库操作失败',
  DATABASE_002: '数据重复',
  
  // 网络错误
  NETWORK_001: '网络连接失败，请检查网络设置',
  NETWORK_002: '请求超时，请稍后重试',
  
  // 服务错误
  SERVICE_001: '服务内部错误，请稍后重试',
  
  // 资源错误
  RESOURCE_001: '请求的资源不存在',
  RESOURCE_002: '资源冲突',
  
  // 配置错误
  CONFIG_001: '配置参数错误',
  
  // 外部API错误
  EXTERNAL_001: '外部服务调用失败',
  
  // 系统错误
  SYSTEM_001: '系统错误，请联系管理员'
};

class ErrorService {
  /**
   * 处理API错误响应
   * @param {Object} error - 错误对象
   * @returns {Object} 标准化的错误对象
   */
  handleApiError(error) {
    let normalizedError = {
      code: 'SYSTEM_001',
      message: '未知错误',
      details: '',
      field: '',
      context: {
        request_id: this.generateRequestId(),
        timestamp: new Date().toISOString(),
        path: error.config?.url || ''
      }
    };

    // 处理HTTP错误
    if (error.response) {
      const { status, data } = error.response;
      
      // 处理后端返回的标准错误格式
      if (data.error) {
        normalizedError = {
          ...normalizedError,
          code: data.error.code || this.getCodeFromStatus(status),
          message: data.error.message || ERROR_CODES[data.error.code] || '请求失败',
          details: data.error.details || '',
          field: data.error.field || '',
          context: {
            ...normalizedError.context,
            ...data.error.context
          }
        };
      } else {
        // 处理旧格式错误响应
        normalizedError = {
          ...normalizedError,
          code: this.getCodeFromStatus(status),
          message: data.detail || data.message || this.getMessageFromStatus(status),
          details: JSON.stringify(data),
          context: {
            ...normalizedError.context,
            status
          }
        };
      }
    } 
    // 处理网络错误
    else if (error.request) {
      normalizedError = {
        ...normalizedError,
        code: 'NETWORK_001',
        message: ERROR_CODES.NETWORK_001,
        details: '无法连接到服务器',
        context: {
          ...normalizedError.context,
          error: error.message
        }
      };
    }
    // 处理请求配置错误
    else {
      normalizedError = {
        ...normalizedError,
        code: 'CONFIG_001',
        message: '请求配置错误',
        details: error.message,
        context: {
          ...normalizedError.context,
          error: error.message
        }
      };
    }

    // 记录错误日志
    this.logError(normalizedError);
    
    return normalizedError;
  }

  /**
   * 从HTTP状态码获取错误码
   * @param {number} status - HTTP状态码
   * @returns {string} 错误码
   */
  getCodeFromStatus(status) {
    switch (status) {
      case 400:
        return 'VALIDATION_001';
      case 401:
        return 'AUTH_001';
      case 403:
        return 'PERMISSION_001';
      case 404:
        return 'RESOURCE_001';
      case 409:
        return 'RESOURCE_002';
      case 422:
        return 'VALIDATION_001';
      case 429:
        return 'NETWORK_002';
      case 500:
        return 'SERVICE_001';
      default:
        return 'SYSTEM_001';
    }
  }

  /**
   * 从HTTP状态码获取错误消息
   * @param {number} status - HTTP状态码
   * @returns {string} 错误消息
   */
  getMessageFromStatus(status) {
    switch (status) {
      case 400:
        return '请求参数错误';
      case 401:
        return '认证失败，请重新登录';
      case 403:
        return '权限不足，无法访问该资源';
      case 404:
        return '请求的资源不存在';
      case 409:
        return '资源冲突';
      case 422:
        return '数据验证失败';
      case 429:
        return '请求过于频繁，请稍后再试';
      case 500:
        return '服务器内部错误，请稍后重试';
      default:
        return '请求失败，请稍后重试';
    }
  }

  /**
   * 生成请求ID
   * @returns {string} 请求ID
   */
  generateRequestId() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }

  /**
   * 记录错误日志
   * @param {Object} error - 错误对象
   */
  logError(error) {
    console.error('Error:', error);
    
    // 在开发环境下显示详细错误信息
    if (import.meta.env.DEV) {
      console.error('Error Details:', error.details);
    }
    
    // 可以在这里添加错误监控服务的集成
    // 例如：Sentry.captureException(error);
  }

  /**
   * 报告错误
   * @param {Object} error - 错误对象
   * @param {Object} context - 错误上下文
   * @returns {Promise} 报告结果
   */
  async reportError(error, context = {}) {
    try {
      // 这里可以实现错误报告逻辑
      // 例如：发送错误到后端错误监控服务
      console.log('Reporting error:', error, context);
      
      // 模拟错误报告
      return {
        success: true,
        reportId: this.generateRequestId()
      };
    } catch (reportError) {
      console.error('Error reporting failed:', reportError);
      return {
        success: false,
        error: reportError.message
      };
    }
  }

  /**
   * 显示错误提示
   * @param {Object} error - 错误对象
   * @param {Object} options - 选项
   */
  showError(error, options = {}) {
    const { 
      type = 'error',
      title = '错误',
      duration = 3000,
      showDetails = import.meta.env.DEV
    } = options;
    
    // 这里可以集成通知组件
    // 例如：useNotification.getState().show({
    //   type,
    //   title,
    //   message: error.message,
    //   duration,
    //   showDetails: showDetails && error.details
    // });
    
    // 临时实现
    alert(`${title}: ${error.message}`);
    if (showDetails && error.details) {
      console.error('Error Details:', error.details);
    }
  }
}

// 导出单例实例
export default new ErrorService();
