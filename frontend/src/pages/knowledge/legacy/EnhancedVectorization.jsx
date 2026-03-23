/**
 * 增强版向量化管理页面
 * 
 * 集成了以下优化功能：
 * - 质量评估面板 (FE-004): 显示向量化质量评分
 * - 批量处理向导 (FE-005): 向导式批量处理界面
 * - 向量空间3D可视化 (FE-006): 3D展示向量分布
 * - 实时资源监控 (FE-008): 显示处理资源使用情况
 * 
 * @module EnhancedVectorization
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';

// 导入新功能组件
import QualityPanel from '@components/Knowledge/QualityPanel';
import BatchProcessingWizard from '@components/Knowledge/BatchProcessingWizard';
import VectorSpace3D from '@components/Knowledge/VectorSpace3D';
import ResourceMonitor from '@components/Knowledge/ResourceMonitor';

// 导入原向量化管理组件
import VectorizationManager from '@components/Vectorization/VectorizationManager';

// 导入状态管理
import useKnowledge from '@hooks/useKnowledge';

// 导入 API
import { 
  listDocuments, 
  getKnowledgeBases,
  getDocumentChunks 
} from '@utils/api/knowledgeApi';

// 导入样式
import './EnhancedVectorization.css';

/**
 * 概览标签页组件
 * 
 * @param {Object} props - 组件属性
 * @param {string} props.knowledgeBaseId - 知识库ID
 * @param {Array} props.documents - 文档列表
 */
const OverviewTab = ({ knowledgeBaseId, documents }) => {
  const { t } = useTranslation(['knowledge', 'common']);
  
  // 统计信息
  const stats = React.useMemo(() => {
    const total = documents.length;
    const vectorized = documents.filter(d => d.vectorization_status === 'vectorized').length;
    const processing = documents.filter(d => d.vectorization_status === 'processing').length;
    const failed = documents.filter(d => d.vectorization_status === 'failed').length;
    const pending = documents.filter(d => !d.vectorization_status || d.vectorization_status === 'pending').length;
    
    return {
      total,
      vectorized,
      processing,
      failed,
      pending,
      vectorizedPercent: total > 0 ? Math.round((vectorized / total) * 100) : 0,
      failedPercent: total > 0 ? Math.round((failed / total) * 100) : 0,
    };
  }, [documents]);
  
  return (
    <div className="overview-tab">
      <div className="stats-grid">
        <div className="stat-card total">
          <div className="stat-icon">📄</div>
          <div className="stat-content">
            <span className="stat-number">{stats.total}</span>
            <span className="stat-label">{t('knowledge:totalDocuments')}</span>
          </div>
        </div>
        
        <div className="stat-card vectorized">
          <div className="stat-icon">✓</div>
          <div className="stat-content">
            <span className="stat-number">{stats.vectorized}</span>
            <span className="stat-label">{t('knowledge:vectorized')}</span>
            <span className="stat-percent">{stats.vectorizedPercent}%</span>
          </div>
        </div>
        
        <div className="stat-card processing">
          <div className="stat-icon">⏳</div>
          <div className="stat-content">
            <span className="stat-number">{stats.processing}</span>
            <span className="stat-label">{t('knowledge:processing')}</span>
          </div>
        </div>
        
        <div className="stat-card failed">
          <div className="stat-icon">✗</div>
          <div className="stat-content">
            <span className="stat-number">{stats.failed}</span>
            <span className="stat-label">{t('knowledge:failed')}</span>
            <span className="stat-percent">{stats.failedPercent}%</span>
          </div>
        </div>
        
        <div className="stat-card pending">
          <div className="stat-icon">○</div>
          <div className="stat-content">
            <span className="stat-number">{stats.pending}</span>
            <span className="stat-label">{t('knowledge:pending')}</span>
          </div>
        </div>
      </div>
      
      {/* 进度条 */}
      <div className="progress-section">
        <h3>{t('knowledge:vectorizationProgress')}</h3>
        <div className="progress-bar-container">
          <div className="progress-bar">
            <div 
              className="progress-fill vectorized" 
              style={{ width: `${stats.vectorizedPercent}%` }}
            />
            <div 
              className="progress-fill processing" 
              style={{ width: `${(stats.processing / stats.total) * 100}%`, left: `${stats.vectorizedPercent}%` }}
            />
            <div 
              className="progress-fill failed" 
              style={{ width: `${stats.failedPercent}%`, left: `${stats.vectorizedPercent + (stats.processing / stats.total) * 100}%` }}
            />
          </div>
          <div className="progress-legend">
            <span className="legend-item vectorized">
              <span className="legend-dot" /> {t('knowledge:vectorized')} ({stats.vectorizedPercent}%)
            </span>
            <span className="legend-item processing">
              <span className="legend-dot" /> {t('knowledge:processing')}
            </span>
            <span className="legend-item failed">
              <span className="legend-dot" /> {t('knowledge:failed')}
            </span>
            <span className="legend-item pending">
              <span className="legend-dot" /> {t('knowledge:pending')}
            </span>
          </div>
        </div>
      </div>
      
      {/* 最近活动 */}
      <div className="recent-activity">
        <h3>{t('knowledge:recentActivity')}</h3>
        <div className="activity-list">
          {documents.slice(0, 5).map((doc, index) => (
            <div key={doc.id} className="activity-item">
              <span className="activity-time">
                {new Date(doc.updated_at).toLocaleString()}
              </span>
              <span className="activity-doc">{doc.title}</span>
              <span className={`activity-status ${doc.vectorization_status}`}>
                {t(`knowledge:status.${doc.vectorization_status || 'pending'}`)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * 配置标签页组件
 * 
 * @param {Object} props - 组件属性
 * @param {string} props.knowledgeBaseId - 知识库ID
 */
const ConfigTab = ({ knowledgeBaseId }) => {
  const { t } = useTranslation(['knowledge', 'common']);
  const [config, setConfig] = useState({
    chunkSize: 500,
    chunkOverlap: 50,
    embeddingModel: 'text-embedding-3-small',
    batchSize: 10,
    autoProcess: false,
    qualityThreshold: 0.8,
  });
  
  const handleSave = () => {
    // 保存配置到后端
    console.log('保存配置:', config);
  };
  
  return (
    <div className="config-tab">
      <h3>{t('knowledge:vectorizationConfig')}</h3>
      
      <div className="config-form">
        <div className="form-group">
          <label>{t('knowledge:chunkSize')}</label>
          <input
            type="number"
            value={config.chunkSize}
            onChange={(e) => setConfig({ ...config, chunkSize: parseInt(e.target.value) })}
            min={100}
            max={2000}
          />
          <span className="help-text">{t('knowledge:chunkSizeHelp')}</span>
        </div>
        
        <div className="form-group">
          <label>{t('knowledge:chunkOverlap')}</label>
          <input
            type="number"
            value={config.chunkOverlap}
            onChange={(e) => setConfig({ ...config, chunkOverlap: parseInt(e.target.value) })}
            min={0}
            max={200}
          />
          <span className="help-text">{t('knowledge:chunkOverlapHelp')}</span>
        </div>
        
        <div className="form-group">
          <label>{t('knowledge:embeddingModel')}</label>
          <select
            value={config.embeddingModel}
            onChange={(e) => setConfig({ ...config, embeddingModel: e.target.value })}
          >
            <option value="text-embedding-3-small">text-embedding-3-small</option>
            <option value="text-embedding-3-large">text-embedding-3-large</option>
            <option value="text-embedding-ada-002">text-embedding-ada-002</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>{t('knowledge:batchSize')}</label>
          <input
            type="number"
            value={config.batchSize}
            onChange={(e) => setConfig({ ...config, batchSize: parseInt(e.target.value) })}
            min={1}
            max={50}
          />
        </div>
        
        <div className="form-group">
          <label>{t('knowledge:qualityThreshold')}</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={config.qualityThreshold}
            onChange={(e) => setConfig({ ...config, qualityThreshold: parseFloat(e.target.value) })}
          />
          <span className="range-value">{Math.round(config.qualityThreshold * 100)}%</span>
        </div>
        
        <div className="form-group checkbox">
          <label>
            <input
              type="checkbox"
              checked={config.autoProcess}
              onChange={(e) => setConfig({ ...config, autoProcess: e.target.checked })}
            />
            {t('knowledge:autoProcess')}
          </label>
        </div>
        
        <div className="form-actions">
          <button className="btn-primary" onClick={handleSave}>
            {t('common:save')}
          </button>
          <button className="btn-secondary">
            {t('common:reset')}
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * 增强版向量化管理页面组件
 * 
 * @component
 */
const EnhancedVectorization = () => {
  const { t } = useTranslation(['knowledge', 'common']);
  
  // 使用状态管理
  const { currentKnowledgeBase, setCurrentKnowledgeBase } = useKnowledge();

  // 兼容旧代码的别名
  const selectedKnowledgeBase = currentKnowledgeBase;
  const setSelectedKnowledgeBase = setCurrentKnowledgeBase;
  
  // 标签页状态
  const [activeTab, setActiveTab] = useState('overview');
  
  // 获取知识库列表
  const { data: knowledgeBasesData } = useQuery({
    queryKey: ['knowledgeBases'],
    queryFn: () => getKnowledgeBases(0, 50),
    staleTime: 5 * 60 * 1000,
  });
  
  // 支持两种数据结构：response.knowledge_bases 或 response.data
  const knowledgeBases = knowledgeBasesData?.knowledge_bases || knowledgeBasesData?.data || knowledgeBasesData || [];
  
  // 获取文档列表 - 使用较大的 limit 以获取所有文档
  const { data: documentsData, isLoading, error: documentsError } = useQuery({
    queryKey: ['documents', selectedKnowledgeBase],
    queryFn: () => listDocuments(0, 1000, selectedKnowledgeBase, null),
    enabled: !!selectedKnowledgeBase,
    staleTime: 2 * 60 * 1000,
  });

  // 调试日志
  console.log('EnhancedVectorization - documentsData:', documentsData);
  console.log('EnhancedVectorization - documentsError:', documentsError);
  console.log('EnhancedVectorization - selectedKnowledgeBase:', selectedKnowledgeBase);

  // 支持多种数据结构
  const documents = documentsData?.documents || documentsData?.data || documentsData || [];
  console.log('EnhancedVectorization - parsed documents:', documents);
  
  // 标签页配置
  const tabs = [
    { key: 'overview', label: t('knowledge:overview'), icon: '📊' },
    { key: 'batch', label: t('knowledge:batchProcessing'), icon: '🚀' },
    { key: 'quality', label: t('knowledge:qualityAssessment'), icon: '⭐' },
    { key: 'vectorspace', label: t('knowledge:vectorSpace'), icon: '🎯' },
    { key: 'resources', label: t('knowledge:resourceMonitor'), icon: '📈' },
    { key: 'config', label: t('knowledge:configuration'), icon: '⚙️' },
  ];
  
  // 处理批量处理完成
  const handleBatchComplete = useCallback((results) => {
    console.log('批量处理完成:', results);
    // 刷新文档列表
  }, []);
  
  return (
    <div className="enhanced-vectorization-page">
      {/* 页面头部 */}
      <div className="page-header">
        <h1>{t('knowledge:vectorizationManagement')}</h1>
        
        {/* 知识库选择器 */}
        <div className="knowledge-base-selector">
          <select
            value={selectedKnowledgeBase || ''}
            onChange={(e) => setSelectedKnowledgeBase(e.target.value)}
          >
            <option value="">{t('knowledge:selectKnowledgeBase')}</option>
            {knowledgeBases.map(kb => (
              <option key={kb.id} value={kb.id}>{kb.name}</option>
            ))}
          </select>
        </div>
      </div>
      
      {/* 标签栏 */}
      <div className="tabs-bar">
        {tabs.map(tab => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
      
      {/* 标签内容 */}
      <div className="tab-content">
        {isLoading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>{t('common:loading')}</p>
          </div>
        ) : !selectedKnowledgeBase ? (
          <div className="empty-state">
            <p>{t('knowledge:pleaseSelectKnowledgeBase')}</p>
          </div>
        ) : (
          <>
            {/* 概览标签 */}
            {activeTab === 'overview' && (
              <OverviewTab 
                knowledgeBaseId={selectedKnowledgeBase}
                documents={documents}
              />
            )}
            
            {/* 批量处理标签 - FE-005 */}
            {activeTab === 'batch' && (
              <BatchProcessingWizard
                knowledgeBaseId={selectedKnowledgeBase}
                documents={documents}
                onComplete={handleBatchComplete}
              />
            )}
            
            {/* 质量评估标签 - FE-004 */}
            {activeTab === 'quality' && (
              <QualityPanel
                knowledgeBaseId={selectedKnowledgeBase}
                documents={documents}
              />
            )}
            
            {/* 向量空间标签 - FE-006 */}
            {activeTab === 'vectorspace' && (
              <VectorSpace3D
                knowledgeBaseId={selectedKnowledgeBase}
                height={600}
                showControls={true}
                enableClustering={true}
              />
            )}
            
            {/* 资源监控标签 - FE-008 */}
            {activeTab === 'resources' && (
              <ResourceMonitor
                showCpu={true}
                showMemory={true}
                showGpu={true}
                showNetwork={true}
                refreshInterval={5000}
              />
            )}
            
            {/* 配置标签 */}
            {activeTab === 'config' && (
              <ConfigTab knowledgeBaseId={selectedKnowledgeBase} />
            )}
          </>
        )}
      </div>
      
      {/* 嵌入原向量化管理组件（用于兼容） */}
      <div style={{ display: 'none' }}>
        <VectorizationManager />
      </div>
    </div>
  );
};

export default EnhancedVectorization;
