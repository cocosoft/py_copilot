import { request, requestWithRetry } from '../apiUtils';

// Knowledge Base API
export const createKnowledgeBase = async (name, description) => {
    const response = await request('/v1/knowledge/knowledge-bases', {
        method: 'POST',
        data: { name, description }
    });
    return response;
};

export const getKnowledgeBases = async (skip = 0, limit = 10) => {
    const response = await request('/v1/knowledge/knowledge-bases', {
        method: 'GET',
        params: { skip, limit }
    });
    return response;
};

export const getKnowledgeBase = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}`, {
        method: 'GET'
    });
    return response;
};

export const updateKnowledgeBase = async (knowledgeBaseId, name, description) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}`, {
        method: 'PUT',
        data: { name, description }
    });
    return response;
};

export const deleteKnowledgeBase = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}`, {
        method: 'DELETE'
    });
    return response;
};

// Knowledge Document API

/**
 * 上传文档到知识库
 *
 * @param {File} file - 文件对象
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 上传结果
 */
export const uploadDocument = async (file, knowledgeBaseId) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await request('/v1/knowledge/documents', {
        method: 'POST',
        params: { knowledge_base_id: knowledgeBaseId },
        body: formData,
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        // 设置较长的超时时间（5分钟），因为后端需要处理文档解析、分块、向量化和图谱化
        timeout: 300000
    });

    return response;
};

export const searchDocuments = async (query, limit = 10, knowledgeBaseId = null, sortBy = 'relevance', sortOrder = 'desc', fileTypes = [], startDate = null, endDate = null) => {
    const response = await request('/v1/knowledge/search', {
        method: 'GET',
        params: {
            query,
            limit,
            knowledge_base_id: knowledgeBaseId,
            sort_by: sortBy,
            sort_order: sortOrder,
            file_types: fileTypes.join(','),
            start_date: startDate,
            end_date: endDate
        }
    });
    
    return response.results;
};

export const listDocuments = async (skip = 0, limit = 10, knowledgeBaseId = null, isVectorized = null, processingStatus = null, metadataFilter = null) => {
    const params = { skip, limit, knowledge_base_id: knowledgeBaseId };
    // 使用 processing_status 单字段进行筛选，isVectorized 参数已废弃
    if (processingStatus !== null) {
        params.processing_status = processingStatus;
    }
    // 支持细粒度的元数据筛选
    if (metadataFilter !== null) {
        Object.keys(metadataFilter).forEach(key => {
            if (metadataFilter[key] !== null) {
                params[`metadata_${key}`] = metadataFilter[key];
            }
        });
    }
    const response = await request('/v1/knowledge/documents', {
        method: 'GET',
        params
    });
    
    return response;
};

export const loadDocumentsAsync = async (knowledgeBaseId, skip = 0, limit = 20, options = {}) => {
    const response = await request('/v1/knowledge/documents/async', {
        method: 'POST',
        data: {
            knowledge_base_id: knowledgeBaseId,
            skip,
            limit,
            ...options
        }
    });
    return response;
};

export const getDocumentLoadStatus = async (taskId) => {
    const response = await request(`/v1/knowledge/documents/async/status/${taskId}`, {
        method: 'GET'
    });
    return response;
};

export const getDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'GET'
    });
    return response;
};

/**
 * 更新文档
 *
 * @param {number} documentId - 文档ID
 * @param {Object} data - 更新数据
 * @returns {Promise<Object>} 更新后的文档
 */
export const updateDocument = async (documentId, data) => {
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'PUT',
        data
    });
    return response;
};

export const deleteDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'DELETE'
    });
    return response;
};

export const downloadDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/download`, {
        method: 'GET',
        responseType: 'blob'
    });
    return response;
};

export const previewDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/preview`, {
        method: 'GET'
    });
    return response;
};

// Document Processing API
export const processDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/process`, {
        method: 'POST'
    });
    return response;
};

export const batchProcessDocuments = async (documentIds) => {
    const response = await request('/v1/knowledge/documents/batch-process', {
        method: 'POST',
        data: { document_ids: documentIds }
    });
    return response;
};

export const getUnprocessedDocuments = async (knowledgeBaseId) => {
    const response = await request('/v1/knowledge/documents/unprocessed', {
        method: 'GET',
        params: { knowledge_base_id: knowledgeBaseId }
    });
    return response;
};

export const getProcessingStatus = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/status`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取知识库处理状态
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 知识库处理状态信息
 */
export const getKnowledgeBaseProcessingStatus = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/processing-status`, {
        method: 'GET',
        timeout: 60000 // 60秒超时，足够处理复杂的状态计算
    });
    return response;
};

export const getDocumentProcessingProgress = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/progress`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取处理队列状态
 *
 * @returns {Promise<Object>} 队列状态信息
 */
export const getProcessingQueueStatus = async () => {
    const response = await request('/v1/knowledge/processing-queue/status', {
        method: 'GET'
    });
    return response;
};

// Document Chunks API
export const getDocumentChunks = async (documentId, skip = 0, limit = 50, options = {}) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/chunks`, {
        method: 'GET',
        params: { skip, limit },
        ...options
    });
    return response;
};

export const getChunkDetail = async (chunkId) => {
    const response = await request(`/v1/knowledge/chunks/${chunkId}`, {
        method: 'GET'
    });
    return response;
};

// Document Tags API
export const getDocumentTags = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags`, {
        method: 'GET'
    });
    return response;
};

export const addDocumentTags = async (documentId, tagNames) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags`, {
        method: 'POST',
        data: { tag_names: tagNames }
    });
    return response;
};

export const removeDocumentTag = async (documentId, tagId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags/${tagId}`, {
        method: 'DELETE'
    });
    return response;
};

/**
 * 添加文档标签（单数形式，兼容旧代码）
 *
 * @param {number} documentId - 文档ID
 * @param {string} tagName - 标签名称
 * @returns {Promise<Object>} 添加结果
 */
export const addDocumentTag = async (documentId, tagName) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags`, {
        method: 'POST',
        data: { name: tagName }
    });
    return response;
};

// Knowledge Tags API
export const listKnowledgeTags = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/tags`, {
        method: 'GET'
    });
    return response;
};

export const createKnowledgeTag = async (knowledgeBaseId, name, color = null) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/tags`, {
        method: 'POST',
        data: { name, color }
    });
    return response;
};

export const updateKnowledgeTag = async (knowledgeBaseId, tagId, name, color) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/tags/${tagId}`, {
        method: 'PUT',
        data: { name, color }
    });
    return response;
};

export const deleteKnowledgeTag = async (knowledgeBaseId, tagId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/tags/${tagId}`, {
        method: 'DELETE'
    });
    return response;
};

/**
 * 获取所有标签
 *
 * @returns {Promise<Object>} 所有标签列表
 */
export const getAllTags = async () => {
    const response = await request('/v1/knowledge/tags', {
        method: 'GET'
    });
    return response;
};

/**
 * 根据标签搜索文档
 *
 * @param {string} tagName - 标签名称
 * @param {Object} options - 搜索选项
 * @returns {Promise<Object>} 搜索结果
 */
export const searchDocumentsByTag = async (tagName, options = {}) => {
    const response = await request('/v1/knowledge/documents/search-by-tag', {
        method: 'GET',
        params: { tag: tagName, ...options }
    });
    return response;
};

// Search API
export const searchKnowledgeBase = async (knowledgeBaseId, query, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/search`, {
        method: 'POST',
        data: { query, ...options }
    });
    return response;
};

export const semanticSearch = async (knowledgeBaseId, query, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/semantic-search`, {
        method: 'POST',
        data: { query, ...options }
    });
    return response;
};

export const hybridSearch = async (knowledgeBaseId, query, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/hybrid-search`, {
        method: 'POST',
        data: { query, ...options }
    });
    return response;
};

// Graph API
export const getKnowledgeGraph = async (knowledgeBaseId, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/graph`, {
        method: 'GET',
        params: options
    });
    return response;
};

export const getDocumentGraph = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/graph`, {
        method: 'GET'
    });
    return response;
};

export const getEntityGraph = async (entityId) => {
    const response = await request(`/v1/knowledge/entities/${entityId}/graph`, {
        method: 'GET'
    });
    return response;
};

// Entity API
export const getKnowledgeEntities = async (knowledgeBaseId, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/entities`, {
        method: 'GET',
        params: options
    });
    return response;
};

export const getEntityDetail = async (entityId) => {
    const response = await request(`/v1/knowledge/entities/${entityId}`, {
        method: 'GET'
    });
    return response;
};

export const updateEntity = async (entityId, data) => {
    const response = await request(`/v1/knowledge/entities/${entityId}`, {
        method: 'PUT',
        data
    });
    return response;
};

export const deleteEntity = async (entityId) => {
    const response = await request(`/v1/knowledge/entities/${entityId}`, {
        method: 'DELETE'
    });
    return response;
};

export const mergeEntities = async (sourceId, targetId) => {
    const response = await request('/v1/knowledge/entities/merge', {
        method: 'POST',
        data: { source_id: sourceId, target_id: targetId }
    });
    return response;
};

export const splitEntity = async (entityId, newEntities) => {
    const response = await request(`/v1/knowledge/entities/${entityId}/split`, {
        method: 'POST',
        data: { new_entities: newEntities }
    });
    return response;
};

/**
 * 提取实体
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {Object} options - 提取选项
 * @returns {Promise<Object>} 提取结果
 */
export const extractEntities = async (knowledgeBaseId, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/extract-entities`, {
        method: 'POST',
        data: options
    });
    return response;
};

// Relationship API
export const getEntityRelationships = async (entityId) => {
    const response = await request(`/v1/knowledge/entities/${entityId}/relationships`, {
        method: 'GET'
    });
    return response;
};

export const createRelationship = async (data) => {
    const response = await request('/v1/knowledge/relationships', {
        method: 'POST',
        data
    });
    return response;
};

export const updateRelationship = async (relationshipId, data) => {
    const response = await request(`/v1/knowledge/relationships/${relationshipId}`, {
        method: 'PUT',
        data
    });
    return response;
};

export const deleteRelationship = async (relationshipId) => {
    const response = await request(`/v1/knowledge/relationships/${relationshipId}`, {
        method: 'DELETE'
    });
    return response;
};

// Stats API
export const getKnowledgeBaseStats = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/stats`, {
        method: 'GET'
    });
    return response;
};

export const getDocumentStats = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/stats`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取实体统计信息
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 实体统计信息
 */
export const getEntityStats = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/entity-stats`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取知识库统计信息
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 知识库统计信息
 */
export const getKnowledgeStats = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/stats`, {
        method: 'GET'
    });
    return response;
};

// Vectorization API (已在上面的细粒度API中定义，这里保留向后兼容的别名)
export const vectorizeDocumentLegacy = async (documentId, config = {}) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/vectorize`, {
        method: 'POST',
        data: config
    });
    return response;
};

/**
 * 异步向量化文档
 *
 * @param {number} documentId - 文档ID
 * @param {Object} config - 向量化配置
 * @returns {Promise<Object>} 异步任务信息
 */
export const vectorizeDocumentAsync = async (documentId, config = {}) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/vectorize-async`, {
        method: 'POST',
        data: config
    });
    return response;
};

export const batchVectorizeDocuments = async (documentIds, config = {}) => {
    const response = await request('/v1/knowledge/documents/batch-vectorize', {
        method: 'POST',
        data: { document_ids: documentIds, ...config }
    });
    return response;
};

// Re-ranking API
export const rerankResults = async (query, results, options = {}) => {
    const response = await request('/v1/knowledge/rerank', {
        method: 'POST',
        data: { query, results, ...options }
    });
    return response;
};

// Permission API
export const getKnowledgeBasePermissions = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions`, {
        method: 'GET'
    });
    return response;
};

export const addKnowledgeBasePermission = async (knowledgeBaseId, userId, permission) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions`, {
        method: 'POST',
        data: { user_id: userId, permission }
    });
    return response;
};

export const updateKnowledgeBasePermission = async (knowledgeBaseId, permissionId, permission) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions/${permissionId}`, {
        method: 'PUT',
        data: { permission }
    });
    return response;
};

export const removeKnowledgeBasePermission = async (knowledgeBaseId, permissionId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions/${permissionId}`, {
        method: 'DELETE'
    });
    return response;
};

// Batch Operations API
export const batchDeleteDocuments = async (documentIds) => {
    const response = await request('/v1/knowledge/documents/batch-delete', {
        method: 'POST',
        data: { document_ids: documentIds }
    });
    return response;
};

/**
 * 批量下载文档
 *
 * @param {number[]} documentIds - 文档ID数组
 * @returns {Promise<Blob>} 下载的文件Blob
 */
export const batchDownloadDocuments = async (documentIds) => {
    const response = await request('/v1/knowledge/documents/batch-download', {
        method: 'POST',
        data: { document_ids: documentIds },
        responseType: 'blob'
    });
    return response;
};

export const batchTagDocuments = async (documentIds, tagNames) => {
    const response = await request('/v1/knowledge/documents/batch-tag', {
        method: 'POST',
        data: { document_ids: documentIds, tag_names: tagNames }
    });
    return response;
};

export const batchMoveDocuments = async (documentIds, targetKnowledgeBaseId) => {
    const response = await request('/v1/knowledge/documents/batch-move', {
        method: 'POST',
        data: { document_ids: documentIds, target_knowledge_base_id: targetKnowledgeBaseId }
    });
    return response;
};

/**
 * 批量更新文档实体状态
 *
 * @param {number[]} documentIds - 文档ID数组
 * @param {string} status - 实体状态
 * @returns {Promise<Object>} 更新结果
 */
export const batchUpdateEntityStatus = async (documentIds, status) => {
    const response = await request('/v1/knowledge/documents/batch-update-entity-status', {
        method: 'POST',
        data: { document_ids: documentIds, status }
    });
    return response;
};

/**
 * 构建知识图谱
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {Object} options - 构建选项
 * @returns {Promise<Object>} 构建结果
 */
export const buildKnowledgeGraph = async (knowledgeBaseId, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/build-graph`, {
        method: 'POST',
        data: options
    });
    return response;
};

/**
 * 获取知识库图谱数据
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {Object} options - 查询选项
 * @returns {Promise<Object>} 图谱数据
 */
export const getKnowledgeBaseGraphData = async (knowledgeBaseId, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/graph`, {
        method: 'GET',
        params: options
    });
    return response;
};

/**
 * 获取图谱统计信息
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 图谱统计信息
 */
export const getGraphStatistics = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/graph-statistics`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取文档图谱数据
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 文档图谱数据
 */
export const getDocumentGraphData = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/graph`, {
        method: 'GET'
    });
    return response;
};

/**
 * 分析知识图谱
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {Object} options - 分析选项
 * @returns {Promise<Object>} 分析结果
 */
export const analyzeKnowledgeGraph = async (knowledgeBaseId, options = {}) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/analyze-graph`, {
        method: 'POST',
        data: options
    });
    return response;
};

// Import/Export API
export const exportKnowledgeBase = async (knowledgeBaseId, format = 'json') => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/export`, {
        method: 'GET',
        params: { format },
        responseType: 'blob'
    });
    return response;
};

export const importKnowledgeBase = async (knowledgeBaseId, file, format = 'json') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);

    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/import`, {
        method: 'POST',
        body: formData,
        headers: {
            'Content-Type': 'multipart/form-data',
        }
    });
    return response;
};

// Maintenance API
export const optimizeKnowledgeBase = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/optimize`, {
        method: 'POST'
    });
    return response;
};

export const repairKnowledgeBase = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/repair`, {
        method: 'POST'
    });
    return response;
};

export const backupKnowledgeBase = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/backup`, {
        method: 'POST'
    });
    return response;
};

export const restoreKnowledgeBase = async (knowledgeBaseId, backupId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/restore`, {
        method: 'POST',
        data: { backup_id: backupId }
    });
    return response;
};

// Settings API
export const getKnowledgeBaseSettings = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/settings`, {
        method: 'GET'
    });
    return response;
};

export const updateKnowledgeBaseSettings = async (knowledgeBaseId, settings) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/settings`, {
        method: 'PUT',
        data: settings
    });
    return response;
};

// LLM Configuration API
export const getLLMConfig = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/llm-config`, {
        method: 'GET'
    });
    return response;
};

export const updateLLMConfig = async (knowledgeBaseId, config) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/llm-config`, {
        method: 'PUT',
        data: config
    });
    return response;
};

// Embedding Configuration API
export const getEmbeddingConfig = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/embedding-config`, {
        method: 'GET'
    });
    return response;
};

export const updateEmbeddingConfig = async (knowledgeBaseId, config) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/embedding-config`, {
        method: 'PUT',
        data: config
    });
    return response;
};

// Graph Configuration API
export const getGraphConfig = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/graph-config`, {
        method: 'GET'
    });
    return response;
};

export const updateGraphConfig = async (knowledgeBaseId, config) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/graph-config`, {
        method: 'PUT',
        data: config
    });
    return response;
};

// Processing Configuration API
export const getProcessingConfig = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/processing-config`, {
        method: 'GET'
    });
    return response;
};

export const updateProcessingConfig = async (knowledgeBaseId, config) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/processing-config`, {
        method: 'PUT',
        data: config
    });
    return response;
};

// Entity Extraction API
export const extractDocumentEntities = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-entities`, {
        method: 'POST'
    });
    return response;
};

export const batchExtractEntities = async (documentIds) => {
    const response = await request('/v1/knowledge/documents/batch-extract-entities', {
        method: 'POST',
        data: { document_ids: documentIds }
    });
    return response;
};

export const getDocumentEntities = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/entities`, {
        method: 'GET'
    });
    return response;
};

// Graph Construction API
export const constructDocumentGraph = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/construct-graph`, {
        method: 'POST'
    });
    return response;
};

export const batchConstructGraph = async (documentIds) => {
    const response = await request('/v1/knowledge/documents/batch-construct-graph', {
        method: 'POST',
        data: { document_ids: documentIds }
    });
    return response;
};

// Quality API
export const getDocumentQuality = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/quality`, {
        method: 'GET'
    });
    return response;
};

export const improveDocumentQuality = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/improve-quality`, {
        method: 'POST'
    });
    return response;
};

// Similarity API
export const getSimilarDocuments = async (documentId, limit = 10) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/similar`, {
        method: 'GET',
        params: { limit }
    });
    return response;
};

export const getDuplicateDocuments = async (knowledgeBaseId, threshold = 0.9) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/duplicates`, {
        method: 'GET',
        params: { threshold }
    });
    return response;
};

// Version API
export const getDocumentVersions = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/versions`, {
        method: 'GET'
    });
    return response;
};

export const createDocumentVersion = async (documentId, comment = '') => {
    const response = await request(`/v1/knowledge/documents/${documentId}/versions`, {
        method: 'POST',
        data: { comment }
    });
    return response;
};

export const restoreDocumentVersion = async (documentId, versionId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/versions/${versionId}/restore`, {
        method: 'POST'
    });
    return response;
};

export const compareDocumentVersions = async (documentId, versionId1, versionId2) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/versions/compare`, {
        method: 'GET',
        params: { version_id_1: versionId1, version_id_2: versionId2 }
    });
    return response;
};

// Collaboration API
export const getDocumentComments = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/comments`, {
        method: 'GET'
    });
    return response;
};

export const addDocumentComment = async (documentId, content, parentId = null) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/comments`, {
        method: 'POST',
        data: { content, parent_id: parentId }
    });
    return response;
};

export const updateDocumentComment = async (documentId, commentId, content) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/comments/${commentId}`, {
        method: 'PUT',
        data: { content }
    });
    return response;
};

export const deleteDocumentComment = async (documentId, commentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/comments/${commentId}`, {
        method: 'DELETE'
    });
    return response;
};

// Notification API
export const getNotifications = async (limit = 20, offset = 0) => {
    const response = await request('/v1/knowledge/notifications', {
        method: 'GET',
        params: { limit, offset }
    });
    return response;
};

export const markNotificationRead = async (notificationId) => {
    const response = await request(`/v1/knowledge/notifications/${notificationId}/read`, {
        method: 'POST'
    });
    return response;
};

export const markAllNotificationsRead = async () => {
    const response = await request('/v1/knowledge/notifications/read-all', {
        method: 'POST'
    });
    return response;
};

export const deleteNotification = async (notificationId) => {
    const response = await request(`/v1/knowledge/notifications/${notificationId}`, {
        method: 'DELETE'
    });
    return response;
};

// Activity API
export const getRecentActivities = async (limit = 20) => {
    const response = await request('/v1/knowledge/activities', {
        method: 'GET',
        params: { limit }
    });
    return response;
};

export const getKnowledgeBaseActivities = async (knowledgeBaseId, limit = 20) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/activities`, {
        method: 'GET',
        params: { limit }
    });
    return response;
};

// WebSocket API
export const subscribeToUpdates = (knowledgeBaseId, onMessage) => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/knowledge-bases/${knowledgeBaseId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
    };

    return ws;
};

// Chunk Entity Extraction API
export const extractChunkEntities = async (documentId, maxWorkers = 4) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-chunk-entities`, {
        method: 'POST',
        params: { max_workers: maxWorkers }
    });
    return response;
};

export const getExtractTaskStatus = async (documentId, taskId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-chunk-entities/status/${taskId}`, {
        method: 'GET'
    });
    return response;
};

export const listExtractTasks = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/extract-chunk-entities/tasks`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取片段的实体
 *
 * @param {number} chunkId - 片段ID
 * @returns {Promise<Object>} 实体列表
 */
export const getChunkEntities = async (chunkId) => {
  const response = await request(`/v1/knowledge/chunks/${chunkId}/entities`, {
    method: 'GET'
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
 * 获取文档的文档级实体
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 文档级实体列表
 */
export const getDocumentEntitiesNew = async (documentId) => {
  const response = await request(`/v1/knowledge/documents/${documentId}/entities`, {
    method: 'GET'
  });
  return response;
};

/**
 * 对齐知识库的文档级实体为KB级实体
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {boolean} useBert - 是否使用BERT语义对齐
 * @returns {Promise<Object>} 对齐结果
 */
export const alignKnowledgeBaseEntities = async (knowledgeBaseId, useBert = false) => {
  const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/align-entities`, {
    method: 'POST',
    params: { use_bert: useBert }
  });
  return response;
};

/**
 * 从维护表获取文档实体
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 实体列表
 */
export const getDocumentEntitiesFromMaintenance = async (documentId) => {
  const response = await request(`/v1/knowledge/documents/${documentId}/entities-from-maintenance`, {
    method: 'GET'
  });
  return response;
};

/**
 * 更新实体状态
 *
 * @param {number} entityId - 实体ID
 * @param {string} status - 实体状态
 * @returns {Promise<Object>} 更新结果
 */
export const updateEntityStatus = async (entityId, status) => {
  const response = await request(`/v1/knowledge/entities/${entityId}/status`, {
    method: 'PUT',
    data: { status }
  });
  return response;
};

/**
 * 获取文档切片实体
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 切片实体列表
 */
export const getDocumentChunkEntities = async (documentId) => {
  const response = await request(`/v1/knowledge/documents/${documentId}/chunk-entities`, {
    method: 'GET'
  });
  return response;
};

/**
 * 更新文档处理状态
 *
 * @param {number} documentId - 文档ID
 * @param {Object} status - 处理状态
 * @returns {Promise<Object>} 更新结果
 */
export const updateDocumentProcessingStatus = async (documentId, status) => {
  const response = await request(`/v1/knowledge/documents/${documentId}/processing-status`, {
    method: 'PUT',
    data: status
  });
  return response;
};

// ==================== 文档重新切片 API ====================

/**
 * 获取文档切片统计信息
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 切片统计信息
 */
export const getDocumentChunkStats = async (documentId) => {
  const response = await request(`/v1/knowledge/documents/${documentId}/chunk-stats`, {
    method: 'GET'
  });
  return response;
};

/**
 * 重新切片文档
 *
 * @param {number} documentId - 文档ID
 * @param {Object} config - 切片配置
 * @param {number} config.max_chunk_size - 最大切片大小（默认1500）
 * @param {number} config.min_chunk_size - 最小切片大小（默认300）
 * @param {number} config.overlap - 重叠大小（默认100）
 * @returns {Promise<Object>} 重新切片结果
 */
export const rechunkDocument = async (documentId, config = {}) => {
  const response = await request(`/v1/knowledge/documents/${documentId}/rechunk`, {
    method: 'POST',
    data: {
      max_chunk_size: config.maxChunkSize || 1500,
      min_chunk_size: config.minChunkSize || 300,
      overlap: config.overlap || 100
    }
  });
  return response;
};
