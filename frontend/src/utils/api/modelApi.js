import { request } from '../apiUtils';

const modelApi = {
  // 参数管理相关API
  
  /**
   * 获取参数列表
   * @param {number|null} supplierId - 供应商ID
   * @param {number|null} modelId - 模型ID
   * @param {string} level - 参数级别 (system, supplier, model_type, model_capability, model, agent)
   */
  async getParameters(supplierId, modelId, level) {
    let endpoint = '/v1/model-management/parameters';
    
    // 根据级别构建不同的查询参数
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (supplierId) params.append('supplier_id', supplierId);
    if (modelId) params.append('model_id', modelId);
    
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
    let endpoint = '/v1/model-management/parameters';
    
    // 根据级别构建不同的查询参数
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (supplierId) params.append('supplier_id', supplierId);
    if (modelId) params.append('model_id', modelId);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return request(endpoint, { method: 'POST', body: JSON.stringify(parameterData), headers: { 'Content-Type': 'application/json' } });
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
    if (modelId) params.append('model_id', modelId);
    
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
   * @param {string} level - 模板级别 (system, supplier, model_type, model_capability, model, agent)
   */
  async getParameterTemplates(level) {
    let endpoint = '/v1/parameter-templates';
    
    if (level) {
      endpoint += `?level=${level}`;
    }
    
    return request(endpoint, { method: 'GET' });
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
    let endpoint = `/v1/parameter-templates/${templateId}/apply`;
    
    // 根据级别构建不同的查询参数
    const params = new URLSearchParams();
    if (supplierId) params.append('supplier_id', supplierId);
    if (modelId) params.append('model_id', modelId);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return request(endpoint, { method: 'POST' });
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
   * @param {object} modelData - 模型数据
   */
  async create(modelData) {
    return request('/v1/model-management/models', { method: 'POST', body: JSON.stringify(modelData), headers: { 'Content-Type': 'application/json' } });
  },

  /**
   * 更新模型
   * @param {number} modelId - 模型ID
   * @param {object} modelData - 模型数据
   */
  async update(modelId, modelData) {
    return request(`/v1/model-management/models/${modelId}`, { method: 'PUT', body: JSON.stringify(modelData), headers: { 'Content-Type': 'application/json' } });
  },

  /**
   * 删除模型
   * @param {number} modelId - 模型ID
   */
  async delete(modelId) {
    return request(`/v1/model-management/models/${modelId}`, { method: 'DELETE' });
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