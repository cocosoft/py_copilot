/**
 * 实体维护API服务
 */

import axios from 'axios';

// 在开发环境中，Vite代理会将 /api 请求转发到后端服务器
// 在生产环境中，使用完整的API地址
const isDev = import.meta.env.DEV;
const API_BASE_URL = isDev ? '/api/v1' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8007/api/v1');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 获取文档实体列表
 */
export const getDocumentEntities = async (documentId, params = {}) => {
  const { page = 1, pageSize = 50, entityType } = params;
  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (entityType) queryParams.append('entity_type', entityType);

  const response = await api.get(`/entity-maintenance/document-entities/${documentId}?${queryParams}`);
  return response.data;
};

/**
 * 获取KB实体列表
 */
export const getKBEntities = async (knowledgeBaseId, params = {}) => {
  const { page = 1, pageSize = 50, entityType } = params;
  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (entityType) queryParams.append('entity_type', entityType);

  const response = await api.get(`/entity-maintenance/kb-entities/${knowledgeBaseId}?${queryParams}`);
  return response.data;
};

/**
 * 获取全局实体列表
 */
export const getGlobalEntities = async (params = {}) => {
  const { page = 1, pageSize = 50, entityType } = params;
  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (entityType) queryParams.append('entity_type', entityType);

  const response = await api.get(`/entity-maintenance/global-entities?${queryParams}`);
  return response.data;
};

/**
 * 获取实体详情
 */
export const getEntityDetail = async (level, entityId) => {
  const response = await api.get(`/entity-maintenance/entity-detail/${level}/${entityId}`);
  return response.data;
};

/**
 * 更新文档实体
 */
export const updateDocumentEntity = async (entityId, data) => {
  const response = await api.put(`/entity-maintenance/document-entity/${entityId}`, data);
  return response.data;
};

/**
 * 更新KB实体
 */
export const updateKBEntity = async (entityId, data) => {
  const response = await api.put(`/entity-maintenance/kb-entity/${entityId}`, data);
  return response.data;
};

/**
 * 删除文档实体
 */
export const deleteDocumentEntity = async (entityId) => {
  const response = await api.delete(`/entity-maintenance/document-entity/${entityId}`);
  return response.data;
};

/**
 * 批量删除实体
 */
export const batchDeleteEntities = async (entityIds, level) => {
  const response = await api.post(`/entity-maintenance/batch-delete?level=${level}`, entityIds);
  return response.data;
};

/**
 * 添加文档实体
 */
export const addDocumentEntity = async (data) => {
  const response = await api.post('/entity-maintenance/add-document-entity', data);
  return response.data;
};

/**
 * 合并实体
 */
export const mergeEntities = async (data) => {
  const response = await api.post('/entity-maintenance/merge-document-entities', data);
  return response.data;
};

/**
 * 提交实体反馈
 */
export const submitEntityFeedback = async (data) => {
  const response = await api.post('/entity-maintenance/feedback', data);
  return response.data;
};

/**
 * 获取实体统计
 */
export const getEntityStatistics = async (knowledgeBaseId) => {
  const response = await api.get(`/entity-maintenance/statistics/${knowledgeBaseId}`);
  return response.data;
};

// 实体类型选项
export const ENTITY_TYPES = [
  { value: '', label: '全部类型' },
  { value: 'PERSON', label: '人物' },
  { value: 'ORG', label: '组织' },
  { value: 'GPE', label: '地点' },
  { value: 'LOC', label: '位置' },
  { value: 'FAC', label: '设施' },
  { value: 'PRODUCT', label: '产品' },
  { value: 'EVENT', label: '事件' },
  { value: 'DATE', label: '日期' },
  { value: 'TIME', label: '时间' },
  { value: 'MONEY', label: '货币' },
  { value: 'PERCENT', label: '百分比' },
  { value: 'CARDINAL', label: '基数' },
  { value: 'ORDINAL', label: '序数' },
  { value: 'QUANTITY', label: '数量' },
  { value: 'NORP', label: '民族/宗教/政治' },
  { value: 'LANGUAGE', label: '语言' },
  { value: 'WORK_OF_ART', label: '艺术作品' },
];

export default {
  getDocumentEntities,
  getKBEntities,
  getGlobalEntities,
  getEntityDetail,
  updateDocumentEntity,
  updateKBEntity,
  deleteDocumentEntity,
  batchDeleteEntities,
  addDocumentEntity,
  mergeEntities,
  submitEntityFeedback,
  getEntityStatistics,
  ENTITY_TYPES,
};
