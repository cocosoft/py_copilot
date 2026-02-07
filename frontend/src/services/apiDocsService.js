import apiClient from './apiClient';

export const apiDocsService = {
  
  getApiList: async (params = {}) => {
    const response = await apiClient.get('/api/v1/api-docs/list', { params });
    return response.data;
  },

  searchApi: async (keyword) => {
    const response = await apiClient.get('/api/v1/api-docs/search', {
      params: { keyword }
    });
    return response.data;
  },

  getApiStats: async () => {
    const response = await apiClient.get('/api/v1/api-docs/stats');
    return response.data;
  },

  testApi: async (path, method, data) => {
    const config = {
      method: 'POST',
      url: '/api/v1/api-docs/test',
      data: {
        path: path.startsWith('/api') ? path : `/api${path}`,
        method: method,
        data: data
      }
    };
    const response = await apiClient.request(config);
    return response.data;
  },

  addFavorite: async (apiData) => {
    const response = await apiClient.post('/api/v1/api-docs/favorites', apiData);
    return response.data;
  },

  removeFavorite: async (apiPath, apiMethod, userId = null) => {
    const params = {
      api_path: apiPath,
      api_method: apiMethod
    };
    if (userId) {
      params.user_id = userId;
    }
    const response = await apiClient.delete('/api/v1/api-docs/favorites', { params });
    return response.data;
  },

  getFavorites: async (userId = null) => {
    const params = {};
    if (userId) {
      params.user_id = userId;
    }
    const response = await apiClient.get('/api/v1/api-docs/favorites', { params });
    return response.data;
  },

  checkFavorite: async (apiPath, apiMethod, userId = null) => {
    const params = {
      api_path: apiPath,
      api_method: apiMethod
    };
    if (userId) {
      params.user_id = userId;
    }
    const response = await apiClient.get('/api/v1/api-docs/favorites/check', { params });
    return response.data;
  }
};
