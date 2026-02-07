import { request } from '../apiUtils';

// 供应商相关API
export const supplierApi = {
  // 获取所有供应商
  getAll: async () => {
    try {
      const response = await request('/v1/suppliers-list', {
        method: 'GET'
      });

      // 处理后端返回格式
      let suppliersData = [];
      
      // 检查是否是对象格式，并且有suppliers属性
      if (typeof response === 'object' && response !== null && Array.isArray(response.suppliers)) {
        suppliersData = response.suppliers;
      } 
      // 检查是否直接返回了数组
      else if (Array.isArray(response)) {
        suppliersData = response;
      } else {
      }
      
      // 转换后端数据格式为前端所需格式，包含website、is_active和logo字段
      const formattedSuppliers = suppliersData.map(supplier => ({
        id: supplier.id,
        key: String(supplier.id),
        name: supplier.name || supplier.display_name || '',
        description: supplier.description || '',
        logo: supplier.logo || '',  // 添加logo字段
        category: supplier.category || '',  // 添加category字段
        apiUrl: supplier.api_endpoint || supplier.api_url || supplier.base_url || '',
        api_docs: supplier.api_docs || '',  // 添加api_docs字段
        website: supplier.website || '',  // 添加官网字段
        apiKeyRequired: supplier.api_key_required || (supplier.api_key ? true : false),
        api_key: supplier.api_key || '',  // 添加API密钥字段
        is_active: supplier.is_active !== undefined ? supplier.is_active : false // 添加is_active字段
      }));
      return formattedSuppliers;
    } catch (error) {
      // 处理500错误或其他API错误
      console.error('获取供应商列表失败:', error);
      
      // 如果是500错误，返回空数组以避免组件崩溃
      // 但也允许其他类型的错误抛出，以便更高级别的错误处理
      if (error.status === 500 || error.message.includes('状态码: 500')) {
        return [];
      }
      
      throw error;
    }
  },
  
  // 获取单个供应商
  getById: async (id) => {
    const endpoint = `/v1/suppliers/${id}`;
    
    // 调用API获取供应商详情
    const supplier = await request(endpoint, {
      method: 'GET'
    });

    // 格式化响应数据以匹配前端需求
    if (supplier) {
      return {
        id: supplier.id,
        key: String(supplier.id),
        name: supplier.name || supplier.display_name || '',
        logo: supplier.logo || '',  // 添加logo字段
        category: supplier.category || '',  // 添加category字段
        website: supplier.website || '',  // 添加官网字段
        description: supplier.description || '',
        apiUrl: supplier.api_endpoint || supplier.api_url || supplier.base_url || '',
        api_docs: supplier.api_docs || '',  // 添加api_docs字段
        api_key: supplier.api_key || '',  // 添加API密钥字段
        apiKeyRequired: supplier.api_key_required || (supplier.api_key ? true : false),
        is_active: supplier.is_active !== undefined ? supplier.is_active : false // 添加is_active字段
      };
    }
    return { error: 'Supplier not found' };
  },
  
  // 创建新供应商
  create: async (supplier) => {
    
    // 检查是否是FormData对象（用于文件上传）
    const isFormData = supplier instanceof FormData;
    let requestData = supplier;
    
    if (!isFormData) {
      // 修正字段映射，确保与数据库字段一致，使用新的字段名
      const backendSupplierData = {
          name: supplier.name,
          display_name: supplier.display_name || supplier.name || '', // 后端需要display_name字段
          description: supplier.description || '',
          logo: supplier.logo || '',
          category: supplier.category || '',
          website: supplier.website || '', // 确保正确处理website字段
          api_endpoint: supplier.api_endpoint || '',
          api_docs: supplier.api_docs || '',
          api_key: supplier.api_key || '',
          api_key_required: supplier.api_key_required !== undefined ? supplier.api_key_required : !!supplier.api_key,
          is_active: supplier.is_active !== undefined ? supplier.is_active : true
      };

      requestData = JSON.stringify(backendSupplierData);
    } else {

    }
    
    // 使用正确的API路径
    const requestOptions = {
      method: 'POST',
      body: requestData
    };
    
    // 只有非FormData时才设置Content-Type
    if (!isFormData) {
      requestOptions.headers = {
        'Content-Type': 'application/json'
      };
    }
    
    const response = await request('/v1/suppliers', requestOptions);
    
    // 格式化响应以匹配前端需求
    return {
      id: response.id,
      key: String(response.id),
      name: response.name,
      description: response.description || '',
      logo: response.logo || '',
      category: response.category || '',
      website: response.website || '',
      api_endpoint: response.api_endpoint || '',
      api_docs: response.api_docs || '',
      api_key: response.api_key || '',
      api_key_required: response.api_key_required,
      is_active: response.is_active
    };
  },
  
  // 只更新供应商状态(is_active)
  updateSupplierStatus: async (id, isActive) => {

    // 确保ID是数字类型
    const numericId = Number(id);

    
    // 使用专门的状态更新端点(PATCH请求)
    const endpoint = `/v1/suppliers/${numericId}/status`;

    // 发送PATCH请求，使用JSON格式
    const response = await request(endpoint, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ is_active: isActive })
    });
    

    // 返回更新后的供应商数据
    return {
      id: response.id,
      key: String(response.id),
      name: response.name,
      display_name: response.display_name,
      description: response.description || '',
      website: response.website || '',
      api_endpoint: response.api_endpoint || '',
      api_docs: response.api_docs || '',
      api_key: response.api_key || '',
      api_key_required: response.api_key_required,
      is_active: response.is_active
    };
  },
  
  // 更新供应商（部分更新）
  update: async (id, updatedSupplier) => {

    // 确保ID是数字类型
    const numericId = Number(id);

    // 检查是否是FormData对象（用于文件上传）
    const isFormData = updatedSupplier instanceof FormData;
    let requestData = updatedSupplier;
    
    if (!isFormData) {
      // 只发送请求中包含的字段，避免覆盖现有值
      const backendUpdateData = {};
      
      // 只复制updatedSupplier中实际存在的字段
      for (const [key, value] of Object.entries(updatedSupplier)) {
        if (value !== undefined && value !== null) {
          backendUpdateData[key] = value;
        }
      }
      
      // 确保api_endpoint和api_key使用正确的字段名
      if (backendUpdateData.apiUrl) {
        backendUpdateData.api_endpoint = backendUpdateData.apiUrl;
        delete backendUpdateData.apiUrl;
      }
      
      requestData = JSON.stringify(backendUpdateData);
    } else {
    }
    
    // 修正endpoint，后端路由是/api/v1/suppliers/{id}
    const endpoint = `/v1/suppliers/${numericId}`;

    // 准备请求选项
    const requestOptions = {
      method: 'PUT',
      body: requestData
    };
    
    // 只有非FormData时才设置Content-Type
    if (!isFormData) {
      requestOptions.headers = {
        'Content-Type': 'application/json'
      };
    }
    
    // 直接发送请求，不使用嵌套try-catch，确保错误正确抛出
    const response = await request(endpoint, requestOptions);
    

    // 格式化响应以匹配前端需求
    return {
      id: response.id,
      key: String(response.id),
      name: response.name,
      description: response.description || '',
      logo: response.logo || '',
      category: response.category || '',
      website: response.website || '',
      api_endpoint: response.api_endpoint || '',
      api_docs: response.api_docs || '',
      api_key: response.api_key || '',
      api_key_required: response.api_key_required,
      is_active: response.is_active
    };
  },
  
  // 删除供应商
  delete: async (id) => {
    const endpoint = `/v1/suppliers/${id}`;
    return await request(endpoint, {
      method: 'DELETE'
    });
  },

  // 测试API配置
  testApiConfig: async (id, apiConfig) => {
    // 确保ID是数字类型
    const numericId = Number(id);
    
    const endpoint = `/v1/suppliers/${numericId}/test-api`;
    const response = await request(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        apiUrl: apiConfig.apiUrl,
        apiKey: apiConfig.apiKey
      }),
      timeout: 60000 // 测试API连接设置60秒超时
    });
    
    // 检查后端返回的状态
    if (response.status === 'error') {
      // 构建错误信息
      let errorMessage = response.message;
      if (response.response_text) {
        errorMessage += `: ${response.response_text}`;
      }
      
      // 抛出错误，让前端的错误处理逻辑捕获
      const error = new Error(errorMessage);
      error.response = response;
      throw error;
    }
    
    return response;
  },

  // 从API获取模型列表
  fetchModelsFromApi: async (id, apiConfig) => {
    
    // 确保id是数字
    const numericId = parseInt(id, 10);
    if (isNaN(numericId)) {
      throw new Error('供应商ID必须是有效的数字');
    }
    
    // 添加调试信息（对API密钥进行脱敏处理）
    const maskedConfig = {
      apiUrl: apiConfig.apiUrl,
      apiKey: apiConfig.apiKey ? `${apiConfig.apiKey.substring(0, 8)}...` : ''
    };
    console.log('调用fetchModelsFromApi，传递的apiConfig:', JSON.stringify(maskedConfig, null, 2));
    
    const endpoint = `/v1/suppliers/${numericId}/fetch-models`;
    const response = await request(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        apiUrl: apiConfig.apiUrl,
        apiKey: apiConfig.apiKey
      })
    });
    
    // 检查后端返回的状态
    if (response.status === 'error') {
      // 构建错误信息
      let errorMessage = response.message;
      
      // 抛出错误，让前端的错误处理逻辑捕获
      const error = new Error(errorMessage);
      error.response = response;
      throw error;
    }
    
    return response;
  },

  // 获取所有模型
  getModels: async () => {
    try {
      const response = await request('/v1/models', {
        method: 'GET'
      });
      
      // 处理后端返回格式
      let modelsData = [];
      
      // 后端返回的是直接数组格式
      if (Array.isArray(response)) {
        modelsData = response;
      }
      // 如果是对象格式，检查是否有items属性
      else if (typeof response === 'object' && response !== null && Array.isArray(response.items)) {
        modelsData = response.items;
      }
      // 如果是对象格式且有models属性
      else if (typeof response === 'object' && response !== null && Array.isArray(response.models)) {
        modelsData = response.models;
      }
      
      return modelsData;
    } catch (error) {
      console.error('获取模型列表失败:', error);
      throw error;
    }
  },

  // 根据场景获取模型
  getModelsByScene: async (scene) => {
    try {
      const response = await request(`/v1/models/by-scene/${scene}`, {
        method: 'GET'
      });
      
      // 处理后端返回格式
      let modelsData = [];
      
      // 后端返回的是直接数组格式
      if (Array.isArray(response)) {
        modelsData = response;
      }
      // 如果是对象格式，检查是否有items属性
      else if (typeof response === 'object' && response !== null && Array.isArray(response.items)) {
        modelsData = response.items;
      }
      // 如果是对象格式且有models属性
      else if (typeof response === 'object' && response !== null && Array.isArray(response.models)) {
        modelsData = response.models;
      }
      
      return modelsData;
    } catch (error) {
      console.error(`获取场景 ${scene} 的模型列表失败:`, error);
      throw error;
    }
  },

  // 获取模型的能力分数
  getModelCapabilityScores: async (modelId, scene) => {
    try {
      const response = await request(`/v1/models/${modelId}/capability-scores/${scene}`, {
        method: 'GET'
      });
      
      return response;
    } catch (error) {
      console.error(`获取模型 ${modelId} 在场景 ${scene} 的能力分数失败:`, error);
      throw error;
    }
  },

  // 获取本地模型列表
  getLocalModels: async () => {
    try {
      const response = await request('/v1/local-models', {
        method: 'GET'
      });
      
      // 处理后端返回格式
      let modelsData = [];
      
      // 后端返回的是直接数组格式
      if (Array.isArray(response)) {
        modelsData = response;
      }
      // 如果是对象格式，检查是否有items属性
      else if (typeof response === 'object' && response !== null && Array.isArray(response.items)) {
        modelsData = response.items;
      }
      // 如果是对象格式且有models属性
      else if (typeof response === 'object' && response !== null && Array.isArray(response.models)) {
        modelsData = response.models;
      }
      
      return modelsData;
    } catch (error) {
      console.error('获取本地模型列表失败:', error);
      throw error;
    }
  }
};

export default supplierApi;