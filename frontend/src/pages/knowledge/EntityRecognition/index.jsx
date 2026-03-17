/**
 * 实体识别页面
 *
 * 提供实体提取、确认、编辑功能，支持从文档中自动识别实体
 */

import React, { useEffect, useCallback, useState, useMemo } from 'react';
import { FiCpu, FiCheck, FiX, FiEdit2, FiTrash2, FiRefreshCw, FiFilter, FiSearch, FiBox, FiSettings, FiFolder } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { VirtualListEnhanced } from '../../../components/UI';
import Modal from '../../../components/UI/Modal';
import { message } from '../../../components/UI/Message/Message';
import EntityConfigModal from '../../../components/Knowledge/EntityConfigModal';
import {
  listDocuments,
  extractEntities,
  getDocument,
  getDocumentChunks,
  getKnowledgeBaseEntities,
  batchUpdateEntityStatus,
  updateEntityStatus,
  getDocumentEntitiesFromMaintenance
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
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractProgress, setExtractProgress] = useState(0);
  const [extractStage, setExtractStage] = useState('');
  const [processedDocs, setProcessedDocs] = useState(0);

  // 默认模型状态
  const [defaultModel, setDefaultModel] = useState(null);
  const [loadingModel, setLoadingModel] = useState(false);

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

  // 文档搜索状态
  const [docSearchQuery, setDocSearchQuery] = useState('');

  /**
   * 过滤后的文档列表
   */
  const filteredDocuments = useMemo(() => {
    if (!docSearchQuery.trim()) return documents;
    const query = docSearchQuery.toLowerCase();
    return documents.filter(doc =>
      doc.title.toLowerCase().includes(query)
    );
  }, [documents, docSearchQuery]);

  /**
   * 全选文档
   */
  const handleSelectAllDocuments = () => {
    setSelectedDocuments(filteredDocuments.map(doc => doc.id));
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
    } catch (error) {
      console.error('加载知识库实体失败:', error);
    }
  }, [currentKnowledgeBase]);

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
        return;
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
    } catch (error) {
      console.error('获取默认模型失败:', error);
      message.warning({ content: '获取默认模型失败，将使用系统默认配置' });
      setDefaultModel(null);
    } finally {
      setLoadingModel(false);
    }
  }, [currentKnowledgeBase]);

  /**
   * 执行实体提取 - 逐个文档处理并保存到数据库
   */
  const handleExtractEntities = useCallback(async () => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择一个知识库' });
      return;
    }

    if (selectedDocuments.length === 0) {
      message.warning({ content: '请至少选择一个文档' });
      return;
    }

    setExtracting(true);
    setExtractProgress(0);
    setExtractStage('准备中...');
    setProcessedDocs(0);

    try {
      // 获取默认模型配置
      setExtractStage('获取模型配置...');
      const currentDefaultModel = defaultModel || await loadDefaultModel();

      let totalExtractedEntities = 0;
      const allExtractedEntities = [];

      // 逐个文档处理
      for (let i = 0; i < selectedDocuments.length; i++) {
        const docId = selectedDocuments[i];
        try {
          // 获取文档详情以获取文档名称
          const docDetail = await getDocument(docId);
          
          setExtractStage(`处理文档 ${i + 1}/${selectedDocuments.length}: ${docDetail.title}`);

          // 构建实体提取参数 - 使用 document_id 参数（这样会自动保存到数据库）
          const extractParams = {
            document_id: docId,
            entity_types: ENTITY_TYPES.map(t => t.value),
            threshold: 0.7,
            use_llm: true,
            knowledge_base_id: currentKnowledgeBase.id,
          };

          // 如果有默认模型配置，添加到参数中
          if (currentDefaultModel && currentDefaultModel.model_id) {
            extractParams.model_id = currentDefaultModel.model_id.toString();
            extractParams.model_configuration = {
              temperature: currentDefaultModel.temperature || 0.3,
              max_tokens: currentDefaultModel.max_tokens || 2000,
            };
          }

          // 调用实体提取 API
          const response = await extractEntities(extractParams);

          // 处理提取结果
          console.log('API 响应:', response);
          console.log('API 响应实体:', response.entities);
          const documentEntities = (response.entities || []).map((entity, index) => ({
            id: `entity-${Date.now()}-${i}-${index}`,
            name: entity.name || entity.text,
            type: entity.type || 'concept',
            description: entity.description || '',
            documentId: docId,
            documentName: docDetail.title || '未命名文档',
            confidence: entity.confidence || entity.score || 0.8,
            status: 'pending',
            occurrences: entity.occurrences || 1,
            source: 'llm',
            modelUsed: currentDefaultModel?.model_name || '默认模型',
          }));
          console.log('处理后的实体:', documentEntities);

          totalExtractedEntities += documentEntities.length;
          allExtractedEntities.push(...documentEntities);

        } catch (error) {
          console.error(`处理文档 ${docId} 失败:`, error);
          message.warning({ content: `文档 ${docId} 处理失败: ${error.message}` });
        }

        setProcessedDocs(i + 1);
        setExtractProgress(Math.round(((i + 1) / selectedDocuments.length) * 100));
      }

      // 将所有提取的实体添加到前端状态，去重并保留已确认的实体
      setEntities(prev => {
        // 创建一个映射，键为实体文本和类型的组合，值为实体对象
        const entityMap = new Map();
        
        // 先添加现有实体，已确认的实体优先级更高
        prev.forEach(entity => {
          const key = `${entity.name}-${entity.type}-${entity.documentId}`;
          // 只保留已确认的实体或不在新提取列表中的实体
          if (entity.status === 'confirmed' || !allExtractedEntities.some(e => 
            e.name === entity.name && e.type === entity.type && e.documentId === entity.documentId
          )) {
            entityMap.set(key, entity);
          }
        });
        
        // 添加新提取的实体，跳过已确认的实体
        allExtractedEntities.forEach(entity => {
          const key = `${entity.name}-${entity.type}-${entity.documentId}`;
          // 只有当该实体尚未被确认时才添加
          if (!entityMap.has(key)) {
            entityMap.set(key, entity);
          }
        });
        
        // 转换回数组
        return Array.from(entityMap.values());
      });
      setExtractStage('完成');
      setExtractProgress(100);
      message.success({ content: `成功从 ${selectedDocuments.length} 个文档中提取 ${totalExtractedEntities} 个实体` });
    } catch (error) {
      setExtractStage('提取失败');
      message.error({ content: '实体提取失败：' + error.message });
    } finally {
      setExtracting(false);
      setExtractStage('');
      setProcessedDocs(0);
    }
  }, [currentKnowledgeBase, selectedDocuments, documents, defaultModel, loadDefaultModel]);

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

      {/* 文档选择区域 */}
      <div className="document-selection">
        <div className="selection-header">
          <h4>选择要处理的文档</h4>
          <div className="header-actions">
            {/* 配置按钮 */}
            <Button
              variant="ghost"
              size="small"
              icon={<FiSettings />}
              onClick={() => {
                console.log('实体配置按钮被点击');
                console.log('当前 configModalVisible 状态:', configModalVisible);
                setConfigModalVisible(true);
                console.log('设置后 configModalVisible 状态:', true);
              }}
              className="config-btn"
            >
              实体配置
            </Button>
            {/* 默认模型信息 */}
            <div className="model-info">
              <FiBox size={14} />
              {loadingModel ? (
                <span className="model-loading">加载模型配置...</span>
              ) : defaultModel ? (
                <span className="model-name">
                  使用模型: {defaultModel.model_name || defaultModel.name || '默认模型'}
                </span>
              ) : (
                <span className="model-warning">未配置默认模型，将使用系统默认</span>
              )}
            </div>
          </div>
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
          <div className="selection-actions">
            <Button size="small" variant="ghost" onClick={handleSelectAllDocuments}>
              全选
            </Button>
            <Button size="small" variant="ghost" onClick={handleClearDocumentSelection}>
              清除
            </Button>
            <span className="selected-count">
              已选 {selectedDocuments.length} / {documents.length} 个
            </span>
          </div>
        </div>
        
        <div className="document-list">
          {filteredDocuments.map(doc => (
            <label key={doc.id} className="document-checkbox">
              <input
                type="checkbox"
                checked={selectedDocuments.includes(doc.id)}
                onChange={() => toggleDocumentSelection(doc.id)}
              />
              <span className="document-name">{doc.title}</span>
              <span className="document-type">{doc.file_type}</span>
            </label>
          ))}
          {filteredDocuments.length === 0 && documents.length > 0 && (
            <div className="no-results">没有匹配的文档</div>
          )}
          {documents.length === 0 && (
            <div className="no-documents">暂无文档，请先上传文档到知识库</div>
          )}
        </div>
        <Button
          variant="primary"
          icon={<FiCpu />}
          onClick={handleExtractEntities}
          loading={extracting}
          disabled={extracting || selectedDocuments.length === 0 || loadingModel}
        >
          {extracting ? `提取中 ${extractProgress}%` : '开始实体提取'}
        </Button>

        {/* 提取进度显示 */}
        {extracting && (
          <div className="extraction-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${extractProgress}%` }}
              />
            </div>
            <div className="progress-info">
              <span className="progress-stage">{extractStage}</span>
              <span className="progress-percent">{extractProgress}%</span>
            </div>
            {processedDocs > 0 && selectedDocuments.length > 1 && (
              <div className="progress-details">
                <span>已处理文档: {processedDocs} / {selectedDocuments.length}</span>
              </div>
            )}
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
