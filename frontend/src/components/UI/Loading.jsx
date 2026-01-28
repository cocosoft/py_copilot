import React from 'react';
import './Loading.css';

/**
 * 加载状态组件
 * 支持多种类型和大小
 */
const Loading = ({
  type = 'spinner', // spinner, dots, pulse, skeleton
  size = 'medium', // small, medium, large
  text,
  overlay = false,
  fullscreen = false,
  className = '',
  ...props
}) => {
  const baseClass = 'ui-loading';
  const typeClass = `ui-loading--${type}`;
  const sizeClass = `ui-loading--${size}`;
  const overlayClass = overlay ? 'ui-loading--overlay' : '';
  const fullscreenClass = fullscreen ? 'ui-loading--fullscreen' : '';
  
  const classes = [
    baseClass,
    typeClass,
    sizeClass,
    overlayClass,
    fullscreenClass,
    className
  ].filter(Boolean).join(' ');

  const renderSpinner = () => (
    <div className="ui-loading__spinner">
      <svg viewBox="0 0 24 24" className="ui-loading__spinner-svg">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" />
      </svg>
    </div>
  );

  const renderDots = () => (
    <div className="ui-loading__dots">
      <span className="ui-loading__dot"></span>
      <span className="ui-loading__dot"></span>
      <span className="ui-loading__dot"></span>
    </div>
  );

  const renderPulse = () => (
    <div className="ui-loading__pulse">
      <span className="ui-loading__pulse-circle"></span>
    </div>
  );

  const renderSkeleton = () => (
    <div className="ui-loading__skeleton">
      <div className="ui-loading__skeleton-line"></div>
      <div className="ui-loading__skeleton-line"></div>
      <div className="ui-loading__skeleton-line ui-loading__skeleton-line--short"></div>
    </div>
  );

  const renderContent = () => {
    switch (type) {
      case 'dots':
        return renderDots();
      case 'pulse':
        return renderPulse();
      case 'skeleton':
        return renderSkeleton();
      default:
        return renderSpinner();
    }
  };

  return (
    <div className={classes} {...props}>
      <div className="ui-loading__content">
        {renderContent()}
        {text && (
          <span className="ui-loading__text">
            {text}
          </span>
        )}
      </div>
    </div>
  );
};

/**
 * 骨架屏组件
 */
const Skeleton = ({
  variant = 'text', // text, circle, rect
  width,
  height,
  animation = 'pulse', // pulse, wave
  className = '',
  ...props
}) => {
  const baseClass = 'ui-skeleton';
  const variantClass = `ui-skeleton--${variant}`;
  const animationClass = `ui-skeleton--${animation}`;
  
  const classes = [
    baseClass,
    variantClass,
    animationClass,
    className
  ].filter(Boolean).join(' ');

  const style = {
    width: width || '100%',
    height: height || '1em'
  };

  return (
    <div
      className={classes}
      style={style}
      {...props}
    />
  );
};

// 导出所有组件
Loading.Skeleton = Skeleton;

export default Loading;