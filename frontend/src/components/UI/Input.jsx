import React, { memo, useCallback, useMemo } from 'react';
import './Input.css';

/**
 * 统一输入框组件
 * 支持多种类型、大小、状态和图标
 */
const Input = memo(({
  type = 'text',
  size = 'medium', // small, medium, large
  disabled = false,
  error = false,
  success = false,
  loading = false,
  icon,
  iconPosition = 'left', // left, right
  placeholder,
  value,
  onChange,
  onFocus,
  onBlur,
  className = '',
  ...props
}) => {
  const classes = useMemo(() => {
    const baseClass = 'ui-input';
    const sizeClass = `ui-input--${size}`;
    const disabledClass = disabled ? 'ui-input--disabled' : '';
    const errorClass = error ? 'ui-input--error' : '';
    const successClass = success ? 'ui-input--success' : '';
    const loadingClass = loading ? 'ui-input--loading' : '';
    const hasIconClass = icon ? 'ui-input--has-icon' : '';
    const iconPositionClass = `ui-input--icon-${iconPosition}`;
    
    return [
      baseClass,
      sizeClass,
      disabledClass,
      errorClass,
      successClass,
      loadingClass,
      hasIconClass,
      iconPositionClass,
      className
    ].filter(Boolean).join(' ');
  }, [size, disabled, error, success, loading, icon, iconPosition, className]);

  const handleChange = useCallback((e) => {
    if (!disabled && !loading && onChange) {
      onChange(e);
    }
  }, [disabled, loading, onChange]);

  return (
    <div className={classes}>
      {icon && iconPosition === 'left' && (
        <span className="ui-input__icon ui-input__icon--left">
          {icon}
        </span>
      )}
      
      <input
        type={type}
        className="ui-input__field"
        placeholder={placeholder}
        value={value}
        disabled={disabled || loading}
        onChange={handleChange}
        onFocus={onFocus}
        onBlur={onBlur}
        {...props}
      />
      
      {loading && (
        <span className="ui-input__loading">
          <svg className="ui-input__spinner" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" />
          </svg>
        </span>
      )}
      
      {icon && iconPosition === 'right' && (
        <span className="ui-input__icon ui-input__icon--right">
          {icon}
        </span>
      )}
      
      {error && (
        <span className="ui-input__error-icon">
          ⚠️
        </span>
      )}
      
      {success && (
        <span className="ui-input__success-icon">
          ✓
        </span>
      )}
    </div>
  );
});

export default Input;