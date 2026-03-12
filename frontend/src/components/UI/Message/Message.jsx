/**
 * 消息通知系统
 * 
 * 提供全局消息提示功能
 */

import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  FiCheckCircle, 
  FiAlertCircle, 
  FiInfo, 
  FiXCircle, 
  FiX 
} from 'react-icons/fi';
import './Message.css';

/**
 * 消息类型
 * @typedef {'success' | 'error' | 'warning' | 'info'} MessageType
 */

/**
 * 消息选项
 * @typedef {Object} MessageOptions
 * @property {string} content - 消息内容
 * @property {number} [duration=3000] - 显示时长（毫秒），0表示不自动关闭
 * @property {Function} [onClose] - 关闭回调
 */

// 图标映射
const icons = {
  success: <FiCheckCircle />,
  error: <FiXCircle />,
  warning: <FiAlertCircle />,
  info: <FiInfo />,
};

// 颜色映射
const colors = {
  success: '#52c41a',
  error: '#ff4d4f',
  warning: '#faad14',
  info: '#1890ff',
};

/**
 * 消息组件
 * 
 * @param {Object} props
 * @param {MessageType} props.type - 消息类型
 * @param {string} props.content - 消息内容
 * @param {Function} props.onClose - 关闭回调
 */
const MessageComponent = ({ type, content, onClose }) => {
  useEffect(() => {
    return () => {
      onClose?.();
    };
  }, [onClose]);

  return (
    <div className={`message message--${type}`}>
      <span className="message-icon" style={{ color: colors[type] }}>
        {icons[type]}
      </span>
      <span className="message-content">{content}</span>
      <button className="message-close" onClick={onClose}>
        <FiX />
      </button>
    </div>
  );
};

// 消息容器
let messageContainer = null;
let messageRoot = null;

/**
 * 获取消息容器
 */
const getMessageContainer = () => {
  if (!messageContainer) {
    messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';
    document.body.appendChild(messageContainer);
    messageRoot = createRoot(messageContainer);
  }
  return { container: messageContainer, root: messageRoot };
};

/**
 * 显示消息
 * 
 * @param {MessageType} type - 消息类型
 * @param {MessageOptions} options - 消息选项
 * @returns {{ close: Function }} 关闭方法
 */
const showMessage = (type, options) => {
  const { root } = getMessageContainer();
  const duration = options.duration ?? 3000;

  const messageId = Date.now();
  const messageElement = document.createElement('div');
  messageElement.className = 'message-wrapper';
  messageElement.dataset.id = messageId;

  const close = () => {
    messageElement.classList.add('message-exit');
    setTimeout(() => {
      messageElement.remove();
      options.onClose?.();
    }, 300);
  };

  messageContainer.appendChild(messageElement);
  const elementRoot = createRoot(messageElement);

  elementRoot.render(
    <MessageComponent
      type={type}
      content={options.content}
      onClose={close}
    />
  );

  // 自动关闭
  let timer = null;
  if (duration > 0) {
    timer = setTimeout(close, duration);
  }

  return {
    close: () => {
      clearTimeout(timer);
      close();
    },
  };
};

/**
 * 消息 API
 */
export const message = {
  /**
   * 成功消息
   * @param {MessageOptions | string} options - 消息选项或内容
   */
  success: (options) => {
    if (typeof options === 'string') {
      return showMessage('success', { content: options });
    }
    return showMessage('success', options);
  },

  /**
   * 错误消息
   * @param {MessageOptions | string} options - 消息选项或内容
   */
  error: (options) => {
    if (typeof options === 'string') {
      return showMessage('error', { content: options });
    }
    return showMessage('error', options);
  },

  /**
   * 警告消息
   * @param {MessageOptions | string} options - 消息选项或内容
   */
  warning: (options) => {
    if (typeof options === 'string') {
      return showMessage('warning', { content: options });
    }
    return showMessage('warning', options);
  },

  /**
   * 信息消息
   * @param {MessageOptions | string} options - 消息选项或内容
   */
  info: (options) => {
    if (typeof options === 'string') {
      return showMessage('info', { content: options });
    }
    return showMessage('info', options);
  },

  /**
   * 加载中消息
   * @param {string} content - 消息内容
   * @returns {{ close: Function }} 关闭方法
   */
  loading: (content = '加载中...') => {
    return showMessage('info', { content, duration: 0 });
  },

  /**
   * 销毁所有消息
   */
  destroy: () => {
    if (messageContainer) {
      messageContainer.innerHTML = '';
    }
  },
};

export default message;
