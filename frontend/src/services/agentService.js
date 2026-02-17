// 智能体管理API服务
import { API_BASE_URL, request } from '../utils/apiUtils';

// 智能体API的基本路径
const AGENT_API_BASE = '/v1/agents'

// 类型检查辅助函数
const checkResponseType = (response, expectedType) => {
  if (!response || typeof response !== 'object') {
    throw new Error('无效的响应格式');
  }
  if (expectedType === 'list' && !Array.isArray(response.agents)) {
    throw new Error('智能体列表格式错误');
  }
  if (expectedType === 'single' && !response.id) {
    throw new Error('智能体详情格式错误');
  }
}

// 创建智能体
export const createAgent = async (agentData) => {
  try {
    const response = await request(`${AGENT_API_BASE}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(agentData)
    });
    checkResponseType(response, 'single');
    return response;
  } catch (error) {
    console.error('创建智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 获取智能体详情
export const getAgent = async (agentId) => {
  try {
    const response = await request(`${AGENT_API_BASE}/${agentId}`);
    checkResponseType(response, 'single');
    return response;
  } catch (error) {
    console.error('获取智能体详情失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 获取用户智能体列表
export const getAgents = async (page = 1, limit = 10, categoryId = null) => {
  try {
    const skip = (page - 1) * limit;
    let url = `${AGENT_API_BASE}/?skip=${skip}&limit=${limit}`;
    if (categoryId) {
      url += `&category_id=${categoryId}`;
    }
    const response = await request(url);
    checkResponseType(response, 'list');
    return response;
  } catch (error) {
    console.error('获取智能体列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 获取公开智能体列表
export const getPublicAgents = async (page = 1, limit = 10) => {
  try {
    const skip = (page - 1) * limit;
    const response = await request(`${AGENT_API_BASE}/public/list?skip=${skip}&limit=${limit}`);
    checkResponseType(response, 'list');
    return response;
  } catch (error) {
    console.error('获取公开智能体列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 获取推荐智能体列表
export const getRecommendedAgents = async (page = 1, limit = 10) => {
  try {
    const skip = (page - 1) * limit;
    const response = await request(`${AGENT_API_BASE}/recommended/list?skip=${skip}&limit=${limit}`);
    checkResponseType(response, 'list');
    return response;
  } catch (error) {
    console.error('获取推荐智能体列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 更新智能体
export const updateAgent = async (agentId, agentData) => {
  try {
    const response = await request(`${AGENT_API_BASE}/${agentId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(agentData)
    });
    checkResponseType(response, 'single');
    return response;
  } catch (error) {
    console.error('更新智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 删除智能体
export const deleteAgent = async (agentId) => {
  try {
    await request(`${AGENT_API_BASE}/${agentId}`, {
      method: 'DELETE'
    });
    return true;
  } catch (error) {
    console.error('删除智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 搜索智能体
export const searchAgents = async (keyword, page = 1, limit = 10, categoryId = null) => {
  try {
    const skip = (page - 1) * limit;
    let url = `${AGENT_API_BASE}/search?keyword=${encodeURIComponent(keyword)}&skip=${skip}&limit=${limit}`;
    if (categoryId) {
      url += `&category_id=${categoryId}`;
    }
    const response = await request(url);
    checkResponseType(response, 'list');
    return response;
  } catch (error) {
    console.error('搜索智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 测试智能体
export const testAgent = async (agentId, testMessage = '你好，请介绍一下你自己') => {
  try {
    const response = await request(`${AGENT_API_BASE}/${agentId}/test?test_message=${encodeURIComponent(testMessage)}`, {
      method: 'POST'
    });
    return response;
  } catch (error) {
    console.error('测试智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 复制智能体
export const copyAgent = async (agentId, newName = null) => {
  try {
    let url = `${AGENT_API_BASE}/${agentId}/copy`;
    if (newName) {
      url += `?new_name=${encodeURIComponent(newName)}`;
    }
    const response = await request(url, {
      method: 'POST'
    });
    return response;
  } catch (error) {
    console.error('复制智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 恢复智能体
export const restoreAgent = async (agentId) => {
  try {
    const response = await request(`${AGENT_API_BASE}/${agentId}/restore`, {
      method: 'POST'
    });
    return response;
  } catch (error) {
    console.error('恢复智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 获取已删除智能体列表
export const getDeletedAgents = async (page = 1, limit = 10) => {
  try {
    const skip = (page - 1) * limit;
    const response = await request(`${AGENT_API_BASE}/deleted/list?skip=${skip}&limit=${limit}`);
    checkResponseType(response, 'list');
    return response;
  } catch (error) {
    console.error('获取已删除智能体列表失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 导出智能体
export const exportAgent = async (agentId) => {
  try {
    const response = await request(`${AGENT_API_BASE}/${agentId}/export`, {
      method: 'GET'
    });
    return response;
  } catch (error) {
    console.error('导出智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};

// 导入智能体
export const importAgent = async (importData) => {
  try {
    const response = await request(`${AGENT_API_BASE}/import`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(importData)
    });
    return response;
  } catch (error) {
    console.error('导入智能体失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
    throw error;
  }
};
