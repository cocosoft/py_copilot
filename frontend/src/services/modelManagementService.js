/**
 * 模型管理服务
 * 提供模型管理相关的API调用
 */

import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * 模型管理API
 */
export const modelManagementService = {
  /**
   * 获取模型列表
   */
  getModels: async (params = {}) => {
    const response = await apiClient.get('/api/v1/model-management/models', { params });
    return response.data;
  },

  /**
   * 获取模型详情
   */
  getModel: async (id) => {
    const response = await apiClient.get(`/api/v1/model-management/models/${id}`);
    return response.data;
  },

  /**
   * 创建模型
   */
  createModel: async (data) => {
    const response = await apiClient.post('/api/v1/model-management/models', data);
    return response.data;
  },

  /**
   * 更新模型
   */
  updateModel: async (id, data) => {
    const response = await apiClient.put(`/api/v1/model-management/models/${id}`, data);
    return response.data;
  },

  /**
   * 删除模型
   */
  deleteModel: async (id) => {
    const response = await apiClient.delete(`/api/v1/model-management/models/${id}`);
    return response.data;
  },

  /**
   * 批量删除模型
   */
  batchDeleteModels: async (ids) => {
    const response = await apiClient.post('/api/v1/model-management/models/batch-delete', { ids });
    return response.data;
  },
};

/**
 * Webhook管理API
 */
export const webhookService = {
  /**
   * 获取Webhook列表
   */
  getWebhooks: async (params = {}) => {
    const response = await apiClient.get('/api/v1/model-management/webhooks', { params });
    return response.data;
  },

  /**
   * 获取Webhook详情
   */
  getWebhook: async (id) => {
    const response = await apiClient.get(`/api/v1/model-management/webhooks/${id}`);
    return response.data;
  },

  /**
   * 创建Webhook
   */
  createWebhook: async (data) => {
    const response = await apiClient.post('/api/v1/model-management/webhooks', data);
    return response.data;
  },

  /**
   * 更新Webhook
   */
  updateWebhook: async (id, data) => {
    const response = await apiClient.put(`/api/v1/model-management/webhooks/${id}`, data);
    return response.data;
  },

  /**
   * 删除Webhook
   */
  deleteWebhook: async (id) => {
    const response = await apiClient.delete(`/api/v1/model-management/webhooks/${id}`);
    return response.data;
  },

  /**
   * 获取Webhook投递记录
   */
  getWebhookDeliveries: async (webhookId, params = {}) => {
    const response = await apiClient.get(`/api/v1/model-management/webhooks/${webhookId}/deliveries`, { params });
    return response.data;
  },

  /**
   * 重试Webhook投递
   */
  retryWebhookDelivery: async (deliveryId) => {
    const response = await apiClient.post(`/api/v1/model-management/webhooks/deliveries/${deliveryId}/retry`);
    return response.data;
  },

  /**
   * 测试Webhook
   */
  testWebhook: async (id) => {
    const response = await apiClient.post(`/api/v1/model-management/webhooks/${id}/test`);
    return response.data;
  },
};

/**
 * 配置管理API
 */
export const configService = {
  /**
   * 获取配置列表
   */
  getConfigs: async (params = {}) => {
    const response = await apiClient.get('/api/v1/model-management/configs', { params });
    return response.data;
  },

  /**
   * 获取配置值
   */
  getConfig: async (key, params = {}) => {
    const response = await apiClient.get(`/api/v1/model-management/configs/${key}`, { params });
    return response.data;
  },

  /**
   * 创建配置
   */
  createConfig: async (data) => {
    const response = await apiClient.post('/api/v1/model-management/configs', data);
    return response.data;
  },

  /**
   * 更新配置
   */
  updateConfig: async (key, data) => {
    const response = await apiClient.put(`/api/v1/model-management/configs/${key}`, data);
    return response.data;
  },

  /**
   * 删除配置
   */
  deleteConfig: async (key) => {
    const response = await apiClient.delete(`/api/v1/model-management/configs/${key}`);
    return response.data;
  },

  /**
   * 获取配置历史
   */
  getConfigHistory: async (key, params = {}) => {
    const response = await apiClient.get(`/api/v1/model-management/configs/${key}/history`, { params });
    return response.data;
  },

  /**
   * 回滚配置
   */
  rollbackConfig: async (key, data) => {
    const response = await apiClient.post(`/api/v1/model-management/configs/${key}/rollback`, data);
    return response.data;
  },

  /**
   * 获取配置审计日志
   */
  getConfigAuditLogs: async (params = {}) => {
    const response = await apiClient.get('/api/v1/model-management/configs/audit-logs', { params });
    return response.data;
  },
};

/**
 * 生命周期管理API
 */
export const lifecycleService = {
  /**
   * 获取模型生命周期
   */
  getLifecycle: async (modelId) => {
    const response = await apiClient.get(`/api/v1/model-management/lifecycles/${modelId}`);
    return response.data;
  },

  /**
   * 请求状态变更
   */
  requestTransition: async (modelId, data) => {
    const response = await apiClient.post(`/api/v1/model-management/lifecycles/${modelId}/transition`, data);
    return response.data;
  },

  /**
   * 获取状态流转历史
   */
  getTransitionHistory: async (modelId, params = {}) => {
    const response = await apiClient.get(`/api/v1/model-management/lifecycles/${modelId}/history`, { params });
    return response.data;
  },

  /**
   * 获取待审批列表
   */
  getPendingApprovals: async (params = {}) => {
    const response = await apiClient.get('/api/v1/model-management/lifecycles/approvals', { params });
    return response.data;
  },

  /**
   * 审批状态变更
   */
  approveTransition: async (approvalId, data) => {
    const response = await apiClient.post(`/api/v1/model-management/lifecycles/approvals/${approvalId}/approve`, data);
    return response.data;
  },

  /**
   * 撤销审批请求
   */
  cancelApproval: async (approvalId) => {
    const response = await apiClient.post(`/api/v1/model-management/lifecycles/approvals/${approvalId}/cancel`);
    return response.data;
  },

  /**
   * 创建废弃预告
   */
  createDeprecation: async (modelId, data) => {
    const response = await apiClient.post(`/api/v1/model-management/lifecycles/${modelId}/deprecation`, data);
    return response.data;
  },

  /**
   * 获取废弃预告列表
   */
  getDeprecationNotices: async (params = {}) => {
    const response = await apiClient.get('/api/v1/model-management/lifecycles/deprecation-notices', { params });
    return response.data;
  },

  /**
   * 确认废弃预告
   */
  acknowledgeDeprecation: async (noticeId, data) => {
    const response = await apiClient.post(`/api/v1/model-management/lifecycles/deprecation-notices/${noticeId}/acknowledge`, data);
    return response.data;
  },
};

/**
 * 配额管理API
 */
export const quotaService = {
  /**
   * 获取用户配额
   */
  getQuota: async (userId, params = {}) => {
    const response = await apiClient.get(`/api/v1/model-management/quotas/${userId}`, { params });
    return response.data;
  },

  /**
   * 设置用户配额
   */
  setQuota: async (data) => {
    const response = await apiClient.post('/api/v1/model-management/quotas', data);
    return response.data;
  },

  /**
   * 更新用户配额
   */
  updateQuota: async (userId, data) => {
    const response = await apiClient.put(`/api/v1/model-management/quotas/${userId}`, data);
    return response.data;
  },

  /**
   * 记录配额使用
   */
  recordUsage: async (userId, data) => {
    const response = await apiClient.post(`/api/v1/model-management/quotas/${userId}/record`, data);
    return response.data;
  },

  /**
   * 获取配额使用历史
   */
  getQuotaHistory: async (userId, params = {}) => {
    const response = await apiClient.get(`/api/v1/model-management/quotas/${userId}/history`, { params });
    return response.data;
  },

  /**
   * 获取所有配额
   */
  getAllQuotas: async (params = {}) => {
    const response = await apiClient.get('/api/v1/model-management/quotas', { params });
    return response.data;
  },
};

export default {
  modelManagement: modelManagementService,
  webhook: webhookService,
  config: configService,
  lifecycle: lifecycleService,
  quota: quotaService,
};
