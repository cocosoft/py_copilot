import { create } from 'zustand';

const useSupplierStore = create((set, get) => ({
  // Supplier state
  suppliers: [],
  selectedSupplier: null,
  isLoading: false,
  error: null,

  // Supplier actions
  setSuppliers: (suppliers) => set({ suppliers }),
  setSelectedSupplier: (supplier) => set({ selectedSupplier: supplier }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  // CRUD operations
  addSupplier: (supplier) => {
    const suppliers = get().suppliers;
    set({ suppliers: [...suppliers, supplier] });
  },

  updateSupplier: (supplierId, updates) => {
    const suppliers = get().suppliers;
    set({
      suppliers: suppliers.map(supplier => 
        supplier.id === supplierId ? { ...supplier, ...updates } : supplier
      )
    });
  },

  deleteSupplier: (supplierId) => {
    const suppliers = get().suppliers;
    set({ suppliers: suppliers.filter(supplier => supplier.id !== supplierId) });
  },

  // Initialize supplier store
  initialize: async () => {
    set({ isLoading: true, error: null });
    try {
      // Load suppliers data
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
    suppliers: [],
    selectedSupplier: null,
    isLoading: false,
    error: null,
  }),
}));

export default useSupplierStore;