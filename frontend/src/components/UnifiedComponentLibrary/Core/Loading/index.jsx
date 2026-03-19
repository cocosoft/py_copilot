/**
 * 统一加载组件
 * 
 * 整合项目中多个加载状态实现，提供统一的加载指示器
 * 支持多种类型、大小、颜色和自定义内容
 */

import React, { memo } from 'react';
import './Loading.css';

/**
 * 加载组件属性定义
 * @typedef {Object} LoadingProps
 * @property {'spinner'|'dots'|'progress'|'skeleton'} type - 加载类型
 * @property {'small'|'medium'|'large'} size - 加载器大小
 * @property {string} color - 加载器颜色
 * @property {string} text - 加载文本
 * @property {number} progress - 进度百分比（0-100）
 * @property {boolean} overlay - 是否显示遮罩层
 * @property {boolean} fullscreen - 是否全屏显示
 * @property {string} className - 自定义类名
 */

const Loading = memo(({
  type = 'spinner',
  size = 'medium',
  color,
  text,
  progress,
  overlay = false,
  fullscreen = false,
  className = '',
}) => {
  const baseClass = 'ucl-loading';
  const typeClass = `ucl-loading--${type}`;
  const sizeClass = `ucl-loading--${size}`;
  const overlayClass = overlay ? 'ucl-loading--overlay' : '';
  const fullscreenClass = fullscreen ? 'ucl-loading--fullscreen' : '';
  
  const classes = [
    baseClass,
    typeClass,
    sizeClass,
    overlayClass,
    fullscreenClass,
    className
  ].filter(Boolean).join(' ');

  // 渲染加载指示器
  const renderLoader = () => {
    switch (type) {
      case 'spinner':
        return (
          <div className="ucl-loading__spinner">
            <svg viewBox="0 0 24 24" fill="none" stroke={color || 'currentColor'}>
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <path d="M12 6v6l4 2" strokeWidth="2" />
            </svg>
          </div>
        );
      
      case 'dots':
        return (
          <div className="ucl-loading__dots">
            <span style={{ backgroundColor: color }}></span>
            <span style={{ backgroundColor: color }}></span>
            <span style={{ backgroundColor: color }}></span>
          </div>
        );
      
      case 'progress':
        return (
          <div className="ucl-loading__progress">
            <div 
              className="ucl-loading__progress-bar"
              style={{
                width: `${progress || 0}%`,
                backgroundColor: color
              }}
            ></div>
          </div>
        );
      
      case 'skeleton':
        return (
          <div className="ucl-loading__skeleton">
            <div className="ucl-loading__skeleton-line" style={{ backgroundColor: color }}></div>
            <div className="ucl-loading__skeleton-line" style={{ backgroundColor: color }}></div>
            <div className="ucl-loading__skeleton-line" style={{ backgroundColor: color }}></div>
          </div>
        );
      
      default:
        return null;
    }
  };

  const content = (
    <div className={classes} role="status" aria-live="polite">
      {renderLoader()}
      {text && (
        <div className="ucl-loading__text">
          {text}
        </div>
      )}
      {type === 'progress' && progress !== undefined && (
        <div className="ucl-loading__progress-text">
          {progress}%
        </div>
      )}
    </div>
  );

  // 如果需要遮罩层或全屏显示
  if (overlay || fullscreen) {
    return (
      <div className="ucl-loading-container">
        {content}
      </div>
    );
  }

  return content;
});

Loading.displayName = 'Loading';

export default Loading;