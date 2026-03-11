/**
 * 批量处理向导使用示例 - FE-005
 *
 * 展示如何使用批量处理向导组件
 *
 * @task FE-005
 * @phase 前端功能拓展
 */

import React, { useState, useCallback } from 'react';
import BatchProcessingWizard from './index';
import { Play, Settings, FileText } from 'lucide-react';

// ==================== 模拟数据 ====================

const mockDocuments = [
  { id: '1', title: '技术架构文档.pdf', fileType: 'pdf', size: 2048576, status: 'pending', lastProcessed: null },
  { id: '2', title: 'API接口规范.docx', fileType: 'docx', size: 1024000, status: 'completed', lastProcessed: '2024-03-01' },
  { id: '3', title: '用户手册.txt', fileType: 'txt', size: 512000, status: 'pending', lastProcessed: null },
  { id: '4', title: '开发指南.md', fileType: 'md', size: 768000, status: 'error', lastProcessed: '2024-02-28' },
  { id: '5', title: '产品需求文档.pdf', fileType: 'pdf', size: 3072000, status: 'pending', lastProcessed: null },
  { id: '6', title: '数据库设计.docx', fileType: 'docx', size: 1536000, status: 'completed', lastProcessed: '2024-03-05' },
  { id: '7', title: '部署文档.txt', fileType: 'txt', size: 256000, status: 'pending', lastProcessed: null },
  { id: '8', title: '测试报告.pdf', fileType: 'pdf', size: 4096000, status: 'processing', lastProcessed: null },
  { id: '9', title: '安全规范.md', fileType: 'md', size: 640000, status: 'pending', lastProcessed: null },
  { id: '10', title: '性能优化指南.docx', fileType: 'docx', size: 1280000, status: 'pending', lastProcessed: null },
];

// ==================== 示例 1: 基础用法 ====================

/**
 * 基础批量处理向导示例
 */
export const BasicExample = () => {
  const [isOpen, setIsOpen] = useState(false);

  const handleProcess = useCallback(async ({ documentIds, config, onProgress }) => {
    console.log('开始处理文档:', documentIds);
    console.log('配置:', config);

    // 模拟处理进度
    for (let i = 0; i < documentIds.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      onProgress({
        current: i + 1,
        total: documentIds.length,
        percentage: Math.round(((i + 1) / documentIds.length) * 100),
        currentDocument: mockDocuments.find((d) => d.id === documentIds[i])?.title,
      });
    }
  }, []);

  const handleCancel = useCallback(() => {
    console.log('用户取消处理');
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>批量处理向导 - 基础示例</h2>

      <button
        onClick={() => setIsOpen(true)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 24px',
          background: '#1890ff',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          fontSize: '14px',
          cursor: 'pointer',
        }}
      >
        <Play size={16} />
        打开批量处理向导
      </button>

      <BatchProcessingWizard
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        documents={mockDocuments}
        onProcess={handleProcess}
        onCancel={handleCancel}
      />
    </div>
  );
};

// ==================== 示例 2: 带状态管理 ====================

/**
 * 带状态管理的批量处理示例
 */
export const WithStateManagementExample = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [processingHistory, setProcessingHistory] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleProcess = useCallback(async ({ documentIds, config, onProgress }) => {
    setIsProcessing(true);

    const startTime = Date.now();

    // 模拟处理
    for (let i = 0; i < documentIds.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 600));
      onProgress({
        current: i + 1,
        total: documentIds.length,
        percentage: Math.round(((i + 1) / documentIds.length) * 100),
        currentDocument: mockDocuments.find((d) => d.id === documentIds[i])?.title,
      });
    }

    const endTime = Date.now();

    // 记录处理历史
    setProcessingHistory((prev) => [
      {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        documentCount: documentIds.length,
        config,
        duration: endTime - startTime,
      },
      ...prev,
    ]);

    setIsProcessing(false);
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>批量处理向导 - 状态管理</h2>

      <div style={{ marginBottom: '24px' }}>
        <button
          onClick={() => setIsOpen(true)}
          disabled={isProcessing}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            background: isProcessing ? '#d9d9d9' : '#1890ff',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            fontSize: '14px',
            cursor: isProcessing ? 'not-allowed' : 'pointer',
          }}
        >
          <Settings size={16} />
          {isProcessing ? '处理中...' : '批量处理文档'}
        </button>
      </div>

      {/* 处理历史 */}
      {processingHistory.length > 0 && (
        <div style={{ marginTop: '32px' }}>
          <h3 style={{ marginBottom: '16px' }}>处理历史</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {processingHistory.map((record) => (
              <div
                key={record.id}
                style={{
                  padding: '16px',
                  background: '#f5f5f5',
                  borderRadius: '8px',
                  border: '1px solid #e8e8e8',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 500 }}>
                    {new Date(record.timestamp).toLocaleString()}
                  </span>
                  <span style={{ color: '#52c41a' }}>
                    {record.documentCount} 个文档
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: '#8c8c8c' }}>
                  模式: {record.config.processingMode} | 
                  策略: {record.config.chunkStrategy} | 
                  耗时: {(record.duration / 1000).toFixed(1)}s
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <BatchProcessingWizard
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        documents={mockDocuments}
        onProcess={handleProcess}
      />
    </div>
  );
};

// ==================== 示例 3: 自定义处理逻辑 ====================

/**
 * 自定义处理逻辑示例
 */
export const CustomProcessingExample = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [results, setResults] = useState(null);

  const handleProcess = useCallback(async ({ documentIds, config, onProgress }) => {
    console.log('自定义处理逻辑');
    console.log('文档:', documentIds);
    console.log('配置:', config);

    // 模拟不同的处理结果
    const results = {
      total: documentIds.length,
      success: 0,
      failed: 0,
      skipped: 0,
      details: [],
    };

    for (let i = 0; i < documentIds.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 500));

      const doc = mockDocuments.find((d) => d.id === documentIds[i]);
      const random = Math.random();

      let status, error, details;
      if (random > 0.7) {
        status = 'success';
        results.success++;
        details = {
          chunkCount: Math.floor(Math.random() * 50 + 10),
          entityCount: Math.floor(Math.random() * 20 + 5),
        };
      } else if (random > 0.4) {
        status = 'skipped';
        results.skipped++;
        error = '文档已是最新版本';
      } else {
        status = 'error';
        results.failed++;
        error = '处理过程中发生错误';
      }

      results.details.push({
        id: documentIds[i],
        documentName: doc?.title,
        status,
        error,
        details,
        processingTime: (Math.random() * 5 + 1).toFixed(1),
      });

      onProgress({
        current: i + 1,
        total: documentIds.length,
        percentage: Math.round(((i + 1) / documentIds.length) * 100),
        currentDocument: doc?.title,
      });
    }

    setResults(results);
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>批量处理向导 - 自定义处理</h2>

      <button
        onClick={() => setIsOpen(true)}
        style={{
          padding: '12px 24px',
          background: '#52c41a',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          fontSize: '14px',
          cursor: 'pointer',
        }}
      >
        开始自定义处理
      </button>

      {results && (
        <div style={{ marginTop: '24px', padding: '16px', background: '#f6ffed', borderRadius: '8px' }}>
          <h4>上次处理结果</h4>
          <p>成功: {results.success} | 失败: {results.failed} | 跳过: {results.skipped}</p>
        </div>
      )}

      <BatchProcessingWizard
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        documents={mockDocuments}
        onProcess={handleProcess}
      />
    </div>
  );
};

// ==================== 示例 4: 集成到页面 ====================

/**
 * 页面集成示例
 */
export const PageIntegrationExample = () => {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [documents, setDocuments] = useState(mockDocuments);

  const handleProcess = useCallback(async ({ documentIds, config, onProgress }) => {
    // 更新文档状态为处理中
    setDocuments((prev) =>
      prev.map((doc) =>
        documentIds.includes(doc.id) ? { ...doc, status: 'processing' } : doc
      )
    );

    // 模拟处理
    for (let i = 0; i < documentIds.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 700));
      onProgress({
        current: i + 1,
        total: documentIds.length,
        percentage: Math.round(((i + 1) / documentIds.length) * 100),
        currentDocument: mockDocuments.find((d) => d.id === documentIds[i])?.title,
      });
    }

    // 更新文档状态为已完成
    setDocuments((prev) =>
      prev.map((doc) =>
        documentIds.includes(doc.id)
          ? { ...doc, status: 'completed', lastProcessed: new Date().toISOString() }
          : doc
      )
    );
  }, []);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2>文档管理</h2>
        <button
          onClick={() => setIsWizardOpen(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            background: '#1890ff',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          <Play size={16} />
          批量处理
        </button>
      </div>

      {/* 文档列表 */}
      <div style={{ display: 'grid', gap: '12px' }}>
        {documents.map((doc) => (
          <div
            key={doc.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              padding: '16px',
              background: '#fff',
              borderRadius: '8px',
              border: '1px solid #f0f0f0',
            }}
          >
            <FileText size={24} color="#1890ff" />
            <div style={{ flex: 1 }}>
              <h4 style={{ margin: '0 0 4px 0' }}>{doc.title}</h4>
              <div style={{ fontSize: '13px', color: '#8c8c8c' }}>
                {doc.fileType?.toUpperCase()} · {(doc.size / 1024).toFixed(1)} KB
              </div>
            </div>
            <span
              style={{
                padding: '4px 12px',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 500,
                background:
                  doc.status === 'completed'
                    ? '#f6ffed'
                    : doc.status === 'processing'
                    ? '#e6f7ff'
                    : doc.status === 'error'
                    ? '#fff1f0'
                    : '#f0f0f0',
                color:
                  doc.status === 'completed'
                    ? '#52c41a'
                    : doc.status === 'processing'
                    ? '#1890ff'
                    : doc.status === 'error'
                    ? '#ff4d4f'
                    : '#595959',
              }}
            >
              {doc.status}
            </span>
          </div>
        ))}
      </div>

      <BatchProcessingWizard
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        documents={documents}
        onProcess={handleProcess}
      />
    </div>
  );
};

// ==================== 主示例页面 ====================

const BatchProcessingWizardExamples = () => {
  const [activeExample, setActiveExample] = useState('basic');

  const examples = {
    basic: { title: '基础用法', component: BasicExample },
    state: { title: '状态管理', component: WithStateManagementExample },
    custom: { title: '自定义处理', component: CustomProcessingExample },
    integration: { title: '页面集成', component: PageIntegrationExample },
  };

  const ActiveComponent = examples[activeExample].component;

  return (
    <div>
      <div
        style={{
          padding: '16px 24px',
          background: '#fff',
          borderBottom: '1px solid #f0f0f0',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <h1 style={{ margin: '0 0 16px 0' }}>批量处理向导示例 (FE-005)</h1>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {Object.entries(examples).map(([key, { title }]) => (
            <button
              key={key}
              onClick={() => setActiveExample(key)}
              style={{
                padding: '8px 16px',
                background: activeExample === key ? '#1890ff' : '#f0f0f0',
                color: activeExample === key ? '#fff' : '#333',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              {title}
            </button>
          ))}
        </div>
      </div>

      <ActiveComponent />
    </div>
  );
};

export default BatchProcessingWizardExamples;
