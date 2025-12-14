import React, { useState, useEffect, useRef } from 'react';
import { conversationApi } from '../utils/api';
import ReactMarkdown from 'react-markdown';
import 'katex/dist/katex.min.css';
import '../styles/katex.css';
import { InlineMath, BlockMath } from 'react-katex';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import './chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: '你好！我是 **Py Copilot** 智能助手，有什么可以帮到你的吗？\n\n> 现在支持 Markdown 格式和数学公式了！',
      timestamp: new Date(Date.now() - 3600000)
    },
    {
      id: 2,
      sender: 'user',
      text: '你能展示一些数学公式吗？',
      timestamp: new Date(Date.now() - 3500000)
    },
    {
      id: 3,
      sender: 'bot',
      text: '# 数学公式示例\n\n## 基础数学\n- 行内公式: $E = mc^2$ 和 $a^2 + b^2 = c^2$\n- 块级公式:\n\n$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$\n\n$$\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}$$\n\n$$\\lim_{x \\to \\infty} (1 + \\frac{1}{x})^x = e$$\n\n## 物理公式\n- 牛顿第二定律: $F = ma$\n- 万有引力定律:\n\n$$F = G\\frac{m_1m_2}{r^2}$$\n\n- 麦克斯韦方程:\n\n$$\\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\epsilon_0}$$\n\n## 化学公式\n- 水的化学式: $H_2O$\n- 硫酸: $H_2SO_4$\n- 反应式:\n\n$$2H_2 + O_2 \\rightarrow 2H_2O$$\n\n$$CH_4 + 2O_2 \\rightarrow CO_2 + 2H_2O$$\n\n$$N_2 + 3H_2 \\rightleftharpoons 2NH_3$$\n\n## 高级数学\n- 矩阵:\n\n$$\\begin{pmatrix} a & b \\ c & d \\end{pmatrix}$$\n\n- 微分方程:\n\n$$\\frac{d^2y}{dx^2} + \\frac{dy}{dx} + y = 0$$\n\n使用 $ 和 $$ 语法可以插入各种数学、物理和化学公式。',
      timestamp: new Date(Date.now() - 3400000)
    }
  ]);
  
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  
  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // 处理发送消息
  const handleSendMessage = async (e) => {
    e.preventDefault();
    const text = inputText.trim();
    if (!text) return;
    
    setIsTyping(true);
    
    // 添加用户消息到列表
    const newUserMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: text,
      timestamp: new Date()
    };
    
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    setInputText('');
    
    try {
      // 使用api.js中的conversationApi发送消息

      const messageData = {
        content: text,
        use_llm: true,
        model_id: 'deepseek-chat'
      };

      const response = await conversationApi.sendMessage(1, messageData);

      
      // 从响应中提取助手回复
      const botReply = response.assistant_message?.content || '抱歉，我无法生成回复。';

      
      const newBotMessage = {
        id: messages.length + 2,
        sender: 'bot',
        text: botReply,
        timestamp: new Date()
      };
      
      setMessages(prevMessages => [...prevMessages, newBotMessage]);
    } catch (error) {
      // 添加更详细的错误日志
      console.error('发送消息时出错:', JSON.stringify({ message: error.message, stack: error.stack, name: error.name }, null, 2));
      
      // 显示后端返回的具体错误信息或默认错误消息
      const errorMessageText = error.response?.data?.detail || error.message || '抱歉，我暂时无法处理你的请求。请稍后再试。';
      const errorMessage = {
        id: messages.length + 2,
        sender: 'bot',
        text: errorMessageText,
        timestamp: new Date()
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
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

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-title">
          <div className="bot-avatar">🤖</div>
          <h2>Py Copilot</h2>
        </div>
        <div className="chat-actions">
          <button className="action-btn">📞</button>
          <button className="action-btn">📹</button>
          <button className="action-btn">📎</button>
          <button className="action-btn">🔽</button>
        </div>
      </div>
      
      <div className="chat-messages">
        {messages.map(message => (
          <div 
            key={message.id} 
            className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
          >
            {message.sender === 'bot' && <div className="message-avatar">🤖</div>}
            <div className="message-content">
              <div className="message-bubble">
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                >
                  {message.text}
                </ReactMarkdown>
                <span className="message-time">{formatTime(message.timestamp)}</span>
              </div>
            </div>
            {message.sender === 'user' && <div className="message-avatar">👤</div>}
          </div>
        ))}
        
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
        <button type="submit" className="send-btn">发送</button>
      </form>
    </div>
  );
};

export default Chat;