/**
 * 页面骨架屏组件
 * 
 * 用于页面加载时的占位显示
 */

import React from 'react';
import './styles.css';

/**
 * 骨架屏组件
 * 
 * @param {Object} props
 * @param {string} props.type - 骨架屏类型 (list | grid | card | text)
 * @param {number} props.rows - 行数
 * @param {number} props.columns - 列数（仅grid类型）
 */
const PageSkeleton = ({ type = 'list', rows = 5, columns = 3 }) => {
  if (type === 'grid') {
    return (
      <div className="page-skeleton page-skeleton--grid">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="skeleton-row">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <div key={colIndex} className="skeleton-card">
                <div className="skeleton-header">
                  <div className="skeleton-avatar" />
                  <div className="skeleton-title" />
                </div>
                <div className="skeleton-content">
                  <div className="skeleton-line" />
                  <div className="skeleton-line short" />
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }

  if (type === 'card') {
    return (
      <div className="page-skeleton page-skeleton--card">
        <div className="skeleton-card-large">
          <div className="skeleton-image" />
          <div className="skeleton-body">
            <div className="skeleton-title large" />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
            <div className="skeleton-line short" />
          </div>
        </div>
      </div>
    );
  }

  if (type === 'text') {
    return (
      <div className="page-skeleton page-skeleton--text">
        <div className="skeleton-paragraph">
          {Array.from({ length: rows }).map((_, index) => (
            <div key={index} className="skeleton-line" />
          ))}
        </div>
      </div>
    );
  }

  // 默认列表类型
  return (
    <div className="page-skeleton page-skeleton--list">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="skeleton-list-item">
          <div className="skeleton-checkbox" />
          <div className="skeleton-icon" />
          <div className="skeleton-content">
            <div className="skeleton-title" />
            <div className="skeleton-line short" />
          </div>
          <div className="skeleton-action" />
        </div>
      ))}
    </div>
  );
};

/**
 * 页面加载骨架屏
 * 
 * 包含头部和内容的完整页面骨架
 */
export const FullPageSkeleton = () => (
  <div className="full-page-skeleton">
    <div className="skeleton-header">
      <div className="skeleton-title large" />
      <div className="skeleton-actions">
        <div className="skeleton-button" />
        <div className="skeleton-button" />
      </div>
    </div>
    <div className="skeleton-body">
      <PageSkeleton type="list" rows={8} />
    </div>
  </div>
);

/**
 * 知识库页面骨架屏
 */
export const KnowledgePageSkeleton = () => (
  <div className="knowledge-page-skeleton">
    <div className="skeleton-sidebar">
      <div className="skeleton-search" />
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="skeleton-sidebar-item">
          <div className="skeleton-icon" />
          <div className="skeleton-text" />
        </div>
      ))}
    </div>
    <div className="skeleton-main">
      <div className="skeleton-toolbar">
        <div className="skeleton-tabs">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="skeleton-tab" />
          ))}
        </div>
      </div>
      <div className="skeleton-content">
        <PageSkeleton type="list" rows={6} />
      </div>
    </div>
  </div>
);

export default PageSkeleton;
