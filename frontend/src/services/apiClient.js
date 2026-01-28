import axios from 'axios';
import useAuthStore from '../stores/authStore';
import useErrorStore from '../stores/errorStore';
import errorService from './errorService';

// Create axios instance
const apiClient = axios.create({
  baseURL: '/api', // Use relative path to go through Vite proxy
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

    // Add request timestamp and ID for debugging
    const requestId = errorService.generateRequestId();
    config.headers['X-Request-ID'] = requestId;
    config.metadata = {
      startTime: new Date(),
      requestId
    };

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
    // 使用错误处理服务处理错误
    const normalizedError = useErrorStore.getState().handleApiError(error);
    
    // 特殊处理认证错误
    if (normalizedError.code === 'AUTH_001' || normalizedError.code === 'AUTH_002') {
      useAuthStore.getState().logout();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    return Promise.reject(normalizedError);
  }
);

export default apiClient;