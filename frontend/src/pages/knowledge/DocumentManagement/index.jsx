/**
 * 文档管理页面
 *
 * 知识库文档管理主页面，整合所有新组件
 */

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiGrid, FiList, FiFilter, FiDownload, FiTrash2, FiFile, FiLoader, FiZap } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { EnhancedBatchOperations } from '../../../components/Knowledge/EnhancedBatchOperations';
import ProcessingDocumentsPanel from '../../../components/Knowledge/ProcessingDocumentsPanel';
import ProcessingFlowPanel from '../../../components/Knowledge/ProcessingFlowPanel';
import { VirtualListEnhanced } from '../../../components/UI';
import DocumentCard from '../../../components/Knowledge/DocumentCard';
import DocumentActions from '../../../components/Knowledge/DocumentActions';
import UploadButton from '../../../components/Knowledge/UploadButton';
import SmartSearch from '../../../components/Knowledge/SmartSearch/SmartSearch';
import { message } from '../../../components/UI/Message/Message';
import {
  loadDocumentsAsync,
  getDocumentLoadStatus,
  uploadDocument,
  getDocument,
  deleteDocument,
  downloadDocument,
  getDocumentChunks,
  processDocument,
  batchProcessDocuments,
  getUnprocessedDocuments,
  getProcessingStatus,
  getKnowledgeBaseProcessingStatus,
  getDocumentProcessingProgress,
  extractChunkEntities,
  aggregateDocumentEntities,
  alignKnowledgeBaseEntities,
  searchDocuments,
  getKnowledgeBases,
  listDocuments,
  getDocumentChunkStats,
  rechunkDocument
} from '../../../utils/api/knowledgeApi';
import RechunkDialog from '../../../components/Knowledge/RechunkDialog';
import websocketService from '../../../services/websocketService';
import './styles.css';

/**
 * 视图模式
 */
const VIEW_MODES = {
  LIST: 'list',
  GRID: 'grid',
};

/**
 * 排序选项
 */
const SORT_OPTIONS = [
  { value: 'createdAt-desc', label: '最新上传' },
  { value: 'createdAt-asc', label: '最早上传' },
  { value: 'title-asc', label: '名称 A-Z' },
  { value: 'title-desc', label: '名称 Z-A' },
  { value: 'size-desc', label: '大小 大→小' },
  { value: 'size-asc', label: '大小 小→大' },
];

/**
 * 过滤器选项
 * 支持细粒度的文档状态筛选
 */
const FILTER_OPTIONS = [
  { value: 'all', label: '全部文档' },
  { value: 'idle', label: '待处理' },
  { value: 'pending', label: '待处理' },
  { value: 'queued', label: '排队中' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' },
  { value: 'error', label: '错误' },
  // 细粒度筛选
  { value: 'text_extracted', label: '已提取文本' },
  { value: 'chunked', label: '已切片' },
  { value: 'entity_extracted', label: '已识别实体' },
  { value: 'vectorized', label: '已向量化' },
  { value: 'graph_built', label: '已构建图谱' }
];

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 记忆化文档卡片组件
 * 用于优化虚拟列表性能，避免不必要的重渲染
 */
const MemoDocumentCard = React.memo(({
  document,
  selectedDocuments,
  onSelect,
  onClick,
  onProcessingFlow,
  viewMode
}) => {
  const isSelected = selectedDocuments.some(id => String(id) === String(document.id));

  const handleSelect = useCallback(() => {
    onSelect(document.id);
  }, [onSelect, document.id]);

  const handleClick = useCallback(() => {
    onClick(document);
  }, [onClick, document]);

  const handleProcessingFlow = useCallback(() => {
    onProcessingFlow(document.id);
  }, [onProcessingFlow, document.id]);

  return (
    <DocumentCard
      document={document}
      isSelected={isSelected}
      onSelect={handleSelect}
      onClick={handleClick}
      onProcessingFlow={handleProcessingFlow}
      viewMode={viewMode}
    />
  );
});

MemoDocumentCard.displayName = 'MemoDocumentCard';

/**
 * 文档管理页面
 */
const DocumentManagement = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  
  const {
    currentKnowledgeBase,
    documents,
    selectedDocuments,
    documentFilters,
    documentsLoading,
    documentsError,
    documentsTotal,
    documentsPage,
    documentsPageSize,
    setDocuments,
    setDocumentsLoading,
    setDocumentsError,
    toggleDocumentSelection,
    setDocumentsPage,
    setDocumentFilters,
    addSearchHistory,
    setCurrentKnowledgeBase,
    selectAllDocuments,
    clearSelection,
  } = useKnowledgeStore();

  // 本地状态
  const [viewMode, setViewMode] = useState(VIEW_MODES.LIST);
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('createdAt-desc');
  const [filterStatus, setFilterStatus] = useState('all');
  
  // 向量化配置状态
  const [vectorizationConfig, setVectorizationConfig] = useState({
    chunkSize: 500,
    chunkOverlap: 50,
    embeddingModel: 'default',
    batchSize: 10,
    autoProcess: false
  });
  
  // 向量化设置模态框
  const [showVectorizationConfig, setShowVectorizationConfig] = useState(false);

  // 处理流程面板状态
  const [showProcessingFlow, setShowProcessingFlow] = useState(false);
  const [documentProcessingStatus, setDocumentProcessingStatus] = useState({});
  const [processingFlowLoading, setProcessingFlowLoading] = useState(false);

  // 重新切片对话框状态
  const [showRechunkDialog, setShowRechunkDialog] = useState(false);
  const [rechunkDocumentId, setRechunkDocumentId] = useState(null);
  const [rechunkDocumentTitle, setRechunkDocumentTitle] = useState('');

  // 文档详情状态
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [documentDetailLoading, setDocumentDetailLoading] = useState(false);
  const [documentChunks, setDocumentChunks] = useState([]);
  const [chunksLoading, setChunksLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('info'); // 'info', 'content', 'chunks'

  // 请求取消控制器
  const abortControllersRef = useRef(new Map());

  // 批量处理状态
  const [, setBatchProcessing] = useState(false);
  const [unprocessedCount, setUnprocessedCount] = useState(0);
  const [showBatchProcessModal, setShowBatchProcessModal] = useState(false);
  const [batchProcessResult, setBatchProcessResult] = useState(null);

  // 实时处理进度状态
  const [processingStatus, setProcessingStatus] = useState(null);
  const [showProgressPanel, setShowProgressPanel] = useState(false);
  
  // 异步文档加载状态
  const loadTaskId = useRef(null);
  const [, setLoadTaskStatus] = useState(null);
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadMessage, setLoadMessage] = useState('');
  const websocketConnected = useRef(false);
  const loadProgressUnsubscribe = useRef(null);
  const [processingDocuments, setProcessingDocuments] = useState(new Map());
  const [processingProgress, setProcessingProgress] = useState(new Map());

  /**
   * 获取文档处理状态
   * 使用 processing_status 单字段判断文档状态
   * 支持向量化状态和实体识别状态
   */
  const getVectorizationStatus = (doc) => {
    const status = doc.document_metadata?.processing_status;
    // 根据 processing_status 判断状态
    if (status === 'completed') return 'vectorized';
    if (status === 'entity_processing') return 'entity_processing';
    if (status === 'entity_aggregating') return 'entity_aggregating';
    if (status === 'entity_aligning') return 'entity_aligning';
    if (status === 'entity_completed') return 'entity_completed';
    if (status === 'text_extracted') return 'text_extracted';
    if (status === 'text_extraction_failed') return 'error';
    if (status === 'chunked') return 'chunked';
    if (status === 'chunking_failed') return 'error';
    if (status === 'entities_extracted') return 'entities_extracted';
    if (status === 'entity_extraction_failed') return 'error';
    if (status === 'vectorized') return 'vectorized';
    if (status === 'vectorization_failed') return 'error';
    if (status === 'graph_built') return 'graph_built';
    if (status === 'graph_building_failed') return 'error';
    if (status === 'failed') return 'error';
    if (status === 'processing' || status === 'queued') return 'processing';
    if (status === 'idle' || status === 'pending' || !status) return 'pending';
    return 'pending';
  };

  /**
   * 获取文档列表 - 使用异步API
   */
  const fetchDocuments = useCallback(async () => {
    if (!currentKnowledgeBase) {
      return;
    }

    setDocumentsLoading(true);
    setDocumentsError(null);
    setLoadProgress(0);
    setLoadMessage('准备加载文档...');

    try {
      // 检查是否有搜索关键词
      const searchQuery = documentFilters?.search?.trim();

      if (searchQuery) {
        // 搜索模式：使用同步搜索API
        setLoadMessage('搜索文档...');
        const searchResponse = await searchDocuments(
          searchQuery,
          documentsPageSize,
          currentKnowledgeBase.id,
          sortBy.split('-')[0] || 'relevance',
          sortBy.split('-')[1] || 'desc'
        );

        // 搜索API可能直接返回数组或包含results的对象
        const searchResults = Array.isArray(searchResponse) ? searchResponse : (searchResponse.results || []);
        // 转换搜索结果
        const documents = searchResults.map(result => ({
          id: String(result.id || result.document_id),
          title: result.title,
          fileType: result.file_type || 'unknown',
          size: result.metadata?.file_size || 0,
          createdAt: result.created_at || result.metadata?.created_at,
          // 使用 processing_status 判断状态，completed 表示已向量化
          vectorizationStatus: result.metadata?.processing_status === 'completed' ? 'vectorized' : (result.metadata?.processing_status || 'pending'),
          score: result.score,
        }));
        const total = Array.isArray(searchResponse) ? searchResults.length : (searchResponse.total || documents.length);
        
        setDocuments(documents, total, documentsPage > 1);
        setLoadProgress(100);
        setLoadMessage('搜索完成');
      } else {
        // 普通列表模式：使用异步API
        const skip = (documentsPage - 1) * documentsPageSize;
        // 使用 processing_status 单字段进行筛选
        // 支持细粒度的状态筛选
        const processingStatusMap = {
          'all': null,
          'idle': 'idle',
          'pending': 'pending',
          'queued': 'queued',
          'processing': 'processing',
          'completed': 'completed',
          'failed': 'failed',
          'error': 'failed',
          // 细粒度筛选 - 这些需要特殊处理
          'text_extracted': null,  // 需要后端支持
          'chunked': null,       // 需要后端支持
          'entity_extracted': null, // 需要后端支持
          'vectorized': 'completed',
          'graph_built': null       // 需要后端支持
        };
        const processingStatus = processingStatusMap[filterStatus] || null;
        
        // 连接WebSocket
        setLoadMessage('连接进度服务...');
        try {
          await websocketService.connect();
          websocketConnected.current = true;
        } catch (wsError) {
          console.warn('[文档加载] WebSocket连接失败，将使用轮询模式:', wsError);
          websocketConnected.current = false;
        }

        // 注册WebSocket进度监听
        if (websocketConnected.current) {
          loadProgressUnsubscribe.current = websocketService.on('document_load_progress', (data) => {
            if (data && data.task_id === loadTaskId.current) {
              setLoadProgress(data.progress || 0);
              setLoadMessage(data.current_message || '');
              setLoadTaskStatus(data.status);

              // 任务完成
              if (data.status === 'completed') {
              } else if (data.status === 'failed') {
                message.error({ content: `文档加载失败: ${data.error || '未知错误'}` });
              }
            }
          });
        }

        // 调用异步加载API
        setLoadMessage('启动异步加载任务...');
        try {
          const response = await loadDocumentsAsync(
            currentKnowledgeBase.id,
            skip,
            documentsPageSize,
            {
              // 使用 processing_status 单字段进行筛选，不再传递 is_vectorized
              processing_status: processingStatus,
              sort_by: sortBy.split('-')[0] || 'created_at',
              sort_order: sortBy.split('-')[1] || 'desc'
            }
          );


          if (response.success && response.task_id) {
            loadTaskId.current = response.task_id;
            setLoadMessage(response.message || '任务已启动');
            
            // 如果WebSocket未连接，使用轮询模式
            if (!websocketConnected.current) {
              setLoadMessage('使用轮询模式监控进度...');
              await pollLoadTaskStatus(response.task_id);
            } else {
              // WebSocket模式：等待任务完成
              await waitForLoadTaskComplete(response.task_id);
            }
          } else {
            throw new Error(response.message || '启动任务失败');
          }
        } catch (asyncError) {
          console.error('[文档加载] 异步加载失败，使用同步API:', asyncError);
          setLoadMessage('使用同步模式加载文档...');
          // 使用同步API加载文档列表
          try {
            // 计算筛选参数
            let isVectorized = null;
            let metadataFilter = null;
            
            // 处理细粒度筛选
            if (['text_extracted', 'chunked', 'entity_extracted', 'graph_built'].includes(filterStatus)) {
              metadataFilter = { [filterStatus]: true };
            } else if (filterStatus === 'vectorized') {
              isVectorized = 1;
            }
            
            const response = await listDocuments(
              skip,
              documentsPageSize,
              currentKnowledgeBase?.id,
              isVectorized,
              processingStatus,
              metadataFilter
            );
            
            // 处理listDocuments的返回格式
            const documentsData = Array.isArray(response) ? response : (response.documents || response.items || []);
            const total = response.total || documentsData.length;
            
            // 转换文档数据
            const documents = documentsData.map(doc => ({
              id: String(doc.id),
              title: doc.title,
              fileType: doc.file_type || 'unknown',
              size: doc.document_metadata?.file_size || 0,
              createdAt: doc.created_at,
              document_metadata: doc.document_metadata || {},
              vectorizationStatus: getVectorizationStatus(doc),
            }));
            
            // 客户端排序
            const sortedDocuments = [...documents].sort((a, b) => {
              const [field, order] = sortBy.split('-');
              const multiplier = order === 'desc' ? -1 : 1;

              if (field === 'createdAt') {
                return multiplier * (new Date(a.createdAt) - new Date(b.createdAt));
              }
              if (field === 'title') {
                return multiplier * a.title.localeCompare(b.title);
              }
              if (field === 'size') {
                return multiplier * (a.size - b.size);
              }
              return 0;
            });

            // 后端已经根据processing_status筛选，前端不需要再次过滤
            setDocuments(sortedDocuments, total, documentsPage > 1);
            setLoadProgress(100);
            setLoadMessage('加载完成');
          } catch (syncError) {
            console.error('[文档加载] 同步API加载失败:', syncError);
            throw new Error('加载文档失败，请刷新页面重试');
          }
        }
      }
    } catch (error) {
      console.error('[fetchDocuments] 获取文档列表失败:', error);
      setDocumentsError(error.message);
      message.error({ content: '获取文档列表失败：' + error.message });
    } finally {
      setDocumentsLoading(false);
    }
  }, [
    currentKnowledgeBase,
    documentsPage,
    documentsPageSize,
    documentFilters,
    sortBy,
    filterStatus,
    setDocuments,
    setDocumentsLoading,
    setDocumentsError,
  ]);

  /**
   * 轮询加载任务状态（WebSocket不可用时的备用方案）
   */
  const pollLoadTaskStatus = useCallback(async (taskId) => {
    const maxPolls = 60; // 最多轮询60次（每秒一次）
    let pollCount = 0;

    const poll = async () => {
      try {
        const status = await getDocumentLoadStatus(taskId);

        setLoadProgress(status.progress || 0);
        setLoadMessage(status.current_message || '');
        setLoadTaskStatus(status.status);

        if (status.status === 'completed' && status.documents) {
          // 转换文档数据
          const documents = status.documents.map(doc => ({
            id: String(doc.id),
            title: doc.title,
            fileType: doc.file_type || 'unknown',
            size: doc.document_metadata?.file_size || 0,
            createdAt: doc.created_at,
            document_metadata: doc.document_metadata || {},
            vectorizationStatus: getVectorizationStatus(doc),
          }));
          
          // 客户端排序
          const sortedDocuments = [...documents].sort((a, b) => {
            const [field, order] = sortBy.split('-');
            const multiplier = order === 'desc' ? -1 : 1;

            if (field === 'createdAt') {
              return multiplier * (new Date(a.createdAt) - new Date(b.createdAt));
            }
            if (field === 'title') {
              return multiplier * a.title.localeCompare(b.title);
            }
            if (field === 'size') {
              return multiplier * (a.size - b.size);
            }
            return 0;
          });

          // 异步加载任务已经根据processing_status筛选，前端不需要再次过滤
          setDocuments(sortedDocuments, status.total || documents.length, documentsPage > 1);
          setLoadProgress(100);
          setLoadMessage('加载完成');
          return;
        }

        if (status.status === 'failed') {
          message.error({ content: `文档加载失败: ${status.error || '未知错误'}` });
          return;
        }

        // 继续轮询 - 支持 pending 和 loading 状态
        pollCount++;
        if (pollCount < maxPolls && (status.status === 'loading' || status.status === 'pending')) {
          setTimeout(poll, 1000);
        } else if (pollCount >= maxPolls) {
          message.warning({ content: '任务轮询超时，请刷新页面查看最新状态' });
        }
      } catch (error) {
        console.error('[文档加载] 轮询失败:', error);
        // 检查是否是404错误（任务不存在）
        if (error.message && error.message.includes('404') || error.message && error.message.includes('任务不存在')) {
          console.info('[文档加载] 任务不存在，使用同步API加载文档');
          setLoadMessage('使用备用方法加载文档...');
          // 使用同步API加载文档列表
          try {
            const skip = (documentsPage - 1) * documentsPageSize;
            
            // 支持细粒度的状态筛选
            const processingStatusMap = {
              'all': null,
              'idle': 'idle',
              'pending': 'pending',
              'queued': 'queued',
              'processing': 'processing',
              'completed': 'completed',
              'failed': 'failed',
              'error': 'failed',
              // 细粒度筛选 - 这些需要特殊处理
              'text_extracted': null,
              'chunked': null,
              'entity_extracted': null,
              'vectorized': 'completed',
              'graph_built': null
            };
            const processingStatus = processingStatusMap[filterStatus] || null;
            
            // 计算筛选参数
            let isVectorized = null;
            let metadataFilter = null;
            
            // 处理细粒度筛选
            if (['text_extracted', 'chunked', 'entity_extracted', 'graph_built'].includes(filterStatus)) {
              metadataFilter = { [filterStatus]: true };
            } else if (filterStatus === 'vectorized') {
              isVectorized = 1;
            }

            const response = await listDocuments(
              skip,
              documentsPageSize,
              currentKnowledgeBase?.id,
              isVectorized,
              processingStatus,
              metadataFilter
            );
            
            // 处理listDocuments的返回格式
            const documentsData = Array.isArray(response) ? response : (response.documents || response.items || []);
            const total = response.total || documentsData.length;
            
            // 转换文档数据
            const documents = documentsData.map(doc => ({
              id: String(doc.id),
              title: doc.title,
              fileType: doc.file_type || 'unknown',
              size: doc.document_metadata?.file_size || 0,
              createdAt: doc.created_at,
              document_metadata: doc.document_metadata || {},
              vectorizationStatus: getVectorizationStatus(doc),
            }));
            
            // 客户端排序
            const sortedDocuments = [...documents].sort((a, b) => {
              const [field, order] = sortBy.split('-');
              const multiplier = order === 'desc' ? -1 : 1;

              if (field === 'createdAt') {
                return multiplier * (new Date(a.createdAt) - new Date(b.createdAt));
              }
              if (field === 'title') {
                return multiplier * a.title.localeCompare(b.title);
              }
              if (field === 'size') {
                return multiplier * (a.size - b.size);
              }
              return 0;
            });

            // 后端已经根据processing_status筛选，前端不需要再次过滤
            setDocuments(sortedDocuments, total, documentsPage > 1);
            setLoadProgress(100);
            setLoadMessage('加载完成');
          } catch (syncError) {
            console.error('[文档加载] 同步API加载失败:', syncError);
            message.error({ content: '加载文档失败，请刷新页面重试' });
          }
          return;
        }
        // 其他错误继续重试
        pollCount++;
        if (pollCount < maxPolls) {
          setTimeout(poll, 2000); // 出错后延迟2秒重试
        } else {
          message.error({ content: '获取任务状态失败' });
        }
      }
    };

    await poll();
  }, [setDocuments, sortBy, filterStatus, documentsPage, currentKnowledgeBase, documentsPageSize]);

  /**
   * 轮询加载任务状态（WebSocket不可用时的备用方案）
   */
  const waitForLoadTaskComplete = useCallback(async (taskId) => {
    const maxWait = 60000; // 最多等待60秒
    const startTime = Date.now();
    
    const checkComplete = async () => {
      try {
        const status = await getDocumentLoadStatus(taskId);
        
        if (status.status === 'completed' && status.documents) {
          // 转换文档数据
          const documents = status.documents.map(doc => ({
            id: String(doc.id),
            title: doc.title,
            fileType: doc.file_type || 'unknown',
            size: doc.document_metadata?.file_size || 0,
            createdAt: doc.created_at,
            document_metadata: doc.document_metadata || {},
            vectorizationStatus: getVectorizationStatus(doc),
          }));
          
          // 客户端排序
          const sortedDocuments = [...documents].sort((a, b) => {
            const [field, order] = sortBy.split('-');
            const multiplier = order === 'desc' ? -1 : 1;

            if (field === 'createdAt') {
              return multiplier * (new Date(a.createdAt) - new Date(b.createdAt));
            }
            if (field === 'title') {
              return multiplier * a.title.localeCompare(b.title);
            }
            if (field === 'size') {
              return multiplier * (a.size - b.size);
            }
            return 0;
          });

          // 异步加载任务已经根据processing_status筛选，前端不需要再次过滤
          setDocuments(sortedDocuments, status.total || documents.length, documentsPage > 1);
          setLoadProgress(100);
          setLoadMessage('加载完成');
          return;
        }

        if (status.status === 'failed') {
          message.error({ content: `文档加载失败: ${status.error || '未知错误'}` });
          return;
        }

        // 继续等待 - 支持 pending 和 loading 状态
        if (Date.now() - startTime < maxWait && (status.status === 'loading' || status.status === 'pending')) {
          setTimeout(checkComplete, 500);
        } else if (Date.now() - startTime >= maxWait) {
          message.warning({ content: '任务等待超时，请刷新页面查看最新状态' });
        } else {
          // 其他未知状态，使用同步API加载
          console.warn('[文档加载] 任务状态未知:', status.status);
          message.warning({ content: '任务状态异常，使用备用方法加载文档' });
          try {
            const skip = (documentsPage - 1) * documentsPageSize;
            const response = await listDocuments(skip, documentsPageSize, currentKnowledgeBase?.id, null, null, null);
            const documentsData = Array.isArray(response) ? response : (response.documents || response.items || []);
            const total = response.total || documentsData.length;
            const documents = documentsData.map(doc => ({
              id: String(doc.id),
              title: doc.title,
              fileType: doc.file_type || 'unknown',
              size: doc.document_metadata?.file_size || 0,
              createdAt: doc.created_at,
              document_metadata: doc.document_metadata || {},
              vectorizationStatus: getVectorizationStatus(doc),
            }));
            const sortedDocuments = [...documents].sort((a, b) => {
              const [field, order] = sortBy.split('-');
              const multiplier = order === 'desc' ? -1 : 1;
              if (field === 'createdAt') {
                return multiplier * (new Date(a.createdAt) - new Date(b.createdAt));
              }
              if (field === 'title') {
                return multiplier * a.title.localeCompare(b.title);
              }
              if (field === 'size') {
                return multiplier * (a.size - b.size);
              }
              return 0;
            });
            setDocuments(sortedDocuments, total, documentsPage > 1);
            setLoadProgress(100);
            setLoadMessage('加载完成');
          } catch (syncError) {
            console.error('[文档加载] 同步API加载失败:', syncError);
            message.error({ content: '加载文档失败，请刷新页面重试' });
          }
        }
      } catch (error) {
        console.error('[文档加载] 检查完成状态失败:', error);
        // 检查是否是404错误（任务不存在）
        if (error.message && error.message.includes('404') || error.message && error.message.includes('任务不存在')) {
          console.info('[文档加载] 任务不存在，使用同步API加载文档');
          setLoadMessage('使用备用方法加载文档...');
          // 使用同步API加载文档列表
          try {
            const skip = (documentsPage - 1) * documentsPageSize;
            
            // 支持细粒度的状态筛选
            const processingStatusMap = {
              'all': null,
              'idle': 'idle',
              'pending': 'pending',
              'queued': 'queued',
              'processing': 'processing',
              'completed': 'completed',
              'failed': 'failed',
              'error': 'failed',
              // 细粒度筛选 - 这些需要特殊处理
              'text_extracted': null,
              'chunked': null,
              'entity_extracted': null,
              'vectorized': 'completed',
              'graph_built': null
            };
            const processingStatus = processingStatusMap[filterStatus] || null;
            
            // 计算筛选参数
            let isVectorized = null;
            let metadataFilter = null;
            
            // 处理细粒度筛选
            if (['text_extracted', 'chunked', 'entity_extracted', 'graph_built'].includes(filterStatus)) {
              metadataFilter = { [filterStatus]: true };
            } else if (filterStatus === 'vectorized') {
              isVectorized = 1;
            }

            const response = await listDocuments(
              skip,
              documentsPageSize,
              currentKnowledgeBase?.id,
              isVectorized,
              processingStatus,
              metadataFilter
            );
            
            // 处理listDocuments的返回格式
            const documentsData = Array.isArray(response) ? response : (response.documents || response.items || []);
            const total = response.total || documentsData.length;
            
            // 转换文档数据
            const documents = documentsData.map(doc => ({
              id: String(doc.id),
              title: doc.title,
              fileType: doc.file_type || 'unknown',
              size: doc.document_metadata?.file_size || 0,
              createdAt: doc.created_at,
              document_metadata: doc.document_metadata || {},
              vectorizationStatus: getVectorizationStatus(doc),
            }));

            // 客户端排序
            const sortedDocuments = [...documents].sort((a, b) => {
              const [field, order] = sortBy.split('-');
              const multiplier = order === 'desc' ? -1 : 1;

              if (field === 'createdAt') {
                return multiplier * (new Date(a.createdAt) - new Date(b.createdAt));
              }
              if (field === 'title') {
                return multiplier * a.title.localeCompare(b.title);
              }
              if (field === 'size') {
                return multiplier * (a.size - b.size);
              }
              return 0;
            });

            // 后端已经根据processing_status筛选，前端不需要再次过滤
            setDocuments(sortedDocuments, total, documentsPage > 1);
            setLoadProgress(100);
            setLoadMessage('加载完成');
          } catch (syncError) {
            console.error('[文档加载] 同步API加载失败:', syncError);
            message.error({ content: '加载文档失败，请刷新页面重试' });
          }
          return;
        }
        // 其他错误继续重试，但增加延迟
        setTimeout(checkComplete, 2000);
      }
    };

    await checkComplete();
  }, [setDocuments, sortBy, filterStatus, documentsPage, currentKnowledgeBase, documentsPageSize]);

  /**
   * 等待加载任务完成（WebSocket模式）
   */
  useEffect(() => {
    return () => {
      if (loadProgressUnsubscribe.current) {
        loadProgressUnsubscribe.current();
        loadProgressUnsubscribe.current = null;
      }
    };
  }, []);

  // 初始加载和筛选变化时重新获取
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments, currentKnowledgeBase]);

  /**
   * 获取未处理文档数量
   */
  const fetchUnprocessedCount = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      const response = await getUnprocessedDocuments(currentKnowledgeBase.id);
      if (response.success) {
        setUnprocessedCount(response.total_unprocessed);
      }
    } catch (error) {
      console.error('获取未处理文档数量失败:', error);
    }
  }, [currentKnowledgeBase]);

  // 初始加载时获取未处理文档数量
  useEffect(() => {
    fetchUnprocessedCount();
  }, [fetchUnprocessedCount]);

  // 组件加载时清除搜索关键词
  useEffect(() => {
    if (documentFilters?.search) {
      setDocumentFilters({ search: '' });
    }
  }, []);

  /**
   * 加载知识库列表
   * 如果没有当前知识库，自动选择第一个
   */
  const loadKnowledgeBases = useCallback(async () => {
    // 如果已经有当前知识库，不需要重新加载
    if (currentKnowledgeBase) return;

    try {
      const response = await getKnowledgeBases(0, 10);
      const knowledgeBasesList = response.knowledge_bases || response;

      if (knowledgeBasesList.length > 0) {
        setCurrentKnowledgeBase(knowledgeBasesList[0]);
      } else {
        console.warn('[DocumentManagement] 没有可用的知识库');
      }
    } catch (error) {
      console.error('[DocumentManagement] 加载知识库列表失败:', error);
    }
  }, [currentKnowledgeBase, setCurrentKnowledgeBase]);

  // 组件加载时，如果没有当前知识库，加载知识库列表
  useEffect(() => {
    loadKnowledgeBases();
  }, [loadKnowledgeBases]);

  /**
   * 获取处理状态
   */
  const fetchProcessingStatus = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      const response = await getKnowledgeBaseProcessingStatus(currentKnowledgeBase.id);
      
      if (response.success) {
        setProcessingStatus(response);

        // 更新正在处理的文档Map - 合并后端返回的状态和前端本地状态
        setProcessingDocuments(prevDocs => {
          const newProcessingDocs = new Map(prevDocs);

          // 添加后端返回的处理中文档
          if (response.processing_documents && response.processing_documents.length > 0) {
            response.processing_documents.forEach(doc => {
              newProcessingDocs.set(doc.document_id, {
                id: doc.document_id,
                name: doc.document_name
              });
            });
          }

          return newProcessingDocs;
        });

        // 更新进度信息 - 保留本地进度，添加后端返回的进度
        setProcessingProgress(prevProgress => {
          const newProcessingProgress = new Map(prevProgress);

          // 为后端返回的处理中文档初始化进度
          if (response.processing_documents && response.processing_documents.length > 0) {
            response.processing_documents.forEach(doc => {
              if (!newProcessingProgress.has(doc.document_id)) {
                newProcessingProgress.set(doc.document_id, {
                  status: 'processing',
                  step_name: '处理中...',
                  progress_percentage: 0,
                  message: '文档正在处理中'
                });
              }
            });
          }

          return newProcessingProgress;
        });

        // 计算实际处理中的文档数量（包括前端本地添加的和后端返回的）
        const backendProcessingCount = response.processing_documents?.length || 0;
        const frontendProcessingCount = processingDocuments.size;
        const actualProcessingCount = Math.max(backendProcessingCount, frontendProcessingCount);

        // 如果有正在处理的文档，显示进度面板并获取详细进度
        const hasProcessing = actualProcessingCount > 0 ||
                             response.queue_status.processing_count > 0 ||
                             response.queue_status.queue_size > 0;
        if (hasProcessing) {
          setShowProgressPanel(true);

          // 获取每个处理中文档的详细进度
          if (response.processing_documents && response.processing_documents.length > 0) {
            response.processing_documents.forEach(doc => {
              fetchDocumentProgressDetail(doc.document_id);
            });
          }
        }
        // 注意：不再在这里关闭面板，面板关闭由用户手动控制或文档处理完成后自动关闭
        
        // 修正queue_status数据，确保与processing_documents一致
        if (actualProcessingCount > 0 && 
            (response.queue_status.processing_count === 0 && response.queue_status.queue_size === 0)) {
          // 如果processing_documents有数据但queue_status显示为0，修正queue_status
          const correctedStatus = {
            ...response,
            queue_status: {
              ...response.queue_status,
              processing_count: actualProcessingCount,
              queue_size: 0
            }
          };
          setProcessingStatus(correctedStatus);
        }

        // 更新未处理数量
        setUnprocessedCount(response.statistics.unprocessed_documents);
      } else {
        console.warn('[fetchProcessingStatus] 获取处理状态失败:', response);
      }
    } catch (error) {
      console.error('[fetchProcessingStatus] 获取处理状态失败:', error);
      // 只在开发环境显示详细错误，生产环境显示友好提示
      if (import.meta.env.DEV) {
        message.error({ content: `获取处理状态失败: ${error.message}` });
      } else {
        message.error({ content: '获取处理状态失败，请稍后重试' });
      }
    }
  }, [currentKnowledgeBase]);

  /**
   * 获取单个文档的详细进度
   */
  const fetchDocumentProgressDetail = useCallback(async (documentId) => {
    try {
      const progress = await getDocumentProcessingProgress(documentId);

      setProcessingProgress(prev => {
        const newProgress = new Map(prev);
        newProgress.set(documentId, {
          status: progress.status || 'processing',
          step_name: progress.step_name || progress.step || '处理中...',
          progress_percentage: progress.progress_percentage || progress.progress || 0,
          message: progress.message || '文档正在处理中',
          current_step: progress.current_step,
          total_steps: progress.total_steps,
          ...progress
        });
        return newProgress;
      });

      // 如果文档已完成或失败，5秒后从列表中移除
      if (progress.status === 'completed' || progress.status === 'failed') {
        setTimeout(() => {
          setProcessingDocuments(prev => {
            const newDocs = new Map(prev);
            newDocs.delete(documentId);
            return newDocs;
          });
          setProcessingProgress(prev => {
            const newProgress = new Map(prev);
            newProgress.delete(documentId);
            return newProgress;
          });

          // 如果没有更多处理中的文档，关闭面板
          setProcessingDocuments(currentDocs => {
            if (currentDocs.size <= 1) {  // <=1 因为当前文档还未删除
              setTimeout(() => setShowProgressPanel(false), 1000);
            }
            return currentDocs;
          });
        }, 5000);
      }
    } catch (error) {
      console.error(`[fetchDocumentProgressDetail] 获取文档 ${documentId} 进度失败:`, error);
      // 获取进度失败时，保持现有进度信息，不更新
      // 这样可以避免单个文档获取失败影响其他文档的进度显示
    }
  }, []);

  // 用户活动状态
  const [userActive, setUserActive] = useState(true);

  // 监听用户活动
  useEffect(() => {
    const handleUserActivity = () => {
      setUserActive(true);
      // 30秒无活动后标记为非活动
      setTimeout(() => {
        setUserActive(false);
      }, 30000);
    };

    // 绑定事件监听器
    window.addEventListener('mousemove', handleUserActivity);
    window.addEventListener('keydown', handleUserActivity);
    window.addEventListener('click', handleUserActivity);

    return () => {
      window.removeEventListener('mousemove', handleUserActivity);
      window.removeEventListener('keydown', handleUserActivity);
      window.removeEventListener('click', handleUserActivity);
    };
  }, []);

  // 轮询处理状态
  useEffect(() => {
    if (!currentKnowledgeBase) return;

    // 轮询间隔时间（毫秒） - 进一步增加间隔减少API压力
    const POLLING_INTERVALS = {
      IDLE: 180000,       // 无处理任务时：180秒（3分钟）
      NORMAL: 120000,     // 有处理任务时：120秒（2分钟）
      ACTIVE: 60000,       // 处理任务接近完成时：60秒（1分钟）
    };
    // 错误重试延迟（毫秒） - 大幅增加重试延迟
    const ERROR_RETRY_DELAY = 120000;  // 2分钟
    // 最大连续错误次数 - 进一步减少阈值
    const MAX_CONSECUTIVE_ERRORS = 2;
    
    let intervalId = null;
    let lastErrorTime = 0;
    let isProcessing = false;
    let consecutiveErrors = 0;
    let currentPollingInterval = POLLING_INTERVALS.NORMAL;
    let isMounted = true;

    // 安全的获取处理状态函数
    const safeFetchProcessingStatus = async () => {
      // 检查组件是否已卸载
      if (!isMounted) return;

      // 检查是否在错误重试期间
      if (lastErrorTime > 0 && (Date.now() - lastErrorTime) < ERROR_RETRY_DELAY) {
        console.log('[轮询处理状态] 在错误重试延迟期间，跳过本次轮询');
        return;
      }

      // 避免并发请求
      if (isProcessing) {
        console.log('[轮询处理状态] 上次请求仍在处理中，跳过本次轮询');
        return;
      }

      // 检查是否有处理任务或进度面板是否显示
      const hasProcessingTasks = processingStatus?.queue_status?.processing_count > 0 || 
                              processingStatus?.queue_status?.queue_size > 0 ||
                              processingDocuments.size > 0;

      // 根据处理状态和用户活动动态调整轮询间隔
      if (!userActive && !hasProcessingTasks) {
        // 用户不活动且无处理任务时，延长轮询间隔
        currentPollingInterval = POLLING_INTERVALS.IDLE;
      } else if (hasProcessingTasks) {
        // 有处理任务时，根据任务数量动态调整轮询间隔
        const totalTasks = (processingStatus?.queue_status?.processing_count || 0) + 
                          (processingStatus?.queue_status?.queue_size || 0) +
                          processingDocuments.size;
        if (totalTasks <= 2) {
          // 处理任务接近完成时，使用快速轮询间隔
          currentPollingInterval = POLLING_INTERVALS.ACTIVE;
        } else {
          // 正常处理任务时，使用正常轮询间隔
          currentPollingInterval = POLLING_INTERVALS.NORMAL;
        }
      } else {
        // 无处理任务但用户活动时，使用正常轮询间隔
        currentPollingInterval = POLLING_INTERVALS.NORMAL;
      }

      // 检查连续错误次数，超过阈值时暂停轮询
      if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
        console.warn('[轮询处理状态] 连续错误次数超过阈值，暂停轮询');
        // 暂停轮询后，设置一个定时器在一段时间后重试
        setTimeout(() => {
          if (isMounted) {
            console.log('[轮询处理状态] 暂停后重试，重置错误计数');
            consecutiveErrors = 0;
            lastErrorTime = 0;
            safeFetchProcessingStatus();
          }
        }, 300000); // 5分钟后重试
        return;
      }

      isProcessing = true;
      try {
        // 使用API工具的超时设置，避免与Promise.race冲突
        // 直接调用fetchProcessingStatus，API工具会处理超时
        await fetchProcessingStatus();
        
        // 重置错误时间和连续错误计数
        lastErrorTime = 0;
        consecutiveErrors = 0;
      } catch (error) {
        console.error('[轮询处理状态] 轮询失败:', error);
        console.error('[轮询处理状态] 错误详情:', {
          message: error.message,
          status: error.status,
          name: error.name,
          stack: error.stack
        });
        // 记录错误时间和增加连续错误计数
        lastErrorTime = Date.now();
        consecutiveErrors++;
        
        // 连续错误时增加轮询间隔
        if (consecutiveErrors > 0) {
          currentPollingInterval = POLLING_INTERVALS.NORMAL * (1 + consecutiveErrors * 1.5); // 增加倍数
        }
        
        // 如果是超时错误，显示警告但继续轮询
        if (error.message.includes('超时')) {
          console.warn('[轮询处理状态] API请求超时，将继续轮询');
        }
      } finally {
        isProcessing = false;
      }
    };

    // 立即获取一次处理状态（组件初始化时）
    safeFetchProcessingStatus();

    // 定时轮询 - 使用动态间隔
    const startPolling = () => {
      if (!isMounted) return;

      intervalId = setInterval(() => {
        safeFetchProcessingStatus();
        // 清除当前定时器并使用新的间隔时间重新设置
        if (intervalId && isMounted) {
          clearInterval(intervalId);
          startPolling();
        }
      }, currentPollingInterval);
    };

    // 延迟启动轮询，避免与WebSocket连接冲突
    setTimeout(() => {
      if (isMounted) {
        startPolling();
      }
    }, 2000);

    return () => {
      isMounted = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [currentKnowledgeBase, fetchProcessingStatus, userActive, processingStatus, processingDocuments.size]);

  // WebSocket 连接和进度监听
  useEffect(() => {
    if (!currentKnowledgeBase) return;

    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 10;
    const RECONNECT_DELAY = 3000;
    let isMounted = true;

    // 连接 WebSocket
    const connectWebSocket = async () => {
      // 限制重连次数
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error('[WebSocket] 达到最大重连次数，停止尝试');
        return;
      }

      try {
        await websocketService.connect();
        
        if (!isMounted) return;
        
        // 重置重连计数器
        reconnectAttempts = 0;
        
        // 连接成功后，立即获取处理状态并订阅所有处理中文档
        try {
          await fetchProcessingStatus();
          
          // 获取处理状态后，重新订阅所有处理中文档
          const processingDocIds = Array.from(processingDocuments.keys());
          
          if (processingDocIds.length > 0) {
            websocketService.subscribeToDocumentProgress(processingDocIds);
          }
        } catch (error) {
          console.error('[WebSocket] 获取处理状态失败:', error);
        }
      } catch (error) {
        if (!isMounted) return;
        
        console.error('[WebSocket] 连接失败:', error);
        reconnectAttempts++;
        // 连接失败后，延迟重试，每次增加延迟时间
        const delay = RECONNECT_DELAY * reconnectAttempts;
        
        setTimeout(() => {
          if (isMounted) {
            connectWebSocket();
          }
        }, delay);
      }
    };

    // 延迟连接，避免与轮询冲突
    setTimeout(() => {
      if (isMounted) {
        connectWebSocket();
      }
    }, 1000);

    // 注册文档进度消息处理器
    const handleDocumentProgress = (message) => {
      // 确保 document_id 是整数类型，与后端保持一致
      const docId = parseInt(message.document_id, 10);
      
      if (docId) {
        setProcessingProgress(prev => {
          const newProgress = new Map(prev);
          newProgress.set(docId, {
            status: message.status || 'processing',
            step_name: message.step_name || '处理中...',
            progress_percentage: message.progress_percent || message.progress_percentage || 0,
            message: message.message || '文档正在处理中',
            ...message
          });
          return newProgress;
        });

        // 更新文档状态 - 始终更新名称
        setProcessingDocuments(prev => {
          const newDocs = new Map(prev);
          const existingDoc = newDocs.get(docId);
          newDocs.set(docId, {
            id: docId,
            name: message.document_name || (existingDoc?.name) || `文档 ${docId}`
          });
          return newDocs;
        });

        // 显示进度面板
        setShowProgressPanel(true);

        // 如果处理完成，取消订阅并清理状态
        if (message.status === 'completed' || message.status === 'failed') {
          setTimeout(() => {
            websocketService.unsubscribeFromDocumentProgress(message.document_id);
            // 从处理文档列表中移除
            setProcessingDocuments(prev => {
              const newDocs = new Map(prev);
              newDocs.delete(docId);
              return newDocs;
            });
            // 从进度列表中移除
            setProcessingProgress(prev => {
              const newProgress = new Map(prev);
              newProgress.delete(docId);
              return newProgress;
            });
            // 检查是否还有处理中的文档
            fetchProcessingStatus();
          }, 2000);
        }
      }
    };

    websocketService.on('document_progress', handleDocumentProgress);

    return () => {
      isMounted = false;
      websocketService.off('document_progress');
    };
  }, [currentKnowledgeBase, fetchProcessingStatus]);

  /**
   * 处理批量处理
   */
  const handleBatchProcess = useCallback(async () => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    if (unprocessedCount === 0) {
      message.info({ content: '没有需要处理的文档' });
      return;
    }

    setBatchProcessing(true);
    try {
      const response = await batchProcessDocuments(currentKnowledgeBase.id);
      setBatchProcessResult(response);
      setShowBatchProcessModal(true);

      if (response.success) {
        message.success({
          content: `批量处理已启动！共 ${response.total_documents} 个文档，成功加入队列 ${response.queued_documents} 个`
        });
        // 更新未处理数量
        setUnprocessedCount(response.total_documents - response.queued_documents);
        // 显示进度面板
        setShowProgressPanel(true);

        // 订阅所有处理中文档的进度（WebSocket）
        if (response.processing_documents && response.processing_documents.length > 0) {
          const docIds = response.processing_documents.map(doc => doc.document_id || doc.id);
          websocketService.subscribeToDocumentProgress(docIds);
        }

        // 立即获取处理状态
        fetchProcessingStatus();
        // 刷新文档列表
        fetchDocuments();
      } else {
        message.error({ content: response.message || '批量处理失败' });
      }
    } catch (error) {
      message.error({ content: '批量处理失败：' + error.message });
    } finally {
      setBatchProcessing(false);
    }
  }, [currentKnowledgeBase, unprocessedCount, fetchDocuments, fetchProcessingStatus]);

  /**
   * 处理搜索
   */
  const handleSearch = useCallback((query) => {
    // 重置页码和列表
    setDocumentsPage(1);
    setDocuments([], 0);
    setDocumentFilters({ search: query });
    if (query) {
      addSearchHistory(query);
    }
  }, [setDocumentFilters, addSearchHistory, setDocumentsPage, setDocuments]);

  /**
   * 处理文件上传
   */
  const handleUpload = useCallback(async (files) => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    try {
      let successCount = 0;
      let errorCount = 0;

      for (const file of files) {
        try {
          await uploadDocument(file, currentKnowledgeBase.id);
          successCount++;
        } catch (error) {
          console.error('上传文件失败:', file.name, error);
          errorCount++;
        }
      }

      if (successCount > 0) {
        message.success({ content: `成功上传 ${successCount} 个文件` });
        fetchDocuments();
      }
      if (errorCount > 0) {
        message.error({ content: `${errorCount} 个文件上传失败` });
      }
    } catch (error) {
      message.error({ content: '上传失败：' + error.message });
    }
  }, [currentKnowledgeBase, fetchDocuments]);

  /**
   * 取消之前的请求
   */
  const cancelPreviousRequest = useCallback((key) => {
    const controller = abortControllersRef.current.get(key);
    if (controller) {
      controller.abort();
      abortControllersRef.current.delete(key);
    }
  }, []);

  /**
   * 获取文档详情
   */
  const fetchDocumentDetail = useCallback(async (docId) => {
    if (!docId) return;

    // 取消之前的请求
    cancelPreviousRequest('documentDetail');

    // 创建新的控制器
    const controller = new AbortController();
    abortControllersRef.current.set('documentDetail', controller);

    setDocumentDetailLoading(true);
    try {
      const doc = await getDocument(docId, { signal: controller.signal });
      setSelectedDocument(doc);
      // 请求成功后清理控制器
      cancelPreviousRequest('documentDetail');
    } catch (error) {
      if (error.name !== 'AbortError') {
        message.error({ content: '获取文档详情失败：' + error.message });
      }
      // 错误时也清理控制器（非 AbortError）
      if (error.name !== 'AbortError') {
        cancelPreviousRequest('documentDetail');
      }
    } finally {
      setDocumentDetailLoading(false);
    }
  }, [cancelPreviousRequest]);

  /**
   * 获取文档片段
   */
  const fetchDocumentChunks = useCallback(async (docId) => {
    if (!docId) {
      return;
    }

    // 取消之前的请求
    cancelPreviousRequest('documentChunks');

    // 创建新的控制器
    const controller = new AbortController();
    abortControllersRef.current.set('documentChunks', controller);

    setChunksLoading(true);
    try {
      const response = await getDocumentChunks(docId, 0, 50, { signal: controller.signal });
      // API 直接返回数组，不是 {chunks: [...]} 格式
      const chunks = Array.isArray(response) ? response : (response.chunks || []);
      setDocumentChunks(chunks);
      // 请求成功后清理控制器
      cancelPreviousRequest('documentChunks');
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('[fetchDocumentChunks] 获取文档片段失败:', error);
      }
      setDocumentChunks([]);
      // 错误时也清理控制器（非 AbortError）
      if (error.name !== 'AbortError') {
        cancelPreviousRequest('documentChunks');
      }
    } finally {
      setChunksLoading(false);
    }
  }, [cancelPreviousRequest]);

  /**
   * 获取文档内容（用于文本文件预览）
   */
  const fetchDocumentContent = useCallback(async (docId) => {
    if (!docId) return;

    // 取消之前的请求
    cancelPreviousRequest('documentContent');

    // 创建新的控制器
    const controller = new AbortController();
    abortControllersRef.current.set('documentContent', controller);

    try {
      const response = await fetch(`/api/knowledge/documents/${docId}/preview`, {
        signal: controller.signal
      });
      
      if (!response.ok) {
        throw new Error('获取文档内容失败');
      }
      
      const content = await response.text();
      return content;
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('[fetchDocumentContent] 获取文档内容失败:', error);
      }
      return null;
    } finally {
      cancelPreviousRequest('documentContent');
    }
  }, [cancelPreviousRequest]);

  // 当 documentId 变化时，获取文档详情
  useEffect(() => {
    if (documentId) {
      fetchDocumentDetail(documentId);
      fetchDocumentChunks(documentId);
    } else {
      setSelectedDocument(null);
      setDocumentChunks([]);
    }
  }, [documentId, fetchDocumentDetail, fetchDocumentChunks]);

  /**
   * 处理文档点击
   */
  const handleDocumentClick = useCallback((document) => {
    // 使用uuid进行导航，如果没有uuid则使用id
    const docId = document.uuid || document.id;
    navigate(`/knowledge/documents/${docId}`);
  }, [navigate]);

  /**
   * 处理下载文档
   */
  const handleDownloadDocument = useCallback(async () => {
    if (!selectedDocument) return;

    try {
      // 使用uuid或id下载文档
      const docId = selectedDocument.uuid || selectedDocument.id;
      const blob = await downloadDocument(docId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = selectedDocument.title;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      message.success({ content: '文档下载成功' });
    } catch (error) {
      message.error({ content: '下载失败：' + error.message });
    }
  }, [selectedDocument]);

  /**
   * 处理删除文档
   */
  const handleDeleteDocument = useCallback(async () => {
    if (!selectedDocument) return;

    if (!window.confirm(`确定要删除文档 "${selectedDocument.title}" 吗？`)) {
      return;
    }

    try {
      // 使用uuid或id删除文档
      const docId = selectedDocument.uuid || selectedDocument.id;
      await deleteDocument(docId);
      message.success({ content: '文档已删除' });
      navigate('/knowledge/documents');
      fetchDocuments();
    } catch (error) {
      message.error({ content: '删除失败：' + error.message });
    }
  }, [selectedDocument, navigate, fetchDocuments]);

  /**
   * 处理向量化文档
   */
  const handleVectorizeDocument = useCallback(async () => {
    if (!selectedDocument) return;

    try {
      // 使用uuid或id处理文档
      const docId = selectedDocument.uuid || selectedDocument.id;

      // 添加到处理文档列表
      setProcessingDocuments(prev => {
        const newDocs = new Map(prev);
        newDocs.set(docId, {
          id: docId,
          name: selectedDocument.title || `文档 ${docId}`
        });
        return newDocs;
      });

      // 初始化进度
      setProcessingProgress(prev => {
        const newProgress = new Map(prev);
        newProgress.set(docId, {
          status: 'processing',
          step_name: '初始化...',
          progress_percentage: 0,
          message: '开始处理文档'
        });
        return newProgress;
      });

      // 订阅文档进度（WebSocket）
      websocketService.subscribeToDocumentProgress(docId);

      await processDocument(docId);
      message.success({ content: '文档已向量化' });

      // 显示进度面板
      setShowProgressPanel(true);
      // 立即获取处理状态
      fetchProcessingStatus();

      fetchDocumentDetail(docId);
      fetchDocuments();
    } catch (error) {
      message.error({ content: '向量化失败：' + error.message });
    }
  }, [selectedDocument, fetchDocumentDetail, fetchDocuments, fetchProcessingStatus]);

  /**
   * 处理文档操作（用于DocumentActions组件的回调）
   */
  const handleDocumentAction = useCallback(async (actionKey, document) => {
    if (!document) return;

    const docId = document.uuid || document.id;

    switch (actionKey) {
      case 'download':
        await handleDownloadDocument();
        break;
      case 'delete':
        await handleDeleteDocument();
        break;
      case 'viewDetails':
        // 查看详情已经在当前页面显示
        break;
      case 'extractText':
      case 'chunkDocument':
      case 'extractEntities':
      case 'vectorize':
      case 'buildGraph':
      case 'reprocess':
        // 这些操作由DocumentActions组件内部处理
        // 操作完成后刷新文档列表和详情
        fetchDocumentDetail(docId);
        fetchDocuments();
        break;
      default:
        console.warn('未知的操作:', actionKey);
    }
  }, [handleDownloadDocument, handleDeleteDocument, fetchDocumentDetail, fetchDocuments]);
  
  /**
   * 保存向量化配置
   */
  const handleSaveVectorizationConfig = () => {
    // 这里可以添加保存配置到后端的逻辑
    message.success({ content: '向量化配置已保存' });
    setShowVectorizationConfig(false);
  };

  /**
   * 处理流程面板步骤操作
   */
  const handleProcessingFlowAction = useCallback(async (stepKey, docId) => {
    if (!docId) {
      message.warning({ content: '请先选择一个文档' });
      return;
    }

    setProcessingFlowLoading(true);

    try {
      switch (stepKey) {
        case 'vectorization':
          // 向量化
          await processDocument(docId);
          message.success({ content: '文档向量化已启动' });
          // 更新状态
          setDocumentProcessingStatus(prev => ({
            ...prev,
            vectorization_status: 'processing'
          }));
          break;

        case 'chunk_entities':
          // 片段级实体识别
          await extractChunkEntities(docId, 4);
          message.success({ content: '片段级实体识别已启动' });
          // 更新状态
          setDocumentProcessingStatus(prev => ({
            ...prev,
            chunk_entity_status: 'processing'
          }));
          break;

        case 'document_entities':
          // 文档级实体聚合
          await aggregateDocumentEntities(docId);
          message.success({ content: '文档级实体聚合已启动' });
          // 更新状态
          setDocumentProcessingStatus(prev => ({
            ...prev,
            document_entity_status: 'processing'
          }));
          break;

        case 'kb_alignment':
          // 知识库级实体对齐
          if (!currentKnowledgeBase) {
            message.warning({ content: '请先选择知识库' });
            return;
          }
          await alignKnowledgeBaseEntities(currentKnowledgeBase.id, false);
          message.success({ content: '知识库级实体对齐已启动' });
          // 更新状态
          setDocumentProcessingStatus(prev => ({
            ...prev,
            kb_alignment_status: 'processing'
          }));
          break;

        default:
          break;
      }
    } catch (error) {
      message.error({ content: `操作失败: ${error.message}` });
      // 更新状态为错误
      setDocumentProcessingStatus(prev => ({
        ...prev,
        [`${stepKey}_status`]: 'error'
      }));
    } finally {
      setProcessingFlowLoading(false);
    }
  }, [currentKnowledgeBase]);

  /**
   * 获取文档处理状态
   * 根据文档的 vectorizationStatus 确定各级处理状态
   */
  const fetchDocumentProcessingStatus = useCallback(async (docId) => {
    if (!docId) return;

    try {
      // 查找文档对象
      const doc = documents.find(d => String(d.id) === String(docId));

      if (!doc) {
        console.warn(`文档 ${docId} 未找到`);
        return;
      }

      // 根据文档的 vectorizationStatus 确定向量化状态
      let vectorizationStatus = 'pending';
      if (doc.vectorizationStatus === 'vectorized') {
        vectorizationStatus = 'completed';
      } else if (doc.vectorizationStatus === 'processing') {
        vectorizationStatus = 'processing';
      } else if (doc.vectorizationStatus === 'error') {
        vectorizationStatus = 'error';
      }

      // TODO: 后续需要从后端获取片段级、文档级、知识库级的真实状态
      // 目前根据向量化状态推断：如果向量化未完成，后续步骤都不可进行
      const status = {
        vectorization_status: vectorizationStatus,
        chunk_entity_status: vectorizationStatus === 'completed' ? 'pending' : 'waiting',
        document_entity_status: vectorizationStatus === 'completed' ? 'pending' : 'waiting',
        kb_alignment_status: vectorizationStatus === 'completed' ? 'pending' : 'waiting'
      };

      setDocumentProcessingStatus(status);
    } catch (error) {
      console.error('获取文档处理状态失败:', error);
    }
  }, [documents]);

  /**
   * 切换处理流程面板显示
   */
  const toggleProcessingFlow = useCallback((docId) => {
    if (showProcessingFlow && selectedDocument?.id === docId) {
      setShowProcessingFlow(false);
      setSelectedDocument(null);
    } else {
      // 查找文档对象
      const doc = documents.find(d => String(d.id) === String(docId));
      setSelectedDocument(doc || null);
      setShowProcessingFlow(true);
      fetchDocumentProcessingStatus(docId);
    }
  }, [showProcessingFlow, selectedDocument, fetchDocumentProcessingStatus, documents]);

  /**
   * 渲染文档项 - 使用稳定引用避免不必要的重渲染
   */
  const renderDocument = useCallback((doc) => (
    <MemoDocumentCard
      document={doc}
      selectedDocuments={selectedDocuments}
      onSelect={toggleDocumentSelection}
      onClick={handleDocumentClick}
      onProcessingFlow={toggleProcessingFlow}
      viewMode={viewMode}
    />
  ), [selectedDocuments, toggleDocumentSelection, handleDocumentClick, toggleProcessingFlow, viewMode]);

  /**
   * 加载更多
   */
  const handleLoadMore = useCallback(() => {
    if (!documentsLoading && documents.length < documentsTotal) {
      setDocumentsPage(documentsPage + 1);
    }
  }, [documentsLoading, documents.length, documentsTotal, documentsPage, setDocumentsPage]);

  /**
   * 切换视图模式
   */
  const toggleViewMode = useCallback(() => {
    setViewMode(prev => prev === VIEW_MODES.LIST ? VIEW_MODES.GRID : VIEW_MODES.LIST);
  }, []);

  /**
   * 处理排序变更
   */
  const handleSortChange = useCallback((e) => {
    setSortBy(e.target.value);
    // 重置页码和列表
    setDocumentsPage(1);
    setDocuments([], 0);
    // 立即重新获取文档
    fetchDocuments();
  }, [setSortBy, setDocumentsPage, setDocuments, fetchDocuments]);

  /**
   * 处理过滤变更
   */
  const handleFilterChange = useCallback((status) => {
    setFilterStatus(status);
    setShowFilters(false);
    // 重置页码和列表
    setDocumentsPage(1);
    setDocuments([], 0);
    // 立即重新获取文档
    fetchDocuments();
  }, [setFilterStatus, setShowFilters, setDocumentsPage, setDocuments, fetchDocuments]);

  if (documentsError) {
    return (
      <div className="document-management-error">
        <div className="error-icon">⚠️</div>
        <h3>加载失败</h3>
        <p>{documentsError}</p>
        <button className="retry-button" onClick={fetchDocuments}>
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="document-management">
      {/* 顶部工具栏 */}
      <div className="document-management-header">
        <div className="header-left">
          <UploadButton onUpload={handleUpload} />
        </div>
        
        <div className="header-right">
          {/* 搜索框 */}
          <div className="header-search">
            <SmartSearch 
              onSearch={handleSearch}
              placeholder="搜索文档..."
            />
          </div>
          
          {/* 过滤器 */}
          <div className="header-filters">
            <button 
              className={`filter-toggle ${showFilters ? 'active' : ''}`}
              onClick={() => setShowFilters(!showFilters)}
            >
              <FiFilter size={16} />
              <span>筛选</span>
            </button>
            
            {showFilters && (
              <div className="filter-dropdown">
                {FILTER_OPTIONS.map(option => (
                  <button
                    key={option.value}
                    className={`filter-option ${filterStatus === option.value ? 'active' : ''}`}
                    onClick={() => handleFilterChange(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {/* 排序选择 */}
          <div className="header-sort">
            <select value={sortBy} onChange={handleSortChange}>
              {SORT_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* 向量化设置 */}
          <div className="header-vectorization">
            <button 
              className="vectorization-settings-btn"
              onClick={() => setShowVectorizationConfig(true)}
              title="向量化设置"
            >
              <FiZap size={18} />
              <span>向量化设置</span>
            </button>
          </div>
          
          {/* 批量处理按钮 */}
          {unprocessedCount > 0 && (
            <div className="header-batch-process">
              <button 
                className="batch-process-btn"
                onClick={handleBatchProcess}
                title={`批量处理 ${unprocessedCount} 个未处理文档`}
              >
                <FiZap size={18} />
                <span>批量处理 ({unprocessedCount})</span>
              </button>
            </div>
          )}
          
          {/* 视图切换 */}
          <div className="header-view-toggle">
            <button 
              className={viewMode === VIEW_MODES.LIST ? 'active' : ''}
              onClick={toggleViewMode}
              title={viewMode === VIEW_MODES.LIST ? '切换到网格视图' : '切换到列表视图'}
            >
              {viewMode === VIEW_MODES.LIST ? <FiGrid size={18} /> : <FiList size={18} />}
            </button>
          </div>
        </div>
      </div>

      {/* 增强版批量操作工具栏 */}
      {selectedDocuments.length > 0 && (
        <EnhancedBatchOperations
          onBatchProcessStart={(selectedDocs) => {
            // 添加到处理列表
            const docIds = [];
            selectedDocs.forEach(doc => {
              // 确保使用整数ID，与后端WebSocket消息保持一致
              const docId = parseInt(doc.id, 10);
              if (!docId) return; // 跳过无效ID
              docIds.push(docId);

              // 添加到处理文档列表
              setProcessingDocuments(prev => {
                const newDocs = new Map(prev);
                newDocs.set(docId, {
                  id: docId,
                  name: doc.title || `文档 ${docId}`
                });
                return newDocs;
              });

              // 初始化进度
              setProcessingProgress(prev => {
                const newProgress = new Map(prev);
                newProgress.set(docId, {
                  status: 'processing',
                  step_name: '等待处理...',
                  progress_percentage: 0,
                  message: '文档正在排队处理'
                });
                return newProgress;
              });
            });

            // 订阅所有文档进度（WebSocket）
            websocketService.subscribeToDocumentProgress(docIds);

            // 显示进度面板
            setShowProgressPanel(true);
          }}
          onRefresh={fetchDocuments}
        />
      )}

      {/* 实时处理进度面板 */}
      {showProgressPanel && processingStatus && (
        <div className="processing-progress-panel">
          <div className="progress-panel-header">
            <div className="progress-title">
              <FiLoader size={16} className="spinning" />
              <span>文档处理中...</span>
            </div>
            <button
              className="close-progress-panel"
              onClick={() => setShowProgressPanel(false)}
              title="隐藏进度面板"
            >
              ×
            </button>
          </div>
          <div className="progress-panel-content">
            {/* 总体进度 */}
            <div className="progress-overview">
              <div className="progress-stat">
                <span className="stat-label">总文档:</span>
                <span className="stat-value">{processingStatus.statistics?.total_documents || 0}</span>
              </div>
              <div className="progress-stat">
                <span className="stat-label">已完成:</span>
                <span className="stat-value success">{processingStatus.statistics?.vectorized_documents || 0}</span>
              </div>
              <div className="progress-stat">
                <span className="stat-label">待处理:</span>
                <span className="stat-value warning">{processingStatus.statistics?.unprocessed_documents || 0}</span>
              </div>
              <div className="progress-stat">
                <span className="stat-label">完成率:</span>
                <span className="stat-value info">{processingStatus.statistics?.vectorization_rate || 0}%</span>
              </div>
            </div>

            {/* 队列状态 */}
            <div className="queue-status">
              <div className="queue-item">
                <span className="queue-label">队列中:</span>
                <span className="queue-value">{processingStatus.queue_status?.queue_size || 0}</span>
              </div>
              <div className="queue-item">
                <span className="queue-label">处理中:</span>
                <span className="queue-value processing">{processingStatus.queue_status?.processing_count || 0}</span>
              </div>
              <div className="queue-item">
                <span className="queue-label">已完成:</span>
                <span className="queue-value success">{processingStatus.queue_status?.completed_count || 0}</span>
              </div>
              <div className="queue-item">
                <span className="queue-label">失败:</span>
                <span className="queue-value error">{processingStatus.queue_status?.failed_count || 0}</span>
              </div>
            </div>

            {/* 正在处理的文档 - 使用ProcessingDocumentsPanel组件 */}
            <ProcessingDocumentsPanel
              processingDocuments={processingDocuments}
              processingProgress={processingProgress}
              queueStatus={processingStatus.queue_status}
            />

            {/* 进度条 */}
            <div className="progress-bar-container">
              <div
                className="progress-bar"
                style={{
                  width: `${processingStatus.statistics?.vectorization_rate || 0}%`
                }}
              />
              <span className="progress-text">
                {processingStatus.statistics?.vectorization_rate || 0}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 四级分层处理流程面板 */}
      {showProcessingFlow && selectedDocument && (
        <ProcessingFlowPanel
          document={selectedDocument}
          knowledgeBaseId={currentKnowledgeBase?.id}
          onStatusUpdate={setDocumentProcessingStatus}
          className="document-processing-flow"
        />
      )}

      {/* 统计信息和全选 */}
      <div className="document-management-stats">
        <label className="select-all-checkbox">
          <input
            type="checkbox"
            checked={documents.length > 0 && selectedDocuments.length === documents.length}
            onChange={(e) => {
              if (e.target.checked) {
                selectAllDocuments(true);
              } else {
                clearSelection();
              }
            }}
          />
          <span>全选</span>
        </label>
        <span>共 {documentsTotal} 个文档</span>
        {selectedDocuments.length > 0 && (
          <span className="selected-count">已选择 {selectedDocuments.length} 个</span>
        )}
        {processingStatus?.statistics?.vectorization_rate !== undefined && (
          <span className="vectorization-rate">
            向量化: {processingStatus.statistics.vectorization_rate}%
          </span>
        )}
      </div>

      {/* 文档加载进度显示 */}
      {documentsLoading && loadProgress > 0 && (
        <div className="document-load-progress">
          <div className="load-progress-header">
            <FiLoader size={16} className="spinning" />
            <span>正在加载文档...</span>
          </div>
          <div className="load-progress-bar-container">
            <div
              className="load-progress-bar"
              style={{ width: `${loadProgress}%` }}
            />
          </div>
          <div className="load-progress-info">
            <span className="load-progress-percent">{loadProgress.toFixed(1)}%</span>
            {loadMessage && <span className="load-progress-message">{loadMessage}</span>}
          </div>
        </div>
      )}

      {/* 文档列表 */}
      <div className={`document-list-container ${viewMode === VIEW_MODES.GRID ? 'grid-view' : 'list-view'}`}>
        <VirtualListEnhanced
          key={`doc-list-${currentKnowledgeBase?.id || 'empty'}`}
          items={documents}
          renderItem={renderDocument}
          estimateSize={viewMode === VIEW_MODES.GRID ? 200 : 80}
          overscan={viewMode === VIEW_MODES.GRID ? 5 : 8}
          onEndReached={handleLoadMore}
          hasMore={documents.length < documentsTotal}
          loading={documentsLoading}
          emptyText={
            <div className="empty-state">
              <div className="empty-icon">📁</div>
              <h3>暂无文档</h3>
              <p>点击上方&quot;上传文档&quot;按钮添加文档</p>
            </div>
          }
        />
      </div>

      {/* 向量化设置模态框 */}
      {showVectorizationConfig && (
        <div className="modal-overlay" onClick={() => setShowVectorizationConfig(false)}>
          <div className="modal-content modal-large" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>向量化设置</h3>
              <button className="close-btn" onClick={() => setShowVectorizationConfig(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="config-section">
                <h4>分块配置</h4>
                <div className="config-form">
                  <div className="form-group">
                    <label>分块大小</label>
                    <input 
                      type="number" 
                      value={vectorizationConfig.chunkSize}
                      onChange={(e) => setVectorizationConfig({...vectorizationConfig, chunkSize: Number(e.target.value)})}
                      min={100}
                      max={2000}
                    />
                    <span className="help-text">每个文本块的最大字符数</span>
                  </div>
                  <div className="form-group">
                    <label>分块重叠</label>
                    <input 
                      type="number" 
                      value={vectorizationConfig.chunkOverlap}
                      onChange={(e) => setVectorizationConfig({...vectorizationConfig, chunkOverlap: Number(e.target.value)})}
                      min={0}
                      max={500}
                    />
                    <span className="help-text">相邻文本块之间的重叠字符数</span>
                  </div>
                </div>
              </div>

              <div className="config-section">
                <h4>模型配置</h4>
                <div className="config-form">
                  <div className="form-group">
                    <label>嵌入模型</label>
                    <select 
                      value={vectorizationConfig.embeddingModel}
                      onChange={(e) => setVectorizationConfig({...vectorizationConfig, embeddingModel: e.target.value})}
                    >
                      <option value="default">默认模型</option>
                      <option value="text-embedding-3-small">Text Embedding 3 Small</option>
                      <option value="text-embedding-3-large">Text Embedding 3 Large</option>
                    </select>
                    <span className="help-text">用于生成向量嵌入的模型</span>
                  </div>
                </div>
              </div>

              <div className="config-section">
                <h4>批处理配置</h4>
                <div className="config-form">
                  <div className="form-group">
                    <label>批处理大小</label>
                    <input 
                      type="number" 
                      value={vectorizationConfig.batchSize}
                      onChange={(e) => setVectorizationConfig({...vectorizationConfig, batchSize: Number(e.target.value)})}
                      min={1}
                      max={50}
                    />
                    <span className="help-text">同时处理的文档数量</span>
                  </div>
                  <div className="form-group checkbox">
                    <label>
                      <input 
                        type="checkbox" 
                        checked={vectorizationConfig.autoProcess}
                        onChange={(e) => setVectorizationConfig({...vectorizationConfig, autoProcess: e.target.checked})}
                      />
                      自动处理新上传的文档
                    </label>
                  </div>
                </div>
              </div>

              <div className="config-actions">
                <button className="btn btn-secondary" onClick={() => setShowVectorizationConfig(false)}>
                  取消
                </button>
                <button className="btn btn-primary" onClick={handleSaveVectorizationConfig}>
                  保存
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 文档详情面板 */}
      {documentId && (
        <div className="document-detail-panel">
          <div className="document-detail-header">
            <h3>文档详情</h3>
            <button
              className="close-detail"
              onClick={() => navigate('/knowledge/documents')}
            >
              ×
            </button>
          </div>
          <div className="document-detail-content">
            {documentDetailLoading ? (
              <div className="detail-loading">加载中...</div>
            ) : selectedDocument ? (
              <>
                {/* 文档基本信息 */}
                <div className="detail-section">
                  <h4 className="detail-title">{selectedDocument.title}</h4>
                  <div className="detail-meta">
                    <span className="detail-meta-item">
                      <FiFile size={14} />
                      类型: {selectedDocument.file_type?.toUpperCase() || '未知'}
                    </span>
                    <span className="detail-meta-item">
                      大小: {formatFileSize(selectedDocument.document_metadata?.file_size || 0)}
                    </span>
                    <span className="detail-meta-item">
                      创建时间: {new Date(selectedDocument.created_at).toLocaleString('zh-CN')}
                    </span>
                    <span className={`detail-meta-item status-${selectedDocument.document_metadata?.processing_status === 'completed' ? 'vectorized' : 'pending'}`}>
                      状态: {selectedDocument.document_metadata?.processing_status === 'completed' ? '已向量化' : '未向量化'}
                    </span>
                  </div>
                </div>

                {/* 标签页导航 */}
                <div className="detail-tabs">
                  <button
                    className={`detail-tab ${activeTab === 'info' ? 'active' : ''}`}
                    onClick={() => setActiveTab('info')}
                  >
                    基本信息
                  </button>
                  <button
                    className={`detail-tab ${activeTab === 'preview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('preview')}
                  >
                    文档预览
                  </button>
                  <button
                    className={`detail-tab ${activeTab === 'tags' ? 'active' : ''}`}
                    onClick={() => setActiveTab('tags')}
                  >
                    标签管理
                  </button>
                  {selectedDocument.document_metadata?.processing_status === 'completed' && (
                    <button
                      className={`detail-tab ${activeTab === 'chunks' ? 'active' : ''}`}
                      onClick={() => setActiveTab('chunks')}
                    >
                      向量片段 ({documentChunks.length})
                    </button>
                  )}
                </div>

                {/* 标签页内容 */}
                <div className="detail-tab-content">
                  {activeTab === 'info' && (
                    <div className="info-content">
                      <div className="info-item">
                        <label>文档 ID:</label>
                        <span>{selectedDocument.id}</span>
                      </div>
                      <div className="info-item">
                        <label>知识库 ID:</label>
                        <span>{selectedDocument.knowledge_base_id}</span>
                      </div>
                      {selectedDocument.document_metadata?.processing_status && (
                        <div className="info-item">
                          <label>处理状态:</label>
                          <span>{selectedDocument.document_metadata.processing_status}</span>
                        </div>
                      )}
                      {selectedDocument.document_metadata?.chunk_count !== undefined && (
                        <div className="info-item">
                          <label>片段数量:</label>
                          <span>{selectedDocument.document_metadata.chunk_count}</span>
                        </div>
                      )}

                      {/* 使用DocumentActions组件提供细粒度操作 */}
                      <DocumentActions 
                        document={selectedDocument}
                        onActionComplete={handleDocumentAction}
                        compact={true}
                      />
                    </div>
                  )}

                  {activeTab === 'preview' && (
                    <div className="preview-content">
                      <div className="preview-header">
                        <h4>文档预览</h4>
                        <p className="preview-hint">支持 PDF、Word、Excel 等常见文件类型的预览</p>
                      </div>
                      <div className="preview-container">
                        {(() => {
                          const fileType = selectedDocument.file_type?.toLowerCase() || '';
                          const docId = selectedDocument.uuid || selectedDocument.id;
                          
                          if (fileType === 'pdf') {
                            return (
                              <div className="pdf-preview">
                                <iframe 
                                  src={`/api/knowledge/documents/${docId}/preview`} 
                                  title="PDF 预览"
                                  className="preview-iframe"
                                  frameBorder="0"
                                />
                              </div>
                            );
                          } else if (['doc', 'docx', 'xls', 'xlsx'].includes(fileType)) {
                            return (
                              <div className="office-preview">
                                <iframe 
                                  src={`https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(window.location.origin + `/api/knowledge/documents/${docId}/download`)}`} 
                                  title="Office 文档预览"
                                  className="preview-iframe"
                                  frameBorder="0"
                                />
                              </div>
                            );
                          } else if (['txt', 'md'].includes(fileType)) {
                            const [content, setContent] = React.useState('加载中...');
                            
                            React.useEffect(() => {
                              const loadContent = async () => {
                                const textContent = await fetchDocumentContent(docId);
                                setContent(textContent || '无法加载文件内容');
                              };
                              
                              loadContent();
                            }, [docId, fetchDocumentContent]);
                            
                            return (
                              <div className="text-preview">
                                <pre className="text-content">{content}</pre>
                              </div>
                            );
                          } else if (['jpg', 'jpeg', 'png', 'gif'].includes(fileType)) {
                            return (
                              <div className="image-preview">
                                <img 
                                  src={`/api/knowledge/documents/${docId}/download`} 
                                  alt={selectedDocument.title}
                                  className="preview-image"
                                />
                              </div>
                            );
                          } else {
                            return (
                              <div className="unsupported-preview">
                                <div className="preview-icon">📄</div>
                                <h5>不支持的文件类型</h5>
                                <p>该文件类型无法在线预览，请下载查看</p>
                                <button
                                  className="action-btn primary"
                                  onClick={handleDownloadDocument}
                                >
                                  <FiDownload size={16} />
                                  下载文档
                                </button>
                              </div>
                            );
                          }
                        })()}
                      </div>
                    </div>
                  )}

                  {activeTab === 'tags' && (
                    <div className="tags-content">
                      <div className="tags-header">
                        <h4>标签管理</h4>
                        <p className="tags-hint">为文档添加标签，便于分类和检索</p>
                      </div>
                      <div className="tags-management">
                        <div className="tags-input-section">
                          <div className="tags-input-container">
                            <input
                              type="text"
                              placeholder="输入标签名称，按回车添加"
                              className="tags-input"
                              onKeyPress={(e) => {
                                if (e.key === 'Enter' && e.target.value.trim()) {
                                  const newTag = e.target.value.trim();
                                  setSelectedDocument(prev => ({
                                    ...prev,
                                    tags: [...(prev.tags || []), newTag]
                                  }));
                                  e.target.value = '';
                                }
                              }}
                            />
                          </div>
                        </div>
                        <div className="tags-list-section">
                          <h5>当前标签</h5>
                          <div className="tags-list">
                            {(selectedDocument.tags || []).map((tag, index) => (
                              <div key={index} className="tag-item">
                                <span className="tag-name">{tag}</span>
                                <button
                                  className="tag-remove"
                                  onClick={() => {
                                    setSelectedDocument(prev => ({
                                      ...prev,
                                      tags: prev.tags.filter((_, i) => i !== index)
                                    }));
                                  }}
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                            {(!selectedDocument.tags || selectedDocument.tags.length === 0) && (
                              <div className="empty-tags">
                                <p>暂无标签，点击上方输入框添加</p>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="tags-actions">
                          <button
                            className="action-btn primary"
                            onClick={() => {
                              message.success({ content: '标签已保存' });
                              // 这里可以添加保存标签的 API 调用
                            }}
                          >
                            保存标签
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'chunks' && (
                    <div className="chunks-content">
                      {chunksLoading ? (
                        <div className="detail-loading">加载片段中...</div>
                      ) : documentChunks.length > 0 ? (
                        <div className="chunks-list">
                          {documentChunks.map((chunk, index) => (
                            <div key={chunk.id || index} className="chunk-item">
                              <div className="chunk-header">
                                <span className="chunk-index">
                                  片段 {chunk.chunk_index !== undefined ? chunk.chunk_index + 1 : index + 1}
                                  {chunk.total_chunks ? ` / ${chunk.total_chunks}` : ''}
                                </span>
                                {chunk.score !== undefined && (
                                  <span className="chunk-score">
                                    相似度: {(chunk.score * 100).toFixed(1)}%
                                  </span>
                                )}
                              </div>
                              <div className="chunk-text">{chunk.content || chunk.text || '无内容'}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty-chunks">
                          <p>暂无向量片段</p>
                          {selectedDocument.document_metadata?.processing_status === 'completed' && (
                            <p className="empty-hint">文档已向量化，但未能获取到片段数据</p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="detail-error">无法加载文档详情</div>
            )}
          </div>
        </div>
      )}

      {/* 批量处理结果弹窗 */}
      {showBatchProcessModal && batchProcessResult && (
        <div className="batch-process-modal-overlay" onClick={() => setShowBatchProcessModal(false)}>
          <div className="batch-process-modal" onClick={(e) => e.stopPropagation()}>
            <div className="batch-process-modal-header">
              <h3>批量处理结果</h3>
              <button className="close-button" onClick={() => setShowBatchProcessModal(false)}>×</button>
            </div>
            <div className="batch-process-modal-content">
              <div className="result-summary">
                <div className="result-item">
                  <span className="result-label">知识库:</span>
                  <span className="result-value">{batchProcessResult.knowledge_base_name}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">总文档数:</span>
                  <span className="result-value">{batchProcessResult.total_documents}</span>
                </div>
                <div className="result-item success">
                  <span className="result-label">成功加入队列:</span>
                  <span className="result-value">{batchProcessResult.queued_documents}</span>
                </div>
                {batchProcessResult.skipped_documents > 0 && (
                  <div className="result-item warning">
                    <span className="result-label">跳过:</span>
                    <span className="result-value">{batchProcessResult.skipped_documents}</span>
                  </div>
                )}
                {batchProcessResult.failed_documents > 0 && (
                  <div className="result-item error">
                    <span className="result-label">失败:</span>
                    <span className="result-value">{batchProcessResult.failed_documents}</span>
                  </div>
                )}
              </div>
              <div className="result-message">
                <p>{batchProcessResult.message}</p>
              </div>
              <div className="queue-status">
                <h4>队列状态</h4>
                <div className="status-item">
                  <span>处理中:</span>
                  <span>{batchProcessResult.queue_status?.processing_count || 0}</span>
                </div>
                <div className="status-item">
                  <span>队列中:</span>
                  <span>{batchProcessResult.queue_status?.queue_size || 0}</span>
                </div>
              </div>
            </div>
            <div className="batch-process-modal-footer">
              <button className="confirm-button" onClick={() => setShowBatchProcessModal(false)}>
                确定
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 重新切片对话框 */}
      <RechunkDialog
        documentId={rechunkDocumentId}
        documentTitle={rechunkDocumentTitle}
        visible={showRechunkDialog}
        onClose={() => setShowRechunkDialog(false)}
        onSuccess={() => {
          // 刷新文档列表
          fetchDocuments();
          // 如果当前有选中的文档，刷新其详情
          if (selectedDocument && String(selectedDocument.id) === String(rechunkDocumentId)) {
            handleDocumentClick(selectedDocument);
          }
        }}
      />
    </div>
  );
};

export default DocumentManagement;
