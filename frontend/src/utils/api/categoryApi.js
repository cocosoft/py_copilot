// 模型分类相关API
import { request } from '../apiUtils';

// 将扁平分类数据转换为树形结构
const buildCategoryTree = (categories) => {
  const categoryMap = {};
  const rootCategories = [];
  
  // 构建分类ID映射
  categories.forEach(category => {
    categoryMap[category.id] = {
      ...category,
      children: []
    };
  });
  
  // 构建树形结构
  categories.forEach(category => {
    if (category.parent_id === null || !categoryMap[category.parent_id]) {
      rootCategories.push(categoryMap[category.id]);
    } else {
      categoryMap[category.parent_id].children.push(categoryMap[category.id]);
    }
  });
  
  return rootCategories;
};

// 模型分类API实现
export const categoryApi = {
  // 获取所有分类
  getAll: async () => {
    try {
      const result = await request('/v1/categories/', {
        method: 'GET'
      });
      
      // 处理不同的数据格式返回
      let categoriesData = [];
      
      if (Array.isArray(result)) {
        categoriesData = result;
      } else if (result && Array.isArray(result.categories)) {
        categoriesData = result.categories;
      } else if (result && Array.isArray(result.data)) {
        categoriesData = result.data;
      }
      
      // 直接返回原始数据，不构建分类树
      return categoriesData;
    } catch (error) {
      console.error('❌ categoryApi.getAll - API调用失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取单个分类
  getById: async (categoryId) => {
    try {
      return await request(`/v1/categories/${categoryId}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取分类 ${categoryId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 创建分类
  create: async (categoryData) => {
    try {
      // 判断是否为FormData对象（用于文件上传）
      const isFormData = categoryData instanceof FormData;
      
      return await request('/v1/categories/', {
        method: 'POST',
        body: isFormData ? categoryData : JSON.stringify(categoryData),
        headers: isFormData ? {} : {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('创建分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 更新分类
  update: async (categoryId, categoryData) => {
    try {
      // 判断是否为FormData对象（用于文件上传）
      const isFormData = categoryData instanceof FormData;
      
      return await request(`/v1/categories/${categoryId}`, {
        method: 'PUT',
        body: isFormData ? categoryData : JSON.stringify(categoryData),
        headers: isFormData ? {} : {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`更新分类 ${categoryId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 删除分类
  delete: async (categoryId) => {
    try {
      return await request(`/v1/categories/${categoryId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除分类 ${categoryId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取分类树形结构
  getTree: async () => {
    try {
      return await request('/v1/categories/tree/all', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取分类树失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 添加模型分类关联
  addModelToCategory: async (modelId, categoryId) => {
    try {
      return await request('/v1/categories/associations', {
        method: 'POST',
        body: JSON.stringify({ id: modelId, category_id: categoryId }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      // 如果是409错误（关联已存在），不抛出异常，返回空对象
      if (error.message && error.message.includes('409')) {
        console.warn(`模型 ${modelId} 与分类 ${categoryId} 的关联已存在，跳过重复添加`);
        return {};
      }
      console.error('添加模型分类关联失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 移除模型分类关联
  removeModelFromCategory: async (modelId, categoryId) => {
    try {
      return await request(`/v1/categories/associations/model/${modelId}/category/${categoryId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('移除模型分类关联失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取分类下的模型
  getModelsByCategory: async (categoryId) => {
    try {
      return await request(`/v1/categories/${categoryId}/models`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取分类 ${categoryId} 下的模型失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 获取模型的分类
  getCategoriesByModel: async (modelId) => {
    try {
      return await request(`/v1/categories/model/${modelId}/categories`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取模型 ${modelId} 的分类失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 获取类型默认参数
  getParameters: async (categoryId) => {
    try {
      return await request(`/v1/categories/${categoryId}/parameters`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取分类 ${categoryId} 的默认参数失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 设置类型默认参数
  setParameters: async (categoryId, parameters) => {
    try {
      return await request(`/v1/categories/${categoryId}/parameters`, {
        method: 'POST',
        body: JSON.stringify(parameters),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`设置分类 ${categoryId} 的默认参数失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 删除类型默认参数
  deleteParameter: async (categoryId, paramName) => {
    try {
      return await request(`/v1/categories/${categoryId}/parameters/${paramName}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除分类 ${categoryId} 的参数 ${paramName} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 获取所有分类维度
  getAllDimensions: async () => {
    try {
      return await request('/v1/categories/dimensions/all', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取分类维度失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },
  
  // 按维度分组获取分类
  getCategoriesByDimension: async () => {
    try {
      return await request('/v1/categories/by-dimension', {
        method: 'GET'
      });
    } catch (error) {
      console.error('按维度获取分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 模板相关API方法
  getTemplates: async () => {
    try {
      return await request('/v1/category-templates', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取模板列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  getTemplateById: async (templateId) => {
    try {
      return await request(`/v1/category-templates/${templateId}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取模板 ${templateId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  createTemplate: async (templateData) => {
    try {
      return await request('/v1/category-templates', {
        method: 'POST',
        body: JSON.stringify(templateData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('创建模板失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  updateTemplate: async (templateId, templateData) => {
    try {
      return await request(`/v1/category-templates/${templateId}`, {
        method: 'PUT',
        body: JSON.stringify(templateData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`更新模板 ${templateId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  deleteTemplate: async (templateId) => {
    try {
      return await request(`/v1/category-templates/${templateId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除模板 ${templateId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  applyTemplate: async (templateId, categoryData = {}) => {
    try {
      return await request(`/v1/category-templates/${templateId}/apply`, {
        method: 'POST',
        body: JSON.stringify(categoryData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`应用模板 ${templateId} 失败:`, JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  exportTemplates: async (templateIds = null) => {
    try {
      const params = new URLSearchParams();
      if (templateIds && templateIds.length > 0) {
        templateIds.forEach(id => params.append('template_ids', id));
      }
      const url = `/v1/category-templates/export${params.toString() ? `?${params.toString()}` : ''}`;
      return await request(url, {
        method: 'GET'
      });
    } catch (error) {
      console.error('导出模板失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  importTemplates: async (templatesData, overwrite = false) => {
    try {
      return await request('/v1/category-templates/import', {
        method: 'POST',
        body: JSON.stringify({
          templates_data: templatesData,
          overwrite: overwrite
        }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('导入模板失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 获取主分类
  getPrimaryCategories: async (dimension = 'task_type') => {
    try {
      return await request(`/v1/categories/primary?dimension=${dimension}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取主分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 批量创建分类
  batchCreate: async (categoriesData) => {
    try {
      return await request('/v1/categories/batch', {
        method: 'POST',
        body: JSON.stringify(categoriesData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('批量创建分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 批量删除分类
  batchDelete: async (categoryIds) => {
    try {
      // 构建查询字符串
      const queryParams = new URLSearchParams();
      categoryIds.forEach(id => queryParams.append('category_ids', id));
      
      return await request(`/v1/categories/batch?${queryParams.toString()}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('批量删除分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 批量添加模型到分类
  batchAddModelsToCategory: async (categoryId, modelIds) => {
    try {
      // 构建查询字符串
      const queryParams = new URLSearchParams();
      queryParams.append('category_id', categoryId);
      modelIds.forEach(id => queryParams.append('model_ids', id));
      
      return await request(`/v1/categories/batch/model-associations?${queryParams.toString()}`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('批量添加模型到分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 高级查询分类
  search: async (params = {}) => {
    try {
      // 构建查询字符串
      const queryParams = new URLSearchParams();
      if (params.keyword) queryParams.append('keyword', params.keyword);
      if (params.dimension) queryParams.append('dimension', params.dimension);
      if (params.isActive !== undefined) queryParams.append('is_active', params.isActive);
      if (params.isSystem !== undefined) queryParams.append('is_system', params.isSystem);
      if (params.parentId) queryParams.append('parent_id', params.parentId);
      if (params.skip) queryParams.append('skip', params.skip);
      if (params.limit) queryParams.append('limit', params.limit);
      if (params.sortBy) queryParams.append('sort_by', params.sortBy);
      if (params.sortOrder) queryParams.append('sort_order', params.sortOrder);
      
      return await request(`/v1/categories/?${queryParams.toString()}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error('高级查询分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  // 获取分类统计信息
  getStatistics: async (params = {}) => {
    try {
      // 构建查询字符串
      const queryParams = new URLSearchParams();
      if (params.dimension) queryParams.append('dimension', params.dimension);
      if (params.includeChildren) queryParams.append('include_children', params.includeChildren);
      
      return await request(`/v1/categories/statistics?${queryParams.toString()}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取分类统计信息失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  }
};

export default categoryApi;
