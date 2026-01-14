// API基础配置 - 直接使用后端完整URL，绕过代理问题
export const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 本地存储前缀
export const STORAGE_PREFIX = 'llm_admin_';

// 导入认证工具函数
import { getAuthToken } from './authUtils';

// 通用请求函数
export const request = async (endpoint, options = {}) => {
  
  // 处理data属性，将其转换为body
  let body = options.body;
  if (options.data && !body) {
    body = JSON.stringify(options.data);
  }
  
  // 处理params参数，将其添加到URL中
  // 确保API_BASE_URL和endpoint之间只有一个斜杠
  let base = API_BASE_URL.replace(/\/$/, '');
  let url = `${base}${endpoint}`;
  if (options.params) {
    const params = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        params.append(key, value);
      }
    });
    const paramsString = params.toString();
    if (paramsString) {
      url += `?${paramsString}`;
    }
  }
  
  // 对于FormData，不设置默认的Content-Type，让浏览器自动处理
  const isFormData = body instanceof FormData;
  
  // 准备默认选项
  let defaultHeaders = {};
  if (!isFormData) {
    defaultHeaders['Content-Type'] = 'application/json';
  }
  
  // 添加认证令牌（如果存在）
  const authToken = getAuthToken();
  if (authToken) {
    defaultHeaders['Authorization'] = `Bearer ${authToken}`;
  }
  
  const defaultOptions = {
    headers: defaultHeaders,
  };
  
  // 合并选项
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    body, // 使用处理后的body
    credentials: 'include', // 包含cookies
  };
  
  // 特别处理headers：如果是FormData，确保不设置任何Content-Type
  if (isFormData) {
    mergedOptions.headers = { ...mergedOptions.headers };
    delete mergedOptions.headers['Content-Type'];
  } else {
    // 非FormData时正常合并headers
    mergedOptions.headers = {
      ...defaultOptions.headers,
      ...options.headers,
    };
  }
  
  try {

    // 发送请求
    const response = await fetch(url, mergedOptions);
    

    // 检查响应状态
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      // 提取错误信息
      let errorMessage;
      let statusCode = response.status;
      let responseText = '';
      
      if (errorData.detail) {
        // 如果detail存在，检查它是否是对象
        if (typeof errorData.detail === 'object') {
          // 如果detail是对象，提取其中的字段
          const detailObj = errorData.detail;
          // 优先使用detail中的message字段
          errorMessage = detailObj.message || 'API错误!';
          // 使用detail中的status_code
          statusCode = detailObj.status_code || response.status;
          // 使用detail中的response_text
          responseText = detailObj.response_text || '';
          
          // 如果有response_text且与message不同，则添加到错误消息中
          if (responseText && responseText !== detailObj.message) {
            errorMessage += `：${responseText}`;
          }
        } else {
          // 否则直接使用detail
          errorMessage = errorData.detail;
          // 使用errorData中的status_code和response_text
          statusCode = errorData.status_code || response.status;
          responseText = errorData.response_text || '';
        }
      } else {
        // 否则使用message或默认错误消息
        errorMessage = errorData.message || 'HTTP错误!';
        // 使用errorData中的status_code和response_text
        statusCode = errorData.status_code || response.status;
        responseText = errorData.response_text || '';
      }
      
      // 添加强制性的状态码信息
      errorMessage += ` 状态码: ${statusCode}`;
      
      // 创建错误对象
      const errorObj = new Error(errorMessage);
      
      // 在错误对象上添加状态码，以便更易于在客户端代码中检查
      errorObj.status = statusCode;
      
      // 特别处理422错误，获取所有可能的详细信息
      if (statusCode === 422 && responseText) {
        try {
          const errorData = JSON.parse(responseText);
          if (errorData.detail && Array.isArray(errorData.detail)) {
            const validationErrors = errorData.detail.map(err => 
              err.msg || (err.loc && err.msg ? `${err.loc.join('.')}: ${err.msg}` : JSON.stringify(err))
            ).join('; ');
            errorMessage += ` 验证错误: ${validationErrors}`;
          } else if (errorData.detail && typeof errorData.detail === 'string') {
            errorMessage += ` 详细信息: ${errorData.detail}`;
          } else if (errorData.errors) {
            const fieldErrors = Object.entries(errorData.errors)
              .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
              .join('; ');
            errorMessage += ` 字段错误: ${fieldErrors}`;
          }
        } catch (e) {
          // 如果无法解析响应文本，忽略此部分
        }
      }
      
      // 添加可选的响应文本信息（如果有且未包含在message中）
      if (responseText && !errorMessage.includes(responseText)) {
        errorMessage += ` 响应文本: ${responseText}`;
      }
      
      // 特别处理500错误，提供更详细的错误日志
      if (statusCode === 500) {
        console.error('❌ 服务器内部错误(500):', {
          status: statusCode,
          message: errorMessage,
          url: url,
          options: mergedOptions,
          response: errorData
        });
      } else {
        console.error('❌ API响应错误:', statusCode, errorMessage);
      }
      
      throw errorObj;
    }
    
    // 特别处理204 No Content（DELETE请求的标准响应）
    if (response.status === 204) {
      return null; // 204响应没有内容，返回null
    }
    
    // 特别处理responseType为blob的情况
    if (options.responseType === 'blob') {
      const blob = await response.blob();
      return blob;
    }
    
    // 检查响应内容类型
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      // 生产环境中移除调试日志
      // console.log('API响应数据:', JSON.stringify(data, null, 2));
      return data;
    } else {
      const text = await response.text();
      // 生产环境中移除调试日志
      // console.log('API响应文本:', text);
      return text;
    }
  } catch (error) {
    console.error('❌ API请求异常:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 检查网络连接
export const checkNetworkConnection = async () => {
  try {
    // 健康检查端点不需要/api前缀，直接访问根路径下的/health
    const response = await fetch('/health', { method: 'HEAD', cache: 'no-cache' });
    return response.ok;
  } catch {
    return false;
  }
};

// 延迟函数
export const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// 重试函数
export const retry = async (fn, maxRetries = 3, delayMs = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await delay(delayMs * Math.pow(2, i)); // 指数退避
    }
  }
};