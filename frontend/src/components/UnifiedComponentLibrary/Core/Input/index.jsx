/**
 * 统一输入组件
 * 
 * 提供一致的输入框样式和行为
 * 
 * 任务编号: Phase1-Week3
 * 阶段: 第一阶段 - 功能重复问题优化
 */

import React, { forwardRef, useState } from 'react';
import PropTypes from 'prop-types';

const sizeStyles = {
  sm: {
    padding: '6px 10px',
    fontSize: '12px',
    borderRadius: '4px',
  },
  md: {
    padding: '8px 12px',
    fontSize: '14px',
    borderRadius: '6px',
  },
  lg: {
    padding: '12px 16px',
    fontSize: '16px',
    borderRadius: '8px',
  },
};

const variantStyles = {
  default: {
    backgroundColor: '#ffffff',
    border: '1px solid #d1d5db',
    '&:hover': {
      borderColor: '#9ca3af',
    },
    '&:focus': {
      borderColor: '#0ea5e9',
      boxShadow: '0 0 0 3px rgba(14, 165, 233, 0.1)',
    },
  },
  filled: {
    backgroundColor: '#f3f4f6',
    border: '1px solid transparent',
    '&:hover': {
      backgroundColor: '#e5e7eb',
    },
    '&:focus': {
      backgroundColor: '#ffffff',
      borderColor: '#0ea5e9',
    },
  },
  flushed: {
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '2px solid #d1d5db',
    borderRadius: '0',
    '&:hover': {
      borderBottomColor: '#9ca3af',
    },
    '&:focus': {
      borderBottomColor: '#0ea5e9',
    },
  },
  unstyled: {
    backgroundColor: 'transparent',
    border: 'none',
  },
};

const statusStyles = {
  error: {
    borderColor: '#ef4444',
    '&:focus': {
      borderColor: '#ef4444',
      boxShadow: '0 0 0 3px rgba(239, 68, 68, 0.1)',
    },
  },
  success: {
    borderColor: '#22c55e',
    '&:focus': {
      borderColor: '#22c55e',
      boxShadow: '0 0 0 3px rgba(34, 197, 94, 0.1)',
    },
  },
  warning: {
    borderColor: '#f59e0b',
    '&:focus': {
      borderColor: '#f59e0b',
      boxShadow: '0 0 0 3px rgba(245, 158, 11, 0.1)',
    },
  },
};

/**
 * 统一输入组件
 * 
 * @param {Object} props - 组件属性
 * @param {string} props.variant - 输入框变体 (default, filled, flushed, unstyled)
 * @param {string} props.size - 输入框尺寸 (sm, md, lg)
 * @param {string} props.status - 输入框状态 (default, error, success, warning)
 * @param {string} props.leftIcon - 左侧图标
 * @param {string} props.rightIcon - 右侧图标
 * @param {string} props.leftElement - 左侧元素
 * @param {string} props.rightElement - 右侧元素
 * @param {string} props.helperText - 帮助文本
 * @param {string} props.errorText - 错误文本
 * @param {string} props.label - 标签
 * @param {boolean} props.required - 是否必填
 * @param {boolean} props.disabled - 是否禁用
 * @param {boolean} props.fullWidth - 是否全宽
 * @param {string} props.className - 自定义类名
 * @param {Object} props.style - 自定义样式
 * @returns {JSX.Element} 输入组件
 */
const Input = forwardRef(({
  variant = 'default',
  size = 'md',
  status = 'default',
  leftIcon,
  rightIcon,
  leftElement,
  rightElement,
  helperText,
  errorText,
  label,
  required = false,
  disabled = false,
  fullWidth = false,
  className = '',
  style = {},
  onChange,
  onFocus,
  onBlur,
  value,
  defaultValue,
  placeholder,
  type = 'text',
  name,
  id,
  autoFocus,
  maxLength,
  minLength,
  pattern,
  readOnly,
  spellCheck,
  autoComplete,
  ...rest
}, ref) => {
  const [isFocused, setIsFocused] = useState(false);
  const [internalValue, setInternalValue] = useState(defaultValue || '');
  
  const currentValue = value !== undefined ? value : internalValue;
  
  const handleFocus = (e) => {
    setIsFocused(true);
    onFocus?.(e);
  };
  
  const handleBlur = (e) => {
    setIsFocused(false);
    onBlur?.(e);
  };
  
  const handleChange = (e) => {
    if (value === undefined) {
      setInternalValue(e.target.value);
    }
    onChange?.(e);
  };
  
  const getInputStyles = () => {
    const baseStyles = {
      width: fullWidth ? '100%' : 'auto',
      outline: 'none',
      transition: 'all 0.2s ease',
      fontFamily: 'inherit',
      lineHeight: '1.5',
      color: disabled ? '#9ca3af' : '#1f2937',
      cursor: disabled ? 'not-allowed' : 'text',
      opacity: disabled ? 0.7 : 1,
      ...sizeStyles[size],
    };
    
    const variantStyle = variantStyles[variant] || variantStyles.default;
    const statusStyle = status !== 'default' ? statusStyles[status] : {};
    
    return {
      ...baseStyles,
      backgroundColor: variantStyle.backgroundColor,
      border: variantStyle.border,
      borderRadius: variantStyle.borderRadius || sizeStyles[size].borderRadius,
      ...(isFocused && variantStyle['&:focus']),
      ...statusStyle,
    };
  };
  
  const wrapperStyles = {
    display: 'flex',
    flexDirection: 'column',
    width: fullWidth ? '100%' : 'auto',
    marginBottom: helperText || errorText ? '4px' : '0',
  };
  
  const inputWrapperStyles = {
    display: 'flex',
    alignItems: 'center',
    position: 'relative',
    width: '100%',
  };
  
  const iconStyles = {
    position: 'absolute',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#9ca3af',
    pointerEvents: 'none',
    height: '100%',
  };
  
  const leftIconStyles = {
    ...iconStyles,
    left: '12px',
  };
  
  const rightIconStyles = {
    ...iconStyles,
    right: '12px',
  };
  
  const labelStyles = {
    display: 'block',
    marginBottom: '6px',
    fontSize: '14px',
    fontWeight: '500',
    color: status === 'error' ? '#ef4444' : '#374151',
  };
  
  const helperTextStyles = {
    marginTop: '4px',
    fontSize: '12px',
    color: status === 'error' ? '#ef4444' : '#6b7280',
  };
  
  const inputPaddingLeft = leftIcon || leftElement ? '36px' : sizeStyles[size].padding;
  const inputPaddingRight = rightIcon || rightElement ? '36px' : sizeStyles[size].padding;
  
  return (
    <div style={wrapperStyles} className={className}>
      {label && (
        <label htmlFor={id || name} style={labelStyles}>
          {label}
          {required && <span style={{ color: '#ef4444', marginLeft: '4px' }}>*</span>}
        </label>
      )}
      
      <div style={inputWrapperStyles}>
        {leftIcon && (
          <span style={leftIconStyles}>
            {leftIcon}
          </span>
        )}
        
        {leftElement && (
          <span style={{ ...leftIconStyles, pointerEvents: 'auto' }}>
            {leftElement}
          </span>
        )}
        
        <input
          ref={ref}
          id={id || name}
          name={name}
          type={type}
          value={currentValue}
          placeholder={placeholder}
          disabled={disabled}
          readOnly={readOnly}
          autoFocus={autoFocus}
          maxLength={maxLength}
          minLength={minLength}
          pattern={pattern}
          spellCheck={spellCheck}
          autoComplete={autoComplete}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          style={{
            ...getInputStyles(),
            paddingLeft: inputPaddingLeft,
            paddingRight: inputPaddingRight,
            ...style,
          }}
          {...rest}
        />
        
        {rightIcon && (
          <span style={rightIconStyles}>
            {rightIcon}
          </span>
        )}
        
        {rightElement && (
          <span style={{ ...rightIconStyles, pointerEvents: 'auto' }}>
            {rightElement}
          </span>
        )}
      </div>
      
      {(helperText || errorText) && (
        <span style={helperTextStyles}>
          {errorText || helperText}
        </span>
      )}
    </div>
  );
});

Input.displayName = 'Input';

Input.propTypes = {
  variant: PropTypes.oneOf(['default', 'filled', 'flushed', 'unstyled']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  status: PropTypes.oneOf(['default', 'error', 'success', 'warning']),
  leftIcon: PropTypes.node,
  rightIcon: PropTypes.node,
  leftElement: PropTypes.node,
  rightElement: PropTypes.node,
  helperText: PropTypes.string,
  errorText: PropTypes.string,
  label: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  fullWidth: PropTypes.bool,
  className: PropTypes.string,
  style: PropTypes.object,
  onChange: PropTypes.func,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
  value: PropTypes.string,
  defaultValue: PropTypes.string,
  placeholder: PropTypes.string,
  type: PropTypes.string,
  name: PropTypes.string,
  id: PropTypes.string,
  autoFocus: PropTypes.bool,
  maxLength: PropTypes.number,
  minLength: PropTypes.number,
  pattern: PropTypes.string,
  readOnly: PropTypes.bool,
  spellCheck: PropTypes.bool,
  autoComplete: PropTypes.string,
};

export default Input;
