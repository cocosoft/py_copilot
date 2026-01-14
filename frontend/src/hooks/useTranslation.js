import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { showSuccess, showError } from '../components/UI';
import { queryKeys } from '../config/queryClient';
import translationService from '../services/translationService';

// Translation hooks
export const useTranslateText = () => {
  return useMutation({
    mutationFn: async (translationData) => {
      const result = await translationService.translateText(translationData);
      return result;
    },
    onSuccess: (data) => {
      showSuccess('翻译成功');
    },
    onError: (error) => {
      const message = error?.response?.data?.message || '翻译失败，请稍后重试';
      showError(message);
    },
  });
};

export const useSupportedLanguages = () => {
  return useQuery({
    queryKey: queryKeys.supportedLanguages,
    queryFn: async () => {
      const result = await translationService.getSupportedLanguages();
      return result;
    },
    staleTime: 24 * 60 * 60 * 1000, // 24小时
    retry: 2,
  });
};

export const useTranslationHistory = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.translationHistory, params],
    queryFn: async () => {
      const result = await translationService.getTranslationHistory(params);
      return result;
    },
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

export const useSaveTranslationHistory = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (historyData) => {
      const result = await translationService.saveTranslationHistory(historyData);
      return result;
    },
    onSuccess: () => {
      // 使翻译历史查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: queryKeys.translationHistory });
    },
    onError: (error) => {
      console.error('保存翻译历史失败:', error);
    },
  });
};

export const useClearTranslationHistory = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const result = await translationService.clearTranslationHistory();
      return result;
    },
    onSuccess: () => {
      // 使翻译历史查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: queryKeys.translationHistory });
      showSuccess('历史记录已清空');
    },
    onError: (error) => {
      console.error('清空翻译历史失败:', error);
      const message = error?.response?.data?.message || '清空历史记录失败，请稍后重试';
      showError(message);
    },
  });
};

export const useTranslationAgents = () => {
  return useQuery({
    queryKey: queryKeys.translationAgents,
    queryFn: async () => {
      const result = await translationService.getTranslationAgents();
      return result;
    },
    staleTime: 10 * 60 * 1000, // 10分钟
    retry: 2,
  });
};

export const useTranslationModels = () => {
  return useQuery({
    queryKey: queryKeys.translationModels,
    queryFn: async () => {
      const result = await translationService.getTranslationModels();
      return result;
    },
    staleTime: 10 * 60 * 1000, // 10分钟
    retry: 2,
  });
};

// 质量评估和反馈相关钩子
export const useRateTranslation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (ratingData) => {
      const result = await translationService.rateTranslation(ratingData);
      return result;
    },
    onSuccess: (data, variables) => {
      showSuccess('评分提交成功');
      // 使翻译历史查询失效，触发重新获取（可能包含评分信息）
      queryClient.invalidateQueries({ queryKey: queryKeys.translationHistory });
    },
    onError: (error) => {
      const message = error?.response?.data?.message || '评分提交失败，请稍后重试';
      showError(message);
    },
  });
};

export const useSubmitTranslationFeedback = () => {
  return useMutation({
    mutationFn: async (feedbackData) => {
      const result = await translationService.submitTranslationFeedback(feedbackData);
      return result;
    },
    onSuccess: () => {
      showSuccess('反馈提交成功，感谢您的意见！');
    },
    onError: (error) => {
      const message = error?.response?.data?.message || '反馈提交失败，请稍后重试';
      showError(message);
    },
  });
};

export const useTranslationStats = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.translationStats, params],
    queryFn: async () => {
      const result = await translationService.getTranslationStats(params);
      return result;
    },
    staleTime: 30 * 60 * 1000, // 30分钟
    retry: 2,
  });
};

export const useTranslationQuality = (translationId) => {
  return useQuery({
    queryKey: [...queryKeys.translationQuality, translationId],
    queryFn: async () => {
      // 这里可以调用获取翻译质量评分的API
      // 暂时返回模拟数据
      return {
        average_rating: 4.2,
        total_ratings: 15,
        user_rating: null,
        feedback_count: 3,
      };
    },
    enabled: !!translationId,
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

// 实时翻译（防抖版本）
export const useRealTimeTranslation = () => {
  const translateMutation = useTranslateText();
  
  const translateWithDebounce = (text, sourceLang, targetLang, options = {}) => {
    if (!text || text.trim().length === 0) {
      return Promise.resolve({ translated_text: '' });
    }
    
    return translateMutation.mutateAsync({
      text: text.trim(),
      source_language: sourceLang,
      target_language: targetLang,
      ...options,
    });
  };
  
  return {
    translate: translateWithDebounce,
    isLoading: translateMutation.isLoading,
    isError: translateMutation.isError,
    error: translateMutation.error,
  };
};

// 翻译记忆相关钩子
export const useTranslationMemory = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.translationMemory, params],
    queryFn: async () => {
      const result = await translationService.getTranslationMemory(params);
      return result;
    },
    staleTime: 10 * 60 * 1000, // 10分钟
  });
};

export const useSaveTranslationMemory = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (memoryData) => {
      const result = await translationService.saveTranslationMemory(memoryData);
      return result;
    },
    onSuccess: () => {
      // 使翻译记忆查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: queryKeys.translationMemory });
      showSuccess('翻译记忆已保存');
    },
    onError: (error) => {
      console.error('保存翻译记忆失败:', error);
      const message = error?.response?.data?.message || '保存翻译记忆失败，请稍后重试';
      showError(message);
    },
  });
};

export const useSearchTranslationMemory = () => {
  return useMutation({
    mutationFn: async (searchParams) => {
      const result = await translationService.searchTranslationMemory(searchParams);
      return result;
    },
    onError: (error) => {
      console.error('搜索翻译记忆失败:', error);
    },
  });
};

// 术语库相关钩子
export const useTerminology = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.terminology, params],
    queryFn: async () => {
      const result = await translationService.getTerminology(params);
      return result;
    },
    staleTime: 10 * 60 * 1000, // 10分钟
  });
};

export const useSaveTerminology = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (termData) => {
      const result = await translationService.saveTerminology(termData);
      return result;
    },
    onSuccess: () => {
      // 使术语库查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: queryKeys.terminology });
      showSuccess('术语已保存');
    },
    onError: (error) => {
      console.error('保存术语失败:', error);
      const message = error?.response?.data?.message || '保存术语失败，请稍后重试';
      showError(message);
    },
  });
};

export const useSearchTerminology = () => {
  return useMutation({
    mutationFn: async (searchParams) => {
      const result = await translationService.searchTerminology(searchParams);
      return result;
    },
    onError: (error) => {
      console.error('搜索术语库失败:', error);
    },
  });
};

// 知识库相关钩子
export const useKnowledgeBases = () => {
  return useQuery({
    queryKey: queryKeys.knowledgeBases,
    queryFn: async () => {
      const result = await translationService.getKnowledgeBases();
      return result;
    },
    staleTime: 30 * 60 * 1000, // 30分钟
    retry: 2,
  });
};

export const useSearchKnowledgeBase = () => {
  return useMutation({
    mutationFn: async (searchParams) => {
      const result = await translationService.searchKnowledgeBase(searchParams);
      return result;
    },
    onError: (error) => {
      console.error('搜索知识库失败:', error);
    },
  });
};

// 记忆上下文相关钩子
export const useMemoryContext = () => {
  return useMutation({
    mutationFn: async (params) => {
      const result = await translationService.getMemoryContext(params);
      return result;
    },
    onError: (error) => {
      console.error('获取记忆上下文失败:', error);
    },
  });
};

// 多模型翻译支持相关钩子



/**
 * 获取默认翻译模型
 */
export const useDefaultTranslationModel = () => {
  return useQuery({
    queryKey: queryKeys.defaultTranslationModel,
    queryFn: async () => {
      const result = await translationService.getDefaultTranslationModel();
      return result;
    },
    staleTime: 10 * 60 * 1000, // 10分钟
    retry: 2,
  });
};

/**
 * 设置默认翻译模型
 */
export const useSetDefaultTranslationModel = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (modelId) => {
      const result = await translationService.setDefaultTranslationModel(modelId);
      return result;
    },
    onSuccess: () => {
      // 使默认翻译模型查询失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: queryKeys.defaultTranslationModel });
      showSuccess('默认翻译模型已设置');
    },
    onError: (error) => {
      console.error('设置默认翻译模型失败:', error);
      const message = error?.response?.data?.message || '设置默认翻译模型失败，请稍后重试';
      showError(message);
    },
  });
};

/**
 * 获取模型能力列表
 */
export const useModelCapabilities = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.modelCapabilities, params],
    queryFn: async () => {
      const result = await translationService.getModelCapabilities(params);
      return result;
    },
    staleTime: 10 * 60 * 1000, // 10分钟
    retry: 2,
  });
};

/**
 * 获取推荐模型列表
 */
export const useRecommendedModels = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.recommendedModels, params],
    queryFn: async () => {
      const result = await translationService.getRecommendedModels(params);
      return result;
    },
    staleTime: 5 * 60 * 1000, // 5分钟
    retry: 2,
  });
};



export default {
  useTranslateText,
  useSupportedLanguages,
  useTranslationHistory,
  useSaveTranslationHistory,
  useTranslationAgents,
  useTranslationModels,
  useRealTimeTranslation,
  useRateTranslation,
  useSubmitTranslationFeedback,
  useTranslationStats,
  useTranslationQuality,
  useTranslationMemory,
  useSaveTranslationMemory,
  useSearchTranslationMemory,
  useTerminology,
  useSaveTerminology,
  useSearchTerminology,
  useKnowledgeBases,
  useSearchKnowledgeBase,
  useMemoryContext,
};