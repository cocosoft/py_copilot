/**
 * 文件管理API模块
 * 
 * 提供统一的文件上传、下载、管理接口
 */

import { API_BASE_URL, request } from '../apiUtils';

/**
 * 文件分类枚举
 */
export const FileCategory = {
  CONVERSATION_ATTACHMENT: 'conversation_attachment',
  VOICE_MESSAGE: 'voice_message',
  KNOWLEDGE_DOCUMENT: 'knowledge_document',
  KNOWLEDGE_EXTRACT: 'knowledge_extract',
  TRANSLATION_INPUT: 'translation_input',
  TRANSLATION_OUTPUT: 'translation_output',
  USER_AVATAR: 'user_avatar',
  USER_EXPORT: 'user_export',
  TEMP_FILE: 'temp_file',
  MODEL_LOGO: 'model_logo',
  SUPPLIER_LOGO: 'supplier_logo',
  IMAGE_ANALYSIS: 'image_analysis'
};

/**
 * 文件状态枚举
 */
export const FileStatus = {
  PENDING: 'pending',
  UPLOADING: 'uploading',
  COMPLETED: 'completed',
  FAILED: 'failed',
  PROCESSING: 'processing',
  EXPIRED: 'expired'
};

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
};

/**
 * 获取文件扩展名
 * @param {string} filename - 文件名
 * @returns {string} 扩展名
 */
export const getFileExtension = (filename) => {
  if (!filename) return '';
  const parts = filename.split('.');
  return parts.length > 1 ? `.${parts.pop().toLowerCase()}` : '';
};

/**
 * 检查文件类型是否为图片
 * @param {string} filename - 文件名
 * @returns {boolean} 是否为图片
 */
export const isImageFile = (filename) => {
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'];
  return imageExtensions.includes(getFileExtension(filename));
};

/**
 * 检查文件类型是否为文档
 * @param {string} filename - 文件名
 * @returns {boolean} 是否为文档
 */
export const isDocumentFile = (filename) => {
  const docExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md'];
  return docExtensions.includes(getFileExtension(filename));
};

/**
 * 获取文件图标
 * @param {string} filename - 文件名
 * @returns {string} 图标类名
 */
export const getFileIcon = (filename) => {
  const ext = getFileExtension(filename);
  const iconMap = {
    '.pdf': '📄',
    '.doc': '📝',
    '.docx': '📝',
    '.xls': '📊',
    '.xlsx': '📊',
    '.ppt': '📽️',
    '.pptx': '📽️',
    '.txt': '📃',
    '.md': '📃',
    '.jpg': '🖼️',
    '.jpeg': '🖼️',
    '.png': '🖼️',
    '.gif': '🖼️',
    '.mp3': '🎵',
    '.wav': '🎵',
    '.mp4': '🎬',
    '.avi': '🎬',
    '.zip': '📦',
    '.rar': '📦',
    '.7z': '📦'
  };
  return iconMap[ext] || '📎';
};

/**
 * 文件API对象
 */
export const fileApi = {
  /**
   * 上传文件
   * @param {File} file - 文件对象
   * @param {string} category - 文件分类
   * @param {Object} options - 可选参数
   * @param {number} options.conversationId - 对话ID
   * @param {number} options.knowledgeBaseId - 知识库ID
   * @param {number} options.relatedId - 通用关联ID
   * @param {Function} options.onProgress - 进度回调
   * @returns {Promise<Object>} 上传结果
   */
  upload: async (file, category, options = {}) => {
    const { conversationId, knowledgeBaseId, relatedId, onProgress } = options;
    
    const formData = new FormData();
    formData.append('file', file);
    
    // 构建查询参数
    const params = new URLSearchParams();
    params.append('category', category);
    if (conversationId) params.append('conversation_id', conversationId);
    if (knowledgeBaseId) params.append('knowledge_base_id', knowledgeBaseId);
    if (relatedId) params.append('related_id', relatedId);
    
    const url = `${API_BASE_URL}/files/upload?${params.toString()}`;
    
    // 使用XMLHttpRequest以支持进度监控
    if (onProgress) {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            onProgress(progress);
          }
        });
        
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error(`上传失败: ${xhr.statusText}`));
          }
        });
        
        xhr.addEventListener('error', () => {
          reject(new Error('上传失败'));
        });
        
        xhr.open('POST', url);
        xhr.send(formData);
      });
    }
    
    // 普通fetch请求
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '上传失败');
    }
    
    return response.json();
  },

  /**
   * 批量上传文件
   * @param {File[]} files - 文件列表
   * @param {string} category - 文件分类
   * @param {Object} options - 可选参数
   * @returns {Promise<Object[]>} 上传结果列表
   */
  uploadBatch: async (files, category, options = {}) => {
    const results = [];
    const errors = [];
    
    for (const file of files) {
      try {
        const result = await fileApi.upload(file, category, options);
        results.push(result);
      } catch (error) {
        errors.push({ file: file.name, error: error.message });
      }
    }
    
    return {
      success: results.length,
      failed: errors.length,
      results,
      errors
    };
  },

  /**
   * 下载文件
   * @param {string} fileId - 文件ID
   * @param {boolean} asAttachment - 是否作为附件下载
   * @returns {Promise<Blob>} 文件Blob
   */
  download: async (fileId, asAttachment = false) => {
    const params = new URLSearchParams();
    if (asAttachment) params.append('download', 'true');
    
    const url = `${API_BASE_URL}/files/${fileId}?${params.toString()}`;
    
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '下载失败');
    }
    
    return response.blob();
  },

  /**
   * 获取文件下载URL
   * @param {string} fileId - 文件ID
   * @param {boolean} asAttachment - 是否作为附件
   * @returns {string} 下载URL
   */
  getDownloadUrl: (fileId, asAttachment = false) => {
    const params = new URLSearchParams();
    if (asAttachment) params.append('download', 'true');
    return `${API_BASE_URL}/files/${fileId}?${params.toString()}`;
  },

  /**
   * 获取文件信息
   * @param {string} fileId - 文件ID
   * @returns {Promise<Object>} 文件信息
   */
  getInfo: async (fileId) => {
    const response = await fetch(`${API_BASE_URL}/files/${fileId}/info`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '获取文件信息失败');
    }
    
    return response.json();
  },

  /**
   * 获取文件列表
   * @param {Object} filters - 筛选条件
   * @param {string} filters.category - 文件分类
   * @param {number} filters.conversationId - 对话ID
   * @param {number} filters.knowledgeBaseId - 知识库ID
   * @param {string} filters.status - 文件状态
   * @param {number} filters.limit - 每页数量
   * @param {number} filters.offset - 偏移量
   * @returns {Promise<Object>} 文件列表
   */
  getList: async (filters = {}) => {
    const {
      category,
      conversationId,
      knowledgeBaseId,
      status,
      limit = 100,
      offset = 0
    } = filters;
    
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (conversationId) params.append('conversation_id', conversationId);
    if (knowledgeBaseId) params.append('knowledge_base_id', knowledgeBaseId);
    if (status) params.append('status', status);
    params.append('limit', limit);
    params.append('offset', offset);
    
    const response = await fetch(`${API_BASE_URL}/files/?${params.toString()}`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '获取文件列表失败');
    }
    
    return response.json();
  },

  /**
   * 删除文件
   * @param {string} fileId - 文件ID
   * @returns {Promise<Object>} 删除结果
   */
  delete: async (fileId) => {
    const response = await fetch(`${API_BASE_URL}/files/${fileId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '删除失败');
    }
    
    return response.json();
  },

  /**
   * 批量删除文件
   * @param {string[]} fileIds - 文件ID列表
   * @returns {Promise<Object>} 删除结果
   */
  deleteBatch: async (fileIds) => {
    const results = [];
    const errors = [];
    
    for (const fileId of fileIds) {
      try {
        const result = await fileApi.delete(fileId);
        results.push(result);
      } catch (error) {
        errors.push({ fileId, error: error.message });
      }
    }
    
    return {
      success: results.length,
      failed: errors.length,
      results,
      errors
    };
  },

  /**
   * 获取存储使用情况
   * @returns {Promise<Object>} 存储使用情况
   */
  getStorageUsage: async () => {
    const response = await fetch(`${API_BASE_URL}/files/storage/usage`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '获取存储使用情况失败');
    }
    
    return response.json();
  },

  /**
   * 清理临时文件
   * @param {number} maxAgeHours - 最大保留时间（小时）
   * @returns {Promise<Object>} 清理结果
   */
  cleanupTemp: async (maxAgeHours = 24) => {
    const params = new URLSearchParams();
    params.append('max_age_hours', maxAgeHours);
    
    const response = await fetch(`${API_BASE_URL}/files/cleanup/temp?${params.toString()}`, {
      method: 'POST',
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '清理临时文件失败');
    }
    
    return response.json();
  },

  /**
   * 兼容旧版上传接口
   * @param {File} file - 文件对象
   * @param {number} conversationId - 对话ID
   * @returns {Promise<Object>} 上传结果
   */
  uploadLegacy: async (file, conversationId) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const params = new URLSearchParams();
    if (conversationId) params.append('conversation_id', conversationId);
    
    const url = `${API_BASE_URL}/files/upload/legacy?${params.toString()}`;
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '上传失败');
    }
    
    return response.json();
  }
};

export default fileApi;
