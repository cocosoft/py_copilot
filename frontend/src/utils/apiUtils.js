// API基础配置 - 使用相对路径，让Vite代理处理请求
export const API_BASE_URL = '/api';

// 本地存储前缀
export const STORAGE_PREFIX = 'llm_admin_';

// 通用请求函数
export const request = async (endpoint, options = {}) => {
  
  // 对于FormData，不设置默认的Content-Type，让浏览器自动处理
  const isFormData = options.body instanceof FormData;
  
  // 准备默认选项
  let defaultHeaders = {};
  if (!isFormData) {
    defaultHeaders['Content-Type'] = 'application/json';
  }
  
  const defaultOptions = {
    headers: defaultHeaders,
  };
  
  // 合并选项
  const mergedOptions = {
    ...defaultOptions,
    ...options,
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
    // 构建完整URL
    const url = `${API_BASE_URL}${endpoint}`;
    
    // 发送请求
    const response = await fetch(url, mergedOptions);
    
    // 检查响应状态
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail || errorData.message || `HTTP错误! 状态: ${response.status}`;
      console.error('❌ API响应错误:', response.status, errorMessage);
      throw new Error(errorMessage);
    }
    
    // 特别处理204 No Content（DELETE请求的标准响应）
    if (response.status === 204) {
      return null; // 204响应没有内容，返回null
    }
    
    // 检查响应内容类型
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      return data;
    } else {
      const text = await response.text();
      return text;
    }
  } catch (error) {
    console.error('❌ API请求异常:', error);
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