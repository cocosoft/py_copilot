import React, { useState, useMemo } from 'react';
import { useSkills } from '../../hooks/useSkills';
import SkillCard from './SkillCard';
import SkillDetailModal from './SkillDetailModal';
import './SkillManagement.css';

function SkillList() {
  const { skills, loading, error, enableSkill, disableSkill } = useSkills();
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const allTags = useMemo(() => {
    const tags = new Set();
    skills?.forEach(skill => skill.tags?.forEach(t => tags.add(t)));
    return Array.from(tags).sort();
  }, [skills]);

  const filteredSkills = useMemo(() => {
    return skills?.filter(skill => {
      const matchesSearch = 
        skill.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        skill.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTag = !selectedTag || skill.tags?.includes(selectedTag);
      return matchesSearch && matchesTag;
    }) || [];
  }, [skills, searchTerm, selectedTag]);

  const handleViewSkill = (skill) => {
    setSelectedSkill(skill);
    setShowDetail(true);
  };

  const handleCloseDetail = () => {
    setShowDetail(false);
    setSelectedSkill(null);
  };

  const handleToggleEnable = async (skill) => {
    if (skill.status === 'enabled') {
      await disableSkill(skill.id);
    } else {
      await enableSkill(skill.id);
    }
  };

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
      <div className="skill-list-header">
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

      <div className={`skill-list-content ${viewMode}`}>
        {filteredSkills.length === 0 ? (
          <div className="skill-list-empty">
            <p>没有找到匹配的技能</p>
          </div>
        ) : (
          filteredSkills.map(skill => (
            <SkillCard
              key={skill.id}
              skill={skill}
              viewMode={viewMode}
              onView={() => handleViewSkill(skill)}
              onToggleEnable={() => handleToggleEnable(skill)}
            />
          ))
        )}
      </div>

      {showDetail && selectedSkill && (
        <SkillDetailModal
          skill={selectedSkill}
          onClose={handleCloseDetail}
          onToggleEnable={() => handleToggleEnable(selectedSkill)}
        />
      )}
    </div>
  );
}

export default SkillList;
