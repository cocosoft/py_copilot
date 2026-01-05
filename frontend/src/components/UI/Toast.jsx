import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import classNames from 'classnames';
import PropTypes from 'prop-types';
import Icon from './Icon';

const Toast = ({
  id,
  type = 'info',
  title,
  message,
  duration = 5000,
  closable = true,
  showIcon = true,
  position = 'top-right',
  onClose,
  className,
  ...props
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isLeaving, setIsLeaving] = useState(false);

  const typeConfig = {
    success: {
      icon: 'success',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-800',
      iconColor: 'text-green-600',
    },
    error: {
      icon: 'error',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-800',
      iconColor: 'text-red-600',
    },
    warning: {
      icon: 'warning',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-800',
      iconColor: 'text-yellow-600',
    },
    info: {
      icon: 'info',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-800',
      iconColor: 'text-blue-600',
    },
  };

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2',
    'bottom-right': 'bottom-4 right-4',
  };

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration]);

  const handleClose = () => {
    setIsLeaving(true);
    setTimeout(() => {
      setIsVisible(false);
      onClose?.(id);
    }, 300);
  };

  const config = typeConfig[type];

  const toastVariants = {
    hidden: {
      opacity: 0,
      y: position.includes('top') ? -50 : 50,
      scale: 0.8,
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 300,
      },
    },
    exit: {
      opacity: 0,
      y: position.includes('top') ? -50 : 50,
      scale: 0.8,
      transition: {
        duration: 0.2,
      },
    },
  };

  if (!isVisible) return null;

  return createPortal(
    <AnimatePresence>
      {!isLeaving && (
        <motion.div
          id={id}
          className={classNames(
            'fixed z-50 min-w-[300px] max-w-[400px] p-4 rounded-lg border shadow-lg',
            config.bgColor,
            config.borderColor,
            positionClasses[position],
            className
          )}
          variants={toastVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          {...props}
        >
          <div className="flex items-start gap-3">
            {showIcon && (
              <div className={classNames('flex-shrink-0 mt-0.5', config.iconColor)}>
                <Icon name={config.icon} size={16} />
              </div>
            )}
            
            <div className="flex-1 min-w-0">
              {title && (
                <h4 className={classNames('font-medium text-sm', config.textColor)}>
                  {title}
                </h4>
              )}
              {message && (
                <p className={classNames(
                  'text-sm mt-1',
                  title ? config.textColor : config.textColor
                )}>
                  {message}
                </p>
              )}
            </div>
            
            {closable && (
              <button
                onClick={handleClose}
                className={classNames(
                  'flex-shrink-0 p-1 rounded-md hover:bg-black hover:bg-opacity-10',
                  config.iconColor
                )}
              >
                <Icon name="close" size={14} />
              </button>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
};

// Toast Manager
class ToastManager {
  constructor() {
    this.toasts = [];
    this.listeners = new Set();
    this.container = null;
  }

  createContainer() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.style.position = 'fixed';
      this.container.style.top = '0';
      this.container.style.left = '0';
      this.container.style.width = '100%';
      this.container.style.height = '100%';
      this.container.style.pointerEvents = 'none';
      this.container.style.zIndex = '9999';
      document.body.appendChild(this.container);
    }
  }

  add(toast) {
    const id = Date.now() + Math.random();
    const newToast = { ...toast, id };
    this.toasts = [...this.toasts, newToast];
    this.notifyListeners();
    return id;
  }

  remove(id) {
    this.toasts = this.toasts.filter(toast => toast.id !== id);
    this.notifyListeners();
  }

  clear() {
    this.toasts = [];
    this.notifyListeners();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notifyListeners() {
    this.listeners.forEach(listener => listener(this.toasts));
  }
}

// 单例实例
const toastManager = new ToastManager();

// 便捷方法
const showToast = (options) => {
  toastManager.createContainer();
  return toastManager.add(options);
};

const showSuccess = (message, options = {}) => {
  return showToast({ type: 'success', message, ...options });
};

const showError = (message, options = {}) => {
  return showToast({ type: 'error', message, ...options });
};

const showWarning = (message, options = {}) => {
  return showToast({ type: 'warning', message, ...options });
};

const showInfo = (message, options = {}) => {
  return showToast({ type: 'info', message, ...options });
};

// Toast容器组件
const ToastContainer = ({ position = 'top-right' }) => {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const unsubscribe = toastManager.subscribe(setToasts);
    return unsubscribe;
  }, []);

  return (
    <>
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          {...toast}
          position={position}
          onClose={toastManager.remove.bind(toastManager)}
        />
      ))}
    </>
  );
};

Toast.propTypes = {
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  type: PropTypes.oneOf(['success', 'error', 'warning', 'info']),
  title: PropTypes.string,
  message: PropTypes.string,
  duration: PropTypes.number,
  closable: PropTypes.bool,
  showIcon: PropTypes.bool,
  position: PropTypes.oneOf([
    'top-left', 'top-center', 'top-right',
    'bottom-left', 'bottom-center', 'bottom-right'
  ]),
  onClose: PropTypes.func,
  className: PropTypes.string,
};

ToastContainer.propTypes = {
  position: PropTypes.oneOf([
    'top-left', 'top-center', 'top-right',
    'bottom-left', 'bottom-center', 'bottom-right'
  ]),
};

export { Toast, ToastContainer, toastManager };
export { showToast, showSuccess, showError, showWarning, showInfo };
export default Toast;