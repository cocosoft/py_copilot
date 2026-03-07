/**
 * 错误通知组件
 *
 * 用于显示用户友好的错误提示
 */

import React, { useState, useEffect } from 'react';
import errorHandler from '../../utils/errorHandler';
import './ErrorNotification.css';

/**
 * 错误通知组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.duration - 通知显示时长（毫秒）
 * @returns {JSX.Element} 错误通知组件
 */
const ErrorNotification = ({ duration = 5000 }) => {
  const [errors, setErrors] = useState([]);
  const [visible, setVisible] = useState(false);

  // 注册错误监听器
  useEffect(() => {
    const unsubscribe = errorHandler.onError((error) => {
      addError(error);
    });

    return () => unsubscribe();
  }, []);

  /**
   * 添加错误
   * @param {Object} error - 错误对象
   */
  const addError = (error) => {
    setErrors(prev => {
      const newErrors = [error, ...prev].slice(0, 5); // 最多显示5个错误
      setVisible(true);
      return newErrors;
    });

    // 自动移除错误
    setTimeout(() => {
      removeError(error.id);
    }, duration);
  };

  /**
   * 移除错误
   * @param {string} errorId - 错误ID
   */
  const removeError = (errorId) => {
    setErrors(prev => {
      const newErrors = prev.filter(e => e.id !== errorId);
      if (newErrors.length === 0) {
        setVisible(false);
      }
      return newErrors;
    });
  };

  /**
   * 清除所有错误
   */
  const clearAllErrors = () => {
    setErrors([]);
    setVisible(false);
  };

  /**
   * 获取错误图标
   * @param {string} type - 错误类型
   * @returns {string} 错误图标
   */
  const getErrorIcon = (type) => {
    const icons = {
      network: '🌐',
      validation: '⚠️',
      authentication: '🔐',
      permission: '🚫',
      server: '💻',
      client: '🖥️',
      unknown: '❓'
    };
    return icons[type] || '❓';
  };

  if (!visible || errors.length === 0) {
    return null;
  }

  return (
    <div className="error-notification-container">
      <div className="error-notification">
        <div className="error-header">
          <h4>错误通知</h4>
          <button 
            className="clear-all-btn"
            onClick={clearAllErrors}
            title="清除所有"
          >
            ✕
          </button>
        </div>
        <div className="error-list">
          {errors.map(error => (
            <div key={error.id} className="error-item">
              <div className="error-icon">
                {getErrorIcon(error.type)}
              </div>
              <div className="error-content">
                <div className="error-title">{error.title}</div>
                <div className="error-message">{error.message}</div>
              </div>
              <button 
                className="close-btn"
                onClick={() => removeError(error.id)}
                title="关闭"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ErrorNotification;
