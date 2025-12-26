import { request } from '../apiUtils';

const parameterTemplatesApi = {
  /**
   * 获取参数模板列表
   * @param {number} skip - 跳过的记录数
   * @param {number} limit - 返回的最大记录数
   */
  async getTemplates(skip = 0, limit = 100) {
    return request(`/v1/parameter-templates?skip=${skip}&limit=${limit}`, { method: 'GET' });
  },

  /**
   * 获取单个参数模板
   * @param {number} templateId - 参数模板ID
   */
  async getTemplate(templateId) {
    return request(`/v1/parameter-templates/${templateId}`, { method: 'GET' });
  },

  /**
   * 获取参数模板的参数列表
   * @param {number} templateId - 参数模板ID
   */
  async getTemplateParameters(templateId) {
    try {
      const template = await this.getTemplate(templateId);
      return template.parameters || [];
    } catch (error) {
      console.error('获取模板参数失败:', error);
      return [];
    }
  },

  /**
   * 创建参数模板
   * @param {object} templateData - 参数模板数据
   */
  async createTemplate(templateData) {
    return request('/v1/parameter-templates', { 
      method: 'POST', 
      body: JSON.stringify(templateData), 
      headers: { 'Content-Type': 'application/json' } 
    });
  },

  /**
   * 更新参数模板
   * @param {number} templateId - 参数模板ID
   * @param {object} templateData - 更新的参数模板数据
   */
  async updateTemplate(templateId, templateData) {
    return request(`/v1/parameter-templates/${templateId}`, { 
      method: 'PUT', 
      body: JSON.stringify(templateData), 
      headers: { 'Content-Type': 'application/json' } 
    });
  },

  /**
   * 删除参数模板
   * @param {number} templateId - 参数模板ID
   */
  async deleteTemplate(templateId) {
    return request(`/v1/parameter-templates/${templateId}`, { method: 'DELETE' });
  },

  /**
   * 将参数模板应用到模型
   * @param {number} modelId - 模型ID
   * @param {number} templateId - 参数模板ID
   * @param {string} dimension - 维度标识（可选）
   */
  async applyTemplateToModel(modelId, templateId, dimension = null) {
    try {
      const parameters = await this.getTemplateParameters(templateId);
      
      // 这里返回参数列表，由调用方负责创建具体的模型参数
      return parameters.map(param => ({
        ...param,
        dimension: dimension
      }));
    } catch (error) {
      console.error('应用参数模板失败:', error);
      throw error;
    }
  }
};

export default parameterTemplatesApi;