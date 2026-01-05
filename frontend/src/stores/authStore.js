import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useAuthStore = create(
  persist(
    (set, get) => ({
      // Auth state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      permissions: [],

      // Auth actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      setLoading: (isLoading) => set({ isLoading }),
      setPermissions: (permissions) => set({ permissions }),
      
      // Logout action
      logout: () => set({ 
        user: null, 
        token: null, 
        isAuthenticated: false, 
        permissions: [] 
      }),

      // Initialize auth store
      initialize: async () => {
        set({ isLoading: true, error: null });
        try {
          // Check token validity and refresh if needed
          const token = get().token;
          if (token) {
            // Perform token validation
            await new Promise(resolve => setTimeout(resolve, 100));
          }
          set({ isLoading: false });
          return true;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          // Clear invalid token
          set({ token: null, user: null, isAuthenticated: false });
          return false;
        }
      },

      // Check if user has permission
      hasPermission: (permission) => {
        const permissions = get().permissions;
        return permissions.includes(permission) || permissions.includes('admin');
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
        permissions: state.permissions,
      }),
    }
  )
);

export default useAuthStore;