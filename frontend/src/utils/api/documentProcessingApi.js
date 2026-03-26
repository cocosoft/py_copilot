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
 * 执行文档处理（完整流程）
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 处理结果
 */
export const processDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/process`, {
        method: 'POST'
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
 * 执行片段级实体识别
 *
 * @param {number} documentId - 文档ID
 * @param {number} [maxWorkers=4] - 并行工作线程数
 * @returns {Promise<Object>} 实体识别结果
 */
export const extractDocumentEntities = async (documentId, maxWorkers = 4) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-chunk-entities`, {
        method: 'POST',
        data: {
            max_workers: maxWorkers
        }
    });
    return response;
};

/**
 * 获取实体识别任务状态
 *
 * @param {number} documentId - 文档ID
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 任务状态
 */
export const getEntityExtractionStatus = async (documentId, taskId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-chunk-entities/status/${taskId}`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取文档的所有实体识别任务
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 任务列表
 */
export const getEntityExtractionTasks = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-chunk-entities/tasks`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取文档分块统计信息
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 分块统计
 */
export const getDocumentChunkStats = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/chunk-stats`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取文档分块中的实体
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 分块实体列表
 */
export const getChunkEntities = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/chunk-entities`, {
        method: 'GET'
    });
    return response;
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
    return response;
};

/**
 * 获取处理队列状态
 *
 * @returns {Promise<Object>} 队列状态
 */
export const getProcessingQueueStatus = async () => {
    const response = await request('/v1/knowledge/processing-queue/status', {
        method: 'GET'
    });
    return response;
};

/**
 * 执行文档文本提取
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 提取结果
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
 * @param {number} options.maxChunkSize - 最大切片大小
 * @param {number} options.minChunkSize - 最小切片大小
 * @param {number} options.overlap - 切片重叠大小
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
 * 聚合文档的片段级实体为文档级实体
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 聚合结果
 */
export const aggregateDocumentEntities = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/aggregate-entities`, {
        method: 'POST'
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
        },
        timeout: 300000
    });
    return response;
};
