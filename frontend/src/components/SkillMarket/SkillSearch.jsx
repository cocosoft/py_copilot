import React, { useState, useCallback } from 'react';
import { debounce } from 'lodash';

/**
 * 技能搜索组件
 * 提供实时搜索和搜索建议功能
 */
const SkillSearch = ({ 
  searchQuery, 
  onSearchChange, 
  placeholder = "搜索技能...",
  className = '' 
}) => {
  const [localQuery, setLocalQuery] = useState(searchQuery);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  // 防抖搜索函数
  const debouncedSearch = useCallback(
    debounce((query) => {
      onSearchChange(query);
      
      // 模拟搜索建议（实际项目中应该从API获取）
      if (query.length > 1) {
        const mockSuggestions = [
          `${query} 数据分析`,
          `${query} 自动化`,
          `${query} 可视化`,
          `${query} 工具`
        ];
        setSuggestions(mockSuggestions);
        setShowSuggestions(true);
      } else {
        setShowSuggestions(false);
      }
    }, 300),
    [onSearchChange]
  );

  // 处理输入变化
  const handleInputChange = (e) => {
    const value = e.target.value;
    setLocalQuery(value);
    debouncedSearch(value);
  };

  // 处理建议选择
  const handleSuggestionClick = (suggestion) => {
    setLocalQuery(suggestion);
    onSearchChange(suggestion);
    setShowSuggestions(false);
  };

  // 清除搜索
  const handleClearSearch = () => {
    setLocalQuery('');
    onSearchChange('');
    setShowSuggestions(false);
  };

  // 处理键盘事件
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setShowSuggestions(false);
    } else if (e.key === 'Enter') {
      setShowSuggestions(false);
    }
  };

  return (
    <div className={`skill-search ${className}`}>
      <div className="skill-search__container">
        {/* 搜索图标 */}
        <div className="skill-search__icon">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
          </svg>
        </div>
        
        {/* 搜索输入框 */}
        <input
          type="text"
          className="skill-search__input"
          value={localQuery}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => localQuery.length > 1 && setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          placeholder={placeholder}
        />
        
        {/* 清除按钮 */}
        {localQuery && (
          <button 
            className="skill-search__clear"
            onClick={handleClearSearch}
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path fillRule="evenodd" d="M4.646 4.646a.5.5 0 01.708 0L8 7.293l2.646-2.647a.5.5 0 01.708.708L8.707 8l2.647 2.646a.5.5 0 01-.708.708L8 8.707l-2.646 2.647a.5.5 0 01-.708-.708L7.293 8 4.646 5.354a.5.5 0 010-.708z" clipRule="evenodd" />
            </svg>
          </button>
        )}
        
        {/* 搜索建议 */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="skill-search__suggestions">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="skill-search__suggestion"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path fillRule="evenodd" d="M12.5 7a5.5 5.5 0 11-11 0 5.5 5.5 0 0111 0zm-.524 5.924a6.5 6.5 0 111.048-1.095l3.2 3.2a.75.75 0 11-1.06 1.06l-3.188-3.165z" clipRule="evenodd" />
                </svg>
                <span>{suggestion}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* 搜索统计（可选） */}
      {localQuery && (
        <div className="skill-search__stats">
          搜索: "{localQuery}"
        </div>
      )}
    </div>
  );
};

export default SkillSearch;