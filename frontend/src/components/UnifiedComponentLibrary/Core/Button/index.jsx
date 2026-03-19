/**
 * 统一按钮组件
 * 
 * 整合项目中多个按钮实现，提供统一的按钮样式和功能
 * 支持多种变体、大小、状态和图标
 */

import React, { memo, useCallback } from 'react';
import './Button.css';

/**
 * 按钮组件属性定义
 * @typedef {Object} ButtonProps
 * @property {React.ReactNode} children - 按钮内容
 * @property {'primary'|'secondary'|'success'|'warning'|'danger'|'outline'|'ghost'} variant - 按钮变体
 * @property {'small'|'medium'|'large'} size - 按钮大小
 * @property {boolean} disabled - 是否禁用
 * @property {boolean} loading - 加载状态
 * @property {React.ReactNode} icon - 图标
 * @property {'left'|'right'} iconPosition - 图标位置
 * @property {Function} onClick - 点击事件
 * @property {'button'|'submit'|'reset'} type - 按钮类型
 * @property {string} className - 自定义类名
 */

const Button = memo(({
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  onClick,
  type = 'button',
  className = '',
  ...props
}) => {
  const baseClass = 'ucl-button';
  const variantClass = `ucl-button--${variant}`;
  const sizeClass = `ucl-button--${size}`;
  const disabledClass = disabled ? 'ucl-button--disabled' : '';
  const loadingClass = loading ? 'ucl-button--loading' : '';
  
  const classes = [
    baseClass,
    variantClass,
    sizeClass,
    disabledClass,
    loadingClass,
    className
  ].filter(Boolean).join(' ');

  const handleClick = useCallback((e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  }, [disabled, loading, onClick]);

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      onClick={handleClick}
      {...props}
    >
      {loading && (
        <span className="ucl-button__loading-spinner">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" strokeWidth="2" />
            <path d="M12 6v6l4 2" strokeWidth="2" />
          </svg>
        </span>
      )}
      
      {icon && iconPosition === 'left' && !loading && (
        <span className="ucl-button__icon ucl-button__icon--left">
          {icon}
        </span>
      )}
      
      <span className="ucl-button__content">
        {children}
      </span>
      
      {icon && iconPosition === 'right' && !loading && (
        <span className="ucl-button__icon ucl-button__icon--right">
          {icon}
        </span>
      )}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;