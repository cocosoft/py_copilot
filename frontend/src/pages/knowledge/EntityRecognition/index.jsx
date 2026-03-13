/**
 * 实体识别页面
 *
 * 提供实体提取、确认、编辑功能，支持从文档中自动识别实体
 */

import React, { useEffect, useCallback, useState } from 'react';
import { FiCpu, FiCheck, FiX, FiEdit2, FiTrash2, FiRefreshCw, FiFilter, FiSearch, FiBox } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { VirtualListEnhanced } from '../../../components/UI';
import { message } from '../../../components/UI/Message/Message';
import {
  listDocuments,
  extractEntities,
  getDocument,
  getDocumentChunks
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

  // 本地状态
  const [documents, setDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [entities, setEntities] = useState([]);
  const [filteredEntities, setFilteredEntities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractProgress, setExtractProgress] = useState(0);

  // 默认模型状态
  const [defaultModel, setDefaultModel] = useState(null);
  const [loadingModel, setLoadingModel] = useState(false);

  // 筛选状态
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // 编辑状态
  const [editingEntity, setEditingEntity] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', type: '', description: '' });

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
   * 加载默认模型配置
   */
  const loadDefaultModel = useCallback(async () => {
    setLoadingModel(true);
    try {
      // 获取知识库场景的默认模型（使用 'knowledge' 场景名称）
      const response = await defaultModelApi.getSceneDefaultModel('knowledge');
      setDefaultModel(response);
    } catch (error) {
      console.error('获取默认模型失败:', error);
      message.warning({ content: '未配置知识库场景的默认模型，将使用系统默认配置' });
      setDefaultModel(null);
    } finally {
      setLoadingModel(false);
    }
  }, []);

  /**
   * 执行实体提取 - 使用 LLM
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

    try {
      // 获取默认模型配置
      const currentDefaultModel = defaultModel || await loadDefaultModel();

      // 获取选中文档的内容
      const documentContents = [];
      for (let i = 0; i < selectedDocuments.length; i++) {
        const docId = selectedDocuments[i];
        try {
          // 获取文档详情和分块内容
          const [docDetail, chunksData] = await Promise.all([
            getDocument(docId),
            getDocumentChunks(docId, 0, 100)
          ]);

          // 合并所有分块的内容
          const chunks = chunksData.chunks || [];
          const fullContent = chunks.map(chunk => chunk.content || chunk.text || '').join('\n\n');

          documentContents.push({
            id: docId,
            title: docDetail.title || '未命名文档',
            content: fullContent || docDetail.description || '',
          });
        } catch (error) {
          console.error(`获取文档 ${docId} 内容失败:`, error);
        }
        setExtractProgress(Math.round(((i + 1) / selectedDocuments.length) * 20));
      }

      if (documentContents.length === 0) {
        message.warning({ content: '无法获取文档内容' });
        setExtracting(false);
        return;
      }

      // 合并所有文档内容
      const combinedText = documentContents.map(doc =>
        `文档标题: ${doc.title}\n\n${doc.content}`
      ).join('\n\n---\n\n');

      setExtractProgress(30);

      // 构建实体提取参数
      const extractParams = {
        text: combinedText,
        entity_types: ENTITY_TYPES.map(t => t.value),
        threshold: 0.7,
        use_llm: true,
        knowledge_base_id: currentKnowledgeBase.id,
        document_ids: selectedDocuments,
      };

      // 如果有默认模型配置，添加到参数中
      if (currentDefaultModel && currentDefaultModel.model_id) {
        extractParams.model_id = currentDefaultModel.model_id;
        extractParams.model_config = {
          temperature: currentDefaultModel.temperature || 0.3,
          max_tokens: currentDefaultModel.max_tokens || 2000,
        };
      }

      setExtractProgress(50);

      // 调用实体提取 API（使用 LLM）
      const response = await extractEntities(extractParams);

      setExtractProgress(100);

      // 处理提取结果
      const extractedEntities = (response.entities || []).map((entity, index) => ({
        id: `entity-${Date.now()}-${index}`,
        name: entity.name || entity.text,
        type: entity.type || 'concept',
        description: entity.description || '',
        documentId: entity.document_id || selectedDocuments[0],
        documentName: entity.document_name || documentContents[0]?.title,
        confidence: entity.confidence || entity.score || 0.8,
        status: 'pending',
        occurrences: entity.occurrences || 1,
        source: 'llm',
        modelUsed: currentDefaultModel?.model_name || '默认模型',
      }));

      setEntities(prev => [...extractedEntities, ...prev]);
      message.success({ content: `成功提取 ${extractedEntities.length} 个实体` });
    } catch (error) {
      message.error({ content: '实体提取失败：' + error.message });
    } finally {
      setExtracting(false);
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
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(e =>
        e.name.toLowerCase().includes(query) ||
        e.description.toLowerCase().includes(query)
      );
    }

    setFilteredEntities(result);
  }, [entities, filterType, filterStatus, searchQuery]);

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
  const handleConfirmEntity = (entityId) => {
    setEntities(prev =>
      prev.map(e => e.id === entityId ? { ...e, status: 'confirmed' } : e)
    );
    message.success({ content: '实体已确认' });
  };

  /**
   * 拒绝实体
   */
  const handleRejectEntity = (entityId) => {
    setEntities(prev =>
      prev.map(e => e.id === entityId ? { ...e, status: 'rejected' } : e)
    );
    message.success({ content: '实体已拒绝' });
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
  const handleDeleteEntity = (entityId) => {
    if (!window.confirm('确定要删除这个实体吗？')) return;
    setEntities(prev => prev.filter(e => e.id !== entityId));
    message.success({ content: '实体已删除' });
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
              <button className="save-btn" onClick={() => handleSaveEdit(entity.id)}>
                <FiCheck size={16} />
              </button>
              <button className="cancel-btn" onClick={handleCancelEdit}>
                <FiX size={16} />
              </button>
            </div>
          </div>
        ) : (
          <>
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
                  >
                    <FiCheck size={16} />
                  </button>
                  <button
                    className="action-btn reject"
                    onClick={() => handleRejectEntity(entity.id)}
                    title="拒绝"
                  >
                    <FiX size={16} />
                  </button>
                </>
              )}
              <button
                className="action-btn edit"
                onClick={() => handleStartEdit(entity)}
                title="编辑"
              >
                <FiEdit2 size={16} />
              </button>
              <button
                className="action-btn delete"
                onClick={() => handleDeleteEntity(entity.id)}
                title="删除"
              >
                <FiTrash2 size={16} />
              </button>
            </div>
          </>
        )}
      </div>
    );
  }, [editingEntity, editForm]);

  // 初始加载
  useEffect(() => {
    fetchDocuments();
    loadDefaultModel();
  }, [fetchDocuments, loadDefaultModel]);

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
        <div className="document-list">
          {documents.map(doc => (
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
  );
};

export default EntityRecognition;
