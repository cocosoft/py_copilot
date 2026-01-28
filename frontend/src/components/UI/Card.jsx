import React from 'react';
import './Card.css';

/**
 * 统一卡片组件
 * 支持多种变体、大小和交互状态
 */
const Card = ({
  children,
  variant = 'default', // default, outlined, elevated, interactive
  size = 'medium', // small, medium, large
  padding = 'normal', // none, compact, normal, spacious
  hoverable = false,
  selected = false,
  onClick,
  className = '',
  ...props
}) => {
  const baseClass = 'ui-card';
  const variantClass = `ui-card--${variant}`;
  const sizeClass = `ui-card--${size}`;
  const paddingClass = `ui-card--padding-${padding}`;
  const hoverableClass = hoverable ? 'ui-card--hoverable' : '';
  const selectedClass = selected ? 'ui-card--selected' : '';
  const interactiveClass = onClick ? 'ui-card--interactive' : '';
  
  const classes = [
    baseClass,
    variantClass,
    sizeClass,
    paddingClass,
    hoverableClass,
    selectedClass,
    interactiveClass,
    className
  ].filter(Boolean).join(' ');

  const handleClick = (e) => {
    if (onClick) {
      onClick(e);
    }
  };

  const handleKeyDown = (e) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick(e);
    }
  };

  return (
    <div
      className={classes}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={onClick ? 0 : -1}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * 卡片头部组件
 */
const CardHeader = ({ children, className = '', ...props }) => {
  return (
    <div className={`ui-card__header ${className}`} {...props}>
      {children}
    </div>
  );
};

/**
 * 卡片内容组件
 */
const CardContent = ({ children, className = '', ...props }) => {
  return (
    <div className={`ui-card__content ${className}`} {...props}>
      {children}
    </div>
  );
};

/**
 * 卡片底部组件
 */
const CardFooter = ({ children, className = '', ...props }) => {
  return (
    <div className={`ui-card__footer ${className}`} {...props}>
      {children}
    </div>
  );
};

/**
 * 卡片标题组件
 */
const CardTitle = ({ children, level = 'h3', className = '', ...props }) => {
  const Tag = level;
  return (
    <Tag className={`ui-card__title ${className}`} {...props}>
      {children}
    </Tag>
  );
};

/**
 * 卡片描述组件
 */
const CardDescription = ({ children, className = '', ...props }) => {
  return (
    <div className={`ui-card__description ${className}`} {...props}>
      {children}
    </div>
  );
};

// 导出所有组件
Card.Header = CardHeader;
Card.Content = CardContent;
Card.Footer = CardFooter;
Card.Title = CardTitle;
Card.Description = CardDescription;

export default Card;