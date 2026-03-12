import { request } from '../apiUtils';

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

export const listDocuments = async (skip = 0, limit = 10, knowledgeBaseId = null, isVectorized = null) => {
    const params = { skip, limit, knowledge_base_id: knowledgeBaseId };
    if (isVectorized !== null) {
        params.is_vectorized = isVectorized ? 1 : 0;
    }
    const response = await request('/v1/knowledge/documents', {
        method: 'GET',
        params
    });
    
    return response;
};

export const getDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'GET'
    });
    return response;
};

export const deleteDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'DELETE'
    });
    return response;
};

export const updateDocument = async (documentId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'PUT',
        body: formData,
        headers: {
            'Content-Type': 'multipart/form-data',
        },
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

export const getKnowledgeStats = async () => {
    const response = await request('/v1/knowledge/stats', {
        method: 'GET'
    });
    return response;
};

// Knowledge Base Permission API
export const getKnowledgeBasePermissions = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions`, {
        method: 'GET'
    });
    return response;
};

export const updateKnowledgeBasePermissions = async (knowledgeBaseId, permissions) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions`, {
        method: 'PUT',
        data: { permissions }
    });
    return response;
};

export const addKnowledgeBasePermission = async (knowledgeBaseId, userId, role) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions`, {
        method: 'POST',
        data: { user_id: userId, role }
    });
    return response;
};

export const removeKnowledgeBasePermission = async (knowledgeBaseId, permissionId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions/${permissionId}`, {
        method: 'DELETE'
    });
    return response;
};

// Document Tag API
export const getDocumentTags = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags`, {
        method: 'GET'
    });
    return response;
};

export const addDocumentTag = async (documentId, tagName) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags`, {
        method: 'POST',
        data: { tag_name: tagName }
    });
    return response;
};

export const removeDocumentTag = async (documentId, tagId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags/${tagId}`, {
        method: 'DELETE'
    });
    return response;
};

export const getAllTags = async (knowledgeBaseId = null) => {
    const response = await request('/v1/knowledge/tags', {
        method: 'GET',
        params: { knowledge_base_id: knowledgeBaseId }
    });
    return response;
};

export const searchDocumentsByTag = async (tagId, knowledgeBaseId = null) => {
    const response = await request(`/v1/knowledge/tags/${tagId}/documents`, {
        method: 'GET',
        params: { knowledge_base_id: knowledgeBaseId }
    });
    return response;
};

// Document Processing API
/**
 * 启动文档处理（向量化、图谱化）
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 处理启动结果
 */
export const processDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/process`, {
        method: 'POST',
        timeout: 120000  // 120秒超时，ChromaDB服务响应较慢时需要更长时间
    });
    return response;
};

// Document Vectorization API（兼容旧接口）
export const vectorizeDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/vectorize`, {
        method: 'POST',
        timeout: 300000  // 向量化操作可能需要较长时间，设置5分钟超时
    });
    return response;
};

/**
 * 异步向量化文档
 * 启动向量化任务后立即返回，通过WebSocket监听进度
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 包含taskId的任务信息
 */
export const vectorizeDocumentAsync = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/vectorize-async`, {
        method: 'POST',
        timeout: 10000  // 异步接口快速返回，10秒超时足够
    });
    return response;
};

/**
 * 获取文档向量化任务状态
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 任务状态
 */
export const getVectorizationStatus = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/vectorize-status`, {
        method: 'GET',
        timeout: 10000
    });
    return response;
};

// Document Chunks API
export const getDocumentChunks = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/chunks`, {
        method: 'GET'
    });
    return response;
};

// Knowledge Base Import/Export API
export const exportKnowledgeBase = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/export`, {
        method: 'GET',
        responseType: 'json'
    });
    return response;
};

export const importKnowledgeBase = async (knowledgeBaseData) => {
    const response = await request('/v1/knowledge/knowledge-bases/import', {
        method: 'POST',
        data: knowledgeBaseData
    });
    return response;
};

// Knowledge Graph API
export const buildKnowledgeGraph = async (documentId = null, knowledgeBaseId = null) => {
    const response = await request('/v1/knowledge-graph/build-graph', {
        method: 'POST',
        data: {
            document_id: documentId,
            knowledge_base_id: knowledgeBaseId
        }
    });
    return response;
};

export const getDocumentGraphData = async (documentId) => {
    const response = await request(`/v1/knowledge-graph/documents/${documentId}/graph`, {
        method: 'GET',
        timeout: 60000  // 文档图谱设置为1分钟超时
    });
    return response;
};

export const getKnowledgeBaseGraphData = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge-graph/knowledge-bases/${knowledgeBaseId}/graph`, {
        method: 'GET',
        timeout: 120000  // 知识图谱构建可能需要较长时间，设置为2分钟
    });
    return response;
};

/**
 * 获取文档处理进度
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 处理进度信息
 */
export const getDocumentProcessingProgress = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/progress`, {
        method: 'GET',
        timeout: 30000  // 30秒超时，进度查询应该很快返回，但后端繁忙时可能需要更长时间
    });
    return response;
};

export const analyzeKnowledgeGraph = async (graphId) => {
    const response = await request(`/v1/knowledge-graph/graphs/${graphId}/analyze`, {
        method: 'GET'
    });
    return response;
};

export const getGraphStatistics = async (graphId) => {
    const response = await request(`/v1/knowledge-graph/graphs/${graphId}/statistics`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取文档处理队列状态
 *
 * @returns {Promise<Object>} 队列状态信息
 */
export const getProcessingQueueStatus = async () => {
    const response = await request('/v1/knowledge/processing-queue/status', {
        method: 'GET',
        timeout: 60000  // 60秒超时，队列状态查询可能因后端繁忙而延迟
    });
    return response;
};

/**
 * 从文本中提取实体
 *
 * @param {string} text - 要分析的文本
 * @returns {Promise<Object>} 提取的实体列表
 */
/**
 * 实体识别
 * @param {string|Object} params - 文本或参数对象
 * @param {string} params.text - 要识别的文本
 * @param {string[]} params.entity_types - 实体类型列表
 * @param {number} params.threshold - 置信度阈值
 * @param {number} params.model_id - 模型ID
 * @param {Object} params.model_config - 模型配置
 */
export const extractEntities = async (params) => {
    // 兼容旧版调用方式（直接传入字符串）
    const requestData = typeof params === 'string' 
        ? { text: params }
        : params;
    
    const response = await request('/v1/knowledge-graph/extract-entities', {
        method: 'POST',
        data: requestData
    });
    return response;
};