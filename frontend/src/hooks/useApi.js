import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { showSuccess, showError } from '../components/UI';
import { queryKeys } from '../config/queryClient';
import apiClient from '../services/apiClient';

// Generic CRUD hooks
export const useGenericMutation = ({
  mutationFn,
  queryKey,
  onSuccess,
  onError,
  successMessage,
  errorMessage,
  invalidateQueries = [],
}) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: (data, variables, context) => {
      // Invalidate related queries
      invalidateQueries.forEach(key => {
        queryClient.invalidateQueries({ queryKey: key });
      });
      
      // Invalidate specific query if provided
      if (queryKey) {
        queryClient.invalidateQueries({ queryKey });
      }

      // Show success message
      if (successMessage) {
        showSuccess(successMessage);
      }

      // Call custom success handler
      onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      // Show error message
      const message = errorMessage || error?.response?.data?.message || '操作失败';
      showError(message);

      // Call custom error handler
      onError?.(error, variables, context);
    },
  });
};

// Auth hooks
export const useAuth = () => {
  return useQuery({
    queryKey: queryKeys.auth,
    queryFn: async () => {
      const response = await apiClient.get('/auth/me');
      return response.data;
    },
    retry: false,
    staleTime: Infinity, // Auth status doesn't change often
  });
};

export const useLogin = () => {
  const queryClient = useQueryClient();
  
  return useGenericMutation({
    mutationFn: async (credentials) => {
      const response = await apiClient.post('/auth/login', credentials);
      return response.data;
    },
    queryKey: queryKeys.auth,
    successMessage: '登录成功',
    onSuccess: (data) => {
      // Update auth data
      queryClient.setQueryData(queryKeys.auth, data.user);
    },
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/auth/logout');
      return response.data;
    },
    onSuccess: () => {
      // Clear all auth data
      queryClient.clear();
      showSuccess('已成功退出登录');
    },
    onError: () => {
      // Clear auth data even if logout fails
      queryClient.clear();
    },
  });
};

// Model hooks
export const useModels = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.models, params],
    queryFn: async () => {
      const response = await apiClient.get('/models', { params });
      return response.data;
    },
  });
};

export const useModel = (id) => {
  return useQuery({
    queryKey: queryKeys.model(id),
    queryFn: async () => {
      const response = await apiClient.get(`/models/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateModel = () => {
  return useGenericMutation({
    mutationFn: async (modelData) => {
      const response = await apiClient.post('/models', modelData);
      return response.data;
    },
    queryKey: queryKeys.models,
    successMessage: '模型创建成功',
    invalidateQueries: [queryKeys.models],
  });
};

export const useUpdateModel = () => {
  return useGenericMutation({
    mutationFn: async ({ id, ...modelData }) => {
      const response = await apiClient.put(`/models/${id}`, modelData);
      return response.data;
    },
    queryKey: queryKeys.models,
    successMessage: '模型更新成功',
    invalidateQueries: [queryKeys.models],
  });
};

export const useDeleteModel = () => {
  return useGenericMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/models/${id}`);
      return response.data;
    },
    queryKey: queryKeys.models,
    successMessage: '模型删除成功',
    invalidateQueries: [queryKeys.models],
  });
};

// Supplier hooks
export const useSuppliers = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.suppliers, params],
    queryFn: async () => {
      const response = await apiClient.get('/suppliers', { params });
      return response.data;
    },
  });
};

export const useSupplier = (id) => {
  return useQuery({
    queryKey: queryKeys.supplier(id),
    queryFn: async () => {
      const response = await apiClient.get(`/suppliers/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateSupplier = () => {
  return useGenericMutation({
    mutationFn: async (supplierData) => {
      const response = await apiClient.post('/suppliers', supplierData);
      return response.data;
    },
    queryKey: queryKeys.suppliers,
    successMessage: '供应商创建成功',
    invalidateQueries: [queryKeys.suppliers],
  });
};

export const useUpdateSupplier = () => {
  return useGenericMutation({
    mutationFn: async ({ id, ...supplierData }) => {
      const response = await apiClient.put(`/suppliers/${id}`, supplierData);
      return response.data;
    },
    queryKey: queryKeys.suppliers,
    successMessage: '供应商更新成功',
    invalidateQueries: [queryKeys.suppliers],
  });
};

export const useDeleteSupplier = () => {
  return useGenericMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/suppliers/${id}`);
      return response.data;
    },
    queryKey: queryKeys.suppliers,
    successMessage: '供应商删除成功',
    invalidateQueries: [queryKeys.suppliers],
  });
};

// Capability hooks
export const useCapabilities = (params = {}) => {
  return useQuery({
    queryKey: [...queryKeys.capabilities, params],
    queryFn: async () => {
      const response = await apiClient.get('/capabilities', { params });
      return response.data;
    },
  });
};

export const useCapability = (id) => {
  return useQuery({
    queryKey: queryKeys.capability(id),
    queryFn: async () => {
      const response = await apiClient.get(`/capabilities/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateCapability = () => {
  return useGenericMutation({
    mutationFn: async (capabilityData) => {
      const response = await apiClient.post('/capabilities', capabilityData);
      return response.data;
    },
    queryKey: queryKeys.capabilities,
    successMessage: '能力创建成功',
    invalidateQueries: [queryKeys.capabilities],
  });
};

export const useUpdateCapability = () => {
  return useGenericMutation({
    mutationFn: async ({ id, ...capabilityData }) => {
      const response = await apiClient.put(`/capabilities/${id}`, capabilityData);
      return response.data;
    },
    queryKey: queryKeys.capabilities,
    successMessage: '能力更新成功',
    invalidateQueries: [queryKeys.capabilities],
  });
};

export const useDeleteCapability = () => {
  return useGenericMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/capabilities/${id}`);
      return response.data;
    },
    queryKey: queryKeys.capabilities,
    successMessage: '能力删除成功',
    invalidateQueries: [queryKeys.capabilities],
  });
};

// Parameter hooks
export const useParameterTemplates = () => {
  return useQuery({
    queryKey: queryKeys.parameterTemplates,
    queryFn: async () => {
      const response = await apiClient.get('/parameters/templates');
      return response.data;
    },
  });
};

export const useCreateParameterTemplate = () => {
  return useGenericMutation({
    mutationFn: async (templateData) => {
      const response = await apiClient.post('/parameters/templates', templateData);
      return response.data;
    },
    queryKey: queryKeys.parameterTemplates,
    successMessage: '参数模板创建成功',
    invalidateQueries: [queryKeys.parameterTemplates],
  });
};

export const useUpdateParameterTemplate = () => {
  return useGenericMutation({
    mutationFn: async ({ id, ...templateData }) => {
      const response = await apiClient.put(`/parameters/templates/${id}`, templateData);
      return response.data;
    },
    queryKey: queryKeys.parameterTemplates,
    successMessage: '参数模板更新成功',
    invalidateQueries: [queryKeys.parameterTemplates],
  });
};

export const useDeleteParameterTemplate = () => {
  return useGenericMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/parameters/templates/${id}`);
      return response.data;
    },
    queryKey: queryKeys.parameterTemplates,
    successMessage: '参数模板删除成功',
    invalidateQueries: [queryKeys.parameterTemplates],
  });
};

// Knowledge hooks
export const useKnowledgeSearch = (query, options = {}) => {
  return useQuery({
    queryKey: [...queryKeys.semanticSearch, query],
    queryFn: async () => {
      const response = await apiClient.get('/knowledge/search', {
        params: { q: query }
      });
      return response.data;
    },
    enabled: !!query && query.length > 0,
    ...options,
  });
};

export const useKnowledgeGraph = () => {
  return useQuery({
    queryKey: queryKeys.knowledgeGraph,
    queryFn: async () => {
      const response = await apiClient.get('/knowledge/graph');
      return response.data;
    },
  });
};

// Workflow hooks
export const useWorkflows = () => {
  return useQuery({
    queryKey: queryKeys.workflows,
    queryFn: async () => {
      const response = await apiClient.get('/workflows');
      return response.data;
    },
  });
};

export const useWorkflow = (id) => {
  return useQuery({
    queryKey: queryKeys.workflow(id),
    queryFn: async () => {
      const response = await apiClient.get(`/workflows/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateWorkflow = () => {
  return useGenericMutation({
    mutationFn: async (workflowData) => {
      const response = await apiClient.post('/workflows', workflowData);
      return response.data;
    },
    queryKey: queryKeys.workflows,
    successMessage: '工作流创建成功',
    invalidateQueries: [queryKeys.workflows],
  });
};

export const useExecuteWorkflow = () => {
  return useGenericMutation({
    mutationFn: async ({ id, inputs }) => {
      const response = await apiClient.post(`/workflows/${id}/execute`, { inputs });
      return response.data;
    },
    successMessage: '工作流执行成功',
  });
};