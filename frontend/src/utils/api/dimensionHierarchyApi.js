import { request } from '../apiUtils';

const dimensionHierarchyApi = {
  // 获取完整的维度层次结构
  getHierarchy: async () => {
    try {
      // 尝试使用可能的API端点
      const endpoints = [
        '/v1/dimension-hierarchy/hierarchy',
        '/api/v1/dimension-hierarchy/hierarchy',
        '/v1/dimensions/hierarchy'
      ];
      
      let response;
      for (const endpoint of endpoints) {
        try {
          response = await request(endpoint, { method: 'GET' });
          console.log(`维度层次结构API响应 (${endpoint}):`, response);
          return response;
        } catch (err) {
          console.warn(`尝试端点 ${endpoint} 失败:`, err.message);
          // 继续尝试下一个端点
        }
      }
      
      // 如果所有端点都失败，抛出最后一个错误
      throw new Error('所有维度API端点都失败');
    } catch (error) {
      console.error('获取维度层次结构失败:', error);
      // 出错时返回默认维度数据
      return {
        dimensions: {
          tasks: {
            name: 'tasks',
            display_name: '任务维度',
            categories: []
          },
          languages: {
            name: 'languages',
            display_name: '语言维度',
            categories: []
          },
          licenses: {
            name: 'licenses',
            display_name: '协议维度',
            categories: []
          },
          technologies: {
            name: 'technologies',
            display_name: '技术维度',
            categories: []
          }
        }
      };
    }
  },

  // 根据维度和分类获取模型列表
  getModelsByDimensionAndCategory: async (dimension, categoryId) => {
    try {
      const response = await request(`/v1/dimension_hierarchy/dimensions/${dimension}/categories/${categoryId}/models`, { method: 'GET' });
      return response.models;
    } catch (error) {
      console.error('获取模型列表失败:', error);
      throw error;
    }
  },

  // 获取模型所属的所有维度和分类
  getModelDimensions: async (modelId) => {
    try {
      const response = await request(`/v1/dimension_hierarchy/models/${modelId}/dimensions`, { method: 'GET' });
      return response;
    } catch (error) {
      console.error('获取模型维度信息失败:', error);
      throw error;
    }
  },

  // 将模型添加到指定维度的分类中
  addModelToDimensionCategory: async (modelId, dimension, categoryId, weight = 0, associationType = 'primary') => {
    try {
      const response = await request(`/v1/dimension_hierarchy/models/${modelId}/dimensions/${dimension}/categories/${categoryId}`, {
        method: 'POST',
        data: {
          weight,
          association_type: associationType
        }
      });
      return response;
    } catch (error) {
      console.error('添加模型到维度分类失败:', error);
      throw error;
    }
  },

  // 从指定维度的分类中移除模型
  removeModelFromDimensionCategory: async (modelId, categoryId) => {
    try {
      const response = await request(`/v1/dimension_hierarchy/models/${modelId}/categories/${categoryId}`, { method: 'DELETE' });
      return response;
    } catch (error) {
      console.error('从维度分类中移除模型失败:', error);
      throw error;
    }
  },

  // 验证模型在指定维度下的约束条件
  validateDimensionConstraints: async (dimension, modelId) => {
    try {
      const response = await request(`/v1/dimension_hierarchy/dimensions/${dimension}/constraints/${modelId}`, { method: 'GET' });
      return response;
    } catch (error) {
      console.error('验证维度约束失败:', error);
      throw error;
    }
  }
};

export default dimensionHierarchyApi;