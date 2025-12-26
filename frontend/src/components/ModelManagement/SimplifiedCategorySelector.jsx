import React, { useState, useEffect } from 'react';

const SimplifiedCategorySelector = ({ 
  dimensions, 
  categoriesByDimension, 
  onSelectionChange,
  initialSelections = {}
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDimension, setSelectedDimension] = useState('');
  const [selectedCategories, setSelectedCategories] = useState(initialSelections);
  const [showAllDimensions, setShowAllDimensions] = useState(false);

  // 过滤后的分类列表
  const filteredCategories = React.useMemo(() => {
    if (!selectedDimension) {
      // 如果没有选择维度，显示所有分类
      const allCategories = [];
      Object.entries(categoriesByDimension).forEach(([dimension, categories]) => {
        categories.forEach(category => {
          allCategories.push({
            ...category,
            dimension
          });
        });
      });
      
      return allCategories.filter(category => 
        category.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        category.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // 如果选择了维度，只显示该维度的分类
    const categories = categoriesByDimension[selectedDimension] || [];
    return categories.filter(category => 
      category.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      category.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [selectedDimension, categoriesByDimension, searchQuery]);

  // 常用分类列表（按使用频率排序）
  const popularCategories = React.useMemo(() => {
    const allCategories = [];
    Object.entries(categoriesByDimension).forEach(([dimension, categories]) => {
      categories.forEach(category => {
        allCategories.push({
          ...category,
          dimension
        });
      });
    });
    
    // 这里可以根据实际使用频率排序，暂时按名称排序
    return allCategories
      .filter(category => category.name.length < 20) // 过滤掉过长的名称
      .slice(0, 8); // 显示前8个常用分类
  }, [categoriesByDimension]);

  // 处理分类选择
  const handleCategorySelect = (dimension, categoryId, categoryName) => {
    const newSelections = {
      ...selectedCategories,
      [dimension]: {
        categoryId,
        categoryName
      }
    };
    
    setSelectedCategories(newSelections);
    onSelectionChange(newSelections);
  };

  // 处理分类移除
  const handleCategoryRemove = (dimension) => {
    const newSelections = { ...selectedCategories };
    delete newSelections[dimension];
    
    setSelectedCategories(newSelections);
    onSelectionChange(newSelections);
  };

  // 重置选择
  const handleReset = () => {
    setSelectedCategories({});
    setSelectedDimension('');
    setSearchQuery('');
    onSelectionChange({});
  };

  return (
    <div className="simplified-category-selector">
      {/* 搜索和筛选区域 */}
      <div className="selector-header">
        <div className="search-section">
          <input
            type="text"
            placeholder="搜索分类..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          
          <div className="dimension-filters">
            <label>
              <input
                type="checkbox"
                checked={showAllDimensions}
                onChange={(e) => setShowAllDimensions(e.target.checked)}
              />
              显示所有维度
            </label>
            
            {!showAllDimensions && (
              <select 
                value={selectedDimension} 
                onChange={(e) => setSelectedDimension(e.target.value)}
                className="dimension-select"
              >
                <option value="">所有维度</option>
                {Array.isArray(dimensions) && dimensions.length > 0 ? (
                  dimensions.map(dimension => {
                    // 维度显示名称映射
                    const dimensionDisplayNames = {
                      'tasks': '任务维度',
                      'languages': '语言维度',
                      'licenses': '协议维度',
                      'technologies': '技术维度'
                    };
                    const displayName = dimensionDisplayNames[dimension] || dimension;
                    return (
                      <option key={dimension} value={dimension}>
                        {displayName}
                      </option>
                    );
                  })
                ) : (
                  <option value="">暂无维度数据</option>
                )}
              </select>
            )}
          </div>
        </div>
      </div>

      {/* 已选分类显示 */}
      {Object.keys(selectedCategories).length > 0 && (
        <div className="selected-categories">
          <h4>已选择的分类:</h4>
          <div className="selected-list">
            {Object.entries(selectedCategories).map(([dimension, selection]) => (
              <div key={dimension} className="selected-item">
                <span className="dimension-badge">{dimension}</span>
                <span className="category-name">{selection.categoryName}</span>
                <button 
                  type="button"
                  onClick={() => handleCategoryRemove(dimension)}
                  className="remove-btn"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          <button type="button" onClick={handleReset} className="reset-btn">
            重置选择
          </button>
        </div>
      )}

      {/* 常用分类快捷选择 */}
      {searchQuery === '' && Object.keys(selectedCategories).length === 0 && (
        <div className="popular-categories">
          <h4>常用分类</h4>
          <div className="popular-list">
            {popularCategories.map(category => (
              <button
                key={`${category.dimension}-${category.id}`}
                type="button"
                onClick={() => handleCategorySelect(category.dimension, category.id, category.display_name || category.name)}
                className="popular-item"
              >
                <span className="dimension-tag">{category.dimension}</span>
                <span className="category-name">{category.display_name || category.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 分类列表 */}
      <div className="category-list">
        {filteredCategories.length > 0 ? (
          <div className="categories-grid">
            {filteredCategories.map(category => {
              const dimension = selectedDimension || category.dimension;
              const isSelected = selectedCategories[dimension]?.categoryId === category.id;
              
              return (
                <div 
                  key={`${dimension}-${category.id}`}
                  className={`category-item ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleCategorySelect(dimension, category.id, category.display_name || category.name)}
                >
                  <div className="category-header">
                    <span className="dimension-label">{dimension}</span>
                    {isSelected && <span className="selected-indicator">✓</span>}
                  </div>
                  <div className="category-name">
                    {category.display_name || category.name}
                  </div>
                  {category.description && (
                    <div className="category-description">
                      {category.description}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="no-results">
            没有找到匹配的分类
          </div>
        )}
      </div>

      {/* 统计信息 */}
      <div className="selection-stats">
        已选择 {Object.keys(selectedCategories).length} 个维度，共 {filteredCategories.length} 个分类可用
      </div>
    </div>
  );
};

export default SimplifiedCategorySelector;