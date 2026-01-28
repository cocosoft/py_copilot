import React from 'react';
import './Responsive.css';

/**
 * 响应式容器组件
 * 根据屏幕尺寸自动调整布局
 */
const Container = ({
  children,
  size = 'default', // default, sm, md, lg, xl, full
  padding = 'normal', // none, compact, normal, spacious
  className = '',
  ...props
}) => {
  const baseClass = 'ui-container';
  const sizeClass = `ui-container--${size}`;
  const paddingClass = `ui-container--padding-${padding}`;
  
  const classes = [
    baseClass,
    sizeClass,
    paddingClass,
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

/**
 * 栅格布局组件
 */
const Grid = ({
  children,
  columns = 12, // 栅格列数
  gap = 'normal', // none, small, normal, large
  responsive = true,
  className = '',
  ...props
}) => {
  const baseClass = 'ui-grid';
  const gapClass = `ui-grid--gap-${gap}`;
  const responsiveClass = responsive ? 'ui-grid--responsive' : '';
  
  const classes = [
    baseClass,
    gapClass,
    responsiveClass,
    className
  ].filter(Boolean).join(' ');

  const style = {
    '--ui-grid-columns': columns
  };

  return (
    <div className={classes} style={style} {...props}>
      {children}
    </div>
  );
};

/**
 * 栅格项组件
 */
const GridItem = ({
  children,
  span = 1, // 占据的列数
  sm,
  md,
  lg,
  xl,
  className = '',
  ...props
}) => {
  const baseClass = 'ui-grid-item';
  
  const classes = [
    baseClass,
    className
  ].filter(Boolean).join(' ');

  const style = {
    '--ui-grid-span': span,
    '--ui-grid-span-sm': sm,
    '--ui-grid-span-md': md,
    '--ui-grid-span-lg': lg,
    '--ui-grid-span-xl': xl
  };

  return (
    <div className={classes} style={style} {...props}>
      {children}
    </div>
  );
};

/**
 * 断点显示组件
 * 根据屏幕尺寸控制元素显示/隐藏
 */
const Breakpoint = ({
  children,
  showOn = 'all', // all, mobile, tablet, desktop, sm, md, lg, xl
  hideOn,
  className = '',
  ...props
}) => {
  const baseClass = 'ui-breakpoint';
  const showClass = `ui-breakpoint--show-${showOn}`;
  const hideClass = hideOn ? `ui-breakpoint--hide-${hideOn}` : '';
  
  const classes = [
    baseClass,
    showClass,
    hideClass,
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

/**
 * 响应式图片组件
 */
const ResponsiveImage = ({
  src,
  alt,
  sizes,
  srcSet,
  aspectRatio,
  objectFit = 'cover', // cover, contain, fill
  className = '',
  ...props
}) => {
  const baseClass = 'ui-responsive-image';
  const fitClass = `ui-responsive-image--${objectFit}`;
  
  const classes = [
    baseClass,
    fitClass,
    className
  ].filter(Boolean).join(' ');

  const style = aspectRatio ? {
    aspectRatio: aspectRatio
  } : {};

  return (
    <img
      src={src}
      alt={alt}
      sizes={sizes}
      srcSet={srcSet}
      className={classes}
      style={style}
      loading="lazy"
      {...props}
    />
  );
};

/**
 * 折叠面板组件（移动端友好）
 */
const Collapse = ({
  children,
  title,
  isOpen = false,
  onToggle,
  icon,
  className = '',
  ...props
}) => {
  const baseClass = 'ui-collapse';
  const openClass = isOpen ? 'ui-collapse--open' : '';
  
  const classes = [
    baseClass,
    openClass,
    className
  ].filter(Boolean).join(' ');

  const handleToggle = () => {
    if (onToggle) {
      onToggle(!isOpen);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleToggle();
    }
  };

  return (
    <div className={classes} {...props}>
      <button
        className="ui-collapse__header"
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        aria-expanded={isOpen}
        aria-controls="collapse-content"
      >
        {icon && (
          <span className="ui-collapse__icon">
            {icon}
          </span>
        )}
        
        <span className="ui-collapse__title">
          {title}
        </span>
        
        <span className="ui-collapse__arrow">
          {isOpen ? '▼' : '▶'}
        </span>
      </button>
      
      <div
        id="collapse-content"
        className="ui-collapse__content"
        aria-hidden={!isOpen}
      >
        {children}
      </div>
    </div>
  );
};

// 导出所有组件
Container.Grid = Grid;
Container.GridItem = GridItem;
Container.Breakpoint = Breakpoint;
Container.ResponsiveImage = ResponsiveImage;
Container.Collapse = Collapse;

export default Container;