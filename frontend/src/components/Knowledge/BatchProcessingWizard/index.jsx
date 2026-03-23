/**
 * 批量处理向导组件 - FE-005 批量处理向导
 *
 * 智能批量处理向导，包括文档选择、参数配置、实时进度、结果预览
 *
 * @task FE-005
 * @phase 前端功能拓展
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  CheckCircle,
  XCircle,
  FileText,
  Settings,
  Play,
  AlertTriangle,
  Search,
  Eye,
  Download,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
} from '../icons.jsx';
import { vectorizeDocumentLegacy, getDocumentProcessingProgress } from '../../../utils/api/knowledgeApi';
import './BatchProcessingWizard.css';

/**
 * 步骤配置
 */
const STEPS = [
  { id: 'select', title: '选择文档', icon: FileText },
  { id: 'configure', title: '配置参数', icon: Settings },
  { id: 'process', title: '开始处理', icon: Play },
  { id: 'preview', title: '结果预览', icon: Eye },
];

/**
 * 文档选择步骤
 */
const DocumentSelectionStep = ({
  documents,
  selectedIds,
  onSelect,
  onSelectAll,
  searchQuery,
  onSearch,
  filters,
  onFilterChange,
}) => {
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch =
        !searchQuery ||
        doc.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType =
        !filters.type || doc.type === filters.type;
      const matchesStatus =
        !filters.status || doc.status === filters.status;
      return matchesSearch && matchesType && matchesStatus;
    });
  }, [documents, searchQuery, filters]);

  const allSelected =
    filteredDocuments.length > 0 &&
    filteredDocuments.every((doc) => selectedIds.includes(doc.id));

  return (
    <div className="step-content document-selection">
      {/* 搜索和过滤 */}
      <div className="filters-bar">
        <div className="search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="搜索文档..."
            value={searchQuery}
            onChange={(e) => onSearch(e.target.value)}
          />
        </div>
        <select
          value={filters.type}
          onChange={(e) =>
            onFilterChange({ ...filters, type: e.target.value })
          }
        >
          <option value="">所有类型</option>
          <option value="pdf">PDF</option>
          <option value="docx">Word</option>
          <option value="txt">Text</option>
        </select>
        <select
          value={filters.status}
          onChange={(e) =>
            onFilterChange({ ...filters, status: e.target.value })
          }
        >
          <option value="">所有状态</option>
          <option value="pending">待处理</option>
          <option value="processing">处理中</option>
          <option value="completed">已完成</option>
        </select>
      </div>

      {/* 文档列表 */}
      <div className="document-list">
        <div className="list-header">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={() => onSelectAll(filteredDocuments.map((d) => d.id))}
          />
          <span>全选 ({selectedIds.length}/{filteredDocuments.length})</span>
        </div>

        {filteredDocuments.length === 0 ? (
          <div className="empty-state" style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
            <FileText size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
            <p>暂无文档数据</p>
            <p style={{ fontSize: '12px', marginTop: '8px' }}>
              该知识库中还没有文档，请先
              <a href="/knowledge/documents" style={{ color: '#1890ff', marginLeft: '4px' }}>上传文档</a>
            </p>
          </div>
        ) : (
          filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className={`document-item ${
                selectedIds.includes(doc.id) ? 'selected' : ''
              }`}
            >
              <input
                type="checkbox"
                checked={selectedIds.includes(doc.id)}
                onChange={() => onSelect(doc.id)}
              />
              <div className="doc-info">
                <span className="doc-name">{doc.name}</span>
                <span className="doc-meta">
                  {doc.type} · {doc.size} · {doc.status}
                </span>
              </div>
              <span className={`status-badge ${doc.status}`}>
                {doc.status === 'completed' && <CheckCircle size={14} />}
                {doc.status === 'error' && <XCircle size={14} />}
                {doc.status === 'processing' && '⏳'}
                {doc.status === 'pending' && '⏸️'}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

/**
 * 参数配置步骤
 */
const ConfigurationStep = ({ config, onChange }) => {
  return (
    <div className="step-content configuration">
      <div className="config-section">
        <h4>分块配置</h4>
        <div className="config-grid">
          <div className="config-item">
            <label>分块大小</label>
            <input
              type="number"
              value={config.chunkSize}
              onChange={(e) =>
                onChange({ ...config, chunkSize: parseInt(e.target.value) })
              }
              min={100}
              max={2000}
              step={100}
            />
            <span>字符</span>
          </div>
          <div className="config-item">
            <label>重叠大小</label>
            <input
              type="number"
              value={config.overlap}
              onChange={(e) =>
                onChange({ ...config, overlap: parseInt(e.target.value) })
              }
              min={0}
              max={500}
              step={50}
            />
            <span>字符</span>
          </div>
        </div>
      </div>

      <div className="config-section">
        <h4>嵌入模型</h4>
        <select
          value={config.embeddingModel}
          onChange={(e) =>
            onChange({ ...config, embeddingModel: e.target.value })
          }
        >
          <option value="text-embedding-3-small">text-embedding-3-small</option>
          <option value="text-embedding-3-large">text-embedding-3-large</option>
          <option value="text-embedding-ada-002">text-embedding-ada-002</option>
        </select>
      </div>

      <div className="config-section">
        <h4>处理选项</h4>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.skipExisting}
            onChange={(e) =>
              onChange({ ...config, skipExisting: e.target.checked })
            }
          />
          跳过已处理的文档
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.autoRetry}
            onChange={(e) =>
              onChange({ ...config, autoRetry: e.target.checked })
            }
          />
          失败时自动重试
        </label>
      </div>
    </div>
  );
};

/**
 * 处理进度步骤
 */
const ProcessingStep = ({ progress, results, onCancel }) => {
  const { completed, failed, total, percentage } = progress;

  return (
    <div className="step-content processing">
      <div className="progress-overview">
        <div className="progress-circle">
          <svg viewBox="0 0 36 36">
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="#e0e0e0"
              strokeWidth="3"
            />
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="#1890ff"
              strokeWidth="3"
              strokeDasharray={`${percentage}, 100`}
            />
          </svg>
          <span className="progress-text">{Math.round(percentage)}%</span>
        </div>

        <div className="progress-stats">
          <div className="stat-item success">
            <CheckCircle size={20} />
            <span>{completed} 成功</span>
          </div>
          <div className="stat-item error">
            <XCircle size={20} />
            <span>{failed} 失败</span>
          </div>
          <div className="stat-item total">
            <span>{total} 总计</span>
          </div>
        </div>
      </div>

      {/* 实时日志 */}
      <div className="processing-log">
        {results.map((result, index) => (
          <div
            key={index}
            className={`log-item ${result.status}`}
          >
            <span className="log-time">
              {new Date(result.timestamp).toLocaleTimeString()}
            </span>
            <span className="log-doc">{result.documentName}</span>
            <span className="log-status">
              {result.status === 'success' ? '✓' : '✗'}
            </span>
            {result.message && (
              <span className="log-message">{result.message}</span>
            )}
          </div>
        ))}
      </div>

      {percentage < 100 && (
        <button className="btn-cancel" onClick={onCancel}>
          取消处理
        </button>
      )}
    </div>
  );
};

/**
 * 结果预览步骤
 */
const PreviewStep = ({ results, onDownload, onRetry }) => {
  const successResults = results.filter((r) => r.status === 'success');
  const failedResults = results.filter((r) => r.status === 'error');

  return (
    <div className="step-content preview">
      <div className="preview-summary">
        <div className="summary-card success">
          <CheckCircle size={32} />
          <span className="count">{successResults.length}</span>
          <span className="label">处理成功</span>
        </div>
        <div className="summary-card error">
          <XCircle size={32} />
          <span className="count">{failedResults.length}</span>
          <span className="label">处理失败</span>
        </div>
      </div>

      {failedResults.length > 0 && (
        <div className="failed-list">
          <h4>失败文档</h4>
          {failedResults.map((result, index) => (
            <div key={index} className="failed-item">
              <AlertTriangle size={16} />
              <span>{result.documentName}</span>
              <span className="error-message">{result.message}</span>
              <button onClick={() => onRetry(result.documentId)}>
                <RotateCcw size={14} />
                重试
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="preview-actions">
        <button className="btn-download" onClick={onDownload}>
          <Download size={16} />
          下载报告
        </button>
      </div>
    </div>
  );
};

/**
 * 批量处理向导主组件
 */
const BatchProcessingWizard = ({
  documents: initialDocuments = [],
  onComplete,
  onCancel,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({ type: '', status: '' });
  const [config, setConfig] = useState({
    chunkSize: 1000,
    overlap: 200,
    embeddingModel: 'text-embedding-3-small',
    skipExisting: true,
    autoRetry: true,
  });
  const [progress, setProgress] = useState({
    completed: 0,
    failed: 0,
    total: 0,
    percentage: 0,
  });
  const [results, setResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // 处理文档数据，适配不同字段名
  const documents = useMemo(() => {
    console.log('BatchProcessingWizard - initialDocuments:', initialDocuments);
    if (initialDocuments && initialDocuments.length > 0) {
      // 将各种字段名映射到标准格式
      const normalizedDocs = initialDocuments.map(doc => {
        if (!doc) return null;
        return {
          id: doc.id || doc.document_id || doc.file_id || `doc-${Math.random().toString(36).substr(2, 9)}`,
          name: doc.name || doc.file_name || doc.title || doc.filename || '未命名文档',
          type: doc.type || doc.file_type || doc.content_type || 'unknown',
          size: doc.size || doc.file_size || '0MB',
          status: doc.status || doc.processing_status || 'pending',
          ...doc, // 保留原始数据
        };
      }).filter(Boolean);
      console.log('BatchProcessingWizard - normalizedDocs:', normalizedDocs);
      if (normalizedDocs.length > 0) return normalizedDocs;
    }
    // 如果没有有效文档，返回空数组（不生成模拟数据）
    return [];
  }, [initialDocuments]);

  // 选择/取消选择文档
  const handleSelect = useCallback((id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  }, []);

  // 全选/取消全选
  const handleSelectAll = useCallback((ids) => {
    setSelectedIds((prev) =>
      ids.every((id) => prev.includes(id)) ? [] : ids
    );
  }, []);

  // 开始处理 - 使用真实API
  const handleStartProcessing = useCallback(async () => {
    setIsProcessing(true);
    setProgress({
      completed: 0,
      failed: 0,
      total: selectedIds.length,
      percentage: 0,
    });
    setResults([]);

    // 逐个处理文档
    for (let i = 0; i < selectedIds.length; i++) {
      const docId = selectedIds[i];
      const doc = documents.find((d) => d.id === docId);
      
      try {
        // 调用向量化API
        await vectorizeDocumentLegacy(docId);
        
        // 更新进度
        setProgress((prev) => ({
          ...prev,
          completed: prev.completed + 1,
          percentage: ((i + 1) / selectedIds.length) * 100,
        }));
        
        setResults((prev) => [
          ...prev,
          {
            documentId: docId,
            documentName: doc?.name || doc?.title || '未命名文档',
            status: 'success',
            message: '',
            timestamp: Date.now(),
          },
        ]);
      } catch (error) {
        console.error(`文档 ${docId} 向量化失败:`, error);
        
        // 更新进度
        setProgress((prev) => ({
          ...prev,
          failed: prev.failed + 1,
          percentage: ((i + 1) / selectedIds.length) * 100,
        }));
        
        setResults((prev) => [
          ...prev,
          {
            documentId: docId,
            documentName: doc?.name || doc?.title || '未命名文档',
            status: 'error',
            message: error.message || '处理失败',
            timestamp: Date.now(),
          },
        ]);
      }
    }

    setIsProcessing(false);
  }, [selectedIds, documents]);

  // 下一步
  const handleNext = () => {
    if (currentStep === 2) {
      handleStartProcessing();
    }
    setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1));
  };

  // 上一步
  const handlePrev = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  // 渲染当前步骤
  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <DocumentSelectionStep
            documents={documents}
            selectedIds={selectedIds}
            onSelect={handleSelect}
            onSelectAll={handleSelectAll}
            searchQuery={searchQuery}
            onSearch={setSearchQuery}
            filters={filters}
            onFilterChange={setFilters}
          />
        );
      case 1:
        return <ConfigurationStep config={config} onChange={setConfig} />;
      case 2:
        return (
          <ProcessingStep
            progress={progress}
            results={results}
            onCancel={() => setIsProcessing(false)}
          />
        );
      case 3:
        return (
          <PreviewStep
            results={results}
            onDownload={() => console.log('下载报告')}
            onRetry={(id) => console.log('重试:', id)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="batch-processing-wizard">
      {/* 步骤指示器 */}
      <div className="step-indicator">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          return (
            <div
              key={step.id}
              className={`step-item ${
                index === currentStep
                  ? 'active'
                  : index < currentStep
                  ? 'completed'
                  : ''
              }`}
            >
              <div className="step-icon">
                <Icon size={20} />
              </div>
              <span className="step-title">{step.title}</span>
              {index < STEPS.length - 1 && (
                <div className="step-line" />
              )}
            </div>
          );
        })}
      </div>

      {/* 步骤内容 */}
      <div className="wizard-content">{renderStep()}</div>

      {/* 底部按钮 */}
      <div className="wizard-footer">
        <button
          className="btn-prev"
          onClick={handlePrev}
          disabled={currentStep === 0}
        >
          <ChevronLeft size={16} />
          上一步
        </button>

        {currentStep === STEPS.length - 1 ? (
          <button className="btn-finish" onClick={onComplete}>
            完成
          </button>
        ) : (
          <button
            className="btn-next"
            onClick={handleNext}
            disabled={
              (currentStep === 0 && selectedIds.length === 0) || isProcessing
            }
          >
            {currentStep === 2 ? '开始处理' : '下一步'}
            <ChevronRight size={16} />
          </button>
        )}
      </div>
    </div>
  );
};

export default BatchProcessingWizard;
