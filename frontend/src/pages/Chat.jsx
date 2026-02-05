import React, { useState, useEffect, useRef, useCallback } from 'react';
import { conversationApi, defaultModelApi, capabilityApi } from '../utils/api';
import { API_BASE_URL } from '../utils/apiUtils';
import emojis from '../utils/emojis';
import LeftSidebar from '../components/LeftSidebar';
import ChatMain from '../components/ChatMain';
import ModelSelectDropdown from '../components/ModelManagement/ModelSelectDropdown';
import ModelDataManager from '../services/modelDataManager';
import './chat.css';

// 导入新的组件
import MessageItem from '../components/MessageItem';
import MessageSkeleton from '../components/MessageSkeleton';
import TypingIndicator from '../components/TypingIndicator';

// 导入工具函数
import { 
  calculateTokens, 
  getErrorDetails, 
  formatTime, 
  formatDuration, 
  formatFileSize 
} from '../utils/chatUtils.js';

const Chat = () => {
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  // 加载模型数据
  const loadModels = useCallback(async () => {
    if (modelsLoadedRef.current) return;
    
    setIsLoadingModels(true);
    try {
      // 加载所有模型
      const allModels = await ModelDataManager.loadModels('chat');
      
      // 按聊天相关能力筛选模型
      // 使用真实的能力数据从数据库中查询
      
      // 首先获取所有聊天相关的能力
      let chatCapabilities = [];
      try {
        const capabilitiesResponse = await capabilityApi.getAll({ capability_type: 'chat' });
        chatCapabilities = capabilitiesResponse.data || [];
      } catch (error) {
        console.error('获取聊天相关能力失败:', error);
        // 如果获取能力失败，使用备选方案
        chatCapabilities = [];
      }
      
      // 筛选聊天相关的模型
      const chatRelatedModels = [];
      
      // 为每个模型获取其能力并检查是否与聊天相关
      for (const model of allModels) {
        try {
          // 获取模型的能力
          const modelCapabilities = await capabilityApi.getModelCapabilities(model.id);
          
          // 检查模型是否具有聊天相关能力
          const hasChatCapability = modelCapabilities.some(capability => {
            // 检查能力是否与聊天相关
            const capabilityName = capability.name || capability.capability?.name || '';
            const capabilityType = capability.capability_type || capability.capability?.capability_type || '';
            
            return capabilityType === 'chat' || 
                   capabilityName.toLowerCase().includes('chat') ||
                   capabilityName.toLowerCase().includes('conversation') ||
                   capabilityName.toLowerCase().includes('dialog');
          });
          
          // 如果模型具有聊天相关能力，将其添加到筛选列表中
          if (hasChatCapability) {
            chatRelatedModels.push(model);
          }
        } catch (error) {
          console.error(`获取模型 ${model.model_name} 的能力失败:`, error);
          // 如果获取能力失败，跳过该模型
          continue;
        }
      }
      
      setAvailableModels(chatRelatedModels || []);
      
      // 首先尝试获取系统中的默认聊天模型
      try {
        const defaultModelConfig = await defaultModelApi.getSceneDefaultModel('chat');
        if (defaultModelConfig && defaultModelConfig.model_id) {
          // 从所有模型列表中找到对应的系统默认模型
          const defaultModelFromAll = allModels.find(m => m.id === defaultModelConfig.model_id);
          if (defaultModelFromAll) {
            
            // 检查该模型是否已经在筛选后的列表中
            let defaultModel = chatRelatedModels.find(m => m.id === defaultModelConfig.model_id);
            
            // 如果系统默认模型不在筛选后的列表中，将其添加进去
            if (!defaultModel) {
              chatRelatedModels.unshift(defaultModelFromAll);
              setAvailableModels(chatRelatedModels);
              defaultModel = defaultModelFromAll;
            }
            
            setSelectedModel(defaultModel);
            localStorage.setItem('selectedModel', JSON.stringify(defaultModel));
            modelsLoadedRef.current = true;
            return;
          } else {
            console.warn('系统默认模型不在所有模型列表中:', defaultModelConfig.model_id);
          }
        }
      } catch (error) {
        console.error('获取系统默认模型失败:', error);
        // 继续使用其他逻辑
      }
      
      // 如果没有获取到系统默认模型，从localStorage获取之前选择的模型
      const savedModel = localStorage.getItem('selectedModel');
      if (savedModel) {
        try {
          const parsedModel = JSON.parse(savedModel);
          // 检查保存的模型是否仍然可用（在筛选后的列表中）
          const modelExists = chatRelatedModels.some(m => m.id === parsedModel.id);
          if (modelExists) {

            setSelectedModel(parsedModel);
          } else if (chatRelatedModels.length > 0) {
            // 如果保存的模型不可用，使用筛选后列表的第一个模型作为默认值
            setSelectedModel(chatRelatedModels[0]);
            localStorage.setItem('selectedModel', JSON.stringify(chatRelatedModels[0]));
          }
        } catch (error) {
          console.error('解析保存的模型失败:', error);
          // 如果解析失败，使用筛选后列表的第一个模型作为默认值
          if (chatRelatedModels.length > 0) {
            setSelectedModel(chatRelatedModels[0]);
            localStorage.setItem('selectedModel', JSON.stringify(chatRelatedModels[0]));
          }
        }
      } else if (chatRelatedModels.length > 0) {
        // 如果没有保存的模型，使用筛选后列表的第一个模型作为默认值
        setSelectedModel(chatRelatedModels[0]);
        localStorage.setItem('selectedModel', JSON.stringify(chatRelatedModels[0]));
      }
      
      modelsLoadedRef.current = true;
    } catch (error) {
      console.error('加载模型失败:', error);
      setAvailableModels([]);
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  // 组件加载时加载模型数据
  useEffect(() => {
    loadModels();
  }, [loadModels]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  
  // 添加日志来追踪 uploadedFiles 的变化
  useEffect(() => {
    console.log('========== uploadedFiles 状态变化 ==========');
    console.log('当前文件数量:', uploadedFiles.length);
    console.log('当前文件列表:', uploadedFiles);
    console.log('================================');
  }, [uploadedFiles]);
   
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [lastResponseTime, setLastResponseTime] = useState(null);
  const [enableStreaming, setEnableStreaming] = useState(false);
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
  const [refreshTopicsFlag, setRefreshTopicsFlag] = useState(false); // 控制话题列表刷新的标志
  const messagesEndRef = useRef(null); // 滚动到底部的引用
  const reconnectTimerRef = useRef(null); // 重连定时器引用
  const modelsLoadedRef = useRef(false); // 防止重复加载模型列表
  const [isEmojiPickerOpen, setIsEmojiPickerOpen] = useState(false); // emoji选择器是否打开
  const [selectedEmojiCategory, setSelectedEmojiCategory] = useState(0); // 当前选中的emoji分类
  
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
  const preloadMessages = useCallback(async (conversationId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/conversations/${conversationId}/messages`);
      const data = await response.json();
      setPreloadedMessages(prev => ({
        ...prev,
        [conversationId]: data.messages
      }));
    } catch (error) {
      console.error('预加载消息失败:', error);
    }
  }, []);

  // 加载话题消息
  const loadTopicMessages = useCallback(async (topicId) => {
    if (!conversationId || !topicId) return;
    
    try {
      setIsLoadingMessages(true);
      setMessageSkeletons([1, 2, 3]);
      
      const response = await conversationApi.getTopicMessages(conversationId, topicId);
      
      if (response && response.messages) {
        setMessages(response.messages);
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error('加载话题消息失败:', error);
      setMessages([]);
    } finally {
      setMessageSkeletons([]);
      setIsLoadingMessages(false);
    }
  }, [conversationId]);

  // 当活跃话题变化时，加载对应话题的消息
  useEffect(() => {
    if (activeTopic) {
      loadTopicMessages(activeTopic.id);
    }
  }, [activeTopic, loadTopicMessages]);

  // 处理发送消息
  const handleSendMessage = useCallback(async (e) => {
    e.preventDefault();
    
    if (!inputText.trim()) return;
    
    // 创建临时消息（移到try块外面，确保在catch块中也能访问）
    const tempMessage = {
      id: Date.now(),
      sender: 'user',
      text: inputText.trim(),
      timestamp: new Date(),
      status: 'sending',
      conversationId: conversationId,
      topicId: activeTopic?.id || null,
      attachedFiles: uploadedFiles, // 添加文件信息
      metrics: {
        tokens_used: calculateTokens(inputText.trim())
      }
    };
    
    try {
      console.log('========== 开始发送消息 ==========');
      console.log('消息内容:', inputText);
      console.log('已上传文件数量:', uploadedFiles.length);
      console.log('已上传文件列表:', uploadedFiles);
      console.log('================================');
      
      // 只记录关键步骤的日志
      console.log(`开始发送消息: ${inputText.substring(0, 50)}${inputText.length > 50 ? '...' : ''}`);
      
      // 添加到消息列表
      setMessages(prev => [...prev, tempMessage]);
      scrollToBottom();
      
      // 检查网络连接
      if (!navigator.onLine) {
        console.warn('网络离线，将消息加入离线队列');
        // 离线状态，加入离线消息队列
        setOfflineMessages(prev => [...prev, { text: inputText.trim() }]);
        // 更新消息状态为离线
        setMessages(prev => prev.map(msg => 
          msg.id === tempMessage.id 
            ? { ...msg, status: 'offline' }
            : msg
        ));
        setInputText('');
        return;
      }
      
      // 在线状态，发送消息
      if (enableStreaming) {
        // 流式响应已在handleStreamingResponse中记录日志
        console.log('使用流式响应发送消息');
        await handleStreamingResponse(inputText.trim(), conversationId, activeTopic?.id, tempMessage);
      } else {
        // 普通响应
        console.log('使用普通响应发送消息');
        const messageData = {
          content: inputText.trim(),
          use_llm: true,
          model_name: selectedModel ? selectedModel.model_id : 'moonshotai/Kimi-K2-Thinking',
          enable_thinking_chain: enableThinkingChain,
          attached_files: uploadedFiles.map(f => f.id)
        };
        
        // 只有在有活跃话题时才添加topic_id
        if (activeTopic?.id) {
          messageData.topic_id = activeTopic.id;
        }
        
        console.log('发送消息数据:', JSON.stringify(messageData, null, 2));
        
        const response = await fetch(`${API_BASE_URL}/v1/conversations/${conversationId}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(messageData)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('消息发送响应:', result);
        
        // 计算AI回复的tokens数量
        const aiTokens = calculateTokens(result.assistant_message.content);
        
        // 更新临时消息为成功状态
        setMessages(prev => prev.map(msg => 
          msg.id === tempMessage.id 
            ? { 
                ...msg, 
                status: 'success',
                text: result.assistant_message.content,
                metrics: {
                  tokens_used: aiTokens
                }
              } 
            : msg
        ));
        
        // 添加AI回复消息
        const aiMessage = {
          id: result.assistant_message.id,
          sender: 'bot',
          text: result.assistant_message.content,
          timestamp: new Date(),
          status: 'success',
          model: selectedModel ? selectedModel.model_name : '未知模型',
          conversationId: conversationId,
          topicId: activeTopic?.id || null,
          metrics: {
            tokens_used: aiTokens
          }
        };
        
        setMessages(prev => [...prev, aiMessage]);
        setConnectionStatus('connected');
        
        // 清空输入框和已上传文件列表
        setInputText('');
        setUploadedFiles([]);
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      const errorDetails = getErrorDetails(error);
      
      // 更新临时消息为错误状态
      setMessages(prev => prev.map(msg => 
        msg.id === tempMessage.id 
          ? { 
              ...msg, 
              status: 'error',
              text: errorDetails.message,
              errorType: errorDetails.type,
              recoverySuggestion: errorDetails.recovery,
              severity: errorDetails.severity
            } 
          : msg
      ));
      
      setConnectionStatus('error');
    }
  }, [inputText, uploadedFiles, enableStreaming, enableThinkingChain, selectedModel, conversationId, activeTopic, scrollToBottom]);

  // 流式响应处理
  const handleStreamingResponse = useCallback(async (text, conversationId = 1, topicId = null, tempMessage = null) => {
    try {
      console.log('========== 流式响应处理 ==========');
      console.log('消息内容:', text);
      console.log('已上传文件数量:', uploadedFiles.length);
      console.log('已上传文件列表:', uploadedFiles);
      console.log('================================');
      
      // 构建消息数据，在新话题状态下不传递topic_id
      const messageData = {
        content: text,
        use_llm: true,
        model_name: selectedModel ? selectedModel.model_id : 'moonshotai/Kimi-K2-Thinking',
        enable_thinking_chain: enableThinkingChain,
        attached_files: uploadedFiles.map(f => f.id)
      };
      
      console.log('流式响应消息数据:', JSON.stringify(messageData, null, 2));
      
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
            
            // 处理后端返回的不同数据格式
            if (data.status === 'streaming' && data.chunk) {
              // 处理后端返回的流式文本块
              const content = data.chunk;
              fullResponse += content;
              
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
            } else if (data.status === 'completed') {
              // 处理后端返回的完成响应
              streamCompleted = true;
              setCurrentStreamingMessage(null);
              
              // 检查是否有assistant_message，如果有，使用其内容
              let responseText = fullResponse;
              if (data.assistant_message && data.assistant_message.content) {
                responseText = data.assistant_message.content;
              }
              
              // 如果仍然没有内容，设置默认提示信息
              if (!responseText) {
                responseText = '抱歉，我暂时无法为您提供相关信息。请尝试提供更多上下文或换一种方式提问。';
              }
              
              // 计算AI回复的tokens数量
              const aiTokens = calculateTokens(responseText);
              
              setMessages(prevMessages => 
                prevMessages.map(msg => 
                  msg.id === streamingMessage.id 
                    ? { 
                        ...msg, 
                        text: responseText,
                        status: 'success', 
                        isStreaming: false,
                        metrics: {
                          tokens_used: aiTokens
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
              
              // 清空已上传文件列表
              setUploadedFiles([]);
            } else if (data.status === 'error') {
              // 处理后端返回的错误响应
              streamCompleted = true;
              setCurrentStreamingMessage(null);
              
              setMessages(prevMessages => 
                prevMessages.map(msg => 
                  msg.id === streamingMessage.id 
                    ? { 
                        ...msg, 
                        text: data.error || '流式响应发生错误', 
                        status: 'error',
                        isStreaming: false 
                      }
                    : msg
                )
              );
              setConnectionStatus('error');
            } else if (data.type) {
              // 处理前端期望的格式（兼容旧格式）
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
                  
                  // 检查是否有内容，如果没有，设置默认提示信息
                  const responseText = fullResponse || '抱歉，我暂时无法为您提供相关信息。请尝试提供更多上下文或换一种方式提问。';
                  
                  setMessages(prevMessages => 
                    prevMessages.map(msg => {
                      // 更新流式消息状态
                      if (msg.id === streamingMessage.id) {
                        return {
                          ...msg, 
                          text: responseText,
                          status: 'success', 
                          isStreaming: false,
                          metrics: {
                            ...(data.metrics || {}),
                            tokens_used: data.metrics?.tokens_used || aiTokens
                          }
                        };
                      }
                      // 更新用户消息状态为成功
                      if (tempMessage && msg.id === tempMessage.id) {
                        return {
                          ...msg,
                          status: 'success'
                        };
                      }
                      return msg;
                    })
                  );
                  // 设置思维链默认收缩状态
                  setExpandedThinkingChains(prev => ({ ...prev, [streamingMessage.id]: false }));
                  setConnectionStatus('connected');
                  
                  // 刷新话题列表，更新消息数量
                  refreshTopics();
                  
                  // 清空已上传文件列表
                  setUploadedFiles([]);

                  break;
                  
                case 'error':
                  // 处理错误
                  streamCompleted = true;
                  setCurrentStreamingMessage(null);
                  
                  setMessages(prevMessages => 
                    prevMessages.map(msg => {
                      // 更新流式消息状态
                      if (msg.id === streamingMessage.id) {
                        return {
                          ...msg, 
                          text: data.content || '流式响应发生错误', 
                          status: 'error',
                          isStreaming: false 
                        };
                      }
                      // 更新用户消息状态为错误
                      if (tempMessage && msg.id === tempMessage.id) {
                        return {
                          ...msg,
                          status: 'error'
                        };
                      }
                      return msg;
                    })
                  );
                  setConnectionStatus('error');
                  break;
                  
                default:
                  break;
              }
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
        
        // 检查是否有内容，如果没有，设置默认提示信息
        const responseText = fullResponse || '抱歉，我暂时无法为您提供相关信息。请尝试提供更多上下文或换一种方式提问。';
        
        setMessages(prevMessages => 
          prevMessages.map(msg => 
            msg.id === streamingMessage.id 
              ? { 
                  ...msg, 
                  text: responseText,
                  status: 'success', 
                  isStreaming: false 
                } 
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
      
      setMessages(prevMessages => 
        prevMessages.map(msg => {
          // 更新用户消息状态为错误
          if (tempMessage && msg.id === tempMessage.id) {
            return {
              ...msg,
              status: 'error',
              text: errorDetails.message,
              errorType: errorDetails.type,
              recoverySuggestion: errorDetails.recovery,
              severity: errorDetails.severity
            };
          }
          return msg;
        }).concat(errorMessage)
      );
      setConnectionStatus('error');
    }
  }, [selectedModel, enableThinkingChain, activeTopic, uploadedFiles]);

  // 处理选择模型
  const handleSelectModel = useCallback((model) => {
    setSelectedModel(model);
    localStorage.setItem('selectedModel', JSON.stringify(model));
  }, []);

  // 清除对话
  const clearConversation = useCallback(() => {
    setMessages([]);
    setUploadedFiles([]);
  }, []);

  // 复制消息
  const copyMessage = useCallback((message) => {
    navigator.clipboard.writeText(message.text);
  }, []);

  // 重新生成消息
  const regenerateMessage = useCallback((message) => {
    // 这里可以实现重新生成逻辑
    console.log('重新生成消息:', message);
  }, []);

  // 翻译消息
  const translateMessage = useCallback((message) => {
    // 这里可以实现翻译逻辑
    console.log('翻译消息:', message);
  }, []);

  // 删除消息
  const deleteMessage = useCallback((message) => {
    setMessages(prev => prev.filter(m => m.id !== message.id));
  }, []);

  // 保存消息
  const saveMessage = useCallback((message) => {
    // 这里可以实现保存逻辑
    console.log('保存消息:', message);
  }, []);

  // 引用消息
  const quoteMessage = useCallback((message) => {
    setQuotedMessage(message);
    setInputText(`${message.text}\n`);
  }, []);

  // 取消引用
  const cancelQuote = useCallback(() => {
    setQuotedMessage(null);
  }, []);

  // 开始编辑消息
  const startEditingMessage = useCallback((messageId, messageText) => {
    setEditingMessageId(messageId);
    setEditingMessageText(messageText);
  }, []);

  // 保存编辑消息
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

  // 切换消息标记
  const toggleMessageMark = useCallback((messageId) => {
    setMarkedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  }, []);

  // 切换思维链显示
  const toggleThinkingChain = useCallback((messageId) => {
    setExpandedThinkingChains(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  }, []);

  // 刷新话题
  const refreshTopics = useCallback(() => {
    // 这里可以实现刷新话题的逻辑
    console.log('刷新话题列表');
  }, []);

  // 切换emoji选择器
  const toggleEmojiPicker = useCallback(() => {
    setIsEmojiPickerOpen(!isEmojiPickerOpen);
  }, [isEmojiPickerOpen]);

  // 处理emoji分类切换
  const handleEmojiCategoryChange = useCallback((index) => {
    setSelectedEmojiCategory(index);
  }, []);

  // 主渲染部分
  return (
    <div className="chat-container">
      {/* 左侧边栏 */}
      <LeftSidebar 
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        conversationId={conversationId}
        activeTopic={activeTopic}
        setActiveTopic={setActiveTopic}
        refreshFlag={refreshTopicsFlag}
        setRefreshFlag={setRefreshTopicsFlag}
      />

      {/* 主聊天区域 */}
      <div className="chat-main-container">
        {/* 聊天主区域 */}
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
          MessageItem={MessageItem}
          MessageSkeleton={MessageSkeleton}
          TypingIndicator={TypingIndicator}
          activeTopic={activeTopic}
          enableThinkingChain={enableThinkingChain}
          setEnableThinkingChain={setEnableThinkingChain}
          selectedModel={selectedModel}
          availableModels={availableModels}
          onModelChange={setSelectedModel}
          isLoadingModels={isLoadingModels}
          uploadedFiles={uploadedFiles}
          setUploadedFiles={setUploadedFiles}
        />
      </div>
    </div>
  );
};

// 使用React.memo包装组件，避免不必要的重渲染
export default React.memo(Chat);