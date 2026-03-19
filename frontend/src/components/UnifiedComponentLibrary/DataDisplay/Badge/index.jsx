/**
 * 统一徽章组件
 * 
 * 提供一致的徽章样式和行为
 * 
 * 任务编号: Phase1-Week3
 * 阶段: 第一阶段 - 功能重复问题优化
 */

import React from 'react';
import PropTypes from 'prop-types';

const colorStyles = {
  primary: {
    solid: { backgroundColor: '#0ea5e9', color: '#ffffff' },
    subtle: { backgroundColor: '#e0f2fe', color: '#0369a1' },
    outline: { backgroundColor: 'transparent', color: '#0ea5e9', border: '1px solid #0ea5e9' },
  },
  secondary: {
    solid: { backgroundColor: '#64748b', color: '#ffffff' },
    subtle: { backgroundColor: '#f1f5f9', color: '#475569' },
    outline: { backgroundColor: 'transparent', color: '#64748b', border: '1px solid #64748b' },
  },
  success: {
    solid: { backgroundColor: '#22c55e', color: '#ffffff' },
    subtle: { backgroundColor: '#dcfce7', color: '#15803d' },
    outline: { backgroundColor: 'transparent', color: '#22c55e', border: '1px solid #22c55e' },
  },
  warning: {
    solid: { backgroundColor: '#f59e0b', color: '#ffffff' },
    subtle: { backgroundColor: '#fef3c7', color: '#b45309' },
    outline: { backgroundColor: 'transparent', color: '#f59e0b', border: '1px solid #f59e0b' },
  },
  danger: {
    solid: { backgroundColor: '#ef4444', color: '#ffffff' },
    subtle: { backgroundColor: '#fee2e2', color: '#b91c1c' },
    outline: { backgroundColor: 'transparent', color: '#ef4444', border: '1px solid #ef4444' },
  },
  info: {
    solid: { backgroundColor: '#3b82f6', color: '#ffffff' },
    subtle: { backgroundColor: '#dbeafe', color: '#1d4ed8' },
    outline: { backgroundColor: 'transparent', color: '#3b82f6', border: '1px solid #3b82f6' },
  },
};

const sizeStyles = {
  sm: {
    padding: '2px 6px',
    fontSize: '10px',
    borderRadius: '4px',
  },
  md: {
    padding: '4px 8px',
    fontSize: '12px',
    borderRadius: '6px',
  },
  lg: {
    padding: '6px 12px',
    fontSize: '14px',
    borderRadius: '8px',
  },
};

/**
 * 统一徽章组件
 * 
 * @param {Object} props - 组件属性
 * @param {string} props.color - 徽章颜色 (primary, secondary, success, warning, danger, info)
 * @param {string} props.variant - 徽章变体 (solid, subtle, outline)
 * @param {string} props.size - 徽章尺寸 (sm, md, lg)
 * @param {React.ReactNode} props.icon - 徽章图标
 * @param {boolean} props.closable - 是否可关闭
 * @param {function} props.onClose - 关闭回调
 * @param {React.ReactNode} props.children - 徽章内容
 * @param {string} props.className - 自定义类名
 * @param {Object} props.style - 自定义样式
 * @returns {JSX.Element} 徽章组件
 */
const Badge = ({
  color = 'primary',
  variant = 'subtle',
  size = 'md',
  icon,
  closable = false,
  onClose,
  children,
  className = '',
  style = {},
  ...rest
}) => {
  const getBadgeStyles = () => {
    const baseStyles = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: '500',
      lineHeight: '1',
      whiteSpace: 'nowrap',
      transition: 'all 0.2s ease',
    };
    
    const colorStyle = colorStyles[color]?.[variant] || colorStyles.primary.subtle;
    const sizeStyle = sizeStyles[size] || sizeStyles.md;
    
    return {
      ...baseStyles,
      ...colorStyle,
      ...sizeStyle,
      ...style,
    };
  };
  
  const iconStyles = {
    marginRight: children ? '4px' : '0',
    display: 'inline-flex',
    alignItems: 'center',
  };
  
  const closeStyles = {
    marginLeft: '6px',
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    opacity: 0.7,
    transition: 'opacity 0.2s ease',
  };
  
  const handleClose = (e) => {
    e.stopPropagation();
    onClose?.(e);
  };
  
  return (
    <span
      className={className}
      style={getBadgeStyles()}
      {...rest}
    >
      {icon && (
        <span style={iconStyles}>
          {icon}
        </span>
      )}
      
      {children}
      
      {closable && (
        <span
          style={closeStyles}
          onClick={handleClose}
          role="button"
          tabIndex={0}
          aria-label="关闭"
        >
          ×
        </span>
      )}
    </span>
  );
};

Badge.propTypes = {
  color: PropTypes.oneOf(['primary', 'secondary', 'success', 'warning', 'danger', 'info']),
  variant: PropTypes.oneOf(['solid', 'subtle', 'outline']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  icon: PropTypes.node,
  closable: PropTypes.bool,
  onClose: PropTypes.func,
  children: PropTypes.node,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default Badge;
