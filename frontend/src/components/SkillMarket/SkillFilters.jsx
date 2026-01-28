import React, { useState } from 'react';

/**
 * 技能筛选组件
 * 提供分类筛选、排序和高级筛选功能
 */
const SkillFilters = ({
  categories = [],
  filters = {},
  onFiltersChange,
  sortBy = 'popularity',
  onSortChange,
  totalSkills = 0,
  className = ''
}) => {
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // 排序选项
  const sortOptions = [
    { value: 'popularity', label: '热门程度' },
    { value: 'rating', label: '评分最高' },
    { value: 'downloads', label: '下载最多' },
    { value: 'recent', label: '最近更新' },
    { value: 'name', label: '名称排序' }
  ];

  // 处理分类筛选变化
  const handleCategoryChange = (category) => {
    const newFilters = { ...filters };
    
    if (newFilters.categories?.includes(category)) {
      newFilters.categories = newFilters.categories.filter(c => c !== category);
    } else {
      newFilters.categories = [...(newFilters.categories || []), category];
    }
    
    onFiltersChange(newFilters);
  };

  // 处理安装状态筛选
  const handleInstallStatusChange = (status) => {
    const newFilters = { ...filters };
    
    if (status === 'all') {
      delete newFilters.installed;
    } else {
      newFilters.installed = status === 'installed';
    }
    
    onFiltersChange(newFilters);
  };

  // 处理评分筛选
  const handleRatingChange = (minRating) => {
    const newFilters = { ...filters };
    
    if (minRating === 0) {
      delete newFilters.minRating;
    } else {
      newFilters.minRating = minRating;
    }
    
    onFiltersChange(newFilters);
  };

  // 处理排序变化
  const handleSortChange = (e) => {
    onSortChange(e.target.value);
  };

  // 清除所有筛选
  const handleClearFilters = () => {
    onFiltersChange({});
    onSortChange('popularity');
  };

  // 获取当前筛选状态摘要
  const getFilterSummary = () => {
    const activeFilters = [];
    
    if (filters.categories?.length > 0) {
      activeFilters.push(`${filters.categories.length} 个分类`);
    }
    
    if (filters.installed !== undefined) {
      activeFilters.push(filters.installed ? '已安装' : '未安装');
    }
    
    if (filters.minRating) {
      activeFilters.push(`评分 ≥ ${filters.minRating}`);
    }
    
    return activeFilters.length > 0 ? activeFilters.join(' • ') : '无筛选条件';
  };

  return (
    <div className={`skill-filters ${className}`}>
      <div className="skill-filters__header">
        <div className="skill-filters__summary">
          <span className="skill-filters__count">{totalSkills} 个技能</span>
          <span className="skill-filters__status">{getFilterSummary()}</span>
        </div>
        
        <div className="skill-filters__controls">
          {/* 排序选择 */}
          <div className="skill-filters__sort">
            <label htmlFor="skill-sort" className="skill-filters__sort-label">
              排序方式:
            </label>
            <select
              id="skill-sort"
              className="skill-filters__sort-select"
              value={sortBy}
              onChange={handleSortChange}
            >
              {sortOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* 高级筛选切换 */}
          <button
            className={`skill-filters__toggle ${showAdvancedFilters ? 'skill-filters__toggle--active' : ''}`}
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M6 10.5a.5.5 0 01.5-.5h3a.5.5 0 010 1h-3a.5.5 0 01-.5-.5zM3.5 8a.5.5 0 000 1h9a.5.5 0 000-1h-9zM2 5.5a.5.5 0 01.5-.5h11a.5.5 0 010 1h-11a.5.5 0 01-.5-.5z"/>
            </svg>
            筛选
          </button>

          {/* 清除筛选 */}
          {(filters.categories?.length > 0 || filters.installed !== undefined || filters.minRating) && (
            <button
              className="skill-filters__clear"
              onClick={handleClearFilters}
            >
              清除筛选
            </button>
          )}
        </div>
      </div>

      {/* 高级筛选面板 */}
      {showAdvancedFilters && (
        <div className="skill-filters__panel">
          {/* 分类筛选 */}
          <div className="skill-filters__section">
            <h4 className="skill-filters__section-title">分类</h4>
            <div className="skill-filters__categories">
              {categories.map(category => (
                <label key={category} className="skill-filters__category">
                  <input
                    type="checkbox"
                    checked={filters.categories?.includes(category) || false}
                    onChange={() => handleCategoryChange(category)}
                  />
                  <span className="skill-filters__category-label">{category}</span>
                  <span className="skill-filters__category-count">
                    {/* 这里应该显示每个分类的技能数量 */}
                    {/* 实际项目中应该从props传递 */}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* 安装状态筛选 */}
          <div className="skill-filters__section">
            <h4 className="skill-filters__section-title">安装状态</h4>
            <div className="skill-filters__install-status">
              <label className="skill-filters__radio">
                <input
                  type="radio"
                  name="install-status"
                  value="all"
                  checked={filters.installed === undefined}
                  onChange={() => handleInstallStatusChange('all')}
                />
                <span>全部技能</span>
              </label>
              <label className="skill-filters__radio">
                <input
                  type="radio"
                  name="install-status"
                  value="installed"
                  checked={filters.installed === true}
                  onChange={() => handleInstallStatusChange('installed')}
                />
                <span>已安装</span>
              </label>
              <label className="skill-filters__radio">
                <input
                  type="radio"
                  name="install-status"
                  value="not-installed"
                  checked={filters.installed === false}
                  onChange={() => handleInstallStatusChange('not-installed')}
                />
                <span>未安装</span>
              </label>
            </div>
          </div>

          {/* 评分筛选 */}
          <div className="skill-filters__section">
            <h4 className="skill-filters__section-title">最低评分</h4>
            <div className="skill-filters__ratings">
              {[0, 3, 4, 4.5].map(rating => (
                <label key={rating} className="skill-filters__rating">
                  <input
                    type="radio"
                    name="min-rating"
                    value={rating}
                    checked={filters.minRating === rating}
                    onChange={() => handleRatingChange(rating)}
                  />
                  <span className="skill-filters__rating-stars">
                    {Array.from({ length: 5 }, (_, i) => (
                      <span
                        key={i}
                        className={`skill-filters__rating-star ${i < rating ? 'skill-filters__rating-star--active' : ''}`}
                      >
                        ★
                      </span>
                    ))}
                  </span>
                  <span className="skill-filters__rating-label">
                    {rating === 0 ? '全部' : `${rating}+`}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* 其他筛选选项可以在这里添加 */}
          <div className="skill-filters__section">
            <h4 className="skill-filters__section-title">更多选项</h4>
            <div className="skill-filters__advanced">
              <label className="skill-filters__checkbox">
                <input
                  type="checkbox"
                  checked={filters.official || false}
                  onChange={(e) => onFiltersChange({
                    ...filters,
                    official: e.target.checked
                  })}
                />
                <span>仅显示官方技能</span>
              </label>
              
              <label className="skill-filters__checkbox">
                <input
                  type="checkbox"
                  checked={filters.recentlyUpdated || false}
                  onChange={(e) => onFiltersChange({
                    ...filters,
                    recentlyUpdated: e.target.checked
                  })}
                />
                <span>最近30天更新</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* 当前激活的筛选标签 */}
      {(filters.categories?.length > 0 || filters.installed !== undefined || filters.minRating) && (
        <div className="skill-filters__active-tags">
          {/* 分类标签 */}
          {filters.categories?.map(category => (
            <span key={category} className="skill-filters__active-tag">
              {category}
              <button
                onClick={() => handleCategoryChange(category)}
                className="skill-filters__active-tag-remove"
              >
                ×
              </button>
            </span>
          ))}
          
          {/* 安装状态标签 */}
          {filters.installed !== undefined && (
            <span className="skill-filters__active-tag">
              {filters.installed ? '已安装' : '未安装'}
              <button
                onClick={() => handleInstallStatusChange('all')}
                className="skill-filters__active-tag-remove"
              >
                ×
              </button>
            </span>
          )}
          
          {/* 评分标签 */}
          {filters.minRating && (
            <span className="skill-filters__active-tag">
              评分 ≥ {filters.minRating}
              <button
                onClick={() => handleRatingChange(0)}
                className="skill-filters__active-tag-remove"
              >
                ×
              </button>
            </span>
          )}
          
          {/* 官方技能标签 */}
          {filters.official && (
            <span className="skill-filters__active-tag">
              官方技能
              <button
                onClick={() => onFiltersChange({ ...filters, official: false })}
                className="skill-filters__active-tag-remove"
              >
                ×
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default SkillFilters;