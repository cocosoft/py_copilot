// 对话相关API模块
import { request } from '../apiUtils';

// 对话API实现
export const conversationApi = {
  // 获取所有对话
  getAll: async () => {
    try {
      return await request('/v1/conversations', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取对话列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取单个对话
  getById: async (conversationId) => {
    try {
      return await request(`/v1/conversations/${conversationId}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取对话 ${conversationId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 创建对话
  create: async (conversationData) => {
    try {
      return await request('/v1/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(conversationData)
      });
    } catch (error) {
      console.error('创建对话失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 更新对话
  update: async (conversationId, updatedData) => {
    try {
      return await request(`/v1/conversations/${conversationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatedData)
      });
    } catch (error) {
      console.error(`更新对话 ${conversationId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 删除对话
  delete: async (conversationId) => {
    try {
      return await request(`/v1/conversations/${conversationId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除对话 ${conversationId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 批量删除对话
  batchDelete: async (conversationIds) => {
    try {
      return await request('/v1/conversations/batch-delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ids: conversationIds })
      });
    } catch (error) {
      console.error('批量删除对话失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取对话消息
  getMessages: async (conversationId, params = {}) => {
    try {
      const queryParams = new URLSearchParams(params).toString();
      const url = queryParams 
        ? `/v1/conversations/${conversationId}/messages?${queryParams}` 
        : `/v1/conversations/${conversationId}/messages`;
      
      return await request(url, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取对话 ${conversationId} 的消息失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 发送消息（核心功能）
  sendMessage: async (conversationId, messageData) => {
    try {
      // 通过API发送消息
      return await request(`/v1/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(messageData)
      });
    } catch (error) {
      console.error(`在对话 ${conversationId} 中发送消息失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 删除消息
  deleteMessage: async (conversationId, messageId) => {
    try {
      return await request(`/v1/conversations/${conversationId}/messages/${messageId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除消息 ${messageId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取对话历史统计
  getStats: async () => {
    try {
      return await request('/v1/conversations/stats', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取对话统计失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 导出对话
  exportConversation: async (conversationId, format = 'json') => {
    try {
      return await request(`/v1/conversations/${conversationId}/export?format=${format}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`导出对话 ${conversationId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 清除所有对话（谨慎使用）
  clearAll: async () => {
    try {
      return await request('/v1/conversations/clear-all', {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('清除所有对话失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  }
};

export default conversationApi;