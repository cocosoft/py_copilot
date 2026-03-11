/**
 * 质量评估面板使用示例 - FE-004
 *
 * 展示如何使用质量评估面板组件
 *
 * @task FE-004
 * @phase 前端功能拓展
 */

import React, { useState, useCallback } from 'react';
import QualityPanel from './index';

// ==================== 模拟数据 ====================

const mockQualityData = {
  overallScore: 78.5,
  documentCount: 42,
  chunkCount: 1256,
  averageScore: 76.2,
  trend: 'up',
  trendValue: '+5.3%',
  distribution: {
    excellent: 320,
    good: 580,
    fair: 256,
    poor: 100,
  },
};

const mockAnomalyChunks = [
  {
    id: 1,
    sourceDocument: '技术文档.pdf',
    content: '这是一个示例片段内容，由于某些原因质量较低。可能是由于文本不完整、格式问题或者包含过多噪声。',
    score: 35,
    anomalyType: 'low_quality',
    issues: [
      { severity: 'high', description: '文本包含过多噪声和格式标记' },
      { severity: 'medium', description: '语义连贯性较差' },
      { severity: 'low', description: '长度偏短' },
    ],
    dimensionScores: {
      completeness: 45,
      coherence: 30,
      relevance: 60,
      readability: 40,
    },
  },
  {
    id: 2,
    sourceDocument: '产品手册.docx',
    content: '另一个示例片段，内容不完整，可能是在文档分割时出现了问题。',
    score: 42,
    anomalyType: 'incomplete',
    issues: [
      { severity: 'high', description: '内容在句子中间截断' },
      { severity: 'medium', description: '缺少上下文信息' },
    ],
    dimensionScores: {
      completeness: 25,
      coherence: 50,
      relevance: 70,
      readability: 55,
    },
  },
  {
    id: 3,
    sourceDocument: 'API文档.md',
    content: '这个片段与其他片段内容重复，可能是由于文档中存在重复章节导致的。',
    score: 55,
    anomalyType: 'duplicated',
    issues: [
      { severity: 'medium', description: '与片段 #45 内容相似度 85%' },
      { severity: 'low', description: '建议合并或删除' },
    ],
    dimensionScores: {
      completeness: 80,
      coherence: 75,
      relevance: 40,
      readability: 70,
    },
  },
  {
    id: 4,
    sourceDocument: '用户指南.pdf',
    content: '质量较低的片段示例，包含大量特殊字符和格式标记。',
    score: 28,
    anomalyType: 'low_quality',
    issues: [
      { severity: 'high', description: '包含大量HTML标签' },
      { severity: 'high', description: '特殊字符过多' },
      { severity: 'medium', description: '语义不清晰' },
    ],
    dimensionScores: {
      completeness: 30,
      coherence: 20,
      relevance: 50,
      readability: 25,
    },
  },
  {
    id: 5,
    sourceDocument: '开发文档.txt',
    content: '内容不完整的片段，在代码块中间被截断。',
    score: 38,
    anomalyType: 'incomplete',
    issues: [
      { severity: 'high', description: '代码块未闭合' },
      { severity: 'medium', description: '缺少后续说明' },
    ],
    dimensionScores: {
      completeness: 20,
      coherence: 45,
      relevance: 65,
      readability: 50,
    },
  },
];

const mockTrendData = [
  { date: '2024-01-01', score: 65, target: 80 },
  { date: '2024-01-05', score: 68, target: 80 },
  { date: '2024-01-10', score: 70, target: 80 },
  { date: '2024-01-15', score: 69, target: 80 },
  { date: '2024-01-20', score: 72, target: 80 },
  { date: '2024-01-25', score: 74, target: 80 },
  { date: '2024-02-01', score: 75, target: 80 },
  { date: '2024-02-05', score: 73, target: 80 },
  { date: '2024-02-10', score: 76, target: 80 },
  { date: '2024-02-15', score: 77, target: 80 },
  { date: '2024-02-20', score: 76, target: 80 },
  { date: '2024-02-25', score: 78, target: 80 },
  { date: '2024-03-01', score: 79, target: 80 },
  { date: '2024-03-05', score: 78, target: 80 },
  { date: '2024-03-10', score: 78.5, target: 80 },
];

const mockDimensionData = [
  { name: '完整性', score: 82 },
  { name: '连贯性', score: 76 },
  { name: '相关性', score: 88 },
  { name: '可读性', score: 71 },
  { name: '准确性', score: 85 },
  { name: '语义密度', score: 69 },
];

// ==================== 示例 1: 基础用法 ====================

/**
 * 基础质量评估面板示例
 */
export const BasicExample = () => {
  const [loading, setLoading] = useState(false);

  const handleReprocess = useCallback(async (chunkId) => {
    setLoading(true);
    // 模拟API调用
    await new Promise((resolve) => setTimeout(resolve, 1500));
    console.log('重处理片段:', chunkId);
    setLoading(false);
  }, []);

  const handleReprocessAll = useCallback(async () => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    console.log('重处理所有异常片段');
    setLoading(false);
  }, []);

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: '24px' }}>质量评估面板 - 基础示例</h2>

      <QualityPanel
        qualityData={mockQualityData}
        anomalyChunks={mockAnomalyChunks}
        trendData={mockTrendData}
        dimensionData={mockDimensionData}
        onReprocess={handleReprocess}
        onReprocessAll={handleReprocessAll}
        loading={loading}
      />
    </div>
  );
};

// ==================== 示例 2: 带选中重处理 ====================

/**
 * 带批量重处理功能的质量评估面板
 */
export const WithBatchReprocessExample = () => {
  const [loading, setLoading] = useState(false);
  const [reprocessedIds, setReprocessedIds] = useState([]);

  const handleReprocess = useCallback(async (chunkId) => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setReprocessedIds((prev) => [...prev, chunkId]);
    setLoading(false);
  }, []);

  const handleReprocessAll = useCallback(async () => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setReprocessedIds(mockAnomalyChunks.map((c) => c.id));
    setLoading(false);
  }, []);

  const handleReprocessSelected = useCallback(async (selectedIds) => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setReprocessedIds((prev) => [...prev, ...selectedIds]);
    setLoading(false);
  }, []);

  // 过滤掉已重处理的片段
  const remainingChunks = mockAnomalyChunks.filter(
    (c) => !reprocessedIds.includes(c.id)
  );

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: '24px' }}>质量评估面板 - 批量重处理</h2>

      {reprocessedIds.length > 0 && (
        <div
          style={{
            padding: '12px 16px',
            background: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: '4px',
            marginBottom: '16px',
          }}
        >
          ✅ 已成功重处理 {reprocessedIds.length} 个片段
        </div>
      )}

      <QualityPanel
        qualityData={{
          ...mockQualityData,
          anomalyCount: remainingChunks.length,
        }}
        anomalyChunks={remainingChunks}
        trendData={mockTrendData}
        dimensionData={mockDimensionData}
        onReprocess={handleReprocess}
        onReprocessAll={handleReprocessAll}
        onReprocessSelected={handleReprocessSelected}
        loading={loading}
      />
    </div>
  );
};

// ==================== 示例 3: 空状态 ====================

/**
 * 空状态示例
 */
export const EmptyExample = () => {
  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: '24px' }}>质量评估面板 - 空状态</h2>

      <QualityPanel qualityData={null} anomalyChunks={[]} />
    </div>
  );
};

// ==================== 示例 4: 加载状态 ====================

/**
 * 加载状态示例
 */
export const LoadingExample = () => {
  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: '24px' }}>质量评估面板 - 加载状态</h2>

      <QualityPanel
        qualityData={mockQualityData}
        anomalyChunks={mockAnomalyChunks}
        trendData={mockTrendData}
        dimensionData={mockDimensionData}
        onReprocess={() => {}}
        onReprocessAll={() => {}}
        loading={true}
      />
    </div>
  );
};

// ==================== 示例 5: 不同质量等级 ====================

/**
 * 不同质量等级示例
 */
export const DifferentQualityLevelsExample = () => {
  const excellentData = {
    ...mockQualityData,
    overallScore: 92,
    averageScore: 90,
    trend: 'up',
    trendValue: '+3.2%',
    distribution: {
      excellent: 800,
      good: 350,
      fair: 80,
      poor: 26,
    },
  };

  const poorData = {
    ...mockQualityData,
    overallScore: 45,
    averageScore: 48,
    trend: 'down',
    trendValue: '-8.5%',
    distribution: {
      excellent: 50,
      good: 150,
      fair: 400,
      poor: 656,
    },
  };

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: '24px' }}>质量评估面板 - 不同质量等级</h2>

      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ marginBottom: '16px' }}>优秀质量</h3>
        <QualityPanel
          qualityData={excellentData}
          anomalyChunks={mockAnomalyChunks.slice(0, 2)}
          trendData={mockTrendData}
          dimensionData={mockDimensionData.map((d) => ({
            ...d,
            score: Math.min(100, d.score + 15),
          }))}
        />
      </div>

      <div>
        <h3 style={{ marginBottom: '16px' }}>较差质量</h3>
        <QualityPanel
          qualityData={poorData}
          anomalyChunks={mockAnomalyChunks}
          trendData={mockTrendData.map((d) => ({
            ...d,
            score: Math.max(20, d.score - 30),
          }))}
          dimensionData={mockDimensionData.map((d) => ({
            ...d,
            score: Math.max(30, d.score - 25),
          }))}
        />
      </div>
    </div>
  );
};

// ==================== 示例 6: 文档级质量评估 ====================

/**
 * 文档级质量评估示例
 */
export const DocumentLevelExample = () => {
  const [selectedDocument, setSelectedDocument] = useState('doc1');

  const documents = [
    { id: 'doc1', name: '技术文档.pdf', score: 85 },
    { id: 'doc2', name: '产品手册.docx', score: 72 },
    { id: 'doc3', name: 'API文档.md', score: 91 },
    { id: 'doc4', name: '用户指南.pdf', score: 68 },
  ];

  const documentQualityData = {
    doc1: {
      overallScore: 85,
      documentCount: 1,
      chunkCount: 156,
      averageScore: 83,
      trend: 'up',
      trendValue: '+2.1%',
      distribution: {
        excellent: 80,
        good: 50,
        fair: 20,
        poor: 6,
      },
    },
    doc2: {
      overallScore: 72,
      documentCount: 1,
      chunkCount: 203,
      averageScore: 70,
      trend: 'stable',
      trendValue: '0%',
      distribution: {
        excellent: 40,
        good: 80,
        fair: 60,
        poor: 23,
      },
    },
    doc3: {
      overallScore: 91,
      documentCount: 1,
      chunkCount: 89,
      averageScore: 90,
      trend: 'up',
      trendValue: '+5.3%',
      distribution: {
        excellent: 60,
        good: 25,
        fair: 4,
        poor: 0,
      },
    },
    doc4: {
      overallScore: 68,
      documentCount: 1,
      chunkCount: 178,
      averageScore: 66,
      trend: 'down',
      trendValue: '-3.2%',
      distribution: {
        excellent: 25,
        good: 60,
        fair: 55,
        poor: 38,
      },
    },
  };

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: '24px' }}>质量评估面板 - 文档级评估</h2>

      <div style={{ marginBottom: '24px' }}>
        <label style={{ marginRight: '12px' }}>选择文档:</label>
        <select
          value={selectedDocument}
          onChange={(e) => setSelectedDocument(e.target.value)}
          style={{ padding: '8px 12px', fontSize: '14px' }}
        >
          {documents.map((doc) => (
            <option key={doc.id} value={doc.id}>
              {doc.name} (评分: {doc.score})
            </option>
          ))}
        </select>
      </div>

      <QualityPanel
        qualityData={documentQualityData[selectedDocument]}
        anomalyChunks={mockAnomalyChunks.filter(
          (c) => c.sourceDocument === documents.find((d) => d.id === selectedDocument)?.name
        )}
        trendData={mockTrendData}
        dimensionData={mockDimensionData}
      />
    </div>
  );
};

// ==================== 主示例页面 ====================

const QualityPanelExamples = () => {
  const [activeExample, setActiveExample] = useState('basic');

  const examples = {
    basic: { title: '基础用法', component: BasicExample },
    batch: { title: '批量重处理', component: WithBatchReprocessExample },
    empty: { title: '空状态', component: EmptyExample },
    loading: { title: '加载状态', component: LoadingExample },
    levels: { title: '不同质量等级', component: DifferentQualityLevelsExample },
    document: { title: '文档级评估', component: DocumentLevelExample },
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
        <h1 style={{ margin: '0 0 16px 0' }}>质量评估面板示例 (FE-004)</h1>

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

export default QualityPanelExamples;
