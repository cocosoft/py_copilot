/**
 * 增强版实体识别页面
 * 
 * 基于用户体验分析结果，优化实体识别配置界面
 * 解决信息密度过高、操作流程复杂、视觉一致性不足等问题
 */

import React, { useEffect, useCallback, useState, useMemo } from 'react';
import { 
  FiCpu, FiCheck, FiX, FiEdit2, FiTrash2, FiRefreshCw, 
  FiFilter, FiSearch, FiBox, FiSettings, FiFolder,
  FiChevronDown, FiChevronUp, FiPlus, FiList, FiGrid,
  FiDownload, FiUpload, FiHelpCircle, FiUser, FiBuilding,
  FiMapPin, FiClock, FiCalendar, FiTag, FiAward, FiFile
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { 
  Button, 
  Modal, 
  Loading, 
  ErrorBoundary,
  designTokens 
} from '../../../components/UnifiedComponentLibrary';
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
  getDocumentEntitiesNew
} from '../../../utils/api/knowledgeApi';
import defaultModelApi from '../../../utils/api/defaultModelApi';
import './enhanced-styles.css';

/**
 * 实体类型配置 - 优化后的配置
 */
const ENHANCED_ENTITY_TYPES = [
  { value: 'person', label: '人物', color: designTokens.colors.primary[500], icon: FiUser },
  { value: 'organization', label: '组织', color: designTokens.colors.success[500], icon: FiBuilding },
  { value: 'location', label: '地点', color: designTokens.colors.warning[500], icon: FiMapPin },
  { value: 'time', label: '时间', color: designTokens.colors.info[500], icon: FiClock },
  { value: 'event', label: '事件', color: designTokens.colors.danger[500], icon: FiCalendar },
  { value: 'concept', label: '概念', color: designTokens.colors.secondary[500], icon: FiTag },
  { value: 'product', label: '产品', color: designTokens.colors.purple[500], icon: FiBox },
  { value: 'technology', label: '技术', color: designTokens.colors.cyan[500], icon: FiAward },
];

/**
 * 实体状态配置 - 优化后的配置
 */
const ENHANCED_ENTITY_STATUS = {
  pending: { label: '待确认', color: designTokens.colors.warning[500], bgColor: designTokens.colors.warning[50] },
  confirmed: { label: '已确认', color: designTokens.colors.success[500], bgColor: designTokens.colors.success[50] },
  rejected: { label: '已拒绝', color: designTokens.colors.danger[500], bgColor: designTokens.colors.danger[50] },
  modified: { label: '已修改', color: designTokens.colors.info[500], bgColor: designTokens.colors.info[50] },
};

/**
 * 增强版实体识别页面
 */
const EnhancedEntityRecognition = () => {
  const navigate = useNavigate();
  const { currentKnowledgeBase, setCurrentKnowledgeBase } = useKnowledgeStore();
  
  // 本地状态 - 优化后的状态管理
  const [loading, setLoading] = useState(false);
  const [entities, setEntities] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [selectedEntities, setSelectedEntities] = useState(new Set());
  const [filters, setFilters] = useState({
    entityTypes: [],
    status: [],
    searchText: '',
  });
  
  // 视图状态
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'grid'
  const [showFilters, setShowFilters] = useState(false);
  const [showBatchActions, setShowBatchActions] = useState(false);
  
  // 模态框状态
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  
  // 批量操作状态
  const [batchProcessing, setBatchProcessing] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  
  // 实体提取进度状态
  const [extractProgress, setExtractProgress] = useState(0);
  const [extractStatus, setExtractStatus] = useState('');
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [extractTaskId, setExtractTaskId] = useState(null);
  
  // 提取配置状态
  const [extractConfig, setExtractConfig] = useState({
    extractEntities: true,
    extractRelationships: true,
    processingMode: 'quality', // 'standard' | 'quality' | 'speed'
    threshold: 0.7
  });
  const [showConfigPanel, setShowConfigPanel] = useState(false);

  /**
   * 获取文档列表
   */
  const fetchDocuments = useCallback(async () => {
    if (!currentKnowledgeBase) return;
    
    setLoading(true);
    try {
      const docs = await listDocuments(currentKnowledgeBase.id);
      setDocuments(docs);
      
      // 自动选择第一个文档
      if (docs.length > 0 && !selectedDocument) {
        setSelectedDocument(docs[0]);
      }
    } catch (error) {
      message.error({ content: `获取文档列表失败: ${error.message}` });
    } finally {
      setLoading(false);
    }
  }, [currentKnowledgeBase, selectedDocument]);

  /**
   * 获取实体列表
   */
  const fetchEntities = useCallback(async () => {
    if (!currentKnowledgeBase || !selectedDocument) return;

    setLoading(true);
    try {
      // 调用真实 API 获取实体
      // 使用 getDocumentEntitiesNew 替代不存在的 getDocumentEntitiesFromMaintenance
      const entityData = await getDocumentEntitiesNew(selectedDocument.id);
      // 将后端返回的字段映射为前端需要的格式
      const mappedEntities = (entityData.entities || []).map(e => ({
        id: e.id,
        name: e.entity_text || e.text,
        type: e.entity_type || e.type || 'concept',
        status: e.status || 'pending',
        confidence: e.confidence || 0.8,
        context: e.context || '',
        document_id: e.document_id,
        start_pos: e.start_pos,
        end_pos: e.end_pos,
      }));
      setEntities(mappedEntities);
    } catch (error) {
      message.error({ content: `获取实体列表失败: ${error.message}` });
    } finally {
      setLoading(false);
    }
  }, [currentKnowledgeBase, selectedDocument]);

  /**
   * 执行实体提取
   */
  const handleExtractEntities = useCallback(async () => {
    if (!currentKnowledgeBase || !selectedDocument) {
      message.warning({ content: '请先选择知识库和文档' });
      return;
    }
    
    // 显示进度模态框
    setExtractProgress(0);
    setExtractStatus('准备开始实体提取...');
    setShowProgressModal(true);
    
    try {
      // 根据处理模式调整参数
      const modeConfig = {
        standard: { chunkSize: 1024, overlapSize: 128 },
        quality: { chunkSize: 512, overlapSize: 64 },
        speed: { chunkSize: 2048, overlapSize: 256 }
      };
      const currentModeConfig = modeConfig[extractConfig.processingMode] || modeConfig.quality;
      
      // 调用实体提取 API，传入配置参数
      const response = await extractEntities({
        text: selectedDocument.content || '',
        entity_types: ENHANCED_ENTITY_TYPES.map(type => type.value),
        threshold: extractConfig.threshold,
        document_id: selectedDocument.id,
        knowledge_base_id: currentKnowledgeBase.id,
        extract_relationships: extractConfig.extractRelationships,
        chunk_size: currentModeConfig.chunkSize,
        overlap_size: currentModeConfig.overlapSize,
        processing_mode: extractConfig.processingMode
      });
      
      // 获取任务ID（如果后端返回）
      if (response.task_id) {
        setExtractTaskId(response.task_id);
      }
      
      // 开始轮询获取进度
      let pollingInterval = setInterval(async () => {
        try {
          // 这里应该调用获取实体提取进度的API
          // 暂时模拟进度
          setExtractProgress(prev => {
            const newProgress = prev + 10;
            
            // 模拟不同阶段的状态
            if (newProgress < 20) {
              setExtractStatus('正在准备文档...');
            } else if (newProgress < 40) {
              setExtractStatus('正在预处理文本...');
            } else if (newProgress < 60) {
              setExtractStatus('正在识别实体...');
            } else if (newProgress < 80) {
              setExtractStatus('正在提取关系...');
            } else if (newProgress < 90) {
              setExtractStatus('正在保存结果...');
            } else if (newProgress >= 100) {
              setExtractStatus('完成！');
              clearInterval(pollingInterval);
              return 100;
            }
            return newProgress;
          });
        } catch (error) {
          console.error('获取进度失败:', error);
          clearInterval(pollingInterval);
        }
      }, 500);
      
      // 延迟刷新实体列表
      setTimeout(() => {
        fetchEntities();
        setShowProgressModal(false);
        message.success({ content: '实体提取完成' });
      }, 5000);
    } catch (error) {
      message.error({ content: `实体提取失败: ${error.message}` });
      setShowProgressModal(false);
    }
  }, [currentKnowledgeBase, selectedDocument, fetchEntities, extractConfig]);

  /**
   * 更新实体状态
   */
  const updateEntity = useCallback(async (entityId, newStatus) => {
    try {
      await updateEntityStatus(entityId, newStatus);
      
      // 更新本地状态
      setEntities(prev => prev.map(entity => 
        entity.id === entityId ? { ...entity, status: newStatus } : entity
      ));
      
      message.success({ content: `实体状态已更新为${ENHANCED_ENTITY_STATUS[newStatus].label}` });
    } catch (error) {
      message.error({ content: `更新实体状态失败: ${error.message}` });
    }
  }, []);

  /**
   * 批量更新实体状态
   */
  const handleBatchUpdate = useCallback(async (newStatus) => {
    if (selectedEntities.size === 0) {
      message.warning({ content: '请先选择要操作的实体' });
      return;
    }
    
    setBatchProcessing(true);
    setBatchProgress(0);
    
    try {
      const entityIds = Array.from(selectedEntities);
      const total = entityIds.length;
      
      // 批量更新状态
      for (let i = 0; i < entityIds.length; i++) {
        await updateEntityStatus(entityIds[i], newStatus);
        setBatchProgress(((i + 1) / total) * 100);
      }
      
      // 刷新实体列表
      await fetchEntities();
      
      // 清空选择
      setSelectedEntities(new Set());
      setShowBatchActions(false);
      
      message.success({ content: `已批量更新 ${total} 个实体状态` });
    } catch (error) {
      message.error({ content: `批量操作失败: ${error.message}` });
    } finally {
      setBatchProcessing(false);
      setBatchProgress(0);
    }
  }, [selectedEntities, fetchEntities]);

  /**
   * 筛选后的实体列表
   */
  const filteredEntities = useMemo(() => {
    return entities.filter(entity => {
      // 类型筛选
      if (filters.entityTypes.length > 0 && !filters.entityTypes.includes(entity.type)) {
        return false;
      }
      
      // 状态筛选
      if (filters.status.length > 0 && !filters.status.includes(entity.status)) {
        return false;
      }
      
      // 文本搜索
      if (filters.searchText && !entity.name.toLowerCase().includes(filters.searchText.toLowerCase())) {
        return false;
      }
      
      return true;
    });
  }, [entities, filters]);

  /**
   * 实体选择处理
   */
  const handleEntitySelect = useCallback((entityId) => {
    setSelectedEntities(prev => {
      const newSelection = new Set(prev);
      if (newSelection.has(entityId)) {
        newSelection.delete(entityId);
      } else {
        newSelection.add(entityId);
      }
      
      // 自动显示/隐藏批量操作栏
      setShowBatchActions(newSelection.size > 0);
      
      return newSelection;
    });
  }, []);

  /**
   * 全选/取消全选
   */
  const handleSelectAll = useCallback(() => {
    if (selectedEntities.size === filteredEntities.length) {
      // 取消全选
      setSelectedEntities(new Set());
      setShowBatchActions(false);
    } else {
      // 全选
      const allIds = new Set(filteredEntities.map(entity => entity.id));
      setSelectedEntities(allIds);
      setShowBatchActions(true);
    }
  }, [filteredEntities, selectedEntities.size]);

  // 初始化数据
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // 文档变化时刷新实体
  useEffect(() => {
    if (selectedDocument) {
      fetchEntities();
    }
  }, [selectedDocument, fetchEntities]);

  /**
   * 渲染文档选择器
   */
  const renderDocumentSelector = () => (
    <div className="document-selector">
      <div className="selector-header">
        <FiFolder className="icon" />
        <span className="title">文档选择</span>
        <Button 
          variant="ghost" 
          size="small"
          onClick={() => setShowFilters(!showFilters)}
          icon={showFilters ? FiChevronUp : FiChevronDown}
        >
          {showFilters ? '隐藏筛选' : '显示筛选'}
        </Button>
      </div>
      
      <div className="document-list">
        {documents.map(doc => (
          <div 
            key={doc.id}
            className={`document-item ${selectedDocument?.id === doc.id ? 'active' : ''}`}
            onClick={() => setSelectedDocument(doc)}
          >
            <FiFile className="icon" />
            <span className="name">{doc.name}</span>
            <span className="info">{doc.entitiesCount || 0} 个实体</span>
          </div>
        ))}
      </div>
    </div>
  );

  /**
   * 渲染筛选条件
   */
  const renderFilterPanel = () => (
    <div className={`filter-panel ${showFilters ? 'expanded' : ''}`}>
      <div className="filter-section">
        <label>实体类型</label>
        <div className="type-filters">
          {ENHANCED_ENTITY_TYPES.map(type => (
            <div 
              key={type.value}
              className={`type-filter ${filters.entityTypes.includes(type.value) ? 'active' : ''}`}
              onClick={() => {
                setFilters(prev => ({
                  ...prev,
                  entityTypes: prev.entityTypes.includes(type.value)
                    ? prev.entityTypes.filter(t => t !== type.value)
                    : [...prev.entityTypes, type.value]
                }));
              }}
            >
              <type.icon style={{ color: type.color }} />
              <span>{type.label}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="filter-section">
        <label>状态筛选</label>
        <div className="status-filters">
          {Object.entries(ENHANCED_ENTITY_STATUS).map(([status, config]) => (
            <div 
              key={status}
              className={`status-filter ${filters.status.includes(status) ? 'active' : ''}`}
              style={{ 
                backgroundColor: filters.status.includes(status) ? config.bgColor : 'transparent',
                borderColor: config.color
              }}
              onClick={() => {
                setFilters(prev => ({
                  ...prev,
                  status: prev.status.includes(status)
                    ? prev.status.filter(s => s !== status)
                    : [...prev.status, status]
                }));
              }}
            >
              <span style={{ color: config.color }}>{config.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  /**
   * 渲染实体列表
   */
  const renderEntityList = () => (
    <div className="entity-list-container">
      <div className="list-header">
        <div className="header-left">
          <span className="title">
            实体列表 ({filteredEntities.length})
          </span>
          <div className="view-controls">
            <Button 
              variant={viewMode === 'list' ? 'primary' : 'ghost'}
              size="small"
              icon={FiList}
              onClick={() => setViewMode('list')}
            />
            <Button 
              variant={viewMode === 'grid' ? 'primary' : 'ghost'}
              size="small"
              icon={FiGrid}
              onClick={() => setViewMode('grid')}
            />
          </div>
        </div>
        
        <div className="header-right">
          <div className="search-box">
            <FiSearch className="search-icon" />
            <input 
              type="text"
              placeholder="搜索实体..."
              value={filters.searchText}
              onChange={(e) => setFilters(prev => ({ ...prev, searchText: e.target.value }))}
            />
          </div>
          
          {/* 配置面板切换按钮 */}
          <Button 
            variant={showConfigPanel ? 'primary' : 'outline'}
            icon={FiSettings}
            onClick={() => setShowConfigPanel(!showConfigPanel)}
            title="提取配置"
          >
            配置
          </Button>
          
          <Button 
            variant="primary"
            icon={FiCpu}
            onClick={handleExtractEntities}
            loading={loading}
          >
            {extractConfig.extractRelationships ? '提取实体和关系' : '提取实体'}
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
      
      <div className={`entity-list ${viewMode}`}>
        {filteredEntities.map(entity => {
          const entityType = ENHANCED_ENTITY_TYPES.find(t => t.value === entity.type);
          const statusConfig = ENHANCED_ENTITY_STATUS[entity.status];
          
          return (
            <div 
              key={entity.id}
              className={`entity-item ${selectedEntities.has(entity.id) ? 'selected' : ''}`}
              onClick={() => handleEntitySelect(entity.id)}
            >
              <div className="entity-checkbox">
                <input 
                  type="checkbox"
                  checked={selectedEntities.has(entity.id)}
                  onChange={() => handleEntitySelect(entity.id)}
                />
              </div>
              
              <div className="entity-content">
                <div className="entity-header">
                  <div className="entity-type">
                    {entityType && <entityType.icon style={{ color: entityType.color }} />}
                    <span className="type-label">{entityType?.label}</span>
                  </div>
                  <div 
                    className="entity-status"
                    style={{ 
                      backgroundColor: statusConfig.bgColor,
                      color: statusConfig.color
                    }}
                  >
                    {statusConfig.label}
                  </div>
                </div>
                
                <div className="entity-name">{entity.name}</div>
                <div className="entity-context">{entity.context}</div>
                
                <div className="entity-actions">
                  <Button 
                    variant="success"
                    size="small"
                    icon={FiCheck}
                    onClick={(e) => {
                      e.stopPropagation();
                      updateEntity(entity.id, 'confirmed');
                    }}
                  >
                    确认
                  </Button>
                  <Button 
                    variant="danger"
                    size="small"
                    icon={FiX}
                    onClick={(e) => {
                      e.stopPropagation();
                      updateEntity(entity.id, 'rejected');
                    }}
                  >
                    拒绝
                  </Button>
                  <Button 
                    variant="outline"
                    size="small"
                    icon={FiEdit2}
                    onClick={(e) => {
                      e.stopPropagation();
                      // 打开编辑模态框
                    }}
                  >
                    编辑
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  /**
   * 渲染批量操作栏
   */
  const renderBatchActions = () => (
    <div className={`batch-actions-bar ${showBatchActions ? 'visible' : ''}`}>
      <div className="batch-info">
        <span>已选择 {selectedEntities.size} 个实体</span>
        <Button variant="ghost" size="small" onClick={handleSelectAll}>
          {selectedEntities.size === filteredEntities.length ? '取消全选' : '全选'}
        </Button>
      </div>
      
      <div className="batch-buttons">
        {batchProcessing && (
          <div className="batch-progress">
            <Loading size="small" />
            <span>处理中... {Math.round(batchProgress)}%</span>
          </div>
        )}
        
        <Button 
          variant="success"
          icon={FiCheck}
          onClick={() => handleBatchUpdate('confirmed')}
          disabled={batchProcessing}
        >
          批量确认
        </Button>
        <Button 
          variant="danger"
          icon={FiX}
          onClick={() => handleBatchUpdate('rejected')}
          disabled={batchProcessing}
        >
          批量拒绝
        </Button>
        <Button 
          variant="outline"
          icon={FiTrash2}
          onClick={() => setSelectedEntities(new Set())}
          disabled={batchProcessing}
        >
          取消选择
        </Button>
      </div>
    </div>
  );

  return (
    <ErrorBoundary>
      <div className="enhanced-entity-recognition">
        {/* 页面头部 */}
        <div className="page-header">
          <div className="header-content">
            <h1>实体识别管理</h1>
            <div className="header-actions">
              <Button 
                variant="outline"
                icon={FiHelpCircle}
                onClick={() => setShowHelpModal(true)}
              >
                使用帮助
              </Button>
              <Button 
                variant="outline"
                icon={FiSettings}
                onClick={() => setShowConfigModal(true)}
              >
                配置设置
              </Button>
            </div>
          </div>
        </div>

        {/* 主要内容区域 */}
        <div className="main-content">
          {/* 左侧文档选择 */}
          <div className="sidebar">
            {renderDocumentSelector()}
            {renderFilterPanel()}
          </div>

          {/* 右侧实体列表 */}
          <div className="content-area">
            {renderEntityList()}
          </div>
        </div>

        {/* 批量操作栏 */}
        {renderBatchActions()}

        {/* 帮助模态框 */}
        <Modal
          isOpen={showHelpModal}
          onClose={() => setShowHelpModal(false)}
          title="实体识别使用帮助"
          size="large"
        >
          <div className="help-content">
            <h3>操作指南</h3>
            <p>1. 选择文档后，点击"提取实体"按钮开始实体识别</p>
            <p>2. 使用筛选条件快速定位特定类型和状态的实体</p>
            <p>3. 选择实体后可以使用批量操作功能</p>
            <p>4. 支持列表和网格两种视图模式</p>
          </div>
        </Modal>

        {/* 配置设置模态框 */}
        <EntityConfigModal
          isOpen={showConfigModal}
          onClose={() => setShowConfigModal(false)}
          knowledgeBaseId={currentKnowledgeBase?.id}
        />
        
        {/* 实体提取进度模态框 */}
        <Modal
          isOpen={showProgressModal}
          onClose={() => setShowProgressModal(false)}
          title="实体提取进度"
          size="medium"
          disableClose={true}
        >
          <div className="extract-progress-container">
            <div className="progress-header">
              <FiCpu className="icon" />
              <h3>正在提取实体</h3>
            </div>
            
            <div className="progress-content">
              <div className="status-text">
                {extractStatus}
              </div>
              
              <div className="progress-bar-container">
                <div 
                  className="progress-bar"
                  style={{ width: `${extractProgress}%` }}
                ></div>
              </div>
              
              <div className="progress-percentage">
                {Math.round(extractProgress)}%
              </div>
            </div>
            
            {extractProgress === 100 && (
              <div className="progress-complete">
                <FiCheck className="complete-icon" />
                <span>实体提取完成！</span>
              </div>
            )}
          </div>
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

export default EnhancedEntityRecognition;