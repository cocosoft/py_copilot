import { translateText, getSupportedLanguages, getTranslationHistory, saveTranslationHistory, clearTranslationHistory } from '../translationService';
import apiClient from '../apiClient';

// Mock the API client
jest.mock('../apiClient');

describe('translationService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('translateText', () => {
    it('should translate text successfully', async () => {
      const mockParams = {
        text: 'Hello world',
        source_language: 'en',
        target_language: 'zh',
        agent_id: 'agent-123',
        model_id: 'model-456'
      };

      const mockResponse = {
        data: {
          translated_text: '你好世界',
          source_language: 'en',
          target_language: 'zh',
          translation_time: 1.5
        }
      };

      apiClient.post.mockResolvedValue(mockResponse);

      const result = await translateText(mockParams);

      expect(apiClient.post).toHaveBeenCalledWith('/tasks/process', {
        task_type: 'translate',
        ...mockParams
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle translation errors', async () => {
      const mockParams = {
        text: 'Hello world',
        source_language: 'en',
        target_language: 'zh'
      };

      const mockError = new Error('API Error');
      apiClient.post.mockRejectedValue(mockError);

      await expect(translateText(mockParams)).rejects.toThrow('API Error');
      expect(apiClient.post).toHaveBeenCalledWith('/tasks/process', {
        task_type: 'translate',
        ...mockParams
      });
    });

    it('should handle minimal required parameters', async () => {
      const mockParams = {
        text: 'Test',
        source_language: 'en',
        target_language: 'zh'
      };

      const mockResponse = {
        data: {
          translated_text: '测试',
          source_language: 'en',
          target_language: 'zh'
        }
      };

      apiClient.post.mockResolvedValue(mockResponse);

      const result = await translateText(mockParams);

      expect(apiClient.post).toHaveBeenCalledWith('/tasks/process', {
        task_type: 'translate',
        ...mockParams
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getSupportedLanguages', () => {
    it('should fetch supported languages successfully', async () => {
      const mockResponse = {
        data: {
          languages: [
            { code: 'en', name: 'English' },
            { code: 'zh', name: 'Chinese' },
            { code: 'ja', name: 'Japanese' }
          ]
        }
      };

      apiClient.get.mockResolvedValue(mockResponse);

      const result = await getSupportedLanguages();

      expect(apiClient.get).toHaveBeenCalledWith('/languages');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle language fetch errors', async () => {
      const mockError = new Error('Language API Error');
      apiClient.get.mockRejectedValue(mockError);

      await expect(getSupportedLanguages()).rejects.toThrow('Language API Error');
      expect(apiClient.get).toHaveBeenCalledWith('/languages');
    });
  });

  describe('getTranslationHistory', () => {
    it('should fetch translation history successfully', async () => {
      const mockResponse = {
        data: {
          history: [
            {
              id: 1,
              source_text: 'Hello',
              translated_text: '你好',
              source_language: 'en',
              target_language: 'zh',
              created_at: '2024-01-01T00:00:00Z'
            }
          ]
        }
      };

      apiClient.get.mockResolvedValue(mockResponse);

      const result = await getTranslationHistory();

      expect(apiClient.get).toHaveBeenCalledWith('/translation-history');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle history fetch errors', async () => {
      const mockError = new Error('History API Error');
      apiClient.get.mockRejectedValue(mockError);

      await expect(getTranslationHistory()).rejects.toThrow('History API Error');
      expect(apiClient.get).toHaveBeenCalledWith('/translation-history');
    });
  });

  describe('saveTranslationHistory', () => {
    it('should save translation history successfully', async () => {
      const historyData = {
        source_text: 'Hello',
        translated_text: '你好',
        source_language: 'en',
        target_language: 'zh'
      };

      const mockResponse = {
        data: { success: true, id: 123 }
      };

      apiClient.post.mockResolvedValue(mockResponse);

      const result = await saveTranslationHistory(historyData);

      expect(apiClient.post).toHaveBeenCalledWith('/translation-history', historyData);
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('clearTranslationHistory', () => {
    it('should clear translation history successfully', async () => {
      const mockResponse = {
        data: { success: true, message: 'History cleared' }
      };

      apiClient.delete.mockResolvedValue(mockResponse);

      const result = await clearTranslationHistory();

      expect(apiClient.delete).toHaveBeenCalledWith('/translation-history/clear');
      expect(result).toEqual(mockResponse.data);
    });
  });
});