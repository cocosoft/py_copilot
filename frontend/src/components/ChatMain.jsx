import React, { useRef, useEffect, useState } from 'react';
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
  activeTopic,
  enableThinkingChain,
  setEnableThinkingChain,
  selectedModel,
  availableModels,
  onModelChange
}) => {
  const messagesEndRef = useRef(null);
  const chatMessagesRef = useRef(null);
  const modelSelectRef = useRef(null);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const [dropdownDirection, setDropdownDirection] = useState('down');

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage(e);
    }
  };

  // 处理点击外部关闭模型选择下拉列表
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modelSelectRef.current && !modelSelectRef.current.contains(event.target)) {
        setIsModelDropdownOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // 处理模型选择
  const handleSelectModel = (model) => {
    onModelChange(model);
    setIsModelDropdownOpen(false);
  };

  // 计算下拉列表显示方向
  const calculateDropdownDirection = () => {
    if (!modelSelectRef.current) return 'down';
    
    const rect = modelSelectRef.current.getBoundingClientRect();
    const dropdownHeight = 320; // 下拉列表的最大高度
    const windowHeight = window.innerHeight;
    const spaceBelow = windowHeight - rect.bottom;
    const spaceAbove = rect.top;
    
    // 如果下方空间不足，且上方空间更充足，则向上显示
    if (spaceBelow < dropdownHeight && spaceAbove > spaceBelow) {
      return 'up';
    }
    
    return 'down';
  };

  // 处理打开/关闭下拉列表
  const toggleModelDropdown = () => {
    if (!isModelDropdownOpen) {
      // 打开前计算显示方向
      setDropdownDirection(calculateDropdownDirection());
    }
    setIsModelDropdownOpen(!isModelDropdownOpen);
  };

  // 获取模型LOGO URL
  const getModelLogoUrl = (model) => {
    if (model.logo !== null && model.logo !== undefined && model.logo !== '') {
      if (model.logo.startsWith('http') || model.logo.startsWith('/')) {
        return model.logo;
      }
      return `/logos/models/${model.logo}`;
    }
    
    if (model.supplier_logo !== null && model.supplier_logo !== undefined && model.supplier_logo !== '') {
      if (model.supplier_logo.startsWith('http') || model.supplier_logo.startsWith('/')) {
        return model.supplier_logo;
      }
      return `/logos/providers/${model.supplier_logo}`;
    }
    
    return '/logos/models/default.png';
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

  // 窗口大小变化时重新计算下拉列表方向
  useEffect(() => {
    const handleResize = () => {
      if (isModelDropdownOpen) {
        setDropdownDirection(calculateDropdownDirection());
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [isModelDropdownOpen]);

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
          <button type="button" className="input-btn" title="表情">😊</button>
          <button type="button" className="input-btn" title="上传文件">📁</button>
          <button type="button" className="input-btn" title="联网搜索">🌐</button>
          <button type="button" className="input-btn" title="知识库搜索">📚</button>
          <button type="button" className={`input-btn ${enableThinkingChain ? 'active' : ''}`} title="思考模式" onClick={() => setEnableThinkingChain(!enableThinkingChain)}>🧠</button>
          <button type="button" className="input-btn" title="翻译">🔤</button>
          <div className="input-divider"></div>
          <button type="button" className="input-btn" title="录音">🎤</button>
          <button type="button" className="input-btn" title="视频">🎥</button>
          <div className="input-divider"></div>
          {selectedModel && (
            <div className="current-model-info" ref={modelSelectRef}>
              <div 
                className="current-model-display"
                onClick={toggleModelDropdown}
              >
                <img 
                  src={getModelLogoUrl(selectedModel)} 
                  alt={selectedModel.model_name || '模型LOGO'} 
                  className="current-model-logo"
                />
                <span className="current-model-text">
                  {selectedModel.model_name || selectedModel.name || '未知模型'} 
                  <span className="current-supplier-text">
                    ({selectedModel.supplier_display_name || selectedModel.supplier_name || '未知供应商'})
                  </span>
                </span>
                <span className="current-model-arrow">
                  {isModelDropdownOpen ? (dropdownDirection === 'up' ? '▼' : '▲') : '▼'}
                </span>
              </div>
              {isModelDropdownOpen && (
                <div className={`model-dropdown model-dropdown-${dropdownDirection}`}>
                  {availableModels.length === 0 ? (
                    <div className="model-dropdown-item">暂无模型数据</div>
                  ) : (
                    availableModels.map(model => (
                      <div 
                        key={model.id} 
                        className={`model-dropdown-item ${selectedModel?.id === model.id ? 'selected' : ''}`}
                        onClick={() => handleSelectModel(model)}
                      >
                        <img 
                          src={getModelLogoUrl(model)} 
                          alt={model.model_name || '模型LOGO'} 
                          className="dropdown-model-logo"
                        />
                        <div className="dropdown-model-info">
                          <span className="dropdown-model-name">
                            {model.model_name || model.name || '未知模型'}
                          </span>
                          <span className="dropdown-supplier-name">
                            {model.supplier_display_name || model.supplier_name || '未知供应商'}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
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
        
        <div className="input-wrapper">
          <textarea
            placeholder="输入消息... 使用 Shift+Enter 换行"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            className="message-input"
            rows="3"
            style={{ resize: 'none', overflowY: 'auto' }}
          />
          <button type="submit" className="send-btn">
            <span className="send-icon">➤</span>
            <span className="send-text">发送</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatMain;
