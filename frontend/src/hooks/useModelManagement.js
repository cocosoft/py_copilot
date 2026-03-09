/**
 * 模型管理相关Hooks
 * 使用React Query管理模型管理相关的数据和状态
 */

import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { modelManagementService, webhookService, configService, lifecycleService, quotaService } from '../services/modelManagementService';

// 模型管理Hooks
export const useModels = (params = {}) => {
  return useQuery({
    queryKey: ['models', params],
    queryFn: () => modelManagementService.getModels(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useModel = (id) => {
  return useQuery({
    queryKey: ['model', id],
    queryFn: () => modelManagementService.getModel(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateModel = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => modelManagementService.createModel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });
};

export const useUpdateModel = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }) => modelManagementService.updateModel(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      queryClient.invalidateQueries({ queryKey: ['model', variables.id] });
    },
  });
};

export const useDeleteModel = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id) => modelManagementService.deleteModel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });
};

export const useBatchDeleteModels = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (ids) => modelManagementService.batchDeleteModels(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });
};

// Webhook管理Hooks
export const useWebhooks = (params = {}) => {
  return useQuery({
    queryKey: ['webhooks', params],
    queryFn: () => webhookService.getWebhooks(params),
    staleTime: 2 * 60 * 1000,
  });
};

export const useWebhook = (id) => {
  return useQuery({
    queryKey: ['webhook', id],
    queryFn: () => webhookService.getWebhook(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
};

export const useCreateWebhook = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => webhookService.createWebhook(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });
};

export const useUpdateWebhook = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }) => webhookService.updateWebhook(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
      queryClient.invalidateQueries({ queryKey: ['webhook', variables.id] });
    },
  });
};

export const useDeleteWebhook = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id) => webhookService.deleteWebhook(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });
};

export const useWebhookDeliveries = (webhookId, params = {}) => {
  return useQuery({
    queryKey: ['webhookDeliveries', webhookId, params],
    queryFn: () => webhookService.getWebhookDeliveries(webhookId, params),
    enabled: !!webhookId,
    staleTime: 1 * 60 * 1000,
  });
};

export const useRetryWebhookDelivery = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (deliveryId) => webhookService.retryWebhookDelivery(deliveryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhookDeliveries'] });
    },
  });
};

export const useTestWebhook = () => {
  return useMutation({
    mutationFn: (id) => webhookService.testWebhook(id),
  });
};

// 配置管理Hooks
export const useConfigs = (params = {}) => {
  return useQuery({
    queryKey: ['configs', params],
    queryFn: () => configService.getConfigs(params),
    staleTime: 5 * 60 * 1000,
  });
};

export const useConfig = (key, params = {}) => {
  return useQuery({
    queryKey: ['config', key, params],
    queryFn: () => configService.getConfig(key, params),
    enabled: !!key,
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateConfig = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => configService.createConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configs'] });
    },
  });
};

export const useUpdateConfig = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ key, data }) => configService.updateConfig(key, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['configs'] });
      queryClient.invalidateQueries({ queryKey: ['config', variables.key] });
    },
  });
};

export const useDeleteConfig = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (key) => configService.deleteConfig(key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configs'] });
    },
  });
};

export const useConfigHistory = (key, params = {}) => {
  return useQuery({
    queryKey: ['configHistory', key, params],
    queryFn: () => configService.getConfigHistory(key, params),
    enabled: !!key,
    staleTime: 2 * 60 * 1000,
  });
};

export const useRollbackConfig = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ key, data }) => configService.rollbackConfig(key, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['configs'] });
      queryClient.invalidateQueries({ queryKey: ['config', variables.key] });
      queryClient.invalidateQueries({ queryKey: ['configHistory', variables.key] });
    },
  });
};

export const useConfigAuditLogs = (params = {}) => {
  return useQuery({
    queryKey: ['configAuditLogs', params],
    queryFn: () => configService.getConfigAuditLogs(params),
    staleTime: 1 * 60 * 1000,
  });
};

// 生命周期管理Hooks
export const useLifecycle = (modelId) => {
  return useQuery({
    queryKey: ['lifecycle', modelId],
    queryFn: () => lifecycleService.getLifecycle(modelId),
    enabled: !!modelId,
    staleTime: 2 * 60 * 1000,
  });
};

export const useRequestTransition = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ modelId, data }) => lifecycleService.requestTransition(modelId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle', variables.modelId] });
      queryClient.invalidateQueries({ queryKey: ['transitionHistory', variables.modelId] });
    },
  });
};

export const useTransitionHistory = (modelId, params = {}) => {
  return useQuery({
    queryKey: ['transitionHistory', modelId, params],
    queryFn: () => lifecycleService.getTransitionHistory(modelId, params),
    enabled: !!modelId,
    staleTime: 2 * 60 * 1000,
  });
};

export const usePendingApprovals = (params = {}) => {
  return useQuery({
    queryKey: ['pendingApprovals', params],
    queryFn: () => lifecycleService.getPendingApprovals(params),
    staleTime: 1 * 60 * 1000,
  });
};

export const useApproveTransition = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ approvalId, data }) => lifecycleService.approveTransition(approvalId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingApprovals'] });
    },
  });
};

export const useCancelApproval = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (approvalId) => lifecycleService.cancelApproval(approvalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingApprovals'] });
    },
  });
};

export const useCreateDeprecation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ modelId, data }) => lifecycleService.createDeprecation(modelId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle', variables.modelId] });
      queryClient.invalidateQueries({ queryKey: ['deprecationNotices'] });
    },
  });
};

export const useDeprecationNotices = (params = {}) => {
  return useQuery({
    queryKey: ['deprecationNotices', params],
    queryFn: () => lifecycleService.getDeprecationNotices(params),
    staleTime: 2 * 60 * 1000,
  });
};

export const useAcknowledgeDeprecation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ noticeId, data }) => lifecycleService.acknowledgeDeprecation(noticeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deprecationNotices'] });
    },
  });
};

// 配额管理Hooks
export const useQuota = (userId, params = {}) => {
  return useQuery({
    queryKey: ['quota', userId, params],
    queryFn: () => quotaService.getQuota(userId, params),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000,
  });
};

export const useSetQuota = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => quotaService.setQuota(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['quota', variables.user_id] });
      queryClient.invalidateQueries({ queryKey: ['quotas'] });
    },
  });
};

export const useUpdateQuota = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, data }) => quotaService.updateQuota(userId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['quota', variables.userId] });
      queryClient.invalidateQueries({ queryKey: ['quotas'] });
    },
  });
};

export const useRecordUsage = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, data }) => quotaService.recordUsage(userId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['quota', variables.userId] });
    },
  });
};

export const useQuotaHistory = (userId, params = {}) => {
  return useQuery({
    queryKey: ['quotaHistory', userId, params],
    queryFn: () => quotaService.getQuotaHistory(userId, params),
    enabled: !!userId,
    staleTime: 1 * 60 * 1000,
  });
};

export const useAllQuotas = (params = {}) => {
  return useQuery({
    queryKey: ['quotas', params],
    queryFn: () => quotaService.getAllQuotas(params),
    staleTime: 2 * 60 * 1000,
  });
};
