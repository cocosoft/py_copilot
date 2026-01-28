import React, { useState, useEffect } from 'react';
import SkillCard from './SkillCard';
import SkillFilters from './SkillFilters';
import SkillSearch from './SkillSearch';
import SkillDetails from './SkillDetails';
import useSkillMarket from '../../hooks/useSkillMarket';
import './SkillMarket.css';

/**
 * 技能市场主组件
 * 提供技能发现、搜索、筛选和安装功能
 */
const SkillMarket = () => {
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(12);

  // 使用技能市场Hook
  const {
    skills,
    filteredSkills,
    categories,
    isLoading,
    error,
    searchQuery,
    setSearchQuery,
    filters,
    setFilters,
    sortBy,
    setSortBy,
    installSkill,
    uninstallSkill,
    refreshSkills
  } = useSkillMarket();

  // 计算分页数据
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredSkills.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredSkills.length / itemsPerPage);

  // 处理技能选择
  const handleSkillSelect = (skill) => {
    setSelectedSkill(skill);
  };

  // 处理技能安装
  const handleInstallSkill = async (skillId) => {
    try {
      await installSkill(skillId);
      // 安装成功后刷新技能列表
      await refreshSkills();
    } catch (error) {
      console.error('安装技能失败:', error);
    }
  };

  // 处理技能卸载
  const handleUninstallSkill = async (skillId) => {
    try {
      await uninstallSkill(skillId);
      // 卸载成功后刷新技能列表
      await refreshSkills();
    } catch (error) {
      console.error('卸载技能失败:', error);
    }
  };

  // 处理分页变化
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 渲染加载状态
  if (isLoading && skills.length === 0) {
    return (
      <div className="skill-market skill-market--loading">
        <div className="skill-market__loading">
          <div className="skill-market__loading-spinner"></div>
          <p>正在加载技能市场...</p>
        </div>
      </div>
    );
  }

  // 渲染错误状态
  if (error && skills.length === 0) {
    return (
      <div className="skill-market skill-market--error">
        <div className="skill-market__error">
          <h3>加载技能市场失败</h3>
          <p>{error.message}</p>
          <button 
            className="skill-market__retry-button"
            onClick={refreshSkills}
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="skill-market">
      {/* 头部区域 */}
      <div className="skill-market__header">
        <div className="skill-market__header-content">
          <h1 className="skill-market__title">技能市场</h1>
          <p className="skill-market__subtitle">
            发现和安装强大的AI技能来扩展你的助手能力
          </p>
        </div>
        
        <div className="skill-market__header-actions">
          <button 
            className="skill-market__refresh-button"
            onClick={refreshSkills}
            disabled={isLoading}
          >
            {isLoading ? '刷新中...' : '刷新技能'}
          </button>
          
          <div className="skill-market__view-controls">
            <button 
              className={`skill-market__view-button ${viewMode === 'grid' ? 'skill-market__view-button--active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="网格视图"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <rect x="1" y="1" width="6" height="6" rx="1"/>
                <rect x="9" y="1" width="6" height="6" rx="1"/>
                <rect x="1" y="9" width="6" height="6" rx="1"/>
                <rect x="9" y="9" width="6" height="6" rx="1"/>
              </svg>
            </button>
            <button 
              className={`skill-market__view-button ${viewMode === 'list' ? 'skill-market__view-button--active' : ''}`}
              onClick={() => setViewMode('list')}
              title="列表视图"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <rect x="1" y="1" width="14" height="2" rx="1"/>
                <rect x="1" y="7" width="14" height="2" rx="1"/>
                <rect x="1" y="13" width="14" height="2" rx="1"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* 搜索和筛选区域 */}
      <div className="skill-market__controls">
        <SkillSearch
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          placeholder="搜索技能名称、描述或标签..."
        />
        
        <SkillFilters
          categories={categories}
          filters={filters}
          onFiltersChange={setFilters}
          sortBy={sortBy}
          onSortChange={setSortBy}
          totalSkills={filteredSkills.length}
        />
      </div>

      {/* 主要内容区域 */}
      <div className="skill-market__content">
        {/* 技能列表 */}
        <div className="skill-market__main">
          {filteredSkills.length === 0 ? (
            <div className="skill-market__empty">
              <div className="skill-market__empty-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="currentColor">
                  <path d="M32 12c-11.05 0-20 8.95-20 20s8.95 20 20 20 20-8.95 20-20-8.95-20-20-20zm0 36c-8.82 0-16-7.18-16-16s7.18-16 16-16 16 7.18 16 16-7.18 16-16 16z"/>
                  <path d="M32 24c-4.42 0-8 3.58-8 8s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zm0 12c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z"/>
                </svg>
              </div>
              <h3>未找到匹配的技能</h3>
              <p>尝试调整搜索条件或筛选器</p>
              <button 
                className="skill-market__reset-filters"
                onClick={() => {
                  setSearchQuery('');
                  setFilters({});
                  setSortBy('popularity');
                }}
              >
                重置所有筛选条件
              </button>
            </div>
          ) : (
            <>
              {/* 技能网格/列表 */}
              <div className={`skill-market__skills skill-market__skills--${viewMode}`}>
                {currentItems.map(skill => (
                  <SkillCard
                    key={skill.id}
                    skill={skill}
                    viewMode={viewMode}
                    onSelect={handleSkillSelect}
                    onInstall={handleInstallSkill}
                    onUninstall={handleUninstallSkill}
                  />
                ))}
              </div>

              {/* 分页控件 */}
              {totalPages > 1 && (
                <div className="skill-market__pagination">
                  <button 
                    className="skill-market__pagination-button"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    上一页
                  </button>
                  
                  <div className="skill-market__pagination-pages">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                      <button
                        key={page}
                        className={`skill-market__pagination-page ${currentPage === page ? 'skill-market__pagination-page--active' : ''}`}
                        onClick={() => handlePageChange(page)}
                      >
                        {page}
                      </button>
                    ))}
                  </div>
                  
                  <button 
                    className="skill-market__pagination-button"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    下一页
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* 技能详情面板 */}
        {selectedSkill && (
          <div className="skill-market__details">
            <SkillDetails
              skill={selectedSkill}
              onClose={() => setSelectedSkill(null)}
              onInstall={handleInstallSkill}
              onUninstall={handleUninstallSkill}
            />
          </div>
        )}
      </div>

      {/* 统计信息 */}
      <div className="skill-market__stats">
        <div className="skill-market__stats-item">
          <span className="skill-market__stats-label">总技能数</span>
          <span className="skill-market__stats-value">{skills.length}</span>
        </div>
        <div className="skill-market__stats-item">
          <span className="skill-market__stats-label">已安装</span>
          <span className="skill-market__stats-value">
            {skills.filter(s => s.installed).length}
          </span>
        </div>
        <div className="skill-market__stats-item">
          <span className="skill-market__stats-label">匹配结果</span>
          <span className="skill-market__stats-value">{filteredSkills.length}</span>
        </div>
      </div>
    </div>
  );
};

export default SkillMarket;