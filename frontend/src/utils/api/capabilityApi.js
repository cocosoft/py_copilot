// 模型能力相关API模块
import { request } from '../apiUtils';

// 本地能力数据处理函数
const getCapabilitiesStorageKey = () => {
  return `${STORAGE_PREFIX}capabilities`;
};

const getCapabilityAssociationsStorageKey = () => {
  return `${STORAGE_PREFIX}capability_associations`;
};

const handleLocalCapabilitiesGetAll = () => {
  try {
    const capabilities = localStorage.getItem(getCapabilitiesStorageKey());
    if (capabilities) {
      return JSON.parse(capabilities);
    }
    // 返回默认能力数据
    const defaultCapabilities = [
      {
        id: 1,
        name: 'multilingual',
        display_name: '多语言支持',
        description: '模型支持多种自然语言的处理能力',
        capability_type: 'language',
        unit: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        name: 'context_window',
        display_name: '上下文窗口',
        description: '模型能够处理的上下文长度',
        capability_type: 'processing',
        unit: 'tokens',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 3,
        name: 'response_format',
        display_name: '响应格式',
        description: '模型支持的输出格式',
        capability_type: 'output',
        unit: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 4,
        name: 'fine_tuning',
        display_name: '微调支持',
        description: '模型是否支持微调能力',
        capability_type: 'training',
        unit: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 5,
        name: 'code_generation',
        display_name: '代码生成',
        description: '模型生成代码的能力',
        capability_type: 'function',
        unit: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 6,
        name: 'image_generation',
        display_name: '图像生成',
        description: '模型生成图像的能力',
        capability_type: 'function',
        unit: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
    ];
    localStorage.setItem(getCapabilitiesStorageKey(), JSON.stringify(defaultCapabilities));
    return defaultCapabilities;
  } catch (error) {
    console.error('Error handling local capabilities:', error);
    return [];
  }
};

const handleLocalCapabilityCreate = (capabilityData) => {
  const capabilities = handleLocalCapabilitiesGetAll();
  const newCapability = {
    ...capabilityData,
    id: Date.now(), // 使用时间戳作为临时ID
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  capabilities.push(newCapability);
  localStorage.setItem(getCapabilitiesStorageKey(), JSON.stringify(capabilities));
  return newCapability;
};

const handleLocalCapabilityUpdate = (capabilityId, updatedData) => {
  const capabilities = handleLocalCapabilitiesGetAll();
  const index = capabilities.findIndex(c => c.id === capabilityId);
  if (index !== -1) {
    capabilities[index] = {
      ...capabilities[index],
      ...updatedData,
      updated_at: new Date().toISOString()
    };
    localStorage.setItem(getCapabilitiesStorageKey(), JSON.stringify(capabilities));
    return capabilities[index];
  }
  throw new Error('Capability not found');
};

const handleLocalCapabilityDelete = (capabilityId) => {
  const capabilities = handleLocalCapabilitiesGetAll();
  const filtered = capabilities.filter(c => c.id !== capabilityId);
  localStorage.setItem(getCapabilitiesStorageKey(), JSON.stringify(filtered));
  
  // 同时删除相关的关联关系
  const associations = handleLocalCapabilityAssociationsGet();
  const filteredAssociations = associations.filter(a => a.capability_id !== capabilityId);
  localStorage.setItem(getCapabilityAssociationsStorageKey(), JSON.stringify(filteredAssociations));
  
  return { success: true };
};

// 能力关联关系处理函数
const handleLocalCapabilityAssociationsGet = () => {
  try {
    const associations = localStorage.getItem(getCapabilityAssociationsStorageKey());
    return associations ? JSON.parse(associations) : [];
  } catch (error) {
    console.error('Error getting capability associations:', error);
    return [];
  }
};

const handleLocalCapabilityAssociationCreate = (modelId, capabilityId, value = null) => {
  const associations = handleLocalCapabilityAssociationsGet();
  const newAssociation = {
    id: Date.now(),
    model_id: modelId,
    capability_id: capabilityId,
    value: value,
    created_at: new Date().toISOString()
  };
  associations.push(newAssociation);
  localStorage.setItem(getCapabilityAssociationsStorageKey(), JSON.stringify(associations));
  return newAssociation;
};

const handleLocalCapabilityAssociationDelete = (modelId, capabilityId) => {
  const associations = handleLocalCapabilityAssociationsGet();
  const filtered = associations.filter(
    a => a.model_id !== modelId || a.capability_id !== capabilityId
  );
  localStorage.setItem(getCapabilityAssociationsStorageKey(), JSON.stringify(filtered));
  return { success: true };
};

const handleLocalCapabilityAssociationUpdate = (modelId, capabilityId, value) => {
  const associations = handleLocalCapabilityAssociationsGet();
  const index = associations.findIndex(
    a => a.model_id === modelId && a.capability_id === capabilityId
  );
  if (index !== -1) {
    associations[index] = {
      ...associations[index],
      value: value,
      updated_at: new Date().toISOString()
    };
    localStorage.setItem(getCapabilityAssociationsStorageKey(), JSON.stringify(associations));
    return associations[index];
  }
  throw new Error('Association not found');
};

// 获取模型的能力
const handleLocalModelCapabilitiesGet = (modelId) => {
  const associations = handleLocalCapabilityAssociationsGet();
  const capabilities = handleLocalCapabilitiesGetAll();
  
  const modelAssociations = associations.filter(a => a.model_id === modelId);
  const modelCapabilities = modelAssociations.map(association => {
    const capability = capabilities.find(c => c.id === association.capability_id);
    return {
      ...capability,
      value: association.value
    };
  });
  
  return modelCapabilities;
};

// 模型能力API实现
export const capabilityApi = {
  // 获取所有能力
  getAll: async () => {
    try {
      return await request('/model/capabilities', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取能力列表失败:', error);
      throw error;
    }
  },
  
  // 获取单个能力
  getById: async (capabilityId) => {
    try {
      return await request(`/model/capabilities/${capabilityId}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取能力 ${capabilityId} 失败:`, error);
      throw error;
    }
  },
  
  // 创建能力
  create: async (capabilityData) => {
    try {
      return await request('/model/capabilities', {
        method: 'POST',
        body: JSON.stringify(capabilityData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('创建能力失败:', error);
      throw error;
    }
  },
  
  // 更新能力
  update: async (capabilityId, updatedData) => {
    try {
      return await request(`/model/capabilities/${capabilityId}`, {
        method: 'PUT',
        body: JSON.stringify(updatedData),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`更新能力 ${capabilityId} 失败:`, error);
      throw error;
    }
  },
  
  // 删除能力
  delete: async (capabilityId) => {
    try {
      return await request(`/model/capabilities/${capabilityId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error(`删除能力 ${capabilityId} 失败:`, error);
      throw error;
    }
  },
  
  // 获取能力分类
  getTypes: async () => {
    try {
      return await request('/model/capabilities/types', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取能力分类失败:', error);
      throw error;
    }
  },
  
  // 添加模型能力关联
  addModelCapability: async (modelId, capabilityId, value = null) => {
    try {
      return await request('/model/capabilities/associations', {
        method: 'POST',
        body: JSON.stringify({ model_id: modelId, capability_id: capabilityId, value: value }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('添加模型能力关联失败:', error);
      throw error;
    }
  },
  
  // 添加能力到模型（别名，保持向后兼容）
  addCapabilityToModel: async (associationData) => {
    try {
      const { model_id, capability_id, config, value } = associationData;
      return await capabilityApi.addModelCapability(model_id, capability_id, value || config);
    } catch (error) {
      console.error('添加能力到模型失败:', error);
      throw error;
    }
  },
  
  // 移除模型能力关联
  removeModelCapability: async (modelId, capabilityId) => {
    try {
      return await request(`/model/capabilities/associations/model/${modelId}/capability/${capabilityId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('移除模型能力关联失败:', error);
      throw error;
    }
  },
  
  // 从模型移除能力（别名，保持向后兼容）
  removeCapabilityFromModel: async (modelId, capabilityId) => {
    return capabilityApi.removeModelCapability(modelId, capabilityId);
  },
  
  // 更新模型能力值
  updateModelCapabilityValue: async (modelId, capabilityId, value) => {
    try {
      return await request(`/model/capabilities/associations/model/${modelId}/capability/${capabilityId}`, {
        method: 'PUT',
        body: JSON.stringify({ value: value }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('更新模型能力值失败:', error);
      throw error;
    }
  },
  
  // 获取模型的所有能力
  getModelCapabilities: async (modelId) => {
    try {
      return await request(`/model/capabilities/model/${modelId}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取模型 ${modelId} 的能力失败:`, error);
      throw error;
    }
  },
  
  // 获取模型的所有能力（别名，保持向后兼容）
  getCapabilitiesByModel: async (modelId) => {
    return capabilityApi.getModelCapabilities(modelId);
  },
  
  // 获取具备特定能力的模型
  getModelsByCapability: async (capabilityId, minValue = null) => {
    try {
      const params = new URLSearchParams();
      if (minValue !== null) {
        params.append('min_value', minValue);
      }
      const queryString = params.toString() ? `?${params.toString()}` : '';
      
      return await request(`/model/capabilities/${capabilityId}/models${queryString}`, {
        method: 'GET'
      });
    } catch (error) {
      console.error(`获取具备能力 ${capabilityId} 的模型失败:`, error);
      throw error;
    }
  },
  
  // 批量更新模型能力
  batchUpdateModelCapabilities: async (modelId, capabilities) => {
    try {
      return await request(`/model/capabilities/model/${modelId}/batch`, {
        method: 'POST',
        body: JSON.stringify({ capabilities: capabilities }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error(`批量更新模型 ${modelId} 的能力失败:`, error);
      throw error;
    }
  }
};

export default capabilityApi;