import { request, checkNetworkConnection, delay, retry, requestWithRetry } from './apiUtils';
import { getAuthToken, setAuthToken, removeAuthToken, isAuthenticated } from './authUtils';

class APIManager {
  constructor() {
    this.baseURL = '/api';
    this.timeout = 30000;
    this.maxRetries = 3;
    this.retryDelay = 1000;
  }

  setConfig(config) {
    this.baseURL = config.baseURL || this.baseURL;
    this.timeout = config.timeout || this.timeout;
    this.maxRetries = config.maxRetries || this.maxRetries;
    this.retryDelay = config.retryDelay || this.retryDelay;
  }

  async request(endpoint, options = {}) {
    const config = {
      ...options,
      timeout: options.timeout || this.timeout
    };
    return request(endpoint, config);
  }

  async requestWithRetry(endpoint, options = {}) {
    const config = {
      ...options,
      maxRetries: options.maxRetries || this.maxRetries,
      initialDelay: options.initialDelay || this.retryDelay
    };
    return requestWithRetry(endpoint, config);
  }

  async get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  async post(endpoint, data, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', data });
  }

  async put(endpoint, data, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', data });
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }

  async patch(endpoint, data, options = {}) {
    return this.request(endpoint, { ...options, method: 'PATCH', data });
  }
}

class AuthManager {
  constructor() {
    this.token = null;
    this.loadToken();
  }

  loadToken() {
    this.token = getAuthToken();
  }

  saveToken(token) {
    this.token = token;
    setAuthToken(token);
  }

  removeToken() {
    this.token = null;
    removeAuthToken();
  }

  getToken() {
    return this.token;
  }

  isLoggedIn() {
    return isAuthenticated();
  }

  logout() {
    this.removeToken();
  }
}

class NetworkManager {
  constructor() {
    this.isOnline = true;
    this.checkInterval = null;
  }

  async checkConnection() {
    this.isOnline = await checkNetworkConnection();
    return this.isOnline;
  }

  startMonitoring(intervalMs = 30000) {
    if (this.checkInterval) {
      return;
    }
    this.checkInterval = setInterval(() => {
      this.checkConnection();
    }, intervalMs);
  }

  stopMonitoring() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }

  async waitForConnection(timeoutMs = 60000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeoutMs) {
      if (await this.checkConnection()) {
        return true;
      }
      await delay(1000);
    }
    return false;
  }
}

class RetryManager {
  constructor() {
    this.defaultMaxRetries = 3;
    this.defaultDelay = 1000;
  }

  async execute(fn, options = {}) {
    const maxRetries = options.maxRetries || this.defaultMaxRetries;
    const delayMs = options.delay || this.defaultDelay;
    return retry(fn, maxRetries, delayMs);
  }

  async executeWithBackoff(fn, options = {}) {
    const maxRetries = options.maxRetries || this.defaultMaxRetries;
    const initialDelay = options.initialDelay || this.defaultDelay;
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === maxRetries - 1) {
          throw error;
        }
        const delayTime = initialDelay * Math.pow(2, i);
        await delay(delayTime);
      }
    }
  }
}

class UtilityManager {
  static delay(ms) {
    return delay(ms);
  }

  static formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');

    return format
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds);
  }

  static formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  static debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  static throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  static generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  static deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  static isEmpty(value) {
    if (value === null || value === undefined) return true;
    if (typeof value === 'string') return value.trim().length === 0;
    if (Array.isArray(value)) return value.length === 0;
    if (typeof value === 'object') return Object.keys(value).length === 0;
    return false;
  }

  static sanitizeInput(input) {
    if (typeof input !== 'string') return input;
    return input
      .replace(/[<>]/g, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+=/gi, '');
  }
}

class UnifiedManager {
  constructor() {
    this.api = new APIManager();
    this.auth = new AuthManager();
    this.network = new NetworkManager();
    this.retry = new RetryManager();
    this.utils = UtilityManager;
  }

  setAPIConfig(config) {
    this.api.setConfig(config);
  }

  async initialize() {
    await this.network.checkConnection();
    this.network.startMonitoring();
  }

  destroy() {
    this.network.stopMonitoring();
  }
}

const unifiedManager = new UnifiedManager();

export default unifiedManager;
export { APIManager, AuthManager, NetworkManager, RetryManager, UtilityManager };
