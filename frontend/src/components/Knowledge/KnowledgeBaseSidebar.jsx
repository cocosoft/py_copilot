/**
 * 知识库侧边栏组件
 *
 * 显示知识库列表，支持选择、创建、导入、导出和删除操作
 */

import React, { useState, useEffect, useCallback } from 'react';
import { FaDownload } from 'react-icons/fa';
import useKnowledgeStore from '../../stores/knowledgeStore';
import { getKnowledgeBases, createKnowledgeBase, deleteKnowledgeBase, exportKnowledgeBase, importKnowledgeBase } from '../../utils/api/knowledgeApi';
import { message } from '../UI/Message/Message';
import './KnowledgeBaseSidebar.css';

/**
 * 知识库侧边栏组件
 *
 * @param {Object} props - 组件属性
 * @param {boolean} props.collapsed - 是否折叠
 * @returns {JSX.Element} 知识库侧边栏
 */
const KnowledgeBaseSidebar = ({ collapsed }) => {
  const {
    currentKnowledgeBase,
    setCurrentKnowledgeBase,
    setKnowledgeBases,
    knowledgeBases
  } = useKnowledgeStore();

  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalKbs, setTotalKbs] = useState(0);
  const pageSize = 10;

  /**
   * 加载知识库列表
   */
  const fetchKnowledgeBases = useCallback(async () => {
    setLoading(true);
    try {
      const skip = (currentPage - 1) * pageSize;
      const response = await getKnowledgeBases(skip, pageSize);

      const kbs = Array.isArray(response) ? response : (response.items || response.data || []);
      const total = Array.isArray(response) ? response.length : (response.total || kbs.length);

      setKnowledgeBases(kbs, total);
      setTotalKbs(total);
      setTotalPages(Math.ceil(total / pageSize));
    } catch (error) {
      message.error({ content: '加载知识库列表失败：' + error.message });
    } finally {
      setLoading(false);
    }
  }, [currentPage, setKnowledgeBases]);

  // 初始加载
  useEffect(() => {
    fetchKnowledgeBases();
  }, [fetchKnowledgeBases]);

  /**
   * 选择知识库
   */
  const handleSelect = useCallback((kb) => {
    setCurrentKnowledgeBase(kb);
  }, [setCurrentKnowledgeBase]);

  /**
   * 创建知识库
   */
  const handleCreate = useCallback(async () => {
    const name = prompt('请输入知识库名称：');
    if (!name) return;

    const description = prompt('请输入知识库描述（可选）：');

    try {
      await createKnowledgeBase(name, description || '');
      message.success({ content: '知识库创建成功' });
      fetchKnowledgeBases();
    } catch (error) {
      message.error({ content: '创建失败：' + error.message });
    }
  }, [fetchKnowledgeBases]);

  /**
   * 导入知识库
   */
  const handleImport = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        const content = await file.text();
        const data = JSON.parse(content);
        await importKnowledgeBase(data);
        message.success({ content: '知识库导入成功' });
        fetchKnowledgeBases();
      } catch (error) {
        message.error({ content: '导入失败：' + error.message });
      }
    };
    input.click();
  }, [fetchKnowledgeBases]);

  /**
   * 导出知识库
   */
  const handleExport = useCallback(async (kb) => {
    try {
      const data = await exportKnowledgeBase(kb.id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `knowledge-base-${kb.name}.json`;
      a.click();
      URL.revokeObjectURL(url);
      message.success({ content: '导出成功' });
    } catch (error) {
      message.error({ content: '导出失败：' + error.message });
    }
  }, []);

  /**
   * 删除知识库
   */
  const handleDelete = useCallback(async (kb) => {
    if (!confirm(`确定要删除知识库 "${kb.name}" 吗？此操作不可恢复。`)) {
      return;
    }

    try {
      await deleteKnowledgeBase(kb.id);
      message.success({ content: '知识库已删除' });
      if (currentKnowledgeBase?.id === kb.id) {
        setCurrentKnowledgeBase(null);
      }
      fetchKnowledgeBases();
    } catch (error) {
      message.error({ content: '删除失败：' + error.message });
    }
  }, [currentKnowledgeBase, setCurrentKnowledgeBase, fetchKnowledgeBases]);

  /**
   * 页码变化
   */
  const handlePageChange = useCallback((page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  }, [totalPages]);

  // 如果折叠，显示简化视图
  if (collapsed) {
    return (
      <div className="knowledge-sidebar collapsed">
        <div className="sidebar-header">
          <button
            className="sidebar-btn create-btn"
            onClick={handleCreate}
            title="新建知识库"
          >
            +
          </button>
        </div>
        <div className="sidebar-content collapsed">
          {knowledgeBases.map(kb => (
            <div
              key={kb.id}
              className={`sidebar-item collapsed ${currentKnowledgeBase?.id === kb.id ? 'active' : ''}`}
              onClick={() => handleSelect(kb)}
              title={kb.name}
            >
              <div className="sidebar-item-icon">📚</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="knowledge-sidebar">
      <div className="sidebar-header">
        <h3>知识库</h3>
        <div className="sidebar-actions">
          <button
            className="sidebar-btn create-btn"
            onClick={handleCreate}
            title="新建知识库"
          >
            +
          </button>
          <button
            className="sidebar-btn import-btn"
            onClick={handleImport}
            title="导入知识库"
          >
            📥
          </button>
        </div>
      </div>

      <div className="sidebar-content">
        {loading ? (
          <div className="sidebar-loading">
            <div className="loading-spinner"></div>
            <span>加载中...</span>
          </div>
        ) : knowledgeBases?.length > 0 ? (
          <div className="sidebar-list">
            {knowledgeBases.map(kb => (
              <div
                key={kb.id}
                className={`sidebar-item ${currentKnowledgeBase?.id === kb.id ? 'active' : ''}`}
                onClick={() => handleSelect(kb)}
                title={kb.description || kb.name}
              >
                <div className="sidebar-item-icon">📚</div>
                <div className="sidebar-item-info">
                  <span className="sidebar-item-name">{kb.name}</span>
                  {kb.document_count !== undefined && (
                    <span className="sidebar-item-count">{kb.document_count} 文档</span>
                  )}
                </div>
                <div className="sidebar-item-actions">
                  <button
                    className="sidebar-action-btn export-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleExport(kb);
                    }}
                    title="导出"
                  >
                    <FaDownload />
                  </button>
                  <button
                    className="sidebar-action-btn delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(kb);
                    }}
                    title="删除"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="sidebar-empty">
            <span>暂无知识库</span>
            <button onClick={handleCreate}>创建知识库</button>
          </div>
        )}
      </div>

      {/* 知识库分页控件 */}
      {totalKbs > 0 && (
        <div className="sidebar-pagination">
          <div className="sidebar-pagination-info">
            {currentPage}/{totalPages}页
          </div>
          <div className="sidebar-pagination-controls">
            <button
              className="sidebar-page-btn"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              ‹
            </button>
            <button
              className="sidebar-page-btn"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              ›
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseSidebar;
