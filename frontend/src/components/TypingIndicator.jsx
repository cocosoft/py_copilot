import React, { memo } from 'react';

// 打字指示器组件
const TypingIndicator = memo(() => {
  return (
    <div className="message bot-message">
      <div className="message-avatar">🤖</div>
      <div className="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  );
});

export default TypingIndicator;