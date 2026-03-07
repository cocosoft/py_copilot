/**
 * 知识图谱API服务
 * 
 * 提供知识图谱相关的API调用，包括关系类型管理、批量构建、实体管理、图谱分析等功能
 */

import { request } from '../apiUtils';

// ==================== 关系类型管理 ====================

/**
 * 获取所有关系类型
 * @returns {Promise<Array>} 关系类型列表
 */
export const getRelationTypes = async () => {
  try {
    return request('/v1/knowledge-graph/relation-types', { method: 'GET' });
  } catch (error) {
    console.error('获取关系类型失败:', error);
    throw error;
  }
};

/**
 * 添加关系类型
 * @param {Object} data 关系类型数据
 * @returns {Promise<Object>} 创建的关系类型
 */
export const addRelationType = async (data) => {
  try {
    return request('/v1/knowledge-graph/relation-types', { method: 'POST', data });
  } catch (error) {
    console.error('添加关系类型失败:', error);
    throw error;
  }
};

/**
 * 更新关系类型
 * @param {string} id 关系类型ID
 * @param {Object} data 更新的数据
 * @returns {Promise<Object>} 更新后的关系类型
 */
export const updateRelationType = async (id, data) => {
  try {
    return request(`/v1/knowledge-graph/relation-types/${id}`, { method: 'PUT', data });
  } catch (error) {
    console.error('更新关系类型失败:', error);
    throw error;
  }
};

/**
 * 删除关系类型
 * @param {string} id 关系类型ID
 * @returns {Promise<Object>} 删除结果
 */
export const deleteRelationType = async (id) => {
  try {
    return request(`/v1/knowledge-graph/relation-types/${id}`, { method: 'DELETE' });
  } catch (error) {
    console.error('删除关系类型失败:', error);
    throw error;
  }
};

// ==================== 批量构建 ====================

/**
 * 批量构建知识图谱
 * @param {Array<number>} documentIds 文档ID列表
 * @param {Object} options 构建选项
 * @returns {Promise<Object>} 批量构建任务信息
 */
export const batchBuildKnowledgeGraph = async (documentIds, options = {}) => {
  try {
    return request('/v1/knowledge-graph/batch/build-graphs', {
      method: 'POST',
      data: { document_ids: documentIds, ...options }
    });
  } catch (error) {
    console.error('批量构建失败:', error);
    throw error;
  }
};

/**
 * 获取批量构建任务状态
 * @param {string} batchId 批量任务ID
 * @returns {Promise<Object>} 任务状态
 */
export const getBatchBuildStatus = async (batchId) => {
  try {
    return request(`/v1/knowledge-graph/batch/status/${batchId}`);
  } catch (error) {
    console.error('获取批量构建状态失败:', error);
    throw error;
  }
};

/**
 * 取消批量构建任务
 * @param {string} batchId 批量任务ID
 * @returns {Promise<Object>} 取消结果
 */
export const cancelBatchBuild = async (batchId) => {
  try {
    return request(`/v1/knowledge-graph/batch/cancel/${batchId}`, { method: 'POST' });
  } catch (error) {
    console.error('取消批量构建失败:', error);
    throw error;
  }
};

// ==================== 实体管理 ====================

/**
 * 获取实体列表
 * @param {number} knowledgeBaseId 知识库ID
 * @param {Object} params 查询参数
 * @returns {Promise<Object>} 实体列表
 */
export const getEntities = async (knowledgeBaseId, params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (knowledgeBaseId) queryParams.append('kb_id', knowledgeBaseId);
    if (params.keyword) queryParams.append('keyword', params.keyword);
    if (params.type) queryParams.append('type', params.type);
    
    return request(`/v1/knowledge-graph/search-entities?${queryParams.toString()}`, {
      method: 'GET'
    });
  } catch (error) {
    console.error('获取实体列表失败:', error);
    throw error;
  }
};

/**
 * 合并实体
 * @param {Array<string>} sourceIds 源实体ID列表
 * @param {string} targetId 目标实体ID
 * @returns {Promise<Object>} 合并结果
 */
export const mergeEntities = async (sourceIds, targetId) => {
  try {
    return request('/v1/knowledge-graph/entities/merge', {
      method: 'POST',
      data: { source_ids: sourceIds, target_id: targetId }
    });
  } catch (error) {
    console.error('合并实体失败:', error);
    throw error;
  }
};

/**
 * 获取相似实体
 * @param {string} entityId 实体ID
 * @param {number} threshold 相似度阈值（0-1）
 * @returns {Promise<Array>} 相似实体列表
 */
export const getSimilarEntities = async (entityId, threshold = 0.8) => {
  try {
    return request(`/v1/knowledge-graph/entities/${entityId}/similar?threshold=${threshold}`);
  } catch (error) {
    console.error('获取相似实体失败:', error);
    throw error;
  }
};

/**
 * 实体消歧
 * @param {string} entityId 实体ID
 * @param {string} canonicalId 标准实体ID
 * @returns {Promise<Object>} 消歧结果
 */
export const disambiguateEntity = async (entityId, canonicalId) => {
  try {
    return request('/v1/knowledge-graph/entities/disambiguate', {
      method: 'POST',
      data: { entity_id: entityId, canonical_id: canonicalId }
    });
  } catch (error) {
    console.error('实体消歧失败:', error);
    throw error;
  }
};

/**
 * 获取关系列表
 * @param {number} knowledgeBaseId 知识库ID
 * @param {Object} params 查询参数
 * @returns {Promise<Object>} 关系列表
 */
export const getRelations = async (knowledgeBaseId, params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (knowledgeBaseId) queryParams.append('kb_id', knowledgeBaseId);
    if (params.filter) queryParams.append('filter', params.filter);
    if (params.keyword) queryParams.append('keyword', params.keyword);
    if (params.relationType) queryParams.append('relation_type', params.relationType);
    if (params.sourceEntityType) queryParams.append('source_entity_type', params.sourceEntityType);
    if (params.targetEntityType) queryParams.append('target_entity_type', params.targetEntityType);
    if (params.minConfidence) queryParams.append('min_confidence', params.minConfidence);
    if (params.maxConfidence) queryParams.append('max_confidence', params.maxConfidence);
    if (params.startDate) queryParams.append('start_date', params.startDate);
    if (params.endDate) queryParams.append('end_date', params.endDate);
    
    return request(`/v1/knowledge-graph/relationships?${queryParams.toString()}`, {
      method: 'GET'
    });
  } catch (error) {
    console.error('获取关系列表失败:', error);
    throw error;
  }
};

// ==================== 图谱分析 ====================

/**
 * 社区发现
 * @param {number} knowledgeBaseId 知识库ID
 * @returns {Promise<Object>} 社区分析结果
 */
export const detectCommunities = async (knowledgeBaseId) => {
  return await analyzeCommunities(knowledgeBaseId);
};

/**
 * 社区发现分析（别名）
 * @param {number} knowledgeBaseId 知识库ID
 * @returns {Promise<Object>} 社区分析结果
 */
export const analyzeCommunities = async (knowledgeBaseId) => {
  try {
    return request(`/v1/knowledge-graph/analysis/communities?kb_id=${knowledgeBaseId}`);
  } catch (error) {
    console.error('社区发现失败:', error);
    throw error;
  }
};

/**
 * 中心性分析
 * @param {number} knowledgeBaseId 知识库ID
 * @returns {Promise<Object>} 中心性分析结果
 */
export const calculateCentrality = async (knowledgeBaseId) => {
  return await analyzeCentrality(knowledgeBaseId);
};

/**
 * 中心性分析（别名）
 * @param {number} knowledgeBaseId 知识库ID
 * @returns {Promise<Object>} 中心性分析结果
 */
export const analyzeCentrality = async (knowledgeBaseId) => {
  try {
    return request(`/v1/knowledge-graph/analysis/centrality?kb_id=${knowledgeBaseId}`);
  } catch (error) {
    console.error('中心性分析失败:', error);
    throw error;
  }
};

/**
 * 路径发现
 * @param {number} knowledgeBaseId 知识库ID
 * @param {string} sourceId 源实体ID
 * @param {string} targetId 目标实体ID
 * @returns {Promise<Object>} 路径分析结果
 */
export const findPath = async (knowledgeBaseId, sourceId, targetId) => {
  // 别名导出，用于兼容不同命名
  return await findPathInternal(knowledgeBaseId, sourceId, targetId);
};

/**
 * 路径发现（内部实现）
 * @param {number} knowledgeBaseId 知识库ID
 * @param {string} sourceId 源实体ID
 * @param {string} targetId 目标实体ID
 * @returns {Promise<Object>} 路径分析结果
 */
const findPathInternal = async (knowledgeBaseId, sourceId, targetId) => {
  try {
    return request(`/v1/knowledge-graph/analysis/path?source=${sourceId}&target=${targetId}`);
  } catch (error) {
    console.error('路径发现失败:', error);
    throw error;
  }
};

// ==================== 知识库图谱统计 ====================

/**
 * 获取知识库图谱统计信息
 * @param {number} knowledgeBaseId 知识库ID
 * @returns {Promise<Object>} 统计信息
 */
export const getKnowledgeBaseGraphStats = async (knowledgeBaseId) => {
  try {
    return request(`/v1/knowledge-graph/statistics?knowledge_base_id=${knowledgeBaseId}`, {
      method: 'GET'
    });
  } catch (error) {
    console.error('获取图谱统计失败:', error);
    throw error;
  }
};

/**
 * 获取实体类型分布
 * @param {number} knowledgeBaseId 知识库ID
 * @returns {Promise<Object>} 实体类型分布
 */
export const getEntityTypeDistribution = async (knowledgeBaseId) => {
  try {
    const response = await request(`/v1/knowledge-graph/statistics?knowledge_base_id=${knowledgeBaseId}`, {
      method: 'GET'
    });
    
    // 后端直接返回数据对象，格式为 { total_entities, total_relationships, entity_types, relationship_types }
    if (response && response.entity_types) {
      // 计算总数用于计算百分比
      const totalEntities = response.total_entities || 0;
      
      // 转换为前端期望的格式
      const distribution = Object.entries(response.entity_types).map(([type, count]) => {
        return {
          type,
          count,
          percentage: totalEntities > 0 ? Math.round((count / totalEntities) * 100) : 0
        };
      });
      
      return {
        success: true,
        data: { distribution }
      };
    }
    
    // 如果没有数据，返回空分布
    return {
      success: true,
      data: { distribution: [] }
    };
  } catch (error) {
    console.error('获取实体类型分布失败:', error);
    throw error;
  }
};

/**
 * 获取关系类型分布
 * @param {number} knowledgeBaseId 知识库ID
 * @returns {Promise<Object>} 关系类型分布
 */
export const getRelationTypeDistribution = async (knowledgeBaseId) => {
  try {
    const response = await request(`/v1/knowledge-graph/statistics?knowledge_base_id=${knowledgeBaseId}`, {
      method: 'GET'
    });
    
    // 后端直接返回数据对象，格式为 { total_entities, total_relationships, entity_types, relationship_types }
    if (response && response.relationship_types) {
      // 计算总数用于计算百分比
      const totalRelationships = response.total_relationships || 0;
      
      // 转换为前端期望的格式
      const distribution = Object.entries(response.relationship_types).map(([type, count]) => {
        return {
          type,
          count,
          percentage: totalRelationships > 0 ? Math.round((count / totalRelationships) * 100) : 0
        };
      });
      
      return {
        success: true,
        data: { distribution }
      };
    }
    
    // 如果没有数据，返回空分布
    return {
      success: true,
      data: { distribution: [] }
    };
  } catch (error) {
    console.error('获取关系类型分布失败:', error);
    throw error;
  }
};
