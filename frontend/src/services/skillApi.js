const API_BASE = '/api/v1/skills';

async function fetchApi(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'API request failed');
  }

  return response.json();
}

export const skillApi = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.set('status', params.status);
    if (params.tags) query.set('tags', params.tags.join(','));
    if (params.search) query.set('search', params.search);
    if (params.page) query.set('page', params.page.toString());
    if (params.pageSize) query.set('page_size', params.pageSize.toString());
    const queryString = query.toString();
    return fetchApi(queryString ? `?${queryString}` : '');
  },

  get: (skillId) => fetchApi(`/${skillId}`),

  create: (skillData) => fetchApi('', {
    method: 'POST',
    body: JSON.stringify(skillData),
  }),

  update: (skillId, skillData) => fetchApi(`/${skillId}`, {
    method: 'PUT',
    body: JSON.stringify(skillData),
  }),

  delete: (skillId) => fetchApi(`/${skillId}`, {
    method: 'DELETE',
  }),

  enable: (skillId) => fetchApi(`/${skillId}/enable`, {
    method: 'POST',
  }),

  disable: (skillId) => fetchApi(`/${skillId}/disable`, {
    method: 'POST',
  }),

  execute: (skillId, task, params) => fetchApi(`/${skillId}/execute`, {
    method: 'POST',
    body: JSON.stringify({ task, params }),
  }),

  match: (taskDescription) => fetchApi('/match', {
    method: 'POST',
    body: JSON.stringify({ task_description: taskDescription }),
  }),

  activate: (conversationId, skillIds) => fetchApi('/activate', {
    method: 'POST',
    body: JSON.stringify({ conversation_id: conversationId, skill_ids: skillIds }),
  }),

  deactivate: (conversationId, skillIds) => fetchApi('/deactivate', {
    method: 'POST',
    body: JSON.stringify({ conversation_id: conversationId, skill_ids: skillIds }),
  }),

  getContext: (conversationId) => fetchApi(`/context/${conversationId}`),

  getContextForPrompt: (conversationId) => fetchApi(`/context/${conversationId}/prompt`),

  // 版本管理相关API
  getVersions: (skillId) => fetchApi(`/${skillId}/versions`),

  getVersion: (versionId) => fetchApi(`/versions/${versionId}`),

  createVersion: (skillId, versionData) => fetchApi(`/${skillId}/versions`, {
    method: 'POST',
    body: JSON.stringify(versionData),
  }),

  rollbackVersion: (skillId, versionId) => fetchApi(`/${skillId}/versions/${versionId}/rollback`, {
    method: 'POST',
  }),

  compareVersions: (versionId1, versionId2) => fetchApi('/versions/compare', {
    method: 'POST',
    body: JSON.stringify({ version_id_1: versionId1, version_id_2: versionId2 }),
  }),

  // 技能依赖管理API
  getDependencies: (skillId) => fetchApi(`/${skillId}/dependencies`),

  addDependency: (skillId, dependencyData) => fetchApi(`/${skillId}/dependencies`, {
    method: 'POST',
    body: JSON.stringify(dependencyData),
  }),

  removeDependency: (skillId, dependencyId) => fetchApi(`/${skillId}/dependencies/${dependencyId}`, {
    method: 'DELETE',
  }),

  checkDependencyCompatibility: (skillId) => fetchApi(`/${skillId}/dependencies/check`),

  resolveDependencies: (skillId) => fetchApi(`/${skillId}/dependencies/resolve`),

  // 技能执行流程API
  getExecutionFlow: (skillId) => fetchApi(`/${skillId}/execution-flow`),

  updateExecutionFlow: (skillId, flowData) => fetchApi(`/${skillId}/execution-flow`, {
    method: 'PUT',
    body: JSON.stringify(flowData),
  }),

  // 技能Artifacts API
  getArtifacts: (skillId, executionLogId) => fetchApi(`/${skillId}/artifacts/${executionLogId}`),

  downloadArtifact: (skillId, executionLogId, artifactId) => fetchApi(`/${skillId}/artifacts/${executionLogId}/${artifactId}/download`),

  previewArtifact: (skillId, executionLogId, artifactId) => fetchApi(`/${skillId}/artifacts/${executionLogId}/${artifactId}/preview`),
};

export default skillApi;
