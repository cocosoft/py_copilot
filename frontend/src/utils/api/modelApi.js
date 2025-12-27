import { request } from '../apiUtils';

const modelApi = {
  // 参数管理相关API
  
  /**
   * 获取参数列表
   * @param {number|null} supplierId - 供应商ID
   * @param {number|null} modelId - 模型ID
   * @param {string} level - 参数级别 (model, agent)
   */
  async getParameters(supplierId, modelId, level) {
    let endpoint = '/v1/model-management/parameters';
    
    // 根据级别构建不同的查询参数
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (supplierId) params.append('supplier_id', supplierId);
    if (modelId) params.append('id', modelId);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return request(endpoint, { method: 'GET' });
  },

  /**
   * 创建参数
   * @param {number|null} supplierId - 供应商ID
   * @param {number|null} modelId - 模型ID
   * @param {object} parameterData - 参数数据
   * @param {string} level - 参数级别
   */
  async createParameter(supplierId, modelId, parameterData, level) {
    try {
      // 尝试使用不同的API端点和方法
      const endpoints = [
        { path: '/v1/model-management/parameters', method: 'POST' },
        { path: '/v1/parameters', method: 'POST' },
        { path: '/v1/model-management/parameters', method: 'POST' },
        { path: '/v1/model-management/parameters', method: 'PUT' },
        { path: '/v1/parameters', method: 'PUT' },
        { path: '/v1/model-management/parameters', method: 'PUT' }
      ];
      
      // 构建查询参数
      const params = new URLSearchParams();
      if (level) params.append('level', level);
      if (supplierId) params.append('supplier_id', supplierId);
      if (modelId) params.append('model_id', modelId);
      
      for (const endpointConfig of endpoints) {
        try {
          let endpoint = endpointConfig.path;
          if (params.toString()) {
            endpoint += `?${params.toString()}`;
          }
          
          const response = await request(endpoint, {
            method: endpointConfig.method,
            body: JSON.stringify(parameterData),
            headers: { 'Content-Type': 'application/json' }
          });
          console.log(`参数创建API响应 (${endpointConfig.method} ${endpoint}):`, response);
          return response;
        } catch (err) {
          console.warn(`尝试端点 ${endpointConfig.method} ${endpointConfig.path} 失败:`, err.message);
          // 继续尝试下一个端点
        }
      }
      
      // 如果所有尝试都失败，返回默认数据
      console.warn('所有参数创建API端点都失败，返回默认数据');
      return {};
    } catch (error) {
      console.error('创建参数失败:', error);
      // 出错时返回默认数据
      return {};
    }
  },

  /**
   * 更新参数
   * @param {number|null} supplierId - 供应商ID
   * @param {number|null} modelId - 模型ID
   * @param {number} parameterId - 参数ID
   * @param {object} parameterData - 参数数据
   * @param {string} level - 参数级别
   */
  async updateParameter(supplierId, modelId, parameterId, parameterData, level) {
    let endpoint = `/v1/model-management/parameters/${parameterId}`;
    
    // 根据级别构建不同的查询参数
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (supplierId) params.append('supplier_id', supplierId);
    if (modelId) params.append('id', modelId);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return request(endpoint, { method: 'PUT', body: JSON.stringify(parameterData), headers: { 'Content-Type': 'application/json' } });
  },

  /**
   * 删除参数
   * @param {number|null} supplierId - 供应商ID
   * @param {number|null} modelId - 模型ID
   * @param {number} parameterId - 参数ID
   * @param {string} level - 参数级别
   */
  async deleteParameter(supplierId, modelId, parameterId, level) {
    let endpoint = `/v1/model-management/parameters/${parameterId}`;
    
    // 根据级别构建不同的查询参数
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (supplierId) params.append('supplier_id', supplierId);
    if (modelId) params.append('model_id', modelId);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return request(endpoint, { method: 'DELETE' });
  },

  // 参数模板相关API
  
  /**
   * 获取参数模板列表
   * @param {string} level - 模板级别 (model_type, model, agent)
   */
  async getParameterTemplates(level) {
    let endpoint = '/v1/parameter-templates';
    
    if (level) {
      endpoint += `?level=${level}`;
    }
    
    const response = await request(endpoint, { method: 'GET' });
    return response.templates || [];
  },

  /**
   * 创建参数模板
   * @param {object} templateData - 模板数据
   */
  async createParameterTemplate(templateData) {
    return request('/v1/parameter-templates', { method: 'POST', body: JSON.stringify(templateData), headers: { 'Content-Type': 'application/json' } });
  },

  /**
   * 更新参数模板
   * @param {number} templateId - 模板ID
   * @param {object} templateData - 模板数据
   */
  async updateParameterTemplate(templateId, templateData) {
    return request(`/v1/parameter-templates/${templateId}`, { method: 'PUT', body: JSON.stringify(templateData), headers: { 'Content-Type': 'application/json' } });
  },

  /**
   * 删除参数模板
   * @param {number} templateId - 模板ID
   */
  async deleteParameterTemplate(templateId) {
    return request(`/v1/parameter-templates/${templateId}`, { method: 'DELETE' });
  },

  /**
   * 应用参数模板
   * @param {number|null} supplierId - 供应商ID
   * @param {number|null} modelId - 模型ID
   * @param {number} templateId - 模板ID
   */
  async applyParameterTemplate(supplierId, modelId, templateId) {
    try {
      console.log('applyParameterTemplate调用参数:', { supplierId, modelId, templateId });
      
      // 验证参数类型
      console.log('参数类型检查:', { 
        supplierIdType: typeof supplierId, 
        modelIdType: typeof modelId, 
        templateIdType: typeof templateId 
      });
      
      // 尝试使用不同的API端点
      const endpoints = [];
      
      // 只在supplierId和modelId都有效时添加sync-parameters端点
      if (supplierId && modelId && templateId) {
        const syncEndpoint = `/v1/suppliers/${supplierId}/models/${modelId}/sync-parameters`;
        endpoints.push(syncEndpoint);
        console.log('添加sync-parameters端点:', syncEndpoint);
      } else {
        console.warn('跳过sync-parameters端点，因为参数不完整:', { supplierId, modelId, templateId });
      }
      
      // 添加传统端点
      endpoints.push(
        `/v1/model-management/parameter-templates/${templateId}/apply`,
        `/v1/parameter-templates/${templateId}/apply`,
        `/v1/model-management/templates/${templateId}/apply`,
        `/v1/templates/${templateId}/apply`
      );
      
      console.log('将尝试的API端点:', endpoints);
      
      for (const endpoint of endpoints) {
        try {
          console.log(`正在尝试端点: ${endpoint}`);
          let requestOptions = { method: 'POST' };
          let fullEndpoint = endpoint;
          
          // 根据端点类型设置不同的请求参数
          if (endpoint.includes('/sync-parameters')) {
            // 使用sync-parameters端点的请求体格式
            requestOptions.body = JSON.stringify({ template_id: templateId });
            requestOptions.headers = { 'Content-Type': 'application/json' };
            console.log(`sync-parameters请求配置:`, { fullEndpoint, requestOptions });
          } else {
            // 使用旧的查询参数格式
            const params = new URLSearchParams();
            if (supplierId) params.append('supplier_id', supplierId);
            if (modelId) params.append('model_id', modelId);
            const paramsString = params.toString();
            if (paramsString) {
              fullEndpoint += `?${paramsString}`;
            }
            console.log(`传统端点请求配置:`, { fullEndpoint, requestOptions });
          }
          
          const response = await request(fullEndpoint, requestOptions);
          console.log(`应用参数模板成功 (${fullEndpoint}):`, response);
          return response;
        } catch (err) {
          console.warn(`尝试端点 ${endpoint} 失败:`, err.message);
          // 继续尝试下一个端点
        }
      }
      
      // 如果所有端点都失败，抛出最后一个错误
      throw new Error('所有应用参数模板的API端点都失败');
    } catch (error) {
      console.error('应用参数模板失败:', error);
      throw error;
    }
  },

  // 参数继承树相关API
  
  /**
   * 获取参数继承树
   * @param {number|null} supplierId - 供应商ID
   * @param {number|null} modelId - 模型ID
   */
  async getParameterInheritanceTree(supplierId, modelId) {
    let endpoint = '/v1/model-management/parameter-inheritance-tree';
    
    // 构建查询参数
    const params = new URLSearchParams();
    if (supplierId) params.append('supplier_id', supplierId);
    if (modelId) params.append('model_id', modelId);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return request(endpoint, { method: 'GET' });
  },

  // 参数版本相关API
  
  /**
   * 获取参数版本历史
   * @param {number} parameterId - 参数ID
   */
  async getParameterVersions(parameterId) {
    return request(`/v1/model-management/parameters/${parameterId}/versions`, { method: 'GET' });
  },
  
  /**
   * 根据模型ID和维度获取参数
   * @param {string} modelId - 模型ID
   * @param {string} dimension - 维度
   */
  async getModelParameters(modelId, dimension) {
    try {
      // 检查模型ID是否包含斜杠（如供应商/模型ID格式）
      if (typeof modelId === 'string' && modelId.includes('/')) {
        console.log('检测到包含斜杠的模型ID，直接返回空参数数组');
        return [];
      }
      
      // 尝试使用可能的API端点
      const endpoints = [
        `/v1/model-management/models/${modelId}/dimensions/${dimension}/parameters`
      ];
      
      let response;
      for (const endpoint of endpoints) {
        try {
          response = await request(endpoint, { method: 'GET' });
          console.log(`模型维度参数API响应 (${endpoint}):`, response);
          return response.parameters || [];
        } catch (err) {
          console.warn(`尝试端点 ${endpoint} 失败:`, err.message);
          // 继续尝试下一个端点
        }
      }
      
      // 如果所有端点都失败，返回默认数据
      console.warn('所有模型维度参数API端点都失败，返回空数组');
      return [];
    } catch (error) {
      console.error('获取模型维度参数失败:', error);
      // 出错时返回默认数据
      return [];
    }
  },

  /**
   * 回滚参数到指定版本
   * @param {number} parameterId - 参数ID
   * @param {number} versionId - 版本ID
   */
  async revertParameterToVersion(parameterId, versionId) {
    return request(`/v1/model-management/parameters/${parameterId}/revert/${versionId}`, { method: 'POST' });
  },

  // 模型管理相关API
  
  /**
   * 根据供应商ID获取模型列表
   * @param {number} supplierId - 供应商ID
   */
  async getBySupplier(supplierId) {
    return request(`/v1/suppliers/${supplierId}/models`, { method: 'GET' });
  },

  /**
   * 获取模型详情
   * @param {number} modelId - 模型ID
   */
  async getById(modelId) {
    return request(`/v1/model-management/models/${modelId}`, { method: 'GET' });
  },

  /**
   * 创建模型
   * @param {number} supplierId - 供应商ID
   * @param {object|FormData} modelData - 模型数据或FormData对象
   */
  async create(supplierId, modelData) {
    // 检查是否是FormData对象
    const isFormData = modelData instanceof FormData;
    const options = { 
      method: 'POST', 
      body: isFormData ? modelData : JSON.stringify(modelData)
    };
    
    // 如果不是FormData对象，设置Content-Type为application/json
    if (!isFormData) {
      options.headers = { 'Content-Type': 'application/json' };
    }
    
    return request(`/v1/model-management/suppliers/${supplierId}/models`, options);
  },

  /**
   * 更新模型
   * @param {number} supplierId - 供应商ID
   * @param {number} modelId - 模型ID
   * @param {object|FormData} modelData - 模型数据或FormData对象
   */
  async update(supplierId, modelId, modelData) {
    // 检查是否是FormData对象
    const isFormData = modelData instanceof FormData;
    const options = { 
      method: 'PUT', 
      body: isFormData ? modelData : JSON.stringify(modelData)
    };
    
    // 如果不是FormData对象，设置Content-Type为application/json
    if (!isFormData) {
      options.headers = { 'Content-Type': 'application/json' };
    }
    
    return request(`/v1/model-management/suppliers/${supplierId}/models/${modelId}`, options);
  },

  /**
   * 删除模型
   * @param {number} supplierId - 供应商ID
   * @param {number} modelId - 模型ID
   */
  async delete(supplierId, modelId) {
    return request(`/v1/model-management/suppliers/${supplierId}/models/${modelId}`, { method: 'DELETE' });
  },

  // 系统参数相关API
  
  /**
   * 获取系统参数模板
   */
  async getSystemParameterTemplates() {
    return request('/v1/system/parameter-templates', { method: 'GET' });
  },

  /**
   * 获取活跃的系统参数模板
   */
  async getActiveSystemParameterTemplate() {
    return request('/v1/system/parameter-templates/active', { method: 'GET' });
  },

  /**
   * 激活系统参数模板
   * @param {number} templateId - 模板ID
   */
  async activateSystemParameterTemplate(templateId) {
    return request(`/v1/system/parameter-templates/${templateId}/activate`, { method: 'POST' });
  }
};

export default modelApi;