import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { queryKeys } from '../config/queryClient';

// API loading states
const useApiStore = create(
  devtools(
    (set, get) => ({
      // Loading states for different entities
      loading: {
        models: false,
        suppliers: false,
        capabilities: false,
        parameters: false,
        knowledge: false,
        workflows: false,
      },

      // Error states
      errors: {
        models: null,
        suppliers: null,
        capabilities: null,
        parameters: null,
        knowledge: null,
        workflows: null,
      },

      // Selected items for editing/viewing
      selectedItems: {
        model: null,
        supplier: null,
        capability: null,
        parameterTemplate: null,
        workflow: null,
      },

      // Modal states
      modals: {
        createModel: false,
        editModel: false,
        createSupplier: false,
        editSupplier: false,
        createCapability: false,
        editCapability: false,
        createParameterTemplate: false,
        editParameterTemplate: false,
        createWorkflow: false,
        editWorkflow: false,
        viewModelDetails: false,
        viewSupplierDetails: false,
        viewCapabilityDetails: false,
        viewWorkflowDetails: false,
      },

      // Table states
      tableStates: {
        models: {
          sortBy: null,
          sortOrder: 'asc',
          selectedRows: [],
          pagination: {
            current: 1,
            pageSize: 10,
            total: 0,
          },
        },
        suppliers: {
          sortBy: null,
          sortOrder: 'asc',
          selectedRows: [],
          pagination: {
            current: 1,
            pageSize: 10,
            total: 0,
          },
        },
        capabilities: {
          sortBy: null,
          sortOrder: 'asc',
          selectedRows: [],
          pagination: {
            current: 1,
            pageSize: 10,
            total: 0,
          },
        },
        workflows: {
          sortBy: null,
          sortOrder: 'asc',
          selectedRows: [],
          pagination: {
            current: 1,
            pageSize: 10,
            total: 0,
          },
        },
      },

      // Form states
      formStates: {
        model: {
          isDirty: false,
          isValid: false,
          errors: {},
        },
        supplier: {
          isDirty: false,
          isValid: false,
          errors: {},
        },
        capability: {
          isDirty: false,
          isValid: false,
          errors: {},
        },
        parameterTemplate: {
          isDirty: false,
          isValid: false,
          errors: {},
        },
        workflow: {
          isDirty: false,
          isValid: false,
          errors: {},
        },
      },

      // Actions
      setLoading: (entity, loading) =>
        set((state) => ({
          loading: {
            ...state.loading,
            [entity]: loading,
          },
        })),

      setError: (entity, error) =>
        set((state) => ({
          errors: {
            ...state.errors,
            [entity]: error,
          },
        })),

      clearError: (entity) =>
        set((state) => ({
          errors: {
            ...state.errors,
            [entity]: null,
          },
        })),

      setSelectedItem: (entity, item) =>
        set((state) => ({
          selectedItems: {
            ...state.selectedItems,
            [entity]: item,
          },
        })),

      clearSelectedItem: (entity) =>
        set((state) => ({
          selectedItems: {
            ...state.selectedItems,
            [entity]: null,
          },
        })),

      openModal: (modalName) =>
        set((state) => ({
          modals: {
            ...state.modals,
            [modalName]: true,
          },
        })),

      closeModal: (modalName) =>
        set((state) => ({
          modals: {
            ...state.modals,
            [modalName]: false,
          },
        })),

      closeAllModals: () =>
        set((state) => {
          const allModals = Object.keys(state.modals);
          const closedModals = allModals.reduce((acc, modal) => {
            acc[modal] = false;
            return acc;
          }, {});
          return {
            modals: closedModals,
          };
        }),

      setTableState: (entity, updates) =>
        set((state) => ({
          tableStates: {
            ...state.tableStates,
            [entity]: {
              ...state.tableStates[entity],
              ...updates,
            },
          },
        })),

      setTableSort: (entity, sortBy, sortOrder) =>
        set((state) => ({
          tableStates: {
            ...state.tableStates,
            [entity]: {
              ...state.tableStates[entity],
              sortBy,
              sortOrder,
            },
          },
        })),

      setTableSelection: (entity, selectedRows) =>
        set((state) => ({
          tableStates: {
            ...state.tableStates,
            [entity]: {
              ...state.tableStates[entity],
              selectedRows,
            },
          },
        })),

      setTablePagination: (entity, pagination) =>
        set((state) => ({
          tableStates: {
            ...state.tableStates,
            [entity]: {
              ...state.tableStates[entity],
              pagination: {
                ...state.tableStates[entity].pagination,
                ...pagination,
              },
            },
          },
        })),

      setFormState: (entity, formState) =>
        set((state) => ({
          formStates: {
            ...state.formStates,
            [entity]: {
              ...state.formStates[entity],
              ...formState,
            },
          },
        })),

      clearFormState: (entity) =>
        set((state) => ({
          formStates: {
            ...state.formStates,
            [entity]: {
              isDirty: false,
              isValid: false,
              errors: {},
            },
          },
        })),

      // Bulk operations
      bulkSelect: (entity, selectAll, data) =>
        set((state) => {
          const tableState = state.tableStates[entity];
          const selectedRows = selectAll ? data.map(item => item.id) : [];
          return {
            tableStates: {
              ...state.tableStates,
              [entity]: {
                ...tableState,
                selectedRows,
              },
            },
          };
        }),

      // Reset all states
      reset: () =>
        set({
          loading: {
            models: false,
            suppliers: false,
            capabilities: false,
            parameters: false,
            knowledge: false,
            workflows: false,
          },
          errors: {
            models: null,
            suppliers: null,
            capabilities: null,
            parameters: null,
            knowledge: null,
            workflows: null,
          },
          selectedItems: {
            model: null,
            supplier: null,
            capability: null,
            parameterTemplate: null,
            workflow: null,
          },
          modals: {
            createModel: false,
            editModel: false,
            createSupplier: false,
            editSupplier: false,
            createCapability: false,
            editCapability: false,
            createParameterTemplate: false,
            editParameterTemplate: false,
            createWorkflow: false,
            editWorkflow: false,
            viewModelDetails: false,
            viewSupplierDetails: false,
            viewCapabilityDetails: false,
            viewWorkflowDetails: false,
          },
        }),
    }),
    {
      name: 'api-store',
    }
  )
);

export default useApiStore;