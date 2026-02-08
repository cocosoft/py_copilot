import { request } from '../apiUtils';

export const topicTitleApi = {
  generateTitle: async (data) => {
    try {
      return await request('/v1/topic-title/generate', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('标题生成失败:', error);
      throw error;
    }
  }
};

export default topicTitleApi;
