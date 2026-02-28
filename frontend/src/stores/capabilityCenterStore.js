/**
 * 能力中心状态管理Store
 *
 * 使用Zustand管理能力中心的全局状态
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { capabilityCenterApi } from '../services/capabilityCenterApi';

/**
 * 能力中心状态存储
 */
export const useCapabilityCenterStore = create(
  devtools(
    persist(
      (set, get) => ({
        // ==================== 状态 ====================

        // 能力列表
        capabilities: [],
        loading: false,
        error: null,

        // 分页信息
        pagination: {
          page: 1,
          pageSize: 20,
          total: 0,
          totalPages: 0
        },

        // 筛选条件
        filters: {
          type: 'all',      // all/tool/skill
          source: 'all',    // all/official/user/marketplace
          status: 'all',    // all/active/disabled
          category: 'all',  // 分类筛选
          search: ''        // 搜索关键词
        },

        // 分类列表
        categories: [],

        // 选中的能力
        selectedCapability: null,

        // 智能体能力分配
        agentCapabilities: {},

        // ==================== Actions ====================

        /**
         * 设置加载状态
         */
        setLoading: (loading) => set({ loading }),

        /**
         * 设置错误信息
         */
        setError: (error) => set({ error }),

        /**
         * 设置能力列表
         */
        setCapabilities: (capabilities) => set({ capabilities }),

        /**
         * 设置分页信息
         */
        setPagination: (pagination) => set({ pagination }),

        /**
         * 设置筛选条件
         */
        setFilters: (filters) => set({ filters }),

        /**
         * 更新单个筛选条件
         */
        updateFilter: (key, value) => {
          set((state) => ({
            filters: { ...state.filters, [key]: value },
            pagination: { ...state.pagination, page: 1 }
          }));
        },

        /**
         * 重置筛选条件
         */
        resetFilters: () => {
          set({
            filters: {
              type: 'all',
              source: 'all',
              status: 'all',
              category: 'all',
              search: ''
            },
            pagination: { ...get().pagination, page: 1 }
          });
        },

        /**
         * 设置分类列表
         */
        setCategories: (categories) => set({ categories }),

        /**
         * 设置选中的能力
         */
        setSelectedCapability: (capability) => set({ selectedCapability: capability }),

        /**
         * 设置页码
         */
        setPage: (page) => {
          set((state) => ({
            pagination: { ...state.pagination, page }
          }));
        },

        /**
         * 设置每页数量
         */
        setPageSize: (pageSize) => {
          set((state) => ({
            pagination: { ...state.pagination, pageSize, page: 1 }
          }));
        },

        // ==================== 异步Actions ====================

        /**
         * 加载能力列表
         */
        fetchCapabilities: async () => {
          const { filters, pagination } = get();

          set({ loading: true, error: null });

          try {
            const params = {
              type: filters.type === 'all' ? undefined : filters.type,
              source: filters.source === 'all' ? undefined : filters.source,
              status: filters.status === 'all' ? undefined : filters.status,
              category: filters.category === 'all' ? undefined : filters.category,
              search: filters.search || undefined,
              page: pagination.page,
              page_size: pagination.pageSize
            };

            const response = await capabilityCenterApi.getCapabilities(params);

            if (response.success) {
              set({
                capabilities: response.data.items,
                pagination: {
                  page: response.data.page,
                  pageSize: response.data.page_size,
                  total: response.data.total,
                  totalPages: response.data.total_pages
                },
                loading: false
              });
            } else {
              set({
                error: response.message || '加载失败',
                loading: false
              });
            }
          } catch (err) {
            set({
              error: err.message || '加载失败',
              loading: false
            });
          }
        },

        /**
         * 加载分类列表
         */
        fetchCategories: async () => {
          try {
            const response = await capabilityCenterApi.getCategories();
            if (response.success) {
              set({ categories: response.data });
            }
          } catch (err) {
            console.error('加载分类失败:', err);
          }
        },

        /**
         * 启用/禁用能力
         */
        toggleCapability: async (capability) => {
          const newEnabled = !capability.is_active;

          try {
            const response = await capabilityCenterApi.toggleCapability(
              capability.type,
              capability.id,
              newEnabled
            );

            if (response.success) {
              // 更新本地状态
              set((state) => ({
                capabilities: state.capabilities.map(cap =>
                  cap.id === capability.id && cap.type === capability.type
                    ? { ...cap, is_active: newEnabled, status: newEnabled ? 'active' : 'disabled' }
                    : cap
                )
              }));
              return { success: true, message: response.message };
            } else {
              return { success: false, message: response.message };
            }
          } catch (err) {
            return { success: false, message: err.message };
          }
        },

        /**
         * 删除能力
         */
        deleteCapability: async (capability) => {
          try {
            const response = await capabilityCenterApi.deleteCapability(
              capability.type,
              capability.id
            );

            if (response.success) {
              // 从本地状态中移除
              set((state) => ({
                capabilities: state.capabilities.filter(
                  cap => !(cap.id === capability.id && cap.type === capability.type)
                )
              }));
              return { success: true, message: response.message };
            } else {
              return { success: false, message: response.message };
            }
          } catch (err) {
            return { success: false, message: err.message };
          }
        },

        /**
         * 加载智能体的能力分配
         */
        fetchAgentCapabilities: async (agentId) => {
          try {
            const response = await capabilityCenterApi.getAgentCapabilities(agentId);
            if (response.success) {
              set((state) => ({
                agentCapabilities: {
                  ...state.agentCapabilities,
                  [agentId]: response.data
                }
              }));
              return { success: true, data: response.data };
            } else {
              return { success: false, message: response.message };
            }
          } catch (err) {
            return { success: false, message: err.message };
          }
        },

        /**
         * 为智能体分配能力
         */
        assignCapabilityToAgent: async (agentId, assignment) => {
          try {
            const response = await capabilityCenterApi.assignCapabilityToAgent(
              agentId,
              assignment
            );

            if (response.success) {
              // 刷新智能体能力列表
              await get().fetchAgentCapabilities(agentId);
              return { success: true, message: response.message };
            } else {
              return { success: false, message: response.message };
            }
          } catch (err) {
            return { success: false, message: err.message };
          }
        },

        /**
         * 从智能体移除能力
         */
        removeCapabilityFromAgent: async (agentId, capabilityType, capabilityId) => {
          try {
            const response = await capabilityCenterApi.removeCapabilityFromAgent(
              agentId,
              capabilityType,
              capabilityId
            );

            if (response.success) {
              // 刷新智能体能力列表
              await get().fetchAgentCapabilities(agentId);
              return { success: true, message: response.message };
            } else {
              return { success: false, message: response.message };
            }
          } catch (err) {
            return { success: false, message: err.message };
          }
        },

        /**
         * 清除错误
         */
        clearError: () => set({ error: null })
      }),
      {
        name: 'capability-center-storage',
        partialize: (state) => ({
          // 只持久化筛选条件和分页大小
          filters: state.filters,
          pagination: {
            pageSize: state.pagination.pageSize
          }
        })
      }
    ),
    { name: 'CapabilityCenterStore' }
  )
);

export default useCapabilityCenterStore;
