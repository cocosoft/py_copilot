/**
 * 知识库状态管理 Store - FE-002 状态管理优化
 *
 * 使用 Zustand + Immer 实现知识库模块的状态管理
 *
 * @task FE-002
 * @phase 前端界面优化
 */

import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { enableMapSet } from 'immer';

// 启用 Immer 的 MapSet 插件
enableMapSet();

/**
 * 知识库状态类型定义
 * @typedef {Object} KnowledgeState
 * @property {Array} knowledgeBases - 知识库列表
 * @property {Object} currentKnowledgeBase - 当前选中的知识库
 * @property {Array} documents - 文档列表
 * @property {Array} chunks - 片段列表
 * @property {Array} entities - 实体列表
 * @property {Array} relationships - 关系列表
 * @property {Object} selectedItems - 选中的项目
 * @property {Object} filters - 过滤器状态
 * @property {Object} pagination - 分页状态
 * @property {Object} loading - 加载状态
 * @property {Object} error - 错误状态
 * @property {Object} cache - 缓存数据
 */

/**
 * 初始状态
 */
const initialState = {
  // 知识库列表
  knowledgeBases: [],
  knowledgeBasesTotal: 0,
  knowledgeBasesLoading: false,
  knowledgeBasesError: null,

  // 当前知识库
  currentKnowledgeBase: null,
  currentKnowledgeBaseLoading: false,
  currentKnowledgeBaseError: null,

  // 文档列表
  documents: [],
  documentsTotal: 0,
  documentsLoading: false,
  documentsError: null,
  documentsPage: 1,
  documentsPageSize: 20,

  // 片段列表
  chunks: [],
  chunksTotal: 0,
  chunksLoading: false,
  chunksError: null,
  chunksPage: 1,
  chunksPageSize: 20,

  // 实体列表
  entities: [],
  entitiesTotal: 0,
  entitiesLoading: false,
  entitiesError: null,

  // 关系列表
  relationships: [],
  relationshipsTotal: 0,
  relationshipsLoading: false,
  relationshipsError: null,

  // 选中的项目
  selectedDocuments: [],
  selectedChunks: [],
  selectedEntities: [],
  expandedChunks: [],

  // 过滤器
  documentFilters: {
    search: '',
    status: 'all',
    fileType: 'all',
    dateRange: null,
    sortBy: 'updatedAt',
    sortOrder: 'desc',
  },

  chunkFilters: {
    search: '',
    status: 'all',
    minSimilarity: 0,
    sortBy: 'index',
    sortOrder: 'asc',
  },

  entityFilters: {
    search: '',
    entityType: 'all',
    sortBy: 'name',
    sortOrder: 'asc',
  },

  // 搜索状态
  searchQuery: '',
  searchResults: [],
  searchLoading: false,
  searchError: null,

  // 处理状态
  processingStatus: {},

  // 缓存
  cache: {
    documents: new Map(),
    chunks: new Map(),
    entities: new Map(),
    searchResults: new Map(),
    // 缓存配置
    config: {
      maxSize: 1000, // 最大缓存条目数
      maxAge: 5 * 60 * 1000, // 缓存最大年龄（5分钟）
    },
    // 缓存统计
    stats: {
      hits: 0,
      misses: 0,
      size: 0,
    },
  },

  // 视图状态
  viewMode: 'list', // 'list' | 'grid' | 'graph'
  sidebarCollapsed: false,
  activeTab: 'documents', // 'documents' | 'chunks' | 'entities' | 'graph'

  // 批量操作
  batchOperation: null,
  batchProgress: 0,
  batchResults: [],

  // 处理队列
  processingQueue: [],
  isProcessing: false,
  processingProgress: 0,

  // 搜索历史
  searchHistory: [],
  searchSuggestions: [],

  // 消息通知
  notifications: [],

  // 层级状态
  currentHierarchyLevel: 'knowledge_base', // 'fragment' | 'document' | 'knowledge_base' | 'global'

  // 层级数据缓存
  hierarchyData: {
    fragment: {},
    document: {},
    knowledge_base: {},
    global: {}
  },

  // 下钻路径
  drillDownPath: [],

  // ============================================================================
  // 层级视图逻辑修复 - 新增层级状态管理
  // 任务编号: Phase3-Week10
  // ============================================================================

  // 层级选择状态
  hierarchySelection: {
    selectedDocumentId: null,
    selectedChunkId: null,
  },

  // 层级数据
  hierarchyDocuments: [],
  hierarchyDocumentsTotal: 0,
  hierarchyDocumentsLoading: false,
  hierarchyDocumentsError: null,

  hierarchyChunks: [],
  hierarchyChunksTotal: 0,
  hierarchyChunksLoading: false,
  hierarchyChunksError: null,

  hierarchyEntities: [],
  hierarchyEntitiesTotal: 0,
  hierarchyEntitiesLoading: false,
  hierarchyEntitiesError: null,

  // 层级统计数据
  hierarchyStats: {
    fragment: null,
    document: null,
    knowledgeBase: null,
    global: null,
  },

  // 层级视图状态
  hierarchyViewMode: 'list', // 'list' | 'graph' | 'stats'
};

/**
 * 创建知识库 Store
 */
const useKnowledgeStore = create(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          ...initialState,

          // ==================== Actions ====================

          /**
           * 设置知识库列表
           */
          setKnowledgeBases: (knowledgeBases, total) => {
            set((state) => {
              state.knowledgeBases = knowledgeBases;
              state.knowledgeBasesTotal = total;
            });
          },

          /**
           * 设置当前知识库
           * 切换知识库时清除文档列表和选中状态
           */
          setCurrentKnowledgeBase: (knowledgeBase) => {
            set((state) => {
              // 如果是不同的知识库，清除相关数据
              if (!knowledgeBase || state.currentKnowledgeBase?.id !== knowledgeBase?.id) {
                state.documents = [];
                state.documentsTotal = 0;
                state.selectedDocuments = [];
                state.chunks = [];
                state.chunksTotal = 0;
                state.entities = [];
                state.relationships = [];
              }
              state.currentKnowledgeBase = knowledgeBase;
            });
          },

          /**
           * 设置文档列表
           * @param {Array} documents - 文档列表
           * @param {number} total - 文档总数
           * @param {boolean} append - 是否追加模式（用于加载更多）
           */
          setDocuments: (documents, total, append = false) => {
            set((state) => {
              if (append) {
                // 追加模式：合并现有数据和新数据
                const existingIds = new Set(state.documents.map(d => d.id));
                const newDocuments = documents.filter(d => !existingIds.has(d.id));
                state.documents = [...state.documents, ...newDocuments];
              } else {
                // 替换模式：直接替换所有数据
                state.documents = documents;
              }
              state.documentsTotal = total;

              // 更新缓存
              documents.forEach((doc) => {
                state.cache.documents.set(doc.id, doc);
              });
            });
          },

          /**
           * 追加文档（无限滚动）
           */
          appendDocuments: (documents, total) => {
            set((state) => {
              state.documents = [...state.documents, ...documents];
              state.documentsTotal = total;

              // 更新缓存
              documents.forEach((doc) => {
                state.cache.documents.set(doc.id, doc);
              });
            });
          },

          /**
           * 设置片段列表
           */
          setChunks: (chunks, total) => {
            set((state) => {
              state.chunks = chunks;
              state.chunksTotal = total;

              chunks.forEach((chunk) => {
                state.cache.chunks.set(chunk.id, chunk);
              });
            });
          },

          /**
           * 追加片段
           */
          appendChunks: (chunks, total) => {
            set((state) => {
              state.chunks = [...state.chunks, ...chunks];
              state.chunksTotal = total;

              chunks.forEach((chunk) => {
                state.cache.chunks.set(chunk.id, chunk);
              });
            });
          },

          /**
           * 设置实体列表
           */
          setEntities: (entities, total) => {
            set((state) => {
              state.entities = entities;
              state.entitiesTotal = total;

              entities.forEach((entity) => {
                state.cache.entities.set(entity.id, entity);
              });
            });
          },

          /**
           * 设置关系列表
           */
          setRelationships: (relationships, total) => {
            set((state) => {
              state.relationships = relationships;
              state.relationshipsTotal = total;
            });
          },

          /**
           * 设置搜索状态
           */
          setSearchResults: (results) => {
            set((state) => {
              state.searchResults = results;

              // 缓存搜索结果
              const cacheKey = state.searchQuery;
              state.cache.searchResults.set(cacheKey, {
                results,
                timestamp: Date.now(),
              });
            });
          },

          /**
           * 设置搜索查询
           */
          setSearchQuery: (query) => {
            set((state) => {
              state.searchQuery = query;
            });
          },

          // ==================== 选择操作 ====================

          /**
           * 切换文档选中状态
           */
          toggleDocumentSelection: (documentId) => {
            const id = String(documentId);
            console.log('[toggleDocumentSelection] 切换文档选中状态:', id);
            set((state) => {
              const index = state.selectedDocuments.findIndex(selectedId => String(selectedId) === id);
              if (index > -1) {
                state.selectedDocuments.splice(index, 1);
                console.log('[toggleDocumentSelection] 取消选中:', id, '当前选中:', state.selectedDocuments);
              } else {
                state.selectedDocuments.push(id);
                console.log('[toggleDocumentSelection] 选中:', id, '当前选中:', state.selectedDocuments);
              }
            });
          },

          /**
           * 设置选中文档
           */
          setSelectedDocuments: (documentIds) => {
            set((state) => {
              state.selectedDocuments = documentIds;
            });
          },

          /**
           * 全选/取消全选文档
           */
          selectAllDocuments: (select) => {
            set((state) => {
              if (select) {
                state.selectedDocuments = state.documents.map((d) => String(d.id));
              } else {
                state.selectedDocuments = [];
              }
            });
          },

          /**
           * 清空文档选择
           */
          clearSelection: () => {
            set((state) => {
              state.selectedDocuments = [];
            });
          },

          /**
           * 切换片段选中状态
           */
          toggleChunkSelection: (chunkId) => {
            set((state) => {
              const index = state.selectedChunks.indexOf(chunkId);
              if (index > -1) {
                state.selectedChunks.splice(index, 1);
              } else {
                state.selectedChunks.push(chunkId);
              }
            });
          },

          /**
           * 设置选中片段
           */
          setSelectedChunks: (chunkIds) => {
            set((state) => {
              state.selectedChunks = chunkIds;
            });
          },

          /**
           * 切换片段展开状态
           */
          toggleChunkExpansion: (chunkId) => {
            set((state) => {
              const index = state.expandedChunks.indexOf(chunkId);
              if (index > -1) {
                state.expandedChunks.splice(index, 1);
              } else {
                state.expandedChunks.push(chunkId);
              }
            });
          },

          /**
           * 设置展开片段
           */
          setExpandedChunks: (chunkIds) => {
            set((state) => {
              state.expandedChunks = chunkIds;
            });
          },

          // ==================== 过滤器操作 ====================

          /**
           * 设置文档过滤器
           */
          setDocumentFilters: (filters) => {
            set((state) => {
              state.documentFilters = { ...state.documentFilters, ...filters };
              state.documentsPage = 1; // 重置页码
            });
          },

          /**
           * 重置文档过滤器
           */
          resetDocumentFilters: () => {
            set((state) => {
              state.documentFilters = initialState.documentFilters;
              state.documentsPage = 1;
            });
          },

          /**
           * 设置片段过滤器
           */
          setChunkFilters: (filters) => {
            set((state) => {
              state.chunkFilters = { ...state.chunkFilters, ...filters };
              state.chunksPage = 1;
            });
          },

          /**
           * 重置片段过滤器
           */
          resetChunkFilters: () => {
            set((state) => {
              state.chunkFilters = initialState.chunkFilters;
              state.chunksPage = 1;
            });
          },

          /**
           * 设置实体过滤器
           */
          setEntityFilters: (filters) => {
            set((state) => {
              state.entityFilters = { ...state.entityFilters, ...filters };
            });
          },

          // ==================== 分页操作 ====================

          /**
           * 设置文档页码
           */
          setDocumentsPage: (page) => {
            set((state) => {
              state.documentsPage = page;
            });
          },

          /**
           * 设置文档每页数量
           */
          setDocumentsPageSize: (pageSize) => {
            set((state) => {
              state.documentsPageSize = pageSize;
              state.documentsPage = 1;
            });
          },

          /**
           * 设置片段页码
           */
          setChunksPage: (page) => {
            set((state) => {
              state.chunksPage = page;
            });
          },

          // ==================== 加载状态 ====================

          /**
           * 设置知识库列表加载状态
           */
          setKnowledgeBasesLoading: (loading) => {
            set((state) => {
              state.knowledgeBasesLoading = loading;
            });
          },

          /**
           * 设置知识库列表错误
           */
          setKnowledgeBasesError: (error) => {
            set((state) => {
              state.knowledgeBasesError = error;
            });
          },

          /**
           * 设置文档加载状态
           */
          setDocumentsLoading: (loading) => {
            set((state) => {
              state.documentsLoading = loading;
            });
          },

          /**
           * 设置文档错误
           */
          setDocumentsError: (error) => {
            set((state) => {
              state.documentsError = error;
            });
          },

          /**
           * 设置片段加载状态
           */
          setChunksLoading: (loading) => {
            set((state) => {
              state.chunksLoading = loading;
            });
          },

          /**
           * 设置搜索加载状态
           */
          setSearchLoading: (loading) => {
            set((state) => {
              state.searchLoading = loading;
            });
          },

          // ==================== 处理状态 ====================

          /**
           * 设置处理状态
           */
          setProcessingStatus: (id, status) => {
            set((state) => {
              state.processingStatus[id] = status;
            });
          },

          /**
           * 设置处理进度
           */
          setProcessingProgress: (id, progress) => {
            set((state) => {
              state.processingProgress[id] = progress;
            });
          },

          /**
           * 清除处理状态
           */
          clearProcessingStatus: (id) => {
            set((state) => {
              delete state.processingStatus[id];
              delete state.processingProgress[id];
            });
          },



          // ==================== 视图状态 ====================

          /**
           * 设置视图模式
           */
          setViewMode: (mode) => {
            set((state) => {
              state.viewMode = mode;
            });
          },

          /**
           * 切换侧边栏
           */
          toggleSidebar: () => {
            set((state) => {
              state.sidebarCollapsed = !state.sidebarCollapsed;
            });
          },

          /**
           * 设置侧边栏折叠状态
           */
          setSidebarCollapsed: (collapsed) => {
            set((state) => {
              state.sidebarCollapsed = collapsed;
            });
          },

          /**
           * 设置活动标签
           */
          setActiveTab: (tab) => {
            set((state) => {
              state.activeTab = tab;
            });
          },

          // ==================== 缓存操作 ====================

          /**
           * 获取缓存的文档
           */
          getCachedDocument: (id) => {
            return get().cache.documents.get(id);
          },

          /**
           * 获取缓存的片段
           */
          getCachedChunk: (id) => {
            return get().cache.chunks.get(id);
          },

          /**
           * 获取缓存的实体
           */
          getCachedEntity: (id) => {
            return get().cache.entities.get(id);
          },

          /**
           * 获取缓存的搜索结果
           */
          getCachedSearchResults: (query) => {
            const cached = get().cache.searchResults.get(query);
            if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
              return cached.results;
            }
            return null;
          },

          /**
           * 清除缓存
           */
          clearCache: () => {
            set((state) => {
              state.cache.documents.clear();
              state.cache.chunks.clear();
              state.cache.entities.clear();
              state.cache.searchResults.clear();
              state.cache.stats = {
                hits: 0,
                misses: 0,
                size: 0,
              };
            });
          },

          /**
           * 检查缓存是否过期
           */
          isCacheExpired: (timestamp) => {
            const { cache } = get();
            return Date.now() - timestamp > cache.config.maxAge;
          },

          /**
           * 清理过期缓存
           */
          cleanupExpiredCache: () => {
            set((state) => {
              const now = Date.now();
              const maxAge = state.cache.config.maxAge;
              
              // 清理搜索结果缓存
              for (const [key, value] of state.cache.searchResults.entries()) {
                if (now - value.timestamp > maxAge) {
                  state.cache.searchResults.delete(key);
                }
              }
              
              // 清理其他缓存（如果需要）
              // ...
              
              // 更新缓存大小
              state.cache.stats.size = 
                state.cache.documents.size +
                state.cache.chunks.size +
                state.cache.entities.size +
                state.cache.searchResults.size;
            });
          },

          /**
           * 检查缓存大小并清理
           */
          ensureCacheSize: () => {
            set((state) => {
              const maxSize = state.cache.config.maxSize;
              const currentSize = 
                state.cache.documents.size +
                state.cache.chunks.size +
                state.cache.entities.size +
                state.cache.searchResults.size;
              
              if (currentSize > maxSize) {
                // 清理搜索结果缓存（最易过期）
                state.cache.searchResults.clear();
                
                // 如果仍然超过大小，清理其他缓存
                if (
                  state.cache.documents.size +
                  state.cache.chunks.size +
                  state.cache.entities.size > maxSize
                ) {
                  // 这里可以实现更复杂的缓存清理策略
                  // 例如：清理最旧的缓存条目
                  // 简化起见，这里只清理部分缓存
                  state.cache.entities.clear();
                }
              }
              
              // 更新缓存大小
              state.cache.stats.size = 
                state.cache.documents.size +
                state.cache.chunks.size +
                state.cache.entities.size +
                state.cache.searchResults.size;
            });
          },

          /**
           * 获取缓存统计信息
           */
          getCacheStats: () => {
            return get().cache.stats;
          },

          /**
           * 重置缓存统计信息
           */
          resetCacheStats: () => {
            set((state) => {
              state.cache.stats = {
                hits: 0,
                misses: 0,
                size: 
                  state.cache.documents.size +
                  state.cache.chunks.size +
                  state.cache.entities.size +
                  state.cache.searchResults.size,
              };
            });
          },

          // ==================== 工具方法 ====================

          /**
           * 获取选中的文档对象
           */
          getSelectedDocumentsData: () => {
            const state = get();
            return state.documents.filter((d) =>
              state.selectedDocuments.includes(d.id)
            );
          },

          /**
           * 获取选中的片段对象
           */
          getSelectedChunksData: () => {
            const state = get();
            return state.chunks.filter((c) =>
              state.selectedChunks.includes(c.id)
            );
          },

          /**
           * 检查是否有选中项
           */
          hasSelection: () => {
            const state = get();
            return (
              state.selectedDocuments.length > 0 ||
              state.selectedChunks.length > 0 ||
              state.selectedEntities.length > 0
            );
          },

          /**
           * 清除所有选择
           */
          clearAllSelections: () => {
            set((state) => {
              state.selectedDocuments = [];
              state.selectedChunks = [];
              state.selectedEntities = [];
            });
          },

          // ==================== 批量操作 ====================

          /**
           * 开始批量操作
           */
          startBatchOperation: (operation) => {
            set((state) => {
              state.batchOperation = operation;
              state.batchProgress = 0;
              state.batchResults = [];
            });
          },

          /**
           * 更新批量操作进度
           */
          updateBatchProgress: (progress, results) => {
            set((state) => {
              state.batchProgress = progress;
              if (results) {
                state.batchResults = results;
              }
            });
          },

          /**
           * 结束批量操作
           */
          endBatchOperation: () => {
            set((state) => {
              state.batchOperation = null;
              state.batchProgress = 0;
            });
          },

          // ==================== 处理队列 ====================

          /**
           * 添加到处理队列
           */
          addToProcessingQueue: (task) => {
            set((state) => {
              state.processingQueue.push({
                id: Date.now(),
                ...task,
                status: 'pending',
              });
            });
          },

          /**
           * 更新处理队列任务
           */
          updateProcessingTask: (taskId, updates) => {
            set((state) => {
              const task = state.processingQueue.find((t) => t.id === taskId);
              if (task) {
                Object.assign(task, updates);
              }
            });
          },

          /**
           * 从处理队列移除
           */
          removeFromProcessingQueue: (taskId) => {
            set((state) => {
              state.processingQueue = state.processingQueue.filter(
                (t) => t.id !== taskId
              );
            });
          },

          /**
           * 清空处理队列
           */
          clearProcessingQueue: () => {
            set((state) => {
              state.processingQueue = [];
              state.isProcessing = false;
              state.processingProgress = 0;
            });
          },

          /**
           * 设置处理状态
           */
          setProcessing: (isProcessing, progress = 0) => {
            set((state) => {
              state.isProcessing = isProcessing;
              state.processingProgress = progress;
            });
          },

          /**
           * 开始处理队列
           */
          startProcessing: () => {
            set((state) => {
              state.isProcessing = true;
            });
          },

          /**
           * 暂停处理
           */
          pauseProcessing: () => {
            set((state) => {
              state.isProcessing = false;
            });
          },

          /**
           * 恢复处理
           */
          resumeProcessing: () => {
            set((state) => {
              state.isProcessing = true;
            });
          },

          // ==================== 搜索历史 ====================

          /**
           * 添加搜索历史
           */
          addSearchHistory: (query) => {
            set((state) => {
              if (!query.trim()) return;
              // 避免重复
              const filtered = state.searchHistory.filter((h) => h !== query);
              state.searchHistory = [query, ...filtered].slice(0, 20);
            });
          },

          /**
           * 清空搜索历史
           */
          clearSearchHistory: () => {
            set((state) => {
              state.searchHistory = [];
            });
          },

          /**
           * 删除单条搜索历史
           */
          removeSearchHistory: (query) => {
            set((state) => {
              state.searchHistory = state.searchHistory.filter((h) => h !== query);
            });
          },

          /**
           * 设置搜索建议
           */
          setSearchSuggestions: (suggestions) => {
            set((state) => {
              state.searchSuggestions = suggestions;
            });
          },

          // ==================== 消息通知 ====================

          /**
           * 添加通知
           */
          addNotification: (notification) => {
            set((state) => {
              state.notifications.push({
                id: Date.now(),
                timestamp: Date.now(),
                ...notification,
              });
            });
          },

          /**
           * 移除通知
           */
          removeNotification: (notificationId) => {
            set((state) => {
              state.notifications = state.notifications.filter(
                (n) => n.id !== notificationId
              );
            });
          },

          /**
           * 清空通知
           */
          clearNotifications: () => {
            set((state) => {
              state.notifications = [];
            });
          },

          /**
           * 重置状态
           */
          reset: () => {
            set((state) => {
              Object.assign(state, initialState);
            });
          },

          /**
           * 获取状态快照
           */
          getSnapshot: () => {
            return get();
          },

          // ==================== 层级操作 ====================

          /**
           * 设置当前层级
           */
          setHierarchyLevel: (level) => {
            set((state) => {
              state.currentHierarchyLevel = level;
            });
          },

          /**
           * 缓存层级数据
           */
          cacheHierarchyData: (level, key, data) => {
            set((state) => {
              state.hierarchyData[level] = { ...state.hierarchyData[level], [key]: data };
            });
          },

          /**
           * 添加下钻路径
           */
          pushDrillDown: (node) => {
            set((state) => {
              state.drillDownPath = [...state.drillDownPath, node];
            });
          },

          /**
           * 移除下钻路径
           */
          popDrillDown: () => {
            set((state) => {
              state.drillDownPath = state.drillDownPath.slice(0, -1);
            });
          },

          /**
           * 清空下钻路径
           */
          clearDrillDownPath: () => {
            set((state) => {
              state.drillDownPath = [];
            });
          },

          /**
           * 获取当前层级数据
           */
          getCurrentLevelData: (key) => {
            const { currentHierarchyLevel, hierarchyData, currentKnowledgeBase } = get();
            const levelData = hierarchyData[currentHierarchyLevel];
            return levelData?.[key] || levelData?.[currentKnowledgeBase?.id];
          },

          // ============================================================================
          // 层级视图逻辑修复 - 新增层级状态管理 Actions
          // 任务编号: Phase3-Week10
          // ============================================================================

          /**
           * 设置选中文档
           */
          setHierarchySelectedDocument: (documentId) => {
            set((state) => {
              state.hierarchySelection.selectedDocumentId = documentId;
              // 切换文档时清空已选片段
              state.hierarchySelection.selectedChunkId = null;
              state.hierarchyChunks = [];
              state.hierarchyChunksTotal = 0;
            });
          },

          /**
           * 设置选中片段
           */
          setHierarchySelectedChunk: (chunkId) => {
            set((state) => {
              state.hierarchySelection.selectedChunkId = chunkId;
            });
          },

          /**
           * 清除层级选择
           */
          clearHierarchySelection: () => {
            set((state) => {
              state.hierarchySelection.selectedDocumentId = null;
              state.hierarchySelection.selectedChunkId = null;
              state.hierarchyChunks = [];
              state.hierarchyChunksTotal = 0;
              state.hierarchyEntities = [];
              state.hierarchyEntitiesTotal = 0;
            });
          },

          /**
           * 设置层级文档列表
           */
          setHierarchyDocuments: (documents, total) => {
            set((state) => {
              state.hierarchyDocuments = documents;
              state.hierarchyDocumentsTotal = total;
            });
          },

          /**
           * 设置层级文档加载状态
           */
          setHierarchyDocumentsLoading: (loading) => {
            set((state) => {
              state.hierarchyDocumentsLoading = loading;
            });
          },

          /**
           * 设置层级文档错误
           */
          setHierarchyDocumentsError: (error) => {
            set((state) => {
              state.hierarchyDocumentsError = error;
            });
          },

          /**
           * 设置层级片段列表
           */
          setHierarchyChunks: (chunks, total) => {
            set((state) => {
              state.hierarchyChunks = chunks;
              state.hierarchyChunksTotal = total;
            });
          },

          /**
           * 设置层级片段加载状态
           */
          setHierarchyChunksLoading: (loading) => {
            set((state) => {
              state.hierarchyChunksLoading = loading;
            });
          },

          /**
           * 设置层级片段错误
           */
          setHierarchyChunksError: (error) => {
            set((state) => {
              state.hierarchyChunksError = error;
            });
          },

          /**
           * 设置层级实体列表
           */
          setHierarchyEntities: (entities, total) => {
            set((state) => {
              state.hierarchyEntities = entities;
              state.hierarchyEntitiesTotal = total;
            });
          },

          /**
           * 设置层级实体加载状态
           */
          setHierarchyEntitiesLoading: (loading) => {
            set((state) => {
              state.hierarchyEntitiesLoading = loading;
            });
          },

          /**
           * 设置层级实体错误
           */
          setHierarchyEntitiesError: (error) => {
            set((state) => {
              state.hierarchyEntitiesError = error;
            });
          },

          /**
           * 设置层级统计数据
           */
          setHierarchyStats: (level, stats) => {
            set((state) => {
              state.hierarchyStats[level] = stats;
            });
          },

          /**
           * 设置层级视图模式
           */
          setHierarchyViewMode: (mode) => {
            set((state) => {
              state.hierarchyViewMode = mode;
            });
          },
        }))
      ),
      {
        name: 'knowledge-store',
        partialize: (state) => ({
          // 只持久化这些字段
          currentKnowledgeBase: state.currentKnowledgeBase,
          documentFilters: state.documentFilters,
          chunkFilters: state.chunkFilters,
          entityFilters: state.entityFilters,
          viewMode: state.viewMode,
          sidebarCollapsed: state.sidebarCollapsed,
          activeTab: state.activeTab,
          documentsPageSize: state.documentsPageSize,
          searchHistory: state.searchHistory,
          currentHierarchyLevel: state.currentHierarchyLevel,
        }),
      }
    ),
    {
      name: 'KnowledgeStore',
    }
  )
);

export default useKnowledgeStore;
