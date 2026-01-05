import React from 'react';
import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// 导入子stores
import useAppStore from './appStore';
import useAuthStore from './authStore';
import useModelStore from './modelStore';
import useSupplierStore from './supplierStore';
import useApiStore from './apiStore';

/**
 * 根状态管理store
 * 统一管理所有子store和全局状态操作
 */
const useRootStore = create(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        // 全局状态
        isInitialized: false,
        appReady: false,
        error: null,
        loading: false,

        // 初始化应用
        initializeApp: async () => {
          set((state) => {
            state.loading = true;
            state.error = null;
          });

          try {
            // 初始化各个store
            await Promise.all([
              useAppStore.getState().initialize?.(),
              useAuthStore.getState().initialize?.(),
              useModelStore.getState().initialize?.(),
              useSupplierStore.getState().initialize?.(),
              useApiStore.getState().initialize?.(),
            ]);

            set((state) => {
              state.isInitialized = true;
              state.appReady = true;
              state.loading = false;
            });
          } catch (error) {
            set((state) => {
              state.error = error.message || '应用初始化失败';
              state.loading = false;
            });
          }
        },

        // 重置所有状态
        resetAll: () => {
          useAppStore.getState().reset();
          useAuthStore.getState().reset?.();
          useModelStore.getState().reset();
          useSupplierStore.getState().reset();
          useApiStore.getState().reset?.();
          
          set((state) => {
            state.isInitialized = false;
            state.appReady = false;
            state.error = null;
            state.loading = false;
          });
        },

        // 全局错误处理
        setGlobalError: (error) => {
          set((state) => {
            state.error = error;
          });
        },

        clearGlobalError: () => {
          set((state) => {
            state.error = null;
          });
        },

        // 批量状态操作
        batchUpdate: (updates) => {
          set((state) => {
            Object.keys(updates).forEach(key => {
              if (key in state) {
                state[key] = updates[key];
              }
            });
          });
        },

        // 状态订阅
        subscribeToStore: (storeName, callback) => {
          const storeMap = {
            app: useAppStore,
            auth: useAuthStore,
            model: useModelStore,
            supplier: useSupplierStore,
            api: useApiStore,
          };

          const store = storeMap[storeName];
          if (store) {
            return store.subscribe(callback);
          }
          
          return () => {};
        },

        // 获取状态快照
        getSnapshot: () => {
          return {
            app: useAppStore.getState(),
            auth: useAuthStore.getState(),
            model: useModelStore.getState(),
            supplier: useSupplierStore.getState(),
            api: useApiStore.getState(),
            root: get(),
          };
        },
      }))
    ),
    {
      name: 'root-store',
    }
  )
);

// 导出所有store
export {
  useAppStore,
  useAuthStore,
  useModelStore,
  useSupplierStore,
  useApiStore,
  useRootStore,
};

// 便捷的store组合hooks
export const useCombinedStores = (storeNames) => {
  const stores = {
    app: useAppStore(),
    auth: useAuthStore(),
    model: useModelStore(),
    supplier: useSupplierStore(),
    api: useApiStore(),
  };

  return storeNames.reduce((acc, name) => {
    acc[name] = stores[name];
    return acc;
  }, {});
};

// 全局状态选择器
export const useGlobalState = (selector) => {
  return useRootStore(selector);
};

// 监听多个store变化
export const useMultiStoreSubscription = (subscriptions, callback) => {
  React.useEffect(() => {
    const unsubscribers = subscriptions.map(({ store, selector }) => 
      store.subscribe(selector, callback)
    );

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [subscriptions, callback]);
};

export default useRootStore;