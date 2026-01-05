import axios from 'axios';
import { showToast, showSuccess, showError, showWarning } from '../components/UI';
import useAuthStore from '../stores/authStore';

// Create axios instance
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request timestamp for debugging
    if (import.meta.env.DEV) {
      config.metadata = { startTime: new Date() };
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Calculate request duration in development
    if (import.meta.env.DEV && response.config.metadata?.startTime) {
      const duration = new Date() - response.config.metadata.startTime;
      console.log(`API Request: ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`);
    }

    return response;
  },
  (error) => {
    const { response, config } = error;

    // Handle different error scenarios
    if (response) {
      const { status, data } = response;

      switch (status) {
        case 401:
          // Unauthorized - clear auth and redirect to login
          useAuthStore.getState().logout();
          showError('登录已过期，请重新登录');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          break;

        case 403:
          showError('权限不足，无法访问该资源');
          break;

        case 404:
          showError('请求的资源不存在');
          break;

        case 422:
          // Validation errors
          if (data?.detail) {
            if (Array.isArray(data.detail)) {
              data.detail.forEach(err => showError(err.msg || '验证错误'));
            } else {
              showError(data.detail);
            }
          }
          break;

        case 429:
          showWarning('请求过于频繁，请稍后再试');
          break;

        case 500:
          showError('服务器内部错误，请稍后重试');
          break;

        default:
          showError(data?.message || '请求失败，请稍后重试');
      }
    } else if (error.request) {
      // Network error
      showError('网络连接失败，请检查网络设置');
    } else {
      // Other errors
      showError('请求配置错误');
    }

    return Promise.reject(error);
  }
);

export default apiClient;