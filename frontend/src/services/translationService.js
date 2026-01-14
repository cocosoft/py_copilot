import apiClient from './apiClient';

// Translation API endpoints
const TRANSLATION_ENDPOINTS = {
  TRANSLATE_TEXT: '/v1/tasks/process',
  GET_LANGUAGES: '/v1/translation-history/languages', // Use translation history endpoint for languages
  GET_TRANSLATION_HISTORY: '/v1/translation-history/translation-history',
  SAVE_TRANSLATION_HISTORY: '/v1/translation-history/translation-history',
  CLEAR_TRANSLATION_HISTORY: '/v1/translation-history/translation-history/clear',
  RATE_TRANSLATION: '/v1/translation-history/translation-history/rate',
  SUBMIT_FEEDBACK: '/v1/translation-feedback',
  GET_TRANSLATION_STATS: '/v1/translation-history/translation-history/stats',
  // Translation memory functionality is not available in backend - using translation history instead
  GET_TRANSLATION_MEMORY: '/v1/translation-history/translation-history',
  SAVE_TRANSLATION_MEMORY: '/v1/translation-history/translation-history',
  SEARCH_TRANSLATION_MEMORY: '/v1/translation-history/translation-history',
  GET_TERMINOLOGY: '/v1/terminology/',
  SAVE_TERMINOLOGY: '/v1/terminology/',
  SEARCH_TERMINOLOGY: '/v1/terminology/search',
  GET_KNOWLEDGE_BASES: '/v1/knowledge/knowledge-bases',
  SEARCH_KNOWLEDGE_BASE: '/v1/knowledge/knowledge-bases/search',
  GET_MEMORY_CONTEXT: '/v1/memory/memory-context',
  GET_TRANSLATION_MODELS: '/v1/translation-models',
  GET_TRANSLATION_AGENTS: '/v1/agents/translation-agents',
  GET_DEFAULT_TRANSLATION_MODEL: '/v1/default-translation-model',
  SET_DEFAULT_TRANSLATION_MODEL: '/v1/default-translation-model',
  GET_MODEL_CAPABILITIES: '/v1/model_capabilities',
  GET_RECOMMENDED_MODELS: '/v1/recommended-models',
  TRANSLATE_DOCUMENT: '/v1/translate/translate/document',
  GET_SUPPORTED_DOCUMENT_FORMATS: '/v1/translate/translate/supported-formats',
  BATCH_TRANSLATE: '/v1/batch-translate/translate/batch',
  GET_BATCH_TRANSLATION_STATUS: '/v1/batch-translate/translate/batch/status',
  CANCEL_BATCH_TRANSLATION: '/v1/batch-translate/translate/batch/cancel',
};

/**
 * 翻译文本
 * @param {Object} params - 翻译参数
 * @param {string} params.text - 要翻译的文本
 * @param {string} params.source_language - 源语言
 * @param {string} params.target_language - 目标语言
 * @param {string} [params.agent_id] - 智能体ID
 * @param {string} [params.model_id] - 模型ID
 * @param {Object} [params.options] - 翻译选项
 * @returns {Promise<Object>} 翻译结果
 */
export const translateText = async (params) => {
  try {
    const { text, ...options } = params;
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.TRANSLATE_TEXT, {
      task_type: 'translate',
      text: text,
      options: options,
    });
    return response.data;
  } catch (error) {
    console.error('翻译API调用失败:', error);
    throw error;
  }
};

/**
 * 获取支持的语言列表
 * @returns {Promise<Object>} 语言列表
 */
export const getSupportedLanguages = async () => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_LANGUAGES);
    return response.data;
  } catch (error) {
    console.error('获取语言列表API调用失败:', error);
    throw error;
  }
};

/**
 * 获取翻译历史
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页数量
 * @param {string} [params.search] - 搜索关键词
 * @param {string} [params.source_language] - 源语言筛选
 * @param {string} [params.target_language] - 目标语言筛选
 * @param {string} [params.date_range] - 时间范围筛选
 * @returns {Promise<Object>} 翻译历史列表
 */
export const getTranslationHistory = async (params = {}) => {
  try {
    // 过滤掉空字符串参数，只保留有值的参数
    const filteredParams = Object.fromEntries(
      Object.entries(params).filter(([_, value]) => value !== '' && value != null)
    );
    
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_TRANSLATION_HISTORY, {
      params: {
        page: 1,
        page_size: 10,
        ...filteredParams,
      },
    });
    return response.data;
  } catch (error) {
    console.error('获取翻译历史API调用失败:', error);
    throw error;
  }
};

/**
 * 保存翻译历史
 * @param {Object} historyData - 翻译历史数据
 * @param {string} historyData.source_text - 源文本
 * @param {string} historyData.translated_text - 翻译后的文本
 * @param {string} historyData.source_language - 源语言
 * @param {string} historyData.target_language - 目标语言
 * @param {string} [historyData.agent_id] - 使用的智能体ID
 * @param {string} [historyData.model_id] - 使用的模型ID
 * @returns {Promise<Object>} 保存结果
 */
export const saveTranslationHistory = async (historyData) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.SAVE_TRANSLATION_HISTORY, historyData);
    return response.data;
  } catch (error) {
    console.error('保存翻译历史API调用失败:', error);
    throw error;
  }
};

/**
 * 获取翻译智能体列表
 * @returns {Promise<Object>} 智能体列表
 */
export const getTranslationAgents = async () => {
  try {
    const response = await apiClient.get('/v1/agents/', {
      params: {
        skip: 0,
        limit: 100,
      },
    });
    return response.data;
  } catch (error) {
    console.error('获取翻译智能体列表API调用失败:', error);
    throw error;
  }
};

/**
 * 获取翻译模型列表
 * @returns {Promise<Object>} 模型列表
 */
export const getTranslationModels = async () => {
  try {
    const response = await apiClient.get('/v1/models/by-scene/translate');
    return response.data;
  } catch (error) {
    console.error('获取翻译模型列表API调用失败:', error);
    throw error;
  }
};

/**
 * 清空翻译历史记录
 * @returns {Promise<Object>} 清空结果
 */
export const clearTranslationHistory = async () => {
  try {
    const response = await apiClient.delete(TRANSLATION_ENDPOINTS.CLEAR_TRANSLATION_HISTORY);
    return response.data;
  } catch (error) {
    console.error('清空翻译历史API调用失败:', error);
    throw error;
  }
};

/**
 * 对翻译结果进行评分
 * @param {Object} ratingData - 评分数据
 * @param {string} ratingData.translation_id - 翻译记录ID
 * @param {number} ratingData.rating - 评分（1-5分）
 * @param {string} [ratingData.feedback] - 反馈意见
 * @returns {Promise<Object>} 评分结果
 */
export const rateTranslation = async (ratingData) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.RATE_TRANSLATION, ratingData);
    return response.data;
  } catch (error) {
    console.error('翻译评分API调用失败:', error);
    throw error;
  }
};

/**
 * 提交翻译反馈
 * @param {Object} feedbackData - 反馈数据
 * @param {string} feedbackData.translation_id - 翻译记录ID
 * @param {string} feedbackData.feedback_type - 反馈类型（quality, accuracy, fluency, other）
 * @param {string} feedbackData.feedback_text - 反馈内容
 * @param {string} [feedbackData.suggested_translation] - 建议的翻译
 * @returns {Promise<Object>} 反馈结果
 */
export const submitTranslationFeedback = async (feedbackData) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.SUBMIT_FEEDBACK, feedbackData);
    return response.data;
  } catch (error) {
    console.error('提交翻译反馈API调用失败:', error);
    throw error;
  }
};

/**
 * 获取翻译统计数据
 * @param {Object} [params] - 查询参数
 * @param {string} [params.date_range] - 时间范围
 * @param {string} [params.language_pair] - 语言对
 * @returns {Promise<Object>} 统计数据
 */
export const getTranslationStats = async (params = {}) => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_TRANSLATION_STATS, {
      params: {
        ...params,
      },
    });
    return response.data;
  } catch (error) {
    console.error('获取翻译统计数据API调用失败:', error);
    throw error;
  }
};

/**
 * 获取翻译记忆（使用翻译历史作为替代）
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页数量
 * @param {string} [params.source_language] - 源语言筛选
 * @param {string} [params.target_language] - 目标语言筛选
 * @returns {Promise<Object>} 翻译记忆列表
 */
export const getTranslationMemory = async (params = {}) => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_TRANSLATION_MEMORY, {
      params: {
        page: 1,
        page_size: 10,
        ...params,
      },
    });
    return response.data;
  } catch (error) {
    console.error('获取翻译记忆API调用失败:', error);
    throw error;
  }
};

/**
 * 保存翻译记忆（使用翻译历史作为替代）
 * @param {Object} memoryData - 翻译记忆数据
 * @param {string} memoryData.source_text - 源文本
 * @param {string} memoryData.target_text - 目标文本
 * @param {string} memoryData.source_language - 源语言
 * @param {string} memoryData.target_language - 目标语言
 * @param {string} [memoryData.domain] - 领域（如技术、商务等）
 * @param {string} [memoryData.tags] - 标签
 * @returns {Promise<Object>} 保存结果
 */
export const saveTranslationMemory = async (memoryData) => {
  try {
    // 保存到翻译历史，作为翻译记忆的替代方案
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.SAVE_TRANSLATION_MEMORY, memoryData);
    return response.data;
  } catch (error) {
    console.error('保存翻译记忆API调用失败:', error);
    throw error;
  }
};

/**
 * 搜索翻译记忆（使用翻译历史作为替代）
 * @param {Object} searchParams - 搜索参数
 * @param {string} searchParams.query - 搜索查询
 * @param {string} [searchParams.source_language] - 源语言
 * @param {string} [searchParams.target_language] - 目标语言
 * @param {string} [searchParams.domain] - 领域筛选
 * @param {number} [searchParams.similarity_threshold=0.7] - 相似度阈值
 * @returns {Promise<Object>} 搜索结果
 */
export const searchTranslationMemory = async (searchParams) => {
  try {
    // 使用翻译历史的搜索功能，作为翻译记忆搜索的替代方案
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.SEARCH_TRANSLATION_MEMORY, {
      params: {
        search: searchParams.query,
        source_language: searchParams.source_language,
        target_language: searchParams.target_language,
        page: 1,
        page_size: 10
      }
    });
    return response.data;
  } catch (error) {
    console.error('搜索翻译记忆API调用失败:', error);
    throw error;
  }
};

/**
 * 获取术语库条目
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页数量
 * @param {string} [params.source_language] - 源语言筛选
 * @param {string} [params.target_language] - 目标语言筛选
 * @param {string} [params.domain] - 领域筛选
 * @returns {Promise<Object>} 术语库列表
 */
export const getTerminology = async (params = {}) => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_TERMINOLOGY, {
      params: {
        page: 1,
        page_size: 10,
        ...params,
      },
    });
    return response.data;
  } catch (error) {
    console.error('获取术语库API调用失败:', error);
    throw error;
  }
};

/**
 * 保存术语库条目
 * @param {Object} termData - 术语数据
 * @param {string} termData.source_term - 源术语
 * @param {string} termData.target_term - 目标术语
 * @param {string} termData.source_language - 源语言
 * @param {string} termData.target_language - 目标语言
 * @param {string} [termData.domain] - 领域
 * @param {string} [termData.description] - 术语描述
 * @param {string} [termData.tags] - 标签
 * @returns {Promise<Object>} 保存结果
 */
export const saveTerminology = async (termData) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.SAVE_TERMINOLOGY, termData);
    return response.data;
  } catch (error) {
    console.error('保存术语库API调用失败:', error);
    throw error;
  }
};

/**
 * 搜索术语库
 * @param {Object} searchParams - 搜索参数
 * @param {string} searchParams.query - 搜索查询
 * @param {string} [searchParams.source_language] - 源语言
 * @param {string} [searchParams.target_language] - 目标语言
 * @param {string} [searchParams.domain] - 领域筛选
 * @returns {Promise<Object>} 搜索结果
 */
export const searchTerminology = async (searchParams) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.SEARCH_TERMINOLOGY, {
      query: searchParams.query,
      source_language: searchParams.source_language,
      target_language: searchParams.target_language,
      domain: searchParams.domain
    });
    return response.data;
  } catch (error) {
    console.error('搜索术语库API调用失败:', error);
    throw error;
  }
};

/**
 * 获取知识库列表
 * @returns {Promise<Object>} 知识库列表
 */
export const getKnowledgeBases = async () => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_KNOWLEDGE_BASES);
    return response.data;
  } catch (error) {
    console.error('获取知识库列表API调用失败:', error);
    throw error;
  }
};

/**
 * 搜索知识库
 * @param {Object} searchParams - 搜索参数
 * @param {string} searchParams.query - 搜索查询
 * @param {number} searchParams.knowledge_base_id - 知识库ID
 * @param {number} [searchParams.limit=5] - 返回结果数量
 * @returns {Promise<Object>} 搜索结果
 */
export const searchKnowledgeBase = async (searchParams) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.SEARCH_KNOWLEDGE_BASE, searchParams);
    return response.data;
  } catch (error) {
    console.error('搜索知识库API调用失败:', error);
    throw error;
  }
};

/**
 * 获取记忆上下文
 * @param {Object} params - 参数
 * @param {string} params.text - 查询文本
 * @param {string} [params.user_id] - 用户ID
 * @param {number} [params.limit=3] - 返回结果数量
 * @returns {Promise<Object>} 记忆上下文
 */
export const getMemoryContext = async (params) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.GET_MEMORY_CONTEXT, params);
    return response.data;
  } catch (error) {
    console.error('获取记忆上下文API调用失败:', error);
    throw error;
  }
};





/**
 * 获取默认翻译模型
 * @returns {Promise<Object>} 默认翻译模型
 */
export const getDefaultTranslationModel = async () => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_DEFAULT_TRANSLATION_MODEL);
    return response.data;
  } catch (error) {
    console.error('获取默认翻译模型API调用失败:', error);
    throw error;
  }
};

/**
 * 设置默认翻译模型
 * @param {string} modelId - 模型ID
 * @returns {Promise<Object>} 设置结果
 */
export const setDefaultTranslationModel = async (modelId) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.SET_DEFAULT_TRANSLATION_MODEL, {
      model_id: modelId
    });
    return response.data;
  } catch (error) {
    console.error('设置默认翻译模型API调用失败:', error);
    throw error;
  }
};

/**
 * 获取模型能力列表
 * @param {Object} [params] - 查询参数
 * @param {string} [params.domain='translation'] - 领域
 * @param {boolean} [params.is_active=true] - 是否激活
 * @returns {Promise<Object>} 模型能力列表
 */
export const getModelCapabilities = async (params = {}) => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_MODEL_CAPABILITIES, {
      params: {
        domain: 'translation',
        is_active: true,
        ...params
      }
    });
    return response.data;
  } catch (error) {
    console.error('获取模型能力列表API调用失败:', error);
    throw error;
  }
};

/**
 * 获取推荐模型列表
 * @param {Object} [params] - 查询参数
 * @param {string} [params.scene] - 翻译场景
 * @param {Array} [params.capabilities] - 所需能力
 * @param {number} [params.limit=5] - 返回数量
 * @returns {Promise<Object>} 推荐模型列表
 */
export const getRecommendedModels = async (params = {}) => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_RECOMMENDED_MODELS, {
      params: {
        limit: 5,
        ...params
      }
    });
    return response.data;
  } catch (error) {
    console.error('获取推荐模型列表API调用失败:', error);
    throw error;
  }
};



/**
 * 获取批量翻译状态
 * @param {string} batchId - 批量任务ID
 * @returns {Promise<Object>} 批量翻译状态
 */
export const getBatchTranslationStatus = async (batchId) => {
  try {
    const response = await apiClient.get(`${TRANSLATION_ENDPOINTS.GET_BATCH_TRANSLATION_STATUS}/${batchId}`);
    return response.data;
  } catch (error) {
    console.error('获取批量翻译状态API调用失败:', error);
    throw error;
  }
};

/**
 * 取消批量翻译任务
 * @param {string} batchId - 批量任务ID
 * @returns {Promise<Object>} 取消结果
 */
export const cancelBatchTranslation = async (batchId) => {
  try {
    const response = await apiClient.post(`${TRANSLATION_ENDPOINTS.CANCEL_BATCH_TRANSLATION}/${batchId}`);
    return response.data;
  } catch (error) {
    console.error('取消批量翻译API调用失败:', error);
    throw error;
  }
};


export default {
  translateText,
  getSupportedLanguages,
  getTranslationHistory,
  saveTranslationHistory,
  getTranslationAgents,
  getTranslationModels,
  setDefaultTranslationModel,
  getDefaultTranslationModel,
  clearTranslationHistory,
  rateTranslation,
  submitTranslationFeedback,
  getTranslationStats,
  getTranslationMemory,
  saveTranslationMemory,
  searchTranslationMemory,
  getTerminology,
  saveTerminology,
  searchTerminology,
  getKnowledgeBases,
  searchKnowledgeBase,
  getMemoryContext,
};

/**
 * 翻译文档
 * @param {FormData} formData - 包含文件和其他参数的FormData对象
 * @returns {Promise<Object>} 翻译结果
 */
export const translateDocument = async (formData) => {
  try {
    const response = await apiClient.post(TRANSLATION_ENDPOINTS.TRANSLATE_DOCUMENT, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('文档翻译API调用失败:', error);
    throw error;
  }
};

/**
 * 获取支持的文档格式
 * @returns {Promise<Object>} 支持的文档格式列表
 */
export const getSupportedDocumentFormats = async () => {
  try {
    const response = await apiClient.get(TRANSLATION_ENDPOINTS.GET_SUPPORTED_DOCUMENT_FORMATS);
    return response.data;
  } catch (error) {
    console.error('获取支持的文档格式API调用失败:', error);
    throw error;
  }
};

