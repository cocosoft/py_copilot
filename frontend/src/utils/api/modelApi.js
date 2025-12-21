// 模型相关API模块
import { request } from '../apiUtils';

// 统一的模型参数数据格式转换函数
const formatParameterData = (parameter) => {
  if (!parameter) return null;
  
  // Debug: Check what parameter looks like when received
  console.log('Raw parameter data:', JSON.stringify(parameter, null, 2));
  
  // Helper function to safely convert any value to a React-compatible primitive
  const safeValue = (value) => {
    if (value === null || value === undefined) {
      return '';
    }
    if (typeof value === 'object') {
      // Check if it's an array
      if (Array.isArray(value)) {
        return value.join(', ');
      }
      // Check if it has a value property (most common case)
      if (value.value !== undefined) {
        return safeValue(value.value); // Recursively handle nested objects
      }
      // For other objects, convert to string representation
      return JSON.stringify(value);
    }
    // For primitive values, just return as is
    return value;
  };
  
  // Handle parameter_value with safeValue helper
  let parameterValue = safeValue(parameter.parameter_value);
  console.log('Processed parameter_value:', JSON.stringify(parameterValue, null, 2), 'Type:', typeof parameterValue);
  
  // Handle default_value with safeValue helper
  let defaultValue = safeValue(parameter.default_value);
  console.log('Processed default_value:', JSON.stringify(defaultValue, null, 2), 'Type:', typeof defaultValue);
  
  const formatted = {
    id: parameter.id,
    parameter_name: parameter.parameter_name || '',
    parameter_value: parameterValue,
    parameter_type: parameter.parameter_type || 'string',
    default_value: defaultValue,
    description: parameter.description || '',
    is_required: parameter.is_required || false,
    model_id: parameter.model_id,
    created_at: parameter.created_at,
    updated_at: parameter.updated_at,
    inherited: parameter.inherited || false // 添加继承参数标识
  };
  
  console.log('Formatted parameter:', JSON.stringify(formatted, null, 2));
  return formatted;
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
    console.error('  附加信息:', JSON.stringify(additionalInfo, null, 2));
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
  console.log('原始模型数据:', JSON.stringify(model, null, 2));
  
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
    console.log('模型有supplier_id但没有supplier对象:', JSON.stringify(model.supplier_id, null, 2));
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
  
  console.log('处理后的供应商信息:', JSON.stringify({ supplierName, supplierDisplayName }, null, 2));
  console.log('处理后的分类信息:', JSON.stringify(categories, null, 2));
  
  return {
    id: model.id,
    modelId: model.model_id || '',
    modelName: model.model_name || '', // 确保优先使用后端返回的 model_name 字段
    description: model.description || '',
    contextWindow: model.context_window || 0,
    maxTokens: model.max_tokens || 1000,
    isDefault: model.is_default || false,
    isActive: model.is_active !== undefined ? model.is_active : true,
    supplierId: model.supplier_id || '',
    supplierName: supplierName,
    supplierDisplayName: supplierDisplayName,
    modelType: modelType,
    modelTypeName: modelTypeName,
    modelTypeDisplayName: modelTypeDisplayName,
    modelTypeLogo: modelTypeLogo,
    categories: categories,
    logo: model.logo || null,
    createdAt: model.created_at || '',
    updatedAt: model.updated_at || ''
  };
};

// 构建发送到后端的模型数据格式
const buildModelDataForBackend = (model, supplierId) => {
  const integerSupplierId = Number(supplierId);
  
  // 根据后端schema要求，model_id字段必须有至少1个字符
  // 如果用户没有输入模型ID，使用模型名称作为默认值
  // 注意：这里需要同时检查model_id（下划线格式）和modelId（驼峰格式）以兼容不同的表单数据来源
  const modelIdValue = model.model_id || model.modelId;
  const modelId = modelIdValue && modelIdValue.trim() !== '' ? modelIdValue : model.model_name || model.modelName;
  
  // 处理模型名称字段：同时检查model_name（下划线格式）和modelName（驼峰格式）
  const modelNameValue = model.model_name || model.modelName;
  const modelName = modelNameValue && modelNameValue.trim() !== '' ? modelNameValue : modelId;
  
  // 构建基本模型数据
  const modelData = {
    model_id: modelId,
    model_name: modelName, // 添加模型名称字段
    description: model.description || '',
    context_window: Number(model.contextWindow) || Number(model.context_window) || 8000,
    max_tokens: Number(model.maxTokens) || Number(model.max_tokens) || 1000,
    is_default: Boolean(model.isDefault) || Boolean(model.is_default),
    is_active: model.isActive !== undefined ? Boolean(model.isActive) : Boolean(model.is_active) !== undefined ? Boolean(model.is_active) : true,
    supplier_id: integerSupplierId
  };
  
  // 处理模型类型字段：前端传递的是分类ID，需要转换为model_type_id
  if (model.modelType && model.modelType.trim() !== '') {
    modelData.model_type_id = Number(model.modelType);
  } else if (model.model_type && model.model_type.trim() !== '') {
    modelData.model_type_id = Number(model.model_type);
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
      console.error('❌ modelApi.getBySupplier - 参数验证失败:', JSON.stringify(validationError, null, 2));
      return {
        models: [],
        total: 0,
        _source: 'api',
        ...validationError
      };
    }
    
    try {
      // 使用正确的路径格式：/suppliers/{supplier_id}/models
      const result = await request(`/v1/suppliers/${integerSupplierId}/models`, {
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
      const response = await request(`/v1/suppliers/${integerSupplierId}/models/${integerModelId}`, {
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
      const response = await request(`/v1/suppliers/${integerSupplierId}/models`, {
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
      const response = await request(`/v1/suppliers/${integerSupplierId}/models/${integerModelId}`, {
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
      const response = await request(`/v1/suppliers/${integerSupplierId}/models/${integerModelId}`, {
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
      const response = await request(`/v1/suppliers/${integerSupplierId}/models/set-default/${integerModelId}`, {
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

  // 同步模型参数与模板
  syncModelParametersWithTemplate: async (supplierId, modelId, templateId) => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerModelId = Number(modelId);
    const integerTemplateId = Number(templateId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0 || isNaN(integerModelId) || integerModelId <= 0 || isNaN(integerTemplateId) || integerTemplateId <= 0) {
      const validationError = handleApiError(new Error('无效的供应商ID、模型ID或模板ID'), 'syncModelParametersWithTemplate');
      throw new Error(validationError.message);
    }
    
    try {
      // 使用正确的路径格式
      const response = await request(`/v1/parameter-templates/sync-model-parameters`, {
        method: 'POST',
        body: JSON.stringify({
          supplier_id: integerSupplierId,
          model_id: integerModelId,
          template_id: integerTemplateId
        })
      });
      
      return {
        success: true,
        message: response?.message || '模型参数与模板同步成功',
        supplierId: integerSupplierId,
        modelId: integerModelId,
        templateId: integerTemplateId
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'syncModelParametersWithTemplate', 
        `供应商ID: ${integerSupplierId}, 模型ID: ${integerModelId}, 模板ID: ${integerTemplateId}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 获取参数模板列表
  getParameterTemplates: async (level = null) => {
    try {
      let endpoint = `/v1/parameter-templates`;
      if (level) {
        endpoint = `/v1/parameter-templates/level/${level}`;
      }
      
      const response = await request(endpoint, {
        method: 'GET'
      });
      
      // 检查响应格式并转换数据
      let templates = [];
      if (Array.isArray(response)) {
        templates = response;
      } else if (response && Array.isArray(response.templates)) {
        templates = response.templates;
      }
      
      return templates;
    } catch (error) {
      const errorObj = handleApiError(error, 'getParameterTemplates');
      throw new Error(errorObj.message);
    }
  },
  
  // 获取单个参数模板
  getParameterTemplate: async (templateId) => {
    try {
      const response = await request(`/v1/parameter-templates/${templateId}`, {
        method: 'GET'
      });
      
      return response;
    } catch (error) {
      const errorObj = handleApiError(error, 'getParameterTemplate', `模板ID: ${templateId}`);
      throw new Error(errorObj.message);
    }
  },
  
  // 创建参数模板
  createParameterTemplate: async (templateData) => {
    try {
      const response = await request(`/v1/parameter-templates`, {
        method: 'POST',
        body: JSON.stringify(templateData)
      });
      
      return response;
    } catch (error) {
      const errorObj = handleApiError(error, 'createParameterTemplate', templateData);
      throw new Error(errorObj.message);
    }
  },
  
  // 更新参数模板
  updateParameterTemplate: async (templateId, templateData) => {
    try {
      const response = await request(`/v1/parameter-templates/${templateId}`, {
        method: 'PUT',
        body: JSON.stringify(templateData)
      });
      
      return response;
    } catch (error) {
      const errorObj = handleApiError(error, 'updateParameterTemplate', `模板ID: ${templateId}, 数据: ${JSON.stringify(templateData)}`);
      throw new Error(errorObj.message);
    }
  },
  
  // 删除参数模板
  deleteParameterTemplate: async (templateId) => {
    try {
      const response = await request(`/v1/parameter-templates/${templateId}`, {
        method: 'DELETE'
      });
      
      return { success: true, message: '参数模板删除成功' };
    } catch (error) {
      const errorObj = handleApiError(error, 'deleteParameterTemplate', `模板ID: ${templateId}`);
      throw new Error(errorObj.message);
    }
  },
  
  // 获取合并后的参数配置
  getMergedParameters: async (templateId) => {
    try {
      const response = await request(`/v1/parameter-templates/${templateId}/merged-parameters`, {
        method: 'GET'
      });
      
      return response;
    } catch (error) {
      const errorObj = handleApiError(error, 'getMergedParameters', `模板ID: ${templateId}`);
      throw new Error(errorObj.message);
    }
  },
  
  // 应用参数模板到模型
  applyParameterTemplate: async (supplierId, modelId, templateId) => {
    try {
      const response = await request(`/v1/parameter-templates/suppliers/${supplierId}/models/${modelId}/apply-parameter-template`, {
        method: 'POST',
        body: JSON.stringify({ template_id: templateId })
      });
      
      return response;
    } catch (error) {
      const errorObj = handleApiError(error, 'applyParameterTemplate', `供应商ID: ${supplierId}, 模型ID: ${modelId}, 模板ID: ${templateId}`);
      throw new Error(errorObj.message);
    }
  },
  
  // 获取指定层级的参数
  getParameters: async (supplierId, modelId, level = 'model') => {
    try {
      let endpoint;
      
      // 参数验证和类型转换 - 在需要时使用
      let integerSupplierId;
      let integerModelId;
      
      switch (level) {
        case 'system':
          endpoint = '/v1/model-management/system-parameters';
          break;
        case 'supplier':
          // 检查supplierId是否存在
          if (!supplierId) {
            throw new Error('供应商ID不能为空');
          }
          integerSupplierId = Number(supplierId);
          if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
            throw new Error('无效的供应商ID');
          }
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters`;
          break;
        case 'model_type':
          endpoint = '/v1/model-management/model-types/parameters';
          break;
        case 'model_capability':
          endpoint = '/v1/model-management/model-capabilities/parameters';
          break;
        case 'model':
        default:
          // 只有当需要这些参数时才进行验证
          if (level === 'model') {
            // 参数验证和类型转换
            integerSupplierId = Number(supplierId);
            integerModelId = Number(modelId);
            
            // 参数验证
            if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
              throw new Error('无效的供应商ID');
            }
            
            if (isNaN(integerModelId) || integerModelId <= 0) {
              throw new Error('无效的模型ID');
            }
            
            // 使用正确的路径格式
            endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters`;
          } else {
            // 默认使用系统参数端点
            endpoint = '/v1/model-management/system-parameters';
          }
      }
      
      const response = await request(endpoint, {
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
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 创建新的参数
  createParameter: async (supplierId, modelId, parameterData, level = 'model') => {
    try {
      let endpoint;
      let formattedData;
      
      // 参数验证和类型转换 - 在需要时使用
      let integerSupplierId;
      let integerModelId;
      
      switch (level) {
        case 'system':
          endpoint = '/v1/model-management/system-parameters';
          formattedData = {
            parameter_name: parameterData.parameter_name || '',
            parameter_value: parameterData.parameter_value || '',
            parameter_type: parameterData.parameter_type || 'string',
            default_value: parameterData.default_value || '',
            description: parameterData.description || '',
            is_required: parameterData.is_required || false
          };
          break;
        case 'supplier':
          integerSupplierId = Number(supplierId);
          if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
            throw new Error('无效的供应商ID');
          }
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters`;
          formattedData = {
            parameter_name: parameterData.parameter_name || '',
            parameter_value: parameterData.parameter_value || '',
            parameter_type: parameterData.parameter_type || 'string',
            default_value: parameterData.default_value || '',
            description: parameterData.description || '',
            is_required: parameterData.is_required || false
          };
          break;
        case 'model':
        default:
          // 参数验证和类型转换
          integerSupplierId = Number(supplierId);
          integerModelId = Number(modelId);
          
          // 参数验证
          if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
            throw new Error('无效的供应商ID');
          }
          
          if (isNaN(integerModelId) || integerModelId <= 0) {
            throw new Error('无效的模型ID');
          }
          
          // 构建发送到后端的数据格式
          formattedData = buildParameterDataForBackend(parameterData, integerModelId);
          
          // 使用正确的路径格式
          endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters`;
      }
      
      const response = await request(endpoint, {
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
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数数据: ${JSON.stringify(parameterData)}`
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
      const response = await request(`/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}`, {
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
  updateParameter: async (supplierId, modelId, parameterId, parameterData, level = 'model') => {
    // 参数验证和类型转换
    const integerParameterId = Number(parameterId);
    
    // 参数验证
    if (isNaN(integerParameterId) || integerParameterId <= 0) {
      const validationError = handleApiError(new Error('无效的参数ID'), 'updateParameter');
      throw new Error(validationError.message);
    }
    
    try {
      let endpoint;
      
      // 参数验证和类型转换 - 在需要时使用
      let integerSupplierId;
      let integerModelId;
      
      // 根据层级选择不同的端点
      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/system-parameters/${integerParameterId}`;
          break;
        case 'supplier':
          integerSupplierId = Number(supplierId);
          if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
            throw new Error('无效的供应商ID');
          }
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters/${integerParameterId}`;
          break;
        case 'model':
        default:
          // 参数验证和类型转换
          integerSupplierId = Number(supplierId);
          integerModelId = Number(modelId);
          
          // 参数验证
          if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
            throw new Error('无效的供应商ID');
          }
          
          if (isNaN(integerModelId) || integerModelId <= 0) {
            throw new Error('无效的模型ID');
          }
          
          // 使用正确的路径格式
          endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}`;
      }
      
      // 构建发送到后端的数据格式
      const formattedData = {
        parameter_name: parameterData.parameter_name || '',
        parameter_value: parameterData.parameter_value || '',
        parameter_type: parameterData.parameter_type || 'string',
        default_value: parameterData.default_value || '',
        description: parameterData.description || '',
        is_required: parameterData.is_required || false
      };
      
      const response = await request(endpoint, {
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
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数ID: ${parameterId}, 参数数据: ${JSON.stringify(parameterData)}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 删除模型参数
  deleteParameter: async (supplierId, modelId, parameterId, level = 'model') => {
    // 参数验证和类型转换
    const integerParameterId = Number(parameterId);
    
    // 参数验证
    if (isNaN(integerParameterId) || integerParameterId <= 0) {
      const validationError = handleApiError(new Error('无效的参数ID'), 'deleteParameter');
      throw new Error(validationError.message);
    }
    
    try {
      let endpoint;
      
      // 参数验证和类型转换 - 在需要时使用
      let integerSupplierId;
      let integerModelId;
      
      // 根据层级选择不同的端点
      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/system-parameters/${integerParameterId}`;
          break;
        case 'supplier':
          integerSupplierId = Number(supplierId);
          if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
            throw new Error('无效的供应商ID');
          }
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters/${integerParameterId}`;
          break;
        case 'model':
        default:
          // 参数验证和类型转换
          integerSupplierId = Number(supplierId);
          integerModelId = Number(modelId);
          
          // 参数验证
          if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
            throw new Error('无效的供应商ID');
          }
          
          if (isNaN(integerModelId) || integerModelId <= 0) {
            throw new Error('无效的模型ID');
          }
          
          // 使用正确的路径格式
          endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}`;
      }
      
      const response = await request(endpoint, {
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
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数ID: ${parameterId}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 应用参数模板（系统级到供应商级）
  applySystemParameterTemplate: async (supplierId, templateId, level = 'supplier') => {
    // 参数验证和类型转换
    const integerSupplierId = Number(supplierId);
    const integerTemplateId = Number(templateId);
    
    // 参数验证
    if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
      throw new Error('无效的供应商ID');
    }
    
    if (isNaN(integerTemplateId) || integerTemplateId <= 0) {
      throw new Error('无效的模板ID');
    }
    
    try {
      let endpoint;
      
      switch (level) {
        case 'supplier':
          endpoint = `/v1/suppliers/${integerSupplierId}/apply-template`;
          break;
        default:
          throw new Error('不支持的层级');
      }
      
      const response = await request(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        data: {
          template_id: integerTemplateId
        }
      });
      
      return {
        success: true,
        message: response?.message || '参数模板应用成功',
        appliedParameters: response?.applied_parameters || []
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'applySystemParameterTemplate', 
        `层级: ${level}, 供应商ID: ${supplierId}, 模板ID: ${templateId}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 获取参数模板列表（系统级）
  getSystemParameterTemplates: async (level = 'system') => {
    try {
      let endpoint;
      
      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/parameter-templates/system`;
          break;
        case 'supplier':
          endpoint = `/v1/model-management/parameter-templates/supplier`;
          break;
        default:
          endpoint = `/v1/model-management/parameter-templates`;
      }
      
      const response = await request(endpoint, {
        method: 'GET'
      });
      
      // 检查响应格式并转换数据
      let templates = [];
      if (Array.isArray(response)) {
        templates = response;
      } else if (response && Array.isArray(response.templates)) {
        templates = response.templates;
      }
      
      return templates;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getSystemParameterTemplates', 
        `层级: ${level}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 创建参数模板（系统级）
  createSystemParameterTemplate: async (templateData, level = 'system') => {
    try {
      let endpoint;
      
      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/parameter-templates/system`;
          break;
        case 'supplier':
          endpoint = `/v1/model-management/parameter-templates/supplier`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/parameter-templates/model-type`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/parameter-templates/model-capability`;
          break;
        case 'model':
          endpoint = `/v1/model-management/parameter-templates/model`;
          break;
        case 'agent':
          endpoint = `/v1/model-management/parameter-templates/agent`;
          break;
        default:
          endpoint = `/v1/model-management/parameter-templates`;
      }
      
      const response = await request(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        data: templateData
      });
      
      return response;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'createSystemParameterTemplate', 
        `层级: ${level}, 模板数据: ${JSON.stringify(templateData)}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 获取单个参数模板详情（系统级）
  getSystemParameterTemplate: async (templateId, level = 'system') => {
    try {
      const integerTemplateId = Number(templateId);
      
      let endpoint;
      
      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/parameter-templates/system/${integerTemplateId}`;
          break;
        case 'supplier':
          endpoint = `/v1/model-management/parameter-templates/supplier/${integerTemplateId}`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/parameter-templates/model-type/${integerTemplateId}`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/parameter-templates/model-capability/${integerTemplateId}`;
          break;
        case 'model':
          endpoint = `/v1/model-management/parameter-templates/model/${integerTemplateId}`;
          break;
        case 'agent':
          endpoint = `/v1/model-management/parameter-templates/agent/${integerTemplateId}`;
          break;
        default:
          endpoint = `/v1/model-management/parameter-templates/${integerTemplateId}`;
      }
      
      const response = await request(endpoint, {
        method: 'GET'
      });
      
      return response;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getSystemParameterTemplate', 
        `层级: ${level}, 模板ID: ${templateId}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 更新参数模板（系统级）
  updateSystemParameterTemplate: async (templateId, templateData, level = 'system') => {
    try {
      const integerTemplateId = Number(templateId);
      
      let endpoint;
      
      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/parameter-templates/system/${integerTemplateId}`;
          break;
        case 'supplier':
          endpoint = `/v1/model-management/parameter-templates/supplier/${integerTemplateId}`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/parameter-templates/model-type/${integerTemplateId}`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/parameter-templates/model-capability/${integerTemplateId}`;
          break;
        case 'model':
          endpoint = `/v1/model-management/parameter-templates/model/${integerTemplateId}`;
          break;
        case 'agent':
          endpoint = `/v1/model-management/parameter-templates/agent/${integerTemplateId}`;
          break;
        default:
          endpoint = `/v1/model-management/parameter-templates/${integerTemplateId}`;
      }
      
      const response = await request(endpoint, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        data: templateData
      });
      
      return response;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'updateSystemParameterTemplate', 
        `层级: ${level}, 模板ID: ${templateId}, 模板数据: ${JSON.stringify(templateData)}`
      );
      throw new Error(errorObj.message);
    }
  },
  
  // 删除参数模板（系统级）
  deleteSystemParameterTemplate: async (templateId, level = 'system') => {
    try {
      const integerTemplateId = Number(templateId);
      
      let endpoint;
      
      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/parameter-templates/system/${integerTemplateId}`;
          break;
        case 'supplier':
          endpoint = `/v1/model-management/parameter-templates/supplier/${integerTemplateId}`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/parameter-templates/model-type/${integerTemplateId}`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/parameter-templates/model-capability/${integerTemplateId}`;
          break;
        case 'model':
          endpoint = `/v1/model-management/parameter-templates/model/${integerTemplateId}`;
          break;
        case 'agent':
          endpoint = `/v1/model-management/parameter-templates/agent/${integerTemplateId}`;
          break;
        default:
          endpoint = `/v1/model-management/parameter-templates/${integerTemplateId}`;
      }
      
      const response = await request(endpoint, {
        method: 'DELETE'
      });
      
      return {
        success: true,
        message: response?.message || '参数模板删除成功',
        templateId: integerTemplateId
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'deleteSystemParameterTemplate', 
        `层级: ${level}, 模板ID: ${templateId}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 获取参数版本历史
  getParameterVersions: async (supplierId, modelId, parameterId, level = 'model') => {
    try {
      let endpoint;
      const integerSupplierId = supplierId ? Number(supplierId) : null;
      const integerModelId = modelId ? Number(modelId) : null;
      const integerParameterId = Number(parameterId);

      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/system-parameters/${integerParameterId}/versions`;
          break;
        case 'supplier':
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters/${integerParameterId}/versions`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/model-types/parameters/${integerParameterId}/versions`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/model-capabilities/parameters/${integerParameterId}/versions`;
          break;
        default:
          endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}/versions`;
      }

      const response = await request(endpoint, {
        method: 'GET'
      });

      // 检查响应格式并转换数据
      let versions = [];
      if (Array.isArray(response)) {
        versions = response;
      } else if (response && Array.isArray(response.versions)) {
        versions = response.versions;
      }

      return versions;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getParameterVersions', 
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数ID: ${parameterId}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 回滚参数到特定版本
  revertParameterToVersion: async (supplierId, modelId, parameterId, versionId, level = 'model') => {
    try {
      let endpoint;
      const integerSupplierId = supplierId ? Number(supplierId) : null;
      const integerModelId = modelId ? Number(modelId) : null;
      const integerParameterId = Number(parameterId);
      const integerVersionId = Number(versionId);

      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/system-parameters/${integerParameterId}/versions/${integerVersionId}/revert`;
          break;
        case 'supplier':
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters/${integerParameterId}/versions/${integerVersionId}/revert`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/model-types/parameters/${integerParameterId}/versions/${integerVersionId}/revert`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/model-capabilities/parameters/${integerParameterId}/versions/${integerVersionId}/revert`;
          break;
        default:
          endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}/versions/${integerVersionId}/revert`;
      }

      const response = await request(endpoint, {
        method: 'POST'
      });

      return {
        success: true,
        message: response?.message || '参数版本回滚成功',
        parameter: response?.parameter ? formatParameterData(response.parameter) : null
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'revertParameterToVersion', 
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数ID: ${parameterId}, 版本ID: ${versionId}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 获取模型类型参数
  getCategoryParameters: async (categoryId) => {
    try {
      const integerCategoryId = Number(categoryId);
      if (isNaN(integerCategoryId) || integerCategoryId <= 0) {
        throw new Error('无效的模型类型ID');
      }
      
      const response = await request(`/v1/model-management/model-types/${integerCategoryId}/parameters`, {
        method: 'GET'
      });

      let parameters = [];
      if (Array.isArray(response)) {
        parameters = response;
      } else if (response && Array.isArray(response.parameters)) {
        parameters = response.parameters;
      }

      return parameters.map(formatParameterData);
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getCategoryParameters',
        `模型类型ID: ${categoryId}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 创建模型类型参数
  createCategoryParameter: async (categoryId, parameterData) => {
    try {
      const integerCategoryId = Number(categoryId);
      if (isNaN(integerCategoryId) || integerCategoryId <= 0) {
        throw new Error('无效的模型类型ID');
      }

      const formattedData = {
        parameter_name: parameterData.parameter_name || '',
        parameter_value: parameterData.parameter_value || '',
        parameter_type: parameterData.parameter_type || 'string',
        default_value: parameterData.default_value || '',
        description: parameterData.description || '',
        is_required: parameterData.is_required || false
      };

      const response = await request(`/v1/model-management/model-types/${integerCategoryId}/parameters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        data: formattedData
      });

      return formatParameterData(response);
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'createCategoryParameter',
        `模型类型ID: ${categoryId}, 参数数据: ${JSON.stringify(parameterData)}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 更新模型类型参数
  updateCategoryParameter: async (categoryId, parameterId, parameterData) => {
    try {
      const integerCategoryId = Number(categoryId);
      const integerParameterId = Number(parameterId);

      if (isNaN(integerCategoryId) || integerCategoryId <= 0) {
        throw new Error('无效的模型类型ID');
      }

      if (isNaN(integerParameterId) || integerParameterId <= 0) {
        throw new Error('无效的参数ID');
      }

      const formattedData = {
        parameter_name: parameterData.parameter_name || '',
        parameter_value: parameterData.parameter_value || '',
        parameter_type: parameterData.parameter_type || 'string',
        default_value: parameterData.default_value || '',
        description: parameterData.description || '',
        is_required: parameterData.is_required || false
      };

      const response = await request(`/v1/model-management/model-types/${integerCategoryId}/parameters/${integerParameterId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        data: formattedData
      });

      return formatParameterData(response);
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'updateCategoryParameter',
        `模型类型ID: ${categoryId}, 参数ID: ${parameterId}, 参数数据: ${JSON.stringify(parameterData)}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 删除模型类型参数
  deleteCategoryParameter: async (categoryId, parameterId) => {
    try {
      const integerCategoryId = Number(categoryId);
      const integerParameterId = Number(parameterId);

      if (isNaN(integerCategoryId) || integerCategoryId <= 0) {
        throw new Error('无效的模型类型ID');
      }

      if (isNaN(integerParameterId) || integerParameterId <= 0) {
        throw new Error('无效的参数ID');
      }

      const response = await request(`/v1/model-management/model-types/${integerCategoryId}/parameters/${integerParameterId}`, {
        method: 'DELETE'
      });

      return {
        success: true,
        message: response?.message || '模型类型参数删除成功',
        parameterId: integerParameterId
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'deleteCategoryParameter',
        `模型类型ID: ${categoryId}, 参数ID: ${parameterId}`
      );
      throw new Error(errorObj.message);
    }
  },



  // 获取所有参数的版本历史记录
  getAllParameterVersions: async (supplierId, modelId, level = 'model') => {
    try {
      let endpoint;
      const integerSupplierId = supplierId ? Number(supplierId) : null;
      const integerModelId = modelId ? Number(modelId) : null;

      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/system-parameters/versions`;
          break;
        case 'supplier':
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters/versions`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/model-types/parameters/versions`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/model-capabilities/parameters/versions`;
          break;
        default:
          endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/versions`;
      }

      const response = await request(endpoint, {
        method: 'GET'
      });

      // 检查响应格式并转换数据
      let versionHistory = [];
      if (Array.isArray(response)) {
        versionHistory = response;
      } else if (response && Array.isArray(response.version_history)) {
        versionHistory = response.version_history;
      }

      return versionHistory;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getAllParameterVersions', 
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 获取参数继承树
  getParameterInheritanceTree: async (modelId, parameterName) => {
    try {
      const integerModelId = Number(modelId);
      if (isNaN(integerModelId) || integerModelId <= 0) {
        throw new Error('无效的模型ID');
      }
      
      if (!parameterName || parameterName.trim() === '') {
        throw new Error('参数名称不能为空');
      }
      
      const response = await request(`/v1/model-management/models/${integerModelId}/parameters/${parameterName}/inheritance-tree`, {
        method: 'GET'
      });

      return response;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getParameterInheritanceTree',
        `模型ID: ${modelId}, 参数名称: ${parameterName}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 获取参数审计日志
  getParameterAuditLogs: async (supplierId, modelId, parameterId, level = 'model', filters = {}) => {
    try {
      let endpoint;
      const integerSupplierId = supplierId ? Number(supplierId) : null;
      const integerModelId = modelId ? Number(modelId) : null;
      const integerParameterId = parameterId ? Number(parameterId) : null;

      // 构建查询参数
      const queryParams = new URLSearchParams();
      if (filters.startDate) queryParams.append('start_date', filters.startDate);
      if (filters.endDate) queryParams.append('end_date', filters.endDate);
      if (filters.operationType) queryParams.append('operation_type', filters.operationType);
      if (filters.username) queryParams.append('username', filters.username);
      if (filters.limit) queryParams.append('limit', filters.limit);
      if (filters.offset) queryParams.append('offset', filters.offset);

      const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';

      switch (level) {
        case 'system':
          if (integerParameterId) {
            endpoint = `/v1/model-management/system-parameters/${integerParameterId}/audit-logs${queryString}`;
          } else {
            endpoint = `/v1/model-management/system-parameters/audit-logs${queryString}`;
          }
          break;
        case 'supplier':
          if (integerParameterId) {
            endpoint = `/v1/suppliers/${integerSupplierId}/parameters/${integerParameterId}/audit-logs${queryString}`;
          } else {
            endpoint = `/v1/suppliers/${integerSupplierId}/parameters/audit-logs${queryString}`;
          }
          break;
        case 'model_type':
          if (integerParameterId) {
            endpoint = `/v1/model-management/model-types/parameters/${integerParameterId}/audit-logs${queryString}`;
          } else {
            endpoint = `/v1/model-management/model-types/parameters/audit-logs${queryString}`;
          }
          break;
        case 'model_capability':
          if (integerParameterId) {
            endpoint = `/v1/model-management/model-capabilities/parameters/${integerParameterId}/audit-logs${queryString}`;
          } else {
            endpoint = `/v1/model-management/model-capabilities/parameters/audit-logs${queryString}`;
          }
          break;
        default:
          if (integerParameterId) {
            endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${integerParameterId}/audit-logs${queryString}`;
          } else {
            endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/audit-logs${queryString}`;
          }
      }

      const response = await request(endpoint, {
        method: 'GET'
      });

      // 检查响应格式并转换数据
      let auditLogs = [];
      if (Array.isArray(response)) {
        auditLogs = response;
      } else if (response && Array.isArray(response.audit_logs)) {
        auditLogs = response.audit_logs;
      }

      // 处理分页信息
      const pagination = response && response.pagination ? response.pagination : {};

      return {
        auditLogs,
        pagination
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getParameterAuditLogs', 
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数ID: ${parameterId}, 筛选条件: ${JSON.stringify(filters)}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 获取审计日志的操作类型列表
  getAuditLogOperationTypes: async () => {
    try {
      const response = await request(`/v1/model-management/audit-log-operation-types`, {
        method: 'GET'
      });

      // 检查响应格式并转换数据
      let operationTypes = [];
      if (Array.isArray(response)) {
        operationTypes = response;
      } else if (response && Array.isArray(response.operation_types)) {
        operationTypes = response.operation_types;
      }

      return operationTypes;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getAuditLogOperationTypes'
      );
      throw new Error(errorObj.message);
    }
  },

  // 导出参数
  exportParameters: async (supplierId, modelId, level = 'model', format = 'json', filters = {}) => {
    try {
      let endpoint;
      const integerSupplierId = supplierId ? Number(supplierId) : null;
      const integerModelId = modelId ? Number(modelId) : null;

      // 构建查询参数
      const queryParams = new URLSearchParams();
      queryParams.append('format', format);
      if (filters.parameterNames) {
        filters.parameterNames.forEach(name => queryParams.append('parameter_names', name));
      }
      if (filters.includeInherited) queryParams.append('include_inherited', filters.includeInherited);
      if (filters.includeOverridden) queryParams.append('include_overridden', filters.includeOverridden);
      if (filters.parameterType) queryParams.append('parameter_type', filters.parameterType);

      const queryString = `?${queryParams.toString()}`;

      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/system-parameters/export${queryString}`;
          break;
        case 'supplier':
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters/export${queryString}`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/model-types/parameters/export${queryString}`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/model-capabilities/parameters/export${queryString}`;
          break;
        default:
          endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/export${queryString}`;
      }

      // 导出文件需要特殊处理，使用responseType: 'blob'
      const response = await request(endpoint, {
        method: 'GET',
        responseType: 'blob'
      });

      // 从响应头中获取文件名
      const contentDisposition = response.headers.get('content-disposition');
      let fileName = 'parameters';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          fileName = filenameMatch[1];
        }
      } else {
        // 如果没有响应头，使用默认文件名
        fileName += `.${format}`;
      }

      return {
        blob: response,
        fileName
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'exportParameters', 
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}, 格式: ${format}, 筛选条件: ${JSON.stringify(filters)}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 导入参数
  importParameters: async (supplierId, modelId, file, level = 'model', options = {}) => {
    try {
      let endpoint;
      const integerSupplierId = supplierId ? Number(supplierId) : null;
      const integerModelId = modelId ? Number(modelId) : null;

      switch (level) {
        case 'system':
          endpoint = `/v1/model-management/system-parameters/import`;
          break;
        case 'supplier':
          endpoint = `/v1/suppliers/${integerSupplierId}/parameters/import`;
          break;
        case 'model_type':
          endpoint = `/v1/model-management/model-types/parameters/import`;
          break;
        case 'model_capability':
          endpoint = `/v1/model-management/model-capabilities/parameters/import`;
          break;
        default:
          endpoint = `/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/import`;
      }

      // 创建FormData对象来上传文件
      const formData = new FormData();
      formData.append('file', file);
      
      // 添加导入选项
      if (options.mergeStrategy) formData.append('merge_strategy', options.mergeStrategy);
      if (options.overwriteExisting) formData.append('overwrite_existing', options.overwriteExisting);
      if (options.validateOnly) formData.append('validate_only', options.validateOnly);
      if (options.includeInherited) formData.append('include_inherited', options.includeInherited);

      const response = await request(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
          // 不要设置Content-Type，让浏览器自动设置
        }
      });

      return {
        success: response?.success || true,
        message: response?.message || '参数导入成功',
        importedCount: response?.imported_count || 0,
        updatedCount: response?.updated_count || 0,
        skippedCount: response?.skipped_count || 0,
        errors: response?.errors || []
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'importParameters', 
        `层级: ${level}, 供应商ID: ${supplierId}, 模型ID: ${modelId}, 选项: ${JSON.stringify(options)}`
      );
      throw new Error(errorObj.message);
    }
  },

  // 验证导入的参数文件
  validateImportParameters: async (file) => {
    try {
      const endpoint = `/v1/model-management/parameters/validate-import`;

      const formData = new FormData();
      formData.append('file', file);

      const response = await request(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
          // 不要设置Content-Type，让浏览器自动设置
        }
      });

      return {
        valid: response?.valid || false,
        message: response?.message || '',
        errors: response?.errors || [],
        warnings: response?.warnings || [],
        parameterCount: response?.parameter_count || 0
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'validateImportParameters'
      );
      throw new Error(errorObj.message);
    }
  },

  // 获取支持的导出格式列表
  getExportFormats: async () => {
    try {
      const response = await request(`/v1/model-management/parameter-export-formats`, {
        method: 'GET'
      });

      // 检查响应格式并转换数据
      let formats = [];
      if (Array.isArray(response)) {
        formats = response;
      } else if (response && Array.isArray(response.formats)) {
        formats = response.formats;
      }

      return formats;
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getExportFormats'
      );
      throw new Error(errorObj.message);
    }
  },



  // 模型实例参数API方法
  getModelParameters: async (supplierId, modelId) => {
    try {
      const integerSupplierId = Number(supplierId);
      const integerModelId = Number(modelId);
      
      if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
        throw new Error('无效的供应商ID');
      }
      
      if (isNaN(integerModelId) || integerModelId <= 0) {
        throw new Error('无效的模型ID');
      }
      
      const response = await request(`/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters`, {
        method: 'GET'
      });

      let parameters = [];
      if (Array.isArray(response)) {
        parameters = response;
      } else if (response && Array.isArray(response.parameters)) {
        parameters = response.parameters;
      }

      return parameters.map(formatParameterData);
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'getModelParameters',
        `供应商ID: ${supplierId}, 模型ID: ${modelId}`
      );
      throw new Error(errorObj.message);
    }
  },

  createModelParameter: async (supplierId, modelId, parameterData) => {
    try {
      const integerSupplierId = Number(supplierId);
      const integerModelId = Number(modelId);
      
      if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
        throw new Error('无效的供应商ID');
      }
      
      if (isNaN(integerModelId) || integerModelId <= 0) {
        throw new Error('无效的模型ID');
      }
      
      const formattedData = {
        parameter_name: parameterData.parameter_name || '',
        parameter_value: parameterData.parameter_value || '',
        parameter_type: parameterData.parameter_type || 'string',
        description: parameterData.description || ''
      };

      const response = await request(`/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters`, {
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
        'createModelParameter',
        `供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数数据: ${JSON.stringify(parameterData)}`
      );
      throw new Error(errorObj.message);
    }
  },

  updateModelParameter: async (supplierId, modelId, parameterName, parameterData) => {
    try {
      const integerSupplierId = Number(supplierId);
      const integerModelId = Number(modelId);
      
      if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
        throw new Error('无效的供应商ID');
      }
      
      if (isNaN(integerModelId) || integerModelId <= 0) {
        throw new Error('无效的模型ID');
      }
      
      if (!parameterName) {
        throw new Error('参数名称不能为空');
      }
      
      const formattedData = {
        parameter_value: parameterData.parameter_value || '',
        parameter_type: parameterData.parameter_type || 'string',
        description: parameterData.description || ''
      };

      const response = await request(`/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${encodeURIComponent(parameterName)}`, {
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
        'updateModelParameter',
        `供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数名称: ${parameterName}, 参数数据: ${JSON.stringify(parameterData)}`
      );
      throw new Error(errorObj.message);
    }
  },

  deleteModelParameter: async (supplierId, modelId, parameterName) => {
    try {
      const integerSupplierId = Number(supplierId);
      const integerModelId = Number(modelId);
      
      if (isNaN(integerSupplierId) || integerSupplierId <= 0) {
        throw new Error('无效的供应商ID');
      }
      
      if (isNaN(integerModelId) || integerModelId <= 0) {
        throw new Error('无效的模型ID');
      }
      
      if (!parameterName) {
        throw new Error('参数名称不能为空');
      }

      const response = await request(`/v1/suppliers/${integerSupplierId}/models/${integerModelId}/parameters/${encodeURIComponent(parameterName)}`, {
        method: 'DELETE'
      });

      return {
        success: true,
        message: response?.message || '参数删除成功',
        parameterName
      };
    } catch (error) {
      const errorObj = handleApiError(
        error, 
        'deleteModelParameter',
        `供应商ID: ${supplierId}, 模型ID: ${modelId}, 参数名称: ${parameterName}`
      );
      throw new Error(errorObj.message);
    }
  }
};

export default modelApi;