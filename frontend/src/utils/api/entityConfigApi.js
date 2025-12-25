import { request } from '../apiUtils';

/**
 * 实体配置管理API服务
 */

// 获取所有实体类型配置
export const getEntityTypes = async () => {
  return request('/v1/entity-config/entity-types', { method: 'GET' });
};

// 添加新的实体类型
export const addEntityType = async (entityType, config) => {
  return request(`/v1/entity-config/entity-types/${entityType}`, { 
    method: 'POST', 
    data: config 
  });
};

// 更新实体类型配置
export const updateEntityType = async (entityType, config) => {
  return request(`/v1/entity-config/entity-types/${entityType}`, { 
    method: 'PUT', 
    data: config 
  });
};

// 获取提取规则
export const getExtractionRules = async (entityType = null) => {
  const url = entityType 
    ? `/v1/entity-config/extraction-rules?entity_type=${entityType}`
    : '/v1/entity-config/extraction-rules';
  return request(url, { method: 'GET' });
};

// 添加提取规则
export const addExtractionRule = async (entityType, rule) => {
  return request(`/v1/entity-config/extraction-rules/${entityType}`, { 
    method: 'POST', 
    data: rule 
  });
};

// 获取指定实体类型的词典
export const getDictionary = async (entityType) => {
  return request(`/v1/entity-config/dictionaries/${entityType}`, { method: 'GET' });
};

// 向词典添加术语
export const addToDictionary = async (entityType, terms) => {
  return request(`/v1/entity-config/dictionaries/${entityType}`, { 
    method: 'POST', 
    data: { terms } 
  });
};

// 测试实体提取效果
export const testEntityExtraction = async (text) => {
  return request('/v1/entity-config/test-extraction', { 
    method: 'POST',
    params: { text }
  });
};

// 导出配置
export const exportConfig = async (exportPath) => {
  return request('/v1/entity-config/export-config', { 
    method: 'POST', 
    data: { export_path: exportPath } 
  });
};

// 导入配置
export const importConfig = async (importPath) => {
  return request('/v1/entity-config/import-config', { 
    method: 'POST', 
    data: { import_path: importPath } 
  });
};

// 重置为默认配置
export const resetConfig = async () => {
  return request('/v1/entity-config/reset-config', { method: 'POST' });
};