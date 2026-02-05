import React, { memo } from 'react';

// 消息骨架屏组件
const MessageSkeleton = memo(({ index }) => {
  return (
    <div key={`skeleton-${index}`} className="message bot-message skeleton">
      <div className="message-avatar">🤖</div>
      <div className="message-content">
        <div className="message-bubble">
          <div className="message-header">
            <div className="message-status">
              <span className="skeleton-badge"></span>
            </div>
            <span className="skeleton-timestamp"></span>
          </div>
          <div className="message-text">
            <div className="skeleton-text">
              <div className="skeleton-line"></div>
              <div className="skeleton-line"></div>
              <div className="skeleton-line"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

export default MessageSkeleton;