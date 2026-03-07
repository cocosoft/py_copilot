/**
 * 通知组件
 * 
 * 提供统一的操作反馈机制，包括成功、错误、警告和信息提示
 */

import React, { useState, useEffect, useRef } from 'react';
import './Notification.css';

// 通知类型
export const NotificationType = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
};

// 通知队列
const notificationQueue = [];
let notificationId = 0;

/**
 * 显示通知
 * @param {Object} options - 通知选项
 * @param {string} options.message - 通知消息
 * @param {string} options.type - 通知类型 (success, error, warning, info)
 * @param {number} options.duration - 显示时长（毫秒），默认3000
 * @param {string} options.title - 通知标题
 */
export const showNotification = (options) => {
  const id = ++notificationId;
  const notification = {
    id,
    ...options,
    type: options.type || NotificationType.INFO,
    duration: options.duration || 3000
  };
  
  notificationQueue.push(notification);
  return id;
};

/**
 * 移除通知
 * @param {number} id - 通知ID
 */
export const removeNotification = (id) => {
  const index = notificationQueue.findIndex(n => n.id === id);
  if (index > -1) {
    notificationQueue.splice(index, 1);
  }
};

/**
 * 清空所有通知
 */
export const clearNotifications = () => {
  notificationQueue.length = 0;
};

/**
 * 通知组件
 * 
 * @returns {JSX.Element} 通知系统
 */
const Notification = () => {
  const [notifications, setNotifications] = useState([]);
  const containerRef = useRef(null);

  // 监听通知队列变化
  useEffect(() => {
    const updateNotifications = () => {
      setNotifications([...notificationQueue]);
    };

    // 每100毫秒检查一次队列变化
    const interval = setInterval(updateNotifications, 100);
    return () => clearInterval(interval);
  }, []);

  // 处理通知关闭
  const handleClose = (id) => {
    removeNotification(id);
  };

  // 处理通知点击
  const handleClick = (id) => {
    // 可以添加点击通知的回调逻辑
    console.log('Notification clicked:', id);
  };

  return (
    <div className="notification-container" ref={containerRef}>
      {notifications.map(notification => (
        <div
          key={notification.id}
          className={`notification notification-${notification.type}`}
          onClick={() => handleClick(notification.id)}
        >
          <div className="notification-icon">
            {notification.type === NotificationType.SUCCESS && '✅'}
            {notification.type === NotificationType.ERROR && '❌'}
            {notification.type === NotificationType.WARNING && '⚠️'}
            {notification.type === NotificationType.INFO && 'ℹ️'}
          </div>
          <div className="notification-content">
            {notification.title && (
              <h4 className="notification-title">{notification.title}</h4>
            )}
            <p className="notification-message">{notification.message}</p>
          </div>
          <button
            className="notification-close"
            onClick={(e) => {
              e.stopPropagation();
              handleClose(notification.id);
            }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
};

export default Notification;