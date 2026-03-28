/**
 * 通知钩子
 *
 * 封装 antd 的 message 组件，提供统一的通知接口
 */

import { message } from 'antd';

/**
 * 使用通知
 *
 * @returns {Object} 通知方法
 */
export const useNotification = () => {
  /**
   * 显示通知
   *
   * @param {Object} options - 通知选项
   * @param {string} options.type - 通知类型: success, error, warning, info
   * @param {string} options.message - 通知消息
   * @param {string} options.description - 通知描述（可选）
   * @param {number} options.duration - 显示时长（秒）
   */
  const showNotification = (options) => {
    const { type = 'info', message: msg, description, duration = 3 } = options;

    const content = description ? `${msg} ${description}` : msg;

    switch (type) {
      case 'success':
        message.success({ content, duration });
        break;
      case 'error':
        message.error({ content, duration });
        break;
      case 'warning':
        message.warning({ content, duration });
        break;
      case 'info':
      default:
        message.info({ content, duration });
        break;
    }
  };

  return {
    showNotification
  };
};

export default useNotification;
