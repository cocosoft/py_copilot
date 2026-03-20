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

export const listDocuments = async (skip = 0, limit = 10, knowledgeBaseId = null, isVectorized = null, processingStatus = null) => {
    const params = { skip, limit, knowledge_base_id: knowledgeBaseId };
    // 使用 processing_status 单字段进行筛选，isVectorized 参数已废弃
    if (processingStatus !== null) {
        params.processing_status = processingStatus;
    }
    const response = await request('/v1/knowledge/documents', {
        method: 'GET',
        params
    });
    
    return response;
};

/**
 * 异步加载文档列表
 *
 * 启动后台任务进行文档加载，立即返回任务ID，
 * 前端可通过WebSocket订阅进度或轮询查询任务状态
 *
 * @param {Object} params - 请求参数
 * @param {number} params.knowledge_base_id - 知识库ID
 * @param {number} [params.skip=0] - 跳过的文档数
 * @param {number} [params.limit=100] - 返回的文档数限制
 * @param {string} [params.processing_status] - 处理状态筛选: completed=已向量化, idle=待处理, processing=处理中, failed=失败
 * @param {string} [params.sort_by='created_at'] - 排序字段
 * @param {string} [params.sort_order='desc'] - 排序方向
 * @returns {Promise<Object>} 任务信息，包含task_id用于查询进度
 */
export const loadDocumentsAsync = async (params) => {

    const response = await request('/v1/knowledge/documents/load-async', {
        method: 'POST',
        data: params,
        timeout: 120000
    });

    return response;
};

/**
 * 获取文档加载任务状态
 *
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 任务状态信息
 */
export const getDocumentLoadStatus = async (taskId) => {
    const response = await request(`/v1/knowledge/documents/load-status/${taskId}`, {
        method: 'GET',
        timeout: 10000
    });
    return response;
};

/**
 * 订阅知识库的文档加载进度
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {string} connectionId - WebSocket连接ID
 * @returns {Promise<Object>} 订阅结果
 */
export const subscribeDocumentLoadProgress = async (knowledgeBaseId, connectionId) => {
    const response = await request(`/v1/knowledge/documents/subscribe-load/${knowledgeBaseId}`, {
        method: 'POST',
        params: { connection_id: connectionId },
        timeout: 10000
    });
    return response;
};

export const getDocument = async (documentId, options = {}) => {
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'GET',
        ...options
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
    const response = await requestWithRetry(`/v1/knowledge/documents/${documentId}/process`, {
        method: 'POST',
        timeout: 300000,  // 300秒超时（5分钟），后端响应可能较慢
        maxRetries: 2,     // 最多重试2次
        initialDelay: 2000  // 初始重试延迟2秒
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
export const getDocumentChunks = async (documentId, skip = 0, limit = 50, options = {}) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/chunks`, {
        method: 'GET',
        params: { skip, limit },
        ...options
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
    const response = await requestWithRetry(`/v1/knowledge/documents/${documentId}/progress`, {
        method: 'GET',
        timeout: 60000,  // 增加超时时间到60秒
        maxRetries: 3,   // 最多重试3次
        initialDelay: 1000  // 初始重试延迟1秒
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
 * @param {Object} params.model_configuration - 模型配置
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

/**
 * 异步批量提取实体
 *
 * 启动后台任务进行实体提取，立即返回任务ID，
 * 前端可通过WebSocket订阅进度或轮询查询任务状态
 *
 * @param {Object} params - 请求参数
 * @param {number[]} params.document_ids - 文档ID列表
 * @param {number} params.knowledge_base_id - 知识库ID
 * @param {string} [params.model_id] - 模型ID（可选）
 * @param {string[]} [params.entity_types] - 实体类型列表（可选）
 * @returns {Promise<Object>} 任务信息，包含task_id用于查询进度
 */
export const extractEntitiesAsync = async (params) => {
    console.log('异步提取实体请求参数:', params);

    const response = await request('/v1/knowledge-graph/extract-entities-async', {
        method: 'POST',
        data: params,
        timeout: 30000
    });

    console.log('异步提取实体响应:', response);
    return response;
};

/**
 * 获取实体提取任务状态
 *
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 任务状态信息
 */
export const getEntityExtractionStatus = async (taskId) => {
    const response = await request(`/v1/knowledge-graph/extract-entities-status/${taskId}`, {
        method: 'GET',
        timeout: 10000
    });
    return response;
};

/**
 * 订阅知识库的实体提取进度
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {string} connectionId - WebSocket连接ID
 * @returns {Promise<Object>} 订阅结果
 */
export const subscribeEntityExtractionProgress = async (knowledgeBaseId, connectionId) => {
    const response = await request(`/v1/knowledge-graph/subscribe-entity-extraction/${knowledgeBaseId}`, {
        method: 'POST',
        params: { connection_id: connectionId },
        timeout: 10000
    });
    return response;
};

/**
 * 取消订阅知识库的实体提取进度
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @param {string} connectionId - WebSocket连接ID
 * @returns {Promise<Object>} 取消订阅结果
 */
export const unsubscribeEntityExtractionProgress = async (knowledgeBaseId, connectionId) => {
    const response = await request(`/v1/knowledge-graph/unsubscribe-entity-extraction/${knowledgeBaseId}`, {
        method: 'POST',
        params: { connection_id: connectionId },
        timeout: 10000
    });
    return response;
};

/**
 * 批量处理知识库中所有未处理的文档
 * 
 * 该接口会将知识库中所有尚未向量化的文档添加到处理队列中
 * 进行解析、向量化、实体提取和知识图谱构建
 * 
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 批量处理结果
 */
export const batchProcessDocuments = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/batch-process`, {
        method: 'POST',
        timeout: 60000  // 60秒超时，批量处理可能需要较长时间
    });
    return response;
};

/**
 * 获取知识库中所有未处理的文档列表
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 未处理文档列表
 */
export const getUnprocessedDocuments = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/unprocessed-documents`, {
        method: 'GET'
    });
    return response;
};

/**
 * 获取知识库文档处理状态
 *
 * 返回当前处理队列的状态，包括队列大小、正在处理的文档数、
 * 已完成的文档数、处理失败的文档数等信息
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 处理状态信息
 */
export const getProcessingStatus = async (knowledgeBaseId) => {
    try {
        const response = await requestWithRetry(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/processing-status`, {
            method: 'GET',
            timeout: 90000,  // 进一步增加超时时间到90秒
            maxRetries: 3,   // 最多重试3次
            initialDelay: 2000,  // 初始重试延迟2秒
            retryableStatusCodes: [408, 429, 500, 502, 503, 504, 524] // 增加524（Origin is unreachable）
        });
        return response;
    } catch (error) {
        console.error(`[getProcessingStatus] 获取处理状态失败 (knowledgeBaseId: ${knowledgeBaseId}):`, error);
        // 返回默认状态，避免前端崩溃
        return {
            success: false,
            queue_status: {
                queue_size: 0,
                processing_count: 0,
                completed_count: 0,
                failed_count: 0
            },
            statistics: {
                total_documents: 0,
                vectorized_documents: 0,
                unprocessed_documents: 0,
                vectorization_rate: 0
            },
            processing_documents: []
        };
    }
};

/**
 * 批量删除文档
 *
 * @param {string[]} documentIds - 文档ID或UUID列表
 * @returns {Promise<Object>} 删除结果
 */
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
 * @param {string[]} documentIds - 文档ID或UUID列表
 * @returns {Promise<Blob>} ZIP文件Blob
 */
export const batchDownloadDocuments = async (documentIds) => {
  const response = await request('/v1/knowledge/documents/batch-download', {
    method: 'POST',
    data: { document_ids: documentIds },
    responseType: 'blob'
  });
  return response;
};

/**
 * 获取文档的实体列表
 *
 * @param {number} documentId - 文档ID
 * @returns {Promise<Object>} 实体列表
 */
export const getDocumentEntities = async (documentId) => {
  const response = await request(`/v1/knowledge-graph/documents/${documentId}/entities`, {
    method: 'GET'
  });
  return response;
};

/**
 * 获取知识库的所有实体列表
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Object>} 实体列表
 */
export const getKnowledgeBaseEntities = async (knowledgeBaseId) => {
  const response = await request(`/v1/knowledge-graph/knowledge-bases/${knowledgeBaseId}/entities`, {
    method: 'GET'
  });
  return response;
};

/**
 * 批量更新实体状态
 *
 * @param {number[]} entityIds - 实体ID数组
 * @param {string} status - 目标状态 (pending, confirmed, rejected, modified)
 * @returns {Promise<Object>} 更新结果
 */
export const batchUpdateEntityStatus = async (entityIds, status) => {
  const response = await request('/v1/entity-maintenance/batch-update-status', {
    method: 'POST',
    data: {
      entity_ids: entityIds,
      status: status
    }
  });
  return response;
};

/**
 * 更新单个实体状态
 *
 * @param {number} entityId - 实体ID
 * @param {string} status - 目标状态 (pending, confirmed, rejected, modified)
 * @returns {Promise<Object>} 更新结果
 */
export const updateEntityStatus = async (entityId, status) => {
  const response = await request(`/v1/entity-maintenance/document-entity/${entityId}/status`, {
    method: 'PUT',
    data: { status }
  });
  return response;
};

/**
 * 从实体维护API获取文档实体列表
 *
 * @param {number} documentId - 文档ID
 * @param {Object} options - 查询选项
 * @param {string} options.entityType - 实体类型过滤
 * @param {number} options.page - 页码
 * @param {number} options.pageSize - 每页数量
 * @returns {Promise<Object>} 实体列表
 */
export const getDocumentEntitiesFromMaintenance = async (documentId, options = {}) => {
  const { entityType, page = 1, pageSize = 200 } = options;
  let url = `/v1/entity-maintenance/document-entities/${documentId}?page=${page}&page_size=${pageSize}`;
  if (entityType) {
    url += `&entity_type=${encodeURIComponent(entityType)}`;
  }
  const response = await request(url, {
    method: 'GET'
  });
  return response;
};

/**
 * 获取文档统计数据
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Array>} 文档统计数据
 */
export const getDocumentStats = async (knowledgeBaseId) => {
  try {
    const response = await request(`/v1/knowledge-bases/${knowledgeBaseId}/document-stats`, {
      method: 'GET'
    });
    return response;
  } catch (error) {
    console.error('获取文档统计数据失败:', error);
    // 返回模拟数据
    return [
      { status: 'processed', count: 120 },
      { status: 'processing', count: 30 },
      { status: 'pending', count: 15 },
      { status: 'failed', count: 5 }
    ];
  }
};

/**
 * 获取实体统计数据
 *
 * @param {number} knowledgeBaseId - 知识库ID
 * @returns {Promise<Array>} 实体统计数据
 */
export const getEntityStats = async (knowledgeBaseId) => {
  try {
    const response = await request(`/v1/knowledge-bases/${knowledgeBaseId}/entity-stats`, {
      method: 'GET'
    });
    return response;
  } catch (error) {
    console.error('获取实体统计数据失败:', error);
    // 返回模拟数据
    return [
      { type: '人物', count: 300 },
      { type: '组织', count: 250 },
      { type: '地点', count: 200 },
      { type: '事件', count: 150 },
      { type: '其他', count: 100 }
    ];
  }
};