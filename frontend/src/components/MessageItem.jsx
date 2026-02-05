import React, { memo } from 'react';
import EnhancedMarkdownRenderer from './EnhancedMarkdownRenderer/EnhancedMarkdownRenderer';
import { formatTime, formatDuration, formatFileSize } from '../utils/chatUtils.js';

// 使用React.memo优化EnhancedMarkdownRenderer组件
const MemoizedMarkdownRenderer = memo(EnhancedMarkdownRenderer);

// 消息项组件
const MessageItem = memo(({ 
  message, 
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
  saveMessage 
}) => {
  // 处理搜索结果消息
  if (message.type === 'search_result') {
    return (
      <div 
        key={message.id} 
        className="message search-result-message success"
      >
        <div className="message-avatar">🌐</div>
        <div className="message-content">
          <div className="message-bubble">
            <div className="message-header">
              <div className="message-status">
                <span className="status-badge success">🔍 搜索结果</span>
              </div>
              <span className="message-timestamp">{formatTime(message.timestamp)}</span>
            </div>
            <div className="search-result-content">
              {message.search_result ? (
                <>
                  <h4 className="search-result-title">{message.search_result.title}</h4>
                  <p className="search-result-description">{message.search_result.content}</p>
                  <a 
                    href={message.search_result.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="search-result-url"
                  >
                    {message.search_result.url}
                  </a>
                </>
              ) : (
                <div className="message-text">
                  <MemoizedMarkdownRenderer content={message.text} />
                </div>
              )}
            </div>
            <div className="message-actions">
              <button 
                className="message-action-btn"
                onClick={() => copyMessage(message)}
                title="复制"
              >
                📋
              </button>
              <button 
                className="message-action-btn"
                onClick={() => quoteMessage(message)}
                title="引用回复"
              >
                📝
              </button>
              <button 
                className={`message-action-btn ${markedMessages.has(message.id) ? 'active' : ''}`}
                onClick={() => toggleMessageMark(message.id)}
                title={markedMessages.has(message.id) ? '取消标记' : '标记消息'}
              >
                {markedMessages.has(message.id) ? '⭐' : '☆'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 处理普通消息
  return (
    <div 
      key={message.id} 
      className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'} ${message.status || 'success'}`}
    >
      {message.sender === 'bot' && <div className="message-avatar">🤖</div>}
      <div className="message-content">
        <div className={`message-bubble ${message.isStreaming ? 'streaming-text' : ''}`}>
          <div className="message-header">
            <div className="message-status">
              {message.sender === 'bot' && message.model && (
                <span className="model-badge">{message.model}</span>
              )}
              {message.status === 'error' && (
                <span className="status-badge error">❌ 错误</span>
              )}
              {message.status === 'success' && (
                <span className="status-badge success">✅ 成功</span>
              )}
              {message.status === 'streaming' && (
                <span className="status-badge processing">⏳ 流式响应中</span>
              )}
              {message.status === 'processing' && (
                <span className="status-badge processing">⏳ 处理中</span>
              )}
              {message.edited && (
                <span className="status-badge edited">✏️ 已编辑</span>
              )}
            </div>
            <span className="message-timestamp">{formatTime(message.timestamp)}</span>
          </div>
          
          {/* 思维链显示 */}
          {message.thinking && (
            <div className="thinking-chain-container">
              {message.isStreaming ? (
                <div className="thinking-chain">
                  {message.thinking}
                </div>
              ) : (
                <>
                  <div className="thinking-chain-toggle" onClick={() => toggleThinkingChain(message.id)}>
                    <span className="toggle-icon">
                      {expandedThinkingChains[message.id] ? '▼' : '▶'}
                    </span>
                    <span className="toggle-text">思维链</span>
                  </div>
                  {expandedThinkingChains[message.id] && (
                    <div className="thinking-chain">
                      {message.thinking}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
          
          {/* 编辑模式 */}
          {editingMessageId === message.id ? (
            <div className="message-edit-container">
              <textarea
                value={editingMessageText}
                onChange={(e) => setEditingMessageText(e.target.value)}
                className="message-edit-input"
                placeholder="编辑消息..."
                rows="3"
              />
              <div className="message-edit-actions">
                <button 
                  className="message-edit-btn save"
                  onClick={() => saveEditingMessage(message.id)}
                >
                  保存
                </button>
                <button 
                  className="message-edit-btn cancel"
                  onClick={cancelEditingMessage}
                >
                  取消
                </button>
              </div>
            </div>
          ) : (
            /* 普通显示模式 */
            <>
              {/* 文件信息显示 */}
              {message.attachedFiles && message.attachedFiles.length > 0 && (
                <div className="message-files">
                  {message.attachedFiles.map(file => (
                    <div key={file.id} className="message-file-item">
                      <span className="file-icon">📄</span>
                      <span className="file-name" title={file.name}>
                        {file.name}
                      </span>
                      <span className="file-size">
                        {formatFileSize(file.size)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {/* 消息文本显示 */}
              <div className={`message-text ${message.isStreaming ? 'streaming-text' : ''}`}>
                <MemoizedMarkdownRenderer 
                  content={message.text} 
                  className={message.isStreaming ? 'streaming' : ''}
                />
              </div>
              {message.fallbackInfo && (
                <div className="fallback-info">
                  🔄 {message.fallbackInfo}
                </div>
              )}
              {message.recoverySuggestion && (
                <div className="recovery-suggestion">
                  💡 <strong>恢复建议:</strong> {message.recoverySuggestion}
                </div>
              )}
              {message.metrics && (
                <div className="message-metrics">
                  {message.metrics.execution_time && (
                    <span className="metric-item">
                      ⏱️ <span className="metric-value">{formatDuration(message.metrics.execution_time)}</span>
                    </span>
                  )}
                  {message.metrics.success !== undefined && (
                    <span className="metric-item">
                      {message.metrics.success ? '✅' : '❌'} 
                      <span className="metric-value">{message.metrics.success ? '成功' : '失败'}</span>
                    </span>
                  )}
                </div>
              )}
            </>
          )}
          
          {/* 消息操作按钮和Tokens消耗 */}
          {!message.isStreaming && message.sender === 'user' && (
            <div className="message-actions">
              <button 
                className="message-action-btn"
                onClick={() => copyMessage(message)}
                title="复制消息"
              >
                📋
              </button>
              <button 
                className="message-action-btn"
                onClick={() => startEditingMessage(message.id, message.text)}
                title="编辑消息"
              >
                ✏️
              </button>
              <button 
                className="message-action-btn"
                onClick={() => quoteMessage(message)}
                title="引用回复"
              >
                📝
              </button>
              <button 
                className={`message-action-btn ${markedMessages.has(message.id) ? 'active' : ''}`}
                onClick={() => toggleMessageMark(message.id)}
                title={markedMessages.has(message.id) ? '取消标记' : '标记消息'}
              >
                {markedMessages.has(message.id) ? '⭐' : '☆'}
              </button>
              {message.metrics && message.metrics.tokens_used && (
                <span className="tokens-used">
                  📊 {message.metrics.tokens_used}/{totalTokens} tokens
                </span>
              )}
            </div>
          )}
          {!message.isStreaming && message.sender === 'bot' && (
            <div className="message-actions">
              <button 
                className="message-action-btn"
                onClick={() => copyMessage(message)}
                title="复制"
              >
                📋
              </button>
              <button 
                className="message-action-btn"
                onClick={() => regenerateMessage(message)}
                title="重新生成"
              >
                🔄
              </button>
              <button 
                className="message-action-btn"
                onClick={() => translateMessage(message)}
                title="翻译"
              >
                🌐
              </button>
              <button 
                className="message-action-btn"
                onClick={() => deleteMessage(message)}
                title="删除"
              >
                🗑️
              </button>
              <button 
                className="message-action-btn"
                onClick={() => saveMessage(message)}
                title="保存"
              >
                💾
              </button>
              <button 
                className="message-action-btn"
                onClick={() => quoteMessage(message)}
                title="引用回复"
              >
                📝
              </button>
              <button 
                className={`message-action-btn ${markedMessages.has(message.id) ? 'active' : ''}`}
                onClick={() => toggleMessageMark(message.id)}
                title={markedMessages.has(message.id) ? '取消标记' : '标记消息'}
              >
                {markedMessages.has(message.id) ? '⭐' : '☆'}
              </button>
              {message.metrics && message.metrics.tokens_used && (
                <span className="tokens-used">
                  📊 {message.metrics.tokens_used}/{totalTokens} tokens
                </span>
              )}
            </div>
          )}
        </div>
      </div>
      {message.sender === 'user' && <div className="message-avatar">👤</div>}
    </div>
  );
});

export default MessageItem;