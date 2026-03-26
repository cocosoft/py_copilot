/**
 * 层级API封装 - 用于处理不同层级的数据访问
 *
 * 支持四个层级：
 * - fragment: 片段级
 * - document: 文档级
 * - knowledge_base: 知识库级
 * - global: 全局级
 */

import { request } from '../apiUtils';

export const HIERARCHY_LEVELS = {
  FRAGMENT: 'fragment',
  DOCUMENT: 'document',
  KNOWLEDGE_BASE: 'knowledge_base',
  GLOBAL: 'global'
};

// 片段级API
export const getChunkEntities = async (knowledgeBaseId, options = {}) => {
  const {
    page = 1,
    pageSize = 20,
    sortBy = 'index',
    sortOrder = 'asc',
    ...otherOptions
  } = options;
  
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/chunks`, {
    method: 'GET',
    params: {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...otherOptions
    }
  });
};

export const getChunkGraph = async (knowledgeBaseId, chunkId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/chunks/${chunkId}/graph`, {
    method: 'GET'
  });
};

export const getFragmentLevelStats = async (knowledgeBaseId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/stats/fragment`, {
    method: 'GET'
  });
};

// 文档级API
export const getDocumentEntities = async (knowledgeBaseId, options = {}) => {
  const {
    page = 1,
    pageSize = 20,
    sortBy = 'name',
    sortOrder = 'asc',
    ...otherOptions
  } = options;
  
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents/entities`, {
    method: 'GET',
    params: {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...otherOptions
    }
  });
};

export const getDocumentGraph = async (knowledgeBaseId, documentId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/graph`, {
    method: 'GET'
  });
};

export const getDocumentLevelStats = async (knowledgeBaseId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/stats/document`, {
    method: 'GET'
  });
};

// 知识库级API
export const getKnowledgeBaseGraph = async (knowledgeBaseId, options = {}) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/graph`, {
    method: 'GET',
    params: options
  });
};

// 全局级API
export const getGlobalGraph = async (options = {}) => {
  return request(`/v1/knowledge/graph/global`, {
    method: 'GET',
    params: options
  });
};

// 知识库级统计API
export const getKnowledgeBaseLevelStats = async (knowledgeBaseId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/stats`, {
    method: 'GET'
  });
};

export const getGlobalLevelStats = async () => {
  return request(`/v1/knowledge/stats/global`, {
    method: 'GET'
  });
};

// 跨层级查询
export const getEntityHierarchy = async (entityId, level) => {
  return request(`/v1/knowledge/entities/${entityId}/hierarchy`, {
    method: 'GET',
    params: { level }
  });
};

// 层级导航API
export const getHierarchyLevels = async (knowledgeBaseId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/hierarchy/levels`, {
    method: 'GET'
  });
};

// 搜索API
export const searchEntitiesByLevel = async (level, query, options = {}) => {
  switch (level) {
    case HIERARCHY_LEVELS.FRAGMENT:
      return request(`/v1/knowledge/search/fragment`, {
        method: 'GET',
        params: { query, ...options }
      });
    case HIERARCHY_LEVELS.DOCUMENT:
      return request(`/v1/knowledge/search/document`, {
        method: 'GET',
        params: { query, ...options }
      });
    case HIERARCHY_LEVELS.KNOWLEDGE_BASE:
      return request(`/v1/knowledge/search/knowledge-base`, {
        method: 'GET',
        params: { query, ...options }
      });
    case HIERARCHY_LEVELS.GLOBAL:
      return request(`/v1/knowledge/search/global`, {
        method: 'GET',
        params: { query, ...options }
      });
    default:
      throw new Error(`Invalid hierarchy level: ${level}`);
  }
};