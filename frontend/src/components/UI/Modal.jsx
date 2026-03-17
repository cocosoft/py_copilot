import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import classNames from 'classnames';
import PropTypes from 'prop-types';
import Button from './Button';

const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'medium',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  footer,
  className,
  overlayClassName,
  ...props
}) => {
  const sizeClasses = {
    small: 'max-w-md',
    medium: 'max-w-2xl',
    large: 'max-w-4xl',
    xl: 'max-w-6xl',
    full: 'max-w-full mx-4',
  };

  const modalVariants = {
    hidden: {
      opacity: 0,
      scale: 0.95,
      y: -20,
    },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 300,
      },
    },
    exit: {
      opacity: 0,
      scale: 0.95,
      y: -20,
      transition: {
        duration: 0.2,
      },
    },
  };

  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 },
  };

  React.useEffect(() => {
    if (closeOnEscape && isOpen) {
      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          onClose?.();
        }
      };

      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';

      return () => {
        document.removeEventListener('keydown', handleEscape);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen, closeOnEscape, onClose]);

  const handleOverlayClick = (e) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose?.();
    }
  };

  if (!isOpen) return null;

  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          {/* Overlay */}
          <motion.div
            className={classNames(
              'fixed inset-0 bg-black bg-opacity-50',
              overlayClassName
            )}
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={handleOverlayClick}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.7)', // 更暗的背景
              zIndex: 9999, // 更高的z-index
            }}
          />

          {/* Modal */}
          <div 
            className="flex min-h-full items-center justify-center p-4"
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 10000, // 更高的z-index
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <motion.div
              className={classNames(
                'relative w-full rounded-xl shadow-2xl',
                sizeClasses[size],
                className
              )}
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              style={{
                position: 'relative',
                zIndex: 10001, // 更高的z-index
                boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)', // 更明显的阴影
                animation: 'modal-appear 0.3s ease-out', // 添加动画
                backgroundColor: '#ffffff', // 确保背景为白色
                border: '1px solid #e8e8e8', // 添加边框
              }}
              {...props}
            >
              {/* Header */}
              {(title || showCloseButton) && (
                <div className="flex items-center justify-between p-6 border-b border-gray-200" style={{ backgroundColor: '#ffffff' }}>
                  {title && (
                    <h2 className="text-xl font-semibold text-gray-900">
                      {title}
                    </h2>
                  )}
                  {showCloseButton && (
                    <Button
                      variant="danger"
                      size="small"
                      onClick={onClose}
                      className="ml-4"
                    >
                      关闭
                    </Button>
                  )}
                </div>
              )}

              {/* Content */}
              <div className="p-6" style={{ backgroundColor: '#ffffff' }}>
                {children}
              </div>

              {/* Footer */}
              {footer && (
                <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200" style={{ backgroundColor: '#ffffff' }}>
                  {footer}
                </div>
              )}
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );

  return createPortal(modalContent, document.body);
};

Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string,
  children: PropTypes.node,
  size: PropTypes.oneOf(['small', 'medium', 'large', 'xl', 'full']),
  closeOnOverlayClick: PropTypes.bool,
  closeOnEscape: PropTypes.bool,
  showCloseButton: PropTypes.bool,
  footer: PropTypes.node,
  className: PropTypes.string,
  overlayClassName: PropTypes.string,
};

export default Modal;