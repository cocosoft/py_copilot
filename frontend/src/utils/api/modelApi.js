// 模型相关API模块
import { request } from '../apiUtils';

// 统一的错误处理函数
const handleApiError = (error, operation, additionalInfo = '') => {
  // 构建错误信息
  const errorMessage = error.response?.data?.detail || error.message || '未知错误';
  const statusCode = error.response?.status || 'Unknown';
  
  // 详细的错误日志
  console.error(`❌ modelApi.${operation} - API调用失败 [${statusCode}]:`, errorMessage);
  if (additionalInfo) {
    console.error('  附加信息:', additionalInfo);
  }
  
  // 返回结构化错误对象
  return {
    error: true,
    message: errorMessage,
    statusCode,
    operation
  };
};

// 统一的数据格式转换函数
const formatModelData = (model) => {
  if (!model) return null;
  
  return {
    id: model.id,
    name: model.name || '',
    displayName: model.display_name || model.name || '',
    description: model.description || '',
    contextWindow: model.context_window || model.contextWindow || 0,
    maxTokens: model.max_tokens || model.maxTokens || 1000,
    isDefault: model.is_default || model.isDefault || false,
    isActive: model.is_active || model.isActive || true,
    supplierId: model.supplier_id || model.supplierId,
    modelType: model.model_type || model.modelType || 'chat',
    createdAt: model.created_at || model.createdAt,
    updatedAt: model.updated_at || model.updatedAt
  };
};

// 构建发送到后端的模型数据格式
const buildModelDataForBackend = (model, supplierId) => {
  const integerSupplierId = Number(supplierId);
  
  return {
    name: model.name,
    display_name: model.displayName || model.name,
    description: model.description || '',
    context_window: Number(model.contextWindow) || 8000,
    max_tokens: Number(model.maxTokens) || 1000,
    is_default: Boolean(model.isDefault),
    is_active: model.isActive !== undefined ? Boolean(model.isActive) : true,
    supplier_id: integerSupplierId,
    model_type: model.modelType || 'chat'
  };
};

// 模型API实现
export const modelApi = {
  // 获取所有模型（通用）
  getAll: async () => {
    try {
      const response = await request('/model-management/models', {
        method: 'GET'
      });
      
      // 检查响应格式并转换数据
      let models = [];
      if (Array.isArray(response)) {
        models = response;
      } else if (response && Array.isArray(response.models)) {
        models = response.models;
      }
      
      // 格式化每个模型的数据
      return {
        models: models.map(formatModelData),
        total: models.length,
        _source: 'api'
      };
    } catch (error) {
      const errorObj = handleApiError(error, 'getAll');
      // 返回错误信息和空数据，让调用方能够处理错误状态
      return {
        models: [],
        total: 0,
        _source: 'api',
        ...errorObj
      };
    }
  },
  
  // 获取指定供应商的所有模型
  getBySupplier: async (supplierId) => {
    console.log('🔄 modelApi.getBySupplier - 开始调用，供应商ID:', supplierId);
    // 确保supplierId为整数格式（后端要求）
    const integerSupplierId = Number(supplierId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
      const validationError = {
        error: true,
        message: '无效的供应商ID',
        statusCode: 400,
        operation: 'getBySupplier'
      };
      console.error('❌ modelApi.getBySupplier - 参数验证失败:', validationError);
      return {
        models: [],
        total: 0,
        _source: 'api',
        ...validationError
      };
    }
    
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
      
      // 使用统一的格式化函数
      const formattedModels = modelsData.map(formatModelData);
      
      console.log('✅ modelApi.getBySupplier - 成功格式化模型数据，数量:', formattedModels.length);
      return { 
        models: formattedModels, 
        total: formattedModels.length, 
        _source: 'api',
        success: true
      };
    } catch (error) {
      const errorObj = handleApiError(error, 'getBySupplier', `供应商ID: ${integerSupplierId}`);
      // API失败时返回空数组和错误信息，让UI处理错误状态
      return { 
        models: [], 
        total: 0, 
        _source: 'api',
        ...errorObj 
      };
    }
  },
  
  // 获取单个模型
  getById: async (supplierId, modelId) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0 || isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID或模型ID'), 'getById');
      return validationError;
    }
    
    try {
      // 使用正确的路径格式
      const response = await request(`/model-management/suppliers/${integerSupplierId}/models/${integerModelId}`, {
        method: 'GET'
      });
      
      // 使用统一的格式化函数
      const formattedModel = formatModelData(response);
      return {
        ...formattedModel,
        success: true
      };
    } catch (error) {
      return handleApiError(
        error, 
        'getById', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}`
      );
    }
  },
  
  // 创建新模型
  create: async (supplierId, model) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID'), 'create');
      throw new Error(validationError.message);
    }
    
    if (!model || !model.name) {
      const validationError = handleApiError(new Error('模型名称不能为空'), 'create');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用统一的构建函数准备数据
      const modelDataForBackend = buildModelDataForBackend(model, supplierId);
      
      console.log('🔄 modelApi.create - 发送到后端的数据:', modelDataForBackend);
      
      // 使用正确的路径格式
      const response = await request(`/model-management/suppliers/${integerSupplierId}/models`, {
        method: 'POST',
        body: JSON.stringify(modelDataForBackend),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      // 使用统一的格式化函数处理响应
      const formattedModel = formatModelData(response);
      console.log('✅ modelApi.create - 模型创建成功:', formattedModel);
      return {
        ...formattedModel,
        success: true
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'create', 
        `供应商ID: ${integerSupplierId}, 模型名称: ${model?.name}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 更新模型
  update: async (supplierId, modelId, updatedModel) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0 || isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID或模型ID'), 'update');
      throw new Error(validationError.message);
    }
    
    if (!updatedModel || !updatedModel.name) {
      const validationError = handleApiError(new Error('模型名称不能为空'), 'update');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用统一的构建函数准备数据
      const modelDataForBackend = buildModelDataForBackend(updatedModel, supplierId);
      
      console.log('🔄 modelApi.update - 发送到后端的数据:', modelDataForBackend);
      
      // 使用正确的路径格式
      const response = await request(`/model-management/suppliers/${integerSupplierId}/models/${integerModelId}`, {
        method: 'PUT',
        body: JSON.stringify(modelDataForBackend),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      // 使用统一的格式化函数处理响应
      const formattedModel = formatModelData(response);
      console.log('✅ modelApi.update - 模型更新成功:', formattedModel);
      return {
        ...formattedModel,
        success: true
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'update', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}, 模型名称: ${updatedModel?.name}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 删除模型
  delete: async (supplierId, modelId) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0 || isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID或模型ID'), 'delete');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用正确的路径格式
      const response = await request(`/model-management/suppliers/${integerSupplierId}/models/${integerModelId}`, {
        method: 'DELETE'
      });
      
      console.log('✅ modelApi.delete - 模型删除成功', {
        supplierId: integerSupplierId,
        modelId: integerModelId
      });
      
      return {
        success: true,
        message: response?.message || '模型删除成功',
        supplierId: integerSupplierId,
        modelId: integerModelId
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'delete', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 设置默认模型
  setDefault: async (supplierId, modelId) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0 || isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID或模型ID'), 'setDefault');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用正确的路径格式
      const response = await request(`/model-management/suppliers/${integerSupplierId}/models/set-default/${integerModelId}`, {
        method: 'POST'
      });
      
      console.log('✅ modelApi.setDefault - 默认模型设置成功', {
        supplierId: integerSupplierId,
        modelId: integerModelId
      });
      
      return {
        success: true,
        message: response?.message || '默认模型设置成功',
        supplierId: integerSupplierId,
        modelId: integerModelId
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'setDefault', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}`
      );
      throw new Error(errorObj.message);
    }
  }
};

export default modelApi;