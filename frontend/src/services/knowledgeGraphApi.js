/**
 * 知识图谱API服务
 * 
 * 提供与后端知识图谱API的集成
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.REACT_APP_API_URL || '/api/v1';

/**
 * 知识图谱API客户端
 */
class KnowledgeGraphApiService {
  constructor() {
    this.baseURL = `${API_BASE_URL}`;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response.data,
      (error) => {
        console.error('API请求失败:', error);
        return Promise.reject(error);
      }
    );
  }

  // ============== 知识图谱构建任务 ==============

  /**
   * 提交知识图谱构建任务
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {string[]} documentIds - 文档ID列表
   * @param {Object} options - 构建选项
   * @returns {Promise<Object>} 任务信息
   */
  async buildKnowledgeGraph(knowledgeBaseId, documentIds, options = {}) {
    return this.client.post('/kg-tasks/build-knowledge-graph', {
      knowledge_base_id: knowledgeBaseId,
      document_ids: documentIds,
      build_options: options,
    });
  }

  /**
   * 提交文档层构建任务
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {string[]} documentIds - 文档ID列表
   * @param {Object} options - 构建选项
   * @returns {Promise<Object>} 任务信息
   */
  async buildDocumentLayer(knowledgeBaseId, documentIds, options = {}) {
    return this.client.post('/kg-tasks/build-document-layer', {
      knowledge_base_id: knowledgeBaseId,
      document_ids: documentIds,
      options,
    });
  }

  /**
   * 提交实体提取任务
   * @param {string} documentId - 文档ID
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {Object} options - 提取选项
   * @returns {Promise<Object>} 任务信息
   */
  async extractEntities(documentId, knowledgeBaseId, options = {}) {
    return this.client.post('/kg-tasks/extract-entities', {
      document_id: documentId,
      knowledge_base_id: knowledgeBaseId,
      extraction_options: options,
    });
  }

  /**
   * 提交批量实体提取任务
   * @param {string[]} documentIds - 文档ID列表
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {Object} options - 批量选项
   * @returns {Promise<Object>} 任务信息
   */
  async batchExtractEntities(documentIds, knowledgeBaseId, options = {}) {
    return this.client.post('/kg-tasks/batch-extract', {
      document_ids: documentIds,
      knowledge_base_id: knowledgeBaseId,
      batch_options: options,
    });
  }

  /**
   * 提交实体对齐任务
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {string[]} entityIds - 实体ID列表
   * @param {Object} options - 对齐选项
   * @returns {Promise<Object>} 任务信息
   */
  async alignEntities(knowledgeBaseId, entityIds, options = {}) {
    return this.client.post('/kg-tasks/align-entities', {
      knowledge_base_id: knowledgeBaseId,
      entity_ids: entityIds,
      alignment_options: options,
    });
  }

  /**
   * 提交跨知识库链接任务
   * @param {string} sourceKbId - 源知识库ID
   * @param {string} targetKbId - 目标知识库ID
   * @param {Object} options - 链接选项
   * @returns {Promise<Object>} 任务信息
   */
  async crossKBLink(sourceKbId, targetKbId, options = {}) {
    return this.client.post('/kg-tasks/cross-kb-link', {
      source_kb_id: sourceKbId,
      target_kb_id: targetKbId,
      link_options: options,
    });
  }

  // ============== 任务状态管理 ==============

  /**
   * 获取任务状态
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} 任务状态
   */
  async getTaskStatus(taskId) {
    return this.client.get(`/kg-tasks/${taskId}/status`);
  }

  /**
   * 获取任务列表
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} 任务列表
   */
  async getTaskList(params = {}) {
    return this.client.get('/kg-tasks/list', { params });
  }

  /**
   * 取消任务
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} 取消结果
   */
  async revokeTask(taskId) {
    return this.client.post(`/kg-tasks/${taskId}/revoke`);
  }

  /**
   * 获取任务结果
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} 任务结果
   */
  async getTaskResult(taskId) {
    return this.client.get(`/kg-tasks/${taskId}/result`);
  }

  /**
   * 轮询任务状态直到完成
   * @param {string} taskId - 任务ID
   * @param {Function} onProgress - 进度回调
   * @param {number} interval - 轮询间隔(ms)
   * @returns {Promise<Object>} 最终结果
   */
  async pollTaskStatus(taskId, onProgress = null, interval = 1000) {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getTaskStatus(taskId);
          
          if (onProgress) {
            onProgress(status);
          }

          if (status.status === 'success') {
            resolve(status);
          } else if (status.status === 'failure') {
            reject(new Error(status.message || '任务执行失败'));
          } else {
            setTimeout(poll, interval);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  // ============== 知识图谱数据 ==============

  /**
   * 获取知识图谱数据
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {string} layer - 图层类型 (document, kb, global)
   * @returns {Promise<Object>} 图谱数据
   */
  async getGraphData(knowledgeBaseId, layer = 'document') {
    const params = { layer };
    if (knowledgeBaseId) {
      params.knowledge_base_id = knowledgeBaseId;
    }
    return this.client.get('/knowledge-graph/graph-data', { params });
  }

  /**
   * 获取文档级知识图谱数据
   * @param {string} documentId - 文档ID
   * @returns {Promise<Object>} 图谱数据
   */
  async getDocumentGraph(documentId) {
    return this.client.get('/knowledge-graph/graph-data', {
      params: {
        layer: 'document',
        document_id: documentId
      }
    });
  }

  /**
   * 获取知识图谱统计信息
   * @param {string} knowledgeBaseId - 知识库ID
   * @returns {Promise<Object>} 统计信息
   */
  async getGraphStats(knowledgeBaseId) {
    return this.client.get(`/knowledge-graph/${knowledgeBaseId}/stats`);
  }

  /**
   * 搜索实体
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {string} query - 搜索关键词
   * @param {Object} options - 搜索选项
   * @returns {Promise<Object>} 搜索结果
   */
  async searchEntities(knowledgeBaseId, query, options = {}) {
    return this.client.get(`/knowledge-graph/${knowledgeBaseId}/search`, {
      params: {
        q: query,
        ...options,
      },
    });
  }

  /**
   * 获取实体详情
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {string} entityId - 实体ID
   * @returns {Promise<Object>} 实体详情
   */
  async getEntityDetail(knowledgeBaseId, entityId) {
    return this.client.get(`/knowledge-graph/${knowledgeBaseId}/entities/${entityId}`);
  }

  /**
   * 导出知识图谱
   * @param {string} knowledgeBaseId - 知识库ID
   * @param {string} format - 导出格式
   * @returns {Promise<Blob>} 导出文件
   */
  async exportGraph(knowledgeBaseId, format = 'json') {
    return this.client.get(`/knowledge-graph/${knowledgeBaseId}/export`, {
      params: { format },
      responseType: 'blob',
    });
  }

  // ============== 配置管理 ==============

  /**
   * 获取实体类型配置
   * @param {string} knowledgeBaseId - 知识库ID
   * @returns {Promise<Object>} 实体类型配置
   */
  async getEntityTypes(knowledgeBaseId) {
    return this.client.get(`/knowledge-graph/${knowledgeBaseId}/entity-types`);
  }

  /**
   * 获取关系类型配置
   * @param {string} knowledgeBaseId - 知识库ID
   * @returns {Promise<Object>} 关系类型配置
   */
  async getRelationshipTypes(knowledgeBaseId) {
    return this.client.get(`/knowledge-graph/${knowledgeBaseId}/relationship-types`);
  }

  /**
   * 获取提取规则
   * @param {string} knowledgeBaseId - 知识库ID
   * @returns {Promise<Object>} 提取规则
   */
  async getExtractionRules(knowledgeBaseId) {
    return this.client.get(`/knowledge-graph/${knowledgeBaseId}/extraction-rules`);
  }

  // ============== 知识图谱数据清理 ==============

  /**
   * 清理知识图谱数据
   * @param {Object} params - 清理参数
   * @param {string} params.level - 清理级别: all, document, kb, global
   * @param {number} params.knowledge_base_id - 知识库ID（可选）
   * @param {number} params.document_id - 文档ID（可选）
   * @param {boolean} params.confirm - 是否确认删除
   * @returns {Promise<Object>} 清理结果
   */
  async clearGraphData(params) {
    return this.client.post('/knowledge-graph/clear-data', params);
  }
}

// 创建单例实例
const knowledgeGraphApi = new KnowledgeGraphApiService();

export default knowledgeGraphApi;
export { KnowledgeGraphApiService };
