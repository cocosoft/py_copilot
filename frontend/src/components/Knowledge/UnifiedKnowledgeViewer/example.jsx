/**
 * 一体化知识查看器使用示例 - FE-009
 *
 * 展示如何使用一体化知识查看器组件
 *
 * @task FE-009
 * @phase 前端功能拓展
 */

import React, { useState, useCallback } from 'react';
import UnifiedKnowledgeViewer from './index';
import { Box, Layers, FileText, Users, Link, BarChart3, Download, Eye } from 'lucide-react';

// ==================== 示例数据 ====================

const mockUnits = [
  {
    id: 'doc-1',
    type: 'DOCUMENT',
    title: '人工智能基础文档',
    content: '这是一份关于人工智能基础概念的文档，包含机器学习、深度学习等核心内容。',
    metadata: {
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-03-10T15:30:00Z',
      quality: 92.5,
      vectorCount: 5,
      entityCount: 12,
    },
  },
  {
    id: 'chunk-1',
    type: 'CHUNK',
    title: '机器学习概述',
    content: '机器学习是人工智能的一个分支，它使计算机能够从数据中学习而无需明确编程。',
    metadata: {
      createdAt: '2024-01-15T10:05:00Z',
      updatedAt: '2024-03-10T15:35:00Z',
      quality: 88.3,
      vectorCount: 1,
      entityCount: 3,
    },
  },
  {
    id: 'chunk-2',
    type: 'CHUNK',
    title: '深度学习原理',
    content: '深度学习使用多层神经网络来模拟人脑的工作方式，能够处理复杂的模式识别任务。',
    metadata: {
      createdAt: '2024-01-15T10:10:00Z',
      updatedAt: '2024-03-10T15:40:00Z',
      quality: 95.1,
      vectorCount: 1,
      entityCount: 4,
    },
  },
  {
    id: 'entity-1',
    type: 'ENTITY',
    title: '神经网络',
    content: '神经网络是一种模拟生物神经系统的计算模型，由相互连接的节点组成。',
    metadata: {
      createdAt: '2024-01-16T09:00:00Z',
      updatedAt: '2024-03-11T10:00:00Z',
      quality: 90.0,
      vectorCount: 1,
      entityCount: 0,
    },
  },
  {
    id: 'entity-2',
    type: 'ENTITY',
    title: '卷积神经网络',
    content: '卷积神经网络是一种专门用于处理图像数据的深度学习架构。',
    metadata: {
      createdAt: '2024-01-16T09:05:00Z',
      updatedAt: '2024-03-11T10:05:00Z',
      quality: 87.5,
      vectorCount: 1,
      entityCount: 0,
    },
  },
  {
    id: 'concept-1',
    type: 'CONCEPT',
    title: '监督学习',
    content: '监督学习是一种机器学习方法，使用标记数据来训练模型。',
    metadata: {
      createdAt: '2024-01-17T08:00:00Z',
      updatedAt: '2024-03-12T09:00:00Z',
      quality: 93.2,
      vectorCount: 1,
      entityCount: 2,
    },
  },
  {
    id: 'concept-2',
    type: 'CONCEPT',
    title: '无监督学习',
    content: '无监督学习在没有标记数据的情况下发现数据中的隐藏模式。',
    metadata: {
      createdAt: '2024-01-17T08:05:00Z',
      updatedAt: '2024-03-12T09:05:00Z',
      quality: 91.8,
      vectorCount: 1,
      entityCount: 2,
    },
  },
  {
    id: 'rel-1',
    type: 'RELATIONSHIP',
    title: '包含关系',
    content: '文档包含片段的关系',
    metadata: {
      createdAt: '2024-01-18T10:00:00Z',
      updatedAt: '2024-03-13T11:00:00Z',
      quality: 100.0,
      vectorCount: 0,
      entityCount: 0,
    },
  },
];

const mockAssociations = [
  { id: 'assoc-1', sourceId: 'doc-1', targetId: 'chunk-1', type: 'CONTAINS', strength: 1.0 },
  { id: 'assoc-2', sourceId: 'doc-1', targetId: 'chunk-2', type: 'CONTAINS', strength: 1.0 },
  { id: 'assoc-3', sourceId: 'chunk-2', targetId: 'entity-1', type: 'MENTIONS', strength: 0.9 },
  { id: 'assoc-4', sourceId: 'entity-1', targetId: 'entity-2', type: 'SUBCLASS_OF', strength: 0.85 },
  { id: 'assoc-5', sourceId: 'concept-1', targetId: 'chunk-1', type: 'RELATED_TO', strength: 0.75 },
  { id: 'assoc-6', sourceId: 'concept-2', targetId: 'chunk-1', type: 'RELATED_TO', strength: 0.7 },
];

// ==================== 示例 1: 基础用法 ====================

/**
 * 基础用法示例
 */
export const BasicExample = () => {
  const [selectedUnit, setSelectedUnit] = useState(null);

  const handleUnitSelect = useCallback((unit) => {
    console.log('选中知识单元:', unit);
    setSelectedUnit(unit);
  }, []);

  const handleExport = useCallback(() => {
    const data = {
      units: mockUnits,
      associations: mockAssociations,
      exportTime: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  return (
    <div style={{ height: '700px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
      <UnifiedKnowledgeViewer
        units={mockUnits}
        associations={mockAssociations}
        onUnitSelect={handleUnitSelect}
        onExport={handleExport}
      />
    </div>
  );
};

// ==================== 示例 2: 带选中状态 ====================

/**
 * 带选中状态示例
 */
export const WithSelectionExample = () => {
  const [selectedUnit, setSelectedUnit] = useState(mockUnits[0]);
  const [viewHistory, setViewHistory] = useState([]);

  const handleUnitSelect = useCallback((unit) => {
    setSelectedUnit(unit);
    setViewHistory((prev) => [
      { unit, timestamp: new Date().toISOString() },
      ...prev.slice(0, 9),
    ]);
  }, []);

  return (
    <div>
      <div
        style={{
          padding: '16px',
          background: '#fff',
          borderRadius: '8px',
          marginBottom: '16px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <h4 style={{ margin: '0 0 12px 0' }}>当前选中</h4>
        {selectedUnit ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Box size={20} color="#1890ff" />
            <div>
              <div style={{ fontWeight: 500 }}>{selectedUnit.title}</div>
              <div style={{ fontSize: '13px', color: '#8c8c8c' }}>
                {selectedUnit.type} | 质量: {selectedUnit.metadata.quality.toFixed(1)}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ color: '#8c8c8c' }}>未选择任何单元</div>
        )}

        {viewHistory.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <h5 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#8c8c8c' }}>
              浏览历史
            </h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {viewHistory.map((item, index) => (
                <div
                  key={index}
                  style={{
                    padding: '8px 12px',
                    background: '#f5f5f5',
                    borderRadius: '4px',
                    fontSize: '13px',
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>{item.unit.title}</span>
                  <span style={{ color: '#8c8c8c' }}>
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div style={{ height: '500px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <UnifiedKnowledgeViewer
          units={mockUnits}
          associations={mockAssociations}
          onUnitSelect={handleUnitSelect}
        />
      </div>
    </div>
  );
};

// ==================== 示例 3: 大数据量 ====================

/**
 * 大数据量示例
 */
export const LargeDataExample = () => {
  // 生成大量数据
  const largeUnits = Array.from({ length: 200 }, (_, i) => ({
    id: `unit-${i}`,
    type: ['DOCUMENT', 'CHUNK', 'ENTITY', 'CONCEPT'][Math.floor(Math.random() * 4)],
    title: `知识单元 ${i + 1}`,
    content: `这是第 ${i + 1} 个知识单元的内容描述，包含相关的知识和信息。`,
    metadata: {
      createdAt: new Date(Date.now() - Math.random() * 86400000 * 30).toISOString(),
      updatedAt: new Date().toISOString(),
      quality: Math.random() * 100,
      vectorCount: Math.floor(Math.random() * 10),
      entityCount: Math.floor(Math.random() * 5),
    },
  }));

  const largeAssociations = Array.from({ length: 100 }, (_, i) => ({
    id: `assoc-${i}`,
    sourceId: `unit-${Math.floor(Math.random() * 200)}`,
    targetId: `unit-${Math.floor(Math.random() * 200)}`,
    type: ['CONTAINS', 'REFERENCES', 'SIMILAR_TO', 'RELATED_TO'][Math.floor(Math.random() * 4)],
    strength: Math.random(),
  }));

  return (
    <div>
      <div
        style={{
          padding: '16px',
          background: '#e6f7ff',
          borderRadius: '8px',
          marginBottom: '16px',
          border: '1px solid #91d5ff',
        }}
      >
        <h4 style={{ margin: '0 0 8px 0', color: '#096dd9' }}>大数据量测试</h4>
        <p style={{ margin: 0, fontSize: '13px', color: '#595959' }}>
          当前加载 {largeUnits.length} 个知识单元和 {largeAssociations.length} 条关联关系
        </p>
      </div>

      <div style={{ height: '600px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <UnifiedKnowledgeViewer
          units={largeUnits}
          associations={largeAssociations}
        />
      </div>
    </div>
  );
};

// ==================== 示例 4: 自定义数据 ====================

/**
 * 自定义数据示例
 */
export const CustomDataExample = () => {
  const [customUnits, setCustomUnits] = useState(mockUnits);
  const [customAssociations, setCustomAssociations] = useState(mockAssociations);

  const addRandomUnit = () => {
    const types = ['DOCUMENT', 'CHUNK', 'ENTITY', 'CONCEPT'];
    const newUnit = {
      id: `unit-${Date.now()}`,
      type: types[Math.floor(Math.random() * types.length)],
      title: `新单元 ${customUnits.length + 1}`,
      content: '这是新添加的知识单元内容。',
      metadata: {
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        quality: Math.random() * 100,
        vectorCount: Math.floor(Math.random() * 10),
        entityCount: Math.floor(Math.random() * 5),
      },
    };
    setCustomUnits((prev) => [...prev, newUnit]);
  };

  const removeLastUnit = () => {
    setCustomUnits((prev) => prev.slice(0, -1));
  };

  return (
    <div>
      <div
        style={{
          padding: '16px',
          background: '#fff',
          borderRadius: '8px',
          marginBottom: '16px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <h4 style={{ margin: '0 0 12px 0' }}>数据操作</h4>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={addRandomUnit}
            style={{
              padding: '8px 16px',
              background: '#52c41a',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            添加单元
          </button>
          <button
            onClick={removeLastUnit}
            style={{
              padding: '8px 16px',
              background: '#ff4d4f',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            移除单元
          </button>
          <span style={{ marginLeft: 'auto', alignSelf: 'center', color: '#8c8c8c' }}>
            当前: {customUnits.length} 个单元, {customAssociations.length} 条关联
          </span>
        </div>
      </div>

      <div style={{ height: '500px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <UnifiedKnowledgeViewer
          units={customUnits}
          associations={customAssociations}
        />
      </div>
    </div>
  );
};

// ==================== 主示例页面 ====================

const UnifiedKnowledgeViewerExamples = () => {
  const [activeExample, setActiveExample] = useState('basic');

  const examples = {
    basic: { title: '基础用法', component: BasicExample, icon: Eye },
    selection: { title: '选中状态', component: WithSelectionExample, icon: Box },
    large: { title: '大数据量', component: LargeDataExample, icon: BarChart3 },
    custom: { title: '自定义数据', component: CustomDataExample, icon: Layers },
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
        <h1 style={{ margin: '0 0 16px 0' }}>一体化知识查看器示例 (FE-009)</h1>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {Object.entries(examples).map(([key, { title, icon: Icon }]) => (
            <button
              key={key}
              onClick={() => setActiveExample(key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background: activeExample === key ? '#1890ff' : '#f0f0f0',
                color: activeExample === key ? '#fff' : '#333',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              <Icon size={16} />
              {title}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: '24px' }}>
        <ActiveComponent />
      </div>
    </div>
  );
};

export default UnifiedKnowledgeViewerExamples;
