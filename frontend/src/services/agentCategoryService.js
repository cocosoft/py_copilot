// 智能体分类API服务
import { API_BASE_URL, request } from '../utils/apiUtils';

// 智能体分类API的基本路径
const AGENT_CATEGORY_API_BASE = '/v1/agent-categories'

// 类型检查辅助函数
const checkResponseType = (response, expectedType) => {
  if (!response || typeof response !== 'object') {
    throw new Error('无效的响应格式');
  }
  if (expectedType === 'list' && !Array.isArray(response.categories)) {
    throw new Error('智能体分类列表格式错误');
  }
  if (expectedType === 'single' && !response.id) {
    throw new Error('智能体分类详情格式错误');
  }
  if (expectedType === 'tree' && !Array.isArray(response.categories)) {
    throw new Error('智能体分类树格式错误');
  }
}

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
    checkResponseType(response, 'single');
    return response;
  } catch (error) {
    console.error('创建智能体分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 获取智能体分类详情
export const getAgentCategory = async (categoryId) => {
  try {
    const response = await request(`${AGENT_CATEGORY_API_BASE}/${categoryId}`);
    checkResponseType(response, 'single');
    return response;
  } catch (error) {
    console.error('获取智能体分类详情失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 获取智能体分类列表
export const getAgentCategories = async () => {
  try {
    const response = await request(`${AGENT_CATEGORY_API_BASE}/`);
    checkResponseType(response, 'list');
    return response;
  } catch (error) {
    console.error('获取智能体分类列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
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
    checkResponseType(response, 'single');
    return response;
  } catch (error) {
    console.error('更新智能体分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
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
    console.error('删除智能体分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 获取智能体分类树结构
export const getAgentCategoryTree = async () => {
  try {
    const response = await request(`${AGENT_CATEGORY_API_BASE}/tree/`);
    checkResponseType(response, 'tree');
    return response;
  } catch (error) {
    console.error('获取智能体分类树失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};