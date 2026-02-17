import React, { memo, useCallback } from 'react';
import './TopicItem.css';

const TopicItem = memo(({ topic, isActive, onClick, onDelete }) => {
  const formatDate = useCallback((dateString) => {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) {
      return '刚刚';
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)} 分钟前`;
    } else if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)} 小时前`;
    } else if (diff < 604800000) {
      return `${Math.floor(diff / 86400000)} 天前`;
    } else {
      return date.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit'
      });
    }
  }, []);

  const handleClick = useCallback(() => {
    onClick();
  }, [onClick]);

  const handleDelete = useCallback((e) => {
    e.stopPropagation();
    onDelete();
  }, [onDelete]);

  return (
    <div 
      className={`topic-item ${isActive ? 'topic-item-active' : ''}`}
      onClick={handleClick}
    >
      <div className="topic-item-content">
        <div className="topic-item-header">
          <span className="topic-item-name">{topic.topic_name}</span>
          {isActive && <span className="topic-item-badge">活跃</span>}
        </div>
        
        {topic.topic_summary && (
          <div className="topic-item-summary">
            {topic.topic_summary}
          </div>
        )}
        
        <div className="topic-item-footer">
          <span className="topic-item-count">
            {topic.message_count} 条消息
          </span>
          <span className="topic-item-date">
            {formatDate(topic.created_at)}
          </span>
        </div>
      </div>
      
      <button 
        className="topic-item-delete"
        onClick={handleDelete}
        title="删除话题"
      >
        ×
      </button>
    </div>
  );
});

export default TopicItem;
