import React, { useState } from 'react';
import './SearchModal.css';

const SearchModal = ({ isOpen, onClose, onSearchSubmit, searchResults, isSearching, onAddToChat }) => {
  const [query, setQuery] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearchSubmit(query);
    }
  };

  return (
    <div className="search-modal-overlay">
      <div className="search-modal">
        <div className="search-modal-header">
          <h3>联网搜索</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <form className="search-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="输入搜索关键词..."
            className="search-input"
          />
          <button type="submit" className="search-btn" disabled={isSearching}>
            {isSearching ? '搜索中...' : '搜索'}
          </button>
        </form>
        <div className="search-results">
          {isSearching ? (
            <div className="search-loading">搜索中...</div>
          ) : searchResults.length > 0 ? (
            searchResults.map((result, index) => (
              <div key={result.id} className="search-result-item">
                <h4>{result.title}</h4>
                <p>{result.content}</p>
                <a href={result.url} target="_blank" rel="noopener noreferrer">{result.url}</a>
                <button className="add-to-chat-btn" onClick={() => onAddToChat(result)}>
                  添加到对话
                </button>
              </div>
            ))
          ) : (
            <div className="no-results">暂无搜索结果</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchModal;