import { QueryClient } from '@tanstack/react-query';

// Create a client
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        // Retry up to 3 times for other errors
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Query keys factory
export const queryKeys = {
  // Auth
  auth: ['auth'],
  user: ['auth', 'user'],
  permissions: ['auth', 'permissions'],

  // Models
  models: ['models'],
  model: (id) => ['models', id],
  modelCategories: ['models', 'categories'],
  defaultModels: ['models', 'default'],

  // Suppliers
  suppliers: ['suppliers'],
  supplier: (id) => ['suppliers', id],

  // Capabilities
  capabilities: ['capabilities'],
  capability: (id) => ['capabilities', id],
  capabilityDimensions: ['capabilities', 'dimensions'],
  capabilityTypes: ['capabilities', 'types'],

  // Parameters
  parameters: ['parameters'],
  parameterTemplates: ['parameters', 'templates'],
  parameterTemplate: (id) => ['parameters', 'templates', id],

  // Knowledge
  knowledge: ['knowledge'],
  knowledgeGraph: ['knowledge', 'graph'],
  semanticSearch: ['knowledge', 'search'],

  // Workflows
  workflows: ['workflows'],
  workflow: (id) => ['workflows', id],
};