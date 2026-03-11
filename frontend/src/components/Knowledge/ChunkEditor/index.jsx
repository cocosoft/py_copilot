/**
 * 知识块编辑器组件
 *
 * 提供知识块内容的编辑、验证和保存功能
 */

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import {
  Edit3,
  Save,
  Undo,
  Redo,
  Scissors,
  Merge,
  Split,
  Eye,
  EyeOff,
  Check,
  X,
  ChevronLeft,
  ChevronRight,
  Copy,
  Trash2,
  Plus,
  AlignLeft,
  Type,
  FileText,
  AlertTriangle,
  Maximize2,
  Minimize2,
} from '../icons.jsx';
import './ChunkEditor.css';

/**
 * 知识块编辑器
 *
 * @param {Object} props - 组件属性
 * @param {Array} props.chunks - 知识块列表
 * @param {Function} props.onSave - 保存回调
 * @param {Function} props.onCancel - 取消回调
 * @param {Function} props.onSplit - 拆分回调
 * @param {Function} props.onMerge - 合并回调
 * @param {Function} props.onDelete - 删除回调
 */
const ChunkEditor = ({
  chunks = [],
  onSave,
  onCancel,
  onSplit,
  onMerge,
  onDelete,
}) => {
  // 状态管理
  const [editedChunks, setEditedChunks] = useState(chunks);
  const [selectedChunks, setSelectedChunks] = useState(new Set());
  const [currentIndex, setCurrentIndex] = useState(0);
  const [history, setHistory] = useState([chunks]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const editorRef = useRef(null);

  // 同步外部chunks变化
  useEffect(() => {
    setEditedChunks(chunks);
    setHistory([chunks]);
    setHistoryIndex(0);
  }, [chunks]);

  // 当前编辑的知识块
  const currentChunk = editedChunks[currentIndex];

  // 添加历史记录
  const addToHistory = useCallback((newChunks) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newChunks);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [history, historyIndex]);

  // 撤销
  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setEditedChunks(history[historyIndex - 1]);
    }
  }, [history, historyIndex]);

  // 重做
  const handleRedo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setEditedChunks(history[historyIndex + 1]);
    }
  }, [history, historyIndex]);

  // 更新知识块内容
  const handleContentChange = useCallback((index, newContent) => {
    const newChunks = [...editedChunks];
    newChunks[index] = { ...newChunks[index], content: newContent };
    setEditedChunks(newChunks);
    addToHistory(newChunks);
    validateChunk(index, newContent);
  }, [editedChunks, addToHistory]);

  // 验证知识块
  const validateChunk = useCallback((index, content) => {
    const errors = {};
    if (!content || content.trim().length === 0) {
      errors[index] = '内容不能为空';
    } else if (content.length > 10000) {
      errors[index] = '内容超过最大长度限制(10000字符)';
    }
    setValidationErrors(prev => ({ ...prev, ...errors }));
    return Object.keys(errors).length === 0;
  }, []);

  // 选择/取消选择知识块
  const toggleChunkSelection = useCallback((index) => {
    const newSelected = new Set(selectedChunks);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedChunks(newSelected);
  }, [selectedChunks]);

  // 全选
  const selectAll = useCallback(() => {
    if (selectedChunks.size === editedChunks.length) {
      setSelectedChunks(new Set());
    } else {
      setSelectedChunks(new Set(editedChunks.map((_, i) => i)));
    }
  }, [editedChunks, selectedChunks]);

  // 拆分知识块
  const handleSplit = useCallback((index, splitPosition) => {
    const chunk = editedChunks[index];
    const content = chunk.content;
    
    if (splitPosition <= 0 || splitPosition >= content.length) {
      return;
    }

    const newChunks = [...editedChunks];
    const firstPart = content.slice(0, splitPosition);
    const secondPart = content.slice(splitPosition);

    newChunks.splice(index, 1,
      { ...chunk, content: firstPart },
      { ...chunk, content: secondPart, id: `${chunk.id}_split` }
    );

    setEditedChunks(newChunks);
    addToHistory(newChunks);
    onSplit?.(index, splitPosition);
  }, [editedChunks, addToHistory, onSplit]);

  // 合并选中的知识块
  const handleMerge = useCallback(() => {
    if (selectedChunks.size < 2) return;

    const indices = Array.from(selectedChunks).sort((a, b) => a - b);
    const firstIndex = indices[0];
    const mergedContent = indices.map(i => editedChunks[i].content).join('\n\n');

    const newChunks = editedChunks.filter((_, i) => !selectedChunks.has(i));
    newChunks.splice(firstIndex, 0, {
      ...editedChunks[firstIndex],
      content: mergedContent,
    });

    setEditedChunks(newChunks);
    setSelectedChunks(new Set());
    addToHistory(newChunks);
    onMerge?.(indices);
  }, [editedChunks, selectedChunks, addToHistory, onMerge]);

  // 删除选中的知识块
  const handleDelete = useCallback(() => {
    if (selectedChunks.size === 0) return;

    const newChunks = editedChunks.filter((_, i) => !selectedChunks.has(i));
    setEditedChunks(newChunks);
    setSelectedChunks(new Set());
    addToHistory(newChunks);
    onDelete?.(Array.from(selectedChunks));
  }, [editedChunks, selectedChunks, addToHistory, onDelete]);

  // 保存所有更改
  const handleSave = useCallback(() => {
    // 验证所有知识块
    let hasErrors = false;
    editedChunks.forEach((chunk, index) => {
      if (!validateChunk(index, chunk.content)) {
        hasErrors = true;
      }
    });

    if (hasErrors) {
      alert('请修复验证错误后再保存');
      return;
    }

    onSave?.(editedChunks);
  }, [editedChunks, validateChunk, onSave]);

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'z':
            e.preventDefault();
            if (e.shiftKey) {
              handleRedo();
            } else {
              handleUndo();
            }
            break;
          case 's':
            e.preventDefault();
            handleSave();
            break;
          default:
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleUndo, handleRedo, handleSave]);

  // 统计信息
  const stats = useMemo(() => {
    const totalChars = editedChunks.reduce((sum, chunk) => sum + chunk.content.length, 0);
    const avgLength = editedChunks.length > 0 ? Math.round(totalChars / editedChunks.length) : 0;
    return {
      totalChunks: editedChunks.length,
      totalChars,
      avgLength,
      selectedCount: selectedChunks.size,
    };
  }, [editedChunks, selectedChunks]);

  return (
    <div className={`chunk-editor ${isFullscreen ? 'fullscreen' : ''}`} ref={editorRef}>
      {/* 工具栏 */}
      <div className="editor-toolbar">
        <div className="toolbar-group">
          <button
            className="toolbar-btn"
            onClick={handleUndo}
            disabled={historyIndex === 0}
            title="撤销 (Ctrl+Z)"
          >
            <Undo size={16} />
          </button>
          <button
            className="toolbar-btn"
            onClick={handleRedo}
            disabled={historyIndex === history.length - 1}
            title="重做 (Ctrl+Shift+Z)"
          >
            <Redo size={16} />
          </button>
        </div>

        <div className="toolbar-group">
          <button
            className="toolbar-btn"
            onClick={selectAll}
            title="全选"
          >
            <AlignLeft size={16} />
          </button>
          <button
            className="toolbar-btn"
            onClick={handleMerge}
            disabled={selectedChunks.size < 2}
            title="合并选中"
          >
            <Merge size={16} />
          </button>
          <button
            className="toolbar-btn"
            onClick={() => handleSplit(currentIndex, Math.floor(currentChunk?.content.length / 2))}
            disabled={!currentChunk || currentChunk.content.length < 100}
            title="拆分当前"
          >
            <Split size={16} />
          </button>
          <button
            className="toolbar-btn danger"
            onClick={handleDelete}
            disabled={selectedChunks.size === 0}
            title="删除选中"
          >
            <Trash2 size={16} />
          </button>
        </div>

        <div className="toolbar-group">
          <button
            className="toolbar-btn"
            onClick={() => setShowPreview(!showPreview)}
            title={showPreview ? '隐藏预览' : '显示预览'}
          >
            {showPreview ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
          <button
            className="toolbar-btn"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? '退出全屏' : '全屏编辑'}
          >
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>

        <div className="toolbar-group">
          <button className="toolbar-btn" onClick={onCancel}>
            <X size={16} />
            取消
          </button>
          <button className="toolbar-btn primary" onClick={handleSave}>
            <Save size={16} />
            保存
          </button>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="editor-stats">
        <span>总块数: {stats.totalChunks}</span>
        <span>总字符: {stats.totalChars}</span>
        <span>平均长度: {stats.avgLength}</span>
        <span>已选择: {stats.selectedCount}</span>
      </div>

      {/* 主编辑区 */}
      <div className="editor-main">
        {/* 知识块列表 */}
        <div className="chunks-list">
          {editedChunks.map((chunk, index) => (
            <div
              key={chunk.id || index}
              className={`chunk-item ${index === currentIndex ? 'active' : ''} ${
                selectedChunks.has(index) ? 'selected' : ''
              } ${validationErrors[index] ? 'error' : ''}`}
              onClick={() => setCurrentIndex(index)}
            >
              <div className="chunk-header">
                <input
                  type="checkbox"
                  checked={selectedChunks.has(index)}
                  onChange={() => toggleChunkSelection(index)}
                  onClick={(e) => e.stopPropagation()}
                />
                <span className="chunk-index">#{index + 1}</span>
                <span className="chunk-length">{chunk.content.length} 字符</span>
              </div>
              <div className="chunk-preview">
                {chunk.content.slice(0, 100)}...
              </div>
              {validationErrors[index] && (
                <div className="validation-error">
                  <AlertTriangle size={14} />
                  {validationErrors[index]}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 编辑区 */}
        <div className="editor-content">
          {currentChunk ? (
            <>
              <div className="content-header">
                <FileText size={16} />
                <span>编辑知识块 #{currentIndex + 1}</span>
              </div>
              <textarea
                className="content-textarea"
                value={currentChunk.content}
                onChange={(e) => handleContentChange(currentIndex, e.target.value)}
                placeholder="输入知识块内容..."
              />
              {showPreview && (
                <div className="content-preview">
                  <h4>预览</h4>
                  <div className="preview-content">
                    {currentChunk.content}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="empty-state">
              <Type size={48} />
              <p>选择一个知识块进行编辑</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChunkEditor;
