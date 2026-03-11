/**
 * 关联网络可视化使用示例 - FE-010
 *
 * 展示如何使用关联网络可视化组件
 *
 * @task FE-010
 * @phase 前端功能拓展
 */

import React, { useState, useCallback } from 'react';
import AssociationNetwork, { AssociationNetworkWithControls } from './index';
import { Network, Filter, Download, Settings, Eye, GitBranch } from 'lucide-react';

// ==================== 示例数据 ====================

const mockNodes = [
  { id: 'doc-1', label: '人工智能基础', type: 'DOCUMENT', x: 400, y: 300, size: 40, metadata: { description: 'AI基础概念文档', quality: 95 } },
  { id: 'chunk-1', label: '机器学习', type: 'CHUNK', x: 300, y: 200, size: 30, metadata: { description: '机器学习概述', quality: 88 } },
  { id: 'chunk-2', label: '深度学习', type: 'CHUNK', x: 500, y: 200, size: 30, metadata: { description: '深度学习原理', quality: 92 } },
  { id: 'entity-1', label: '神经网络', type: 'ENTITY', x: 250, y: 350, size: 25, metadata: { description: '神经网络概念', quality: 90 } },
  { id: 'entity-2', label: 'CNN', type: 'ENTITY', x: 550, y: 350, size: 25, metadata: { description: '卷积神经网络', quality: 85 } },
  { id: 'concept-1', label: '监督学习', type: 'CONCEPT', x: 350, y: 450, size: 28, metadata: { description: '监督学习方法', quality: 87 } },
  { id: 'concept-2', label: '无监督学习', type: 'CONCEPT', x: 450, y: 450, size: 28, metadata: { description: '无监督学习方法', quality: 86 } },
];

const mockLinks = [
  { id: 'link-1', source: 'doc-1', target: 'chunk-1', type: 'CONTAINS', strength: 1.0 },
  { id: 'link-2', source: 'doc-1', target: 'chunk-2', type: 'CONTAINS', strength: 1.0 },
  { id: 'link-3', source: 'chunk-1', target: 'entity-1', type: 'MENTIONS', strength: 0.9 },
  { id: 'link-4', source: 'chunk-2', target: 'entity-2', type: 'MENTIONS', strength: 0.85 },
  { id: 'link-5', source: 'entity-1', target: 'entity-2', type: 'SUBCLASS_OF', strength: 0.7 },
  { id: 'link-6', source: 'chunk-1', target: 'concept-1', type: 'RELATED_TO', strength: 0.8 },
  { id: 'link-7', source: 'chunk-2', target: 'concept-2', type: 'RELATED_TO', strength: 0.75 },
  { id: 'link-8', source: 'concept-1', target: 'concept-2', type: 'SIMILAR_TO', strength: 0.6 },
];

// ==================== 示例 1: 基础用法 ====================

/**
 * 基础用法示例
 */
export const BasicExample = () => {
  const [selectedNode, setSelectedNode] = useState(null);

  const handleNodeClick = useCallback((node) => {
    console.log('点击节点:', node);
    setSelectedNode(node);
  }, []);

  const handleNodeHover = useCallback((node) => {
    if (node) {
      console.log('悬停节点:', node.label);
    }
  }, []);

  return (
    <div>
      {selectedNode && (
        <div
          style={{
            padding: '12px 16px',
            background: '#e6f7ff',
            borderRadius: '8px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <Network size={20} color="#1890ff" />
          <div>
            <div style={{ fontWeight: 500 }}>选中节点: {selectedNode.label}</div>
            <div style={{ fontSize: '13px', color: '#8c8c8c' }}>
              类型: {selectedNode.type} | 质量: {selectedNode.metadata.quality}
            </div>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            style={{
              marginLeft: 'auto',
              padding: '4px 12px',
              background: '#1890ff',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            清除
          </button>
        </div>
      )}

      <div style={{ height: '600px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <AssociationNetwork
          nodes={mockNodes}
          links={mockLinks}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
        />
      </div>
    </div>
  );
};

// ==================== 示例 2: 大数据量 ====================

/**
 * 大数据量示例
 */
export const LargeDataExample = () => {
  // 生成大量数据
  const largeNodes = Array.from({ length: 100 }, (_, i) => ({
    id: `node-${i}`,
    label: `节点 ${i + 1}`,
    type: ['DOCUMENT', 'CHUNK', 'ENTITY', 'CONCEPT'][Math.floor(Math.random() * 4)],
    x: Math.random() * 800,
    y: Math.random() * 600,
    size: 20 + Math.random() * 20,
    metadata: {
      description: `节点 ${i + 1} 的描述`,
      quality: Math.random() * 100,
    },
  }));

  const largeLinks = Array.from({ length: 150 }, (_, i) => ({
    id: `link-${i}`,
    source: `node-${Math.floor(Math.random() * 100)}`,
    target: `node-${Math.floor(Math.random() * 100)}`,
    type: ['CONTAINS', 'REFERENCES', 'SIMILAR_TO', 'RELATED_TO', 'PART_OF'][Math.floor(Math.random() * 5)],
    strength: 0.3 + Math.random() * 0.7,
  }));

  return (
    <div>
      <div
        style={{
          padding: '16px',
          background: '#f6ffed',
          borderRadius: '8px',
          marginBottom: '16px',
          border: '1px solid #b7eb8f',
        }}
      >
        <h4 style={{ margin: '0 0 8px 0', color: '#389e0d' }}>大数据量测试</h4>
        <p style={{ margin: 0, fontSize: '13px', color: '#595959' }}>
          当前加载 {largeNodes.length} 个节点和 {largeLinks.length} 条关联
        </p>
      </div>

      <div style={{ height: '600px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <AssociationNetwork
          nodes={largeNodes}
          links={largeLinks}
        />
      </div>
    </div>
  );
};

// ==================== 示例 3: 带控制面板 ====================

/**
 * 带控制面板示例
 */
export const WithControlsExample = () => {
  return (
    <div style={{ height: '600px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
      <AssociationNetworkWithControls
        nodes={mockNodes}
        links={mockLinks}
      />
    </div>
  );
};

// ==================== 示例 4: 自定义样式 ====================

/**
 * 自定义样式示例
 */
export const CustomStyleExample = () => {
  const customNodes = mockNodes.map((node) => ({
    ...node,
    size: node.size * 1.5, // 放大节点
  }));

  return (
    <div>
      <div
        style={{
          padding: '16px',
          background: '#fff7e6',
          borderRadius: '8px',
          marginBottom: '16px',
          border: '1px solid #ffd591',
        }}
      >
        <h4 style={{ margin: '0 0 8px 0', color: '#d46b08' }}>自定义样式</h4>
        <p style={{ margin: 0, fontSize: '13px', color: '#595959' }}>
          节点大小已放大1.5倍，更易于查看
        </p>
      </div>

      <div style={{ height: '600px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <AssociationNetwork
          nodes={customNodes}
          links={mockLinks}
        />
      </div>
    </div>
  );
};

// ==================== 主示例页面 ====================

const AssociationNetworkExamples = () => {
  const [activeExample, setActiveExample] = useState('basic');

  const examples = {
    basic: { title: '基础用法', component: BasicExample, icon: Network },
    large: { title: '大数据量', component: LargeDataExample, icon: GitBranch },
    controls: { title: '带控制面板', component: WithControlsExample, icon: Settings },
    custom: { title: '自定义样式', component: CustomStyleExample, icon: Eye },
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
        <h1 style={{ margin: '0 0 16px 0' }}>关联网络可视化示例 (FE-010)</h1>

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

export default AssociationNetworkExamples;
