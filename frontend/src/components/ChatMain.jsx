import React, { useRef, useEffect } from 'react';
import './ChatMain.css';

const ChatMain = ({ 
  messages, 
  inputText, 
  setInputText, 
  onSendMessage, 
  onClearConversation,
  messageSkeletons,
  isTyping,
  editingMessageId,
  editingMessageText,
  setEditingMessageText,
  saveEditingMessage,
  cancelEditingMessage,
  quoteMessage,
  toggleMessageMark,
  markedMessages,
  expandedThinkingChains,
  toggleThinkingChain,
  startEditingMessage,
  totalTokens,
  copyMessage,
  regenerateMessage,
  translateMessage,
  deleteMessage,
  saveMessage,
  quotedMessage,
  cancelQuote,
  formatTime,
  formatDuration,
  MessageItem,
  MessageSkeleton,
  TypingIndicator,
  activeTopic
}) => {
  const messagesEndRef = useRef(null);
  const chatMessagesRef = useRef(null);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage(e);
    }
  };

  // 自动滚动到最新消息
  useEffect(() => {
    // 使用setTimeout确保DOM更新后再滚动
    const timer = setTimeout(() => {
      // 方法1：直接操作scrollTop（最可靠）
      if (chatMessagesRef.current) {
        chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
      } 
      // 方法2：回退到scrollIntoView
      else if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [messages, messageSkeletons, isTyping, activeTopic]);

  return (
    <div className="chat-main">
      {/* 对话操作栏 */}
      <div className="topic-header">
        <label className="topic-label">
          {activeTopic?.topic_name || '对话'}
        </label>
        <div className="topic-actions">
          <button 
            type="button"
            className="topic-action-btn"
            onClick={onClearConversation}
            title="清除对话"
          >
            🔄 清除对话
          </button>
        </div>
      </div>
      
      <div className="chat-messages" ref={chatMessagesRef}>
        {/* 渲染消息 */}
        {messages.map(message => (
          <MessageItem 
            key={message.id}
            message={message}
            formatTime={formatTime}
            formatDuration={formatDuration}
            editingMessageId={editingMessageId}
            editingMessageText={editingMessageText}
            setEditingMessageText={setEditingMessageText}
            saveEditingMessage={saveEditingMessage}
            cancelEditingMessage={cancelEditingMessage}
            quoteMessage={quoteMessage}
            toggleMessageMark={toggleMessageMark}
            markedMessages={markedMessages}
            expandedThinkingChains={expandedThinkingChains}
            toggleThinkingChain={toggleThinkingChain}
            startEditingMessage={startEditingMessage}
            totalTokens={totalTokens}
            copyMessage={copyMessage}
            regenerateMessage={regenerateMessage}
            translateMessage={translateMessage}
            deleteMessage={deleteMessage}
            saveMessage={saveMessage}
          />
        ))}
        
        {/* 渲染骨架屏 */}
        {messageSkeletons.map((index) => (
          <MessageSkeleton key={`skeleton-${index}`} index={index} />
        ))}
        
        {/* 渲染打字指示器 */}
        {isTyping && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form className="chat-input" onSubmit={onSendMessage}>
        <div className="input-actions">
          <button type="button" className="input-btn">🎤</button>
          <button type="button" className="input-btn">📷</button>
          <button type="button" className="input-btn">📁</button>
          <button type="button" className="input-btn">✨</button>
        </div>
        
        {/* 引用消息显示 */}
        {quotedMessage && (
          <div className="quoted-message">
            <div className="quoted-message-header">
              <span className="quoted-message-sender">
                {quotedMessage.sender === 'user' ? '你' : 'AI'}
              </span>
              <button 
                type="button"
                className="quoted-message-cancel"
                onClick={cancelQuote}
                title="取消引用"
              >
                ✕
              </button>
            </div>
            <div className="quoted-message-content">
              {quotedMessage.text.substring(0, 100)}
              {quotedMessage.text.length > 100 && '...'}
            </div>
          </div>
        )}
        
        <textarea
          placeholder="输入消息... 使用 Shift+Enter 换行"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          className="message-input"
          rows="1"
          style={{ resize: 'none', overflowY: 'auto' }}
        />
        <button type="submit" className="send-btn">
          <span className="send-icon">➤</span>
          <span className="send-text">发送</span>
        </button>
      </form>
    </div>
  );
};

export default ChatMain;
