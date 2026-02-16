import apiClient from '../services/apiClient';

const taskApi = {
  /**
   * 获取任务列表
   * @param {Object} params - 查询参数
   * @param {string} params.status - 任务状态筛选
   * @param {number} params.skip - 跳过数量
   * @param {number} params.limit - 返回数量
   * @returns {Promise<Array>} 任务列表
   */
  getTasks: async (params = {}) => {
    try {
      const response = await apiClient.get('/api/v1/tasks', { params });
      return response.data;
    } catch (error) {
      console.error('获取任务列表失败:', error);
      throw error;
    }
  },

  /**
   * 获取任务详情
   * @param {number} taskId - 任务ID
   * @returns {Promise<Object>} 任务详情
   */
  getTask: async (taskId) => {
    try {
      const response = await apiClient.get(`/api/v1/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      console.error('获取任务详情失败:', error);
      throw error;
    }
  },

  /**
   * 创建任务
   * @param {Object} taskData - 任务数据
   * @param {string} taskData.title - 任务标题
   * @param {string} taskData.description - 任务描述
   * @param {string} taskData.priority - 任务优先级
   * @returns {Promise<Object>} 创建的任务
   */
  createTask: async (taskData) => {
    try {
      const response = await apiClient.post('/api/v1/tasks', taskData);
      return response.data;
    } catch (error) {
      console.error('创建任务失败:', error);
      throw error;
    }
  },

  /**
   * 更新任务
   * @param {number} taskId - 任务ID
   * @param {Object} taskData - 更新的任务数据
   * @returns {Promise<Object>} 更新后的任务
   */
  updateTask: async (taskId, taskData) => {
    try {
      const response = await apiClient.put(`/api/v1/tasks/${taskId}`, taskData);
      return response.data;
    } catch (error) {
      console.error('更新任务失败:', error);
      throw error;
    }
  },

  /**
   * 删除任务
   * @param {number} taskId - 任务ID
   * @returns {Promise<Object>} 删除结果
   */
  deleteTask: async (taskId) => {
    try {
      const response = await apiClient.delete(`/api/v1/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      console.error('删除任务失败:', error);
      throw error;
    }
  },

  /**
   * 执行任务
   * @param {number} taskId - 任务ID
   * @returns {Promise<Object>} 执行结果
   */
  executeTask: async (taskId) => {
    try {
      const response = await apiClient.post(`/api/v1/tasks/${taskId}/execute`);
      return response.data;
    } catch (error) {
      console.error('执行任务失败:', error);
      throw error;
    }
  },

  /**
   * 获取任务进度
   * @param {number} taskId - 任务ID
   * @returns {Promise<Object>} 任务进度
   */
  getTaskProgress: async (taskId) => {
    try {
      const response = await apiClient.get(`/api/v1/tasks/${taskId}/progress`);
      return response.data;
    } catch (error) {
      console.error('获取任务进度失败:', error);
      throw error;
    }
  },

  /**
   * 取消任务
   * @param {number} taskId - 任务ID
   * @returns {Promise<Object>} 取消结果
   */
  cancelTask: async (taskId) => {
    try {
      const response = await apiClient.post(`/api/v1/tasks/${taskId}/cancel`);
      return response.data;
    } catch (error) {
      console.error('取消任务失败:', error);
      throw error;
    }
  }
};

export default taskApi;
