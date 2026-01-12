import React, { useState, useEffect, useRef } from 'react';
import { conversationApi } from '../utils/api';
import { API_BASE_URL } from '../utils/apiUtils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import ModelSelectDropdown from '../components/ModelManagement/ModelSelectDropdown';
import './chat.css';



// 自定义remark插件，用于在Markdown解析过程中移除表格前的空白行
const removeEmptyLinesBeforeTables = () => {
  return (tree) => {
    // 遍历Markdown AST，找到所有表格节点
    const findTables = (node, index, parent) => {
      if (node.type === 'table') {
        // 如果表格不是父节点的第一个子节点，检查前面的节点
        if (index > 0) {
          const previousNode = parent.children[index - 1];
          // 如果前面的节点是空白行，移除它
          if (previousNode.type === 'paragraph' && previousNode.children.length === 1 && previousNode.children[0].type === 'text' && !previousNode.children[0].value.trim()) {
            parent.children.splice(index - 1, 1);
          }
        }
      }
      // 递归遍历子节点
      if (node.children) {
        node.children.forEach((child, i) => findTables(child, i, node));
      }
    };
    
    findTables(tree, 0, { children: [tree] });
    
    return tree;
  };
};

// 简化的Markdown渲染组件，只处理基本的Markdown渲染
const MathRenderer = ({ content, isStreaming }) => {
  // 如果是流式响应，只显示纯文本
  if (isStreaming) {
    return (
      <div className="streaming-content">
        {content}
      </div>
    );
  }
  
  // 清理内容中的多余空白行，特别是表格前的空白
  let cleanedContent = content
    // 移除连续的空白行（保留单个空行）
    .replace(/\n{3,}/g, '\n\n')
    // 移除行首和行尾的多余空白
    .trim();
  
  // 只使用基本的Markdown渲染，不包含公式渲染
  return (
    <div className="markdown-renderer">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, removeEmptyLinesBeforeTables]}
        rehypePlugins={[rehypeRaw]}
      >
        {cleanedContent}
      </ReactMarkdown>
    </div>
  );
};

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: '你好！我是 **Py Copilot** 智能助手，现在支持调用真实的大语言模型进行对话！\n\n**新功能：**\n- ✅ 支持多种大模型（Ollama、DeepSeek等）\n- ✅ 智能回退机制（模型失败时自动切换）\n- ✅ 实时状态显示\n- ✅ 更好的错误处理\n\n请选择模型并开始对话吧！',
      timestamp: new Date(Date.now() - 3600000),
      status: 'success'
    }
  ]);
  
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [availableModels, setAvailableModels] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [lastResponseTime, setLastResponseTime] = useState(null);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [enableStreaming, setEnableStreaming] = useState(true);
  const [enableThinkingChain, setEnableThinkingChain] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState(null);
  const [topics, setTopics] = useState([]);
  const [activeTopic, setActiveTopic] = useState(null);
  const [showTopicPanel, setShowTopicPanel] = useState(false);
  const [newTopicTitle, setNewTopicTitle] = useState('');
  const [newTopicDescription, setNewTopicDescription] = useState('');
  const [expandedThinkingChains, setExpandedThinkingChains] = useState({}); // 管理各个消息的思维链展开/收缩状态
  const messagesEndRef = useRef(null);
  
  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  // 从API获取对话模型列表
  const fetchConversationModels = async () => {
    try {
      setIsLoadingModels(true);
      const response = await conversationApi.getConversationModels();
      if (response.status === 'success') {
        setAvailableModels(response.models);
        // 如果有默认模型，自动选择
        const defaultModel = response.models.find(model => model.is_default);
        if (defaultModel) {
          setSelectedModel(defaultModel);
        } else if (response.models.length > 0) {
          setSelectedModel(response.models[0]);
        }
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
  };
  
  // 话题管理函数
  const fetchTopics = async (conversationId = 1) => {
    try {
      const response = await conversationApi.getConversationTopics(conversationId);
      if (response.status === 'success') {
        setTopics(response.topics);
        
        // 获取活跃话题
        const activeResponse = await conversationApi.getActiveTopic(conversationId);
        if (activeResponse.status === 'success') {
          setActiveTopic(activeResponse.active_topic);
        }
      }
    } catch (error) {
      console.error('获取话题列表失败:', error);
    }
  };
  
  const createNewTopic = async (conversationId = 1) => {
    if (!newTopicTitle.trim()) {
      alert('请输入话题标题');
      return;
    }
    
    try {
      const response = await conversationApi.createTopic(
        conversationId, 
        newTopicTitle.trim(), 
        newTopicDescription.trim()
      );
      
      if (response.status === 'success') {
        setNewTopicTitle('');
        setNewTopicDescription('');
        setShowTopicPanel(false);
        await fetchTopics(conversationId);
        
        // 自动切换到新创建的话题
        await switchTopic(conversationId, response.topic.id);
      }
    } catch (error) {
      console.error('创建话题失败:', error);
      alert('创建话题失败，请重试');
    }
  };
  
  const switchTopic = async (conversationId, topicId) => {
    try {
      const response = await conversationApi.switchTopic(conversationId, topicId);
      if (response.status === 'success') {
        setActiveTopic(response.active_topic);
        
        // 清空当前消息，切换到新话题
        setMessages([
          {
            id: 1,
            sender: 'bot',
            text: `已切换到话题：**${response.active_topic.title}**\n\n${response.active_topic.description || '请开始新的对话吧！'}`,
            timestamp: new Date(),
            status: 'success'
          }
        ]);
      }
    } catch (error) {
      console.error('切换话题失败:', error);
      alert('切换话题失败，请重试');
    }
  };
  
  const deleteTopic = async (conversationId, topicId) => {
    if (!confirm('确定要删除这个话题吗？删除后将无法恢复。')) {
      return;
    }
    
    try {
      const response = await conversationApi.deleteTopic(conversationId, topicId);
      if (response.status === 'success') {
        await fetchTopics(conversationId);
        
        // 如果删除的是当前活跃话题，重置活跃话题
        if (activeTopic && activeTopic.id === topicId) {
          setActiveTopic(null);
        }
      }
    } catch (error) {
      console.error('删除话题失败:', error);
      alert('删除话题失败，请重试');
    }
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  useEffect(() => {
    // 组件挂载时获取模型列表和话题列表
    fetchConversationModels();
    fetchTopics();
    
    // 监听网络状态变化
    const handleOnline = () => {
      setConnectionStatus('connected');
      console.log('网络连接已恢复');
    };
    
    const handleOffline = () => {
      setConnectionStatus('offline');
      console.log('网络连接已断开');
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  // 清除对话
  const clearConversation = () => {
    setMessages([
      {
        id: 1,
        sender: 'bot',
        text: '对话已清除！请选择模型并开始新的对话。',
        timestamp: new Date(),
        status: 'success'
      }
    ]);
  };
  
  // 检查模型状态
  const checkModelStatus = async (model) => {
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
  };
  
  // 模型选择变化处理
  const handleModelSelect = async (model) => {
    setSelectedModel(model);
    await checkModelStatus(model);
  };
  
  // 流式响应处理
  const handleStreamingResponse = async (text, conversationId = 1) => {
    try {
      const messageData = {
        content: text,
        use_llm: true,
        model_name: selectedModel ? selectedModel.model_id : 'moonshotai/Kimi-K2-Thinking',
        enable_thinking_chain: enableThinkingChain
      };

      // 创建流式消息对象，使用时间戳+随机数确保唯一ID
        const streamingMessage = {
            id: Date.now() + Math.floor(Math.random() * 1000),
            sender: 'bot',
            text: '',
            timestamp: new Date(),
            status: 'streaming',
            model: selectedModel ? selectedModel.model_name : '未知模型',
            isStreaming: true,
            thinking: null // 初始不显示思维链信息，等待后端发送实际的思维链步骤
        };

      setCurrentStreamingMessage(streamingMessage);
      setMessages(prevMessages => [...prevMessages, streamingMessage]);

      // 使用fetch API的流式响应功能
      const response = await fetch(`${API_BASE_URL}/v1/conversations/${conversationId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData)
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
                // 更新思维链显示
                setCurrentStreamingMessage(prev => ({
                  ...prev,
                  thinking: data.content
                }));
                
                // 更新消息列表中的思维链
                setMessages(prevMessages => 
                  prevMessages.map(msg => 
                    msg.id === streamingMessage.id 
                      ? { ...msg, thinking: data.content }
                      : msg
                  )
                );
                break;
                
              case 'content':
                // 更新消息内容
                setCurrentStreamingMessage(prev => ({
                  ...prev,
                  text: data.content
                }));
                
                // 更新消息列表中的消息，使用防抖机制避免频繁重渲染
                setMessages(prevMessages => 
                  prevMessages.map(msg => 
                    msg.id === streamingMessage.id 
                      ? { ...msg, text: data.content }
                      : msg
                  )
                );
                

                break;
                
              case 'complete':
                // 流式响应完成
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
      
      const errorMessage = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        sender: 'bot',
        text: '流式响应功能暂时不可用，请使用普通模式。',
        timestamp: new Date(),
        status: 'error'
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      setConnectionStatus('error');
    }
  };

  // 处理发送消息
  const handleSendMessage = async (e) => {
    e.preventDefault();
    const text = inputText.trim();
    if (!text) return;
    
    // 检查网络连接
    if (!navigator.onLine) {
      const offlineMessage = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        sender: 'bot',
        text: '网络连接已断开，请检查您的网络连接后重试。',
        timestamp: new Date(),
        status: 'error'
      };
      setMessages(prevMessages => [...prevMessages, offlineMessage]);
      setConnectionStatus('offline');
      return;
    }
    
    setIsTyping(true);
    setConnectionStatus('sending');
    const startTime = Date.now();
    
    // 添加用户消息到列表，使用时间戳+随机数确保唯一ID
    const newUserMessage = {
      id: Date.now() + Math.floor(Math.random() * 1000),
      sender: 'user',
      text: text,
      timestamp: new Date()
    };
    
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    setInputText('');
    
    try {
      // 根据设置选择响应模式
      if (enableStreaming) {
        // 使用流式响应
        await handleStreamingResponse(text, 1);
        setIsTyping(false);
        return;
      }
      
      // 使用普通模式
      const messageData = {
        content: text,
        use_llm: true,
        model_name: selectedModel ? selectedModel.model_id : 'moonshotai/Kimi-K2-Thinking'
      };

      // 设置请求超时（30秒）
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('请求超时，请检查网络连接或稍后重试。')), 30000);
      });
      
      const responsePromise = conversationApi.sendMessage(1, messageData);
      const response = await Promise.race([responsePromise, timeoutPromise]);
      
      // 计算响应时间
      const responseTime = Date.now() - startTime;
      setLastResponseTime(responseTime);
      
      // 从响应中提取助手回复和状态信息
      const botReply = response.assistant_message?.content || '抱歉，我无法生成回复。';
      const fallbackInfo = response.fallback_info;
      const tokensUsed = response.tokens_used;
      const executionTime = response.execution_time_ms;
      
      const newBotMessage = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        sender: 'bot',
        text: botReply,
        timestamp: new Date(),
        status: 'success',
        model: response.model || (selectedModel ? selectedModel.model_name : '未知模型'),
        fallbackInfo: fallbackInfo,
        tokensUsed: tokensUsed,
        executionTime: executionTime,
        responseTime: responseTime
      };
      
      setMessages(prevMessages => [...prevMessages, newBotMessage]);
      setConnectionStatus('connected');
    } catch (error) {
      // 添加更详细的错误日志
      console.error('发送消息时出错:', JSON.stringify({ message: error.message, stack: error.stack, name: error.name }, null, 2));
      
      // 根据错误类型提供更友好的错误消息
      let errorMessageText;
      if (error.message.includes('timeout') || error.message.includes('超时')) {
        errorMessageText = '请求超时，请检查网络连接或稍后重试。';
      } else if (error.response?.status === 404) {
        errorMessageText = '服务暂时不可用，请稍后再试。';
      } else if (error.response?.status >= 500) {
        errorMessageText = '服务器内部错误，请联系管理员。';
      } else if (error.response?.data?.detail) {
        errorMessageText = error.response.data.detail;
      } else {
        errorMessageText = '抱歉，我暂时无法处理你的请求。请稍后再试。';
      }
      
      const errorMessage = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        sender: 'bot',
        text: errorMessageText,
        timestamp: new Date(),
        status: 'error'
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      setConnectionStatus('error');
    } finally {
      setIsTyping(false);
    }
  };
  
  // 格式化时间
  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // 格式化持续时间
  const formatDuration = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  // 获取发送按钮状态
  const getSendButtonStatus = () => {
    if (connectionStatus === 'sending') return 'sending';
    if (!inputText.trim() || connectionStatus === 'error') return 'disabled';
    return 'ready';
  };

  // 获取发送按钮文本
  const getSendButtonText = () => {
    if (connectionStatus === 'sending') return '发送中';
    return '发送';
  };

  // 切换思维链的展开/收缩状态
  const toggleThinkingChain = (messageId) => {
    setExpandedThinkingChains(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-title">
          <div className="bot-avatar">🤖</div>
          <div>
            <h2>Py Copilot</h2>
            <span className="chat-subtitle">智能大模型对话助手</span>
          </div>
        </div>
        
        <div className="status-indicator">
          <div className={`status-dot ${connectionStatus}`}></div>
          <span className="status-text">
            {connectionStatus === 'connected' && '已连接'}
            {connectionStatus === 'checking' && '检查中...'}
            {connectionStatus === 'sending' && '发送中...'}
            {connectionStatus === 'error' && '连接错误'}
            {connectionStatus === 'offline' && '离线'}
          </span>
          {lastResponseTime && connectionStatus === 'connected' && (
            <span className="response-time">{lastResponseTime}ms</span>
          )}
        </div>
        
        <div className="model-selector">
          <label>模型:</label>
          <div className="model-dropdown-container">
            {isLoadingModels ? (
              <div className="model-loading">加载中...</div>
            ) : (
              <ModelSelectDropdown
                models={availableModels}
                selectedModel={selectedModel}
                onModelSelect={handleModelSelect}
                className="chat-model-dropdown"
                placeholder="请选择对话模型"
                disabled={connectionStatus === 'sending'}
              />
            )}
          </div>
        </div>
        
        <div className="chat-actions">
          <div className="streaming-controls">
            <label className="toggle-label">
              <input 
                type="checkbox" 
                checked={enableStreaming} 
                onChange={(e) => setEnableStreaming(e.target.checked)}
                disabled={connectionStatus === 'sending'}
              />
              <span className="toggle-text">流式响应</span>
            </label>
            <label className="toggle-label">
              <input 
                type="checkbox" 
                checked={enableThinkingChain} 
                onChange={(e) => setEnableThinkingChain(e.target.checked)}
                disabled={connectionStatus === 'sending' || !enableStreaming}
              />
              <span className="toggle-text">思维链</span>
            </label>
          </div>
          <div className="topic-management">
            <button 
              className={`topic-toggle-btn ${showTopicPanel ? 'active' : ''}`}
              title="话题管理"
              onClick={() => setShowTopicPanel(!showTopicPanel)}
              disabled={connectionStatus === 'sending'}
            >
              <span className="topic-toggle-icon">📚</span>
              <span>话题</span>
              {activeTopic && <span className="active-topic-badge">{activeTopic.title}</span>}
            </button>
          </div>
          <button 
            className="action-btn" 
            title="清除对话"
            onClick={clearConversation}
            disabled={connectionStatus === 'sending'}
          >🗑️</button>
          <button className="action-btn" title="设置">⚙️</button>
        </div>
      </div>
      
      {/* 话题面板 */}
      {showTopicPanel && (
        <div className="topic-panel">
          <div className="topic-panel-header">
            <h3 className="topic-panel-title">话题管理</h3>
            <button 
              className="topic-panel-close" 
              onClick={() => setShowTopicPanel(false)}
              title="关闭话题面板"
            >✕</button>
          </div>
          
          <div className="topic-panel-content">
            <ul className="topic-list">
              {topics.length === 0 ? (
                <li className="topic-item">
                  <div className="topic-info">
                    <div className="topic-title">暂无话题</div>
                    <div className="topic-description">请创建新话题开始对话</div>
                  </div>
                </li>
              ) : (
                topics.map(topic => (
                  <li 
                    key={topic.id} 
                    className={`topic-item ${activeTopic && activeTopic.id === topic.id ? 'active' : ''}`}
                    onClick={() => switchTopic(1, topic.id)}
                  >
                    <div className="topic-info">
                      <div className="topic-title">{topic.title}</div>
                      {topic.description && (
                        <div className="topic-description">{topic.description}</div>
                      )}
                    </div>
                    <div className="topic-actions">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          switchTopic(1, topic.id);
                        }}
                        className="topic-action-btn edit"
                        title="切换到该话题"
                      >↻</button>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteTopic(1, topic.id);
                        }}
                        className="topic-action-btn delete"
                        title="删除话题"
                      >🗑️</button>
                    </div>
                  </li>
                ))
              )}
            </ul>
            
            <div className="topic-create-section">
              <div className="topic-create-form">
                <div className="topic-input-group">
                  <label className="topic-input-label">话题标题</label>
                  <input
                    type="text"
                    placeholder="请输入话题标题"
                    value={newTopicTitle}
                    onChange={(e) => setNewTopicTitle(e.target.value)}
                    className="topic-input"
                  />
                </div>
                <div className="topic-input-group">
                  <label className="topic-input-label">话题描述（可选）</label>
                  <input
                    type="text"
                    placeholder="请输入话题描述"
                    value={newTopicDescription}
                    onChange={(e) => setNewTopicDescription(e.target.value)}
                    className="topic-input"
                  />
                </div>
                <button 
                  onClick={createNewTopic}
                  className="topic-create-btn"
                  disabled={!newTopicTitle.trim()}
                >
                  创建新话题
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div className="chat-messages">
        {messages.map(message => {
          // 检测是否包含表格
          const hasTable = /\|.*\|/.test(message.text);
          
          // 普通消息渲染
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
                
                <MathRenderer 
                  content={message.text} 
                  isStreaming={message.isStreaming}
                />
                {message.fallbackInfo && (
                  <div className="fallback-info">
                    🔄 {message.fallbackInfo}
                  </div>
                )}
                {message.metrics && (
                  <div className="message-metrics">
                    {message.metrics.execution_time && (
                      <span className="metric-item">
                        ⏱️ <span className="metric-value">{formatDuration(message.metrics.execution_time)}</span>
                      </span>
                    )}
                    {message.metrics.tokens_used && (
                      <span className="metric-item">
                        📊 <span className="metric-value">{message.metrics.tokens_used} tokens</span>
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
              </div>
            </div>
            {message.sender === 'user' && <div className="message-avatar">👤</div>}
          </div>
        );
      })}
        
        {isTyping && (
          <div className="message bot-message">
            <div className="message-avatar">🤖</div>
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form className="chat-input" onSubmit={handleSendMessage}>
        <div className="input-actions">
          <button type="button" className="input-btn">🎤</button>
          <button type="button" className="input-btn">📷</button>
          <button type="button" className="input-btn">📁</button>
          <button type="button" className="input-btn">✨</button>
          <div className="markdown-hint" title="支持 Markdown 格式：**粗体**、*斜体*、# 标题、- 列表等">MD</div>
        </div>
        <textarea
          placeholder="输入消息... 支持 Markdown 格式和数学公式($公式$ 或 $$块公式$$)，使用 Shift+Enter 换行"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage(e)}
          className="message-input"
          rows="1"
          style={{ resize: 'none', overflowY: 'auto' }}
        />
        <button 
          type="submit" 
          className={`send-btn ${getSendButtonStatus()}`}
          disabled={getSendButtonStatus() === 'disabled'}
        >
          <span className="send-icon">
            {getSendButtonStatus() === 'sending' ? '⏳' : '➤'}
          </span>
          <span className="send-text">{getSendButtonText()}</span>
        </button>
      </form>
    </div>
  );
};

export default Chat;