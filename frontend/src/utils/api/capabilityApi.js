// 模型能力相关API模块
import { request } from '../apiUtils';

// 模型能力API实现
export const capabilityApi = {
  // 获取所有能力
  getAll: async (params = {}) => {
    try {
      // 构建查询参数
      const queryParams = new URLSearchParams();
      if (params.is_active !== undefined) {
        queryParams.append('is_active', params.is_active);
      }
      if (params.capability_type) {
        queryParams.append('capability_type', params.capability_type);
      }
      if (params.skip) {
        queryParams.append('skip', params.skip);
      }
      if (params.limit) {
        queryParams.append('limit', params.limit);
      }
      
      // 构建完整URL
      const url = queryParams.toString() 
        ? `/v1/capabilities?${queryParams.toString()}` 
        : '/v1/capabilities';
      
      const response = await request(url, {
        method: 'GET'
      });
      
      // 统一处理API返回格式
      if (response?.capabilities && Array.isArray(response.capabilities)) {
        return response.capabilities;
      }
      return response;
    } catch (error) {
      console.error('获取能力列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取单个能力
  getById: async (capabilityId) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取能力 ${capabilityId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 创建能力
  create: async (capabilityData) => {
    try {
      return await request('/v1/capabilities', {
        method: 'POST',
        body: JSON.stringify(capabilityData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('创建能力失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 更新能力
  update: async (capabilityId, updatedData) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}`, {
        method: 'PUT',
        body: JSON.stringify(updatedData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`更新能力 ${capabilityId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 删除能力
  delete: async (capabilityId) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除能力 ${capabilityId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取能力分类
  getTypes: async () => {
    try {
      return await request('/v1/capabilities/types', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取能力分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 添加模型能力关联
  addModelCapability: async (modelId, capabilityId, value = null) => {
    try {
      return await request('/v1/capabilities/associations', {
        method: 'POST',
        body: JSON.stringify({ model_id: modelId, capability_id: capabilityId, value: value }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('添加模型能力关联失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 添加能力到模型（别名，保持向后兼容）
  addCapabilityToModel: async (associationData) => {
    try {
      const { model_id, capability_id, config, value } = associationData;
      return await capabilityApi.addModelCapability(model_id, capability_id, value || config);
    } catch (error) {
      console.error('添加能力到模型失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 移除模型能力关联
  removeModelCapability: async (modelId, capabilityId) => {
    try {
      return await request(`/v1/capabilities/associations/model/${modelId}/capability/${capabilityId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('移除模型能力关联失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 从模型移除能力（别名，保持向后兼容）
  removeCapabilityFromModel: async (modelId, capabilityId) => {
    return capabilityApi.removeModelCapability(modelId, capabilityId);
  },
  
  // 更新模型能力值
  updateModelCapabilityValue: async (modelId, capabilityId, value) => {
    try {
      return await request(`/v1/capabilities/associations/model/${modelId}/capability/${capabilityId}`, {
        method: 'PUT',
        body: JSON.stringify({ value: value }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('更新模型能力值失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取模型的所有能力
  getModelCapabilities: async (modelId) => {
    try {
      const response = await request(`/v1/capabilities/model/${modelId}/capabilities`, {
        method: 'GET'
      });
      
      // 统一处理API返回格式
      if (response?.capabilities && Array.isArray(response.capabilities)) {
        return response.capabilities;
      }
      return response;
    } catch (error) {
      console.error(`获取模型 ${modelId} 的能力失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取模型的所有能力（别名，保持向后兼容）
  getCapabilitiesByModel: async (modelId) => {
    return capabilityApi.getModelCapabilities(modelId);
  },
  
  // 获取具备特定能力的模型
  getModelsByCapability: async (capabilityId, minValue = null) => {
    try {
      const params = new URLSearchParams();
      if (minValue !== null) {
        params.append('min_value', minValue);
      }
      const queryString = params.toString() ? `?${params.toString()}` : '';
      
      return await request(`/v1/capabilities/${capabilityId}/models${queryString}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取具备能力 ${capabilityId} 的模型失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 批量更新模型能力 - 注意：后端目前没有这个端点，暂时返回空对象
  batchUpdateModelCapabilities: async (modelId, capabilities) => {
    try {
      console.warn('批量更新模型能力功能尚未实现，因为后端没有对应的API端点');
      // 暂时返回一个空对象
      return { success: true, message: '批量更新功能尚未实现' };
    } catch (error) {
      console.error(`批量更新模型 ${modelId} 的能力失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  }
};

export default capabilityApi;