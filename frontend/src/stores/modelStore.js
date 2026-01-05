import { create } from 'zustand';

const useModelStore = create((set, get) => ({
  // Model state
  models: [],
  selectedModel: null,
  modelCategories: [],
  defaultModels: [],
  isLoading: false,
  error: null,

  // Model actions
  setModels: (models) => set({ models }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setModelCategories: (categories) => set({ modelCategories: categories }),
  setDefaultModels: (models) => set({ defaultModels: models }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  // CRUD operations
  addModel: (model) => {
    const models = get().models;
    set({ models: [...models, model] });
  },

  updateModel: (modelId, updates) => {
    const models = get().models;
    set({
      models: models.map(model => 
        model.id === modelId ? { ...model, ...updates } : model
      )
    });
  },

  deleteModel: (modelId) => {
    const models = get().models;
    set({ models: models.filter(model => model.id !== modelId) });
  },

  // Initialize model store
  initialize: async () => {
    set({ isLoading: true, error: null });
    try {
      // Load default models and categories
      await new Promise(resolve => setTimeout(resolve, 100));
      set({ isLoading: false });
      return true;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      return false;
    }
  },

  // Utility actions
  clearError: () => set({ error: null }),
  reset: () => set({
    models: [],
    selectedModel: null,
    modelCategories: [],
    defaultModels: [],
    isLoading: false,
    error: null,
  }),
}));

export default useModelStore;