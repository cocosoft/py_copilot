/**
 * 文档处理相关 API
 * 
 * 提供文档处理流程的统一接口
 */

import { request } from '../apiUtils';

/**
 * 获取文档处理状态
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 文档处理状态信息
 */
export const getDocumentProcessingStatus = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/status`, {
        method: 'GET'
    });
    return response;
};

/**
 * 执行文档文本提取
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 文本提取结果
 */
export const extractDocumentText = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-text`, {
        method: 'POST'
    });
    return response;
};

/**
 * 执行文档切片处理
 *
 * @param {number} documentId - 文档ID
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {Object} options - 切片选项
 * @returns {Promise<Object>} 切片结果
 */
export const chunkDocument = async (documentId, knowledgeBaseId, options = {}) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/chunk`, {
        method: 'POST',
        data: {
            knowledge_base_id: knowledgeBaseId,
            max_chunk_size: options.maxChunkSize || 1000,
            min_chunk_size: options.minChunkSize || 200,
            overlap: options.overlap || 50
        }
    });
    return response;
};

/**
 * 执行文档向量化
 *
 * @param {number} documentId - 文档ID
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 向量化结果
 */
export const vectorizeDocument = async (documentId, knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/vectorize`, {
        method: 'POST',
        data: {
            knowledge_base_id: knowledgeBaseId
        }
    });
    return response;
};

/**
 * 执行文档知识图谱构建
 *
 * @param {number} documentId - 文档ID
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 图谱构建结果
 */
export const buildDocumentGraph = async (documentId, knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/build-graph`, {
        method: 'POST',
        data: {
            knowledge_base_id: knowledgeBaseId
        }
    });
    return response;
};

/**
 * 执行片段级实体识别
 *
 * @param {number} documentId - 文档ID
 * @param {number} [maxWorkers=4] - 并行工作线程数
 * @returns {Promise<Object>} 实体识别结果
 */
export const extractDocumentEntities = async (documentId, maxWorkers = 4) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-entities`, {
        method: 'POST',
        data: {
            max_workers: maxWorkers
        }
    });
    return response;
};

/**
 * 执行文档级实体聚合
 *
 * @param {number} documentId - 文档ID
 * @param {number} [similarityThreshold=0.85] - 相似度阈值
 * @returns {Promise<Object>} 实体聚合结果
 */
export const aggregateDocumentEntities = async (documentId, similarityThreshold = 0.85) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/aggregate-entities`, {
        method: 'POST',
        data: {
            similarity_threshold: similarityThreshold
        }
    });
    return response.data;
};

/**
 * 获取知识库处理状态摘要
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 处理状态摘要
 */
export const getKnowledgeBaseProcessingSummary = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/processing-summary`, {
        method: 'GET'
    });
    return response.data;
};

/**
 * 验证文档处理前置条件
 *
 * @param {number} documentId - 文档ID
 * @param {string} targetStage - 目标处理阶段
 * @returns {Promise<Object>} 验证结果
 */
export const validateDocumentPreconditions = async (documentId, targetStage) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/validate-preconditions`, {
        method: 'POST',
        data: {
            target_stage: targetStage
        }
    });
    return response.data;
};
