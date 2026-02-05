// 简单的tokens计算函数
export const calculateTokens = (text) => {
  if (!text) return 0;
  
  // 移除多余的空白字符
  const cleanedText = text.trim();
  
  // 计算英文单词数（按空格分割）
  const englishWords = cleanedText.match(/\b[a-zA-Z]+\b/g) || [];
  
  // 计算中文汉字数
  const chineseChars = cleanedText.match(/[\u4e00-\u9fa5]/g) || [];
  
  // 计算其他字符数（数字、标点符号等）
  const otherChars = cleanedText.replace(/[a-zA-Z\u4e00-\u9fa5\s]/g, '').length;
  
  // 估算tokens数量：英文单词 * 1.3 + 中文汉字 * 1 + 其他字符
  const estimatedTokens = Math.round(englishWords.length * 1.3 + chineseChars.length + otherChars);
  
  return estimatedTokens;
};

// 错误详情获取函数
export const getErrorDetails = (error) => {
  // 网络错误
  if (error.message.includes('Network Error') || error.message.includes('network')) {
    return {
      type: 'network',
      message: '网络连接失败，请检查您的网络连接。',
      recovery: '请检查网络连接，然后重试。',
      severity: 'high'
    };
  }
  
  // 超时错误
  if (error.message.includes('timeout') || error.message.includes('超时')) {
    return {
      type: 'timeout',
      message: '请求超时，服务器响应时间过长。',
      recovery: '请检查网络连接，或尝试使用更短的问题，稍后再重试。',
      severity: 'medium'
    };
  }
  
  // 404错误
  if (error.response?.status === 404) {
    return {
      type: 'not_found',
      message: '服务暂时不可用，请稍后再试。',
      recovery: '服务器可能正在维护，请稍后再尝试发送消息。',
      severity: 'medium'
    };
  }
  
  // 500+错误
  if (error.response?.status >= 500) {
    return {
      type: 'server_error',
      message: '服务器内部错误，请联系管理员。',
      recovery: '服务器遇到问题，请稍后再试，或联系系统管理员。',
      severity: 'high'
    };
  }
  
  // 401/403错误
  if (error.response?.status === 401 || error.response?.status === 403) {
    return {
      type: 'unauthorized',
      message: '权限不足，请检查您的登录状态。',
      recovery: '请重新登录系统，然后再尝试发送消息。',
      severity: 'high'
    };
  }
  
  // 模型错误
  if (error.message.includes('model') || error.message.includes('模型')) {
    return {
      type: 'model_error',
      message: '模型调用失败，请尝试选择其他模型。',
      recovery: '请尝试选择其他可用的模型，或稍后再试。',
      severity: 'medium'
    };
  }
  
  // API详细错误
  if (error.response?.data?.detail) {
    return {
      type: 'api_error',
      message: error.response.data.detail,
      recovery: '请检查您的请求内容，确保符合要求，然后重试。',
      severity: 'medium'
    };
  }
  
  // 默认错误
  return {
    type: 'unknown',
    message: '抱歉，我暂时无法处理你的请求。请稍后再试。',
    recovery: '请稍后再尝试发送消息，或检查系统状态。',
    severity: 'low'
  };
};

// 消息格式化函数
export const formatTime = (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
};

export const formatDuration = (milliseconds) => {
  if (milliseconds < 1000) {
    return `${Math.round(milliseconds)}ms`;
  }
  return `${(milliseconds / 1000).toFixed(2)}s`;
};

export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

// Token计算工具
export const tokenCalculator = {
  calculate: calculateTokens,
  estimateCost: (tokens, pricePerThousand = 0.02) => {
    return (tokens / 1000) * pricePerThousand;
  }
};