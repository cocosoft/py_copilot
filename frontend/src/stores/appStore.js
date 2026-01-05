import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useAppStore = create(
  persist(
    (set, get) => ({
      // App state
      theme: 'light',
      sidebarCollapsed: false,
      language: 'zh-CN',
      notifications: [],
      isLoading: false,
      error: null,

      // App settings
      autoSave: true,
      showPerformanceMetrics: false,
      debugMode: false,

      // App actions
      setTheme: (theme) => set({ theme }),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setLanguage: (language) => set({ language }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),

      // Notification actions
      addNotification: (notification) => {
        const id = Date.now().toString();
        const newNotification = { 
          id, 
          timestamp: Date.now(), 
          ...notification 
        };
        set((state) => ({
          notifications: [newNotification, ...state.notifications].slice(0, 50) // Keep max 50
        }));
        
        // Auto remove after duration
        if (notification.duration) {
          setTimeout(() => {
            get().removeNotification(id);
          }, notification.duration);
        }
        
        return id;
      },

      removeNotification: (id) => {
        set((state) => ({
          notifications: state.notifications.filter(n => n.id !== id)
        }));
      },

      clearNotifications: () => set({ notifications: [] }),

      // Initialize app store
  initialize: async () => {
    set({ isLoading: true, error: null });
    try {
      // Perform any necessary initialization
      await new Promise(resolve => setTimeout(resolve, 100));
      set({ isLoading: false });
      return true;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      return false;
    }
  },

  // Utility actions
  toggleSidebar: () => {
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
  },

  toggleDebugMode: () => {
    set((state) => ({ debugMode: !state.debugMode }));
  },

  reset: () => set({
    theme: 'light',
    sidebarCollapsed: false,
    language: 'zh-CN',
    notifications: [],
    isLoading: false,
    error: null,
    autoSave: true,
    showPerformanceMetrics: false,
    debugMode: false,
  }),
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        language: state.language,
        autoSave: state.autoSave,
        showPerformanceMetrics: state.showPerformanceMetrics,
        debugMode: state.debugMode,
      }),
    }
  )
);

export default useAppStore;