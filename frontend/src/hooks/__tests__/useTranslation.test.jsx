import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTranslateText, useSupportedLanguages, useTranslationHistory, useSaveTranslationHistory, useClearTranslationHistory } from '../useTranslation';
import translationService from '../../services/translationService';
import { showSuccess, showError } from '../../components/UI';

// Mock the translation service and UI components
jest.mock('../../services/translationService');
jest.mock('../../components/UI', () => ({
  showSuccess: jest.fn(),
  showError: jest.fn()
}));

describe('useTranslation Hooks', () => {
  let queryClient;
  let wrapper;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    jest.clearAllMocks();
  });

  describe('useTranslateText', () => {
    it('should translate text successfully', async () => {
      const mockTranslationData = {
        text: 'Hello world',
        source_language: 'en',
        target_language: 'zh'
      };

      const mockResult = {
        translated_text: '你好世界',
        source_language: 'en',
        target_language: 'zh'
      };

      translationService.translateText.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useTranslateText(), { wrapper });

      let mutationResult;
      await act(async () => {
        mutationResult = await result.current.mutateAsync(mockTranslationData);
      });

      expect(translationService.translateText).toHaveBeenCalledWith(mockTranslationData);
      expect(mutationResult).toEqual(mockResult);
      expect(showSuccess).toHaveBeenCalledWith('翻译成功');
    });

    it('should handle translation errors', async () => {
      const mockError = new Error('Translation failed');
      translationService.translateText.mockRejectedValue(mockError);

      const { result } = renderHook(() => useTranslateText(), { wrapper });

      await act(async () => {
        try {
          await result.current.mutateAsync({
            text: 'Hello',
            source_language: 'en',
            target_language: 'zh'
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(showError).toHaveBeenCalledWith('翻译失败，请稍后重试');
    });

    it('should handle API error with custom message', async () => {
      const mockError = {
        response: {
          data: {
            message: 'API rate limit exceeded'
          }
        }
      };

      translationService.translateText.mockRejectedValue(mockError);

      const { result } = renderHook(() => useTranslateText(), { wrapper });

      await act(async () => {
        try {
          await result.current.mutateAsync({
            text: 'Hello',
            source_language: 'en',
            target_language: 'zh'
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(showError).toHaveBeenCalledWith('API rate limit exceeded');
    });
  });

  describe('useSupportedLanguages', () => {
    it('should fetch supported languages successfully', async () => {
      const mockLanguages = {
        languages: [
          { code: 'en', name: 'English' },
          { code: 'zh', name: 'Chinese' },
          { code: 'ja', name: 'Japanese' }
        ]
      };

      translationService.getSupportedLanguages.mockResolvedValue(mockLanguages);

      const { result } = renderHook(() => useSupportedLanguages(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockLanguages);
      expect(translationService.getSupportedLanguages).toHaveBeenCalled();
    });

    it('should handle language fetch errors', async () => {
      const mockError = new Error('Failed to fetch languages');
      translationService.getSupportedLanguages.mockRejectedValue(mockError);

      const { result } = renderHook(() => useSupportedLanguages(), { wrapper });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('useTranslationHistory', () => {
    it('should fetch translation history successfully', async () => {
      const mockHistory = {
        history: [
          {
            id: 1,
            source_text: 'Hello',
            translated_text: '你好',
            source_language: 'en',
            target_language: 'zh'
          }
        ]
      };

      translationService.getTranslationHistory.mockResolvedValue(mockHistory);

      const { result } = renderHook(() => useTranslationHistory(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockHistory);
      expect(translationService.getTranslationHistory).toHaveBeenCalledWith({});
    });

    it('should fetch translation history with parameters', async () => {
      const params = { limit: 10, offset: 0 };
      const mockHistory = {
        history: []
      };

      translationService.getTranslationHistory.mockResolvedValue(mockHistory);

      const { result } = renderHook(() => useTranslationHistory(params), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(translationService.getTranslationHistory).toHaveBeenCalledWith(params);
    });
  });

  describe('useSaveTranslationHistory', () => {
    it('should save translation history successfully', async () => {
      const mockHistoryData = {
        source_text: 'Hello',
        translated_text: '你好',
        source_language: 'en',
        target_language: 'zh'
      };

      const mockResult = { success: true, id: 123 };
      translationService.saveTranslationHistory.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useSaveTranslationHistory(), { wrapper });

      let mutationResult;
      await act(async () => {
        mutationResult = await result.current.mutateAsync(mockHistoryData);
      });

      expect(translationService.saveTranslationHistory).toHaveBeenCalledWith(mockHistoryData);
      expect(mutationResult).toEqual(mockResult);
      expect(showSuccess).toHaveBeenCalledWith('翻译历史已保存');
    });
  });

  describe('useClearTranslationHistory', () => {
    it('should clear translation history successfully', async () => {
      const mockResult = { success: true, message: 'History cleared' };
      translationService.clearTranslationHistory.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useClearTranslationHistory(), { wrapper });

      let mutationResult;
      await act(async () => {
        mutationResult = await result.current.mutateAsync();
      });

      expect(translationService.clearTranslationHistory).toHaveBeenCalled();
      expect(mutationResult).toEqual(mockResult);
      expect(showSuccess).toHaveBeenCalledWith('翻译历史已清空');
    });
  });
});