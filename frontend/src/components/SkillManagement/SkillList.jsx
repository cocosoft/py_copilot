import React, { useState, useMemo, useRef, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useSkills } from '../../hooks/useSkills';
import { skillApi } from '../../services/skillApi';
import SkillCard from './SkillCard';
import SkillDetailModal from './SkillDetailModal';
import SkillFormModal from './SkillFormModal';
import SkillExecutionModal from './SkillExecutionModal';
import SkillMatchModal from './SkillMatchModal';
import './SkillManagement.css';

function SkillList() {
  const { skills, loading, error, enableSkill, disableSkill, deleteSkill, refetch: fetchSkills } = useSkills();
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingSkill, setEditingSkill] = useState(null);
  const [showExecution, setShowExecution] = useState(false);
  const [executionSkill, setExecutionSkill] = useState(null);
  const [operationResult, setOperationResult] = useState({ type: '', message: '' });
  const [showMatch, setShowMatch] = useState(false);
  // 批量操作相关状态
  const [selectedSkills, setSelectedSkills] = useState(new Set());
  const [showBatchActions, setShowBatchActions] = useState(false);

  const allTags = useMemo(() => {
    const tags = new Set();
    skills?.forEach(skill => skill.tags?.forEach(t => tags.add(t)));
    return Array.from(tags).sort();
  }, [skills]);



  const handleViewSkill = (skill) => {
    setSelectedSkill(skill);
    setShowDetail(true);
  };

  const handleCloseDetail = () => {
    setShowDetail(false);
    setSelectedSkill(null);
  };

  const handleToggleEnable = async (skill) => {
    try {
      if (skill.status === 'enabled') {
        await disableSkill(skill.id);
        setOperationResult({ type: 'success', message: `技能 "${skill.name}" 已禁用` });
      } else {
        await enableSkill(skill.id);
        setOperationResult({ type: 'success', message: `技能 "${skill.name}" 已启用` });
      }
    } catch (error) {
      setOperationResult({ type: 'error', message: `操作失败: ${error.message}` });
    }
    // 3秒后自动隐藏结果消息
    setTimeout(() => setOperationResult({ type: '', message: '' }), 3000);
  };

  const handleCreateSkill = () => {
    setEditingSkill(null);
    setShowForm(true);
  };

  const handleOpenMatchModal = () => {
    setShowMatch(true);
  };

  const handleEditSkill = (skill) => {
    setEditingSkill(skill);
    setShowForm(true);
  };

  const handleFormSubmit = async (skillData) => {
    try {
      if (editingSkill) {
        await skillApi.update(editingSkill.id, skillData);
      } else {
        await skillApi.create(skillData);
      }
      await fetchSkills();
    } catch (err) {
      console.error('Failed to save skill:', err);
      throw err;
    }
  };

  const handleDeleteSkill = async (skill) => {
    if (window.confirm(`确定要删除技能 "${skill.name}" 吗？此操作不可恢复。`)) {
      try {
        await deleteSkill(skill.id);
        // deleteSkill函数已经在前端更新了技能列表，无需再次请求
        setOperationResult({ type: 'success', message: `技能 "${skill.name}" 已删除` });
      } catch (err) {
        console.error('Failed to delete skill:', err);
        setOperationResult({ type: 'error', message: `删除失败: ${err.message}` });
      }
      // 3秒后自动隐藏结果消息
      setTimeout(() => setOperationResult({ type: '', message: '' }), 3000);
    }
  };

  const handleExecuteSkill = (skill) => {
    setExecutionSkill(skill);
    setShowExecution(true);
  };
  
  // 批量操作相关函数
  const handleSelectSkill = (skillId, isSelected) => {
    const newSelected = new Set(selectedSkills);
    if (isSelected) {
      newSelected.add(skillId);
    } else {
      newSelected.delete(skillId);
    }
    setSelectedSkills(newSelected);
    setShowBatchActions(newSelected.size > 0);
  };
  
  const handleSelectAll = () => {
    if (selectedSkills.size === filteredSkills.length) {
      // 如果已经全选，则取消全选
      setSelectedSkills(new Set());
      setShowBatchActions(false);
    } else {
      // 全选所有可见技能
      const allVisibleSkillIds = new Set(filteredSkills.map(skill => skill.id));
      setSelectedSkills(allVisibleSkillIds);
      setShowBatchActions(true);
    }
  };
  
  const handleBatchEnable = async () => {
    try {
      for (const skillId of selectedSkills) {
        await enableSkill(skillId);
      }
      setOperationResult({ type: 'success', message: `已批量启用 ${selectedSkills.size} 个技能` });
      setSelectedSkills(new Set());
      setShowBatchActions(false);
    } catch (err) {
      setOperationResult({ type: 'error', message: `批量启用失败: ${err.message}` });
    }
    setTimeout(() => setOperationResult({ type: '', message: '' }), 3000);
  };
  
  const handleBatchDisable = async () => {
    try {
      for (const skillId of selectedSkills) {
        await disableSkill(skillId);
      }
      setOperationResult({ type: 'success', message: `已批量禁用 ${selectedSkills.size} 个技能` });
      setSelectedSkills(new Set());
      setShowBatchActions(false);
    } catch (err) {
      setOperationResult({ type: 'error', message: `批量禁用失败: ${err.message}` });
    }
    setTimeout(() => setOperationResult({ type: '', message: '' }), 3000);
  };
  
  const handleBatchDelete = async () => {
    if (window.confirm(`确定要删除选中的 ${selectedSkills.size} 个技能吗？此操作不可恢复。`)) {
      try {
        for (const skillId of selectedSkills) {
          await deleteSkill(skillId);
        }
        setOperationResult({ type: 'success', message: `已批量删除 ${selectedSkills.size} 个技能` });
        setSelectedSkills(new Set());
        setShowBatchActions(false);
      } catch (err) {
        setOperationResult({ type: 'error', message: `批量删除失败: ${err.message}` });
      }
      setTimeout(() => setOperationResult({ type: '', message: '' }), 3000);
    }
  };

  const handleExecutionComplete = async () => {
    await fetchSkills();
  };

  // 虚拟滚动相关
  const parentRef = useRef(null);
  
  // 根据视图模式计算卡片尺寸
  const cardSize = useMemo(() => {
    if (viewMode === 'grid') {
      return { width: 320, height: 280 }; // 网格视图卡片尺寸
    } else {
      return { width: '100%', height: 80 }; // 列表视图卡片高度
    }
  }, [viewMode]);
  
  // 优化后的filteredSkills计算
  const filteredSkills = useMemo(() => {
    if (!skills) return [];
    
    const searchLower = searchTerm.toLowerCase();
    return skills.filter(skill => {
      const matchesSearch = searchLower
        ? skill.name.toLowerCase().includes(searchLower) ||
          skill.description.toLowerCase().includes(searchLower)
        : true;
      const matchesTag = !selectedTag || skill.tags?.includes(selectedTag);
      return matchesSearch && matchesTag;
    });
  }, [skills, searchTerm, selectedTag]);
  
  // 虚拟滚动实现 - 针对列表视图
  const listVirtualizer = useVirtualizer({
    count: filteredSkills.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 5,
  });

  // 渲染虚拟卡片
  const renderVirtualCard = useCallback((index) => {
    const skill = filteredSkills[index];
    return (
      <SkillCard
        key={skill.id}
        skill={skill}
        viewMode={viewMode}
        onView={() => handleViewSkill(skill)}
        onToggleEnable={() => handleToggleEnable(skill)}
        onEdit={() => handleEditSkill(skill)}
        onDelete={() => handleDeleteSkill(skill)}
        onExecute={() => handleExecuteSkill(skill)}
        onSelect={handleSelectSkill}
        isSelected={selectedSkills.has(skill.id)}
      />
    );
  }, [filteredSkills, viewMode, handleViewSkill, handleToggleEnable, handleEditSkill, handleDeleteSkill, handleExecuteSkill, handleSelectSkill, selectedSkills]);

  if (loading) {
    return (
      <div className="skill-list-loading">
        <div className="loading-spinner"></div>
        <p>加载技能中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="skill-list-error">
        <p>加载技能失败: {error}</p>
        <button onClick={() => window.location.reload()}>重试</button>
      </div>
    );
  }

  return (
    <div className="skill-list">
      {operationResult.message && (
        <div className={`operation-result ${operationResult.type}`}>
          {operationResult.message}
        </div>
      )}
      
      {showBatchActions && (
        <div className="batch-actions-bar">
          <div className="batch-select-all">
            <input
              type="checkbox"
              checked={selectedSkills.size === filteredSkills.length && filteredSkills.length > 0}
              onChange={handleSelectAll}
            />
            <span>全选</span>
          </div>
          <div className="batch-info">
            已选择 {selectedSkills.size} 个技能
          </div>
          <div className="batch-actions">
            <button className="batch-btn batch-enable" onClick={handleBatchEnable}>
              批量启用
            </button>
            <button className="batch-btn batch-disable" onClick={handleBatchDisable}>
              批量禁用
            </button>
            <button className="batch-btn batch-delete" onClick={handleBatchDelete}>
              批量删除
            </button>
          </div>
        </div>
      )}
      
      <div className="skill-list-header">
        <div className="skill-header-left">
          <div className="skill-search">
            <input
              type="text"
              placeholder="搜索技能..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="skill-search-input"
            />
          </div>

          <div className="skill-filter">
            <select
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
              className="skill-filter-select"
            >
              <option value="">所有标签</option>
              {allTags.map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="skill-header-right">
          <button
            className="create-skill-btn"
            onClick={handleCreateSkill}
            title="创建新技能"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" style={{ marginRight: '8px' }}>
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/>
            </svg>
            创建技能
          </button>
          
          <button
            className="match-skill-btn"
            onClick={handleOpenMatchModal}
            title="技能匹配"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" style={{ marginRight: '8px' }}>
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>
            </svg>
            技能匹配
          </button>
          
          <div className="skill-view-toggle">
            <button
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="网格视图"
            >
              <svg viewBox="0 0 24 24" width="20" height="20">
                <rect x="3" y="3" width="7" height="7" fill="currentColor"/>
                <rect x="14" y="3" width="7" height="7" fill="currentColor"/>
                <rect x="3" y="14" width="7" height="7" fill="currentColor"/>
                <rect x="14" y="14" width="7" height="7" fill="currentColor"/>
              </svg>
            </button>
            <button
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
              title="列表视图"
            >
              <svg viewBox="0 0 24 24" width="20" height="20">
                <rect x="3" y="4" width="18" height="4" fill="currentColor"/>
                <rect x="3" y="10" width="18" height="4" fill="currentColor"/>
                <rect x="3" y="16" width="18" height="4" fill="currentColor"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      {allTags.length > 0 && (
        <div className="skill-tags">
          <button
            className={`tag-chip ${!selectedTag ? 'active' : ''}`}
            onClick={() => setSelectedTag('')}
          >
            全部
          </button>
          {allTags.map(tag => (
            <button
              key={tag}
              className={`tag-chip ${selectedTag === tag ? 'active' : ''}`}
              onClick={() => setSelectedTag(tag === selectedTag ? '' : tag)}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      <div 
        className={`skill-list-content ${viewMode}`}
        ref={parentRef}
        style={{
          height: 'calc(100vh - 300px)',
          overflow: 'auto',
        }}
      >
        {filteredSkills.length === 0 ? (
          <div className="skill-list-empty">
            <p>没有找到匹配的技能</p>
          </div>
        ) : viewMode === 'list' ? (
          // 列表视图使用虚拟滚动
          <div
            style={{
              height: `${listVirtualizer.getTotalSize()}px`,
              position: 'relative',
            }}
          >
            {listVirtualizer.getVirtualItems().map(virtualItem => (
              <div
                key={filteredSkills[virtualItem.index].id}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualItem.size}px`,
                  transform: `translateY(${virtualItem.start}px)`,
                }}
              >
                {renderVirtualCard(virtualItem.index)}
              </div>
            ))}
          </div>
        ) : (
          // 网格视图使用传统渲染，但优化filteredSkills计算
          filteredSkills.map((skill, index) => renderVirtualCard(index))
        )}
      </div>

      {showDetail && selectedSkill && (
        <SkillDetailModal
          skill={selectedSkill}
          onClose={handleCloseDetail}
          onToggleEnable={() => handleToggleEnable(selectedSkill)}
        />
      )}
      
      {showForm && (
        <SkillFormModal
          skill={editingSkill}
          onClose={() => setShowForm(false)}
          onSubmit={handleFormSubmit}
        />
      )}
      
      {showExecution && executionSkill && (
        <SkillExecutionModal
          skill={executionSkill}
          onClose={() => setShowExecution(false)}
          onExecutionComplete={handleExecutionComplete}
        />
      )}
      
      {showMatch && (
        <SkillMatchModal
          onClose={() => setShowMatch(false)}
        />
      )}
    </div>
  );
}

export default SkillList;
