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
  update: async (capabilityId, capabilityData) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}`, {
        method: 'PUT',
        body: JSON.stringify(capabilityData),
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
  
  // 获取能力类型列表（后端未实现，暂时注释）
  // getTypes: async () => {
  //   try {
  //     return await request('/v1/capabilities/types', {
  //       method: 'GET'
  //     });
  //   } catch (error) {
  //     console.error('获取能力分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
  //     throw error;
  //   }
  // },
  
  // 添加模型能力关联
  addModelCapability: async (modelId, capabilityId, value = null) => {
    try {
      const requestData = {
        model_id: modelId,
        capability_id: capabilityId
      };
      
      // 如果有value参数，将其转换为JSON字符串并添加到config_json字段
      if (value !== null && value !== undefined) {
        if (typeof value === 'object') {
          requestData.config_json = JSON.stringify(value);
        } else {
          requestData.config_json = String(value);
        }
      }
      
      return await request('/v1/capabilities/associations', {
        method: 'POST',
        body: JSON.stringify(requestData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      // 如果是409错误（关联已存在），不抛出异常，返回空对象
      if (error.message && error.message.includes('409')) {
        console.warn(`模型 ${modelId} 与能力 ${capabilityId} 的关联已存在，跳过重复添加`);
        return {};
      }
      console.error('添加模型能力关联失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 添加能力到模型（别名，保持向后兼容）
  addCapabilityToModel: async (associationData) => {
    try {
      const { id: modelId, capability_id, config, value } = associationData;
      // 确保传入正确的参数
      const finalValue = value || config;
      return await capabilityApi.addModelCapability(modelId, capability_id, finalValue);
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
      const updateData = {};
      
      // 如果有value参数，将其转换为JSON字符串并添加到config_json字段
      if (value !== null && value !== undefined) {
        if (typeof value === 'object') {
          updateData.config_json = JSON.stringify(value);
        } else {
          updateData.config_json = String(value);
        }
      }
      
      return await request(`/v1/capabilities/associations/model/${modelId}/capability/${capabilityId}`, {
        method: 'PUT',
        body: JSON.stringify(updateData),
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
      if (response?.data && Array.isArray(response.data)) {
        return response.data;
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
  
  // 获取能力维度列表
  getDimensions: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams();
      if (params.is_active !== undefined) {
        queryParams.append('is_active', params.is_active);
      }
      if (params.skip) {
        queryParams.append('skip', params.skip);
      }
      if (params.limit) {
        queryParams.append('limit', params.limit);
      }
      const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
      
      const path = queryString ? `/v1/capability/dimensions/${queryString}` : `/v1/capability/dimensions/`;
      const response = await request(path, {
        method: 'GET'
      });
      
      return response;
    } catch (error) {
      console.error('获取能力维度列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取能力子维度列表
  getSubdimensions: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams();
      if (params.is_active !== undefined) {
        queryParams.append('is_active', params.is_active);
      }
      if (params.dimension_id) {
        queryParams.append('dimension_id', params.dimension_id);
      }
      if (params.skip) {
        queryParams.append('skip', params.skip);
      }
      if (params.limit) {
        queryParams.append('limit', params.limit);
      }
      const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
      
      const response = await request(`/v1/capability/dimensions/subdimensions${queryString}`, {
        method: 'GET'
      });
      
      return response;
    } catch (error) {
      console.error('获取能力子维度列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 创建能力维度
  createDimension: async (dimensionData) => {
    try {
      return await request('/v1/capability/dimensions', {
        method: 'POST',
        body: JSON.stringify(dimensionData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('创建能力维度失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 更新能力维度
  updateDimension: async (dimensionId, dimensionData) => {
    try {
      return await request(`/v1/capability/dimensions/${dimensionId}`, {
        method: 'PUT',
        body: JSON.stringify(dimensionData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`更新能力维度 ${dimensionId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 删除能力维度
  deleteDimension: async (dimensionId) => {
    try {
      return await request(`/v1/capability/dimensions/${dimensionId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除能力维度 ${dimensionId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 创建能力子维度
  createSubdimension: async (subdimensionData) => {
    try {
      return await request('/v1/capability/dimensions/subdimensions', {
        method: 'POST',
        body: JSON.stringify(subdimensionData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('创建能力子维度失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 更新能力子维度
  updateSubdimension: async (subdimensionId, subdimensionData) => {
    try {
      return await request(`/v1/capability/dimensions/subdimensions/${subdimensionId}`, {
        method: 'PUT',
        body: JSON.stringify(subdimensionData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`更新能力子维度 ${subdimensionId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 删除能力子维度
  deleteSubdimension: async (subdimensionId) => {
    try {
      return await request(`/v1/capability/dimensions/subdimensions/${subdimensionId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除能力子维度 ${subdimensionId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
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
  },

  // 获取能力参数模板
  getParameterTemplatesByCapability: async (capabilityId) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}/parameter-templates`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取能力 ${capabilityId} 的参数模板失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 创建能力参数模板
  createParameterTemplate: async (templateData) => {
    try {
      return await request('/v1/capability/parameter-templates', {
        method: 'POST',
        body: JSON.stringify(templateData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('创建能力参数模板失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 更新能力参数模板
  updateParameterTemplate: async (templateId, templateData) => {
    try {
      return await request(`/v1/capability/parameter-templates/${templateId}`, {
        method: 'PUT',
        body: JSON.stringify(templateData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`更新能力参数模板 ${templateId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 删除能力参数模板
  deleteParameterTemplate: async (templateId) => {
    try {
      return await request(`/v1/capability/parameter-templates/${templateId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除能力参数模板 ${templateId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 获取分类的默认能力
  getDefaultCapabilitiesByCategory: async (categoryId) => {
    try {
      // 尝试使用不同的API端点
      const endpoints = [
        { path: `/v1/capability/categories/${categoryId}/default-capabilities`, method: 'GET' },
        { path: `/v1/model/categories/${categoryId}/capabilities`, method: 'GET' }
      ];
      
      for (const endpoint of endpoints) {
        try {
          const response = await request(endpoint.path, { method: endpoint.method });
          return response;
        } catch (err) {
          console.warn(`尝试端点 ${endpoint.path} 失败:`, err.message);
          // 继续尝试下一个端点
        }
      }
      
      // 如果所有端点都失败，返回默认空数据结构
      return [];
    } catch (error) {
      console.error(`获取分类 ${categoryId} 的默认能力失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      // 返回默认空数据结构，避免影响其他功能
      return [];
    }
  },

  // 设置分类的默认能力
  setDefaultCapabilities: async (categoryId, capabilityIds) => {
    try {
      return await request(`/v1/capability/categories/${categoryId}/default-capabilities`, {
        method: 'POST',
        body: JSON.stringify({ capability_ids: capabilityIds }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`设置分类 ${categoryId} 的默认能力失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 为模型自动关联默认能力
  autoAssociateDefaultCapabilities: async (modelId) => {
    try {
      return await request(`/v1/capabilities/models/${modelId}/auto-associate`, {
        method: 'POST'
      });
    } catch (error) {
      console.error(`为模型 ${modelId} 自动关联默认能力失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 能力版本管理 API
  // 创建能力版本
  createCapabilityVersion: async (capabilityId, versionData) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}/versions`, {
        method: 'POST',
        body: JSON.stringify(versionData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`为能力 ${capabilityId} 创建版本失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 获取能力的所有版本
  getCapabilityVersions: async (capabilityId) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}/versions`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取能力 ${capabilityId} 的版本列表失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 获取特定版本的能力
  getCapabilityVersion: async (capabilityId, versionId) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}/versions/${versionId}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取能力 ${capabilityId} 的版本 ${versionId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 设置当前版本
  setCurrentVersion: async (capabilityId, versionId) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}/versions/${versionId}/set-current`, {
        method: 'PUT'
      });
    } catch (error) {
      console.error(`设置能力 ${capabilityId} 的当前版本失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 设置稳定版本
  setStableVersion: async (capabilityId, versionId) => {
    try {
      return await request(`/v1/capabilities/${capabilityId}/versions/${versionId}/set-stable`, {
        method: 'PUT'
      });
    } catch (error) {
      console.error(`设置能力 ${capabilityId} 的稳定版本失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  }
};

export default capabilityApi;