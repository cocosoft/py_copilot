/**
 * 文档级关系管理组件
 *
 * 用于管理文档内的实体关系
 */

import React, { useState, useEffect } from 'react';
import { FiSearch, FiFilter, FiPlus, FiTrash2, FiEdit2, FiRefreshCw } from 'react-icons/fi';
import { getDocumentRelations, deleteRelation } from '../../utils/api/hierarchyApi';
import { showNotification, NotificationType } from '../UI/Notification';
import './DocumentRelationManagement.css';

/**
 * 文档级关系管理组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @param {number} props.documentId - 文档ID
 * @returns {JSX.Element} 关系管理界面
 */
const DocumentRelationManagement = ({ knowledgeBaseId, documentId }) => {
  // 关系列表
  const [relations, setRelations] = useState([]);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 搜索关键词
  const [searchKeyword, setSearchKeyword] = useState('');
  // 关系类型筛选
  const [relationTypeFilter, setRelationTypeFilter] = useState('all');
  // 当前页
  const [currentPage, setCurrentPage] = useState(1);
  // 每页数量
  const [pageSize] = useState(10);
  // 总数量
  const [totalCount, setTotalCount] = useState(0);
  // 选中的关系
  const [selectedRelations, setSelectedRelations] = useState([]);

  // 加载关系列表
  useEffect(() => {
    if (knowledgeBaseId && documentId) {
      loadRelations();
    } else {
      setRelations([]);
      setTotalCount(0);
    }
  }, [knowledgeBaseId, documentId, currentPage, relationTypeFilter]);

  /**
   * 加载文档关系列表
   */
  const loadRelations = async () => {
    setLoading(true);
    try {
      const response = await getDocumentRelations(knowledgeBaseId, documentId, {
        page: currentPage,
        pageSize: pageSize,
        relationType: relationTypeFilter !== 'all' ? relationTypeFilter : ''
      });

      if (response.code === 200 && response.data) {
        setRelations(response.data.list || []);
        setTotalCount(response.data.total || 0);
      } else {
        setRelations([]);
        setTotalCount(0);
      }
    } catch (error) {
      console.error('加载关系列表失败:', error);
      showNotification({
        type: NotificationType.ERROR,
        message: '加载关系列表失败'
      });
      setRelations([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理搜索
   */
  const handleSearch = () => {
    setCurrentPage(1);
    loadRelations();
  };

  /**
   * 处理关系类型筛选变化
   */
  const handleTypeFilterChange = (e) => {
    setRelationTypeFilter(e.target.value);
    setCurrentPage(1);
  };

  /**
   * 处理选择关系
   */
  const handleSelectRelation = (relationId) => {
    setSelectedRelations(prev => {
      if (prev.includes(relationId)) {
        return prev.filter(id => id !== relationId);
      } else {
        return [...prev, relationId];
      }
    });
  };

  /**
   * 处理全选
   */
  const handleSelectAll = () => {
    if (selectedRelations.length === relations.length) {
      setSelectedRelations([]);
    } else {
      setSelectedRelations(relations.map(r => r.id));
    }
  };

  /**
   * 处理删除关系
   */
  const handleDeleteRelation = async (relationId) => {
    if (!window.confirm('确定要删除这个关系吗？')) {
      return;
    }

    try {
      await deleteRelation(knowledgeBaseId, relationId);
      showNotification({
        type: NotificationType.SUCCESS,
        message: '关系删除成功'
      });
      loadRelations();
    } catch (error) {
      console.error('删除关系失败:', error);
      showNotification({
        type: NotificationType.ERROR,
        message: '删除关系失败'
      });
    }
  };

  /**
   * 处理批量删除
   */
  const handleBatchDelete = async () => {
    if (selectedRelations.length === 0) {
      showNotification({
        type: NotificationType.WARNING,
        message: '请先选择要删除的关系'
      });
      return;
    }

    if (!window.confirm(`确定要删除选中的 ${selectedRelations.length} 个关系吗？`)) {
      return;
    }

    try {
      // 批量删除
      await Promise.all(selectedRelations.map(id => deleteRelation(knowledgeBaseId, id)));
      showNotification({
        type: NotificationType.SUCCESS,
        message: `成功删除 ${selectedRelations.length} 个关系`
      });
      setSelectedRelations([]);
      loadRelations();
    } catch (error) {
      console.error('批量删除关系失败:', error);
      showNotification({
        type: NotificationType.ERROR,
        message: '批量删除关系失败'
      });
    }
  };

  /**
   * 获取关系类型列表
   */
  const getRelationTypes = () => {
    const types = [...new Set(relations.map(r => r.relation_type))];
    return ['all', ...types];
  };

  /**
   * 获取关系类型标签
   */
  const getRelationTypeLabel = (type) => {
    const typeMap = {
      all: '全部类型',
      WORKS_FOR: '工作于',
      LOCATED_IN: '位于',
      FOUNDED_BY: '创始人',
      PART_OF: '属于',
      RELATED_TO: '相关',
      MENTIONS: '提及'
    };
    return typeMap[type] || type;
  };

  // 过滤后的关系（前端搜索）
  const filteredRelations = relations.filter(relation => {
    if (!searchKeyword) return true;
    const keyword = searchKeyword.toLowerCase();
    return (
      (relation.source_entity && relation.source_entity.toLowerCase().includes(keyword)) ||
      (relation.target_entity && relation.target_entity.toLowerCase().includes(keyword)) ||
      (relation.relation_type && relation.relation_type.toLowerCase().includes(keyword))
    );
  });

  // 总页数
  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="document-relation-management">
      {/* 标题栏 */}
      <div className="drm-header">
        <h3>文档关系管理 <span className="relation-count">({totalCount})</span></h3>
        <div className="drm-actions">
          <button className="btn-refresh" onClick={loadRelations} title="刷新">
            <FiRefreshCw />
          </button>
          <button className="btn-add" onClick={() => {}} title="添加关系">
            <FiPlus /> 添加关系
          </button>
          {selectedRelations.length > 0 && (
            <button className="btn-batch-delete" onClick={handleBatchDelete} title="批量删除">
              <FiTrash2 /> 删除 ({selectedRelations.length})
            </button>
          )}
        </div>
      </div>

      {/* 工具栏 */}
      <div className="drm-toolbar">
        <div className="search-box">
          <FiSearch />
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="搜索关系..."
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch}>搜索</button>
        </div>

        <div className="filter-box">
          <FiFilter />
          <select value={relationTypeFilter} onChange={handleTypeFilterChange}>
            {getRelationTypes().map((type, index) => (
              <option key={`rel-type-${type}-${index}`} value={type}>
                {getRelationTypeLabel(type)}
              </option>
            ))}
          </select>
        </div>

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="pagination">
            <button
              className="page-btn"
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
            >
              首页
            </button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage(currentPage - 1)}
              disabled={currentPage === 1}
            >
              上一页
            </button>
            <span className="page-info">{currentPage}/{totalPages}</span>
            <button
              className="page-btn"
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              下一页
            </button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
            >
              末页
            </button>
          </div>
        )}
      </div>

      {/* 关系列表 */}
      {loading ? (
        <div className="loading">加载中...</div>
      ) : (
        <div className="drm-content">
          <table className="relation-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedRelations.length === relations.length && relations.length > 0}
                    onChange={handleSelectAll}
                  />
                </th>
                <th>源实体</th>
                <th>关系类型</th>
                <th>目标实体</th>
                <th>置信度</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredRelations.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-cell">
                    {searchKeyword ? '没有找到匹配的关系' : '暂无关系数据'}
                  </td>
                </tr>
              ) : (
                filteredRelations.map((relation) => (
                  <tr key={relation.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedRelations.includes(relation.id)}
                        onChange={() => handleSelectRelation(relation.id)}
                      />
                    </td>
                    <td className="entity-name">{relation.source_entity}</td>
                    <td>
                      <span className="relation-type-badge">
                        {getRelationTypeLabel(relation.relation_type)}
                      </span>
                    </td>
                    <td className="entity-name">{relation.target_entity}</td>
                    <td>
                      <div className="confidence-bar">
                        <div
                          className="confidence-fill"
                          style={{ width: `${(relation.confidence || 0) * 100}%` }}
                        />
                      </div>
                      <span className="confidence-value">{((relation.confidence || 0) * 100).toFixed(1)}%</span>
                    </td>
                    <td>
                      <button
                        className="action-btn edit"
                        onClick={() => {}}
                        title="编辑"
                      >
                        <FiEdit2 />
                      </button>
                      <button
                        className="action-btn delete"
                        onClick={() => handleDeleteRelation(relation.id)}
                        title="删除"
                      >
                        <FiTrash2 />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default DocumentRelationManagement;
