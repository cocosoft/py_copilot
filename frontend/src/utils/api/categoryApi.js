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
      const result = await request('/v1/categories', {
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
      
      // 构建分类树
      return buildCategoryTree(categoriesData);
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
      
      return await request('/v1/categories', {
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
        body: JSON.stringify({ model_id: modelId, category_id: categoryId }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
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
  }
};

export default categoryApi;