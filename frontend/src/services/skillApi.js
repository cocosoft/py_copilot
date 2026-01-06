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
    return fetchApi(`/?${query.toString()}`);
  },

  get: (skillId) => fetchApi(`/${skillId}`),

  create: (skillData) => fetchApi('/', {
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

  execute: (skillId, task) => fetchApi(`/${skillId}/execute`, {
    method: 'POST',
    body: JSON.stringify({ task }),
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
};

export default skillApi;
