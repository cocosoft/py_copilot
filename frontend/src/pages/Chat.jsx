import React, { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react';
import { conversationApi } from '../utils/api';
import { API_BASE_URL } from '../utils/apiUtils';
import EnhancedMarkdownRenderer from '../components/EnhancedMarkdownRenderer/EnhancedMarkdownRenderer';
import LeftSidebar from '../components/LeftSidebar';
import ChatMain from '../components/ChatMain';
import TopicSidebar from '../components/TopicSidebar';
import './chat.css';

// 简单的tokens计算函数
const calculateTokens = (text) => {
  if (!text) return 0;
  
  // 移除多余的空白字符
  const cleanedText = text.trim();
  
  // 计算英文单词数（按空格分割）
  const englishWords = cleanedText.match(/\b[a-zA-Z]+\b/g) || [];
  
  // 计算中文汉字数
  const chineseChars = cleanedText.match(/[\u4e00-\u9fa5]/g) || [];
  
  // 计算其他字符数（数字、标点符号等）
  const otherChars = cleanedText.replace(/[a-zA-Z\u4e00-\u9fa5\s]/g, '').length;
  
  // 估算tokens数量：英文单词 * 1.3 + 中文汉字 * 1 + 其他字符
  const estimatedTokens = Math.round(englishWords.length * 1.3 + chineseChars.length + otherChars);
  
  return estimatedTokens;
};

// 使用React.memo优化EnhancedMarkdownRenderer组件
const MemoizedMarkdownRenderer = memo(EnhancedMarkdownRenderer);

// 使用React.memo优化消息项组件
const MessageItem = memo(({ message, formatTime, formatDuration, editingMessageId, editingMessageText, setEditingMessageText, saveEditingMessage, cancelEditingMessage, quoteMessage, toggleMessageMark, markedMessages, expandedThinkingChains, toggleThinkingChain, startEditingMessage, totalTokens, copyMessage, regenerateMessage, translateMessage, deleteMessage, saveMessage }) => {
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
          <>                <div className={`message-text ${message.isStreaming ? 'streaming-text' : ''}`}>
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

// 使用React.memo优化消息骨架屏组件
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

// 使用React.memo优化打字指示器组件
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

const Chat = () => {
  
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [availableModels, setAvailableModels] = useState([
    {
      id: 50,
      model_id: 'moonshotai/Kimi-K2-Thinking',
      model_name: 'Kimi-K2-Thinking',
      description: 'Kimi K2 Thinking 是最新、最强大的开源思考模型。它通过大幅扩展多步推理深度，并在 200–300 次连续工具调用中保持稳定的工具使用，在 Humanity\'s Last Exam (HLE)、BrowseComp 及其他基准测试中树立了新的标杆。同时，K2 Thinking 是一款原生支持 INT4 量化的模型，拥有 256K 上下文窗口，实现了推理延迟和 GPU 显存占用的无损降低',
      logo: '/logos/models/20251227_102702_831766.png',
      supplier_id: 45,
      supplier_name: '硅基流动',
      supplier_display_name: '硅基流动',
      supplier_logo: '/logos/providers/siliconflow.png',
      is_default: true,
      capabilities: [
        {
          id: 1,
          name: 'text_generation',
          display_name: '文本生成'
        },
        {
          id: 2,
          name: 'text_summarization',
          display_name: '文本摘要'
        },
        {
          id: 3,
          name: 'text_classification',
          display_name: '文本分类'
        },
        {
          id: 4,
          name: 'sentiment_analysis',
          display_name: '情感分析'
        },
        {
          id: 5,
          name: 'translation',
          display_name: '翻译'
        },
        {
          id: 6,
          name: 'question_answering',
          display_name: '问答'
        },
        {
          id: 69,
          name: 'chat',
          display_name: '对话'
        }
      ]
    }
  ]);
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [lastResponseTime, setLastResponseTime] = useState(null);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [enableStreaming, setEnableStreaming] = useState(true);
  const [enableThinkingChain, setEnableThinkingChain] = useState(false);
  const [expandedThinkingChains, setExpandedThinkingChains] = useState({}); // 管理各个消息的思维链展开/收缩状态
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false); // 左侧控制面板伸缩状态
  const [isLoadingMessages, setIsLoadingMessages] = useState(false); // 消息加载状态
  const [messageSkeletons, setMessageSkeletons] = useState([]); // 消息骨架屏数量
  const [preloadedMessages, setPreloadedMessages] = useState({}); // 预加载的消息
  const [offlineMessages, setOfflineMessages] = useState([]); // 离线消息队列
  const [isReconnecting, setIsReconnecting] = useState(false); // 重连状态
  const [reconnectAttempts, setReconnectAttempts] = useState(0); // 重连尝试次数
  const [editingMessageId, setEditingMessageId] = useState(null); // 正在编辑的消息ID
  const [editingMessageText, setEditingMessageText] = useState(''); // 正在编辑的消息文本
  const [quotedMessage, setQuotedMessage] = useState(null); // 引用的消息
  const [theme, setTheme] = useState('light'); // 当前主题：light或dark
  const [searchQuery, setSearchQuery] = useState(''); // 搜索关键词
  const [searchResults, setSearchResults] = useState([]); // 搜索结果
  const [isSearching, setIsSearching] = useState(false); // 搜索状态
  const [markedMessages, setMarkedMessages] = useState(new Set()); // 标记的消息ID集合
  const [isShared, setIsShared] = useState(false); // 对话是否已共享
  const [shareLink, setShareLink] = useState(''); // 共享链接
  const [collaborators, setCollaborators] = useState([]); // 协作者列表
  const [isCollaborating, setIsCollaborating] = useState(false); // 是否处于协作模式
  const [totalTokens, setTotalTokens] = useState(0); // 整个对话的总tokens数量
  const [messages, setMessages] = useState([]); // 消息列表
  const [conversationId, setConversationId] = useState(1); // 对话ID
  const [activeTopic, setActiveTopic] = useState(null); // 当前活跃的话题
  const [showTopicSidebar, setShowTopicSidebar] = useState(true); // 是否显示话题侧边栏
  const [refreshTopicsFlag, setRefreshTopicsFlag] = useState(false); // 控制话题列表刷新的标志
  const [topicSidebarCollapsed, setTopicSidebarCollapsed] = useState(false); // 话题侧边栏收缩状态
  const messagesEndRef = useRef(null);
  const reconnectTimerRef = useRef(null); // 重连定时器引用
  const modelsLoadedRef = useRef(false); // 防止重复加载模型列表
  
  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);
  

  
  // 显示消息骨架屏
  const showMessageSkeletons = useCallback((count = 3) => {
    setMessageSkeletons(Array.from({ length: count }, (_, index) => index));
    setIsLoadingMessages(true);
  }, []);
  
  // 隐藏消息骨架屏
  const hideMessageSkeletons = useCallback(() => {
    setMessageSkeletons([]);
    setIsLoadingMessages(false);
  }, []);
  
  // 预加载消息
  const preloadMessages = useCallback(async (conversationId, topicId) => {
    const cacheKey = `${conversationId}:${topicId}`;
    
    // 检查是否已经预加载过
    if (preloadedMessages[cacheKey]) {
      return preloadedMessages[cacheKey];
    }
    
    try {
      // 显示骨架屏
      showMessageSkeletons();
      
      // 模拟预加载延迟
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // 实际获取消息（这里可以根据实际情况调用API）
      // 由于当前没有实际的消息API，这里返回模拟数据
      const preloadedData = {
        messages: [
          {
            id: 1,
            sender: 'bot',
            text: '欢迎回来！我是Py Copilot，您的智能助手。',
            timestamp: new Date(),
            status: 'success'
          }
        ],
        timestamp: Date.now()
      };
      
      // 缓存预加载的消息
      setPreloadedMessages(prev => ({
        ...prev,
        [cacheKey]: preloadedData
      }));
      
      return preloadedData;
    } catch (error) {
      console.error('预加载消息失败:', error);
      return null;
    } finally {
      // 隐藏骨架屏
      hideMessageSkeletons();
    }
  }, [preloadedMessages, showMessageSkeletons, hideMessageSkeletons]);
  
  // 从API获取对话模型列表
  const fetchConversationModels = useCallback(async () => {
    // 防止重复加载
    if (modelsLoadedRef.current) {
      console.log('模型列表已加载，跳过重复请求');
      return;
    }
    
    try {
      setIsLoadingModels(true);
      const response = await conversationApi.getConversationModels();
      console.log('获取到的模型列表响应:', response);
      // 检查后端返回的数据格式
      let modelsData = [];
      if (response.models) {
        // 后端直接返回models和total格式
        modelsData = response.models;
        console.log('从response.models获取到的模型数据:', modelsData);
      } else if (response.status === 'success' && response.models) {
        // 兼容旧的status格式
        modelsData = response.models;
        console.log('从response.status获取到的模型数据:', modelsData);
      } else {
        console.error('未找到模型数据:', response);
      }
      
      if (modelsData.length > 0) {
        console.log('设置模型数据:', modelsData);
        setAvailableModels(modelsData);
        // 如果有默认模型，自动选择
        const defaultModel = modelsData.find(model => model.is_default);
        if (defaultModel) {
          setSelectedModel(defaultModel);
        } else {
          setSelectedModel(modelsData[0]);
        }
        // 标记模型已加载
        modelsLoadedRef.current = true;
      } else {
        console.error('模型数据为空:', modelsData);
        // 设置默认模型作为备用
        setAvailableModels([
          {
            id: 50,
            model_id: 'moonshotai/Kimi-K2-Thinking',
            model_name: 'Kimi-K2-Thinking',
            supplier_name: '硅基流动',
            supplier_display_name: '硅基流动',
            is_default: true
          }
        ]);
        setSelectedModel({
          id: 50,
          model_id: 'moonshotai/Kimi-K2-Thinking',
          model_name: 'Kimi-K2-Thinking',
          supplier_name: '硅基流动',
          supplier_display_name: '硅基流动',
          is_default: true
        });
      }
    } catch (error) {
      console.error('获取对话模型列表失败:', error);
      // 设置默认模型作为备用
      setAvailableModels([
        {
          id: 50,
          model_id: 'moonshotai/Kimi-K2-Thinking',
          model_name: 'Kimi-K2-Thinking',
          supplier_name: '硅基流动',
          supplier_display_name: '硅基流动',
          is_default: true
        }
      ]);
      setSelectedModel({
        id: 50,
        model_id: 'moonshotai/Kimi-K2-Thinking',
        model_name: 'Kimi-K2-Thinking',
        supplier_name: '硅基流动',
        supplier_display_name: '硅基流动',
        is_default: true
      });
    } finally {
      setIsLoadingModels(false);
    }
  }, []);
  
  // 话题管理函数
  const refreshTopics = useCallback(() => {
    // 设置刷新标志，触发话题列表刷新
    setRefreshTopicsFlag(prev => !prev);
  }, []);

  // 处理话题创建
  const handleTopicCreate = useCallback(async (newTopic) => {
    if (newTopic) {
      // 设置为活跃话题
      setActiveTopic(newTopic);
      // 清空消息列表，准备接收新消息
      setMessages([]);
      // 自动聚焦到输入框
      setTimeout(() => {
        const inputElement = document.querySelector('.message-input');
        if (inputElement) {
          inputElement.focus();
        }
      }, 100);
    }
  }, []);

  
  // 切换主题
  const toggleTheme = useCallback(() => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    // 应用主题到文档根元素
    document.documentElement.setAttribute('data-theme', newTheme);
  }, [theme]);
  
  // 执行消息搜索
  const performSearch = useCallback(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }
    
    setIsSearching(true);
    
    // 简单的客户端搜索实现
    const query = searchQuery.toLowerCase().trim();
    const results = messages.filter(message => {
      const messageText = message.text.toLowerCase();
      return messageText.includes(query);
    });
    
    // 模拟搜索延迟
    setTimeout(() => {
      setSearchResults(results);
      setIsSearching(false);
    }, 300);
  }, [searchQuery, messages]);
  
  // 添加快捷键监听
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl/Cmd + K: 聚焦到输入框
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const inputElement = document.querySelector('.message-input');
        if (inputElement) {
          inputElement.focus();
        }
      }
      
      // Ctrl/Cmd + H: 切换话题侧边栏
      if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
        e.preventDefault();
        setShowTopicSidebar(prev => !prev);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);
  
  // 清除搜索结果
  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setSearchResults([]);
    setIsSearching(false);
  }, []);
  
  // 标记/取消标记消息
  const toggleMessageMark = useCallback((messageId) => {
    setMarkedMessages(prev => {
      const newMarked = new Set(prev);
      if (newMarked.has(messageId)) {
        newMarked.delete(messageId);
      } else {
        newMarked.add(messageId);
      }
      return newMarked;
    });
  }, []);
  
  // 复制消息内容
  const copyMessage = useCallback((message) => {
    if (!message || !message.text) return;
    
    navigator.clipboard.writeText(message.text).then(() => {
      alert('消息内容已复制到剪贴板！');
    }).catch(err => {
      console.error('复制失败:', err);
      alert('复制失败，请重试');
    });
  }, []);
  
  // 翻译消息
  const translateMessage = useCallback((message) => {
    if (!message || !message.text) return;
    
    alert('翻译功能正在开发中，敬请期待！');
  }, []);
  
  // 删除消息
  const deleteMessage = useCallback((message) => {
    if (!message) return;
    
    if (window.confirm('确定要删除这条消息吗？删除后将无法恢复。')) {
      setMessages(prev => prev.filter(msg => msg.id !== message.id));
      alert('消息已删除');
    }
  }, []);
  
  // 保存消息
  const saveMessage = useCallback((message) => {
    if (!message || !message.text) return;
    
    // 准备保存的数据
    const saveData = {
      id: message.id,
      text: message.text,
      timestamp: message.timestamp,
      model: message.model,
      tokensUsed: message.metrics?.tokens_used || 0,
      saveTime: new Date().toISOString()
    };
    
    // 保存到localStorage
    try {
      const savedMessages = JSON.parse(localStorage.getItem('savedMessages') || '[]');
      savedMessages.push(saveData);
      localStorage.setItem('savedMessages', JSON.stringify(savedMessages));
      alert('消息已保存到本地存储！');
    } catch (error) {
      console.error('保存失败:', error);
      alert('保存失败，请重试');
    }
  }, []);
  
  // 导出消息
  const exportMessages = useCallback((format = 'json') => {
    // 准备导出数据
    const exportData = {
      conversationId: 1,
      exportTime: new Date().toISOString(),
      messageCount: messages.length,
      messages: messages.map(msg => ({
        id: msg.id,
        sender: msg.sender,
        text: msg.text,
        timestamp: msg.timestamp,
        status: msg.status,
        ...(msg.model && { model: msg.model }),
        ...(msg.tokensUsed && { tokensUsed: msg.tokensUsed }),
        ...(msg.executionTime && { executionTime: msg.executionTime })
      }))
    };
    
    let content, mimeType, filename;
    
    if (format === 'json') {
      content = JSON.stringify(exportData, null, 2);
      mimeType = 'application/json';
      filename = `conversation_${Date.now()}.json`;
    } else if (format === 'txt') {
      // 生成纯文本格式
      let textContent = `对话导出\n`;
      textContent += `导出时间: ${new Date().toLocaleString()}\n`;
      textContent += `消息数量: ${messages.length}\n\n`;
      
      messages.forEach(msg => {
        const senderLabel = msg.sender === 'user' ? '你' : 'AI';
        const timestamp = new Date(msg.timestamp).toLocaleString();
        textContent += `[${timestamp}] ${senderLabel}:\n`;
        textContent += `${msg.text}\n\n`;
      });
      
      content = textContent;
      mimeType = 'text/plain';
      filename = `conversation_${Date.now()}.txt`;
    }
    
    // 创建下载链接
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [messages]);
  
  // 生成共享链接
  const generateShareLink = useCallback(() => {
    // 模拟生成共享链接
    const shareId = Math.random().toString(36).substring(2, 10);
    const link = `${window.location.origin}/shared/${shareId}`;
    setShareLink(link);
    setIsShared(true);
    
    // 模拟添加当前用户为协作者
    setCollaborators([{
      id: 1,
      name: '当前用户',
      avatar: '👤',
      isOwner: true
    }]);
    
    setIsCollaborating(true);
    
    // 复制到剪贴板
    navigator.clipboard.writeText(link).then(() => {
      alert('共享链接已复制到剪贴板！');
    }).catch(err => {
      console.error('复制失败:', err);
    });
  }, []);
  
  // 复制共享链接
  const copyShareLink = useCallback(() => {
    if (!shareLink) return;
    
    navigator.clipboard.writeText(shareLink).then(() => {
      alert('共享链接已复制到剪贴板！');
    }).catch(err => {
      console.error('复制失败:', err);
    });
  }, [shareLink]);
  
  // 停止共享
  const stopSharing = useCallback(() => {
    if (window.confirm('确定要停止共享对话吗？停止后协作者将无法访问此对话。')) {
      setIsShared(false);
      setShareLink('');
      setCollaborators([]);
      setIsCollaborating(false);
      alert('对话共享已停止！');
    }
  }, []);
  
  // 邀请协作者
  const inviteCollaborator = useCallback(() => {
    const email = prompt('请输入要邀请的协作者邮箱：');
    if (!email) return;
    
    // 模拟邀请协作者
    const newCollaborator = {
      id: Date.now(),
      name: email.split('@')[0],
      avatar: '👥',
      isOwner: false
    };
    
    setCollaborators(prev => [...prev, newCollaborator]);
    alert(`已邀请 ${email} 作为协作者！`);
  }, []);
  
  // 移除协作者
  const removeCollaborator = useCallback((collaboratorId) => {
    setCollaborators(prev => prev.filter(c => c.id !== collaboratorId));
  }, []);
  
  // 错误分类和恢复建议
  const getErrorDetails = useCallback((error) => {
    // 网络错误
    if (!navigator.onLine) {
      return {
        type: 'network',
        message: '网络连接已断开，请检查您的网络连接后重试。',
        recovery: '请检查您的网络连接，确保您已连接到互联网，然后重新发送消息。',
        severity: 'high'
      };
    }
    
    // 超时错误
    if (error.message.includes('timeout') || error.message.includes('超时')) {
      return {
        type: 'timeout',
        message: '请求超时，服务器响应时间过长。',
        recovery: '请检查网络连接，或尝试使用更短的问题，稍后再重试。',
        severity: 'medium'
      };
    }
    
    // 404错误
    if (error.response?.status === 404) {
      return {
        type: 'not_found',
        message: '服务暂时不可用，请稍后再试。',
        recovery: '服务器可能正在维护，请稍后再尝试发送消息。',
        severity: 'medium'
      };
    }
    
    // 500+错误
    if (error.response?.status >= 500) {
      return {
        type: 'server_error',
        message: '服务器内部错误，请联系管理员。',
        recovery: '服务器遇到问题，请稍后再试，或联系系统管理员。',
        severity: 'high'
      };
    }
    
    // 401/403错误
    if (error.response?.status === 401 || error.response?.status === 403) {
      return {
        type: 'unauthorized',
        message: '权限不足，请检查您的登录状态。',
        recovery: '请重新登录系统，然后再尝试发送消息。',
        severity: 'high'
      };
    }
    
    // 模型错误
    if (error.message.includes('model') || error.message.includes('模型')) {
      return {
        type: 'model_error',
        message: '模型调用失败，请尝试选择其他模型。',
        recovery: '请尝试选择其他可用的模型，或稍后再试。',
        severity: 'medium'
      };
    }
    
    // API详细错误
    if (error.response?.data?.detail) {
      return {
        type: 'api_error',
        message: error.response.data.detail,
        recovery: '请检查您的请求内容，确保符合要求，然后重试。',
        severity: 'medium'
      };
    }
    
    // 默认错误
    return {
      type: 'unknown',
      message: '抱歉，我暂时无法处理你的请求。请稍后再试。',
      recovery: '请稍后再尝试发送消息，或检查系统状态。',
      severity: 'low'
    };
  }, []);
  


  // 流式响应处理
  const handleStreamingResponse = useCallback(async (text, conversationId = 1, topicId = null) => {
    try {
      // 构建消息数据，在新话题状态下不传递topic_id
      const messageData = {
        content: text,
        use_llm: true,
        model_name: selectedModel ? selectedModel.model_id : 'moonshotai/Kimi-K2-Thinking',
        enable_thinking_chain: enableThinkingChain
      };
      
      // 只有在有活跃话题时才添加topic_id
      if (topicId || activeTopic?.id) {
        messageData.topic_id = topicId || activeTopic?.id;
      }

      // 创建流式消息对象，使用时间戳+随机数确保唯一ID
      const streamingMessage = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        sender: 'bot',
        text: '',
        timestamp: new Date(),
        status: 'streaming',
        conversationId: conversationId,
        topicId: topicId || activeTopic?.id || null,
        model: selectedModel ? selectedModel.model_name : '未知模型',
        isStreaming: true,
        thinking: null // 初始不显示思维链信息，等待后端发送实际的思维链步骤
      };

      setCurrentStreamingMessage(streamingMessage);
      setMessages(prevMessages => [...prevMessages, streamingMessage]);

      // 用于累积完整的回复内容
      let fullResponse = '';
      // 用于累积完整的思维链内容
      let fullThinkingChain = '';

      // 使用apiUtils中的request函数发送流式请求
      // 注意：由于需要处理流式响应，这里直接使用fetch API，但确保使用正确的URL格式
      const response = await fetch(`/api/v1/conversations/${conversationId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData),
        // 增加超时时间，适合长连接
        timeout: 60000
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // 检查是否支持流式响应
      if (!response.body || !response.body.getReader) {
        throw new Error('浏览器不支持流式响应');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let streamCompleted = false;

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            // 处理流结束前的最后一段数据
            if (buffer.length > 0) {
              // 尝试处理剩余缓冲区数据
              buffer += decoder.decode(); // 最后一次解码不需要stream: true
              let eventIndex;
              while ((eventIndex = buffer.indexOf('\n\n')) !== -1) {
                const eventData = buffer.slice(0, eventIndex);
                buffer = buffer.slice(eventIndex + 2);
                processEventData(eventData);
              }
              // 如果还有剩余数据，也尝试处理
              if (buffer.trim().length > 0 && buffer.startsWith('data: ')) {
                processEventData(buffer.trim());
              }
            }
            break;
          }

          // 解码数据并添加到缓冲区
          buffer += decoder.decode(value, { stream: true });
          
          // 处理缓冲区中的所有完整事件
          let eventIndex;
          while ((eventIndex = buffer.indexOf('\n\n')) !== -1) {
            const eventData = buffer.slice(0, eventIndex);
            buffer = buffer.slice(eventIndex + 2);
            processEventData(eventData);
          }
        }

        // 处理流结束
        handleStreamEnd();
        
      } catch (streamError) {
        console.error('流式响应读取错误:', streamError);
        handleStreamError(streamError);
      } finally {
        reader.releaseLock();
        if (!streamCompleted) {
          // 确保在任何情况下都能正确关闭流
          handleStreamEnd();
        }
      }

      // 处理单个事件数据
      function processEventData(eventData) {
        if (eventData.startsWith('data: ')) {
          const jsonData = eventData.slice(6).trim();
          if (!jsonData) return;
          
          if (jsonData === '[DONE]') {
            // 流式响应结束标记
            handleStreamEnd();
            return;
          }

          try {
            const data = JSON.parse(jsonData);
            
            switch (data.type) {
              case 'thinking':
                // 累积完整的思维链内容
                fullThinkingChain += data.content;
                
                // 更新思维链显示，使用累积的完整内容
                setCurrentStreamingMessage(prev => ({
                  ...prev,
                  thinking: fullThinkingChain
                }));
                
                // 更新消息列表中的思维链，使用累积的完整内容
                setMessages(prevMessages => 
                  prevMessages.map(msg => 
                    msg.id === streamingMessage.id 
                      ? { ...msg, thinking: fullThinkingChain }
                      : msg
                  )
                );
                break;
                
              case 'content':
                // 累积完整的回复内容
                fullResponse += data.content;
                
                // 更新消息内容，使用累积的完整内容
                setCurrentStreamingMessage(prev => ({
                  ...prev,
                  text: fullResponse
                }));
                
                // 更新消息列表中的消息，使用累积的完整内容
                setMessages(prevMessages => 
                  prevMessages.map(msg => 
                    msg.id === streamingMessage.id 
                      ? { ...msg, text: fullResponse }
                      : msg
                  )
                );
                break;
                
              case 'topic':
                // 更新话题信息
                if (data.topic) {
                  console.log(`收到话题信息: ${data.topic.title}`);
                  setActiveTopic(data.topic);
                  streamingMessage.topic = data.topic;
                  // 不要立即刷新话题列表，避免覆盖更新后的话题信息
                  // 而是在complete事件中，当所有的响应都完成后，再刷新话题列表
                }
                break;
                
              case 'complete':
                // 流式响应完成
                streamCompleted = true;
                setCurrentStreamingMessage(null);
                
                // 计算AI回复的tokens数量
                const aiTokens = calculateTokens(fullResponse);
                
                setMessages(prevMessages => 
                  prevMessages.map(msg => 
                    msg.id === streamingMessage.id 
                      ? { 
                          ...msg, 
                          status: 'success', 
                          isStreaming: false,
                          metrics: {
                            ...(data.metrics || {}),
                            tokens_used: data.metrics?.tokens_used || aiTokens
                          }
                        } 
                      : msg
                  )
                );
                // 设置思维链默认收缩状态
                setExpandedThinkingChains(prev => ({ ...prev, [streamingMessage.id]: false }));
                setConnectionStatus('connected');
                
                // 刷新话题列表，更新消息数量
                refreshTopics();

                break;
                
              case 'error':
                // 处理错误
                streamCompleted = true;
                setCurrentStreamingMessage(null);
                
                setMessages(prevMessages => 
                  prevMessages.map(msg => 
                    msg.id === streamingMessage.id 
                      ? { 
                          ...msg, 
                          text: data.content || '流式响应发生错误', 
                          status: 'error',
                          isStreaming: false 
                        }
                      : msg
                  )
                );
                setConnectionStatus('error');
                break;
                
              default:
                break;
            }
          } catch (parseError) {
            console.error('解析流式响应数据失败:', parseError, '原始数据:', jsonData);
          }
        }
      }

      // 处理流结束
      function handleStreamEnd() {
        if (streamCompleted) return;
        streamCompleted = true;
        
        setCurrentStreamingMessage(null);
        setMessages(prevMessages => 
          prevMessages.map(msg => 
            msg.id === streamingMessage.id 
              ? { ...msg, status: 'success', isStreaming: false } 
              : msg
          )
        );
        // 设置思维链默认收缩状态
        setExpandedThinkingChains(prev => ({ ...prev, [streamingMessage.id]: false }));
        setConnectionStatus('connected');
        
        // 如果有话题信息，更新活跃话题
        if (streamingMessage.topic) {
          console.log(`流结束时使用streamingMessage中的话题信息: ${streamingMessage.topic.title}`);
          setActiveTopic(streamingMessage.topic);
          // 不再刷新话题列表，避免无限递归
          // 话题列表的刷新已经在complete事件中处理
        }
      }

      // 处理流错误
      function handleStreamError(error) {
        if (streamCompleted) return;
        streamCompleted = true;
        
        setCurrentStreamingMessage(null);
        setMessages(prevMessages => 
          prevMessages.map(msg => 
            msg.id === streamingMessage.id 
              ? { 
                  ...msg, 
                  text: '流式响应读取失败: ' + (error.message || '网络错误'), 
                  status: 'error',
                  isStreaming: false 
                }
              : msg
          )
        );
        setConnectionStatus('error');
      }

    } catch (error) {
      console.error('流式响应处理失败:', error);
      setCurrentStreamingMessage(null);
      
      // 获取错误详情和恢复建议
      const errorDetails = getErrorDetails(error);
      
      // 创建错误消息
      const errorMessage = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        sender: 'bot',
        text: errorDetails.message,
        timestamp: new Date(),
        status: 'error',
        errorType: errorDetails.type,
        recoverySuggestion: errorDetails.recovery,
        severity: errorDetails.severity
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      setConnectionStatus('error');
    }
  }, [selectedModel, enableThinkingChain, getErrorDetails, activeTopic]);

  // 处理发送消息
  // 重连函数
  // 发送消息的核心逻辑，不依赖于inputText
  const sendMessageCore = useCallback(async (text) => {
    if (!text.trim()) return;
    
    try {
      // 只记录关键步骤的日志
      console.log(`开始发送消息: ${text.substring(0, 50)}${text.length > 50 ? '...' : ''}`);
      
      // 计算用户消息的tokens数量
      const userTokens = calculateTokens(text.trim());
      
      // 创建临时消息
      const tempMessage = {
        id: Date.now(),
        sender: 'user',
        text: text.trim(),
        timestamp: new Date(),
        status: 'sending',
        conversationId: conversationId,
        topicId: activeTopic?.id || null,
        metrics: {
          tokens_used: userTokens
        }
      };
      
      // 添加到消息列表
      setMessages(prev => [...prev, tempMessage]);
      scrollToBottom();
      
      // 检查网络连接
      if (!navigator.onLine) {
        console.warn('网络离线，将消息加入离线队列');
        // 离线状态，加入离线消息队列
        setOfflineMessages(prev => [...prev, { text: text.trim() }]);
        // 更新消息状态为离线
        setMessages(prev => prev.map(msg => 
          msg.id === tempMessage.id 
            ? { ...msg, status: 'offline' }
            : msg
        ));
        return;
      }
      
      // 在线状态，发送消息
      if (enableStreaming) {
        // 流式响应已在handleStreamingResponse中记录日志
        await handleStreamingResponse(text.trim());
      } else {
        // 普通响应
        const response = await conversationApi.sendMessage(conversationId, {
          content: text.trim(),
          use_llm: true,
          model_name: selectedModel ? selectedModel.model_id : 'moonshotai/Kimi-K2-Thinking',
          enable_thinking_chain: enableThinkingChain,
          topic_id: activeTopic?.id || null
        });
        
        // 更新消息状态
        setMessages(prev => prev.map(msg => 
          msg.id === tempMessage.id 
            ? { ...msg, status: 'success' }
            : msg
        ));
        
        // 计算AI回复的tokens数量
        const aiTokens = calculateTokens(response.assistant_message?.content || '');
        
        // 添加AI回复
        if (response.assistant_message) {
          setMessages(prev => [...prev, {
            id: response.assistant_message.id || Date.now() + 1,
            sender: 'bot',
            text: response.assistant_message.content,
            timestamp: new Date(response.assistant_message.created_at),
            status: 'success',
            conversationId: conversationId,
            topicId: response.assistant_message.topic_id || activeTopic?.id || null,
            metrics: {
              tokens_used: aiTokens
            }
          }]);
        }
        
        // 如果有新话题创建，更新活跃话题
        if (response.new_topic) {
          setActiveTopic(response.new_topic);
          console.log(`新话题创建: ${response.new_topic.topic_name}`);
        }
        
        // 刷新话题列表，更新消息数量
        refreshTopics();
        
      }
      
    } catch (error) {
      console.error(`发送消息失败: ${error.message}`);
      // 更新消息状态为失败
      setMessages(prev => prev.map(msg => 
        msg.id === tempMessage.id 
          ? { ...msg, status: 'error' }
          : msg
      ));
      
      // 显示错误提示
      const errorDetails = getErrorDetails(error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'bot',
        text: errorDetails.message,
        timestamp: new Date(),
        status: 'error',
        conversationId: conversationId,
        topicId: activeTopic?.id || null
      }]);
    }
  }, [enableStreaming, selectedModel, handleStreamingResponse, getErrorDetails, conversationId, activeTopic, refreshTopics]);
  
  // 重新生成消息
  const regenerateMessage = useCallback(async (message) => {
    if (!message || message.sender !== 'bot') return;
    
    // 找到该消息之前的用户消息
    const messageIndex = messages.findIndex(msg => msg.id === message.id);
    if (messageIndex === -1) return;
    
    // 找到最近的用户消息
    let userMessage = null;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].sender === 'user') {
        userMessage = messages[i];
        break;
      }
    }
    
    if (!userMessage) {
      alert('无法找到对应的用户消息');
      return;
    }
    
    // 重新发送用户消息，不删除原有AI回复
    await sendMessageCore(userMessage.text);
  }, [messages, sendMessageCore]);
  
  // 处理发送消息
  const handleSendMessage = useCallback(async (e) => {
    e.preventDefault();
    const text = inputText.trim();
    if (!text) return;
    
    // 清空输入框
    setInputText('');
    
    // 调用核心发送逻辑
    await sendMessageCore(text);
  }, [inputText, sendMessageCore]);

  const reconnect = useCallback(() => {
    if (isReconnecting) return;
    
    console.log('开始重连尝试');
    setIsReconnecting(true);
    setReconnectAttempts(0);
    
    const attemptReconnect = async (attempt) => {
      try {
        console.log(`重连尝试 ${attempt + 1}`);
        // 模拟重连尝试
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 检查连接状态
        if (navigator.onLine) {
          console.log('网络连接已恢复');
          setConnectionStatus('connected');
          setIsReconnecting(false);
          setReconnectAttempts(0);
          
          // 尝试发送离线消息
          if (offlineMessages.length > 0) {
            console.log(`发现 ${offlineMessages.length} 条离线消息，准备发送`);
            const pendingMessages = [...offlineMessages];
            setOfflineMessages([]);
            
            for (const msg of pendingMessages) {
              console.log(`发送离线消息: ${msg.text.substring(0, 50)}${msg.text.length > 50 ? '...' : ''}`);
              await sendMessageCore(msg.text);
            }
            console.log('所有离线消息发送完成');
          }
          
          return;
        }
        
        // 指数退避重连
        const delay = Math.min(30000, 1000 * Math.pow(2, attempt));
        console.log(`网络仍未恢复，${delay}ms 后重试`);
        setTimeout(() => attemptReconnect(attempt + 1), delay);
        
      } catch (error) {
        console.error(`重连失败: ${error.message}`);
        setConnectionStatus('error');
        setIsReconnecting(false);
      }
    };
    
    attemptReconnect(0);
  }, [isReconnecting, offlineMessages, sendMessageCore]);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);
  
  // 当messages数组变化时，重新计算总tokens数量
  useEffect(() => {
    const total = messages.reduce((sum, message) => {
      if (message.metrics && message.metrics.tokens_used) {
        return sum + message.metrics.tokens_used;
      }
      return sum;
    }, 0);
    setTotalTokens(total);
  }, [messages]);
  

  
  // 只在挂载时运行的初始化逻辑
  useEffect(() => {
    console.log('组件开始初始化');
    // 清理所有上下文相关状态
    setQuotedMessage(null);
    setEditingMessageId(null);
    setEditingMessageText('');
    setCurrentStreamingMessage(null);
    setExpandedThinkingChains({});
    setMarkedMessages(new Set());
    setMessages([]);
    setActiveTopic(null);
    console.log('上下文状态已清理');
    
    // 加载保存的主题设置
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
    console.log(`主题设置加载完成: ${savedTheme}`);
    
    // 监听网络状态变化
    const handleOnline = () => {
      setConnectionStatus('connected');
      console.log('网络连接已恢复');
      // 网络恢复时尝试重连
      reconnect();
    };
    
    const handleOffline = () => {
      setConnectionStatus('offline');
      console.log('网络连接已断开');
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    console.log('网络状态监听器已添加');
    
    return () => {
      // 清理网络状态监听器
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      console.log('网络状态监听器已移除');
      
      // 清除重连定时器
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
        console.log('重连定时器已清除');
      }

    };
  }, []); // 空依赖项，只运行一次
  
  // 获取模型列表
  useEffect(() => {
    console.log('开始获取对话模型列表');
    fetchConversationModels();
  }, []); // 空依赖项，只运行一次
  

  
  // 清除对话
  const clearConversation = useCallback(() => {
    // 清空消息列表，不设置欢迎消息
    setMessages([]);
    // 清空活跃话题
    setActiveTopic(null);
  }, []);
  
  // 处理话题选择
  const handleTopicSelect = useCallback(async (topic) => {
    if (!topic) {
      // 清空状态，显示空状态
      setActiveTopic(null);
      setMessages([]);
      return;
    }
    
    try {
      setIsLoadingMessages(true);
      setMessageSkeletons([1, 2]);
      
      // 调用后端API切换话题
      const response = await conversationApi.switchTopic(conversationId, topic.id);
      
      if (response && response.active_topic && response.messages) {
        // 设置活跃话题
        setActiveTopic(response.active_topic);
        
        // 转换消息格式
        const formattedMessages = response.messages.map(msg => {
          // 处理思维链信息
          let thinking = null;
          if (msg.thinking && msg.thinking.reasoning_steps) {
            // 将推理步骤转换为字符串
            thinking = msg.thinking.reasoning_steps.join('\n');
          }
          
          return {
            id: msg.id,
            sender: msg.role === 'user' ? 'user' : 'bot',
            text: msg.content,
            timestamp: new Date(msg.created_at),
            status: 'success',
            topicId: topic.id,
            thinking: thinking
          };
        });
        
        setMessages(formattedMessages);
      }
      
      setMessageSkeletons([]);
    } catch (error) {
      console.error('加载话题消息失败:', error);
      alert('加载话题消息失败，请重试');
    } finally {
      setIsLoadingMessages(false);
    }
  }, [conversationId]);
  
  // 检查模型状态
  const checkModelStatus = useCallback(async (model) => {
    try {
      setConnectionStatus('checking');
      // 这里可以添加模型状态检查的API调用
      // 暂时模拟检查
      await new Promise(resolve => setTimeout(resolve, 500));
      setConnectionStatus('connected');
      return true;
    } catch (error) {
      setConnectionStatus('error');
      return false;
    }
  }, []);
  
  // 模型选择变化处理
  const handleModelSelect = useCallback(async (model) => {
    setSelectedModel(model);
    await checkModelStatus(model);
  }, [checkModelStatus]);

  // 新建话题


  // 处理编辑消息
  const startEditingMessage = useCallback((messageId, currentText) => {
    setEditingMessageId(messageId);
    setEditingMessageText(currentText);
  }, []);
  
  // 保存编辑后的消息
  const saveEditingMessage = useCallback((messageId) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, text: editingMessageText, edited: true } 
        : msg
    ));
    setEditingMessageId(null);
    setEditingMessageText('');
  }, [editingMessageText]);
  
  // 取消编辑消息
  const cancelEditingMessage = useCallback(() => {
    setEditingMessageId(null);
    setEditingMessageText('');
  }, []);
  
  // 引用消息
  const quoteMessage = useCallback((message) => {
    setQuotedMessage(message);
  }, []);
  
  // 取消引用
  const cancelQuote = useCallback(() => {
    setQuotedMessage(null);
  }, []);
  
  // 切换思维链显示状态
  const toggleThinkingChain = useCallback((messageId) => {
    setExpandedThinkingChains(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  }, []);
  
  // 格式化时间
  const formatTime = useCallback((timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }, []);
  
  // 格式化持续时间
  const formatDuration = useCallback((ms) => {
    if (ms < 1000) {
      return `${ms}ms`;
    } else if (ms < 60000) {
      return `${(ms / 1000).toFixed(1)}s`;
    } else {
      const minutes = Math.floor(ms / 60000);
      const seconds = ((ms % 60000) / 1000).toFixed(0);
      return `${minutes}m ${seconds}s`;
    }
  }, []);
  
  // 发送按钮状态
  const sendButtonStatus = useMemo(() => {
    if (connectionStatus === 'sending' || isTyping) {
      return 'sending';
    } else if (!inputText.trim()) {
      return 'disabled';
    } else {
      return 'enabled';
    }
  }, [connectionStatus, isTyping, inputText]);
  
  // 发送按钮文本
  const sendButtonText = useMemo(() => {
    if (connectionStatus === 'sending' || isTyping) {
      return '发送中...';
    } else if (connectionStatus === 'offline') {
      return '离线';
    } else if (connectionStatus === 'error') {
      return '发送失败';
    } else {
      return '发送';
    }
  }, [connectionStatus, isTyping]);
  
  return (
    <div className={`chat-container ${theme}`}>
      {/* 主内容区域：话题侧边栏 + 聊天主区域 */}
      <div className="chat-content-wrapper">
        {/* 左侧侧边栏（话题和模型管理） */}
        <LeftSidebar
          conversationId={conversationId}
          activeTopic={activeTopic}
          onTopicSelect={handleTopicSelect}
          onTopicCreate={handleTopicCreate}
          onTopicDelete={(topicId) => {
            // 当删除当前活跃话题时，清空状态
            if (activeTopic && activeTopic.id === topicId) {
              setActiveTopic(null);
              setMessages([]);
              // 清理上下文相关状态
              setQuotedMessage(null);
              setEditingMessageId(null);
              setEditingMessageText('');
              setCurrentStreamingMessage(null);
              setExpandedThinkingChains({});
              setMarkedMessages(new Set());
            }
          }}
          refreshFlag={refreshTopicsFlag}
          onCollapseChange={setTopicSidebarCollapsed}
          models={availableModels}
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          collapsed={topicSidebarCollapsed}
        />
        
        {/* 右侧聊天主区域 */}
        <div className={`chat-main-wrapper ${topicSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
          {/* 聊天主区域 */}
          {messages.length === 0 && !activeTopic ? (
            // 空状态显示 - 显示简化版ChatMain，突出输入面板
            <div className="empty-chat-state-with-input">
              <div className="empty-state-header">
                <div className="empty-state-icon">💬</div>
                <h2>开始新对话</h2>
                <p>我是 Py Copilot，您的智能助手。请输入您的问题，我会为您提供帮助。</p>
              </div>
              
              {/* 直接显示输入面板 */}
              <form className="chat-input centered-input" onSubmit={handleSendMessage}>
                <div className="input-actions">
                  <button type="button" className="input-btn" title="联网搜索">🌐</button>
                  <button type="button" className="input-btn" title="知识库搜索">📚</button>
                  <button type="button" className="input-btn" title="翻译">🔤</button>
                  <button type="button" className="input-btn" title="上传文件">📁</button>
                  <button type="button" className={`input-btn ${enableThinkingChain ? 'active' : ''}`} title="思考模式" onClick={() => setEnableThinkingChain(!enableThinkingChain)}>🧠</button>
                  <button type="button" className="input-btn" title="表情">😊</button>
                  <button type="button" className="input-btn" title="录音">🎤</button>
                  <button type="button" className="input-btn" title="视频">🎥</button>
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
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage(e);
                      }
                    }}
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
          ) : (
            // 正常聊天界面
            <ChatMain
              messages={messages}
              inputText={inputText}
              setInputText={setInputText}
              onSendMessage={handleSendMessage}
              onClearConversation={clearConversation}
              messageSkeletons={messageSkeletons}
              isTyping={isTyping}
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
              quotedMessage={quotedMessage}
              cancelQuote={cancelQuote}
              formatTime={formatTime}
              formatDuration={formatDuration}
              MessageItem={MessageItem}
              MessageSkeleton={MessageSkeleton}
              TypingIndicator={TypingIndicator}
              activeTopic={activeTopic}
              enableThinkingChain={enableThinkingChain}
              setEnableThinkingChain={setEnableThinkingChain}
              selectedModel={selectedModel}
              availableModels={availableModels}
              onModelChange={setSelectedModel}
            />
          )}
        </div>
      </div>
      

    </div>
  );
};

// 使用React.memo包装组件，避免不必要的重渲染
export default React.memo(Chat);
