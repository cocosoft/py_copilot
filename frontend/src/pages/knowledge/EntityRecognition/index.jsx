/**
 * 实体识别页面
 *
 * 提供实体提取、确认、编辑功能，支持从文档中自动识别实体
 */

import { useEffect, useCallback, useState, useMemo, useRef } from 'react';
import { FiCheck, FiX, FiEdit2, FiTrash2, FiSearch, FiBox, FiSettings, FiFolder, FiLayers, FiDatabase, FiGlobe, FiFileText } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { VirtualListEnhanced } from '../../../components/UI';
import Modal from '../../../components/UI/Modal';
import { message } from '../../../components/UI/Message/Message';
import EntityConfigModal from '../../../components/Knowledge/EntityConfigModal';
import {
  listDocuments,
  getDocumentEntitiesFromMaintenance,
  batchUpdateEntityStatus,
  updateEntityStatus,
  extractChunkEntities,
  getExtractTaskStatus,
  aggregateDocumentEntities,
  alignKnowledgeBaseEntities,
  getDocumentChunkEntities,
  getDocumentEntitiesNew,
  updateDocumentProcessingStatus
} from '../../../utils/api/knowledgeApi';
import defaultModelApi from '../../../utils/api/defaultModelApi';
import './styles.css';

/**
 * 实体类型配置
 */
const ENTITY_TYPES = [
  { value: 'person', label: '人物', color: '#1890ff' },
  { value: 'organization', label: '组织', color: '#52c41a' },
  { value: 'location', label: '地点', color: '#faad14' },
  { value: 'time', label: '时间', color: '#722ed1' },
  { value: 'event', label: '事件', color: '#eb2f96' },
  { value: 'concept', label: '概念', color: '#13c2c2' },
  { value: 'product', label: '产品', color: '#f5222d' },
  { value: 'technology', label: '技术', color: '#2f54eb' },
];

/**
 * 实体状态配置
 */
const ENTITY_STATUS = {
  pending: { label: '待确认', color: '#faad14', bgColor: '#fffbe6' },
  confirmed: { label: '已确认', color: '#52c41a', bgColor: '#f6ffed' },
  rejected: { label: '已拒绝', color: '#ff4d4f', bgColor: '#fff2f0' },
  modified: { label: '已修改', color: '#1890ff', bgColor: '#e6f7ff' },
};

/**
 * 文档处理状态配置
 * 统一使用 processing_status 字段判断文档状态
 * 状态值：
 *   - idle/pending: 待向量化
 *   - queued: 排队中
 *   - processing: 向量化中
 *   - completed: 已向量化
 *   - entity_processing: 实体识别中
 *   - entity_completed: 已实体识别
 *   - failed: 处理失败
 */
const DOCUMENT_STATUS = {
  // 向量化相关状态
  completed: { label: '已向量化', color: '#389e0d', bgColor: '#f6ffed', borderColor: '#b7eb8f', canSelect: true, stage: 'vectorization' },
  processing: { label: '向量化中', color: '#1890ff', bgColor: '#e6f7ff', borderColor: '#91d5ff', canSelect: false, stage: 'vectorization' },
  queued: { label: '排队中', color: '#722ed1', bgColor: '#f9f0ff', borderColor: '#d3adf7', canSelect: false, stage: 'vectorization' },
  pending: { label: '待向量化', color: '#faad14', bgColor: '#fffbe6', borderColor: '#ffd591', canSelect: false, stage: 'vectorization' },
  idle: { label: '待向量化', color: '#faad14', bgColor: '#fffbe6', borderColor: '#ffd591', canSelect: false, stage: 'vectorization' },

  // 实体识别相关状态（新增）
  entity_processing: { label: '实体识别中', color: '#13c2c2', bgColor: '#e6fffb', borderColor: '#87e8de', canSelect: false, stage: 'entity_extraction' },
  entity_aggregating: { label: '实体聚合中', color: '#eb2f96', bgColor: '#fff0f6', borderColor: '#ffadd2', canSelect: false, stage: 'entity_extraction' },
  entity_aligning: { label: '实体对齐中', color: '#722ed1', bgColor: '#f9f0ff', borderColor: '#d3adf7', canSelect: false, stage: 'entity_extraction' },
  entity_completed: { label: '已实体识别', color: '#52c41a', bgColor: '#f6ffed', borderColor: '#b7eb8f', canSelect: true, stage: 'entity_extraction' },

  // 失败状态
  failed: { label: '处理失败', color: '#ff4d4f', bgColor: '#fff2f0', borderColor: '#ffccc7', canSelect: false, stage: 'error' },
  entity_failed: { label: '实体识别失败', color: '#ff4d4f', bgColor: '#fff2f0', borderColor: '#ffccc7', canSelect: false, stage: 'error' },

  // 未知状态
  unknown: { label: '未知', color: '#8c8c8c', bgColor: '#f5f5f5', borderColor: '#d9d9d9', canSelect: false, stage: 'unknown' },
};

/**
 * 获取文档处理状态
 * 统一使用 processing_status 字段判断
 * @param {Object} doc - 文档对象
 * @returns {Object} 状态配置对象
 */
const getDocumentStatus = (doc) => {
  if (!doc) return DOCUMENT_STATUS.unknown;
  // 优先使用 document_metadata 中的 processing_status
  const status = doc.document_metadata?.processing_status || doc.processing_status || 'unknown';
  return DOCUMENT_STATUS[status] || DOCUMENT_STATUS.unknown;
};

/**
 * 检查文档是否已完成向量化（可用于实体提取）
 * @param {Object} doc - 文档对象
 * @returns {boolean}
 */
const isDocumentProcessed = (doc) => {
  if (!doc) return false;
  const status = doc.document_metadata?.processing_status || doc.processing_status || 'unknown';
  // 已完成向量化或已完成实体识别的文档都可以进行实体提取
  return status === 'completed' || status === 'entity_processing' ||
         status === 'entity_aggregating' || status === 'entity_aligning' ||
         status === 'entity_completed';
};

/**
 * 检查文档是否已完成实体识别
 * @param {Object} doc - 文档对象
 * @returns {boolean}
 */
const isEntityExtractionCompleted = (doc) => {
  if (!doc) return false;
  const status = doc.document_metadata?.processing_status || doc.processing_status || 'unknown';
  return status === 'entity_completed';
};

/**
 * 获取文档当前处理阶段
 * @param {Object} doc - 文档对象
 * @returns {string} 阶段名称：vectorization, entity_extraction, error, unknown
 */
const getDocumentStage = (doc) => {
  if (!doc) return 'unknown';
  const status = doc.document_metadata?.processing_status || doc.processing_status || 'unknown';
  const statusConfig = DOCUMENT_STATUS[status];
  return statusConfig?.stage || 'unknown';
};

/**
 * 实体识别页面
 */
const EntityRecognition = () => {
  const { currentKnowledgeBase } = useKnowledgeStore();
  const navigate = useNavigate();

  // 本地状态
  const [documents, setDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [entities, setEntities] = useState([]);
  const [filteredEntities, setFilteredEntities] = useState([]);

  // 默认模型状态
  const [defaultModel, setDefaultModel] = useState(null);
  const [loadingModel, setLoadingModel] = useState(false);

  // 状态同步相关
  const [statusSyncNeeded, setStatusSyncNeeded] = useState(false);
  const [docsNeedSync, setDocsNeedSync] = useState([]);
  const [syncingStatus, setSyncingStatus] = useState(false);

  // 筛选状态
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');

  /**
   * 搜索防抖处理
   */
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // 编辑状态
  const [editingEntity, setEditingEntity] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', type: '', description: '' });

  // 配置弹窗状态
  const [configModalVisible, setConfigModalVisible] = useState(false);

  // 监听 configModalVisible 状态变化
  useEffect(() => {
    console.log('configModalVisible 状态变化:', configModalVisible);
  }, [configModalVisible]);

  // 提取配置状态
  const [extractConfig, setExtractConfig] = useState({
    extractEntities: true,
    extractRelationships: true,
    processingMode: 'quality', // 'standard' | 'quality' | 'speed'
    threshold: 0.7
  });
  const [showConfigPanel, setShowConfigPanel] = useState(false);

  // 文档搜索状态
  const [docSearchQuery, setDocSearchQuery] = useState('');

  // 文档筛选状态: all(全部), pending(待识别), completed(已识别)
  const [docFilterStatus, setDocFilterStatus] = useState('all');

  // ==================== 四级架构状态 ====================
  // 当前选中的实体层级: chunk(片段级), document(文档级), kb(知识库级), global(全局级)
  const [entityLevel, setEntityLevel] = useState('document');

  // 四级处理流程状态
  const [processingFlow, setProcessingFlow] = useState({
    chunk: { status: 'idle', progress: 0, message: '' },      // 片段级提取
    document: { status: 'idle', progress: 0, message: '' },   // 文档级聚合
    kb: { status: 'idle', progress: 0, message: '' },         // 知识库级对齐
    global: { status: 'idle', progress: 0, message: '' }      // 全局级对齐
  });

  // 是否正在处理中（用于UI显示）
  const isProcessing = useMemo(() => {
    return processingFlow.chunk.status === 'processing' ||
           processingFlow.document.status === 'processing' ||
           processingFlow.kb.status === 'processing' ||
           processingFlow.global.status === 'processing';
  }, [processingFlow]);

  // 各层级实体数据
  const [chunkEntities, setChunkEntities] = useState([]);
  const [documentEntities, setDocumentEntities] = useState([]);
  const [kbEntities, setKbEntities] = useState([]);

  // 当前选中的文档（用于查看片段级实体）
  const [selectedDocForChunks, setSelectedDocForChunks] = useState(null);

  /**
   * 过滤后的文档列表
   * 支持搜索和状态筛选
   */
  const filteredDocuments = useMemo(() => {
    let result = documents;

    // 状态筛选
    if (docFilterStatus === 'completed') {
      result = result.filter(doc => isEntityExtractionCompleted(doc));
    } else if (docFilterStatus === 'pending') {
      result = result.filter(doc => !isEntityExtractionCompleted(doc));
    }

    // 搜索筛选
    if (docSearchQuery.trim()) {
      const query = docSearchQuery.toLowerCase();
      result = result.filter(doc =>
        doc.title.toLowerCase().includes(query)
      );
    }

    return result;
  }, [documents, docSearchQuery, docFilterStatus]);

  /**
   * 全选文档
   * 只选择已处理完成（processing_status === 'completed'）的文档
   */
  const handleSelectAllDocuments = () => {
    const selectableDocs = filteredDocuments.filter(doc => isDocumentProcessed(doc));
    setSelectedDocuments(selectableDocs.map(doc => doc.id));
    if (selectableDocs.length === 0) {
      message.info({ content: '没有可选择的已处理文档' });
    }
  };

  /**
   * 清除文档选择
   */
  const handleClearDocumentSelection = () => {
    setSelectedDocuments([]);
  };

  // 批量操作状态
  const [selectedEntities, setSelectedEntities] = useState([]);

  /**
   * 全选实体
   */
  const handleSelectAllEntities = () => {
    setSelectedEntities(filteredEntities.map(e => e.id));
  };

  /**
   * 清除实体选择
   */
  const handleClearEntitySelection = () => {
    setSelectedEntities([]);
  };

  /**
   * 切换实体选择
   */
  const toggleEntitySelection = (entityId) => {
    setSelectedEntities(prev =>
      prev.includes(entityId)
        ? prev.filter(id => id !== entityId)
        : [...prev, entityId]
    );
  };

  /**
   * 批量确认实体
   */
  const handleBatchConfirm = async () => {
    const dbEntityIds = selectedEntities.filter(id => !String(id).startsWith('extracted-'));
    const count = selectedEntities.length;

    try {
      // 将数据库中的实体状态更新为 confirmed
      if (dbEntityIds.length > 0) {
        await batchUpdateEntityStatus(dbEntityIds, 'confirmed');
      }

      // 更新前端状态
      setEntities(prev =>
        prev.map(e =>
          selectedEntities.includes(e.id) && e.status === 'pending'
            ? { ...e, status: 'confirmed' }
            : e
        )
      );
      setSelectedEntities([]);
      message.success({ content: `已批量确认 ${count} 个实体` });
    } catch (error) {
      message.error({ content: '批量确认失败：' + error.message });
    }
  };

  /**
   * 批量拒绝实体
   */
  const handleBatchReject = async () => {
    const dbEntityIds = selectedEntities.filter(id => !String(id).startsWith('extracted-'));
    const count = selectedEntities.length;

    try {
      // 将数据库中的实体状态更新为 rejected
      if (dbEntityIds.length > 0) {
        await batchUpdateEntityStatus(dbEntityIds, 'rejected');
      }

      // 更新前端状态
      setEntities(prev =>
        prev.map(e =>
          selectedEntities.includes(e.id) && e.status === 'pending'
            ? { ...e, status: 'rejected' }
            : e
        )
      );
      setSelectedEntities([]);
      message.success({ content: `已批量拒绝 ${count} 个实体` });
    } catch (error) {
      message.error({ content: '批量拒绝失败：' + error.message });
    }
  };

  /**
   * 获取文档列表
   */
  const fetchDocuments = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      const response = await listDocuments(0, 1000, currentKnowledgeBase.id, true);
      setDocuments(response.documents || []);
    } catch (error) {
      message.error({ content: '获取文档列表失败：' + error.message });
    }
  }, [currentKnowledgeBase]);

  /**
   * 从数据库加载知识库的实体
   * 从所有文档中加载实体，包含确认状态
   */
  const loadKnowledgeBaseEntities = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      // 先获取知识库的所有文档
      const docsResponse = await listDocuments(0, 1000, currentKnowledgeBase.id, true);
      const docs = docsResponse.documents || [];

      // 从每个文档加载实体
      const allEntities = [];
      for (const doc of docs) {
        try {
          const response = await getDocumentEntitiesFromMaintenance(doc.id, { pageSize: 1000 });
          if (response && Array.isArray(response.entities)) {
            const docEntities = response.entities.map((entity) => ({
              id: entity.id,  // 使用数据库中的真实ID
              name: entity.text,
              type: entity.type || 'concept',
              description: '',
              documentId: doc.id,
              documentName: doc.title || '未命名文档',
              confidence: entity.confidence || 0.8,
              status: entity.status || 'pending',  // 从数据库读取状态
              occurrences: 1,
              source: 'database',
              modelUsed: '已保存',
            }));
            allEntities.push(...docEntities);
          }
        } catch (docError) {
          console.error(`加载文档 ${doc.id} 的实体失败:`, docError);
        }
      }

      setEntities(allEntities);

      // 检测状态不一致：有实体但文档状态不是 entity_completed
      checkStatusConsistency(allEntities, docs);
    } catch (error) {
      console.error('加载知识库实体失败:', error);
    }
  }, [currentKnowledgeBase]);

  /**
   * 检测文档状态一致性
   * 检查是否有实体但文档状态未更新为 entity_completed 的情况
   */
  const checkStatusConsistency = useCallback((entitiesList, docsList) => {
    if (!entitiesList.length || !docsList.length) {
      setStatusSyncNeeded(false);
      setDocsNeedSync([]);
      return;
    }

    // 按文档ID分组统计实体数量
    const docEntityCount = {};
    entitiesList.forEach(entity => {
      if (entity.documentId) {
        docEntityCount[entity.documentId] = (docEntityCount[entity.documentId] || 0) + 1;
      }
    });

    // 找出有实体但状态不是 entity_completed 的文档
    const needSync = docsList.filter(doc => {
      const hasEntities = docEntityCount[doc.id] > 0;
      const status = doc.document_metadata?.processing_status || doc.processing_status || 'unknown';
      const isCompleted = status === 'entity_completed';
      return hasEntities && !isCompleted;
    });

    setDocsNeedSync(needSync);
    setStatusSyncNeeded(needSync.length > 0);

    if (needSync.length > 0) {
      console.log(`检测到 ${needSync.length} 个文档需要同步状态:`, needSync.map(d => d.title));
    }
  }, []);

  /**
   * 同步文档状态
   * 将有实体但状态未更新的文档状态设置为 entity_completed
   */
  const handleSyncDocumentStatus = useCallback(async () => {
    if (docsNeedSync.length === 0) return;

    setSyncingStatus(true);
    try {
      let successCount = 0;
      for (const doc of docsNeedSync) {
        try {
          await updateDocumentProcessingStatus(doc.id, 'entity_completed');
          successCount++;
        } catch (e) {
          console.warn(`更新文档 ${doc.id} 状态失败:`, e);
        }
      }

      // 刷新文档列表
      await fetchDocuments();

      message.success({ content: `已成功同步 ${successCount} 个文档的状态` });
      setStatusSyncNeeded(false);
      setDocsNeedSync([]);
    } catch (error) {
      message.error({ content: '同步状态失败：' + error.message });
    } finally {
      setSyncingStatus(false);
    }
  }, [docsNeedSync, fetchDocuments]);

  /**
   * 加载默认模型配置
   * 按照优先级获取知识库专属的默认模型：
   * 1. 知识库任务级: knowledge_kb_{kb_id}_extraction
   * 2. 知识库级: knowledge_kb_{kb_id}
   * 3. 任务级: knowledge_extraction
   * 4. 通用知识库级: knowledge
   */
  const loadDefaultModel = useCallback(async () => {
    setLoadingModel(true);
    try {
      if (!currentKnowledgeBase) {
        setDefaultModel(null);
        return null;
      }

      const kbId = currentKnowledgeBase.id;
      const scenes = [
        `knowledge_kb_${kbId}_extraction`,
        `knowledge_kb_${kbId}`,
        'knowledge_extraction',
        'knowledge'
      ];

      let response = null;
      for (const scene of scenes) {
        try {
          console.log(`尝试获取场景 ${scene} 的默认模型`);
          const sceneModel = await defaultModelApi.getSceneDefaultModel(scene);
          if (sceneModel && sceneModel.model_id) {
            console.log(`场景 ${scene} 的默认模型:`, sceneModel);
            response = sceneModel;
            break;
          }
        } catch (error) {
          console.log(`场景 ${scene} 未配置模型，尝试下一个场景`);
        }
      }

      setDefaultModel(response);
      if (!response) {
        message.warning({ content: '未配置知识库场景的默认模型，将使用系统默认配置' });
      }
      return response;
    } catch (error) {
      console.error('获取默认模型失败:', error);
      message.warning({ content: '获取默认模型失败，将使用系统默认配置' });
      setDefaultModel(null);
      return null;
    } finally {
      setLoadingModel(false);
    }
  }, [currentKnowledgeBase]);

  // ==================== 四级架构处理函数 ====================

  /**
   * 更新处理流程状态
   */
  const updateProcessingFlow = (level, status, progress = 0, message = '') => {
    setProcessingFlow(prev => ({
      ...prev,
      [level]: { status, progress, message }
    }));
  };

  /**
   * 步骤1: 片段级实体提取（异步）
   * 对选中的文档进行片段级实体识别
   */
  const handleExtractChunkEntities = useCallback(async () => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    if (selectedDocuments.length === 0) {
      message.warning({ content: '请至少选择一个文档' });
      return;
    }

    updateProcessingFlow('chunk', 'processing', 0, '开始片段级实体提取...');

    try {
      const total = selectedDocuments.length;
      const taskIds = {};  // 存储每个文档的任务ID

      // 更新所有选中文档的状态为实体识别中
      for (const docId of selectedDocuments) {
        try {
          await updateDocumentProcessingStatus(docId, 'entity_processing');
        } catch (e) {
          console.warn(`更新文档 ${docId} 状态失败:`, e);
        }
      }

      // 第一步：为每个文档创建异步任务
      updateProcessingFlow('chunk', 'processing', 5, `正在为 ${total} 个文档创建提取任务...`);
      
      for (const docId of selectedDocuments) {
        const doc = documents.find(d => d.id === docId);
        try {
          console.log(`[批量处理] 创建任务: 文档 ${docId}: ${doc?.title || '未知'}`);
          const result = await extractChunkEntities(docId, 4);
          if (result.task_id) {
            taskIds[docId] = result.task_id;
            console.log(`[批量处理] 任务创建成功: ${result.task_id}`);
          }
        } catch (error) {
          console.error(`[批量处理] 创建任务失败 文档 ${docId}:`, error);
        }
      }

      const createdTasks = Object.keys(taskIds).length;
      if (createdTasks === 0) {
        throw new Error('没有成功创建任何提取任务');
      }

      message.success({ content: `已创建 ${createdTasks} 个提取任务，开始轮询进度...` });

      // 第二步：轮询任务进度
      let allCompleted = false;
      let pollCount = 0;
      const maxPolls = 600;  // 最多轮询600次（约20分钟）
      
      while (!allCompleted && pollCount < maxPolls) {
        await new Promise(resolve => setTimeout(resolve, 2000));  // 每2秒轮询一次
        pollCount++;
        
        let completedCount = 0;
        let failedCount = 0;
        let totalProgress = 0;
        
        for (const docId of Object.keys(taskIds)) {
          const taskId = taskIds[docId];
          try {
            const status = await getExtractTaskStatus(docId, taskId);
            totalProgress += status.progress || 0;
            
            if (status.status === 'completed') {
              completedCount++;
            } else if (status.status === 'failed') {
              failedCount++;
            }
          } catch (e) {
            console.warn(`获取任务状态失败: ${taskId}`, e);
          }
        }
        
        const totalTasks = Object.keys(taskIds).length;
        const avgProgress = Math.round(totalProgress / totalTasks);
        const processedCount = completedCount + failedCount;
        
        updateProcessingFlow(
          'chunk', 
          'processing', 
          avgProgress,
          `处理中: ${processedCount}/${totalTasks} 完成 (${avgProgress}%) | 成功: ${completedCount}, 失败: ${failedCount}`
        );
        
        // 检查是否全部完成
        if (processedCount === totalTasks) {
          allCompleted = true;
        }
        
        // 每30秒显示一次进度消息
        if (pollCount % 15 === 0) {
          message.info({ 
            content: `实体提取进度: ${avgProgress}% (${processedCount}/${totalTasks})`,
            duration: 3 
          });
        }
      }

      if (!allCompleted) {
        message.warning({ content: '轮询超时，部分任务可能仍在后台运行' });
      } else {
        updateProcessingFlow('chunk', 'completed', 100, `完成！共处理 ${createdTasks} 个文档`);
        message.success({ content: `片段级实体提取完成，共处理 ${createdTasks} 个文档` });
      }

      // 自动进入下一步
      updateProcessingFlow('document', 'idle', 0, '等待开始文档级聚合...');
    } catch (error) {
      console.error('片段级实体提取失败:', error);
      updateProcessingFlow('chunk', 'failed', 0, `失败: ${error.message}`);

      // 更新失败的文档状态
      for (const docId of selectedDocuments) {
        try {
          await updateDocumentProcessingStatus(docId, 'entity_failed');
        } catch (e) {
          console.warn(`更新文档 ${docId} 失败状态失败:`, e);
        }
      }

      message.error({ content: '片段级实体提取失败：' + error.message });
    }
  }, [currentKnowledgeBase, selectedDocuments, documents]);

  /**
   * 步骤2: 文档级实体聚合
   * 将片段级实体聚合成文档级实体
   */
  const handleAggregateDocumentEntities = useCallback(async () => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    if (selectedDocuments.length === 0) {
      message.warning({ content: '请至少选择一个文档' });
      return;
    }

    updateProcessingFlow('document', 'processing', 0, '开始文档级实体聚合...');

    try {
      let completed = 0;
      let totalEntities = 0;
      const total = selectedDocuments.length;

      // 更新所有选中文档的状态为实体聚合中
      for (const docId of selectedDocuments) {
        try {
          await updateDocumentProcessingStatus(docId, 'entity_aggregating');
        } catch (e) {
          console.warn(`更新文档 ${docId} 状态失败:`, e);
        }
      }

      for (const docId of selectedDocuments) {
        const doc = documents.find(d => d.id === docId);
        updateProcessingFlow('document', 'processing', Math.round((completed / total) * 100), `正在聚合: ${doc?.title || docId}`);

        try {
          console.log(`[批量聚合] 开始聚合文档 ${docId}: ${doc?.title || '未知'}`);
          const result = await aggregateDocumentEntities(docId);
          totalEntities += result.entities_created || 0;
          console.log(`[批量聚合] 完成聚合文档 ${docId}, 生成 ${result.entities_created || 0} 个实体`);
          completed++;
        } catch (error) {
          console.error(`[批量聚合] 聚合文档 ${docId} 失败:`, error);
          // 继续处理下一个文档，不中断流程
        }
      }

      updateProcessingFlow('document', 'completed', 100, `完成！共生成 ${totalEntities} 个文档级实体`);
      message.success({ content: `文档级实体聚合完成，共生成 ${totalEntities} 个实体` });

      // 自动进入下一步
      updateProcessingFlow('kb', 'idle', 0, '等待开始知识库级对齐...');
    } catch (error) {
      console.error('文档级实体聚合失败:', error);
      updateProcessingFlow('document', 'failed', 0, `失败: ${error.message}`);

      // 更新失败的文档状态
      for (const docId of selectedDocuments) {
        try {
          await updateDocumentProcessingStatus(docId, 'entity_failed');
        } catch (e) {
          console.warn(`更新文档 ${docId} 失败状态失败:`, e);
        }
      }

      message.error({ content: '文档级实体聚合失败：' + error.message });
    }
  }, [currentKnowledgeBase, selectedDocuments, documents]);

  /**
   * 步骤3: 知识库级实体对齐
   * 将文档级实体对齐到知识库级实体
   */
  const handleAlignKBEntities = useCallback(async () => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    updateProcessingFlow('kb', 'processing', 0, '开始知识库级实体对齐...');

    try {
      // 更新所有选中文档的状态为实体对齐中
      for (const docId of selectedDocuments) {
        try {
          await updateDocumentProcessingStatus(docId, 'entity_aligning');
        } catch (e) {
          console.warn(`更新文档 ${docId} 状态失败:`, e);
        }
      }

      const result = await alignKnowledgeBaseEntities(currentKnowledgeBase.id, false);

      updateProcessingFlow('kb', 'completed', 100, `完成！共生成 ${result.kb_entities_created || 0} 个知识库级实体`);
      message.success({ content: `知识库级实体对齐完成，共生成 ${result.kb_entities_created || 0} 个实体` });

      // 自动进入下一步
      updateProcessingFlow('global', 'idle', 0, '等待开始全局级对齐...');
    } catch (error) {
      console.error('知识库级实体对齐失败:', error);
      updateProcessingFlow('kb', 'failed', 0, `失败: ${error.message}`);

      // 更新失败的文档状态
      for (const docId of selectedDocuments) {
        try {
          await updateDocumentProcessingStatus(docId, 'entity_failed');
        } catch (e) {
          console.warn(`更新文档 ${docId} 失败状态失败:`, e);
        }
      }

      message.error({ content: '知识库级实体对齐失败：' + error.message });
    }
  }, [currentKnowledgeBase, selectedDocuments]);

  /**
   * 步骤4: 全局级实体对齐
   * 将知识库级实体对齐到全局级实体
   * 注：此功能需要后端实现全局级对齐API
   */
  const handleAlignGlobalEntities = useCallback(async () => {
    updateProcessingFlow('global', 'processing', 0, '开始全局级实体对齐...');

    // 模拟全局级对齐（需要后端实现）
    return new Promise((resolve) => {
      setTimeout(() => {
        updateProcessingFlow('global', 'completed', 100, '完成！全局级对齐功能待后端实现');
        message.info({ content: '全局级实体对齐功能需要后端API支持' });
        resolve();
      }, 2000);
    });
  }, []);

  /**
   * 执行完整的四级处理流程
   * 批量处理所有选中的文档
   */
  const handleRunFullPipeline = useCallback(async () => {
    if (selectedDocuments.length === 0) {
      message.warning({ content: '请至少选择一个文档' });
      return;
    }

    // 重置所有状态
    setProcessingFlow({
      chunk: { status: 'idle', progress: 0, message: '' },
      document: { status: 'idle', progress: 0, message: '' },
      kb: { status: 'idle', progress: 0, message: '' },
      global: { status: 'idle', progress: 0, message: '' }
    });

    try {
      // 依次执行四个步骤
      await handleExtractChunkEntities();
      await handleAggregateDocumentEntities();
      await handleAlignKBEntities();
      await handleAlignGlobalEntities();

      // 所有步骤完成后，更新所有选中文档状态为已实体识别
      message.loading(`正在更新 ${selectedDocuments.length} 个文档的状态...`);

      let successCount = 0;
      for (const docId of selectedDocuments) {
        try {
          await updateDocumentProcessingStatus(docId, 'entity_completed');
          successCount++;
        } catch (error) {
          console.error(`更新文档 ${docId} 状态失败:`, error);
        }
      }

      message.destroy();
      message.success({ content: `已完成 ${successCount}/${selectedDocuments.length} 个文档的实体识别` });

      // 刷新文档列表以显示最新状态
      if (currentKnowledgeBase) {
        try {
          const response = await listDocuments(0, 1000, currentKnowledgeBase.id, true);
          setDocuments(response.documents || []);
        } catch (err) {
          console.error('刷新文档列表失败:', err);
        }
      }

      // 刷新实体列表
      await loadKnowledgeBaseEntities();

    } catch (error) {
      message.destroy();
      console.error('实体识别流程失败:', error);
      message.error({ content: '实体识别流程失败：' + error.message });
    }
  }, [handleExtractChunkEntities, handleAggregateDocumentEntities, handleAlignKBEntities, handleAlignGlobalEntities, selectedDocuments, currentKnowledgeBase, loadKnowledgeBaseEntities]);

  /**
   * 加载指定层级的实体数据
   */
  const loadEntitiesByLevel = useCallback(async (level) => {
    if (!currentKnowledgeBase) return;

    try {
      switch (level) {
        case 'chunk':
          // 片段级实体需要选择具体文档
          if (selectedDocForChunks) {
            const result = await getDocumentChunkEntities(selectedDocForChunks);
            setChunkEntities(result.entities || []);
          }
          break;
        case 'document':
          // 加载所有选中文档的文档级实体
          const docEntities = [];
          for (const docId of selectedDocuments) {
            try {
              const result = await getDocumentEntitiesNew(docId);
              docEntities.push(...(result.entities || []).map(e => ({ ...e, documentId: docId })));
            } catch (e) {
              console.warn(`获取文档 ${docId} 实体失败:`, e);
            }
          }
          setDocumentEntities(docEntities);
          break;
        case 'kb':
          // 知识库级实体
          // 需要后端提供获取KB级实体的API
          message.info({ content: '知识库级实体查看功能开发中' });
          break;
        case 'global':
          // 全局级实体
          message.info({ content: '全局级实体查看功能开发中' });
          break;
        default:
          break;
      }
    } catch (error) {
      console.error(`加载${level}级实体失败:`, error);
      message.error({ content: `加载${level}级实体失败` });
    }
  }, [currentKnowledgeBase, selectedDocuments, selectedDocForChunks]);

  /**
   * 切换实体层级时加载对应数据
   */
  useEffect(() => {
    loadEntitiesByLevel(entityLevel);
  }, [entityLevel, loadEntitiesByLevel]);

  /**
   * 应用筛选
   */
  useEffect(() => {
    let result = [...entities];

    // 类型筛选
    if (filterType !== 'all') {
      result = result.filter(e => e.type === filterType);
    }

    // 状态筛选
    if (filterStatus !== 'all') {
      result = result.filter(e => e.status === filterStatus);
    }

    // 搜索筛选
    if (debouncedSearchQuery.trim()) {
      const query = debouncedSearchQuery.toLowerCase();
      result = result.filter(e =>
        e.name.toLowerCase().includes(query) ||
        e.description.toLowerCase().includes(query)
      );
    }

    setFilteredEntities(result);
  }, [entities, filterType, filterStatus, debouncedSearchQuery]);

  /**
   * 切换文档选择
   */
  const toggleDocumentSelection = (docId) => {
    setSelectedDocuments(prev =>
      prev.includes(docId)
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  /**
   * 确认实体
   */
  const handleConfirmEntity = async (entityId) => {
    try {
      // 如果是数据库中的实体（非临时提取的），更新后端状态
      if (!String(entityId).startsWith('extracted-')) {
        await updateEntityStatus(entityId, 'confirmed');
      }

      setEntities(prev =>
        prev.map(e => e.id === entityId ? { ...e, status: 'confirmed' } : e)
      );
      message.success({ content: '实体已确认' });
    } catch (error) {
      message.error({ content: '确认实体失败：' + error.message });
    }
  };

  /**
   * 拒绝实体
   */
  const handleRejectEntity = async (entityId) => {
    try {
      // 如果是数据库中的实体（非临时提取的），更新后端状态
      if (!String(entityId).startsWith('extracted-')) {
        await updateEntityStatus(entityId, 'rejected');
      }

      setEntities(prev =>
        prev.map(e => e.id === entityId ? { ...e, status: 'rejected' } : e)
      );
      message.success({ content: '实体已拒绝' });
    } catch (error) {
      message.error({ content: '拒绝实体失败：' + error.message });
    }
  };

  /**
   * 开始编辑实体
   */
  const handleStartEdit = (entity) => {
    setEditingEntity(entity.id);
    setEditForm({
      name: entity.name,
      type: entity.type,
      description: entity.description,
    });
  };

  /**
   * 保存实体编辑
   */
  const handleSaveEdit = (entityId) => {
    setEntities(prev =>
      prev.map(e =>
        e.id === entityId
          ? { ...e, ...editForm, status: 'modified' }
          : e
      )
    );
    setEditingEntity(null);
    message.success({ content: '实体已更新' });
  };

  /**
   * 取消编辑
   */
  const handleCancelEdit = () => {
    setEditingEntity(null);
    setEditForm({ name: '', type: '', description: '' });
  };

  /**
   * 删除实体
   */
  const [deleteConfirmVisible, setDeleteConfirmVisible] = useState(false);
  const [entityToDelete, setEntityToDelete] = useState(null);

  const handleDeleteEntity = (entityId) => {
    setEntityToDelete(entityId);
    setDeleteConfirmVisible(true);
  };

  const confirmDeleteEntity = () => {
    if (entityToDelete) {
      setEntities(prev => prev.filter(e => e.id !== entityToDelete));
      message.success({ content: '实体已删除' });
    }
    setDeleteConfirmVisible(false);
    setEntityToDelete(null);
  };

  const cancelDeleteEntity = () => {
    setDeleteConfirmVisible(false);
    setEntityToDelete(null);
  };

  /**
   * 渲染实体项
   */
  const renderEntity = useCallback((entity) => {
    const typeConfig = ENTITY_TYPES.find(t => t.value === entity.type) || ENTITY_TYPES[5];
    const statusConfig = ENTITY_STATUS[entity.status] || ENTITY_STATUS.pending;
    const isEditing = editingEntity === entity.id;

    return (
      <div key={entity.id} className={`entity-item ${entity.status}`}>
        {isEditing ? (
          <div className="entity-edit-form">
            <input
              type="text"
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              className="edit-input"
              placeholder="实体名称"
            />
            <select
              value={editForm.type}
              onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
              className="edit-select"
            >
              {ENTITY_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={editForm.description}
              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              className="edit-input"
              placeholder="描述（可选）"
            />
            <div className="edit-actions">
              <button className="save-btn" onClick={() => handleSaveEdit(entity.id)} aria-label="保存修改">
                <FiCheck size={16} />
              </button>
              <button className="cancel-btn" onClick={handleCancelEdit} aria-label="取消编辑">
                <FiX size={16} />
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* 批量选择框 */}
            <div className="entity-checkbox">
              <input
                type="checkbox"
                checked={selectedEntities.includes(entity.id)}
                onChange={() => toggleEntitySelection(entity.id)}
              />
            </div>
            
            <div className="entity-info">
              <div className="entity-header">
                <span
                  className="entity-type-badge"
                  style={{ backgroundColor: typeConfig.color + '20', color: typeConfig.color }}
                >
                  {typeConfig.label}
                </span>
                <span
                  className="entity-status-badge"
                  style={{ backgroundColor: statusConfig.bgColor, color: statusConfig.color }}
                >
                  {statusConfig.label}
                </span>
              </div>
              <h4 className="entity-name">{entity.name}</h4>
              {entity.description && (
                <p className="entity-description">{entity.description}</p>
              )}
              <div className="entity-meta">
                <span>来源: {entity.documentName}</span>
                <span>置信度: {(entity.confidence * 100).toFixed(1)}%</span>
                <span>出现次数: {entity.occurrences}</span>
              </div>
            </div>
            <div className="entity-actions">
              {entity.status === 'pending' && (
                <>
                  <button
                    className="action-btn confirm"
                    onClick={() => handleConfirmEntity(entity.id)}
                    title="确认"
                    aria-label="确认实体"
                  >
                    <FiCheck size={16} />
                  </button>
                  <button
                    className="action-btn reject"
                    onClick={() => handleRejectEntity(entity.id)}
                    title="拒绝"
                    aria-label="拒绝实体"
                  >
                    <FiX size={16} />
                  </button>
                </>
              )}
              <button
                className="action-btn edit"
                onClick={() => handleStartEdit(entity)}
                title="编辑"
                aria-label="编辑实体"
              >
                <FiEdit2 size={16} />
              </button>
              <button
                className="action-btn delete"
                onClick={() => handleDeleteEntity(entity.id)}
                title="删除"
                aria-label="删除实体"
              >
                <FiTrash2 size={16} />
              </button>
            </div>
          </>
        )}
      </div>
    );
  }, [editingEntity, editForm, selectedEntities]);

  // 初始加载 - 当选择知识库时加载文档和实体
  useEffect(() => {
    if (currentKnowledgeBase) {
      fetchDocuments();
      loadKnowledgeBaseEntities();
      loadDefaultModel();
    }
  }, [currentKnowledgeBase, fetchDocuments, loadKnowledgeBaseEntities, loadDefaultModel]);

  // 统计信息
  const stats = {
    total: entities.length,
    pending: entities.filter(e => e.status === 'pending').length,
    confirmed: entities.filter(e => e.status === 'confirmed').length,
    rejected: entities.filter(e => e.status === 'rejected').length,
    modified: entities.filter(e => e.status === 'modified').length,
  };

  if (!currentKnowledgeBase) {
    return (
      <div className="entity-recognition-empty">
        <div className="empty-icon">🔍</div>
        <h3>请选择一个知识库</h3>
        <p>从左侧边栏选择一个知识库开始实体识别</p>
        
        <div className="empty-actions">
          <Button
            variant="primary"
            onClick={() => navigate('/knowledge/documents')}
            icon={<FiFolder />}
          >
            前往知识库管理
          </Button>
        </div>
        
        <div className="empty-guide">
          <h4>使用步骤</h4>
          <ol>
            <li>选择或创建一个知识库</li>
            <li>上传文档到知识库</li>
            <li>选择文档进行实体提取</li>
            <li>确认或编辑提取的实体</li>
          </ol>
        </div>
      </div>
    );
  }

  return (
    <div className="entity-recognition">
      {/* 统计卡片 */}
      <div className="stats-cards">
        <div className="stat-card">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">总实体</span>
        </div>
        <div className="stat-card pending">
          <span className="stat-value">{stats.pending}</span>
          <span className="stat-label">待确认</span>
        </div>
        <div className="stat-card confirmed">
          <span className="stat-value">{stats.confirmed}</span>
          <span className="stat-label">已确认</span>
        </div>
        <div className="stat-card rejected">
          <span className="stat-value">{stats.rejected}</span>
          <span className="stat-label">已拒绝</span>
        </div>
        <div className="stat-card modified">
          <span className="stat-value">{stats.modified}</span>
          <span className="stat-label">已修改</span>
        </div>
      </div>

      {/* ==================== 主内容区域 - 左右布局 ==================== */}
      <div className="entity-recognition-main">

        {/* 左侧：文档选择区域 */}
        <div className="document-selection">
          <div className="selection-header">
            <h4>选择要处理的文档</h4>
          </div>

          {/* 文档搜索和选择操作 */}
          <div className="document-list-header">
            <div className="doc-search">
              <FiSearch size={14} />
              <input
                type="text"
                placeholder="搜索文档..."
                value={docSearchQuery}
                onChange={(e) => setDocSearchQuery(e.target.value)}
              />
            </div>
            <div className="doc-filter">
              <select
                value={docFilterStatus}
                onChange={(e) => setDocFilterStatus(e.target.value)}
                className="filter-select"
              >
                <option value="all">全部文档</option>
                <option value="pending">待识别</option>
                <option value="completed">已识别</option>
              </select>
            </div>
            <div className="selection-actions">
              <Button size="small" variant="ghost" onClick={handleSelectAllDocuments}>
                全选
              </Button>
              <Button size="small" variant="ghost" onClick={handleClearDocumentSelection}>
                清除
              </Button>
              <span className="selected-count">
                已选 {selectedDocuments.length} / {filteredDocuments.length} 个
              </span>
            </div>
          </div>

          <div className="document-list">
            {filteredDocuments.map(doc => {
              const docStatus = getDocumentStatus(doc);
              const canSelect = docStatus.canSelect;
              return (
                <label
                  key={doc.id}
                  className={`document-checkbox ${!canSelect ? 'not-processed' : ''}`}
                  title={!canSelect ? `文档状态：${docStatus.label}，请先在文档管理页面处理文档` : ''}
                >
                  <input
                    type="checkbox"
                    checked={selectedDocuments.includes(doc.id)}
                    onChange={() => toggleDocumentSelection(doc.id)}
                    disabled={!canSelect}
                  />
                  <span className="document-name">{doc.title}</span>
                  <span className="document-type">{doc.file_type}</span>
                  <span
                    className="document-status"
                    style={{
                      color: docStatus.color,
                      backgroundColor: docStatus.bgColor,
                      borderColor: docStatus.borderColor,
                      border: '1px solid'
                    }}
                  >
                    {docStatus.label}
                  </span>
                </label>
              );
            })}
            {filteredDocuments.length === 0 && documents.length > 0 && (
              <div className="no-results">没有匹配的文档</div>
            )}
            {documents.length === 0 && (
              <div className="no-documents">暂无文档，请先上传文档到知识库</div>
            )}
          </div>
        </div>

        {/* 右侧：实体列表区域 */}
        <div className="entities-section">
          {/* 状态同步提示 */}
          {statusSyncNeeded && (
            <div className="status-sync-notice">
              <span className="sync-text">
                检测到 {docsNeedSync.length} 个文档已有实体但状态未同步
              </span>
              <Button
                variant="primary"
                size="small"
                onClick={handleSyncDocumentStatus}
                loading={syncingStatus}
                disabled={syncingStatus}
              >
                {syncingStatus ? '同步中...' : '同步状态'}
              </Button>
            </div>
          )}

          {/* 操作栏 - 包含实体配置和识别处理 */}
          <div className="entity-actions-bar">
            <div className="actions-left">
              {/* 一键识别实体按钮 - 核心操作放在左侧显眼位置 */}
              <Button
                variant="primary"
                size="small"
                icon={<FiLayers />}
                onClick={handleRunFullPipeline}
                disabled={selectedDocuments.length === 0 || isProcessing}
                loading={isProcessing}
                className="extract-btn"
              >
                {isProcessing ? '处理中...' : (extractConfig.extractRelationships ? '一键识别实体和关系' : '一键识别实体')}
              </Button>
              {/* 配置按钮 */}
              <Button
                variant={showConfigPanel ? 'primary' : 'ghost'}
                size="small"
                icon={<FiSettings />}
                onClick={() => setShowConfigPanel(!showConfigPanel)}
              >
                提取配置
              </Button>
            </div>
            <div className="actions-right">
              {/* 模型信息 */}
              <div className="model-info-compact">
                <FiBox size={14} />
                {loadingModel ? (
                  <span className="model-loading">加载中...</span>
                ) : defaultModel ? (
                  <span className="model-name">{defaultModel.model_name || defaultModel.name || '默认模型'}</span>
                ) : (
                  <span className="model-warning">未配置模型</span>
                )}
              </div>
              {/* 实体配置按钮 */}
              <Button
                variant="ghost"
                size="small"
                icon={<FiSettings />}
                onClick={() => setConfigModalVisible(true)}
              >
                实体配置
              </Button>
            </div>
          </div>

          {/* 提取配置面板 */}
          {showConfigPanel && (
            <div className="extract-config-panel">
              <div className="config-section">
                <h4>处理模式</h4>
                <div className="mode-selector">
                  <label className={`mode-option ${extractConfig.processingMode === 'speed' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="processingMode"
                      value="speed"
                      checked={extractConfig.processingMode === 'speed'}
                      onChange={(e) => setExtractConfig(prev => ({
                        ...prev,
                        processingMode: e.target.value,
                        extractRelationships: false
                      }))}
                    />
                    <span className="mode-name">速度模式</span>
                    <span className="mode-desc">快速处理，不提取关系</span>
                  </label>
                  <label className={`mode-option ${extractConfig.processingMode === 'standard' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="processingMode"
                      value="standard"
                      checked={extractConfig.processingMode === 'standard'}
                      onChange={(e) => setExtractConfig(prev => ({
                        ...prev,
                        processingMode: e.target.value,
                        extractRelationships: false
                      }))}
                    />
                    <span className="mode-name">标准模式</span>
                    <span className="mode-desc">平衡速度和质量</span>
                  </label>
                  <label className={`mode-option ${extractConfig.processingMode === 'quality' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="processingMode"
                      value="quality"
                      checked={extractConfig.processingMode === 'quality'}
                      onChange={(e) => setExtractConfig(prev => ({
                        ...prev,
                        processingMode: e.target.value,
                        extractRelationships: true
                      }))}
                    />
                    <span className="mode-name">质量模式</span>
                    <span className="mode-desc">高质量提取，包含关系</span>
                  </label>
                </div>
              </div>

              <div className="config-section">
                <h4>提取选项</h4>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={extractConfig.extractEntities}
                    onChange={(e) => setExtractConfig(prev => ({ ...prev, extractEntities: e.target.checked }))}
                  />
                  <span>提取实体</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={extractConfig.extractRelationships}
                    onChange={(e) => setExtractConfig(prev => ({ ...prev, extractRelationships: e.target.checked }))}
                  />
                  <span>提取关系</span>
                </label>
              </div>

              <div className="config-section">
                <h4>置信度阈值</h4>
                <div className="threshold-control">
                  <input
                    type="range"
                    min="0.1"
                    max="1.0"
                    step="0.1"
                    value={extractConfig.threshold}
                    onChange={(e) => setExtractConfig(prev => ({ ...prev, threshold: parseFloat(e.target.value) }))}
                  />
                  <span className="threshold-value">{(extractConfig.threshold * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          )}

          {/* 处理进度条 */}
          {isProcessing && (
            <div className="processing-progress-bar">
              <div className="progress-steps-compact">
                {[
                  { key: 'chunk', label: '片段提取' },
                  { key: 'document', label: '文档聚合' },
                  { key: 'kb', label: '知识库对齐' },
                  { key: 'global', label: '全局对齐' }
                ].map((step, index) => {
                  const status = processingFlow[step.key].status;
                  return (
                    <div key={step.key} className={`step-compact ${status}`}>
                      <span className="step-num">{index + 1}</span>
                      <span className="step-label">{step.label}</span>
                      {status === 'completed' && <FiCheck size={12} />}
                      {status === 'processing' && <span className="step-dot" />}
                    </div>
                  );
                })}
              </div>
              {/* 当前处理文档信息 */}
              <div className="processing-message">
                {processingFlow.chunk.status === 'processing' && (
                  <span>
                    <strong>片段提取：</strong>
                    {processingFlow.chunk.message || '正在处理...'}
                    {processingFlow.chunk.progress > 0 && ` (${processingFlow.chunk.progress}%)`}
                  </span>
                )}
                {processingFlow.document.status === 'processing' && (
                  <span>
                    <strong>文档聚合：</strong>
                    {processingFlow.document.message || '正在处理...'}
                    {processingFlow.document.progress > 0 && ` (${processingFlow.document.progress}%)`}
                  </span>
                )}
                {processingFlow.kb.status === 'processing' && (
                  <span>
                    <strong>知识库对齐：</strong>
                    {processingFlow.kb.message || '正在处理...'}
                    {processingFlow.kb.progress > 0 && ` (${processingFlow.kb.progress}%)`}
                  </span>
                )}
                {processingFlow.global.status === 'processing' && (
                  <span>
                    <strong>全局对齐：</strong>
                    {processingFlow.global.message || '正在处理...'}
                    {processingFlow.global.progress > 0 && ` (${processingFlow.global.progress}%)`}
                  </span>
                )}
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{
                    width: `${(
                      (processingFlow.chunk.status === 'completed' ? 25 : processingFlow.chunk.progress * 0.25) +
                      (processingFlow.document.status === 'completed' ? 25 : processingFlow.document.progress * 0.25) +
                      (processingFlow.kb.status === 'completed' ? 25 : processingFlow.kb.progress * 0.25) +
                      (processingFlow.global.status === 'completed' ? 25 : processingFlow.global.progress * 0.25)
                    )}%`
                  }}
                />
              </div>
            </div>
          )}

          {/* 实体层级切换 - 简化版 */}
          <div className="entity-level-bar">
            <div className="level-tabs-compact">
              {[
                { key: 'document', label: '文档级', icon: FiDatabase, count: documentEntities.length },
                { key: 'chunk', label: '片段级', icon: FiFileText, count: chunkEntities.length },
                { key: 'kb', label: '知识库级', icon: FiLayers, count: kbEntities.length },
              ].map(level => {
                const Icon = level.icon;
                return (
                  <button
                    key={level.key}
                    className={`level-tab-compact ${entityLevel === level.key ? 'active' : ''}`}
                    onClick={() => setEntityLevel(level.key)}
                  >
                    <Icon size={14} />
                    <span>{level.label}</span>
                    {level.count > 0 && <span className="level-count">{level.count}</span>}
                  </button>
                );
              })}
            </div>

            {/* 片段级实体查看时的文档选择 */}
            {entityLevel === 'chunk' && (
              <div className="chunk-doc-select">
                <select
                  value={selectedDocForChunks || ''}
                  onChange={(e) => setSelectedDocForChunks(e.target.value ? parseInt(e.target.value) : null)}
                >
                  <option value="">选择文档查看片段实体</option>
                  {documents.map(doc => (
                    <option key={doc.id} value={doc.id}>{doc.title}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

        {/* 筛选栏 */}
        <div className="filter-bar">
          <div className="search-box">
            <FiSearch size={16} />
            <input
              type="text"
              placeholder="搜索实体..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">全部类型</option>
              {ENTITY_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">全部状态</option>
              <option value="pending">待确认</option>
              <option value="confirmed">已确认</option>
              <option value="rejected">已拒绝</option>
              <option value="modified">已修改</option>
            </select>
          </div>
        </div>

        {/* 批量操作栏 */}
        {entities.length > 0 && (
          <div className="batch-actions-bar">
            <label className="batch-checkbox">
              <input
                type="checkbox"
                checked={selectedEntities.length === filteredEntities.length && filteredEntities.length > 0}
                ref={input => {
                  if (input) {
                    input.indeterminate = selectedEntities.length > 0 && selectedEntities.length < filteredEntities.length;
                  }
                }}
                onChange={(e) => e.target.checked ? handleSelectAllEntities() : handleClearEntitySelection()}
              />
              <span>全选</span>
            </label>

            <span className="selection-info">
              已选择 {selectedEntities.length} 个实体
            </span>

            <Button
              size="small"
              variant="primary"
              disabled={selectedEntities.length === 0}
              onClick={handleBatchConfirm}
            >
              批量确认
            </Button>

            <Button
              size="small"
              variant="danger"
              disabled={selectedEntities.length === 0}
              onClick={handleBatchReject}
            >
              批量拒绝
            </Button>
          </div>
        )}

        {/* 实体列表 */}
        <div className="entities-list-container">
          <VirtualListEnhanced
            items={filteredEntities}
            renderItem={renderEntity}
            estimateSize={100}
            overscan={10}
            emptyText={
              <div className="empty-state">
                <div className="empty-icon">📋</div>
                <h3>暂无实体</h3>
                <p>选择文档并开始实体提取</p>
              </div>
            }
          />
        </div>
      </div>

      </div>

      {/* 实体配置弹窗 */}
      <EntityConfigModal
        isOpen={configModalVisible}
        onClose={() => setConfigModalVisible(false)}
        knowledgeBaseId={currentKnowledgeBase?.id}
      />

      {/* 删除确认弹窗 */}
      <Modal
        isOpen={deleteConfirmVisible}
        onClose={cancelDeleteEntity}
        title="确认删除"
        size="small"
        footer={
          <>
            <Button variant="ghost" onClick={cancelDeleteEntity}>
              取消
            </Button>
            <Button variant="danger" onClick={confirmDeleteEntity}>
              确认删除
            </Button>
          </>
        }
      >
        <div className="delete-confirm-content">
          <div className="delete-icon">🗑️</div>
          <p>确定要删除这个实体吗？</p>
          <p className="delete-hint">此操作无法撤销</p>
        </div>
      </Modal>
    </div>
  );
};

export default EntityRecognition;
