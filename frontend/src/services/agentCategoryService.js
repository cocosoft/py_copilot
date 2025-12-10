// 智能体分类API服务
import { API_BASE_URL, request } from '../utils/apiUtils';

// 智能体分类API的基本路径
const AGENT_CATEGORY_API_BASE = '/agent-categories'

// 创建智能体分类
export const createAgentCategory = async (categoryData) => {
  try {
    const response = await request(`${AGENT_CATEGORY_API_BASE}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(categoryData)
    });
    return response;
  } catch (error) {
    console.error('创建智能体分类失败:', error);
    throw error;
  }
};

// 获取智能体分类详情
export const getAgentCategory = async (categoryId) => {
  try {
    const response = await request(`${AGENT_CATEGORY_API_BASE}/${categoryId}`);
    return response;
  } catch (error) {
    console.error('获取智能体分类详情失败:', error);
    throw error;
  }
};

// 获取智能体分类列表
export const getAgentCategories = async () => {
  try {
    const response = await request(`${AGENT_CATEGORY_API_BASE}/`);
    return response;
  } catch (error) {
    console.error('获取智能体分类列表失败:', error);
    throw error;
  }
};

// 更新智能体分类
export const updateAgentCategory = async (categoryId, categoryData) => {
  try {
    const response = await request(`${AGENT_CATEGORY_API_BASE}/${categoryId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(categoryData)
    });
    return response;
  } catch (error) {
    console.error('更新智能体分类失败:', error);
    throw error;
  }
};

// 删除智能体分类
export const deleteAgentCategory = async (categoryId) => {
  try {
    await request(`${AGENT_CATEGORY_API_BASE}/${categoryId}`, {
      method: 'DELETE'
    });
    return true;
  } catch (error) {
    console.error('删除智能体分类失败:', error);
    throw error;
  }
};