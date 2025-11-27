// API基础配置 - 使用相对路径，让Vite代理处理请求
export const API_BASE_URL = '/api';

// 本地存储前缀
export const STORAGE_PREFIX = 'llm_admin_';

// 通用请求函数
export const request = async (endpoint, options = {}) => {
  console.log('🚀 API请求:', `${API_BASE_URL}${endpoint}`, options);
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
    credentials: 'include', // 包含cookies
  };
  
  try {
    // 构建完整URL
    const url = `${API_BASE_URL}${endpoint}`;
    console.log('🚀 请求URL:', url);
    
    // 发送请求
    const response = await fetch(url, mergedOptions);
    
    // 检查响应状态
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail || errorData.message || `HTTP错误! 状态: ${response.status}`;
      console.error('❌ API响应错误:', response.status, errorMessage);
      throw new Error(errorMessage);
    }
    
    // 检查响应内容类型
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('✅ API请求成功，返回数据:', data);
      return data;
    } else {
      const text = await response.text();
      console.log('✅ API请求成功，返回文本:', text);
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
    const response = await fetch('/api/health', { method: 'HEAD', cache: 'no-cache' });
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