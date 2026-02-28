/**
 * MCP 服务 API
 * 
 * 提供 MCP 配置管理的前端 API 调用。
 */

import api from './apiClient';

const MCP_BASE_URL = '/api/v1/mcp';

/**
 * MCP 服务对象
 */
export const mcpService = {
  // ==================== Server Config APIs ====================
  
  /**
   * 获取服务端配置列表
   * 
   * @returns {Promise<Object>} 配置列表响应
   */
  async getServerConfigs() {
    const response = await api.get(`${MCP_BASE_URL}/servers`);
    return response.data;
  },

  /**
   * 获取单个服务端配置
   * 
   * @param {number} id - 配置ID
   * @returns {Promise<Object>} 配置详情响应
   */
  async getServerConfig(id) {
    const response = await api.get(`${MCP_BASE_URL}/servers/${id}`);
    return response.data;
  },

  /**
   * 创建服务端配置
   * 
   * @param {Object} config - 配置数据
   * @returns {Promise<Object>} 创建响应
   */
  async createServerConfig(config) {
    const response = await api.post(`${MCP_BASE_URL}/servers`, config);
    return response.data;
  },

  /**
   * 更新服务端配置
   * 
   * @param {number} id - 配置ID
   * @param {Object} config - 更新数据
   * @returns {Promise<Object>} 更新响应
   */
  async updateServerConfig(id, config) {
    const response = await api.put(`${MCP_BASE_URL}/servers/${id}`, config);
    return response.data;
  },

  /**
   * 删除服务端配置
   * 
   * @param {number} id - 配置ID
   * @returns {Promise<Object>} 删除响应
   */
  async deleteServerConfig(id) {
    const response = await api.delete(`${MCP_BASE_URL}/servers/${id}`);
    return response.data;
  },

  // ==================== Client Config APIs ====================
  
  /**
   * 获取客户端配置列表
   * 
   * @returns {Promise<Object>} 配置列表响应
   */
  async getClientConfigs() {
    const response = await api.get(`${MCP_BASE_URL}/clients`);
    return response.data;
  },

  /**
   * 获取单个客户端配置
   * 
   * @param {number} id - 配置ID
   * @returns {Promise<Object>} 配置详情响应
   */
  async getClientConfig(id) {
    const response = await api.get(`${MCP_BASE_URL}/clients/${id}`);
    return response.data;
  },

  /**
   * 创建客户端配置
   * 
   * @param {Object} config - 配置数据
   * @returns {Promise<Object>} 创建响应
   */
  async createClientConfig(config) {
    const response = await api.post(`${MCP_BASE_URL}/clients`, config);
    return response.data;
  },

  /**
   * 更新客户端配置
   * 
   * @param {number} id - 配置ID
   * @param {Object} config - 更新数据
   * @returns {Promise<Object>} 更新响应
   */
  async updateClientConfig(id, config) {
    const response = await api.put(`${MCP_BASE_URL}/clients/${id}`, config);
    return response.data;
  },

  /**
   * 删除客户端配置
   * 
   * @param {number} id - 配置ID
   * @returns {Promise<Object>} 删除响应
   */
  async deleteClientConfig(id) {
    const response = await api.delete(`${MCP_BASE_URL}/clients/${id}`);
    return response.data;
  },

  /**
   * 连接客户端
   * 
   * @param {number} id - 客户端配置ID
   * @returns {Promise<Object>} 连接响应
   */
  async connectClient(id) {
    const response = await api.post(`${MCP_BASE_URL}/clients/${id}/connect`);
    return response.data;
  },

  /**
   * 断开客户端连接
   * 
   * @param {number} id - 客户端配置ID
   * @returns {Promise<Object>} 断开响应
   */
  async disconnectClient(id) {
    const response = await api.post(`${MCP_BASE_URL}/clients/${id}/disconnect`);
    return response.data;
  },

  // ==================== Tool Management APIs ====================
  
  /**
   * 获取 MCP 工具列表
   * 
   * @returns {Promise<Object>} 工具列表响应
   */
  async getTools() {
    const response = await api.get(`${MCP_BASE_URL}/tools`);
    return response.data;
  },
  
  /**
   * 获取 MCP 工具列表（别名）
   * 
   * @returns {Promise<Object>} 工具列表响应
   */
  async getMCPTools() {
    const response = await api.get(`${MCP_BASE_URL}/tools`);
    return response.data;
  },

  // ==================== Status API ====================
  
  /**
   * 获取 MCP 整体状态
   * 
   * @returns {Promise<Object>} 状态响应
   */
  async getStatus() {
    const response = await api.get(`${MCP_BASE_URL}/status`);
    return response.data;
  },

  // ==================== Marketplace APIs ====================

  /**
   * 获取 MCP 市场列表
   *
   * @returns {Promise<Object>} 市场列表响应
   */
  async getMarketplaceList() {
    const response = await api.get(`${MCP_BASE_URL}/marketplace/list`);
    return response.data;
  },

  /**
   * 获取 MCP 市场服务列表
   *
   * @param {string} source - 市场源 (mcpmarket, modelscope)
   * @param {string} category - 可选的类别筛选
   * @returns {Promise<Object>} 服务列表响应
   */
  async getMarketplaceServers(source = 'mcpmarket', category = null) {
    const params = { source };
    if (category) params.category = category;
    const response = await api.get(`${MCP_BASE_URL}/marketplace/servers`, { params });
    return response.data;
  },

  /**
   * 获取 MCP 市场服务类别
   *
   * @param {string} source - 市场源
   * @returns {Promise<Object>} 类别列表响应
   */
  async getMarketplaceCategories(source = 'mcpmarket') {
    const response = await api.get(`${MCP_BASE_URL}/marketplace/categories`, {
      params: { source }
    });
    return response.data;
  },

  /**
   * 从 MCP 市场安装服务
   *
   * @param {string} serverId - 服务ID
   * @param {string} source - 市场源
   * @param {string} name - 可选的自定义名称
   * @returns {Promise<Object>} 安装响应
   */
  async installMarketplaceServer(serverId, source = 'mcpmarket', name = null) {
    const params = { server_id: serverId, source };
    if (name) params.name = name;
    const response = await api.post(`${MCP_BASE_URL}/marketplace/install`, null, { params });
    return response.data;
  },

  /**
   * 添加自定义 MCP 市场
   *
   * @param {Object} marketplaceData - 市场配置数据
   * @returns {Promise<Object>} 添加响应
   */
  async addCustomMarketplace(marketplaceData) {
    const response = await api.post(`${MCP_BASE_URL}/marketplace/custom`, marketplaceData);
    return response.data;
  },

  /**
   * 移除自定义 MCP 市场
   *
   * @param {string} marketplaceId - 市场ID
   * @returns {Promise<Object>} 移除响应
   */
  async removeCustomMarketplace(marketplaceId) {
    const response = await api.delete(`${MCP_BASE_URL}/marketplace/custom/${marketplaceId}`);
    return response.data;
  }
};

export default mcpService;
