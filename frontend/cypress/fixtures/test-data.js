// 默认模型测试数据
export const defaultModels = {
  global: {
    id: 1,
    scope: 'global',
    scene: null,
    model_id: 1,
    model_name: 'GPT-3.5',
    priority: 1,
    fallback_model_id: 2,
    fallback_model_name: 'GPT-4',
    is_active: true,
    created_at: '2024-01-15T08:30:00Z',
    updated_at: '2024-02-20T14:15:00Z'
  },
  sceneChat: {
    id: 2,
    scope: 'scene',
    scene: 'chat',
    model_id: 3,
    model_name: 'Claude-3',
    priority: 1,
    fallback_model_id: 1,
    fallback_model_name: 'GPT-3.5',
    is_active: true,
    created_at: '2024-01-18T10:45:00Z',
    updated_at: '2024-02-22T16:30:00Z'
  },
  sceneWriting: {
    id: 3,
    scope: 'scene',
    scene: 'writing',
    model_id: 4,
    model_name: 'GPT-4',
    priority: 2,
    fallback_model_id: 1,
    fallback_model_name: 'GPT-3.5',
    is_active: true,
    created_at: '2024-01-20T13:20:00Z',
    updated_at: '2024-02-25T11:10:00Z'
  }
};

// 模型测试数据
export const models = [
  {
    id: 1,
    model_id: 'gpt-3.5-turbo',
    model_name: 'GPT-3.5',
    description: 'OpenAI GPT-3.5 Turbo模型',
    supplier_id: 1,
    supplier_name: 'OpenAI',
    context_window: 16384,
    max_tokens: 4096,
    is_default: false,
    is_active: true,
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-02-15T15:30:00Z'
  },
  {
    id: 2,
    model_id: 'gpt-4',
    model_name: 'GPT-4',
    description: 'OpenAI GPT-4模型',
    supplier_id: 1,
    supplier_name: 'OpenAI',
    context_window: 32768,
    max_tokens: 8192,
    is_default: false,
    is_active: true,
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-02-15T15:30:00Z'
  },
  {
    id: 3,
    model_id: 'claude-3-sonnet',
    model_name: 'Claude-3',
    description: 'Anthropic Claude-3 Sonnet模型',
    supplier_id: 2,
    supplier_name: 'Anthropic',
    context_window: 200000,
    max_tokens: 4096,
    is_default: false,
    is_active: true,
    created_at: '2024-01-12T10:15:00Z',
    updated_at: '2024-02-18T14:20:00Z'
  },
  {
    id: 4,
    model_id: 'gpt-4-turbo',
    model_name: 'GPT-4 Turbo',
    description: 'OpenAI GPT-4 Turbo模型',
    supplier_id: 1,
    supplier_name: 'OpenAI',
    context_window: 128000,
    max_tokens: 4096,
    is_default: false,
    is_active: true,
    created_at: '2024-01-15T11:30:00Z',
    updated_at: '2024-02-20T16:45:00Z'
  }
];

// 用户测试数据
export const users = {
  admin: {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    is_active: true,
    is_superuser: true,
    is_verified: true,
    created_at: '2024-01-05T08:00:00Z',
    updated_at: '2024-02-10T14:20:00Z'
  },
  user: {
    id: 2,
    username: 'user',
    email: 'user@example.com',
    is_active: true,
    is_superuser: false,
    is_verified: true,
    created_at: '2024-01-10T10:30:00Z',
    updated_at: '2024-02-15T12:45:00Z'
  }
};

// 权限测试数据
export const permissions = [
  {
    id: 1,
    name: 'view_default_models',
    description: '查看默认模型'
  },
  {
    id: 2,
    name: 'edit_default_models',
    description: '编辑默认模型'
  },
  {
    id: 3,
    name: 'delete_default_models',
    description: '删除默认模型'
  },
  {
    id: 4,
    name: 'manage_global_defaults',
    description: '管理全局默认模型'
  },
  {
    id: 5,
    name: 'manage_scene_defaults',
    description: '管理场景默认模型'
  }
];

// API响应模板
export const apiResponses = {
  success: {
    status: 200,
    body: {
      success: true,
      message: '操作成功'
    }
  },
  error: {
    status: 400,
    body: {
      detail: '请求参数错误'
    }
  },
  unauthorized: {
    status: 401,
    body: {
      detail: '未授权访问'
    }
  },
  forbidden: {
    status: 403,
    body: {
      detail: '权限不足'
    }
  },
  notFound: {
    status: 404,
    body: {
      detail: '资源不存在'
    }
  },
  serverError: {
    status: 500,
    body: {
      detail: '服务器内部错误'
    }
  }
};

// 通知测试数据
export const notifications = {
  defaultModelUpdated: {
    title: '默认模型已更新',
    message: '全局默认模型已成功更新为 GPT-4',
    type: 'success'
  },
  defaultModelDeleted: {
    title: '默认模型已删除',
    message: '场景默认模型已成功删除',
    type: 'info'
  },
  error: {
    title: '操作失败',
    message: '无法设置默认模型，请稍后重试',
    type: 'error'
  }
};

// 桌面应用测试数据
export const desktopApp = {
  version: '1.0.0',
  updateAvailable: {
    hasUpdate: true,
    version: '1.2.3',
    downloadUrl: 'https://example.com/update/download',
    releaseNotes: '新功能和错误修复'
  },
  offlineMode: {
    isOnline: false,
    message: '当前处于离线模式'
  },
  syncStatus: {
    inProgress: '正在同步...',
    completed: '同步完成',
    failed: '同步失败'
  }
};

// 场景测试数据
export const scenes = [
  'chat',
  'writing',
  'analysis',
  'translation',
  'code_generation',
  'summarization'
];

// 供应商测试数据
export const suppliers = [
  {
    id: 1,
    name: 'OpenAI',
    display_name: 'OpenAI',
    description: 'OpenAI是一家专注于人工智能研究的公司',
    is_active: true,
    website: 'https://openai.com',
    logo: '/images/suppliers/openai-logo.png'
  },
  {
    id: 2,
    name: 'Anthropic',
    display_name: 'Anthropic',
    description: 'Anthropic是一家专注于AI安全的研究公司',
    is_active: true,
    website: 'https://anthropic.com',
    logo: '/images/suppliers/anthropic-logo.png'
  },
  {
    id: 3,
    name: 'Google',
    display_name: 'Google AI',
    description: 'Google的人工智能研究部门',
    is_active: true,
    website: 'https://ai.google',
    logo: '/images/suppliers/google-logo.png'
  }
];