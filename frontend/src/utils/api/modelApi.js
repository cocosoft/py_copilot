// 模型相关API模块
import { request } from '../apiUtils';

// 模型API实现
export const modelApi = {
  // 获取所有模型（通用）
  getAll: async () => {
    try {
      const response = await request('/model-management/models', {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error('获取所有模型失败:', error);
      return [];
    }
  },
  
  // 获取指定供应商的所有模型
  getBySupplier: async (supplierId) => {
    console.log('🔄 modelApi.getBySupplier - 开始调用，供应商ID:', supplierId);
    // 确保supplierId为整数格式（后端要求）
    const integerSupplierId = Number(supplierId);
    try {
      // 使用正确的路径格式：/model-management/suppliers/{supplier_id}/models
      console.log(`🔄 modelApi.getBySupplier - 调用后端API，路径: /model-management/suppliers/${integerSupplierId}/models`);
      const result = await request(`/model-management/suppliers/${integerSupplierId}/models`, {
        method: 'GET'
      });
      
      console.log('🔄 modelApi.getBySupplier - 收到后端响应:', result);
      
      // 统一返回格式，确保包含models数组
      let modelsData = [];
      
      if (Array.isArray(result)) {
        modelsData = result;
      } else if (result && Array.isArray(result.models)) {
        modelsData = result.models;
      } else if (result && Array.isArray(result.data)) {
        modelsData = result.data;
      }
      
      // 转换模型数据，处理字段映射
      const formattedModels = modelsData.map(model => ({
        id: model.id,
        name: model.name,
        description: model.description || '',
        contextWindow: model.context_window || model.contextWindow || 0,
        isDefault: model.is_default || model.isDefault || false,
        supplier_id: model.supplier_id,
        modelType: model.model_type || 'chat',
        maxTokens: model.max_tokens || model.maxTokens || 0
      }));
      
      console.log('✅ modelApi.getBySupplier - 成功格式化模型数据，数量:', formattedModels.length);
      return { models: formattedModels, total: formattedModels.length, _source: 'api' };
    } catch (error) {
      console.error(`❌ modelApi.getBySupplier - API调用失败:`, error);
      // API失败时返回空数组，让UI处理错误状态
      return { models: [], total: 0, _source: 'api', error: error.message };
    }
  },
  
  // 获取单个模型
  getById: async (supplierId, modelId) => {
    // 确保supplierId为整数格式（后端要求）
    const integerSupplierId = Number(supplierId);
    try {
      // 使用正确的路径格式
      const response = await request(`/model-management/suppliers/${integerSupplierId}/models/${modelId}`, {
        method: 'GET'
      });
      
      // 格式化响应数据
      return {
        id: response.id,
        name: response.name,
        description: response.description || '',
        contextWindow: response.context_window || response.contextWindow || 0,
        isDefault: response.is_default || response.isDefault || false,
        supplier_id: response.supplier_id,
        modelType: response.model_type || 'chat',
        maxTokens: response.max_tokens || response.maxTokens || 0
      };
    } catch (error) {
      console.error(`获取模型 ${modelId} 失败:`, error);
      return null;
    }
  },
  
  // 创建新模型
  create: async (supplierId, model) => {
    // 确保supplierId为整数格式（后端要求）
    const integerSupplierId = Number(supplierId);
    // 确保模型数据包含supplier_id字段，也使用整数格式
    const modelWithSupplierId = {
      ...model,
      supplier_id: integerSupplierId,
      is_default: model.isDefault,
      context_window: model.contextWindow,
      model_type: model.modelType,
      max_tokens: model.maxTokens
    };
    try {
      // 使用正确的路径格式
      const response = await request(`/model-management/suppliers/${integerSupplierId}/models`, {
        method: 'POST',
        body: JSON.stringify(modelWithSupplierId),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      // 格式化响应数据
      return {
        id: response.id,
        name: response.name,
        description: response.description || '',
        contextWindow: response.context_window || response.contextWindow || 0,
        isDefault: response.is_default || response.isDefault || false,
        supplier_id: response.supplier_id,
        modelType: response.model_type || 'chat',
        maxTokens: response.max_tokens || response.maxTokens || 0
      };
    } catch (error) {
      console.error('创建模型失败:', error);
      throw error;
    }
  },
  
  // 更新模型
  update: async (supplierId, modelId, updatedModel) => {
    // 确保supplierId为整数格式（后端要求）
    const integerSupplierId = Number(supplierId);
    // 确保模型数据包含supplier_id字段，也使用整数格式
    const modelWithSupplierId = {
      ...updatedModel,
      supplier_id: integerSupplierId,
      is_default: updatedModel.isDefault,
      context_window: updatedModel.contextWindow,
      model_type: updatedModel.modelType,
      max_tokens: updatedModel.maxTokens
    };
    try {
      // 使用正确的路径格式
      const response = await request(`/model-management/suppliers/${integerSupplierId}/models/${modelId}`, {
        method: 'PUT',
        body: JSON.stringify(modelWithSupplierId),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      // 格式化响应数据
      return {
        id: response.id,
        name: response.name,
        description: response.description || '',
        contextWindow: response.context_window || response.contextWindow || 0,
        isDefault: response.is_default || response.isDefault || false,
        supplier_id: response.supplier_id,
        modelType: response.model_type || 'chat',
        maxTokens: response.max_tokens || response.maxTokens || 0
      };
    } catch (error) {
      console.error('更新模型失败:', error);
      throw error;
    }
  },
  
  // 删除模型
  delete: async (supplierId, modelId) => {
    // 确保supplierId为整数格式（后端要求）
    const integerSupplierId = Number(supplierId);
    try {
      // 使用正确的路径格式
      return await request(`/model-management/suppliers/${integerSupplierId}/models/${modelId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('删除模型失败:', error);
      throw error;
    }
  },
  
  // 设置默认模型
  setDefault: async (supplierId, modelId) => {
    // 确保supplierId为整数格式（后端要求）
    const integerSupplierId = Number(supplierId);
    try {
      // 使用正确的路径格式
      return await request(`/model-management/suppliers/${integerSupplierId}/models/set-default/${modelId}`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('设置默认模型失败:', error);
      throw error;
    }
  }
};

export default modelApi;