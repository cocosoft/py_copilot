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
    console.log('🔄 categoryApi.getAll - 开始调用后端API');
    try {
      const result = await request('/model/categories', {
        method: 'GET'
      });
      
      console.log('🔄 categoryApi.getAll - 收到后端响应:', result);
      
      // 处理不同的数据格式返回
      let categoriesData = [];
      
      if (Array.isArray(result)) {
        categoriesData = result;
      } else if (result && Array.isArray(result.categories)) {
        categoriesData = result.categories;
      } else if (result && Array.isArray(result.data)) {
        categoriesData = result.data;
      }
      
      console.log('✅ categoryApi.getAll - 处理分类数据，数量:', categoriesData.length);
      // 构建分类树
      return buildCategoryTree(categoriesData);
    } catch (error) {
      console.error('❌ categoryApi.getAll - API调用失败:', error);
      throw error;
    }
  },
  
  // 获取单个分类
  getById: async (categoryId) => {
    try {
      return await request(`/model/categories/${categoryId}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取分类 ${categoryId} 失败:`, error);
      throw error;
    }
  },
  
  // 创建分类
  create: async (categoryData) => {
    try {
      return await request('/model/categories', {
        method: 'POST',
        body: JSON.stringify(categoryData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('创建分类失败:', error);
      throw error;
    }
  },
  
  // 更新分类
  update: async (categoryId, updatedData) => {
    try {
      return await request(`/model/categories/${categoryId}`, {
        method: 'PUT',
        body: JSON.stringify(updatedData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`更新分类 ${categoryId} 失败:`, error);
      throw error;
    }
  },
  
  // 删除分类
  delete: async (categoryId) => {
    try {
      return await request(`/model/categories/${categoryId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除分类 ${categoryId} 失败:`, error);
      throw error;
    }
  },
  
  // 获取分类树形结构
  getTree: async () => {
    try {
      return await request('/model/categories/tree/all', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取分类树失败:', error);
      throw error;
    }
  },
  
  // 添加模型分类关联
  addModelToCategory: async (modelId, categoryId) => {
    try {
      return await request('/model/categories/associations', {
        method: 'POST',
        body: JSON.stringify({ model_id: modelId, category_id: categoryId }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('添加模型分类关联失败:', error);
      throw error;
    }
  },
  
  // 移除模型分类关联
  removeModelFromCategory: async (modelId, categoryId) => {
    try {
      return await request(`/model/categories/associations/model/${modelId}/category/${categoryId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('移除模型分类关联失败:', error);
      throw error;
    }
  },
  
  // 获取分类下的模型
  getModelsByCategory: async (categoryId) => {
    try {
      return await request(`/model/categories/${categoryId}/models`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取分类 ${categoryId} 下的模型失败:`, error);
      throw error;
    }
  },
  
  // 获取模型的分类
  getCategoriesByModel: async (modelId) => {
    try {
      return await request(`/model/categories/model/${modelId}/categories`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取模型 ${modelId} 的分类失败:`, error);
      throw error;
    }
  }
};

export default categoryApi;