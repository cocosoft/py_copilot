import React, { useRef, useEffect, useState } from 'react';
import { API_BASE_URL } from '../utils/api';
import emojis from '../utils/emojis';
import ModelSelectDropdown from './ModelManagement/ModelSelectDropdown';
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
  MessageItem,
  MessageSkeleton,
  TypingIndicator,
  activeTopic,
  enableThinkingChain,
  setEnableThinkingChain,
  enableWebSearch,
  setEnableWebSearch,
  enableKnowledgeSearch,
  setEnableKnowledgeSearch,
  selectedModel,
  availableModels,
  onModelChange,
  isLoadingModels,
  uploadedFiles,
  setUploadedFiles
}) => {
  const messagesEndRef = useRef(null);
  const chatMessagesRef = useRef(null);
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isEmojiPickerOpen, setIsEmojiPickerOpen] = useState(false);
  const [selectedEmojiCategory, setSelectedEmojiCategory] = useState(0);
  const emojiPickerRef = useRef(null);
  
  // 搜索相关状态从props获取
  // enableWebSearch, setEnableWebSearch
  // enableKnowledgeSearch, setEnableKnowledgeSearch

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage(e);
    }
  };

  // 处理点击外部关闭emoji选择器
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (emojiPickerRef.current && !emojiPickerRef.current.contains(event.target)) {
        setIsEmojiPickerOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // 处理切换emoji选择器
  const toggleEmojiPicker = () => {
    setIsEmojiPickerOpen(!isEmojiPickerOpen);
  };

  // 处理选择emoji
  const handleEmojiSelect = (emoji) => {
    setInputText(prev => prev + emoji);
  };

  // 处理切换emoji分类
  const handleEmojiCategoryChange = (index) => {
    setSelectedEmojiCategory(index);
  };

  // 处理文件上传按钮点击
  const handleUploadButtonClick = () => {
    fileInputRef.current?.click();
  };

  // 处理文件选择
  const handleFileSelect = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    
    console.log('========== 文件上传开始 ==========');
    console.log('文件名:', file.name);
    console.log('文件大小:', file.size);
    console.log('文件类型:', file.type);
    console.log('================================');
    
    // 检查文件大小（50MB限制）
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('文件大小超过50MB限制');
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      console.log('开始上传文件到:', `${API_BASE_URL}/v1/file-upload/upload`);
      
      const response = await fetch(`${API_BASE_URL}/v1/file-upload/upload`, {
        method: 'POST',
        body: formData
      });

      console.log('上传响应状态:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('上传失败响应:', errorData);
        throw new Error(errorData.detail || '文件上传失败');
      }

      const result = await response.json();
      console.log('上传成功响应:', result);

      const newFile = {
        id: result.file_id,
        name: result.filename,
        size: result.file_size,
        type: result.file_type,
        path: result.upload_path
      };
      
      console.log('新文件对象:', newFile);
      console.log('当前 uploadedFiles:', uploadedFiles);
      console.log('调用 setUploadedFiles');
      
      setUploadedFiles(prev => {
        const newFiles = [...prev, newFile];
        console.log('更新后的文件列表:', newFiles);
        return newFiles;
      });

      alert('文件上传成功！');
    } catch (error) {
      console.error('文件上传错误:', error);
      alert(`文件上传失败: ${error.message}`);
    } finally {
      setIsUploading(false);
      // 清空input，允许重复上传同一文件
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 移除已上传的文件
  const handleRemoveFile = async (fileId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/file-upload/files/${fileId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('删除文件失败');
      }

      setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
      alert('文件删除成功！');
    } catch (error) {
      console.error('删除文件错误:', error);
      alert(`删除文件失败: ${error.message}`);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };
  
  // 搜索功能已通过命令式方式实现，不再需要模态框

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
          <button 
            type="button" 
            className="input-btn" 
            title="表情"
            onClick={toggleEmojiPicker}
            ref={emojiPickerRef}
          >
            😊
          </button>
          <button 
            type="button" 
            className="input-btn" 
            title="上传文件"
            onClick={handleUploadButtonClick}
            disabled={isUploading}
          >
            {isUploading ? '⏳' : '📁'}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
          <button type="button" className={`input-btn ${enableWebSearch ? 'active' : ''}`} title="联网搜索（开关按钮）" onClick={() => {
            if (!enableWebSearch) {
              setEnableWebSearch(true);
              setEnableKnowledgeSearch(false);
            } else {
              setEnableWebSearch(false);
            }
          }}>🌐</button>
          <button type="button" className={`input-btn ${enableKnowledgeSearch ? 'active' : ''}`} title="知识库搜索（开关按钮）" onClick={() => {
            if (!enableKnowledgeSearch) {
              setEnableKnowledgeSearch(true);
              setEnableWebSearch(false);
            } else {
              setEnableKnowledgeSearch(false);
            }
          }}>📚</button>
          <button type="button" className={`input-btn ${enableThinkingChain ? 'active' : ''}`} title="思考模式（开关按钮）" onClick={() => setEnableThinkingChain(!enableThinkingChain)}>🧠</button>
          <button type="button" className="input-btn" title="翻译">🔤</button>
          <div className="input-divider"></div>
          <button type="button" className="input-btn" title="录音">🎤</button>
          <button type="button" className="input-btn" title="视频">🎥</button>
          <div className="input-divider"></div>
          <ModelSelectDropdown
            models={availableModels}
            selectedModel={selectedModel}
            onModelSelect={onModelChange}
            placeholder="请选择模型"
            className="chat-model-selector"
            disabled={isLoadingModels}
            scene="chat"
            dropDirection="up"
            singleLine={true}
          />
        </div>
        
        {/* emoji选择器 */}
        {isEmojiPickerOpen && (
          <div className="emoji-picker">
            <div className="emoji-categories">
              {emojis.map((category, index) => (
                <button
                  key={index}
                  type="button"
                  className={`emoji-category-btn ${selectedEmojiCategory === index ? 'active' : ''}`}
                  onClick={() => handleEmojiCategoryChange(index)}
                  title={category.category}
                >
                  {category.icon}
                </button>
              ))}
            </div>
            <div className="emoji-grid">
              {emojis[selectedEmojiCategory].items.map((emoji, index) => (
                <button
                  key={index}
                  type="button"
                  className="emoji-item"
                  onClick={() => handleEmojiSelect(emoji)}
                  title={emoji}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>
        )}
        
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
        
        {/* 已上传文件显示 */}
        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            {uploadedFiles.map(file => (
              <div key={file.id} className="uploaded-file-item">
                <span className="file-icon">📄</span>
                <span className="file-name" title={file.name}>
                  {file.name}
                </span>
                <span className="file-size">
                  {formatFileSize(file.size)}
                </span>
                <button
                  type="button"
                  className="file-remove-btn"
                  onClick={() => handleRemoveFile(file.id)}
                  title="删除文件"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
        
        <div className="input-wrapper">
          <textarea
            placeholder="输入消息... 使用 Shift+Enter 换行\n提示: 使用 /search 关键词 直接进行网页搜索"
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
