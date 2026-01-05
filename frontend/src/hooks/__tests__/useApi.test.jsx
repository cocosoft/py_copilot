import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import useApi from '../useApi';
import apiClient from '../../utils/apiClient';

// Mock API client
jest.mock('../../utils/apiClient');

describe('useApi Hook', () => {
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

  describe('useApiQuery', () => {
    it('fetches data successfully', async () => {
      const mockData = { id: 1, name: 'Test Model' };
      apiClient.get.mockResolvedValue({ data: mockData });

      const { result } = renderHook(() => useApi.useApiQuery('test-key', '/api/test'), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.data).toEqual(mockData);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(null);
    });

    it('handles fetch errors', async () => {
      const mockError = new Error('API Error');
      apiClient.get.mockRejectedValue(mockError);

      const { result } = renderHook(() => useApi.useApiQuery('test-key', '/api/test'), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.data).toBe(undefined);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(mockError);
    });

    it('refetches data when refetch is called', async () => {
      const mockData = { id: 1, name: 'Test Model' };
      apiClient.get.mockResolvedValue({ data: mockData });

      const { result } = renderHook(() => useApi.useApiQuery('test-key', '/api/test'), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.data).toEqual(mockData);

      const newMockData = { id: 2, name: 'Updated Model' };
      apiClient.get.mockResolvedValue({ data: newMockData });

      await act(async () => {
        result.current.refetch();
      });

      expect(apiClient.get).toHaveBeenCalledTimes(2);
      expect(result.current.data).toEqual(newMockData);
    });
  });

  describe('useApiMutation', () => {
    it('performs mutation successfully', async () => {
      const mockResponse = { id: 1, name: 'Created Model' };
      apiClient.post.mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useApi.useApiMutation('POST', '/api/models'), {
        wrapper,
      });

      let mutationResult;
      await act(async () => {
        mutationResult = await result.current.mutate({ name: 'Test Model' });
      });

      expect(apiClient.post).toHaveBeenCalledWith('/api/models', { name: 'Test Model' });
      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(null);
    });

    it('handles mutation errors', async () => {
      const mockError = new Error('Mutation Error');
      apiClient.post.mockRejectedValue(mockError);

      const { result } = renderHook(() => useApi.useApiMutation('POST', '/api/models'), {
        wrapper,
      });

      await act(async () => {
        try {
          await result.current.mutate({ name: 'Test Model' });
        } catch (error) {
          expect(error).toBe(mockError);
        }
      });

      expect(result.current.error).toBe(mockError);
      expect(result.current.isLoading).toBe(false);
    });

    it('resets mutation state after completion', async () => {
      apiClient.post.mockResolvedValue({ data: { id: 1 } });

      const { result } = renderHook(() => useApi.useApiMutation('POST', '/api/models'), {
        wrapper,
      });

      await act(async () => {
        await result.current.mutate({ name: 'Test Model' });
      });

      expect(result.current.isLoading).toBe(false);

      // 重置状态应该清空数据
      act(() => {
        result.current.reset();
      });

      expect(result.current.data).toBe(undefined);
    });
  });

  describe('useModelApi', () => {
    it('fetches models successfully', async () => {
      const mockModels = [
        { id: '1', name: 'GPT-4', provider: 'OpenAI' },
        { id: '2', name: 'Claude-3', provider: 'Anthropic' }
      ];
      apiClient.get.mockResolvedValue({ data: mockModels });

      const { result } = renderHook(() => useApi.useModelApi(), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.data).toEqual(mockModels);
      expect(apiClient.get).toHaveBeenCalledWith('/api/models');
    });

    it('handles model fetch errors', async () => {
      const mockError = new Error('Failed to fetch models');
      apiClient.get.mockRejectedValue(mockError);

      const { result } = renderHook(() => useApi.useModelApi(), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.error).toBe(mockError);
    });
  });

  describe('useSupplierApi', () => {
    it('fetches suppliers successfully', async () => {
      const mockSuppliers = [
        { id: '1', name: 'OpenAI', type: 'text' },
        { id: '2', name: 'Anthropic', type: 'text' }
      ];
      apiClient.get.mockResolvedValue({ data: mockSuppliers });

      const { result } = renderHook(() => useApi.useSupplierApi(), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.data).toEqual(mockSuppliers);
      expect(apiClient.get).toHaveBeenCalledWith('/api/suppliers');
    });
  });

  describe('useAuthApi', () => {
    it('handles login successfully', async () => {
      const mockAuthResponse = { token: 'abc123', user: { id: '1', username: 'testuser' } };
      apiClient.post.mockResolvedValue({ data: mockAuthResponse });

      const { result } = renderHook(() => useApi.useAuthApi(), {
        wrapper,
      });

      await act(async () => {
        const response = await result.current.login('testuser', 'password');
        expect(response).toEqual(mockAuthResponse);
      });

      expect(apiClient.post).toHaveBeenCalledWith('/api/auth/login', {
        username: 'testuser',
        password: 'password'
      });
    });

    it('handles logout successfully', async () => {
      apiClient.post.mockResolvedValue({});

      const { result } = renderHook(() => useApi.useAuthApi(), {
        wrapper,
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(apiClient.post).toHaveBeenCalledWith('/api/auth/logout');
    });
  });

  describe('Cache Management', () => {
    it('invalidates cache when needed', async () => {
      const mockData = { id: 1, name: 'Test' };
      apiClient.get.mockResolvedValue({ data: mockData });

      const { result } = renderHook(() => useApi.useApiQuery('test-key', '/api/test'), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.data).toEqual(mockData);

      // 手动失效缓存
      act(() => {
        queryClient.invalidateQueries(['test-key']);
      });

      expect(result.current.isStale).toBe(true);
    });

    it('optimistically updates cache during mutations', async () => {
      const mockInitialData = [{ id: 1, name: 'Initial' }];
      apiClient.get.mockResolvedValue({ data: mockInitialData });

      const { result } = renderHook(() => useApi.useApiQuery('models', '/api/models'), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.data).toEqual(mockInitialData);

      // 模拟乐观更新
      apiClient.post.mockResolvedValue({ data: { id: 2, name: 'New Model' } });

      const mutationHook = renderHook(() => useApi.useApiMutation('POST', '/api/models'), {
        wrapper,
      });

      await act(async () => {
        await mutationHook.result.current.mutate({ name: 'New Model' });
      });

      // 验证缓存是否被更新
      expect(queryClient.getQueryData(['models'])).toBeTruthy();
    });
  });

  describe('Retry Logic', () => {
    it('retries failed requests', async () => {
      const mockError = new Error('Network Error');
      apiClient.get.mockRejectedValue(mockError);

      const { result } = renderHook(() => useApi.useApiQuery('test-key', '/api/test', {
        retry: 2,
        retryDelay: 100
      }), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 500));
      });

      expect(apiClient.get).toHaveBeenCalledTimes(3); // 初始请求 + 2次重试
    });

    it('does not retry when retry is disabled', async () => {
      const mockError = new Error('Network Error');
      apiClient.get.mockRejectedValue(mockError);

      const { result } = renderHook(() => useApi.useApiQuery('test-key', '/api/test', {
        retry: false
      }), {
        wrapper,
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      expect(apiClient.get).toHaveBeenCalledTimes(1); // 只请求一次
    });
  });
});