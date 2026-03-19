/**
 * 统一卡片组件
 * 
 * 提供一致的卡片容器样式和行为
 * 
 * 任务编号: Phase1-Week3
 * 阶段: 第一阶段 - 功能重复问题优化
 */

import React, { forwardRef, useState } from 'react';
import PropTypes from 'prop-types';

const variantStyles = {
  default: {
    backgroundColor: '#ffffff',
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  },
  outlined: {
    backgroundColor: '#ffffff',
    border: '1px solid #e5e7eb',
  },
  elevated: {
    backgroundColor: '#ffffff',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  },
  filled: {
    backgroundColor: '#f9fafb',
  },
};

const paddingStyles = {
  none: { padding: '0' },
  sm: { padding: '12px' },
  md: { padding: '16px' },
  lg: { padding: '24px' },
};

const borderRadiusStyles = {
  sm: { borderRadius: '4px' },
  md: { borderRadius: '8px' },
  lg: { borderRadius: '12px' },
  xl: { borderRadius: '16px' },
  none: { borderRadius: '0' },
};

/**
 * 统一卡片组件
 * 
 * @param {Object} props - 组件属性
 * @param {string} props.variant - 卡片变体 (default, outlined, elevated, filled)
 * @param {string} props.padding - 内边距 (none, sm, md, lg)
 * @param {string} props.borderRadius - 圆角 (none, sm, md, lg, xl)
 * @param {boolean} props.hoverable - 是否有悬停效果
 * @param {boolean} props.clickable - 是否可点击
 * @param {function} props.onClick - 点击回调
 * @param {React.ReactNode} props.header - 卡片头部
 * @param {React.ReactNode} props.footer - 卡片底部
 * @param {React.ReactNode} props.children - 卡片内容
 * @param {string} props.className - 自定义类名
 * @param {Object} props.style - 自定义样式
 * @returns {JSX.Element} 卡片组件
 */
const Card = forwardRef(({
  variant = 'default',
  padding = 'md',
  borderRadius = 'lg',
  hoverable = false,
  clickable = false,
  onClick,
  header,
  footer,
  children,
  className = '',
  style = {},
  ...rest
}, ref) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const getCardStyles = () => {
    const baseStyles = {
      overflow: 'hidden',
      transition: 'all 0.2s ease',
      width: '100%',
    };
    
    const variantStyle = variantStyles[variant] || variantStyles.default;
    const paddingStyle = paddingStyles[padding] || paddingStyles.md;
    const radiusStyle = borderRadiusStyles[borderRadius] || borderRadiusStyles.lg;
    
    const hoverStyles = hoverable || clickable ? {
      cursor: clickable ? 'pointer' : 'default',
      transform: isHovered ? 'translateY(-2px)' : 'none',
      boxShadow: isHovered 
        ? '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
        : variantStyle.boxShadow,
    } : {};
    
    return {
      ...baseStyles,
      ...variantStyle,
      ...paddingStyle,
      ...radiusStyle,
      ...hoverStyles,
      ...style,
    };
  };
  
  const headerStyles = {
    padding: padding === 'none' ? '0' : '0 0 16px 0',
    borderBottom: header ? '1px solid #e5e7eb' : 'none',
    marginBottom: header ? '16px' : '0',
  };
  
  const footerStyles = {
    padding: padding === 'none' ? '0' : '16px 0 0 0',
    borderTop: footer ? '1px solid #e5e7eb' : 'none',
    marginTop: footer ? '16px' : '0',
  };
  
  const handleMouseEnter = () => {
    setIsHovered(true);
  };
  
  const handleMouseLeave = () => {
    setIsHovered(false);
  };
  
  const handleClick = (e) => {
    if (clickable && onClick) {
      onClick(e);
    }
  };
  
  return (
    <div
      ref={ref}
      className={className}
      style={getCardStyles()}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      {...rest}
    >
      {header && (
        <div style={headerStyles}>
          {header}
        </div>
      )}
      
      <div className="card-body">
        {children}
      </div>
      
      {footer && (
        <div style={footerStyles}>
          {footer}
        </div>
      )}
    </div>
  );
});

Card.displayName = 'Card';

Card.propTypes = {
  variant: PropTypes.oneOf(['default', 'outlined', 'elevated', 'filled']),
  padding: PropTypes.oneOf(['none', 'sm', 'md', 'lg']),
  borderRadius: PropTypes.oneOf(['none', 'sm', 'md', 'lg', 'xl']),
  hoverable: PropTypes.bool,
  clickable: PropTypes.bool,
  onClick: PropTypes.func,
  header: PropTypes.node,
  footer: PropTypes.node,
  children: PropTypes.node,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default Card;
