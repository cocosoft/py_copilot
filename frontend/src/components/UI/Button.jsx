import React from 'react';
import './Button.css';

/**
 * 统一按钮组件
 * 支持多种变体、大小、状态和图标
 */
const Button = ({
  children,
  variant = 'primary', // primary, secondary, success, warning, danger, outline, ghost
  size = 'medium', // small, medium, large
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left', // left, right
  onClick,
  type = 'button',
  className = '',
  ...props
}) => {
  const baseClass = 'ui-button';
  const variantClass = `ui-button--${variant}`;
  const sizeClass = `ui-button--${size}`;
  const disabledClass = disabled ? 'ui-button--disabled' : '';
  const loadingClass = loading ? 'ui-button--loading' : '';
  
  const classes = [
    baseClass,
    variantClass,
    sizeClass,
    disabledClass,
    loadingClass,
    className
  ].filter(Boolean).join(' ');

  const handleClick = (e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      onClick={handleClick}
      {...props}
    >
      {loading && (
        <span className="ui-button__loading">
          <svg className="ui-button__spinner" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" />
          </svg>
        </span>
      )}
      
      {icon && iconPosition === 'left' && !loading && (
        <span className="ui-button__icon ui-button__icon--left">
          {icon}
        </span>
      )}
      
      <span className="ui-button__content">
        {children}
      </span>
      
      {icon && iconPosition === 'right' && !loading && (
        <span className="ui-button__icon ui-button__icon--right">
          {icon}
        </span>
      )}
    </button>
  );
};

export default Button;