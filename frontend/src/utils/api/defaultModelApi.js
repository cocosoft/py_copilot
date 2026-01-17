import { request } from '../apiUtils';

/**
 * 默认模型管理API
 * 提供全局和场景默认模型的CRUD操作
 */
const defaultModelApi = {
  
  /**
   * 获取所有默认模型配置
   * @param {Object} params - 查询参数
   * @param {string} params.scope - 作用域：'global' 或 'scene'
   * @param {string} params.scene - 场景名称
   * @param {boolean} params.is_active - 是否激活
   * @param {number} params.skip - 跳过数量
   * @param {number} params.limit - 限制数量
   */
  async getDefaultModels(params = {}) {
    const endpoint = '/v1/default-models';
    const queryParams = new URLSearchParams();
    
    if (params.scope) queryParams.append('scope', params.scope);
    if (params.scene) queryParams.append('scene', params.scene);
    if (params.is_active !== undefined) queryParams.append('is_active', params.is_active);
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    
    const url = queryParams.toString() ? `${endpoint}?${queryParams.toString()}` : endpoint;
    return request(url, { method: 'GET' });
  },

  /**
   * 获取全局默认模型
   */
  async getGlobalDefaultModel() {
    const endpoint = '/v1/default-models/global';
    return request(endpoint, { method: 'GET' });
  },

  /**
   * 获取指定场景的默认模型
   * @param {string} scene - 场景名称
   */
  async getSceneDefaultModel(scene) {
    const endpoint = `/v1/default-models/scene/${encodeURIComponent(scene)}`;
    return request(endpoint, { method: 'GET' });
  },

  /**
   * 设置全局默认模型
   * @param {Object} data - 默认模型数据
   * @param {number} data.model_id - 模型ID
   * @param {number} data.fallback_model_id - 备选模型ID（可选）
   */
  async setGlobalDefaultModel(data) {
    const endpoint = '/v1/default-models/set-global';
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    });
  },

  /**
   * 设置场景默认模型
   * @param {Object} data - 默认模型数据
   * @param {string} data.scene - 场景名称
   * @param {number} data.model_id - 模型ID
   * @param {number} data.priority - 优先级
   * @param {number} data.fallback_model_id - 备选模型ID（可选）
   */
  async setSceneDefaultModel(data) {
    const endpoint = '/v1/default-models/set-scene';
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    });
  },

  /**
   * 删除默认模型配置
   * @param {number} defaultModelId - 默认模型配置ID
   */
  async deleteDefaultModel(defaultModelId) {
    const endpoint = `/v1/default-models/${defaultModelId}`;
    return request(endpoint, { method: 'DELETE' });
  },

  /**
   * 更新默认模型配置
   * @param {number} defaultModelId - 默认模型配置ID
   * @param {Object} data - 更新数据
   */
  async updateDefaultModel(defaultModelId, data) {
    const endpoint = `/v1/default-models/${defaultModelId}`;
    return request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    });
  },

  /**
   * 获取模型性能统计
   * @param {Object} params - 查询参数
   * @param {number} params.model_id - 模型ID
   * @param {string} params.scene - 场景名称
   */
  async getModelPerformance(params = {}) {
    const endpoint = '/v1/default-models/performance';
    const queryParams = new URLSearchParams();
    
    if (params.model_id) queryParams.append('model_id', params.model_id);
    if (params.scene) queryParams.append('scene', params.scene);
    
    const url = queryParams.toString() ? `${endpoint}?${queryParams.toString()}` : endpoint;
    return request(url, { method: 'GET' });
  },

  /**
   * 获取模型反馈统计
   * @param {Object} params - 查询参数
   * @param {number} params.model_id - 模型ID
   * @param {string} params.scene - 场景名称
   */
  async getModelFeedback(params = {}) {
    const endpoint = '/v1/default-models/feedback';
    const queryParams = new URLSearchParams();
    
    if (params.model_id) queryParams.append('model_id', params.model_id);
    if (params.scene) queryParams.append('scene', params.scene);
    
    const url = queryParams.toString() ? `${endpoint}?${queryParams.toString()}` : endpoint;
    return request(url, { method: 'GET' });
  },

  /**
   * 提交模型反馈
   * @param {Object} data - 反馈数据
   * @param {number} data.model_id - 模型ID
   * @param {string} data.scene - 场景名称
   * @param {string} data.user_id - 用户ID（可选）
   * @param {number} data.rating - 评分（1-5）
   * @param {string} data.feedback - 反馈内容（可选）
   * @param {Object} data.usage_context - 使用上下文（可选）
   */
  async submitModelFeedback(data) {
    const endpoint = '/v1/default-models/feedback';
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    });
  },

  /**
   * 获取推荐的默认模型列表
   * @param {Object} params - 查询参数
   * @param {string} params.scene - 场景名称
   * @param {number} params.limit - 限制数量
   */
  async getRecommendedModels(params = {}) {
    const endpoint = '/v1/default-models/recommend';
    const queryParams = new URLSearchParams();
    
    if (params.scene) queryParams.append('scene', params.scene);
    if (params.limit) queryParams.append('limit', params.limit);
    
    const url = queryParams.toString() ? `${endpoint}?${queryParams.toString()}` : endpoint;
    return request(url, { method: 'GET' });
  },

  /**
   * 测试默认模型配置
   * @param {Object} data - 测试数据
   * @param {string} data.scene - 场景名称
   * @param {string} data.test_prompt - 测试提示
   */
  async testDefaultModelConfiguration(data) {
    const endpoint = '/v1/default-models/test';
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    });
  },

  /**
   * 批量设置默认模型
   * @param {Array} configs - 默认模型配置数组
   */
  async batchSetDefaultModels(configs) {
    const endpoint = '/v1/default-models/batch-set';
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify({ configs }),
      headers: { 'Content-Type': 'application/json' }
    });
  },

  /**
   * 导出默认模型配置
   * @param {Object} params - 导出参数
   */
  async exportDefaultModels(params = {}) {
    const endpoint = '/v1/default-models/export';
    const queryParams = new URLSearchParams();
    
    if (params.scope) queryParams.append('scope', params.scope);
    if (params.format) queryParams.append('format', params.format);
    
    const url = queryParams.toString() ? `${endpoint}?${queryParams.toString()}` : endpoint;
    return request(url, { method: 'GET', responseType: 'blob' });
  },

  /**
   * 导入默认模型配置
   * @param {FormData} formData - 包含文件和其他参数
   */
  async importDefaultModels(formData) {
    const endpoint = '/v1/default-models/import';
    return request(endpoint, {
      method: 'POST',
      body: formData
    });
  }
};

export default defaultModelApi;
