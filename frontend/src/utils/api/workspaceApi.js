/**
 * 工作空间API接口
 *
 * 提供工作空间的增删改查和切换功能
 */

import api from '../api';

/**
 * 获取用户的工作空间列表
 *
 * @returns {Promise<Object>} 工作空间列表
 */
export const getWorkspaces = async () => {
    const response = await api.get('/api/v1/workspaces');
    return response.data;
};

/**
 * 获取当前工作空间
 *
 * @returns {Promise<Object>} 当前工作空间信息
 */
export const getCurrentWorkspace = async () => {
    const response = await api.get('/api/v1/workspaces/current/default');
    return response.data;
};

/**
 * 创建工作空间
 *
 * @param {Object} data - 工作空间数据
 * @param {string} data.name - 工作空间名称
 * @param {string} [data.description] - 工作空间描述
 * @param {number} [data.max_storage_bytes] - 最大存储空间（字节）
 * @returns {Promise<Object>} 创建的工作空间
 */
export const createWorkspace = async (data) => {
    const response = await api.post('/api/v1/workspaces', data);
    return response.data;
};

/**
 * 更新工作空间
 *
 * @param {number} workspaceId - 工作空间ID
 * @param {Object} data - 更新数据
 * @returns {Promise<Object>} 更新后的工作空间
 */
export const updateWorkspace = async (workspaceId, data) => {
    const response = await api.put(`/api/v1/workspaces/${workspaceId}`, data);
    return response.data;
};

/**
 * 删除工作空间
 *
 * @param {number} workspaceId - 工作空间ID
 * @returns {Promise<void>}
 */
export const deleteWorkspace = async (workspaceId) => {
    await api.delete(`/api/v1/workspaces/${workspaceId}`);
};

/**
 * 设置默认工作空间
 *
 * @param {number} workspaceId - 工作空间ID
 * @returns {Promise<Object>} 新的默认工作空间
 */
export const setDefaultWorkspace = async (workspaceId) => {
    const response = await api.post(`/api/v1/workspaces/${workspaceId}/set-default`);
    return response.data;
};

/**
 * 切换当前工作空间
 *
 * @param {number} workspaceId - 目标工作空间ID
 * @returns {Promise<Object>} 切换后的工作空间
 */
export const switchWorkspace = async (workspaceId) => {
    const response = await api.post(`/api/v1/workspaces/switch/${workspaceId}`);
    return response.data;
};

/**
 * 获取工作空间存储使用情况
 *
 * @param {number} workspaceId - 工作空间ID
 * @returns {Promise<Object>} 存储使用情况
 */
export const getStorageUsage = async (workspaceId) => {
    const response = await api.get(`/api/v1/workspaces/${workspaceId}/storage`);
    return response.data;
};

export default {
    getWorkspaces,
    getCurrentWorkspace,
    createWorkspace,
    updateWorkspace,
    deleteWorkspace,
    setDefaultWorkspace,
    switchWorkspace,
    getStorageUsage
};
