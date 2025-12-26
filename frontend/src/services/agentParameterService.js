import { API_BASE_URL, request } from '../utils/apiUtils';

const AGENT_PARAMETER_API_BASE = '/v1/agents';

export const agentParameterApi = {
  getParameters: async (agentId, skip = 0, limit = 100, parameterGroup = null) => {
    try {
      let url = `${AGENT_PARAMETER_API_BASE}/${agentId}/parameters?skip=${skip}&limit=${limit}`;
      if (parameterGroup) {
        url += `&parameter_group=${encodeURIComponent(parameterGroup)}`;
      }
      const response = await request(url);
      return response;
    } catch (error) {
      console.error('获取智能体参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  getEffectiveParameters: async (agentId) => {
    try {
      const response = await request(`${AGENT_PARAMETER_API_BASE}/${agentId}/parameters/effective`);
      return response;
    } catch (error) {
      console.error('获取智能体有效参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  getParametersWithSource: async (agentId) => {
    try {
      const response = await request(`${AGENT_PARAMETER_API_BASE}/${agentId}/parameters/effective-with-source`);
      return response;
    } catch (error) {
      console.error('获取智能体参数（含来源）失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  getParameter: async (agentId, parameterName) => {
    try {
      const response = await request(`${AGENT_PARAMETER_API_BASE}/${agentId}/parameters/${encodeURIComponent(parameterName)}`);
      return response;
    } catch (error) {
      console.error('获取智能体参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  createParameter: async (agentId, parameterData) => {
    try {
      const response = await request(`${AGENT_PARAMETER_API_BASE}/${agentId}/parameters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(parameterData)
      });
      return response;
    } catch (error) {
      console.error('创建智能体参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  createParametersBulk: async (agentId, parameters, parameterGroup = null) => {
    try {
      const requestBody = { parameters };
      if (parameterGroup) {
        requestBody.parameter_group = parameterGroup;
      }
      const response = await request(`${AGENT_PARAMETER_API_BASE}/${agentId}/parameters/bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      return response;
    } catch (error) {
      console.error('批量创建智能体参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  updateParameter: async (agentId, parameterName, parameterData) => {
    try {
      const response = await request(`${AGENT_PARAMETER_API_BASE}/${agentId}/parameters/${encodeURIComponent(parameterName)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(parameterData)
      });
      return response;
    } catch (error) {
      console.error('更新智能体参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  deleteParameter: async (agentId, parameterName) => {
    try {
      await request(`${AGENT_PARAMETER_API_BASE}/${agentId}/parameters/${encodeURIComponent(parameterName)}`, {
        method: 'DELETE'
      });
      return true;
    } catch (error) {
      console.error('删除智能体参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  deleteAllParameters: async (agentId) => {
    try {
      const response = await request(`${AGENT_PARAMETER_API_BASE}/${agentId}/parameters`, {
        method: 'DELETE'
      });
      return response;
    } catch (error) {
      console.error('删除所有智能体参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  },

  validateParameters: async (agentId, parameters = null) => {
    try {
      const url = parameters 
        ? `${AGENT_PARAMETER_API_BASE}/${agentId}/parameters/validate`
        : `${AGENT_PARAMETER_API_BASE}/${agentId}/parameters/validate`;
      
      const response = await request(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: parameters ? JSON.stringify(parameters) : JSON.stringify({})
      });
      return response;
    } catch (error) {
      console.error('校验智能体参数失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      throw error;
    }
  }
};
