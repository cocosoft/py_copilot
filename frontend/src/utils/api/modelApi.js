// 模型相关API模块
import { request } from '../apiUtils';

// 统一的模型参数数据格式转换函数
const formatParameterData = (parameter) => {
  if (!parameter) return null;
  
  return {
    id: parameter.id,
    parameter_name: parameter.parameter_name || '',
    parameter_value: parameter.parameter_value || '',
    parameter_type: parameter.parameter_type || 'string',
    default_value: parameter.default_value || '',
    description: parameter.description || '',
    is_required: parameter.is_required || false,
    model_id: parameter.model_id,
    created_at: parameter.created_at,
    updated_at: parameter.updated_at,
    inherited: parameter.inherited || false // 添加继承参数标识
  };
};

// 构建发送到后端的模型参数数据格式
const buildParameterDataForBackend = (parameter, modelId) => {
  return {
    parameter_name: parameter.parameter_name || '',
    parameter_value: parameter.parameter_value || '',
    parameter_type: parameter.parameter_type || 'string',
    default_value: parameter.default_value || '',
    description: parameter.description || '',
    is_required: parameter.is_required || false,
    model_id: Number(modelId)
  };
}

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
  
  // 添加调试信息，查看原始模型数据结构
  console.log('原始模型数据:', model);
  
  // 处理供应商信息 - 检查不同的可能路径
  let supplierName = '';
  let supplierDisplayName = '';
  
  // 首先检查直接的supplier对象
  if (model.supplier) {
    supplierName = model.supplier.name || '';
    supplierDisplayName = model.supplier.display_name || supplierName; // 使用display_name，如果没有则使用name
  } 
  // 检查是否有嵌套的supplier数据
  else if (model.supplier_id) {
    // 如果只有supplier_id而没有supplier对象，我们需要通过API获取供应商信息
    // 这里暂时设置为空，实际项目中可能需要额外的API调用
    console.log('模型有supplier_id但没有supplier对象:', model.supplier_id);
  }
  
  // 处理分类信息
  let categories = [];
  if (model.categories && Array.isArray(model.categories)) {
    categories = model.categories.map(category => ({
      id: category.id,
      name: category.name,
      display_name: category.display_name,
      description: category.description,
      logo: category.logo,
      category_type: category.category_type
    }));
  }
  
  // 处理模型类型信息，优先使用后端返回的完整分类信息
  const modelType = model.model_type_id?.toString() || model.modelType || '';
  const modelTypeName = model.model_type_name || '';
  const modelTypeDisplayName = model.model_type_display_name || '';
  const modelTypeLogo = model.model_type_logo || '';
  
  console.log('处理后的供应商信息:', { supplierName, supplierDisplayName });
  console.log('处理后的分类信息:', categories);
  
  return {
    id: model.id,
    modelId: model.model_id || '',
    modelName: model.model_name || model.modelName || '',
    description: model.description || '',
    contextWindow: model.context_window || model.contextWindow || 0,
    maxTokens: model.max_tokens || model.maxTokens || 1000,
    isDefault: model.is_default || model.isDefault || false,
    isActive: model.is_active || model.isActive || true,
    supplierId: model.supplier_id || model.supplierId,
    supplierName: supplierName,
    supplierDisplayName: supplierDisplayName,
    modelType: modelType,
    modelTypeName: modelTypeName,
    modelTypeDisplayName: modelTypeDisplayName,
    modelTypeLogo: modelTypeLogo,
    categories: categories,
    logo: model.logo || null,
    createdAt: model.created_at || model.createdAt,
    updatedAt: model.updated_at || model.updatedAt
  };
};

// 构建发送到后端的模型数据格式
const buildModelDataForBackend = (model, supplierId) => {
  const integerSupplierId = Number(supplierId);
  
  // 根据后端schema要求，model_id字段必须有至少1个字符
  // 如果用户没有输入模型ID，使用模型名称作为默认值
  // 注意：这里需要同时检查model_id（下划线格式）和modelId（驼峰格式）以兼容不同的表单数据来源
  const modelIdValue = model.model_id || model.modelId;
  const modelId = modelIdValue && modelIdValue.trim() !== '' ? modelIdValue : model.modelName || model.model_id;
  
  // 处理模型名称字段：同时检查model_name（下划线格式）和modelName（驼峰格式）
  const modelNameValue = model.model_name || model.modelName;
  const modelName = modelNameValue && modelNameValue.trim() !== '' ? modelNameValue : modelId;
  
  // 构建基本模型数据
  const modelData = {
    model_id: modelId,
    model_name: modelName, // 添加模型名称字段
    description: model.description || '',
    context_window: Number(model.contextWindow) || 8000,
    max_tokens: Number(model.maxTokens) || 1000,
    is_default: Boolean(model.isDefault),
    is_active: model.isActive !== undefined ? Boolean(model.isActive) : true,
    supplier_id: integerSupplierId
  };
  
  // 处理模型类型字段：前端传递的是分类ID，需要转换为model_type_id
  if (model.modelType && model.modelType.trim() !== '') {
    modelData.model_type_id = Number(model.modelType);
  }
  
  // 只有当logo是文件对象时才包含logo字段，避免覆盖现有logo
  if (model.logo && typeof model.logo !== 'string') {
    modelData.logo = model.logo;
  }
  
  return modelData;
};

// 模型API实现
export const modelApi = {
  // 获取所有模型（通用）
  getAll: async () => {
    try {
      const response = await request('/v1/model-management/models', {
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
      const result = await request(`/v1/model-management/suppliers/${integerSupplierId}/models`, {
        method: 'GET'
      });
      
      
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
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/${integerModelId}`, {
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
    
    if (!model || !model.modelId && !model.model_id) {
      const validationError = handleApiError(new Error('模型ID不能为空'), 'create');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用统一的构建函数准备数据
      const modelDataForBackend = buildModelDataForBackend(model, supplierId);
      
      // 创建FormData对象，支持文件上传
      const formData = new FormData();
      
      // 添加模型数据作为JSON字符串
      formData.append('model_data', JSON.stringify(modelDataForBackend));
      
      // 如果有logo文件，添加到FormData
      if (model.logo && typeof model.logo !== 'string') {
        formData.append('logo', model.logo);
      }
      
      // 使用正确的路径格式
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models`, {
        method: 'POST',
        body: formData,
        // 不需要设置Content-Type，浏览器会自动设置并添加边界
        headers: {
          // 'Content-Type': 'multipart/form-data'  // 注释掉，让浏览器自动处理
        }
      });
      
      // 使用统一的格式化函数处理响应
      const formattedModel = formatModelData(response);
      return {
        ...formattedModel,
        success: true
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'create', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${model?.modelId}`
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
    
    // 检查模型ID，兼容model_id（下划线格式）和modelId（驼峰格式）
    const modelIdValue = updatedModel?.model_id || updatedModel?.modelId;
    if (!updatedModel || !modelIdValue) {
      const validationError = handleApiError(new Error('模型ID不能为空'), 'update');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用统一的构建函数准备数据
      const modelDataForBackend = buildModelDataForBackend(updatedModel, supplierId);
      
      // 创建FormData对象，支持文件上传
      const formData = new FormData();
      
      // 添加模型数据作为JSON字符串
      formData.append('model_data', JSON.stringify(modelDataForBackend));
      
      // 如果有logo文件（且不是字符串URL），添加到FormData
      if (updatedModel.logo && typeof updatedModel.logo !== 'string') {
        formData.append('logo', updatedModel.logo);
      }
      
      // 使用正确的路径格式
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/${integerModelId}`, {
        method: 'PUT',
        body: formData,
        // 不需要设置Content-Type，浏览器会自动设置并添加边界
        headers: {
          // 'Content-Type': 'multipart/form-data'  // 注释掉，让浏览器自动处理
        }
      });
      
      // 使用统一的格式化函数处理响应
      const formattedModel = formatModelData(response);

      return {
        ...formattedModel,
        success: true
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'update', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}, 模型ID: ${updatedModel?.modelId}`
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
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/${integerModelId}`, {
        method: 'DELETE'
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
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/set-default/${integerModelId}`, {
        method: 'POST'
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
  },
  
  // 获取指定模型的所有参数
  getParameters: async (supplierId, modelId) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID'), 'getParameters');
      throw new Error(validationError.message);
    }
    
    if (isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的模型ID'), 'getParameters');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用正确的路径格式
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/${integerModelId}/parameters`, {
        method: 'GET'
      });
      
      // 检查响应格式并转换数据
      let parameters = [];
      if (Array.isArray(response)) {
        parameters = response;
      } else if (response && Array.isArray(response.parameters)) {
        parameters = response.parameters;
      }
      
      // 格式化每个参数的数据
      return parameters.map(formatParameterData);
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getParameters', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 创建新的模型参数
  createParameter: async (supplierId, modelId, parameterData) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID'), 'createParameter');
      throw new Error(validationError.message);
    }
    
    if (isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的模型ID'), 'createParameter');
      throw new Error(validationError.message);
    }
    
    try {
      // 构建发送到后端的数据格式
      const formattedData = buildParameterDataForBackend(parameterData, integerModelId);
      
      // 使用正确的路径格式
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/${integerModelId}/parameters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        data: formattedData
      });
      
      return formatParameterData(response);
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'createParameter', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}, 参数数据: ${JSON.stringify(parameterData)}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 获取单个模型参数
  getParameter: async (supplierId, modelId, parameterId) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    const integerParameterId = Number(parameterId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID'), 'getParameter');
      throw new Error(validationError.message);
    }
    
    if (isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的模型ID'), 'getParameter');
      throw new Error(validationError.message);
    }
    
    if (isNaN(integerParameterId) || integerParameterId <= 0) {
      const validationError = handleApiError(new Error('无效的参数ID'), 'getParameter');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用正确的路径格式
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}`, {
        method: 'GET'
      });
      
      return formatParameterData(response);
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getParameter', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}, 参数ID: ${integerParameterId}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 更新模型参数
  updateParameter: async (supplierId, modelId, parameterId, parameterData) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    const integerParameterId = Number(parameterId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID'), 'updateParameter');
      throw new Error(validationError.message);
    }
    
    if (isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的模型ID'), 'updateParameter');
      throw new Error(validationError.message);
    }
    
    if (isNaN(integerParameterId) || integerParameterId <= 0) {
      const validationError = handleApiError(new Error('无效的参数ID'), 'updateParameter');
      throw new Error(validationError.message);
    }
    
    try {
      // 构建发送到后端的数据格式
      const formattedData = {
        parameter_name: parameterData.parameter_name || '',
        parameter_value: parameterData.parameter_value || '',
        parameter_type: parameterData.parameter_type || 'string',
        default_value: parameterData.default_value || '',
        description: parameterData.description || '',
        is_required: parameterData.is_required || false
      };
      
      // 使用正确的路径格式
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        data: formattedData
      });
      
      return formatParameterData(response);
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'updateParameter', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}, 参数ID: ${integerParameterId}, 参数数据: ${JSON.stringify(parameterData)}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 删除模型参数
  deleteParameter: async (supplierId, modelId, parameterId) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    const integerParameterId = Number(parameterId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID'), 'deleteParameter');
      throw new Error(validationError.message);
    }
    
    if (isNaN(integerModelId) || integerModelId <= 0) {
      const validationError = handleApiError(new Error('无效的模型ID'), 'deleteParameter');
      throw new Error(validationError.message);
    }
    
    if (isNaN(integerParameterId) || integerParameterId <= 0) {
      const validationError = handleApiError(new Error('无效的参数ID'), 'deleteParameter');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用正确的路径格式
      const response = await request(`/v1/model-management/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}`, {
        method: 'DELETE'
      });
      
      return {
        success: true,
        message: response?.message || '参数删除成功',
        parameterId: integerParameterId
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'deleteParameter', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}, 参数ID: ${integerParameterId}`
      );
      throw new Error(errorObj.message);
    }
  }
};

export default modelApi;