/**
 * 交互式片段编辑器使用示例 - FE-007
 *
 * 展示如何使用片段编辑器组件
 *
 * @task FE-007
 * @phase 前端功能拓展
 */

import React, { useState, useCallback } from 'react';
import ChunkEditor, { ChunkEditorWithDocument } from './index';
import { Edit3, FileText, Save, Eye, Layers } from 'lucide-react';

// ==================== 模拟数据 ====================

const mockDocuments = [
  { id: '1', title: '人工智能基础.txt', chunkCount: 6, status: 'active' },
  { id: '2', title: '机器学习算法.pdf', chunkCount: 12, status: 'active' },
  { id: '3', title: '深度学习实践.docx', chunkCount: 8, status: 'processing' },
  { id: '4', title: '自然语言处理.md', chunkCount: 15, status: 'active' },
];

// ==================== 示例 1: 基础用法 ====================

/**
 * 基础片段编辑器示例
 */
export const BasicExample = () => {
  const [savedData, setSavedData] = useState(null);

  const handleSave = useCallback((chunks) => {
    console.log('保存的片段:', chunks);
    setSavedData(chunks);
    alert(`成功保存 ${chunks.length} 个片段`);
  }, []);

  const handleCancel = useCallback(() => {
    console.log('用户取消编辑');
  }, []);

  return (
    <div style={{ height: '600px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
      <ChunkEditor
        documentTitle="人工智能基础文档"
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </div>
  );
};

// ==================== 示例 2: 带文档选择 ====================

/**
 * 带文档选择的片段编辑器示例
 */
export const WithDocumentSelectionExample = () => {
  const [lastSaved, setLastSaved] = useState(null);

  const handleSave = useCallback((documentId, chunks) => {
    console.log('保存文档:', documentId, chunks);
    setLastSaved({ documentId, chunkCount: chunks.length, timestamp: new Date().toISOString() });
    alert(`文档 ${documentId} 的 ${chunks.length} 个片段已保存`);
  }, []);

  return (
    <div>
      <div style={{ padding: '16px', background: '#f5f5f5', borderRadius: '8px', marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px 0' }}>最近保存</h4>
        {lastSaved ? (
          <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
            文档ID: {lastSaved.documentId} | 片段数: {lastSaved.chunkCount} | 
            时间: {new Date(lastSaved.timestamp).toLocaleString()}
          </p>
        ) : (
          <p style={{ margin: 0, fontSize: '13px', color: '#999' }}>暂无保存记录</p>
        )}
      </div>

      <div style={{ height: '500px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <ChunkEditorWithDocument
          documents={mockDocuments}
          onSave={handleSave}
        />
      </div>
    </div>
  );
};

// ==================== 示例 3: 只读模式 ====================

/**
 * 只读模式示例
 */
export const ReadOnlyExample = () => {
  return (
    <div>
      <div style={{ padding: '12px 16px', background: '#e6f7ff', borderRadius: '8px', marginBottom: '16px' }}>
        <p style={{ margin: 0, fontSize: '13px', color: '#1890ff' }}>
          <Eye size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          当前为只读模式，只能查看不能编辑
        </p>
      </div>

      <div style={{ height: '500px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <ChunkEditor
          documentTitle="只读文档示例"
          readOnly={true}
        />
      </div>
    </div>
  );
};

// ==================== 示例 4: 自定义初始数据 ====================

/**
 * 自定义初始数据示例
 */
export const CustomDataExample = () => {
  const [editCount, setEditCount] = useState(0);

  const customChunks = [
    {
      id: 'custom-1',
      content: '这是第一个自定义片段。您可以编辑、分割、合并这些片段。',
      startIndex: 0,
      endIndex: 32,
      metadata: { wordCount: 32, charCount: 32, entityCount: 0, quality: 0.95 },
      status: 'active',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: 'custom-2',
      content: '这是第二个片段，展示了不同的内容。支持撤销和重做功能。',
      startIndex: 32,
      endIndex: 64,
      metadata: { wordCount: 32, charCount: 32, entityCount: 0, quality: 0.88 },
      status: 'active',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: 'custom-3',
      content: '第三个片段可以与前一个合并，也可以被分割成更小的片段。',
      startIndex: 64,
      endIndex: 96,
      metadata: { wordCount: 32, charCount: 32, entityCount: 0, quality: 0.92 },
      status: 'active',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ];

  const handleSave = useCallback((chunks) => {
    setEditCount((prev) => prev + 1);
    alert(`已保存！这是第 ${editCount + 1} 次保存`);
  }, [editCount]);

  return (
    <div>
      <div style={{ padding: '12px 16px', background: '#f6ffed', borderRadius: '8px', marginBottom: '16px' }}>
        <p style={{ margin: 0, fontSize: '13px', color: '#52c41a' }}>
          <Edit3 size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          已加载 {customChunks.length} 个自定义片段，保存次数: {editCount}
        </p>
      </div>

      <div style={{ height: '500px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
        <ChunkEditor
          chunks={customChunks}
          documentTitle="自定义数据文档"
          onSave={handleSave}
        />
      </div>
    </div>
  );
};

// ==================== 示例 5: 批量编辑工作流 ====================

/**
 * 批量编辑工作流示例
 */
export const BatchEditWorkflowExample = () => {
  const [workflow, setWorkflow] = useState({
    step: 'select', // select, edit, review
    selectedDoc: null,
    editedChunks: null,
  });

  const handleDocumentSelect = (doc) => {
    setWorkflow({ step: 'edit', selectedDoc: doc, editedChunks: null });
  };

  const handleSave = (chunks) => {
    setWorkflow((prev) => ({ ...prev, step: 'review', editedChunks: chunks }));
  };

  const handleBack = () => {
    setWorkflow({ step: 'select', selectedDoc: null, editedChunks: null });
  };

  const handleConfirm = () => {
    alert('批量编辑完成！');
    setWorkflow({ step: 'select', selectedDoc: null, editedChunks: null });
  };

  return (
    <div>
      {/* 步骤指示器 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
        <div style={{
          padding: '8px 16px',
          background: workflow.step === 'select' ? '#1890ff' : workflow.step === 'edit' || workflow.step === 'review' ? '#52c41a' : '#f0f0f0',
          color: workflow.step === 'select' || workflow.step === 'edit' || workflow.step === 'review' ? '#fff' : '#666',
          borderRadius: '4px',
          fontSize: '13px',
        }}>
          1. 选择文档
        </div>
        <div style={{ color: '#d9d9d9' }}>→</div>
        <div style={{
          padding: '8px 16px',
          background: workflow.step === 'edit' ? '#1890ff' : workflow.step === 'review' ? '#52c41a' : '#f0f0f0',
          color: workflow.step === 'edit' || workflow.step === 'review' ? '#fff' : '#666',
          borderRadius: '4px',
          fontSize: '13px',
        }}>
          2. 编辑片段
        </div>
        <div style={{ color: '#d9d9d9' }}>→</div>
        <div style={{
          padding: '8px 16px',
          background: workflow.step === 'review' ? '#1890ff' : '#f0f0f0',
          color: workflow.step === 'review' ? '#fff' : '#666',
          borderRadius: '4px',
          fontSize: '13px',
        }}>
          3. 审核确认
        </div>
      </div>

      {/* 步骤内容 */}
      <div style={{ minHeight: '400px' }}>
        {workflow.step === 'select' && (
          <div>
            <h4 style={{ marginBottom: '16px' }}>选择要编辑的文档</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px' }}>
              {mockDocuments.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => handleDocumentSelect(doc)}
                  style={{
                    padding: '16px',
                    background: '#fff',
                    border: '1px solid #e8e8e8',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#1890ff';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(24, 144, 255, 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#e8e8e8';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <FileText size={24} color="#1890ff" />
                    <div>
                      <h5 style={{ margin: '0 0 4px 0', fontSize: '14px' }}>{doc.title}</h5>
                      <p style={{ margin: 0, fontSize: '12px', color: '#8c8c8c' }}>
                        {doc.chunkCount} 个片段
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {workflow.step === 'edit' && (
          <div style={{ height: '500px', border: '1px solid #e8e8e8', borderRadius: '8px', overflow: 'hidden' }}>
            <ChunkEditor
              documentTitle={workflow.selectedDoc?.title}
              onSave={handleSave}
              onCancel={handleBack}
            />
          </div>
        )}

        {workflow.step === 'review' && (
          <div>
            <div style={{ padding: '16px', background: '#f6ffed', borderRadius: '8px', marginBottom: '16px' }}>
              <h4 style={{ margin: '0 0 8px 0', color: '#52c41a' }}>
                <Save size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />
                编辑完成
              </h4>
              <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
                文档: {workflow.selectedDoc?.title} | 片段数: {workflow.editedChunks?.length}
              </p>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={handleBack}
                style={{
                  padding: '10px 20px',
                  background: '#f0f0f0',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                返回修改
              </button>
              <button
                onClick={handleConfirm}
                style={{
                  padding: '10px 20px',
                  background: '#52c41a',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                确认完成
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== 主示例页面 ====================

const ChunkEditorExamples = () => {
  const [activeExample, setActiveExample] = useState('basic');

  const examples = {
    basic: { title: '基础用法', component: BasicExample, icon: Edit3 },
    document: { title: '文档选择', component: WithDocumentSelectionExample, icon: FileText },
    readonly: { title: '只读模式', component: ReadOnlyExample, icon: Eye },
    custom: { title: '自定义数据', component: CustomDataExample, icon: Layers },
    workflow: { title: '批量工作流', component: BatchEditWorkflowExample, icon: Save },
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
        <h1 style={{ margin: '0 0 16px 0' }}>交互式片段编辑器示例 (FE-007)</h1>

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

export default ChunkEditorExamples;
