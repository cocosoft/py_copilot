/**
 * 统一模态框组件
 * 
 * 整合项目中多个模态框实现，提供统一的模态框功能
 * 支持多种尺寸、位置、动画效果和自定义内容
 */

import React, { memo, useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import './Modal.css';

/**
 * 模态框组件属性定义
 * @typedef {Object} ModalProps
 * @property {boolean} isOpen - 是否显示模态框
 * @property {Function} onClose - 关闭回调
 * @property {string} title - 标题
 * @property {React.ReactNode} children - 内容
 * @property {'small'|'medium'|'large'|'fullscreen'} size - 模态框尺寸
 * @property {'center'|'top'|'bottom'} position - 模态框位置
 * @property {boolean} showCloseButton - 是否显示关闭按钮
 * @property {boolean} closeOnOverlayClick - 点击遮罩层是否关闭
 * @property {boolean} closeOnEscape - 按ESC键是否关闭
 * @property {React.ReactNode} footer - 底部内容
 * @property {string} className - 自定义类名
 */

const Modal = memo(({
  isOpen = false,
  onClose,
  title,
  children,
  size = 'medium',
  position = 'center',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  footer,
  className = '',
}) => {
  const modalRef = useRef(null);
  const overlayRef = useRef(null);

  // ESC键关闭处理
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape' && closeOnEscape && onClose) {
      onClose();
    }
  }, [closeOnEscape, onClose]);

  // 点击遮罩层关闭处理
  const handleOverlayClick = useCallback((e) => {
    if (e.target === overlayRef.current && closeOnOverlayClick && onClose) {
      onClose();
    }
  }, [closeOnOverlayClick, onClose]);

  // 阻止模态框内容点击事件冒泡
  const handleModalClick = useCallback((e) => {
    e.stopPropagation();
  }, []);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // 阻止背景滚动
      document.body.style.overflow = 'hidden';
    } else {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  // 焦点管理
  useEffect(() => {
    if (isOpen && modalRef.current) {
      modalRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const modalContent = (
    <div
      ref={overlayRef}
      className={`ucl-modal-overlay ucl-modal-overlay--${position}`}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'ucl-modal-title' : undefined}
    >
      <div
        ref={modalRef}
        className={`ucl-modal ucl-modal--${size} ${className}`}
        onClick={handleModalClick}
        tabIndex={-1}
      >
        {/* 头部 */}
        {(title || showCloseButton) && (
          <div className="ucl-modal__header">
            {title && (
              <h2 id="ucl-modal-title" className="ucl-modal__title">
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                className="ucl-modal__close-button"
                onClick={onClose}
                aria-label="关闭模态框"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M18 6L6 18" strokeWidth="2" />
                  <path d="M6 6l12 12" strokeWidth="2" />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* 内容 */}
        <div className="ucl-modal__content">
          {children}
        </div>

        {/* 底部 */}
        {footer && (
          <div className="ucl-modal__footer">
            {footer}
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
});

Modal.displayName = 'Modal';

export default Modal;