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

// ============================================================================
// 文档列表API
// ============================================================================

/**
 * 获取知识库的文档列表
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {Object} options - 查询选项
 * @param {number} options.page - 页码
 * @param {number} options.pageSize - 每页数量
 * @param {string} options.search - 搜索关键词
 * @returns {Promise<Object>} 文档列表
 */
export const getDocumentsList = async (knowledgeBaseId, options = {}) => {
  const {
    page = 1,
    pageSize = 20,
    search = '',
    ...otherOptions
  } = options;

  const params = {
    page,
    page_size: pageSize,
    ...otherOptions
  };

  if (search) {
    params.search = search;
  }

  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents`, {
    method: 'GET',
    params
  });
};

/**
 * 获取文档的片段列表
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} documentId - 文档ID
 * @param {Object} options - 查询选项
 * @param {number} options.page - 页码
 * @param {number} options.pageSize - 每页数量
 * @returns {Promise<Object>} 片段列表
 */
export const getDocumentChunksList = async (knowledgeBaseId, documentId, options = {}) => {
  const {
    page = 1,
    pageSize = 20,
    ...otherOptions
  } = options;

  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/chunks`, {
    method: 'GET',
    params: {
      page,
      page_size: pageSize,
      ...otherOptions
    }
  });
};

/**
 * 获取指定片段的实体列表
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} chunkId - 片段ID
 * @param {Object} options - 查询选项
 * @param {number} options.page - 页码
 * @param {number} options.pageSize - 每页数量
 * @returns {Promise<Object>} 实体列表
 */
export const getChunkEntitiesDetail = async (knowledgeBaseId, chunkId, options = {}) => {
  const {
    page = 1,
    pageSize = 50,
    ...otherOptions
  } = options;

  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/chunks/${chunkId}/entities`, {
    method: 'GET',
    params: {
      page,
      page_size: pageSize,
      ...otherOptions
    }
  });
};

/**
 * 获取指定文档的实体列表
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} documentId - 文档ID
 * @param {Object} options - 查询选项
 * @param {number} options.page - 页码
 * @param {number} options.pageSize - 每页数量
 * @param {string} options.entityType - 实体类型过滤
 * @returns {Promise<Object>} 实体列表
 */
export const getDocumentEntitiesDetail = async (knowledgeBaseId, documentId, options = {}) => {
  const {
    page = 1,
    pageSize = 50,
    entityType = '',
    ...otherOptions
  } = options;

  const params = {
    page,
    page_size: pageSize,
    ...otherOptions
  };

  if (entityType) {
    params.entity_type = entityType;
  }

  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/entities`, {
    method: 'GET',
    params
  });
};

/**
 * 获取文档关系列表
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} documentId - 文档ID
 * @param {Object} options - 查询选项
 * @returns {Promise} 关系列表
 */
export const getDocumentRelations = async (knowledgeBaseId, documentId, options = {}) => {
  const {
    page = 1,
    pageSize = 10,
    relationType = '',
    ...otherOptions
  } = options;

  const params = {
    page,
    page_size: pageSize,
    ...otherOptions
  };

  if (relationType) {
    params.relation_type = relationType;
  }

  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/relations`, {
    method: 'GET',
    params
  });
};

/**
 * 删除关系
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} relationId - 关系ID
 * @returns {Promise} 删除结果
 */
export const deleteRelation = async (knowledgeBaseId, relationId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/relations/${relationId}`, {
    method: 'DELETE'
  });
};

// ============================================================================
// 实体识别任务API
// ============================================================================

/**
 * 提取片段实体
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} chunkId - 片段ID
 * @returns {Promise<Object>} 提取结果
 */
export const extractChunkEntities = async (knowledgeBaseId, chunkId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/chunks/${chunkId}/extract-entities`, {
    method: 'POST'
  });
};

/**
 * 聚合文档实体
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 聚合结果
 */
export const aggregateDocumentEntities = async (knowledgeBaseId, documentId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/aggregate-entities`, {
    method: 'POST'
  });
};

/**
 * 获取文档识别状态
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 识别状态
 */
export const getDocumentExtractionStatus = async (knowledgeBaseId, documentId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/extraction-status`, {
    method: 'GET'
  });
};

/**
 * 获取实体识别任务列表
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {Object} options - 查询选项
 * @returns {Promise<Object>} 任务列表
 */
export const getExtractionTasks = async (knowledgeBaseId, options = {}) => {
  const {
    status = '',
    taskType = '',
    page = 1,
    pageSize = 20,
    ...otherOptions
  } = options;

  const params = {
    page,
    page_size: pageSize,
    ...otherOptions
  };

  if (status) {
    params.status = status;
  }

  if (taskType) {
    params.task_type = taskType;
  }

  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/extraction-tasks`, {
    method: 'GET',
    params
  });
};

/**
 * 重新识别所有片段
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 任务创建结果
 */
export const reExtractAllChunks = async (knowledgeBaseId, documentId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/re-extract-all`, {
    method: 'POST'
  });
};

// ============================================================================
// 任务管理API - 暂停/恢复/取消功能
// ============================================================================

/**
 * 暂停实体识别任务
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} taskId - 任务ID
 * @returns {Promise<Object>} 暂停结果
 */
export const pauseExtractionTask = async (knowledgeBaseId, taskId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/extraction-tasks/${taskId}/pause`, {
    method: 'POST'
  });
};

/**
 * 恢复实体识别任务
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} taskId - 任务ID
 * @returns {Promise<Object>} 恢复结果
 */
export const resumeExtractionTask = async (knowledgeBaseId, taskId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/extraction-tasks/${taskId}/resume`, {
    method: 'POST'
  });
};

/**
 * 取消实体识别任务
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {number} taskId - 任务ID
 * @returns {Promise<Object>} 取消结果
 */
export const cancelExtractionTask = async (knowledgeBaseId, taskId) => {
  return request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/extraction-tasks/${taskId}/cancel`, {
    method: 'POST'
  });
};
