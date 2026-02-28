/**
 * 能力中心API客户端
 *
 * 提供与后端能力中心API的交互功能
 */
import apiClient from './apiClient';

const BASE_URL = '/api/v1/capability-center';

/**
 * 能力中心API
 */
export const capabilityCenterApi = {
  /**
   * 获取能力列表
   *
   * @param {Object} params - 查询参数
   * @param {string} params.type - 类型筛选: tool/skill/all
   * @param {string} params.source - 来源筛选: official/user/marketplace
   * @param {string} params.status - 状态筛选: active/disabled
   * @param {string} params.category - 分类筛选
   * @param {string} params.search - 搜索关键词
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise<Object>} 能力列表响应
   */
  async getCapabilities(params = {}) {
    const queryParams = new URLSearchParams();

    if (params.type) queryParams.append('type', params.type);
    if (params.source) queryParams.append('source', params.source);
    if (params.status) queryParams.append('status', params.status);
    if (params.category) queryParams.append('category', params.category);
    if (params.search) queryParams.append('search', params.search);
    if (params.page) queryParams.append('page', params.page);
    if (params.page_size) queryParams.append('page_size', params.page_size);

    const url = `${BASE_URL}/capabilities?${queryParams.toString()}`;
    const response = await apiClient.get(url);
    return response.data;
  },

  /**
   * 获取能力分类列表
   *
   * @returns {Promise<Object>} 分类列表响应
   */
  async getCategories() {
    const response = await apiClient.get(`${BASE_URL}/capabilities/categories`);
    return response.data;
  },

  /**
   * 启用/禁用能力
   *
   * @param {string} type - 能力类型: skill/tool
   * @param {number} id - 能力ID
   * @param {boolean} enabled - 是否启用
   * @returns {Promise<Object>} 操作响应
   */
  async toggleCapability(type, id, enabled) {
    const response = await apiClient.post(
      `${BASE_URL}/capabilities/${type}/${id}/toggle`,
      { enabled }
    );
    return response.data;
  },

  /**
   * 删除能力
   *
   * @param {string} type - 能力类型: skill/tool
   * @param {number} id - 能力ID
   * @returns {Promise<Object>} 操作响应
   */
  async deleteCapability(type, id) {
    const response = await apiClient.delete(
      `${BASE_URL}/capabilities/${type}/${id}`
    );
    return response.data;
  },

  /**
   * 获取智能体的能力分配
   *
   * @param {number} agentId - 智能体ID
   * @returns {Promise<Object>} 能力分配响应
   */
  async getAgentCapabilities(agentId) {
    const response = await apiClient.get(
      `${BASE_URL}/agents/${agentId}/capabilities`
    );
    return response.data;
  },

  /**
   * 为智能体分配能力
   *
   * @param {number} agentId - 智能体ID
   * @param {Object} assignment - 分配信息
   * @param {number} assignment.capability_id - 能力ID
   * @param {string} assignment.capability_type - 能力类型: skill/tool
   * @param {number} assignment.priority - 优先级
   * @param {boolean} assignment.enabled - 是否启用
   * @param {Object} assignment.config - 配置信息
   * @returns {Promise<Object>} 操作响应
   */
  async assignCapabilityToAgent(agentId, assignment) {
    const response = await apiClient.post(
      `${BASE_URL}/agents/${agentId}/capabilities/assign`,
      assignment
    );
    return response.data;
  },

  /**
   * 从智能体移除能力
   *
   * @param {number} agentId - 智能体ID
   * @param {string} capabilityType - 能力类型: skill/tool
   * @param {number} capabilityId - 能力ID
   * @returns {Promise<Object>} 操作响应
   */
  async removeCapabilityFromAgent(agentId, capabilityType, capabilityId) {
    const response = await apiClient.post(
      `${BASE_URL}/agents/${agentId}/capabilities/remove`,
      null,
      {
        params: {
          capability_type: capabilityType,
          capability_id: capabilityId
        }
      }
    );
    return response.data;
  }
};

export default capabilityCenterApi;
